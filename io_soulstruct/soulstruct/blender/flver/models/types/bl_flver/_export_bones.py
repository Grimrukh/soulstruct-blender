"""Functions for exporting FLVER bones from Blender Armature bones."""
from __future__ import annotations

__all__ = [
    "create_flver_bones",
]

import re

import bpy
from mathutils import Vector

from soulstruct.flver import FLVER, FLVERBone, FLVERBoneUsageFlags
from soulstruct.utilities.maths import Vector3, Matrix3
from soulstruct.utilities.misc import IDList

from soulstruct.blender.exceptions import FLVERExportError
from soulstruct.blender.flver.models.types.enums import FLVERBoneDataType
from soulstruct.blender.flver.utilities import BONE_CoB_4x4
from soulstruct.blender.utilities.conversion import to_game
from soulstruct.blender.utilities.operators import LoggingOperator


def create_flver_bones(
    operator: LoggingOperator,
    context: bpy.types.Context,
    armature: bpy.types.ArmatureObject,
    flver: FLVER,
    bone_data_type: FLVERBoneDataType,
):
    """Create `FLVER` bones from Blender Armature bones.

    Bone transform data may be read from either EDIT mode (typical for rigged FLVERs like characters and objects) or
    CUSTOM mode (custom properties set on Blender `Bone`), according to `bone_data_type`.
    """

    bl_bone_names = [bone.name for bone in armature.data.bones]

    game_bones = []
    game_bone_parent_indices = []  # type: list[int]

    # It's more efficient to set all bones' local transforms at once from ALL of their armature-space transforms, so
    # we collect those here.
    game_arma_transforms = []  # type: list[tuple[Vector3, Matrix3, Vector3]]  # translate, rotate matrix, scale

    if len(set(bl_bone_names)) != len(bl_bone_names):
        # TODO: I think Blender already enforces this.
        raise FLVERExportError("Bone names in Blender Armature are not all unique.")

    # TODO: Check properties on data bone, not EditBone.
    #  Undo bone CoB transform.
    #  Always read scale from FLVER_BONE properties.

    for bl_bone in armature.data.bones:

        # We ALWAYS read (local) bone scale from stored properties, as EditBones cannot store scale.
        game_scale = to_game(Vector(bl_bone.FLVER_BONE.flver_scale))

        # Get FLVER bone name (remove dupe suffix).
        game_bone_name = bl_bone.name
        while re.match(r".*\.\d\d\d$", game_bone_name):
            # Bone names can be repeated in the FLVER. Remove Blender duplicate suffixes.
            game_bone_name = game_bone_name[:-4]
        while game_bone_name.endswith(" <DUPE>"):
            # Bone names can be repeated in the FLVER.
            game_bone_name = game_bone_name.removesuffix(" <DUPE>")

        bone_usage_flags = bl_bone.FLVER_BONE.get_flags()
        if (bone_usage_flags & FLVERBoneUsageFlags.UNUSED) != 0 and bone_usage_flags != 1:
            raise FLVERExportError(
                f"Bone '{bl_bone.name}' has 'Is Unused' enabled, but also has other usage flags set."
            )
        game_bone = FLVERBone(name=game_bone_name, usage_flags=bone_usage_flags)

        if bl_bone.parent:
            parent_bone_name = bl_bone.parent.name
            parent_bone_index = bl_bone_names.index(parent_bone_name)
        else:
            parent_bone_index = -1

        if bone_data_type == FLVERBoneDataType.EDIT:
            # Get armature-space bone transform from rig (characters and objects, typically).
            bl_bone_matrix = bl_bone.matrix_local @ BONE_CoB_4x4  # undo CoB transform
            game_arma_translate = to_game(bl_bone_matrix.translation)
            game_arma_rotmat = to_game(bl_bone_matrix.to_3x3())
            game_arma_transforms.append((game_arma_translate, game_arma_rotmat, game_scale))

        game_bones.append(game_bone)
        game_bone_parent_indices.append(parent_bone_index)

    # Assign game bone parent references. Child and sibling bones are done by caller using FLVER method.
    for game_bone, parent_index in zip(game_bones, game_bone_parent_indices):
        game_bone.parent_bone = game_bones[parent_index] if parent_index >= 0 else None

    operator.to_object_mode(context)

    if bone_data_type == FLVERBoneDataType.CUSTOM:
        # Get armature-space bone transform from PoseBone (map pieces).
        # Note that non-uniform bone scale is supported here (and is actually used in some old vanilla map pieces).
        for game_bone, bl_bone_name in zip(game_bones, bl_bone_names, strict=True):

            pose_bone = armature.pose.bones[bl_bone_name]

            game_arma_translate = to_game(pose_bone.location)
            if pose_bone.rotation_mode == "QUATERNION":
                bl_rot_quat = pose_bone.rotation_quaternion
                bl_rotmat = bl_rot_quat.to_matrix()
                game_arma_rotmat = to_game(bl_rotmat)
            elif pose_bone.rotation_mode == "XYZ":
                # TODO: Could this cause the same weird Blender gimbal lock errors as I was seeing with characters?
                #  If so, I may want to make sure I always set pose bone rotation to QUATERNION mode.
                bl_rot_euler = pose_bone.rotation_euler
                bl_rotmat = bl_rot_euler.to_matrix()
                game_arma_rotmat = to_game(bl_rotmat)
            else:
                raise FLVERExportError(
                    f"Unsupported rotation mode '{pose_bone.rotation_mode}' for bone '{pose_bone.name}'. Must be "
                    f"'QUATERNION' or 'XYZ' (Euler)."
                )
            game_arma_scale = to_game(pose_bone.scale)  # can be non-uniform
            game_arma_transforms.append(
                (
                    game_arma_translate,
                    game_arma_rotmat,
                    game_arma_scale,
                )
            )

    flver.bones = IDList(game_bones)
    # Auto-detect children and siblings from parent bones.
    flver.set_bone_children_siblings()  # only parents set in `create_bones`
    # Set bones' local transforms efficiently from all armature-space transforms.
    flver.set_bone_armature_space_transforms(game_arma_transforms)
