from __future__ import annotations

__all__ = [
    "get_flvers_from_binder",
    "BONE_CoB_4x4",
    "game_bone_transform_to_bl_bone_matrix",
    "get_armature_matrix",
    "get_basis_matrix",
    "game_forward_up_vectors_to_bl_euler",
    "bl_euler_to_game_forward_up_vectors",
    "bl_rotmat_to_game_forward_up_vectors",
]

from pathlib import Path

import bpy
from mathutils import Euler, Matrix

from soulstruct.containers import Binder
from soulstruct.flver import FLVER
from soulstruct.utilities.maths import EulerRad, Vector3, Matrix3

from soulstruct.blender.utilities.conversion import to_blender, to_game
from soulstruct.blender.exceptions import *


def get_flvers_from_binder(
    binder: Binder,
    file_path: Path,
    allow_multiple=False,
) -> list[FLVER]:
    """Find all FLVER files (with or without DCX) in `binder`.

    By default, only one FLVER file is allowed. If `allow_multiple` is True, multiple FLVER files will be returned.
    """
    flver_entries = binder.find_entries_matching_name(r".*\.flver(\.dcx)?")
    if not flver_entries:
        raise FLVERImportError(f"Cannot find a FLVER file in binder {file_path}.")
    elif not allow_multiple and len(flver_entries) > 1:
        raise FLVERImportError(f"Found multiple FLVER files in binder {file_path}.")
    return [entry.to_binary_file(FLVER) for entry in flver_entries]


BONE_CoB_4x4 = Matrix((
    (0.0, 1.0,  0.0, 0.0),
    (1.0, 0.0,  0.0, 0.0),
    (0.0, 0.0, -1.0, 0.0),
    (0.0, 0.0,  0.0, 1.0),
))


def game_bone_transform_to_bl_bone_matrix(
    game_translate: Vector3,
    game_rotmat: Matrix3,
    game_scale: Vector3,
) -> Matrix:
    """Convert a game bone transform to a Blender bone matrix.

    This is the same as `to_blender()` but with an additional CoB matrix applied (swapping X and Y and negating Z). This
    is necessary to make Blender bones appear "X-forward" for FromSoft connectedness.

    Can be called on local or armature-space coordinates; the output will match the input.
    """
    bl_translate = to_blender(game_translate)
    bl_rotmat = to_blender(game_rotmat)
    bl_scale = to_blender(game_scale)
    bl_transform = Matrix.Translation(bl_translate) @ bl_rotmat.to_4x4()
    for i in range(3):
        bl_transform[i][i] *= bl_scale[i]
    # Apply CoB matrix to swap X and Y and negate Z.
    return bl_transform @ BONE_CoB_4x4


def get_armature_matrix(armature: bpy.types.ArmatureObject, bone_name: str, basis=None) -> Matrix:
    """Demonstrates how Blender calculates `pose_bone.matrix` (armature matrix) for `bone_name`.

    This function is not used by Soulstruct (as `pose_bone.matrix` can simply be read directly), but it is informative
    and assisted with the actually-required `get_basis_matrix()` function below, which is the inverse of this function
    and is used for HKX animation import.
    """
    local = armature.data.bones[bone_name].matrix_local
    if basis is None:
        basis = armature.pose.bones[bone_name].matrix_basis

    parent = armature.pose.bones[bone_name].parent
    if parent is None:  # root bone is simple
        # armature = local @ basis
        return local @ basis
    else:
        # Apply relative transform of local (edit bone) from parent and then armature position of parent:
        #     armature = parent_armature @ (parent_local.inv @ local) @ basis
        #  -> basis = (parent_local.inv @ local)parent_local @ parent_armature.inv @ armature
        parent_local = armature.data.bones[parent.name].matrix_local
        return get_armature_matrix(armature, parent.name) @ parent_local.inverted() @ local @ basis


def get_basis_matrix(
    armature: bpy.types.ArmatureObject,
    bone_name: str,
    armature_matrix: Matrix,
    armature_inv_matrices: dict[str, Matrix],
    cached_local_inv_matrices: dict[str, Matrix],
):
    """Get the appropriate matrix to assign to `pose_bone.matrix_basis` from `armature_matrix` by inverting Blender's
    process (see `get_armature_matrix()`).

    Args:
        armature: Armature object containing `bone_name`.
        bone_name: Name of the pose bone for which to get the basis matrix.
        armature_matrix: The desired armature matrix for `bone_name` (i.e., `pose_bone.matrix`).
        armature_inv_matrices: Dictionary mapping bone names to their armature matrices inverted. Used to avoid
            recalculating the inverted matrices of multi-child bones.
        cached_local_inv_matrices: Dictionary mapping bone names to their local matrices inverted. Used to avoid
            recalculating the inverted matrices of multi-child bones.

    Inverse of `get_armature_matrix()`.
    """
    if bone_name not in cached_local_inv_matrices:
        cached_local_inv_matrices[bone_name] = armature.data.bones[bone_name].matrix_local.inverted()
    local_inv = cached_local_inv_matrices[bone_name]
    parent_bone = armature.pose.bones[bone_name].parent

    if parent_bone is None:
        return local_inv @ armature_matrix

    parent_removed = armature_inv_matrices[parent_bone.name] @ armature_matrix
    return local_inv @ armature.data.bones[parent_bone.name].matrix_local @ parent_removed


def game_forward_up_vectors_to_bl_euler(forward: Vector3, up: Vector3) -> Euler:
    """Convert `forward` and `up` vectors to Blender Euler (for FLVER dummies)."""
    right = up.cross(forward)
    rotation_matrix = Matrix3([
        [right.x, up.x, forward.x],
        [right.y, up.y, forward.y],
        [right.z, up.z, forward.z],
    ])
    game_euler = rotation_matrix.to_euler_angles_rad()
    return to_blender(game_euler)


def bl_euler_to_game_forward_up_vectors(bl_euler: Euler) -> tuple[Vector3, Vector3]:
    """Convert a Blender `Euler` to its forward-axis and up-axis vectors in game space (for FLVER dummies)."""
    game_euler = to_game(bl_euler)  # type: EulerRad
    game_mat = Matrix3.from_euler_angles_rad(game_euler)
    forward = Vector3((game_mat[0][2], game_mat[1][2], game_mat[2][2]))  # third column (Z)
    up = Vector3((game_mat[0][1], game_mat[1][1], game_mat[2][1]))  # second column (Y)
    return forward, up


def bl_rotmat_to_game_forward_up_vectors(bl_rotmat: Matrix) -> tuple[Vector3, Vector3]:
    """Convert a Blender `Matrix` to its game equivalent's forward-axis and up-axis vectors (for FLVER dummies)."""
    game_mat = to_game(bl_rotmat)  # type: Matrix3
    forward = Vector3((game_mat[0][2], game_mat[1][2], game_mat[2][2]))  # third column (Z)
    up = Vector3((game_mat[0][1], game_mat[1][1], game_mat[2][1]))  # second column (Y)
    return forward, up
