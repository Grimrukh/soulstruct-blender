"""Functions to create EditBones from game armature-space rest transforms with a change-of-basis (CoB)."""
from __future__ import annotations

__all__ = [
    "create_edit_bones",
    "write_flver_rest_pose_to_edit_bones",
    "write_data_to_custom_bone_prop_and_pose",
]

import math
import typing as tp

import bpy
from mathutils import Vector

from soulstruct.flver import FLVER, FLVERBone
from soulstruct.utilities.maths import Vector3

from soulstruct.blender.flver.utilities import game_bone_transform_to_bl_bone_matrix
from soulstruct.blender.utilities.conversion import to_blender
from soulstruct.blender.utilities.operators import LoggingOperator
from soulstruct.blender.utilities.misc import is_uniform


def create_edit_bones(
    flver: FLVER,
    armature_data: bpy.types.Armature,
    bl_bone_names: list[str],
) -> list[bpy.types.EditBone]:
    """Create all edit bones from FLVER bones in `bl_armature` and return them.

    Note that the returned bones will become invalid when exiting EDIT mode, so they should be used immediately.
    """
    edit_bones = []  # all bones
    for game_bone, bl_bone_name in zip(flver.bones, bl_bone_names, strict=True):
        game_bone: FLVERBone
        edit_bone = armature_data.edit_bones.new(bl_bone_name)  # '<DUPE>' suffixes already added to names
        edit_bone: bpy.types.EditBone

        # Default head/tail (will be overwritten later with any true rest pose data).
        edit_bone.head = Vector((0.0, 0.0, 0.0))
        edit_bone.tail = Vector((0.0, 0.2, 0.0))  # standard Blender Y-forward (no CoB here)

        # If this is `False`, then a bone's rest pose rotation will NOT affect its relative pose basis translation.
        # That is, a standard TRS transform becomes an 'RTS' transform instead. We don't want such behavior,
        # particularly for FLVER root bones like 'Pelvis'.
        edit_bone.use_local_location = True

        # FLVER bones never inherit scale.
        edit_bone.inherit_scale = "NONE"

        # We don't bother storing child or sibling bones. They are generated from parents on export.
        edit_bones.append(edit_bone)

    # Set parent relationships. Any FLVER can have a true bone hierarchy. (For Map Pieces, this just means that child
    # bone transforms are relative to parents.)
    for game_bone, edit_bone in zip(flver.bones, edit_bones, strict=True):
        if game_bone.parent_bone:
            # Set bone parent in Blender.
            parent_bone_index = game_bone.parent_bone.get_bone_index(flver.bones)
            parent_edit_bone = edit_bones[parent_bone_index]
            edit_bone.parent = parent_edit_bone
            # edit_bone.use_connect = True

    return edit_bones


def write_flver_rest_pose_to_edit_bones(
    operator: LoggingOperator,
    flver: FLVER,
    edit_bones: list[bpy.types.EditBone],
):
    """
    Create EditBones from game armature-space rest transforms with a right-multiplied CoB matrix that swaps X and Y
    (making Blender bones appear "X-forward" for FromSoft connectedness) and negates Z (to avoid reflection). This
    applies *after* (in *addition to*) our standard coordinate space transformation between FromSoft and Blender; the
    same is done for pose bone animation later.

    Args:
        operator: LoggingOperator to report errors/warnings.
        flver: FLVER containing bones.
        edit_bones: List to populate with created EditBones.
    """
    game_arma_transforms = flver.get_bone_armature_space_transforms()

    nub_bones = _NubBoneManager(flver.bones)

    for game_bone, edit_bone, game_arma_transform in zip(
        flver.bones, edit_bones, game_arma_transforms, strict=True
    ):
        game_bone: FLVERBone
        game_translate, game_rotmat, game_scale = game_arma_transform
        _check_scale(operator, game_scale, game_bone.name, flver.path_stem)

        # Non-zero length required before we can manipulate `matrix` (which sets head/tail/roll automatically).
        edit_bone.head = Vector((0.0, 0.0, 0.0))
        edit_bone.tail = Vector((0.0, 0.1, 0.0))

        edit_bone.matrix = game_bone_transform_to_bl_bone_matrix(game_translate, game_rotmat, Vector3((1.0, 1.0, 1.0)))

        # Set length (child bone, root stub, nub bone, or unknown stub).
        if game_bone.child_bone:
            edit_bone.length = max(abs(game_bone.child_bone.translate), 0.01)  # avoid zero length
        elif not game_bone.parent_bone:
            # Short stub (unlikely to be animated).
            edit_bone.length = 0.05
        else:
            nub_bone = nub_bones[game_bone]
            if nub_bone:
                # Nub bone gives length of our true leaf bone.
                edit_bone.length = max(abs(nub_bone.translate), 0.01)  # avoid zero length
            else:
                # Unknown stub (slightly larger as it may actually be posed later).
                edit_bone.length = 0.1


