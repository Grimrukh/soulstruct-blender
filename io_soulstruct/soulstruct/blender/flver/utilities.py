from __future__ import annotations

__all__ = [
    "get_flvers_from_binder",
    "BONE_CoB_4x4",
    "BONE_CoB_QUAT",
    "game_bone_transform_to_bl_bone_matrix",
    "game_trs_to_bl_bone_trs",
    "bl_bone_trs_to_game_trs",
    "get_armature_matrix",
    "get_bone_object_parent_matrix",
    "game_forward_up_vectors_to_bl_euler",
    "bl_euler_to_game_forward_up_vectors",
    "bl_rotmat_to_game_forward_up_vectors",
    "flver_layout_to_pyrelink",
    "flver_material_to_pyrelink",
    "split_mesh_def_to_pyrelink",
    "vector2_to_pyrelink",
    "vector3_to_pyrelink",
    "dummy_to_pyrelink",
]

from pathlib import Path

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

from soulstruct.containers import Binder
from soulstruct.flver import *
from soulstruct.utilities.maths import EulerRad, Vector2, Vector3, Matrix3
from soulstruct.havok.utilities.maths import TRSTransform

import pyrelink.core as pyre_core
import pyrelink.flver as pyre_flver

from ..exceptions import *
from ..types import ArmatureObject
from ..utilities.conversion import to_blender, to_game, game_trs_to_bl_trs, bl_trs_to_game_trs


def get_flvers_from_binder(
    binder: Binder,
    file_path: Path,
    allow_multiple: bool = False,
    use_pyrelink_flver: bool  =True,
) -> list[FLVER]:
    """Find all FLVER files (with or without DCX) in `binder`.

    By default, only one FLVER file is allowed. If `allow_multiple` is True, multiple FLVER files will be returned.
    """
    flver_entries = binder.find_entries_by_name_regex(r".*\.flver(\.dcx)?")
    if not flver_entries:
        raise FLVERImportError(f"Cannot find a FLVER file in binder {file_path}.")
    elif not allow_multiple and len(flver_entries) > 1:
        raise FLVERImportError(f"Found multiple FLVER files in binder {file_path}. Only one is expected.")
    if use_pyrelink_flver:
        return [pyre_flver.FLVER.from_bytes(entry.get_uncompressed_data()) for entry in flver_entries]
    return [FLVER.from_binder_entry(entry) for entry in flver_entries]


# Swap X and Y, negate Z (to preserve handedness). Makes bones point nicely X-forward in Blender.
# This has to be carefully handled when posing animations.
BONE_CoB_4x4 = Matrix((
    (0.0, 1.0,  0.0, 0.0),
    (1.0, 0.0,  0.0, 0.0),
    (0.0, 0.0, -1.0, 0.0),
    (0.0, 0.0,  0.0, 1.0),
))

# The CoB is a PROPER rotation (determinant +1: the X/Y swap and the Z negation are each reflections, and their
# product is not), so it has an exact quaternion form and can be applied to a (translation, rotation, scale) triple
# without ever building a 4x4 matrix:
#     T @ R @ S @ CoB  ==  T @ (R @ CoB) @ (CoB^-1 @ S @ CoB)
# and for a signed permutation like this one, `CoB^-1 @ diag(s) @ CoB` is simply `diag(s.y, s.x, s.z)`. Applying the
# CoB this way (see `game_trs_to_bl_bone_trs()`) keeps negative scale intact, where `Matrix.decompose()` would
# re-factor it (see `utilities.conversion.game_trs_to_bl_trs()`).
BONE_CoB_QUAT = BONE_CoB_4x4.to_quaternion()
_BONE_CoB_QUAT_INV = BONE_CoB_QUAT.inverted()


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

    bl_transform = Matrix.LocRotScale(bl_translate, bl_rotmat, bl_scale)
    # Apply CoB matrix to swap X and Y and negate Z.
    return bl_transform @ BONE_CoB_4x4


def _permute_scale_for_cob(scale: Vector) -> Vector:
    """`CoB^-1 @ diag(scale) @ CoB` for `BONE_CoB_4x4`, i.e. swap the X and Y scale components. Self-inverse."""
    return Vector((scale.y, scale.x, scale.z))


