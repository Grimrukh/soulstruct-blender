from __future__ import annotations

__all__ = [
    "create_bl_flver_from_flver",
]

import typing as tp
from dataclasses import dataclass, field

import math
import numpy as np
import time

import bpy
from mathutils import Vector

from soulstruct.base.models.flver import *
from soulstruct.base.models.shaders import MatDefError

from io_soulstruct.flver.material.types import BlenderFLVERMaterial
from io_soulstruct.flver.models.properties import FLVERImportSettings
from io_soulstruct.utilities import *

from ..bl_flver_dummy import BlenderFLVERDummy
from ..enums import FLVERBoneDataType
from ._create_materials import create_materials

if tp.TYPE_CHECKING:
    from io_soulstruct.flver.image.image_import_manager import ImageImportManager
    from .core import BlenderFLVER


@dataclass(slots=True)
class _CreateBlenderFLVERCommand:
    """Shared state used frequently across the sub-functions in `BlenderFLVER` creation.

    All parameters specified by caller, except for stored FLVER import settings.
    """

    operator: LoggingOperator
    context: bpy.types.Context
    flver: FLVER
    name: str
    collection: bpy.types.Collection = None
    image_import_manager: ImageImportManager | None = None
    existing_merged_mesh: MergedMesh = None
    existing_bl_materials: tp.Sequence[BlenderFLVERMaterial] = None

    import_settings: FLVERImportSettings = field(default=None, init=False)

    def __post_init__(self):
        if self.existing_merged_mesh and not self.existing_bl_materials:
            raise ValueError("If `existing_merged_mesh` is given, `existing_bl_materials` must also be given.")
        elif not self.existing_merged_mesh and self.existing_bl_materials:
            raise ValueError("If `existing_bl_materials` are given, `existing_merged_mesh` must also be given.")

        if not self.collection:
            self.collection = self.context.scene.collection

        self.import_settings = self.context.scene.flver_import_settings


def create_bl_flver_from_flver(
    cls: type[BlenderFLVER],
    operator: LoggingOperator,
    context: bpy.types.Context,
    flver: FLVER,
    name: str,
    collection: bpy.types.Collection = None,
    image_import_manager: ImageImportManager | None = None,
    existing_merged_mesh: MergedMesh = None,
    existing_bl_materials: tp.Sequence[BlenderFLVERMaterial] = None,
) -> BlenderFLVER:

    command = _CreateBlenderFLVERCommand(
        operator,
        context,
        flver,
        name,
        collection=collection,
        image_import_manager=image_import_manager,
        existing_merged_mesh=existing_merged_mesh,
        existing_bl_materials=existing_bl_materials,
    )

    armature, bl_bone_data_type, bl_bone_names = _create_armature(command)

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

    mesh_data = bpy.data.meshes.new(name=command.name)

    bl_materials, mesh = _create_bl_mesh(command, armature, bl_bone_names, mesh_data)

    command.collection.objects.link(mesh)
    for bl_material in bl_materials:
        mesh.data.materials.append(bl_material.material)

    if armature:
        # Parent mesh to armature. This is critical for proper animation behavior (especially with root motion).
        mesh.parent = armature
        _create_mesh_armature_modifier(mesh, armature)

        # Armature is always created if there are Dummies, so we can safely create them here.
        for i, dummy in enumerate(command.flver.dummies):
            dummy_name = BlenderFLVERDummy.format_name(command.name, i, dummy.reference_id, suffix=None)
            BlenderFLVERDummy.new_from_soulstruct_obj(
                command.operator,
                command.context,
                dummy,
                name=dummy_name,
                armature=armature,
                collection=command.collection,
            )

    bl_flver = cls(mesh)
    bl_flver.obj.FLVER.bone_data_type = bl_bone_data_type.value

    # Assign FLVER header properties.
    bl_flver.big_endian = command.flver.big_endian

    if command.flver.version in {FLVERVersion.DemonsSouls_0x10, FLVERVersion.DemonsSouls_0x14}:
        # We convert this to "DemonsSouls", since we can't export non-strip triangles for old versions (AFAIK).
        # Obviously, Demon's Souls can handle the newer version and you probably want it anyway.
        bl_flver.version = FLVERVersion.DemonsSouls.name
        command.operator.warning(
            f"Upgrading FLVER version {command.flver.version} to standard Demon's Souls version (0x15)."
        )
    else:
        try:
            bl_flver.version = command.flver.version.name
        except TypeError:
            command.operator.warning(
                f"FLVER version '{command.flver.version}' not recognized. Leaving as 'Selected Game'."
            )

    bl_flver.unicode = command.flver.unicode

    bl_flver.f0_unk_x4a = command.flver.f0_unk_x4a
    bl_flver.f0_unk_x4b = command.flver.f0_unk_x4b
    bl_flver.f0_unk_x4c = command.flver.f0_unk_x4c
    bl_flver.f0_unk_x5c = command.flver.f0_unk_x5c

    bl_flver.f2_unk_x4a = command.flver.f2_unk_x4a
    bl_flver.f2_unk_x4c = command.flver.f2_unk_x4c
    bl_flver.f2_unk_x5c = command.flver.f2_unk_x5c
    bl_flver.f2_unk_x5d = command.flver.f2_unk_x5d
    bl_flver.f2_unk_x68 = command.flver.f2_unk_x68

    bl_flver.mesh_vertices_merged = command.import_settings.merge_mesh_vertices

    return bl_flver  # might be used by other importers


