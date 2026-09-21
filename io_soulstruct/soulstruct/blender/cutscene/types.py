from __future__ import annotations

__all__ = [
    "CutFrames",
    "SoulstructCutsceneAnimation",
]

import typing as tp
from dataclasses import dataclass

import bpy
import numpy as np
from mathutils import Euler, Quaternion as BLQuaternion, Vector

from soulstruct.base.animations.sibcam import *
from soulstruct.havok.fromsoft.darksouls1r.remobnd import RemoPartAnimationFrame
from soulstruct.havok.utilities.maths import TRSTransform
from soulstruct.utilities.maths import EulerRad, Vector3

from ..animation.types import SoulstructAnimation
from ..animation.utilities import *
from ..exceptions import SoulstructTypeError
from ..flver.models.types import FLVERBoneDataType
from ..flver.utilities import bl_bone_trs_to_game_trs
from ..types import ArmatureObject, CameraObject, EmptyObject
from ..utilities import to_blender, to_game, bl_trs_to_game_trs
from .utilities import fov_to_lens, lens_to_fov

if tp.TYPE_CHECKING:
    from .properties import CutsceneActionProps

# Blender BezTriple interpolation enum -> int (for batched `foreach_set`).
# Verify on your Blender build if interpolation ever looks wrong; revert to the
# string-assignment loop below if these differ.
_INTERP_CONSTANT = 0
_INTERP_LINEAR = 1


@dataclass(slots=True)
class CutFrames:
    """One cut's animation data for a single part (or dummy).

    `frames` is `None` when the part does not appear in this cut. `frame_count` is
    *always* the cut's clip length (from the camera), so the timeline pads uniformly
    whether or not this part is present. This replaces the old
    `list[RemoPartAnimationFrame] | int` union, so consumers never branch on type:
    they read `cut.frames is None` for presence and `cut.frame_count` for length.
    """
    frame_count: int
    frames: list[RemoPartAnimationFrame] | None = None


class _ChannelbagSampler:
    """Evaluates the F-curves of one `ActionChannelbag` by `(data_path, array_index)`.

    Cutscene import writes one LINEAR keyframe per game frame, so evaluating at those exact Blender frames is exact
    and far cheaper than stepping `scene.frame_set()` through a (possibly huge) MSB scene. It also makes export
    independent of each bone's `inherit_scale` mode, since armature-space poses are recomposed from the pose channels
    with the same shear-free TRS maths that import used (see `get_pose_trs_from_basis()`).
    """

    def __init__(self, channelbag: bpy.types.ActionChannelbag | None):
        self.fcurves = {}  # type: dict[tuple[str, int], bpy.types.FCurve]
        if channelbag is not None:
            for fcurve in channelbag.fcurves:
                self.fcurves[fcurve.data_path, fcurve.array_index] = fcurve

    def has_path(self, data_path: str) -> bool:
        return any(path == data_path for path, _ in self.fcurves)

    def evaluate(self, data_path: str, index: int, bl_frame: float, default: float) -> float:
        fcurve = self.fcurves.get((data_path, index))
        return float(fcurve.evaluate(bl_frame)) if fcurve is not None else default

    def evaluate_vector(self, data_path: str, bl_frame: float, default: tp.Sequence[float]) -> Vector:
        return Vector([self.evaluate(data_path, i, bl_frame, d) for i, d in enumerate(default)])

    def evaluate_quaternion(self, data_path: str, bl_frame: float) -> BLQuaternion:
        return BLQuaternion([self.evaluate(data_path, i, bl_frame, d) for i, d in enumerate((1.0, 0.0, 0.0, 0.0))])

    def evaluate_rotation(self, bl_frame: float, rotation_mode: str) -> BLQuaternion:
        """Read an Object's rotation from whichever channels are animated, honouring the object's rotation mode."""
        if rotation_mode == "QUATERNION" or self.has_path("rotation_quaternion") and not self.has_path("rotation_euler"):
            return self.evaluate_quaternion("rotation_quaternion", bl_frame)
        if rotation_mode == "AXIS_ANGLE":
            axis_angle = self.evaluate_vector("rotation_axis_angle", bl_frame, (0.0, 0.0, 1.0, 0.0))
            return BLQuaternion(axis_angle[1:4], axis_angle[0])
        euler = self.evaluate_vector("rotation_euler", bl_frame, (0.0, 0.0, 0.0))
        return Euler(euler, rotation_mode if rotation_mode != "QUATERNION" else "XYZ").to_quaternion()