def game_trs_to_bl_bone_trs(transform: TRSTransform) -> tuple[Vector, Quaternion, Vector]:
    """Convert a game `TRSTransform` (typically an HKX animation bone transform, local or armature-space) to the
    Blender `(translation, rotation, scale)` triple of the corresponding X-forward Blender bone, i.e. the TRS-level
    equivalent of `game_bone_transform_to_bl_bone_matrix(...).decompose()` -- but exact for negative scale, which
    matrix decomposition would silently re-factor (e.g. DSR c1200 animates `L Toe0Nub` with scale `(-1, 1, 1)`).

    Inverse of `bl_bone_trs_to_game_trs()`.
    """
    bl_translate, bl_rotate, bl_scale = game_trs_to_bl_trs(transform)
    return bl_translate, bl_rotate @ BONE_CoB_QUAT, _permute_scale_for_cob(bl_scale)


def bl_bone_trs_to_game_trs(translation: Vector, rotation: Quaternion, scale: Vector) -> TRSTransform:
    """Inverse of `game_trs_to_bl_bone_trs()`: undo the X-forward bone CoB at TRS level and convert to a game
    `TRSTransform`, preserving scale signs exactly."""
    return bl_trs_to_game_trs(translation, rotation @ _BONE_CoB_QUAT_INV, _permute_scale_for_cob(scale))


