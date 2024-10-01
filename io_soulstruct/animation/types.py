from __future__ import annotations

import time
import traceback

import numpy as np

import bpy
from mathutils import Matrix, Quaternion as BlenderQuaternion

from soulstruct_havok.fromsoft.base import BaseSkeletonHKX, BaseAnimationHKX
from soulstruct_havok.utilities.maths import TRSTransform

from io_soulstruct.exceptions import *
from io_soulstruct.flver.models import BlenderFLVER
from io_soulstruct.utilities import *
from .utilities import *


class SoulstructAnimation:

    FAST = {"FAST"}

    action: bpy.types.Action

    def __init__(self, action: bpy.types.Action):
        if not isinstance(action, bpy.types.Action):
            raise SoulstructTypeError(f"Animation must be initialized with a Blender Action, not {type(action)}.")
        self.action = action

    @property
    def name(self):
        return self.action.name

    @name.setter
    def name(self, value: str):
        self.action.name = value

    @property
    def animation_stem(self):
        """Try to extract the animation stem from the action name.

        Action name should be in the format `{model_name}}|{anim_name}` and may have a Blender dupe suffix. If there is
        no pipe in the name, we return the whole thing.

        Example:
            'c1234|a00_0000.001' -> 'a00_0000'
        """
        if "|" not in self.action.name:
            return self.action.name
        return self.action.name.split("|")[-1].split(".")[0]

    @property
    def animation_id(self) -> int:
        """Try to parse animation stem as an ID.

        Example:
            'c1234|a12_0500.001' -> 120500
        """
        try:
            return int(self.animation_stem.removeprefix("a"))
        except ValueError:
            raise ValueError(f"Could not parse animation ID from Action name '{self.name}'.")

    @classmethod
    def from_armature_animation_data(cls, armature: bpy.types.ArmatureObject) -> SoulstructAnimation:
        """Load from current animation data of given `armature`."""
        if not armature.animation_data:
            raise ValueError(f"Armature '{armature.name}' has no animation data.")
        if not armature.animation_data.action:
            raise ValueError(f"Armature '{armature.name}' has no animation data Action.")
        return cls(armature.animation_data.action)

    # region Import

    @classmethod
    def new_from_hkx_animation(
        cls,
        operator: LoggingOperator,
        context: Context,
        animation_hkx: ANIMATION_TYPING,
        skeleton_hkx: SKELETON_TYPING,
        name: str,
        bl_flver: BlenderFLVER,
    ) -> SoulstructAnimation:
        armature = bl_flver.armature
        if not armature:
            raise AnimationImportError(
                f"Cannot import animation '{name}' into FLVER model {bl_flver.name} without an armature."
            )

        operator.info(f"Importing HKX animation for {armature.name}: '{name}'")

        # We cannot rely on track annotations for bone names in later games (e.g. Elden Ring).
        # Here, we just check that all animated bones are present in Blender Armature.
        hk_bone_names = [b.name for b in skeleton_hkx.skeleton.bones]
        track_bone_indices = animation_hkx.animation_container.animation_binding.transformTrackToBoneIndices
        track_bone_names = [hk_bone_names[i] for i in track_bone_indices]

        bl_bone_names = [b.name for b in armature.data.bones]
        for bone_name in track_bone_names:
            if bone_name not in bl_bone_names:
                if bone_name == "TwistRoot":
                    raise AnimationImportError(
                        f"Animated bone name '{bone_name}' is missing from Armature. This problem is known for this "
                        f"specific bone, which is absent from the FLVER, but has not yet been resolved in Soulstruct."
                    )
                raise AnimationImportError(f"Animated bone name '{bone_name}' is missing from Armature.")

        p = time.perf_counter()
        animation_hkx.animation_container.spline_to_interleaved()
        operator.info(f"Converted spline animation to interleaved in {time.perf_counter() - p:.4f} seconds.")

        p = time.perf_counter()
        arma_frames = get_armature_frames(animation_hkx, skeleton_hkx)
        root_motion = get_root_motion(animation_hkx)
        operator.info(f"Constructed armature animation frames in {time.perf_counter() - p:.4f} seconds.")

        # Import single animation HKX.
        p = time.perf_counter()
        try:
            bl_animation = cls.new_from_transform_frames(
                context,
                action_name=f"{bl_flver.export_name}|{name}",
                armature=armature,
                arma_frames=arma_frames,
                root_motion=root_motion,
            )
        except Exception as ex:
            traceback.print_exc()
            raise AnimationImportError(f"Cannot import HKX animation: {name}. Error: {ex}")
        operator.info(f"Created animation Blender action in {time.perf_counter() - p:.3f} seconds.")

        return bl_animation

    @classmethod
    def new_from_transform_frames(
        cls,
        context: Context,
        action_name: str,
        armature: bpy.types.ArmatureObject,
        arma_frames: list[dict[str, TRSTransform]],
        root_motion: np.ndarray,
    ) -> SoulstructAnimation:
        """Import single animation HKX."""

        # TODO: Assumes source is 30 FPS, which is probably always true with FromSoft?
        to_60_fps = context.scene.animation_import_settings.to_60_fps
        bone_frame_scaling = 2 if to_60_fps else 1

        root_motion_frame_scaling = bone_frame_scaling
        if root_motion is not None:
            if len(root_motion) == 0:
                # Weird, but we'll leave default scaling and put any single root motion keyframe at 0.
                pass
            elif len(root_motion) != len(arma_frames):
                # Root motion is at a lesser (or possibly greater?) sample rate than bone animation. For example, if
                # only two root motion samples are given, they will be scaled to match the first and last frame of
                # `arma_frames`. This scaling stacks with the intrinsic `bone_frame_scaling` (e.g. 2 for 60 FPS).
                root_motion_frame_scaling *= len(arma_frames) / (len(root_motion) - 1)

        action = None  # type: bpy.types.Action | None
        original_location = armature.location.copy()  # TODO: not necessary with batch method?
        try:
            armature.animation_data_create()
            armature.animation_data.action = action = bpy.data.actions.new(name=action_name)
            bone_basis_samples = cls.get_bone_basis_samples(
                armature, arma_frames, cls.get_armature_local_inv_matrices(armature)
            )
            cls.add_keyframes_batch(
                action, bone_basis_samples, root_motion, bone_frame_scaling, root_motion_frame_scaling
            )
        except Exception:
            if action:
                bpy.data.actions.remove(action)
            armature.location = original_location  # reset location (i.e. erase last root motion)
            raise

        # Ensure action is not deleted when not in use.
        action.use_fake_user = True
        # Update all F-curves and make them cycle.
        for fcurve in action.fcurves:
            fcurve.modifiers.new("CYCLES")  # default settings are fine
            fcurve.update()
        # Update Blender timeline start/stop times.
        context.scene.frame_start = int(action.frame_range[0])
        context.scene.frame_end = int(action.frame_range[1])
        context.scene.frame_set(context.scene.frame_start)

        return cls(action)

    @classmethod
    def new_from_cutscene_cuts(
        cls,
        context: Context,
        action_name: str,
        armature: bpy.types.ArmatureObject,
        arma_cuts: list[list[dict[str, TRSTransform]]],
        ignore_master_bone_name: str,
    ) -> SoulstructAnimation:
        """Create a Blender Action that combines all the given cuts in `all_cut_arma_frames`, read from RemoBND.

        No separate root motion is accepted here. Animation of the master bone constitutes root motion in cutscenes.
        """
        to_60_fps = context.scene.cutscene_import_settings.to_60_fps
        bone_frame_scaling = 2 if to_60_fps else 1

        action = None  # type: bpy.types.Action | None
        original_location = armature.location.copy()  # TODO: not necessary with batch method?

        # Record indices of last frame in each cut to set CONSTANT interpolation afterward.
        cut_end_frame_indices = []  # type: list[float]
        frame_count = 0
        for arma_frames in arma_cuts:
            frame_count += len(arma_frames)
            cut_end_frame_indices.append(float(frame_count - 1))  # e.g. if first cut is 10 frames, frame index 9 added

        try:
            armature.animation_data_create()
            armature.animation_data.action = action = bpy.data.actions.new(name=action_name)
            arma_local_inv_matrices = cls.get_armature_local_inv_matrices(armature)  # used by every frame

            # We concatenate all bone basis samples for each cut.
            bone_basis_samples = {
                bone.name: [] for bone in armature.data.bones if bone.name != ignore_master_bone_name
            }
            for arma_cut_frames in arma_cuts:
                cut_bone_basis_samples = cls.get_bone_basis_samples(
                    armature, arma_cut_frames, arma_local_inv_matrices
                )
                for bone_name, basis_samples in cut_bone_basis_samples.items():
                    if bone_name == ignore_master_bone_name:
                        continue  # not animated by cutscenes
                    bone_basis_samples[bone_name].extend(basis_samples)
                # Record final frame index, so we can set constant interpolation there across camera cuts. Note that
                # this is necessary for ALL parts, not just the camera -- many cuts disguise time jumps!

            cls.add_keyframes_batch(
                action,
                bone_basis_samples,
                root_motion=None,
                bone_frame_scaling=bone_frame_scaling,
                root_motion_frame_scaling=1.0,  # unused
            )
        except Exception:
            if action:
                bpy.data.actions.remove(action)
            armature.location = original_location  # reset location (i.e. erase last root motion)
            raise

        # Set constant interpolation at the ends of cuts.
        for fcurve in action.fcurves:
            for keyframe in fcurve.keyframe_points:
                if keyframe.co.x in cut_end_frame_indices:
                    keyframe.interpolation = "CONSTANT"

        # Ensure action is not deleted when not in use.
        action.use_fake_user = True
        # No CYCLES modifier.
        # Update Blender timeline start/stop times.
        context.scene.frame_start = int(action.frame_range[0])
        context.scene.frame_end = int(action.frame_range[1])
        context.scene.frame_set(context.scene.frame_start)

        return cls(action)

    @staticmethod
    def get_armature_local_inv_matrices(armature: bpy.types.ArmatureObject) -> dict[str, Matrix]:
        """Return a dictionary mapping Blender bone names to their inverted `matrix_local` transforms."""
        return {
            bone.name: bone.matrix_local.inverted()
            for bone in armature.data.bones
        }

    @staticmethod
    def get_bone_basis_samples(
        armature: bpy.types.ArmatureObject,
        arma_frames: list[dict[str, TRSTransform]],
        arma_local_inv_matrices: dict[str, Matrix],
    ) -> dict[str, list[list[float]]]:
        """Convert a list of armature-space frames (mapping bone names to transforms in that frame) to an outer
        dictionary that maps bone names to a list of frames that are each defined by ten floats (location XYZ, rotation
        quaternion WXYZ, scale XYZ) in basis space.
        """
        # Convert armature-space frame data to Blender `(location, rotation_quaternion, scale)` tuples.
        # Note that we decompose the basis matrices so that quaternion discontinuities are handled properly.
        last_frame_rotations = {}  # type: dict[str, BlenderQuaternion]

        bone_basis_samples = {
            bone_name: [[] for _ in range(10)] for bone_name in arma_frames[0].keys()
        }  # type: dict[str, list[list[float]]]

        for frame in arma_frames:

            # Get Blender armature space 4x4 transform `Matrix` for each bone.
            bl_arma_matrices = {
                bone_name: GAME_TRS_TO_BL_MATRIX(transform) for bone_name, transform in frame.items()
            }
            cached_arma_inv_matrices = {}  # cached for frame as needed

            for bone_name, bl_arma_matrix in bl_arma_matrices.items():
                basis_samples = bone_basis_samples[bone_name]

                bl_edit_bone = armature.data.bones[bone_name]

                if (
                    bl_edit_bone.parent is not None
                    and bl_edit_bone.parent.name not in cached_arma_inv_matrices
                ):
                    # Cache parent's inverted armature matrix (may be needed by other sibling bones this frame).
                    # Note that as FLVER and HKX skeleton hierarchies may be different, the FLVER (Blender Armature)
                    # parent bone may not even be animated, in which case we just use an identity matrix.
                    parent_name = bl_edit_bone.parent.name
                    if parent_name in bl_arma_matrices:
                        cached_arma_inv_matrices[parent_name] = bl_arma_matrices[parent_name].inverted()
                    else:
                        cached_arma_inv_matrices[parent_name] = Matrix.Identity(4)

                bl_basis_matrix = get_basis_matrix(
                    armature,
                    bone_name,
                    bl_arma_matrix,
                    cached_arma_inv_matrices,
                    arma_local_inv_matrices,
                )

                t, r, s = bl_basis_matrix.decompose()

                if bone_name in last_frame_rotations:
                    if last_frame_rotations[bone_name].dot(r) < 0:
                        r.negate()  # negate quaternion to avoid discontinuity (reverse direction of rotation)

                for samples, sample_float in zip(basis_samples, [t.x, t.y, t.z, r.w, r.x, r.y, r.z, s.x, s.y, s.z]):
                    samples.append(sample_float)

                last_frame_rotations[bone_name] = r

        return bone_basis_samples

    @staticmethod
    def add_keyframes_batch(
        action: bpy.types.Action,
        bone_basis_samples: dict[str, list[list[float]]],
        root_motion: np.ndarray | None,
        bone_frame_scaling: float,
        root_motion_frame_scaling: float,
    ):
        """Faster method of adding all bone and (optional) root keyframe data.

        Constructs `FCurves` with known length and uses `foreach_set` to batch-set all the `.co` attributes of the
        curve keyframe points at once.

        `bone_basis_samples` should map bone names to ten lists of floats (location XYZ, quaternion WXYZ, scale XYZ).
        """

        # Initialize FCurves for root motion and bones.
        if root_motion is not None:
            root_fcurves = [action.fcurves.new(data_path="location", index=i) for i in range(3)]
            root_fcurves.append(action.fcurves.new(data_path="rotation_euler", index=2))  # z-axis rotation in Blender
        else:
            root_fcurves = []

        bone_fcurves = {}
        for bone_name in bone_basis_samples.keys():
            bone_fcurves[bone_name] = []  # ten FCurves per bone
            bone_fcurves[bone_name] += [
                action.fcurves.new(data_path=f"pose.bones[\"{bone_name}\"].location", index=i)
                for i in range(3)
            ]
            bone_fcurves[bone_name] += [
                action.fcurves.new(data_path=f"pose.bones[\"{bone_name}\"].rotation_quaternion", index=i)
                for i in range(4)
            ]
            bone_fcurves[bone_name] += [
                action.fcurves.new(data_path=f"pose.bones[\"{bone_name}\"].scale", index=i)
                for i in range(3)
            ]

        # Build lists of FCurve keyframe points by initializing their size and using `foreach_set`.
        # Each keyframe point has a `.co` attribute to which we set `(bl_frame_index, value)` (per dimension).
        # `foreach_set` requires that we flatten the list of tuples to be assigned, a la:
        #    `[bl_frame_index_0, value_0, bl_frame_index_1, value_1, ...]`
        # which we do with a list comprehension.
        if root_fcurves:
            # NOTE: There may be less root motion samples than bone animation samples. We spread the root motion samples
            # out to match the bone animation frames using `root_motion_frame_scaling` (done by caller).
            for col, fcurve in enumerate(root_fcurves):  # x, y, z, -rz (from game ry)
                dim_samples = root_motion[:, col]  # one dimension of root motion
                fcurve.keyframe_points.add(count=len(dim_samples))
                root_dim_flat = [
                    x
                    for frame_index, sample_float in enumerate(dim_samples)
                    for x in [frame_index * root_motion_frame_scaling, sample_float]
                ]
                fcurve.keyframe_points.foreach_set("co", root_dim_flat)

        for bone_name, bone_transform_fcurves in bone_fcurves.items():
            basis_samples = bone_basis_samples[bone_name]
            for bone_fcurve, samples in zip(bone_transform_fcurves, basis_samples, strict=True):
                bone_fcurve.keyframe_points.add(count=len(samples))
                bone_dim_flat = [
                    x
                    for frame_index, sample_float in enumerate(samples)
                    for x in [frame_index * bone_frame_scaling, sample_float]
                ]
                bone_fcurve.keyframe_points.foreach_set("co", bone_dim_flat)

    # endregion
    
    # region Export

    def to_animation_hkx(
        self,
        context: Context,
        armature: bpy.types.ArmatureObject,
        skeleton_hkx: BaseSkeletonHKX,
        animation_hkx_class: type[BaseAnimationHKX],
    ) -> ANIMATION_TYPING:
        """Animation data is easier to export from Blender than import, as we can just read the bone transforms on each
        frame in Armature space directly (rather than needing to compute each basis Matrix when importing).

        We still need this action to determine the name and start/end times for the animation.

        The `skeleton_hkx` Havok type version is used to determine the returned `AnimationHKX` Havok type version.
        """
        if animation_hkx_class.get_version_string().startswith("Havok_"):
            raise NotImplementedError("Cannot export Demon's Souls animations.")

        export_settings = context.scene.animation_export_settings

        # TODO: Technically, animation export only needs a start/end frame range, since it samples location/bone pose
        #  on every single frame anyway and does NOT need to actually use the action FCurves!

        # Determine the frame range.
        # TODO: Export bool option to just read from current scene values, rather than checking action.
        if export_settings.selected_frames_only:
            start_frame = context.scene.frame_start
            end_frame = context.scene.frame_end
        else:
            start_frame = int(min(fcurve.range()[0] for fcurve in self.action.fcurves))
            end_frame = int(max(fcurve.range()[1] for fcurve in self.action.fcurves))

        # All frame interleaved transforms, in armature space.
        root_motion_samples = []  # type: list[tuple[float, float, float, float]]
        armature_space_frames = []  # type: list[list[TRSTransform]]

        has_root_motion = False

        # Animation track order will match Blender bone order (which should come from FLVER).
        track_bone_mapping = list(range(len(skeleton_hkx.skeleton.bones)))

        # Store last bone TRS for rotation negation.
        last_bone_trs = {bone.name: TRSTransform.identity() for bone in skeleton_hkx.skeleton.bones}

        # Slight efficiency boost.
        bl_bones_by_name = {
            bone.name: bone for bone in armature.pose.bones
        }

        # Evaluate all curves at every frame, inclusive of `end_frame`.
        for i, frame in enumerate(range(start_frame, end_frame + 1)):

            if export_settings.from_60_fps and i % 2 == 1:
                # Skip every second frame to convert 60 FPS to 30 FPS (frame 0 should generally be keyframed).
                continue

            bpy.context.scene.frame_set(frame)
            armature_space_frame = []  # type: list[TRSTransform]

            # We collect root motion vectors, as we're not sure if any root motion exists yet.
            loc = armature.location
            rot = armature.rotation_euler
            root_motion_sample = (loc[0], loc[1], loc[2], rot[2])  # XYZ and Z rotation (soon to be game Y)
            root_motion_samples.append(root_motion_sample)
            if not has_root_motion:
                if len(root_motion_samples) >= 2 and root_motion_samples[-1] != root_motion_samples[-2]:
                    # Some actual root motion has appeared.
                    has_root_motion = True

            for bone in skeleton_hkx.skeleton.bones:
                try:
                    bl_bone = bl_bones_by_name[bone.name]
                except KeyError:
                    raise AnimationExportError(f"Bone '{bone.name}' in HKX skeleton not found in Blender armature.")
                armature_space_transform = BL_MATRIX_TO_GAME_TRS(bl_bone.matrix)
                if i > 0:
                    # Negate rotation quaternion if dot product with last rotation is negative (first frame ignored).
                    dot = np.dot(armature_space_transform.rotation.data, last_bone_trs[bone.name].rotation.data)
                    if dot < 0:
                        armature_space_transform.rotation = -armature_space_transform.rotation
                last_bone_trs[bone.name] = armature_space_transform
                armature_space_frame.append(armature_space_transform)

            armature_space_frames.append(armature_space_frame)

        if has_root_motion:
            root_motion = np.array(root_motion_samples, dtype=np.float32)
            # Swap translate Y/Z and negate rotation Z (now Y).
            root_motion = np.c_[root_motion[:, 0], root_motion[:, 2], root_motion[:, 1], -root_motion[:, 3]]
        else:
            root_motion = None

        interleaved_animation_hkx = animation_hkx_class.from_minimal_data_interleaved(
            frame_transforms=armature_space_frames,
            track_names=[bone.name for bone in skeleton_hkx.skeleton.bones],
            transform_track_bone_indices=track_bone_mapping,
            root_motion_array=root_motion,
            original_skeleton_name=skeleton_hkx.skeleton.skeleton.name,
            frame_rate=30.0,
            skeleton_for_armature_to_local=skeleton_hkx,
        )

        try:
            spline_animation_hkx = interleaved_animation_hkx.get_spline_hkx()
        except NotImplementedError:
            raise UnsupportedGameError(
                f"Animation export not yet possible for game {context.scene.soulstruct_settings.game}."
            )

        return spline_animation_hkx

    # endregion