def _create_bl_mesh(
    command: _CreateBlenderFLVERCommand,
    armature: bpy.types.ArmatureObject,
    bl_bone_names: list[str],
    mesh_data: bpy.types.Mesh,
) -> tuple[list[BlenderFLVERMaterial], bpy.types.MeshObject]:
    if not command.flver.meshes:
        # FLVER has no meshes (e.g. c0000). Leave empty.
        mesh = new_mesh_object(f"{command.name} <EMPTY>", mesh_data, SoulstructType.FLVER)
        return [], mesh

    if any(mesh.invalid_layout for mesh in command.flver.meshes):
        # Corrupted meshes (e.g. some DS1R map pieces) that couldn't be fixed by `FLVER` class. Leave empty.
        mesh = new_mesh_object(f"{command.name} <INVALID>", mesh_data, SoulstructType.FLVER)
        return [], mesh

    if command.existing_merged_mesh:
        # Merged mesh already given. Implies that Blender materials are handled manually as well.
        bl_vert_bone_weights, bl_vert_bone_indices = _create_bl_mesh_from_merged_mesh(
            command.operator, mesh_data, command.existing_merged_mesh
        )
        mesh = new_mesh_object(command.name, mesh_data, SoulstructType.FLVER)
        if armature:
            _create_bone_vertex_groups(mesh, bl_bone_names, bl_vert_bone_weights, bl_vert_bone_indices)
        return list(command.existing_bl_materials), mesh

    # Create materials and `MergedMesh` now.
    try:
        bl_materials, mesh_bl_material_indices, bl_material_uv_layer_names = create_materials(
            command.operator,
            command.context,
            command.flver,
            model_name=command.name,
            material_blend_mode=command.import_settings.material_blend_mode,
            image_import_manager=command.image_import_manager,
            # No cached MatDef materials to pass in.
        )

    except MatDefError:
        # No materials will be created! TODO: Surely not.
        bl_materials = []
        mesh_bl_material_indices = ()
        bl_material_uv_layer_names = ()

    p = time.perf_counter()
    # Create merged mesh.
    merged_mesh = command.flver.to_merged_mesh(
        mesh_bl_material_indices,
        material_uv_layer_names=bl_material_uv_layer_names,
        merge_vertices=command.import_settings.merge_mesh_vertices,
    )
    command.operator.debug(f"Merged FLVER meshes in {time.perf_counter() - p} s")
    if command.import_settings.merge_mesh_vertices:
        # Report vertex reduction.
        total_vertices = sum(len(mesh.vertices) for mesh in command.flver.meshes)
        total_merged_vertices = merged_mesh.vertex_data.shape[0]
        command.operator.debug(
            f"Merging reduced {total_vertices} vertices to {total_merged_vertices} "
            f"({100 - 100 * total_merged_vertices / total_vertices:.2f}% reduction)"
        )
    bl_vert_bone_weights, bl_vert_bone_indices = _create_bl_mesh_from_merged_mesh(
        command.operator, mesh_data, merged_mesh
    )
    mesh = new_mesh_object(command.name, mesh_data, SoulstructType.FLVER)
    if armature:
        _create_bone_vertex_groups(mesh, bl_bone_names, bl_vert_bone_weights, bl_vert_bone_indices)

    return bl_materials, mesh


