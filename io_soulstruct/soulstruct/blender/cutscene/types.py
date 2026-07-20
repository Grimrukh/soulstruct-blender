from __future__ import annotations

__all__ = [
    "CutFrames",
    "SoulstructCutsceneAnimation",
]

import math
import typing as tp
from dataclasses import dataclass

import bpy
import numpy as np

from soulstruct.base.animations.sibcam import *
from soulstruct.havok.fromsoft.darksouls1r.remobnd import RemoPartAnimationFrame

from ..animation.types import SoulstructAnimation
from ..animation.utilities import *
from ..exceptions import SoulstructTypeError
from ..flver.models.types import FLVERBoneDataType
from ..types import ArmatureObject, CameraObject, EmptyObject
from ..utilities import to_blender

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

    @property
    def name(self) -> str:
        return self.action.name

    @name.setter
    def name(self, value: str):
        self.action.name = value

    @property
    def strip(self) -> bpy.types.ActionKeyframeStrip:
        return get_or_create_action_strip(self.action)

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
        camera_fov_keyframes: list[list[TimescaledFoVKeyframe]],
        bl_frames_per_game_frame: float,
    ):
        camera.rotation_mode = "XYZ"  # Euler
        camera_data = camera.data
        # We have to convert FoV to focal length and animate that.
        # Blender simply cannot animate FoV ("angle"), only compute it.
        camera_data.lens_unit = "MILLIMETERS"

        _, object_channelbag = self.bind(camera)  # OBJECT
        _, data_channelbag = self.bind(camera_data)  # CAMERA

        location_rows = []
        rotation_rows = []
        final_frame_t = []

        cutscene_frame_index = 0
        for cut_camera_transforms in camera_transforms:
            for cut_frame_index, camera_transform in enumerate(cut_camera_transforms):
                bl_frame_index = cutscene_frame_index * bl_frames_per_game_frame
                bl_translate = to_blender(camera_transform.position)
                bl_euler = to_blender(camera_transform.rotation)
                location_rows.append([bl_frame_index, bl_translate.x, bl_translate.y, bl_translate.z])
                rotation_rows.append([bl_frame_index, bl_euler.x, bl_euler.y, bl_euler.z])
                if cut_frame_index == len(cut_camera_transforms) - 1:
                    final_frame_t.append(bl_frame_index)
                cutscene_frame_index += 1

        location_samples = np.array(location_rows, dtype=np.float64) if location_rows else np.empty((0, 4))
        rotation_samples = np.array(rotation_rows, dtype=np.float64) if rotation_rows else np.empty((0, 4))
        self._add_samples(object_channelbag, "location", location_samples)
        self._add_samples(object_channelbag, "rotation_euler", rotation_samples)
        self._set_keyframe_interpolation(object_channelbag, final_frame_t)

        # TODO: Could create a temp FoV FCurve with tan-in/out and bake it to every-frame Focal Length.
        #  Doesn't seem very impactful as (variable) SIBCAM cut data appears to always be 95% baked anyway.

        sensor_width = camera_data.sensor_width  # should be 35 mm (just created)
        cut_fov_t_offset = 0
        lens_rows = []
        lens_final_t = []
        for cut_fov_keyframes, cut_camera_transforms in zip(camera_fov_keyframes, camera_transforms, strict=True):
            last_bl_t = None
            for fov_keyframe in cut_fov_keyframes:
                lens = sensor_width / (2 * math.tan(fov_keyframe.fov / 2.0))
                bl_t = (cut_fov_t_offset + fov_keyframe.fov_t) * bl_frames_per_game_frame
                lens_rows.append([bl_t, lens])
                last_bl_t = bl_t
            if last_bl_t is not None:
                lens_final_t.append(last_bl_t)
            cut_fov_t_offset += len(cut_camera_transforms)

        lens_samples = np.array(lens_rows, dtype=np.float64) if lens_rows else np.empty((0, 2))
        self._add_samples(data_channelbag, "lens", lens_samples)
        self._set_keyframe_interpolation(data_channelbag, lens_final_t)

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
            arma_local_inv_matrices = SoulstructAnimation.get_armature_local_inv_matrices(armature)
        else:
            arma_local_inv_matrices = {}

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
                    arma_local_inv_matrices,
                    bl_frames_per_game_frame,
                    bone_data_type,
                    assert_root_bone_names=assert_root_bone_names,
                )

                for bone_name, basis_samples in cut_bone_basis_samples.items():
                    basis_samples[:, 0] += global_keyframe_t
                    bone_basis_sample_arrays.setdefault(bone_name, []).append(basis_samples)

            for frame in cut.frames:
                # Cutscene "root motion" (root bone transforms) uses a TRS, not just translate + Z-rotation.
                rm_translate = to_blender(frame.root_motion.translation)
                rm_rotate_quat = to_blender(frame.root_motion.rotation)
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
        """Bind cutscene animation data for one Armature or Dummy into this shared Action.

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
                # "Root motion" is full TRS data.
                rm_translate = to_blender(frame.root_motion.translation)
                rm_rotate_quat = to_blender(frame.root_motion.rotation)
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

    # Export Methods

    @staticmethod
    def export_fov_keyframes(
        fcurve: bpy.types.FCurve,
        bl_frames_per_game_frame: float,
        cut_fov_t_offset: float,
        cut_start_bl_t: float,
        cut_end_bl_t: float
    ) -> list[FoVKeyframe]:
        """Get SIBCAM-ready FoV frame data from cutscene camera animation in Blender.

        Read back FOV keyframes for a single cut from a Blender `angle` fcurve and
        reconstruct (t, fov, tan_in, tan_out) tuples in SIBCAM's native units/convention.

        cut_start_bl_t / cut_end_bl_t bound the keyframes belonging to this cut on the
        Blender timeline (matching how `bl_t` was computed on import).
        """
        n = len(fcurve.keyframe_points)
        co = np.empty(n * 2, dtype=np.float64)
        hl = np.empty(n * 2, dtype=np.float64)
        hr = np.empty(n * 2, dtype=np.float64)
        fcurve.keyframe_points.foreach_get("co", co)
        fcurve.keyframe_points.foreach_get("handle_left", hl)
        fcurve.keyframe_points.foreach_get("handle_right", hr)

        co = co.reshape(-1, 2)
        hl = hl.reshape(-1, 2)
        hr = hr.reshape(-1, 2)

        sibcam_fov_keyframes = []  # type: list[FoVKeyframe]
        for i in range(n):
            bl_t, fov = co[i]
            if not (cut_start_bl_t <= bl_t <= cut_end_bl_t):
                continue

            hl_x, hl_y = hl[i]
            hr_x, hr_y = hr[i]

            # Recover slopes in d(fov)/d(bl_t) from the handle offsets.
            # Guard against zero-length handles (shouldn't happen with FREE/dt-3 handles,
            # but a user could have collapsed a handle onto the keyframe itself).
            dt_left = bl_t - hl_x
            dt_right = hr_x - bl_t
            slope_in = (fov - hl_y) / dt_left if dt_left > 1e-9 else 0.0
            slope_out = (hr_y - fov) / dt_right if dt_right > 1e-9 else 0.0

            # Undo the time rescale applied on import, then undo the incoming-slope sign flip
            # to match SIBCAM's tan_in/tan_out convention (tan_in == -tan_out).
            tan_in = -(slope_in * bl_frames_per_game_frame)
            tan_out = slope_out * bl_frames_per_game_frame

            # Convert bl_t back to the cut-local game frame `t`.
            t = round(bl_t / bl_frames_per_game_frame) - cut_fov_t_offset

            sibcam_fov_keyframes.append(FoVKeyframe(fov_t=t, fov=fov, tan_in=tan_in, tan_out=tan_out))

        return sibcam_fov_keyframes

    # endregion