def get_armature_matrix(armature: ArmatureObject, bone_name: str, basis=None) -> Matrix:
    """Demonstrates how Blender calculates `pose_bone.matrix` (armature matrix) for `bone_name`.

    This function is not used by Soulstruct (as `pose_bone.matrix` can simply be read directly), but it is informative
    and inspired the shear-free `animation.utilities.get_basis_trs()`/`get_pose_trs_from_basis()` functions, which
    are conceptually (not literally, since they avoid 4x4 matrix algebra to stay shear-free) each other's inverse and
    are used for HKX animation import/export.
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


def get_bone_object_parent_matrix(bone: bpy.types.Bone) -> Matrix:
    """Return the armature-space matrix that Blender uses as the parent space of an Object whose `parent_type` is
    'BONE' and whose `parent_bone` is `bone`, at rest.

    This is NOT `bone.matrix_local`. Blender's `ob_parbone()` builds the parent matrix from the bone's POSE matrix
    (equal to `matrix_local` at rest) and then translates it along the bone's own +Y axis by `bone.length`, i.e. the
    parent origin is the bone's TAIL, not its head:

        parent_matrix = bone.matrix_local @ Matrix.Translation((0.0, bone.length, 0.0))

    An Object's `matrix_local` is relative to exactly this matrix (`matrix_world == parent_matrix @ matrix_local`
    for a bone-parented child of an unmoved Armature), so any code that computes a bone-relative `matrix_local`
    by hand -- or reads one back -- must use this function rather than `bone.matrix_local`.

    Note that `bone.matrix_local` here is the bone's Blender rest matrix, which for FLVER Armatures INCLUDES the
    X-forward `BONE_CoB_4x4` change of basis. The CoB must NOT be undone for this purpose (unlike for FLVER-space
    bone math), because Blender parents to the bone exactly as Blender sees it.

    `Bone.use_relative_parent` (never set by Soulstruct) would make Blender use the bone's basis/channel matrix
    instead; it is ignored here.
    """
    return bone.matrix_local @ Matrix.Translation((0.0, bone.length, 0.0))


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


# ------------------------------------------ #
# --- SOULSTRUCT -> PYRELINK CONVERSIONS --- #
# ------------------------------------------ #


def flver_layout_to_pyrelink(layout: VertexArrayLayout) -> pyre_flver.VertexArrayLayout:
    """Convert a soulstruct `VertexArrayLayout` (a list of typed `VertexDataType` members) into the equivalent
    `pyre_flver.VertexArrayLayout`.

    Only `write_types` are converted (i.e. `VertexIgnore` members, which have no pyrelink equivalent, are skipped).
    This is safe here because layouts passed to `to_split_mesh_def()` come from `MatDef.get_vertex_array_layout()`,
    which never generates `VertexIgnore` members (those only ever appear when repairing layouts read from existing,
    malformed FLVER files).
    """
    pr_types = []
    for data_type in layout.write_types:
        try:
            usage = pyre_flver.VertexUsage(data_type.type_int)
        except KeyError:
            raise FLVERExportError(
                f"Vertex data type '{data_type}' has no `pyre_flver.VertexUsage` equivalent."
            )
        pr_types.append(pyre_flver.VertexDataType(
            usage=usage,
            # `VertexDataFormatEnum` values are numerically identical to `pyre_flver.VertexDataFormat`.
            format=pyre_flver.VertexDataFormat(data_type.format_enum.value),
            instance_index=data_type.instance_index,
            unk_x00=data_type.unk_x00,
            data_offset=data_type.data_offset or 0,
        ))
    return pyre_flver.VertexArrayLayout(pr_types)


def flver_material_to_pyrelink(material: Material) -> pyre_flver.Material:
    """Convert a soulstruct `Material` (and its `Texture`s) into the equivalent `pyre_flver.Material`."""
    pr_material = pyre_flver.Material()
    pr_material.name = material.name
    pr_material.mat_def_path = material.mat_def_path
    pr_material.flags = material.flags
    pr_material.f2_unk_x18 = material.f2_unk_x18

    # NOTE: `Material.textures`/`.gx_items` are NOT live references -- each access returns a fresh Python list copy,
    # so appending to it directly (e.g. `pr_material.textures.append(...)`) is a silent no-op. We build plain lists
    # here and assign them all at once via the setters instead.
    pr_textures = []
    for texture in material.textures:
        pr_texture = pyre_flver.Texture()
        pr_texture.path = texture.path
        pr_texture.texture_type = texture.texture_type
        pr_texture.scale = pyre_core.Vector2(texture.scale.x, texture.scale.y)
        pr_texture.f2_unk_x10 = texture.f2_unk_x10
        pr_texture.f2_unk_x11 = texture.f2_unk_x11
        pr_texture.f2_unk_x14 = texture.f2_unk_x14
        pr_texture.f2_unk_x18 = texture.f2_unk_x18
        pr_texture.f2_unk_x1c = texture.f2_unk_x1c
        pr_textures.append(pr_texture)
    pr_material.textures = pr_textures

    pr_gx_items = []
    for gx_item in material.gx_items:
        pr_gx_item = pyre_flver.GXItem()
        pr_gx_item.category = gx_item.category
        pr_gx_item.index = gx_item.index
        pr_gx_item.data = gx_item.data
        pr_gx_items.append(pr_gx_item)
    pr_material.gx_items = pr_gx_items

    return pr_material


def split_mesh_def_to_pyrelink(split_mesh_def: SplitMeshDef) -> pyre_flver.SplitMeshDef:
    """Convert a soulstruct `SplitMeshDef` (material, layout, and per-submesh FLVER properties) into the equivalent
    `pyre_flver.SplitMeshDef`, for use with `pyre_flver.MergedMesh.split_mesh()`.
    """
    return pyre_flver.SplitMeshDef(
        material=flver_material_to_pyrelink(split_mesh_def.material),
        layout=flver_layout_to_pyrelink(split_mesh_def.layout),
        is_dynamic=split_mesh_def.is_dynamic,
        use_backface_culling=split_mesh_def.use_backface_culling,
        default_bone_index=split_mesh_def.default_bone_index,
        uses_bounding_boxes=split_mesh_def.uses_bounding_boxes,
        face_set_count=split_mesh_def.face_set_count,
        # TODO: `split_mesh_def.f0_unk_x46` (FLVER0-only, never seen non-zero) has no pyrelink equivalent yet.
        uv_layer_names=split_mesh_def.uv_layer_names or [],
    )


def vector2_to_pyrelink(v: Vector2) -> pyre_core.Vector2:
    """Convert a soulstruct `Vector2` into the equivalent `pyre_core.Vector2`."""
    return pyre_core.Vector2(v.x, v.y)


def vector3_to_pyrelink(v: Vector3) -> pyre_core.Vector3:
    """Convert a soulstruct `Vector3` into the equivalent `pyre_core.Vector3`."""
    return pyre_core.Vector3(v.x, v.y, v.z)


def dummy_to_pyrelink(dummy: Dummy) -> pyre_flver.Dummy:
    """Convert a soulstruct `Dummy` (already fully computed by `BlenderFLVERDummy.to_soulstruct_obj()`) into the
    equivalent `pyre_flver.Dummy`.
    """
    pr_dummy = pyre_flver.Dummy()
    pr_dummy.reference_id = dummy.reference_id
    pr_dummy.parent_bone_index = dummy.parent_bone_index
    pr_dummy.attach_bone_index = dummy.attach_bone_index
    pr_dummy.follows_attach_bone = dummy.follows_attach_bone
    pr_dummy.use_upward_vector = dummy.use_upward_vector
    pr_dummy.unk_x30 = dummy.unk_x30
    pr_dummy.unk_x34 = dummy.unk_x34
    pr_dummy.translate = vector3_to_pyrelink(dummy.translate)
    pr_dummy.forward = vector3_to_pyrelink(dummy.forward)
    pr_dummy.upward = vector3_to_pyrelink(dummy.upward)
    pr_dummy.color = pyre_core.Color4b(dummy.color.r, dummy.color.g, dummy.color.b, dummy.color.a)
    return pr_dummy