def _create_armature(
    command: _CreateBlenderFLVERCommand
) -> tuple[bpy.types.ArmatureObject | None, FLVERBoneDataType, list[str]]:
    if (
        command.import_settings.omit_default_bone
        and not command.flver.dummies
        and len(command.flver.bones) == 1
        and command.flver.bones[0].is_default_origin
    ):
        # Single default bone can be auto-created on export. No Blender Armature parent needed/created.
        return None, FLVERBoneDataType.OMITTED, []

    # Create FLVER bone index -> Blender bone name dictionary. (Blender names are UTF-8.)
    # This is done even when `existing_armature` is given, as the order of bones in this new FLVER may be
    # different and the vertex weight indices need to be directed to the names of bones in `existing_armature`
    # correctly.

    bl_bone_names = []
    for bone in command.flver.bones:
        # Just using actual bone names to avoid the need for parsing rules on export. However, duplicate names
        # need to be handled with suffixes.
        bl_bone_name = f"{bone.name} <DUPE>" if bone.name in bl_bone_names else bone.name
        bl_bone_names.append(bl_bone_name)

    # Create Blender Armature. We have to do this first so mesh vertices can be weighted to its bones.
    command.operator.to_object_mode()
    command.operator.deselect_all()
    armature = new_armature_object(f"{command.name} Armature", bpy.data.armatures.new(f"{command.name} Armature"))
    command.collection.objects.link(armature)  # needed before creating EditBones!
    bl_bone_data_type = _create_bl_bones(command, armature, bl_bone_names)
    return armature, bl_bone_data_type, bl_bone_names


def _create_mesh_armature_modifier(bl_mesh: bpy.types.MeshObject, bl_armature: bpy.types.ArmatureObject):
    armature_mod = bl_mesh.modifiers.new(name="FLVER Armature", type="ARMATURE")
    armature_mod.object = bl_armature
    armature_mod.show_in_editmode = True
    armature_mod.show_on_cage = True


