__all__ = [
    "GAME_TO_BL_QUAT",
    "BL_TO_GAME_QUAT",
    "GAME_TRS_TO_BL_MATRIX",
    "BL_MATRIX_TO_GAME_TRS",
    "get_armature_matrix",
    "get_basis_matrix",
]

from mathutils import Matrix, Euler, Quaternion as BlenderQuaternion

from soulstruct_havok.utilities.maths import Matrix3, TRSTransform, Quaternion as GameQuaternion

from io_soulstruct.utilities.conversion import GAME_TO_BL_VECTOR, BL_TO_GAME_VECTOR3


def GAME_TO_BL_QUAT(quaternion: GameQuaternion) -> BlenderQuaternion:
    """NOTE: Blender Euler rotation mode should be 'XYZ' (corresponding to game 'XZY')."""

    # TODO: Skipping stupid Euler route.
    # game_euler = quaternion.to_euler_angles(radians=True)
    # bl_euler = Euler((-game_euler.x, -game_euler.z, -game_euler.y))
    # return bl_euler.to_quaternion()

    return BlenderQuaternion((quaternion.w, -quaternion.x, -quaternion.z, -quaternion.y))


def BL_TO_GAME_QUAT(quaternion: BlenderQuaternion) -> GameQuaternion:
    """NOTE: Blender Euler rotation mode should be 'XYZ' (corresponding to game 'XZY')."""

    # TODO: Skipping stupid Euler route.
    # bl_euler = quaternion.to_euler("XYZ")
    # game_rotmat3 = Matrix3.from_euler_angles((-bl_euler.x, -bl_euler.z, -bl_euler.y), radians=True)
    # return GameQuaternion.from_matrix3(game_rotmat3)

    return GameQuaternion((-quaternion.x, -quaternion.z, -quaternion.y, quaternion.w))


def GAME_TRS_TO_BL_MATRIX(transform: TRSTransform) -> Matrix:
    """Convert a game `TRSTransform` to a Blender 4x4 `Matrix`."""
    bl_translate = GAME_TO_BL_VECTOR(transform.translation)
    bl_rotate = GAME_TO_BL_QUAT(transform.rotation)
    bl_scale = GAME_TO_BL_VECTOR(transform.scale)
    return Matrix.LocRotScale(bl_translate, bl_rotate, bl_scale)


def BL_MATRIX_TO_GAME_TRS(matrix: Matrix) -> TRSTransform:
    """Convert a Blender 4x4 homogenous `Matrix` to a game `TRSTransform`."""
    bl_translate, bl_rotate, bl_scale = matrix.decompose()
    game_translate = BL_TO_GAME_VECTOR3(bl_translate)
    game_rotate = BL_TO_GAME_QUAT(bl_rotate)
    game_scale = BL_TO_GAME_VECTOR3(bl_scale)
    return TRSTransform(game_translate, game_rotate, game_scale)


def get_armature_matrix(armature, bone_name: str, basis=None) -> Matrix:
    """Demonstrates how Blender calculates `pose_bone.matrix` (armature matrix) for `bone_name`.

    TODO: Likely needed at export to convert the curve keyframes (in basis space) back to armature space.

    Inverse of `get_basis_matrix()`.
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
    armature,
    bone_name: str,
    armature_matrix: Matrix,
    local_inv_matrices: dict[str, Matrix],
    armature_inv_matrices: dict[str, Matrix],
):
    """Get `pose_bone.matrix_basis` from `armature_matrix` by inverting Blender's process.

    Accepts `local_inv_matrix` and `armature_inv_matrices`, both indexed by bone name, to avoid recalculating the
    inverted matrices of multi-child bones.

    Inverse of `get_armature_matrix()`.
    """
    local_inv = local_inv_matrices.setdefault(
        bone_name,
        armature.data.bones[bone_name].matrix_local.inverted(),
    )
    parent_bone = armature.pose.bones[bone_name].parent

    if parent_bone is None:
        return local_inv @ armature_matrix
    else:
        parent_removed = armature_inv_matrices[parent_bone.name] @ armature_matrix
        return local_inv @ armature.data.bones[parent_bone.name].matrix_local @ parent_removed