def write_data_to_custom_bone_prop_and_pose(
    flver: FLVER,
    armature: bpy.types.ArmatureObject,
):
    """
    Write FLVER bone rest pose data to custom bone properties (to ensure correct transfer) and pose bones for immediate
    correct model display.

    Typically used by Map Pieces, which often use bones to position vertex groups such as copy-pasted plants. Some
    annoying map pieces also use bones for larger components like buildings. These bones may also be in a true hierarchy
    (e.g. in m12_01_00_00 in Dark Souls), not just flat.
    """
    bl_bone_transforms = []
    for game_bone in flver.bones:
        # Note that we store the local bone transforms directly, without accumulating parent transforms (unlike when
        # writing Edit Bone transforms). Final pose calculations will be done by Blender automatically.
        bl_bone_location = to_blender(game_bone.translate)
        bl_bone_rotation_euler = to_blender(game_bone.rotate)
        bl_bone_scale = to_blender(game_bone.scale)
        bl_bone_transforms.append((bl_bone_location, bl_bone_rotation_euler, bl_bone_scale))

    for bl_bone_transform, bl_bone in zip(bl_bone_transforms, armature.data.bones, strict=True):
        # Edit bones are left as Blender Y-forward stubs (no CoB).
        # This rigging makes map piece 'pose' bone data transform as expected for showing accurate vertex positions.
        bl_bone.FLVER_BONE.flver_translate = bl_bone_transform[0]
        bl_bone.FLVER_BONE.flver_rotate = bl_bone_transform[1]  # Euler angles (Blender coordinates)
        bl_bone.FLVER_BONE.flver_scale = bl_bone_transform[2]

    pose_bones = armature.pose.bones
    for bl_bone_transform, pose_bone in zip(bl_bone_transforms, pose_bones):
        # TODO: Pose bone transforms are relative to parent (in both FLVER and Blender).
        #  Confirm map pieces still behave as expected, though (they shouldn't even have child bones).
        pose_bone.rotation_mode = "QUATERNION"  # should already be default, but being explicit
        pose_bone.location = bl_bone_transform[0]
        pose_bone.rotation_quaternion = bl_bone_transform[1].to_quaternion()
        pose_bone.scale = bl_bone_transform[2]


class _NubBoneManager:

    nub_bones: dict[str, FLVERBone]

    def __init__(self, bones: tp.Sequence[FLVERBone]):
        self.nub_bones = {
            bone.name: bone
            for bone in bones
            if bone.name.endswith("Nub")
        }

    def __getitem__(self, bone: FLVERBone) -> FLVERBone | None:
        """Recursively search up skeleton for a matching Nub bone name.

        e.g. bone 'R Finger02' with parent 'R Finger0' might use 'R Finger0Nub'.
        """
        nub_name = f"{bone.name}Nub"
        if nub_name in self.nub_bones:
            return self.nub_bones[nub_name]
        elif bone.parent_bone is not None:
            return self.__getitem__(bone.parent_bone)
        return None  # no Nub bone found


def _check_scale(operator: LoggingOperator, game_scale: Vector3, bone_name: str, flver_name: str):
    """Check bone scale for issues. Return `True` if scale is uniform identity and `False` if not."""
    if not is_uniform(game_scale, rel_tol=0.001):
        operator.warning(
            f"Bone {bone_name} in FLVER {flver_name} has non-uniform scale: {game_scale}. "
            f"This is unsupported in Blender. Storing on custom property."
        )
    elif any(c < 0.0 for c in game_scale):
        operator.warning(
            f"Bone {bone_name} in FLVER {flver_name} has negative scale: {game_scale}. "
            f"This is unsupported in Blender. Storing on custom property."
        )
    elif math.isclose(game_scale.x, 1.0, rel_tol=0.001):
        # Bone scale is ALMOST uniform and 1. We don't warn.
        pass
    else:
        operator.warning(
            f"Bone {bone_name} in FLVER {flver_name} has uniform but non-identity scale: {game_scale}. "
            f"This is unsupported in Blender. Storing on custom property."
        )