def _create_bl_mesh_from_merged_mesh(
    operator: LoggingOperator,
    mesh_data: bpy.types.Mesh,
    merged_mesh: MergedMesh,
) -> tuple[np.ndarray, np.ndarray]:
    """Create Blender Mesh with plenty of efficient `foreach_set()` calls to raveled `MergedMesh` arrays.

    Returns two arrays of bone indices and bone weights for the created Blender vertices.
    """

    # p = time.perf_counter()

    merged_mesh.swap_vertex_yz(tangents=False, bitangents=False)
    merged_mesh.invert_vertex_uv(invert_u=False, invert_v=True)
    merged_mesh.normalize_normals()

    # We can create vertices before `BMesh` easily.
    vertex_count = merged_mesh.vertex_data.shape[0]
    mesh_data.vertices.add(vertex_count)
    mesh_data.vertices.foreach_set("co", np.array(merged_mesh.vertex_data["position"]).ravel())

    all_faces = merged_mesh.faces[:, :3]  # drop material index column (N x 3 array)
    if merged_mesh.vertices_merged:
        # Retrieve true (merged) vertex indices used by each face loop indexed in `merged_mesh.faces`.
        # Note that `face_vertex_indices` has the exact same shape as `all_faces` (N x 3).
        face_vertex_indices = merged_mesh.loop_vertex_indices[all_faces]
    else:
        # No vertex merging occurred, so FLVER 'loops' and 'vertices' are still synonymous.
        face_vertex_indices = all_faces

    # Drop faces that don't use three unique vertex indices.
    # TODO: Try a vectorized approach that calculates the difference between each pair of the three columns, then
    #  takes the product of those differences. Any row that ends up with zero is degenerate.
    unique_mask = np.apply_along_axis(lambda row: len(np.unique(row)) == 3, 1, face_vertex_indices)  # 1D array (N)
    valid_face_vertex_indices = face_vertex_indices[unique_mask]  # N' x 3 array
    valid_face_material_indices = merged_mesh.faces[:, 3][unique_mask]  # 1D array (N')

    valid_face_count = valid_face_vertex_indices.shape[0]  # N'
    invalid_face_count = face_vertex_indices.shape[0] - valid_face_count  # N - N'
    if invalid_face_count > 0:
        operator.info(f"Removed {invalid_face_count} invalid/degenerate mesh faces from {mesh_data.name}.")

    # Directly assign face corner (loop) vertex indices.
    mesh_data.loops.add(valid_face_vertex_indices.size)
    mesh_data.loops.foreach_set("vertex_index", valid_face_vertex_indices.ravel())

    # Create triangle polygons.
    # Blender polygons are defined by loop start and count (total), which is entirely on-rails here for triangles.
    loop_starts = np.arange(0, valid_face_count * 3, 3, dtype=np.int32)  # just [0, 3, 6, ...]
    loop_totals = np.full(valid_face_count, 3, dtype=np.int32)  # all triangles (3)
    mesh_data.polygons.add(valid_face_count)
    mesh_data.polygons.foreach_set("loop_start", loop_starts)
    mesh_data.polygons.foreach_set("loop_total", loop_totals)
    mesh_data.polygons.foreach_set("material_index", valid_face_material_indices)

    mesh_data.update(calc_edges=True)

    # self.operator.info(f"Created Blender mesh in {time.perf_counter() - p} s")

    valid_face_loop_indices = all_faces[unique_mask].ravel()

    # Create and populate UV and vertex color data layers (on loops).
    for i, (uv_layer_name, merged_loop_uv_array) in enumerate(merged_mesh.loop_uvs.items()):
        # self.operator.info(f"Creating UV layer {i}: {uv_layer_name}")
        uv_layer = mesh_data.uv_layers.new(name=uv_layer_name, do_init=False)
        loop_uv_data = merged_loop_uv_array[valid_face_loop_indices].ravel()
        uv_layer.data.foreach_set("uv", loop_uv_data)
    for i, merged_color_array in enumerate(merged_mesh.loop_vertex_colors):
        # self.operator.info(f"Creating Vertex Colors layer {i}: VertexColors{i}")
        # TODO: Apparently `vertex_colors` is deprecated in favor of "color attributes". Investigate.
        color_layer = mesh_data.vertex_colors.new(name=f"VertexColors{i}")
        loop_color_data = merged_color_array[valid_face_loop_indices].ravel()
        color_layer.data.foreach_set("color", loop_color_data)

    # Some FLVERs (e.g. c2120, 'Shadowlurker' in Demon's Souls) have materials that reference UV layers (with real
    # included textures) that are not actually used by any Mesh. The game's `MatDef` will handle these special cases
    # and ensure that Blender doesn't look for them on export, even if they appear in the shader's node tree.

    # NOTE: `Mesh.create_normals_split()` was removed in Blender 4.1, and I no longer support older versions than
    # that. New versions of Blender automatically create the `mesh.corner_normals` collection. We also don't need to
    # enable `use_auto_smooth` or call `calc_normals_split()` anymore.

    loop_normal_data = merged_mesh.loop_normals[valid_face_loop_indices]  # NOT raveled
    mesh_data.normals_split_custom_set(loop_normal_data)  # one normal per loop
    mesh_data.update()

    return merged_mesh.vertex_data["bone_weights"], merged_mesh.vertex_data["bone_indices"]


