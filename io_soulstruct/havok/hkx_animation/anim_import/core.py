from __future__ import annotations

__all__ = ["HKXAnimationImporter"]

import numpy as np

import bpy
from mathutils import Matrix, Quaternion as BlenderQuaternion

from soulstruct_havok.utilities.maths import TRSTransform

from io_soulstruct.utilities import *
from io_soulstruct.havok.utilities import GAME_TRS_TO_BL_MATRIX, get_basis_matrix


class HKXAnimationImporter:
    """Manages imports for a batch of HKX animation files imported simultaneously."""

    FAST = {"FAST"}

    model_name: str
    to_60_fps: bool

    def __init__(
        self,
        operator: LoggingOperator,
        context,
        bl_armature: bpy.types.ArmatureObject,
        model_name: str,
        to_60_fps: bool,
    ):
        self.operator = operator
        self.context = context

        self.bl_armature = bl_armature
        self.model_name = model_name
        self.to_60_fps = to_60_fps

    def create_action(
        self,
        animation_name: str,
        arma_frames: list[dict[str, TRSTransform]],
        root_motion: None | np.ndarray = None,
    ):
        """Import single animation HKX."""
        bone_frame_scaling = 2 if self.to_60_fps else 1
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

        action_name = f"{self.model_name}|{animation_name}"
        action = None  # type: bpy.types.Action | None
        original_location = self.bl_armature.location.copy()  # TODO: not necessary with batch method?
        try:
            self.bl_armature.animation_data_create()
            self.bl_armature.animation_data.action = action = bpy.data.actions.new(name=action_name)
            bone_basis_samples = self._get_bone_basis_samples(arma_frames)
            self._add_keyframes_batch(
                action, bone_basis_samples, root_motion, bone_frame_scaling, root_motion_frame_scaling
            )
        except Exception:
            if action:
                bpy.data.actions.remove(action)
            self.bl_armature.location = original_location  # reset location (i.e. erase last root motion)
            raise

        # Ensure action is not deleted when not in use.
        action.use_fake_user = True
        # Update all F-curves and make them cycle.
        for fcurve in action.fcurves:
            fcurve.modifiers.new("CYCLES")  # default settings are fine
            fcurve.update()
        # Update Blender timeline start/stop times.
        bpy.context.scene.frame_start = int(action.frame_range[0])
        bpy.context.scene.frame_end = int(action.frame_range[1])
        bpy.context.scene.frame_set(bpy.context.scene.frame_start)

    def _get_bone_basis_samples(
        self, arma_frames: list[dict[str, TRSTransform]]
    ) -> dict[str, list[list[float]]]:
        """Convert a list of armature-space frames (mapping bone names to transforms in that frame) to an outer
        dictionary that maps bone names to a list of frames that are each defined by ten floats (location XYZ, rotation
        quaternion, scale XYZ) in basis space.
        """
        # Convert armature-space frame data to Blender `(location, rotation_quaternion, scale)` tuples.
        # Note that we decompose the basis matrices so that quaternion discontinuities are handled properly.
        last_frame_rotations = {}  # type: dict[str, BlenderQuaternion]

        bone_basis_samples = {
            bone_name: [[] for _ in range(10)] for bone_name in arma_frames[0].keys()
        }  # type: dict[str, list[list[float]]]

        # We'll be using the inverted local matrices of each bone on every frame to calculate their basis matrices.
        cached_local_inv_matrices = {
            bone.name: bone.matrix_local.inverted()
            for bone in self.bl_armature.data.bones
        }

        for frame in arma_frames:

            # Get Blender armature space 4x4 transform `Matrix` for each bone.
            bl_arma_matrices = {
                bone_name: GAME_TRS_TO_BL_MATRIX(transform) for bone_name, transform in frame.items()
            }
            cached_arma_inv_matrices = {}  # cached for frame as needed

            for bone_name, bl_arma_matrix in bl_arma_matrices.items():
                basis_samples = bone_basis_samples[bone_name]

                bl_edit_bone = self.bl_armature.data.bones[bone_name]

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
                    self.bl_armature,
                    bone_name,
                    bl_arma_matrix,
                    cached_local_inv_matrices,
                    cached_arma_inv_matrices,
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
    def _add_keyframes_batch(
        action: bpy.types.Action,
        bone_basis_samples: dict[str, list[list[float]]],
        root_motion: np.ndarray | None,
        bone_frame_scaling: float,
        root_motion_frame_scaling: float,
    ):
        """Faster method of adding all bone and (optional) root keyframe data.

        Constructs `FCurves` with known length and uses `foreach_set` to batch-set all the `.co` attributes of the
        curve keyframe points at once.

        `bone_basis_samples` maps bone names to ten lists of floats (location_x, location_y, etc.).
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