class SoulstructCutsceneAnimation:
    """Wrapper around a single shared cutscene Action with per-ID slots/channelbags.

    Blender 5.1 no longer exposes a flat `Action.fcurves` API for layered Actions. Instead, every animated ID
    (Object, Camera data, etc.) gets its own `ActionSlot`, whose animation data lives in a `channelbag` on the
    Action's keyframe strip.
    """

    FAST = {"FAST"}

    action: bpy.types.Action

    def __init__(self, action: bpy.types.Action):
        if not isinstance(action, bpy.types.Action):
            raise SoulstructTypeError(
                f"Cutscene animation must be initialized with a Blender Action, not {type(action).__name__}."
            )
        self.action = action

    @classmethod
    def new(cls, action_name: str) -> SoulstructCutsceneAnimation:
        action = bpy.data.actions.new(name=action_name)
        action.use_fake_user = True
        get_or_create_action_strip(action)
        return cls(action)

    @classmethod
    def from_animated_id(cls, animated_id: bpy.types.ID) -> SoulstructCutsceneAnimation | None:
        """Wrap the cutscene Action assigned to `animated_id` (an Object or Camera data), or `None` if it has none."""
        anim_data = animated_id.animation_data
        if not anim_data or not anim_data.action:
            return None
        if not anim_data.action.cutscene.is_cutscene:
            return None
        return cls(anim_data.action)

    @property
    def name(self) -> str:
        return self.action.name

    @name.setter
    def name(self, value: str):
        self.action.name = value

    @property
    def props(self) -> CutsceneActionProps:
        return self.action.cutscene

    @property
    def strip(self) -> bpy.types.ActionKeyframeStrip:
        return get_or_create_action_strip(self.action)

    @property
    def bl_frames_per_game_frame(self) -> float:
        return self.props.bl_frames_per_game_frame

    @staticmethod
    def _get_slot_id_type(animated_id: bpy.types.ID) -> tp.Literal["OBJECT", "CAMERA"]:
        """Only Objects (including Armatures) and Cameras can be animated by cutscenes."""
        if isinstance(animated_id, bpy.types.Object):
            return "OBJECT"
        if isinstance(animated_id, bpy.types.Camera):
            return "CAMERA"
        raise TypeError(f"Unsupported cutscene Action slot ID type: {type(animated_id).__name__}")

    def bind(
        self,
        animated_id: bpy.types.ID,
    ) -> tuple[bpy.types.ActionSlot, bpy.types.ActionChannelbag]:
        """Bind our unified cutscene `Action` to `animated_id` and find/create the appropriate slot."""
        anim_data = animated_id.animation_data_create()
        anim_data.action = self.action
        # After assigning the Action, we can find the same-named slot.
        for slot in anim_data.action_suitable_slots:
            if slot.name_display == animated_id.name:
                anim_data.action_slot = slot
                break
        else:
            # Create new action slot for this ID.
            anim_data.action_slot = self.action.slots.new(
                id_type=self._get_slot_id_type(animated_id),
                name=animated_id.name,
            )

        channelbag = self.strip.channelbag(anim_data.action_slot, ensure=True)
        return anim_data.action_slot, channelbag

    def get_channelbag(self, animated_id: bpy.types.ID) -> bpy.types.ActionChannelbag | None:
        """Get the channelbag of `animated_id`'s slot in this Action, or `None` if it is not bound to this Action."""
        anim_data = animated_id.animation_data
        if not anim_data or anim_data.action != self.action or not anim_data.action_slot:
            return None
        return self.strip.channelbag(anim_data.action_slot, ensure=False)

    def is_bound(self, animated_id: bpy.types.ID) -> bool:
        return self.get_channelbag(animated_id) is not None

    def get_bound_objects(self) -> list[bpy.types.Object]:
        """All Objects currently using this Action (Armatures, Dummy Empties, the Camera)."""
        return [obj for obj in bpy.data.objects if self.is_bound(obj)]

    def get_camera(self) -> CameraObject | None:
        """The (first) Camera Object bound to this Action, if any."""
        for obj in bpy.data.objects:
            if obj.type == "CAMERA" and self.is_bound(obj):
                # noinspection PyTypeChecker
                return obj
        return None

    def is_object_hidden_at(self, obj: bpy.types.Object, bl_frame: float) -> bool:
        """Whether `obj`'s `hide_render` or `hide_viewport` F-curve in this Action evaluates to hidden at `bl_frame`.

        Objects that are not bound to this Action, or have no such F-curves, count as visible (their static
        visibility is deliberately ignored, so parts can be hidden in the viewport while working).
        """
        sampler = _ChannelbagSampler(self.get_channelbag(obj))
        for data_path in ("hide_render", "hide_viewport"):
            if sampler.has_path(data_path) and sampler.evaluate(data_path, 0, bl_frame, 0.0) >= 0.5:
                return True
        return False

    # region Import

    @staticmethod
    def _normalize_keyframe_t(keyframe_t: float) -> float:
        return round(float(keyframe_t), 6)

    @classmethod
    def _set_keyframe_interpolation(
        cls,
        channelbag: bpy.types.ActionChannelbag,
        constant_keyframe_t: tp.Iterable[float] = (),
    ):
        """Set every keyframe to LINEAR, except those whose (rounded) time is in
        `constant_keyframe_t`, which become CONSTANT holds (cut boundaries).

        Keyframes are matched by time rather than index because per-bone keyframe
        rows are not uniformly indexed across cuts. The comparison is vectorized
        with `foreach_get`/`foreach_set` to avoid a per-keyframe Python loop.
        """
        constant_t = np.fromiter(
            {cls._normalize_keyframe_t(t) for t in constant_keyframe_t},
            dtype=np.float64,
        )
        for fcurve in channelbag.fcurves:
            n = len(fcurve.keyframe_points)
            if n == 0:
                continue
            co = np.empty(n * 2, dtype=np.float64)
            fcurve.keyframe_points.foreach_get("co", co)
            frame_t = np.round(co[0::2], 6)

            interp = np.full(n, _INTERP_LINEAR, dtype=np.int32)
            if constant_t.size:
                interp[np.isin(frame_t, constant_t)] = _INTERP_CONSTANT

            fcurve.keyframe_points.foreach_set("interpolation", interp.tolist())
            fcurve.update()

    @staticmethod
    def _add_samples(
        channelbag: bpy.types.ActionChannelbag,
        data_path: str,
        samples: np.ndarray,
    ):
        """Add `t,value...` samples to a channelbag path using batched `foreach_set()` writes."""
        if samples.ndim != 2 or samples.shape[1] < 2:
            raise ValueError(
                f"Cutscene sample array must be 2D with at least 2 columns (`keyframe_t` plus values), not: "
                f"{samples.shape}"
            )
        if samples.shape[0] == 0:
            return

        for array_index in range(samples.shape[1] - 1):
            fcurve = channelbag.fcurves.new(data_path=data_path, index=array_index)
            data = samples[:, [0, array_index + 1]]
            fcurve.keyframe_points.add(count=data.shape[0])
            fcurve.keyframe_points.foreach_set("co", data.ravel().tolist())

    def add_camera_cuts(
        self,
        camera: CameraObject,
        camera_transforms: list[list[CameraFrameTransform]],
        camera_fov_values: list[list[float]],
        bl_frames_per_game_frame: float,
    ):
        """Animate `camera` (Object transform and Camera data lens) from per-cut lists of clipped camera frames and
        the FoV (radians) at each of those frames.

        FoV is baked to one focal length keyframe per game frame. Blender cannot animate `Camera.angle` directly,
        and the SIBCAM FoV curve is a sparse cubic Hermite spline in FoV space that does not map onto Bezier handles
        in (nonlinear) focal length space, so per-frame baking is the only exact representation. Export samples the
        lens curve per frame anyway, so users are free to re-key it sparsely.
        """
        camera.rotation_mode = "XYZ"  # Euler
        camera_data = camera.data
        camera_data.lens_unit = "MILLIMETERS"

        _, object_channelbag = self.bind(camera)  # OBJECT
        _, data_channelbag = self.bind(camera_data)  # CAMERA

        sensor_width = camera_data.sensor_width

        location_rows = []
        rotation_rows = []
        lens_rows = []
        final_frame_t = []

        cutscene_frame_index = 0
        for cut_camera_transforms, cut_fov_values in zip(camera_transforms, camera_fov_values, strict=True):
            if len(cut_camera_transforms) != len(cut_fov_values):
                raise ValueError(
                    f"Cut has {len(cut_camera_transforms)} camera frames but {len(cut_fov_values)} FoV values."
                )
            for cut_frame_index, (camera_transform, fov) in enumerate(zip(cut_camera_transforms, cut_fov_values)):
                bl_frame_index = cutscene_frame_index * bl_frames_per_game_frame
                bl_translate = to_blender(camera_transform.position)
                bl_euler = to_blender(camera_transform.rotation)
                location_rows.append([bl_frame_index, bl_translate.x, bl_translate.y, bl_translate.z])
                rotation_rows.append([bl_frame_index, bl_euler.x, bl_euler.y, bl_euler.z])
                lens_rows.append([bl_frame_index, fov_to_lens(fov, sensor_width)])
                if cut_frame_index == len(cut_camera_transforms) - 1:
                    final_frame_t.append(bl_frame_index)
                cutscene_frame_index += 1

        location_samples = np.array(location_rows, dtype=np.float64) if location_rows else np.empty((0, 4))
        rotation_samples = np.array(rotation_rows, dtype=np.float64) if rotation_rows else np.empty((0, 4))
        lens_samples = np.array(lens_rows, dtype=np.float64) if lens_rows else np.empty((0, 2))
        self._add_samples(object_channelbag, "location", location_samples)
        self._add_samples(object_channelbag, "rotation_euler", rotation_samples)
        self._set_keyframe_interpolation(object_channelbag, final_frame_t)
        self._add_samples(data_channelbag, "lens", lens_samples)
        self._set_keyframe_interpolation(data_channelbag, final_frame_t)

    def add_armature_cuts(
        self,
        armature: ArmatureObject,
        cuts: list[CutFrames],
        bl_frames_per_game_frame: float,
        bone_data_type: FLVERBoneDataType,
        is_root_motion_only: bool = False,
        assert_root_bone_names: tp.Container[str] = (),
    ):
        """Bind cutscene animation data for one Armature into this shared Action.

        A single pass over `cuts` drives both keyframe placement (via `global_keyframe_t`)
        and cut-boundary tracking (`cut_end_keyframe_t`), so there is exactly one frame
        accountant and no chance of the two drifting out of sync. Boundaries are recorded
        only for cuts this part actually appears in.
        """
        armature.rotation_mode = "QUATERNION"
        _, channelbag = self.bind(armature)

        if not is_root_motion_only:
            rest_trs_by_bone_name = get_armature_rest_trs(armature)
            flver_rest_scales = get_flver_bone_rest_scales(armature, bone_data_type)
        else:
            rest_trs_by_bone_name = {}
            flver_rest_scales = {}

        bone_basis_sample_arrays = {}  # type: dict[str, list[np.ndarray]]
        root_motion_rows = []  # type: list[list[float]]
        cut_end_keyframe_t = []  # type: list[float]

        global_keyframe_t = 0.0
        for cut in cuts:
            if cut.frames is None:
                # Part absent from this cut: just pad the timeline by the clip length.
                global_keyframe_t += cut.frame_count * bl_frames_per_game_frame
                continue

            bone_arma_frames = [frame.bone_transforms for frame in cut.frames]
            if not is_root_motion_only and any(bone_arma_frames):
                cut_bone_basis_samples = SoulstructAnimation.get_bone_basis_samples(
                    armature,
                    bone_arma_frames,
                    rest_trs_by_bone_name,
                    bl_frames_per_game_frame,
                    bone_data_type,
                    assert_root_bone_names=assert_root_bone_names,
                    flver_rest_scales=flver_rest_scales,
                )

                for bone_name, basis_samples in cut_bone_basis_samples.items():
                    basis_samples[:, 0] += global_keyframe_t
                    bone_basis_sample_arrays.setdefault(bone_name, []).append(basis_samples)

            for frame in cut.frames:
                # Cutscene "root motion" (root bone transforms) uses a TRS, not just translate + Z-rotation.
                # Rotation is normalized: spline-decompressed quaternions are not exactly unit length, and export
                # (like `game_trs_to_bl_trs()`) always writes unit quaternions.
                rm_translate = to_blender(frame.root_motion.translation)
                rm_rotate_quat = to_blender(frame.root_motion.rotation).normalized()
                rm_scale = to_blender(frame.root_motion.scale)
                root_motion_rows.append(
                    [
                        global_keyframe_t,
                        *rm_translate,
                        *rm_rotate_quat,
                        *rm_scale,
                    ]
                )
                global_keyframe_t += bl_frames_per_game_frame

            # Final keyframe of this cut holds CONSTANT (no interpolation into the next cut).
            cut_end_keyframe_t.append(global_keyframe_t - bl_frames_per_game_frame)

        if bone_basis_sample_arrays:
            bone_basis_samples = {
                bone_name: np.concatenate(basis_sample_arrays)
                for bone_name, basis_sample_arrays in bone_basis_sample_arrays.items()
            }
        else:
            # No bone transforms to animate.
            bone_basis_samples = {}

        root_motion = np.array(root_motion_rows, dtype=np.float64) if root_motion_rows else np.empty((0, 5))

        if not bone_basis_samples and root_motion.shape[0] == 0:
            return

        add_keyframes_batch(
            channelbag,
            bone_basis_samples,
            root_motion=root_motion,
        )
        self._set_keyframe_interpolation(channelbag, cut_end_keyframe_t)

    def add_dummy_cuts(
        self,
        dummy: EmptyObject,
        cuts: list[CutFrames],
        bl_frames_per_game_frame: float,
    ):
        """Bind cutscene animation data for one Dummy Empty into this shared Action (root motion only).

        A single pass over `cuts` drives both keyframe placement (via `global_keyframe_t`)
        and cut-boundary tracking (`cut_end_keyframe_t`), so there is exactly one frame
        accountant and no chance of the two drifting out of sync. Boundaries are recorded
        only for cuts this part actually appears in.
        """
        dummy.rotation_mode = "QUATERNION"
        _, channelbag = self.bind(dummy)

        root_motion_rows = []  # type: list[list[float]]
        cut_end_keyframe_t = []  # type: list[float]

        global_keyframe_t = 0.0
        for cut in cuts:
            if cut.frames is None:
                # Part absent from this cut: just pad the timeline by the clip length.
                global_keyframe_t += cut.frame_count * bl_frames_per_game_frame
                continue

            for frame in cut.frames:
                # "Root motion" is full TRS data (see normalization note in `add_armature_cuts()`).
                rm_translate = to_blender(frame.root_motion.translation)
                rm_rotate_quat = to_blender(frame.root_motion.rotation).normalized()
                root_motion_rows.append(
                    [
                        global_keyframe_t,
                        *rm_translate,
                        *rm_rotate_quat,
                    ]
                )
                global_keyframe_t += bl_frames_per_game_frame

            # Final keyframe of this cut holds CONSTANT (no interpolation into the next cut).
            cut_end_keyframe_t.append(global_keyframe_t - bl_frames_per_game_frame)

        root_motion = np.array(root_motion_rows, dtype=np.float64) if root_motion_rows else np.empty((0, 5))

        if root_motion.shape[0] == 0:
            return

        add_keyframes_batch(
            channelbag,
            bone_basis_samples={},
            root_motion=root_motion,
        )
        self._set_keyframe_interpolation(channelbag, cut_end_keyframe_t)

    def set_scene_frame_range(self, context: bpy.types.Context, reset_current_frame=True):
        """Set Blender scene frame range to match this cutscene Action."""
        context.scene.frame_start = int(self.action.frame_range[0])
        context.scene.frame_end = int(self.action.frame_range[1])
        if reset_current_frame:
            context.scene.frame_set(context.scene.frame_start)

    # endregion

    # region Export

    def get_cut_bl_frames(self, cut_name: str) -> list[float]:
        """Blender timeline frames of every game frame in `cut_name`, from the cut metadata stored on the Action."""
        first, last = self.props.get_cut_bl_frame_ranges()[cut_name]
        step = self.bl_frames_per_game_frame
        count = int(round((last - first) / step)) + 1
        return [first + i * step for i in range(count)]

    def sample_camera(
        self, camera: CameraObject, bl_frames: tp.Sequence[float]
    ) -> list[tuple[Vector3, EulerRad, float]]:
        """Sample the camera's game-space `(position, rotation, fov)` at each Blender frame.

        Exact inverse of `add_camera_cuts()`: position/rotation come from the Object channels and FoV from the
        Camera data `lens` channel (converted with the camera's current sensor width).
        """
        object_sampler = _ChannelbagSampler(self.get_channelbag(camera))
        data_sampler = _ChannelbagSampler(self.get_channelbag(camera.data))
        sensor_width = camera.data.sensor_width
        samples = []
        for bl_frame in bl_frames:
            bl_translate = object_sampler.evaluate_vector("location", bl_frame, camera.location)
            bl_euler = Euler(object_sampler.evaluate_vector("rotation_euler", bl_frame, camera.rotation_euler), "XYZ")
            lens = data_sampler.evaluate("lens", 0, bl_frame, camera.data.lens)
            samples.append((to_game(bl_translate), to_game(bl_euler), lens_to_fov(lens, sensor_width)))
        return samples

    def sample_root_motion(self, obj: bpy.types.Object, bl_frames: tp.Sequence[float]) -> list[TRSTransform]:
        """Sample an Object's (Armature or Dummy Empty) game-space world transform at each Blender frame.

        Exact inverse of the root motion channels written by `add_armature_cuts()`/`add_dummy_cuts()`. Channels that
        are not animated fall back to the Object's current transform.
        """
        sampler = _ChannelbagSampler(self.get_channelbag(obj))
        transforms = []
        for bl_frame in bl_frames:
            bl_translate = sampler.evaluate_vector("location", bl_frame, obj.location)
            if sampler.has_path("rotation_quaternion") or sampler.has_path("rotation_euler") or sampler.has_path(
                "rotation_axis_angle"
            ):
                bl_rotate = sampler.evaluate_rotation(bl_frame, obj.rotation_mode)
            else:
                bl_rotate = obj.matrix_basis.to_quaternion()
            bl_scale = sampler.evaluate_vector("scale", bl_frame, obj.scale)
            transforms.append(bl_trs_to_game_trs(bl_translate, bl_rotate, bl_scale))
        return transforms

    def sample_armature_bones(
        self,
        armature: ArmatureObject,
        bone_names: tp.Sequence[str],
        bl_frames: tp.Sequence[float],
        bone_data_type: FLVERBoneDataType,
        root_bone_names: tp.Container[str] = (),
    ) -> list[dict[str, TRSTransform]]:
        """Sample the game armature-space transform of each bone in `bone_names` at each Blender frame.

        Exact inverse of `SoulstructAnimation.get_bone_basis_samples()` as used by `add_armature_cuts()`:
            - pose channels are recomposed into armature-space poses with shear-free TRS maths, walking up the
              Blender bone hierarchy;
            - bones in `root_bone_names` (the cutscene's own root bones for this part, e.g. `Upper_Root`) are
              treated as parentless, exactly as import did, since cutscene FK ignores their FLVER parents;
            - a parent that is not itself in `bone_names` is taken to sit at its REST pose (the same default import
              used), so its Blender pose channels are deliberately ignored;
            - the FLVER rest bone scale that import divided out of `EDIT` bone poses is multiplied back in, and the
              X-forward bone change of basis is undone at TRS level.
        """
        sampler = _ChannelbagSampler(self.get_channelbag(armature))
        rest_trs_by_bone_name = get_armature_rest_trs(armature)
        flver_rest_scales = get_flver_bone_rest_scales(armature, bone_data_type)
        bl_bones = armature.data.bones
        sampled_names = set(bone_names)

        def _get_pose_trs(bone_name: str, bl_frame: float, cache: dict[str, TRS]) -> TRS:
            if bone_name in cache:
                return cache[bone_name]
            prefix = f"pose.bones[\"{bone_name}\"]."
            basis_trs = (
                sampler.evaluate_vector(prefix + "location", bl_frame, (0.0, 0.0, 0.0)),
                sampler.evaluate_quaternion(prefix + "rotation_quaternion", bl_frame),
                sampler.evaluate_vector(prefix + "scale", bl_frame, (1.0, 1.0, 1.0)),
            )
            rest_trs = rest_trs_by_bone_name[bone_name]
            bl_bone = bl_bones[bone_name]
            if bl_bone.parent is not None and bone_name not in root_bone_names:
                parent_name = bl_bone.parent.name
                parent_rest_trs = rest_trs_by_bone_name[parent_name]
                if parent_name in sampled_names:
                    parent_pose_trs = _get_pose_trs(parent_name, bl_frame, cache)
                else:
                    parent_pose_trs = parent_rest_trs  # un-animated parent sits at rest (mirrors import)
            else:
                parent_rest_trs = None
                parent_pose_trs = None
            pose_trs = get_pose_trs_from_basis(rest_trs, parent_rest_trs, basis_trs, parent_pose_trs)
            cache[bone_name] = pose_trs
            return pose_trs

        frames = []
        for bl_frame in bl_frames:
            cache = {}  # type: dict[str, TRS]
            frame = {}  # type: dict[str, TRSTransform]
            for bone_name in bone_names:
                pose_t, pose_r, pose_s = _get_pose_trs(bone_name, bl_frame, cache)
                rest_scale = flver_rest_scales.get(bone_name)
                if rest_scale is not None:
                    pose_s = Vector((pose_s.x * rest_scale.x, pose_s.y * rest_scale.y, pose_s.z * rest_scale.z))
                if bone_data_type == FLVERBoneDataType.EDIT:
                    frame[bone_name] = bl_bone_trs_to_game_trs(pose_t, pose_r, pose_s)
                else:
                    frame[bone_name] = bl_trs_to_game_trs(pose_t, pose_r, pose_s)
            frames.append(frame)
        return frames

    # endregion