def _create_bone_vertex_groups(
    mesh: bpy.types.MeshObject,
    bl_bone_names: list[str],
    bl_vert_bone_weights: np.ndarray,
    bl_vert_bone_indices: np.ndarray,
):
    # Naming a vertex group after a Blender bone will automatically link it in the Armature modifier below.
    # NOTE: For imports that use an existing Armature (e.g. equipment), invalid bone names such as the root dummy
    # equipment bones have already been removed from `bl_bone_names` here. TODO: I think this note is outdated.
    bone_vertex_groups = [
        mesh.vertex_groups.new(name=bone_name)
        for bone_name in bl_bone_names
    ]  # type: list[bpy.types.VertexGroup]

    # Awkwardly, we need a separate call to `bone_vertex_groups[bone_index].add(indices, weight)` for each combo
    # of `bone_index` and `weight`, so the dictionary keys constructed below are a tuple of those two to minimize
    # the number of `VertexGroup.add()` calls needed at the end of this function.
    bone_vertex_group_indices = {}  # type: dict[tuple[int, float], list[int]]

    # p = time.perf_counter()
    # TODO: Can probably be vectorized better with NumPy.
    for v_i, (bone_indices, bone_weights) in enumerate(zip(bl_vert_bone_indices, bl_vert_bone_weights)):
        if all(weight == 0.0 for weight in bone_weights) and len(set(bone_indices)) == 1:
            # Map Piece FLVERs use a single duplicated index and no weights.
            # TODO: May be able to assert that this is ALWAYS true for ALL vertices in map pieces.
            v_bone_index = bone_indices[0]
            bone_vertex_group_indices.setdefault((v_bone_index, 1.0), []).append(v_i)
        else:
            # Standard multi-bone weighting.
            for v_bone_index, v_bone_weight in zip(bone_indices, bone_weights):
                if v_bone_weight == 0.0:
                    continue
                bone_vertex_group_indices.setdefault((v_bone_index, v_bone_weight), []).append(v_i)

    for (bone_index, bone_weight), bone_vertices in bone_vertex_group_indices.items():
        bone_vertex_groups[bone_index].add(bone_vertices, bone_weight, "ADD")

    # self.operator.info(f"Assigned Blender vertex groups to bones in {time.perf_counter() - p} s")


def _create_bl_bones(
    command: _CreateBlenderFLVERCommand,
    armature: bpy.types.ArmatureObject,
    bl_bone_names: list[str],
) -> FLVERBoneDataType:
    """Create FLVER bones on given `bl_armature_obj` in Blender.

    Bones can be a little confusing in Blender. See:
        https://docs.blender.org/api/blender_python_api_2_71_release/info_gotcha.html#editbones-posebones-bone-bones

    The short story is that the "resting state" of each bone, including its head and tail position, is created in
    EDIT mode (as `EditBone` instances). This data defines the "zero deformation" state of the mesh with regard to
    bone weights, and will typically not be edited again when posing/animating a mesh that is rigged to this
    Armature. Instead, the bones are accessed as `PoseBone` instances in POSE mode, where they are treated like
    objects with transform data.

    If a FLVER bone has a parent bone, its FLVER transform is given relative to its parent's frame of reference.
    Determining the final position of any given bone in world space therefore requires all of its parents'
    transforms to be accumulated up to the root. (The same is true for HKX animation coordinates, which are local
    bone transformations in the same coordinate system.)

    Note that while bones are typically used for obvious animation cases in characters, objects, and parts (e.g.
    armor/weapons), they are also occasionally used in a fairly basic way by map pieces to position certain vertices
    in certain meshes. When this happens, so far, the bones have always been root bones, and basically function as
    shifted origins for the coordinates of certain vertices. I strongly suspect, but have not absolutely confirmed,
    that the `is_bind_pose` attribute of each mesh indicates whether FLVER bone data should be written to the
    EditBone (`is_bind_pose=True`) or PoseBone (`is_bind_pose=False`). Of course, we have to decide for each BONE,
    not each mesh, so currently I am enforcing that `is_bind_pose=False` for ALL meshes in order to write the bone
    transforms to PoseBone rather than EditBone. A warning will be logged if only some of them are `False`.

    The AABB of each bone is presumably generated to include all vertices that use that bone as a weight.

    The detected `FLVERBoneDataType` is returned, which indicates whether bone data was written to `EditBones` or
    `PoseBones`. This is saved to FLVER properties in Blender for export.
    """

    # Detect bone data type (storage location) based on FLVER mesh `is_bind_pose` state.
    if command.flver.any_bind_pose():
        if not command.flver.all_bind_pose():
            command.operator.warning(
                "Some FLVER meshes are in bind pose and some are not. Cannot currently handle this properly in "
                "Blender: using Edit bone data mode, but FLVER may not appear correct when static and/or animated."
            )
        bl_bone_data_type = FLVERBoneDataType.EDIT
    else:
        # No bind pose.
        bl_bone_data_type = FLVERBoneDataType.CUSTOM

    # We need edit mode to create `EditBones` below.
    command.context.view_layer.objects.active = armature
    command.operator.to_edit_mode()

    # Create all edit bones. Head/tail are not set yet (depends on `bl_bone_data_type` below).
    edit_bones = _create_edit_bones(armature.data, command.flver, bl_bone_names)

    # NOTE: Bones that have no vertices weighted to them are left as 'unused' root bones in the FLVER skeleton.
    # They may be animated by HKX animations (and will affect their children appropriately) but will not actually
    # affect any vertices in the mesh.

    if bl_bone_data_type == FLVERBoneDataType.EDIT:
        _write_data_to_edit_bones(
            command.operator, command.flver, edit_bones, command.import_settings.base_edit_bone_length
        )
        del edit_bones  # clear references to edit bones as we exit EDIT mode
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
    elif bl_bone_data_type == FLVERBoneDataType.CUSTOM:
        # We record the bone transforms in custom properties and also write them to PoseBone data for correct static
        # viewing. If animated, this Pose data may be overwritten, but the custom properties will remain for export.
        # This function will change back to OBJECT mode internally before setting pose bone data.
        _write_data_to_custom_bone_prop_and_pose(
            command.operator, command.flver, armature, edit_bones, command.import_settings.base_edit_bone_length
        )
    else:
        # Unreachable.
        raise ValueError(f"Invalid `bl_bone_data_type`: {bl_bone_data_type}")

    return bl_bone_data_type  # can only be EDIT or POSE


def _create_edit_bones(
    armature_data: bpy.types.Armature,
    flver: FLVER,
    bl_bone_names: list[str],
) -> list[bpy.types.EditBone]:
    """Create all edit bones from FLVER bones in `bl_armature`."""
    edit_bones = []  # all bones
    for game_bone, bl_bone_name in zip(flver.bones, bl_bone_names, strict=True):
        game_bone: FLVERBone
        edit_bone = armature_data.edit_bones.new(bl_bone_name)  # '<DUPE>' suffixes already added to names
        edit_bone: bpy.types.EditBone

        # Storing 'Unused' flag for now. TODO: If later games' other flags can't be safely auto-detected, store too.
        edit_bone.FLVER_BONE.is_unused = bool(game_bone.usage_flags & FLVERBoneUsageFlags.UNUSED)

        # If this is `False`, then a bone's rest pose rotation will NOT affect its relative pose basis translation.
        # That is, a standard TRS transform becomes an 'RTS' transform instead. We don't want such behavior,
        # particularly for FLVER root bones like 'Pelvis'.
        edit_bone.use_local_location = True

        # FLVER bones never inherit scale.
        edit_bone.inherit_scale = "NONE"

        # We don't bother storing child or sibling bones. They are generated from parents on export.
        edit_bones.append(edit_bone)
    return edit_bones


def _write_data_to_edit_bones(
    operator: LoggingOperator,
    flver: FLVER,
    edit_bones: list[bpy.types.EditBone],
    base_edit_bone_length: float,
):
    game_arma_transforms = flver.get_bone_armature_space_transforms()

    for game_bone, edit_bone, game_arma_transform in zip(
        flver.bones, edit_bones, game_arma_transforms, strict=True
    ):
        game_bone: FLVERBone
        game_translate, game_rotmat, game_scale = game_arma_transform

        if not is_uniform(game_scale, rel_tol=0.001):
            operator.warning(f"Bone {game_bone.name} has non-uniform scale: {game_scale}. Left as identity.")
            bone_length = base_edit_bone_length
        elif any(c < 0.0 for c in game_scale):
            operator.warning(f"Bone {game_bone.name} has negative scale: {game_scale}. Left as identity.")
            bone_length = base_edit_bone_length
        elif math.isclose(game_scale.x, 1.0, rel_tol=0.001):
            # Bone scale is ALMOST uniform and 1. Correct it.
            bone_length = base_edit_bone_length
        else:
            # Bone scale is uniform and not close to 1, which we can support (though it should be rare/never).
            bone_length = game_scale.x * base_edit_bone_length

        bl_translate = GAME_TO_BL_VECTOR(game_translate)
        # We need to set an initial head/tail position with non-zero length for the `matrix` setter to act upon.
        edit_bone.head = bl_translate
        edit_bone.tail = bl_translate + Vector((0.0, bone_length, 0.0))  # default tail position, rotated below

        bl_rot_mat3 = GAME_TO_BL_MAT3(game_rotmat)
        bl_lrs_mat = bl_rot_mat3.to_4x4()
        bl_lrs_mat.translation = bl_translate
        edit_bone.matrix = bl_lrs_mat
        edit_bone.length = bone_length  # does not interact with `matrix`

        if game_bone.parent_bone is not None:
            parent_bone_index = game_bone.parent_bone.get_bone_index(flver.bones)
            parent_edit_bone = edit_bones[parent_bone_index]
            edit_bone.parent = parent_edit_bone
            # edit_bone.use_connect = True


def _write_data_to_custom_bone_prop_and_pose(
    operator: LoggingOperator,
    flver: FLVER,
    armature: bpy.types.ArmatureObject,
    edit_bones: list[bpy.types.EditBone],
    base_edit_bone_length: float,
):
    bl_bone_transforms = []
    for game_bone in flver.bones:
        bl_bone_location = GAME_TO_BL_VECTOR(game_bone.translate)
        bl_bone_rotation_euler = GAME_TO_BL_EULER(game_bone.rotate)
        bl_bone_scale = GAME_TO_BL_VECTOR(game_bone.scale)
        bl_bone_transforms.append((bl_bone_location, bl_bone_rotation_euler, bl_bone_scale))
    
    for bl_bone_transform, edit_bone in zip(bl_bone_transforms, edit_bones, strict=True):
        # All edit bones are just Blender-Y-direction ("forward") stubs of base length.
        # This rigging makes map piece 'pose' bone data transform as expected for showing accurate vertex positions.
        edit_bone.head = Vector((0, 0, 0))
        edit_bone.tail = Vector((0, base_edit_bone_length, 0))
        edit_bone.FLVER_BONE.flver_translate = bl_bone_transform[0]
        edit_bone.FLVER_BONE.flver_rotate = bl_bone_transform[1]  # Euler angles (Blender coordinates)
        edit_bone.FLVER_BONE.flver_scale = bl_bone_transform[2]

    del edit_bones  # clear references to edit bones as we exit EDIT mode
    operator.to_object_mode()

    pose_bones = armature.pose.bones
    for bl_bone_transform, pose_bone in zip(bl_bone_transforms, pose_bones):
        # TODO: Pose bone transforms are relative to parent (in both FLVER and Blender).
        #  Confirm map pieces still behave as expected, though (they shouldn't even have child bones).
        pose_bone.rotation_mode = "QUATERNION"  # should already be default, but being explicit
        pose_bone.location = bl_bone_transform[0]
        pose_bone.rotation_quaternion = bl_bone_transform[1].to_quaternion()
        pose_bone.scale = bl_bone_transform[2]
