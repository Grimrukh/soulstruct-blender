from __future__ import annotations

__all__ = [
    "BlenderFLVER",
]

import re
import time
import typing as tp
from dataclasses import dataclass, field
from pathlib import Path

import bmesh
import bpy
import numpy as np

from soulstruct.base.models.flver import *
from soulstruct.base.models.shaders import MatDef
from soulstruct.games import DEMONS_SOULS
from soulstruct.utilities.maths import Vector3, Matrix3

from io_soulstruct.exceptions import *
from io_soulstruct.flver.image.types import DDSTextureCollection
from io_soulstruct.flver.material.properties import get_cached_mtdbnd, get_cached_matbinbnd
from io_soulstruct.flver.material.types import BlenderFLVERMaterial
from io_soulstruct.flver.models.properties import FLVERExportSettings
from io_soulstruct.general import BLENDER_GAME_CONFIG, SoulstructSettings
from io_soulstruct.utilities import *

from ..enums import FLVERModelType, FLVERBoneDataType

if tp.TYPE_CHECKING:
    from soulstruct.base.models.mtd import MTDBND
    from soulstruct.base.models.matbin import MATBINBND
    from .core import BlenderFLVER


@dataclass(slots=True)
class _CreateFLVERCommand:
    """Bundled inputs and state for creating an FLVER from a Blender FLVER object."""

    # Command arguments:
    operator: LoggingOperator
    context: bpy.types.Context
    bl_flver: BlenderFLVER
    name: str
    flver_model_type: FLVERModelType = FLVERModelType.Unknown
    texture_collection: DDSTextureCollection | None = None

    # State initialized in `__post_init__`:
    flver: FLVER = field(default=None, init=False)
    settings: SoulstructSettings = field(default=None, init=False)
    export_settings: FLVERExportSettings = field(default=None, init=False)
    mtdbnd: MTDBND | None = field(default=None, init=False)
    matbinbnd: MATBINBND | None = field(default=None, init=False)

    def __post_init__(self):
        """Create an empty FLVER. This is the first step in the FLVER export process."""

        if self.texture_collection is None:
            # Passed all the way through to the node inspection in FLVER materials to map texture stems to Images.
            # May be passed in by multi-FLVER export operator that plans to export all textures at once later.
            self.texture_collection = DDSTextureCollection()

        self.settings = self.context.scene.soulstruct_settings
        self.export_settings = self.context.scene.flver_export_settings

        if BLENDER_GAME_CONFIG[self.settings.game].uses_matbin:
            self.matbinbnd = get_cached_matbinbnd(self.operator, self.context)
        else:
            self.mtdbnd = get_cached_mtdbnd(self.operator, self.context)

        if self.bl_flver.version == "DEFAULT":
            # Default is game-dependent.
            try:
                version = self.settings.game_config.flver_default_version
            except KeyError:
                raise ValueError(
                    f"Do not know default FLVER Version for game {self.settings.game}. You must set 'Version' yourself "
                    f"on FLVER object '{self.name}' before exporting."
                )
        else:
            try:
                version = FLVERVersion[self.bl_flver.version]
            except KeyError:
                raise ValueError(f"Invalid FLVER Version: '{self.bl_flver.version}'. Please report this to Grimrukh!")

        if version <= 0xFFFF:
            # FLVER0 (Demon's Souls)
            self.flver = FLVER(
                big_endian=self.bl_flver.big_endian,
                version=version,
                unicode=self.bl_flver.unicode,
                f0_unk_x4a=self.bl_flver.f0_unk_x4a,
                f0_unk_x4b=self.bl_flver.f0_unk_x4b,
                f0_unk_x4c=self.bl_flver.f0_unk_x4c,
                f0_unk_x5c=self.bl_flver.f0_unk_x5c,
            )
        else:
            # FLVER2
            self.flver = FLVER(
                big_endian=self.bl_flver.big_endian,
                version=version,
                unicode=self.bl_flver.unicode,
                f2_unk_x4a=self.bl_flver.f2_unk_x4a,
                f2_unk_x4c=self.bl_flver.f2_unk_x4c,
                f2_unk_x5c=self.bl_flver.f2_unk_x5c,
                f2_unk_x5d=self.bl_flver.f2_unk_x5d,
                f2_unk_x68=self.bl_flver.f2_unk_x68,
            )

    @property
    def mesh(self):
        return self.bl_flver.mesh

    @property
    def armature(self):
        return self.bl_flver.armature


def create_flver_from_bl_flver(
    operator: LoggingOperator,
    context: bpy.types.Context,
    bl_flver: BlenderFLVER,
    texture_collection: DDSTextureCollection = None,
    flver_model_type=FLVERModelType.Unknown,
) -> FLVER:
    """Wraps actual method with temp FLVER management."""

    command = _CreateFLVERCommand(operator, context, bl_flver, bl_flver.name, flver_model_type, texture_collection)

    _clear_temp_flver()
    try:
        flver = _create_flver_from_bl_flver(context, command)
    except Exception:
        # NOTE: Would use `finally` for this, but PyCharm can't handle the return type at the moment.
        _clear_temp_flver()
        raise

    _clear_temp_flver()
    return flver


def _clear_temp_flver():
    try:
        bpy.data.objects.remove(bpy.data.objects["__TEMP_FLVER_OBJ__"])
    except KeyError:
        pass

    try:
        bpy.data.meshes.remove(bpy.data.meshes["__TEMP_FLVER__"])
    except KeyError:
        pass


def _create_flver_from_bl_flver(
    context: bpy.types.Context,
    command: _CreateFLVERCommand,
) -> FLVER:
    """`FLVER` exporter. By far the most complicated function in the add-on!"""

    if command.bl_flver.armature:
        bl_dummies = command.bl_flver.get_dummies(command.operator)
        bl_bone_data_type = command.bl_flver.bone_data_type  # set on import and managed by user afterward
        command.operator.info(f"Exporting FLVER '{command.bl_flver.name}' with bone data: {bl_bone_data_type.name}")
    else:
        bl_dummies = []
        bl_bone_data_type = FLVERBoneDataType.OMITTED

    if not command.bl_flver.armature or not command.bl_flver.armature.pose.bones:
        command.operator.info(  # not a warning
            f"No non-empty FLVER Armature to export. Creating FLVER skeleton with a single default bone at origin "
            f"named '{command.bl_flver.game_name}'."
        )
        default_bone = FLVERBone(name=command.bl_flver.game_name)  # default transform and other fields
        command.flver.bones.append(default_bone)
        bl_bone_names = [default_bone.name]
        using_default_bone = True
    else:
        command.flver.bones, bl_bone_names, bone_arma_transforms = _create_flver_bones(
            context, command, bl_bone_data_type
        )
        command.flver.set_bone_children_siblings()  # only parents set in `create_bones`
        command.flver.set_bone_armature_space_transforms(bone_arma_transforms)
        using_default_bone = False

    # Make Mesh the active object again.
    command.context.view_layer.objects.active = command.bl_flver.mesh

    for bl_dummy in bl_dummies:
        flver_dummy = bl_dummy.to_soulstruct_obj(command.operator, command.context, command.bl_flver.armature)
        # Mark attach/parent bones as used. TODO: Set more specific flags in later games (2 here).
        if flver_dummy.attach_bone_index >= 0:
            command.flver.bones[flver_dummy.attach_bone_index].usage_flags &= ~1
        if flver_dummy.parent_bone_index >= 0:
            command.flver.bones[flver_dummy.parent_bone_index].usage_flags &= ~1
        command.flver.dummies.append(flver_dummy)

    # `MatDef` for each Blender material is needed to determine which Blender UV layers to use for which loops.
    matdef_class = command.settings.game_config.matdef_class
    if matdef_class is None:
        raise UnsupportedGameError(f"Cannot yet export FLVERs for game {command.settings.game}. (No `MatDef` class.)")

    matdefs = []
    for bl_material in command.bl_flver.mesh.data.materials:
        mat_def_name = Path(bl_material.FLVER_MATERIAL.mat_def_path).name
        if command.matbinbnd:
            matdef = matdef_class.from_matbinbnd_or_name(mat_def_name, command.matbinbnd)
        else:
            matdef = matdef_class.from_mtdbnd_or_name(mat_def_name, command.mtdbnd)
        matdefs.append(matdef)

    if not command.bl_flver.mesh.data.vertices:
        # No meshes in FLVER (e.g. c0000). We also leave all bounding boxes as their default max/min values.
        # We don't warn for expected empty FLVERs c0000 and c1000. (Note there are more that are empty in vanilla.)
        if command.bl_flver.name[:5] not in {"c0000", "c1000"}:
            command.operator.warning(f"Exporting non-c0000/c1000 FLVER '{command.bl_flver.name}' with no mesh data.")
        return command.flver

    if command.flver_model_type == FLVERModelType.Unknown:
        # Guess model type based on name.
        # TODO: For layouts, probably better off checking MTD prefix 'M' or 'C'?
        use_map_piece_layout = FLVERModelType.guess_from_name(command.name) == FLVERModelType.MapPiece
    else:
        use_map_piece_layout = command.flver_model_type == FLVERModelType.MapPiece

    _create_flver_meshes(
        command,
        bl_bone_names=bl_bone_names,
        use_map_piece_layout=use_map_piece_layout,
        matdefs=matdefs,
        using_default_bone=using_default_bone,
    )

    # TODO: Bone bounding box space seems to be always local to the bone for characters and always in armature space
    #  for map pieces. Not sure about objects, could be some of each (haven't found any non-origin bones that any
    #  vertices are weighted to with `is_bind_pose=True`). This is my temporary hack since we are already using
    #  'read_bone_type == FLVERBoneDataType.POSE' as a marker for map pieces.
    # TODO: Better heuristic is likely to use the bone weights themselves (missing or all zero -> armature space).
    # TODO: At least one object with all `is_bind_pose = False` (o1154 in DSR) has 'undefined' bone bounding boxes (i.e.
    #  SINGLE_MAX for min and SINGLE_MIN for max).
    command.flver.refresh_bone_bounding_boxes(in_local_space=bl_bone_data_type == FLVERBoneDataType.EDIT)

    # Refresh `FLVERMesh` and FLVER-wide bounding boxes.
    # TODO: Partially redundant since splitter does this for meshes automatically. Only need FLVER-wide bounds in
    #  that case...
    command.flver.refresh_bounding_boxes()

    return command.flver


def _create_flver_meshes(
    command: _CreateFLVERCommand,
    bl_bone_names: list[str],
    use_map_piece_layout: bool,
    matdefs: list[MatDef],
    using_default_bone: bool,
):
    """
    Construct a `MergedMesh` from Blender data, in a straightforward way (unfortunately using `for` loops over
    vertices, faces, and loops), then split it into `FLVERMesh` instances based on Blender materials.

    Also creates `Material` and `VertexArrayLayout` instances for each Blender material, and assigns them to the
    appropriate `FLVERMesh` instances. Any duplicate instances here will be merged when FLVER is packed.
    """

    # 1. Create per-mesh info. Note that every Blender material index is guaranteed to be mapped to AT LEAST ONE
    #    split `FLVERMesh` in the exported FLVER (more if mesh bone maximum is exceeded). This allows the user to
    #    also split their meshes manually in Blender, if they wish.
    split_mesh_defs = []  # type: list[SplitMeshDef]

    bl_materials = command.bl_flver.get_materials()

    if command.settings.is_game(DEMONS_SOULS):
        # Use absolute texture path prefix, featuring model stem and other subdirectories.
        # NOTE: Almost certainly doesn't actually matter in-game.
        get_texture_path_prefix = _get_des_texture_path_prefix_getter(command.name, command.flver_model_type)
    else:
        # Paths in later games are just naked file names.
        get_texture_path_prefix = None

    for matdef, bl_material in zip(matdefs, bl_materials, strict=True):
        bl_material: BlenderFLVERMaterial
        split_mesh_def = bl_material.to_split_mesh_def(
            command.operator,
            command.context,
            command.export_settings.create_lod_face_sets,
            matdef,
            use_map_piece_layout,
            command.texture_collection,
            get_texture_path_prefix,
        )
        split_mesh_defs.append(split_mesh_def)

    # 2. Validate UV layers: ensure all required material UV layer names are present, and warn if any unexpected
    #    Blender UV layers are present.
    bl_uv_layer_names = command.bl_flver.mesh.data.uv_layers.keys()
    remaining_bl_uv_layer_names = set(bl_uv_layer_names)
    used_uv_layer_names = set()
    for matdef, bl_material in zip(matdefs, command.bl_flver.mesh.data.materials):
        for used_layer in matdef.get_used_uv_layers():
            if used_layer.name not in bl_uv_layer_names:
                raise FLVERExportError(
                    f"Material '{bl_material.name}' with def '{matdef.name}' (shader '{matdef.shader_stem}') "
                    f"requires UV layer '{used_layer.name}', which is missing in Blender."
                )
            if used_layer.name in remaining_bl_uv_layer_names:
                remaining_bl_uv_layer_names.remove(used_layer.name)
            used_uv_layer_names.add(used_layer.name)
    for remaining_bl_uv_layer_name in remaining_bl_uv_layer_names:
        command.operator.warning(
            f"UV layer '{remaining_bl_uv_layer_name}' is present in Blender mesh '{command.bl_flver.mesh.name}' but is "
            f"not used by any FLVER material shader. Ignoring it."
        )

    # 3. Create a triangulated copy of the mesh, so the user doesn't have to triangulate it themselves (though they
    #  may want to do this anyway for absolute approval of the final asset). Materials are copied over. Nothing else
    #  needs to be copied, as it is either done automatically by triangulation (e.g. UVs, vertex colors) or is part
    #  of the unchanged vertex data (e.g. bone weights) in the original mesh.
    tri_mesh_data = _create_triangulated_mesh(command.bl_flver, command.context, do_data_transfer=False)

    # 4. Construct arrays from Blender data and pass into a new `MergedMesh` for splitting.

    # Slow part number 1: iterating over every Blender vertex to retrieve its position and bone weights/indices.
    # We at least know the size of the array in advance.
    vertex_count = len(tri_mesh_data.vertices)
    if use_map_piece_layout and command.flver.version.map_pieces_use_normal_w_bones():
        # Bone weights/indices not in array. `normal_w` is used for single Map Piece bone.
        vertex_data_dtype = [
            ("position", "f", 3),
        ]
        use_normal_w_bone_index = True
    else:
        # Rigged FLVERs and older games' Map Pieces.
        vertex_data_dtype = [
            ("position", "f", 3),  # TODO: support 4D position (see, e.g., Rykard slime in ER: c4711)
            ("bone_weights", "f", 4),
            ("bone_indices", "i", 4),
        ]
        use_normal_w_bone_index = False

    vertex_data = np.empty(vertex_count, dtype=vertex_data_dtype)
    vertex_positions = np.empty((vertex_count, 3), dtype=np.float32)
    command.bl_flver.mesh.data.vertices.foreach_get("co", vertex_positions.ravel())
    vertex_bone_weights = np.zeros((vertex_count, 4), dtype=np.float32)  # default: 0.0
    vertex_bone_indices = np.full((vertex_count, 4), -1, dtype=np.int32)  # default: -1

    # Map bone names to their indices now to avoid `index()` calls in the loop.
    bone_name_indices = {bone_name: i for i, bone_name in enumerate(bl_bone_names)}
    # Map group indices to group objects for bone weights.
    vertex_groups_dict = {group.index: group for group in command.mesh.vertex_groups}
    no_bone_warning_done = False
    used_bone_indices = set()  # for marking unused bones in FLVER

    p = time.perf_counter()

    # Unfortunately, there is no way to retrieve the weighted bones of vertices without iterating over all vertices.
    # We iterate over the original, non-triangulated mesh, as the vertices should be the same and these vertices
    # have their bone vertex groups (which cannot easily be transferred to the triangulated copy).
    for i, vertex in enumerate(command.mesh.data.vertices):
        bone_indices = []  # global (splitter will make them local to mesh if appropriate)
        bone_weights = []
        for vertex_group in vertex.groups:  # only one for Map Pieces; max of 4 for other FLVER types
            mesh_group = vertex_groups_dict[vertex_group.group]
            try:
                bone_index = bone_name_indices[mesh_group.name]
            except ValueError:
                raise FLVERExportError(f"Vertex is weighted to invalid bone name: '{mesh_group.name}'.")
            bone_indices.append(bone_index)
            used_bone_indices.add(bone_index)
            # We don't waste time calling retrieval method `weight()` for map pieces.
            if not use_map_piece_layout:
                # TODO: `vertex_group` has `group` (int) and `weight` (float) on it already?
                bone_weights.append(mesh_group.weight(i))

        if len(bone_indices) > 4:
            raise FLVERExportError(
                f"Vertex {i} cannot be weighted to {len(bone_indices)} bones (max 1 for Map Pieces, 4 for others)."
            )
        elif len(bone_indices) == 0:
            if len(bl_bone_names) == 1 and use_map_piece_layout:
                # Omitted bone indices can be assumed to be the only bone in the skeleton.
                # We issue a warning (once) unless this FLVER export is using a default bone (no Armature), in which
                # case we obviously don't expect any vertices to be weighted to anything.
                if not using_default_bone and not no_bone_warning_done:
                    command.operator.warning(
                        f"WARNING: At least one vertex in mesh '{command.mesh.name}' is not weighted to any bones. "
                        f"Weighting in 'Map Piece' mode to only bone in skeleton: '{bl_bone_names[0]}'"
                    )
                    no_bone_warning_done = True
                bone_indices = [0]  # padded out below
                used_bone_indices.add(0)
                # Leave weights as zero.
            else:
                # Can't guess which bone to weight to. Raise error.
                raise FLVERExportError(
                    f"Vertex {i} is not weighted to any bones, and Map Piece FLVER has multiple bones."
                )

        if use_map_piece_layout:
            if len(bone_indices) == 1:
                # Duplicate single-element list to four-element list.
                # (This is done even for games that will write only a single Map Piece bone to `normal_w`.)
                bone_indices *= 4
            else:
                raise FLVERExportError(f"Map Piece vertices must be weighted to exactly one bone (vertex {i}).")
        else:
            # Pad out bone weights and (unused) indices for rigged meshes.
            while len(bone_weights) < 4:
                bone_weights.append(0.0)
            while len(bone_indices) < 4:
                # NOTE: we use -1 here to optimize the mesh splitting process; it will be changed to 0 for write.
                bone_indices.append(-1)

        vertex_bone_indices[i] = bone_indices
        if bone_weights:  # rigged only
            vertex_bone_weights[i] = bone_weights

    for used_bone_index in used_bone_indices:
        command.flver.bones[used_bone_index].usage_flags &= ~1
        if command.settings.is_game("ELDEN_RING"):  # TODO: Probably started in an earlier game.
            command.flver.bones[used_bone_index].usage_flags |= 8

    vertex_data["position"] = vertex_positions
    if "bone_weights" in vertex_data.dtype.names:
        vertex_data["bone_weights"] = vertex_bone_weights
    if "bone_indices" in vertex_data.dtype.names:
        vertex_data["bone_indices"] = vertex_bone_indices

    command.operator.debug(f"Constructed combined vertex array in {time.perf_counter() - p} s.")

    # NOTE: We now iterate over the faces of the triangulated copy. Material index has been properly triangulated.
    p = time.perf_counter()
    faces = np.empty((len(tri_mesh_data.polygons), 4), dtype=np.int32)
    # TODO: Again, due to the unfortunate need to access Python attributes one by one, we need a `for` loop.
    #  ...But, `foreach_get()` doesn't work for `loop_indices` and `material_index`?
    for i, face in enumerate(tri_mesh_data.polygons):
        # Since we've triangulated the mesh, no need to check face loop count here.
        faces[i] = [*face.loop_indices, face.material_index]

    command.operator.debug(f"Constructed combined face array with {len(faces)} rows in {time.perf_counter() - p} s.")

    # Finally, we iterate over (triangulated) loops and construct their arrays. Note that loop UV and vertex color
    # data IS copied over during the triangulation. Obviously, we will just have more loops.
    p = time.perf_counter()
    loop_count = len(tri_mesh_data.loops)

    # TODO: Could check combined `dtype` now to skip any arrays not needed by ANY materials.

    # UV arrays correspond to FLVER-wide sorted UV layer names.
    # Default UV data is 0.0 (each material may only use a subset of UVs).
    loop_uv_array_dict = {
        uv_layer_name: np.zeros((loop_count, 2), dtype=np.float32)
        for uv_layer_name in used_uv_layer_names
    }

    # Retrieve vertex colors.
    # NOTE: Like UVs, it's extremely unlikely -- and probably untrue in any vanilla FLVER -- that NO FLVER material
    #  uses even one vertex color. In this case, though, the default black color generated here will simply never
    #  make it to any of the `MatDef`-based mesh array layouts after this.
    loop_color_arrays = []
    try:
        colors_layer_0 = tri_mesh_data.vertex_colors["VertexColors0"]
    except KeyError:
        command.operator.warning(f"FLVER mesh '{command.mesh.name}' has no 'VertexColors0' data layer. Using black.")
        colors_layer_0 = None
        # Default to black with alpha 1.
        black = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
        loop_color_arrays.append(np.tile(black, (loop_count, 1)))
    else:
        # Prepare for loop filling.
        loop_color_arrays.append(np.empty((loop_count, 4), dtype=np.float32))

    try:
        colors_layer_1 = tri_mesh_data.vertex_colors["VertexColors1"]
    except KeyError:
        # Fine. This mesh only uses one colors layer.
        colors_layer_1 = None
    else:
        # Prepare for loop filling.
        loop_color_arrays.append(np.empty((loop_count, 4), dtype=np.float32))
    # TODO: Check for arbitrary additional vertex colors? Or first, scan all layouts to check what's expected.

    loop_vertex_indices = np.empty(loop_count, dtype=np.int32)
    tri_mesh_data.loops.foreach_get("vertex_index", loop_vertex_indices)

    loop_normals = np.empty((loop_count, 3), dtype=np.float32)
    tri_mesh_data.loops.foreach_get("normal", loop_normals.ravel())
    if use_normal_w_bone_index:
        # New Map Pieces: single vertex bone index is stored in `normal_w` (as `uint8`).
        # TODO: Given that the default `normal_w` value in older games is 127, this may be signed, and so the max
        #  Map Piece bone count may actually be 127/128. Sticking with 256 for now.
        if (max_bone_index := vertex_bone_indices.max()) > 255:
            raise FLVERExportError(
                f"Map Piece mode only supports up to 256 bones (8-bit index), not: {max_bone_index}"
            )
        loop_normals_w = vertex_bone_indices[:, 0][loop_vertex_indices].astype(np.uint8).reshape(-1, 1)
    else:
        # Rigged models or old Map Pieces: `normal_w` is unused and defaults to 127.
        loop_normals_w = np.full((loop_count, 1), 127, dtype=np.uint8)

    if colors_layer_0:
        colors_layer_0.data.foreach_get("color", loop_color_arrays[0].ravel())
    if colors_layer_1:
        colors_layer_1.data.foreach_get("color", loop_color_arrays[1].ravel())
    for uv_layer_name in used_uv_layer_names:
        uv_layer = tri_mesh_data.uv_layers[uv_layer_name]
        if len(uv_layer.data) == 0:
            raise FLVERExportError(f"UV layer {uv_layer.name} contains no data.")
        uv_layer.data.foreach_get("uv", loop_uv_array_dict[uv_layer_name].ravel())

    # 5. Calculate individual tangent arrays for each UV layer that starts with `UVTexture`.
    #  We also need to manually include `UVBloodMaskOrLightmap` for non-Map Pieces (Bloodborne) as the same slot is
    #  used for Lightmaps by Map Pieces. (No better solution for this yet.)

    loop_tangent_arrays = []
    uv_texture_layer_names = sorted(
        [
            name for name in bl_uv_layer_names
            if name.startswith("UVTexture") or (name == "UVBloodMaskOrLightmap" and not use_map_piece_layout)
        ]
    )
    for uv_name in uv_texture_layer_names:
        loop_tangents = _get_tangents_for_uv_layer(
            command.operator, uv_name, loop_count, loop_normals, loop_uv_array_dict, tri_mesh_data,
        )
        loop_tangent_arrays.append(loop_tangents)

    # Assign second tangents array to bitangents in earlier games (DeS/DS1).
    # TODO: Not sure if DS2 uses bitangent field.
    # Bloodborne onwards properly use multiple tangent fields.
    if command.settings.is_game("DEMONS_SOULS", "DARK_SOULS_PTDE", "DARK_SOULS_DSR"):
        # Early games only support up to two tangent arrays, and put the second in "bitangent" vertex array data.
        if len(loop_tangent_arrays) > 2:
            command.operator.warning(
                f"Game '{command.settings.game.name}' does not support more than two vertex tangent arrays (i.e. does "
                f"not support more than two 'UVTexture#' UV layers). Only the first two tangent arrays will be used."
            )
        loop_bitangents = loop_tangent_arrays[1] if len(loop_tangent_arrays) > 1 else None
        loop_tangent_arrays = [loop_tangent_arrays[0]]
    else:
        # Later games support multiple vertex tangents and do not overload the bitangents.
        loop_bitangents = None

    command.operator.debug(f"Constructed combined loop array in {time.perf_counter() - p} s.")

    merged_mesh_kwargs = dict(
        vertex_data=vertex_data,
        loop_vertex_indices=loop_vertex_indices,
        vertices_merged=True,
        loop_normals=loop_normals,
        loop_normals_w=loop_normals_w,
        loop_tangents=loop_tangent_arrays,
        loop_bitangents=loop_bitangents,
        loop_vertex_colors=loop_color_arrays,
        loop_uvs=loop_uv_array_dict,
        faces=faces,
    )

    merged_mesh = MergedMesh(**merged_mesh_kwargs)

    # Apply Blender -> FromSoft transformations.
    merged_mesh.swap_vertex_yz(tangents=True, bitangents=True)
    merged_mesh.invert_vertex_uv(invert_u=False, invert_v=True)

    p = time.perf_counter()
    command.flver.meshes = merged_mesh.split_mesh(
        split_mesh_defs,
        unused_bone_indices_are_minus_one=True,  # saves some time within the splitter (no ambiguous zeroes)
        normal_tangent_dot_threshold=command.export_settings.normal_tangent_dot_max,
        **command.settings.game_config.split_mesh_kwargs,
    )
    command.operator.debug(
        f"Split Blender mesh into {len(command.flver.meshes)} FLVER meshes in {time.perf_counter() - p} s."
    )


def _get_tangents_for_uv_layer(
    operator: LoggingOperator,
    uv_name: str,
    loop_count: int,
    loop_normals: np.ndarray,
    loop_uvs: dict[str, np.ndarray],
    tri_mesh_data: bpy.types.Mesh,
) -> np.ndarray:
    try:
        tri_mesh_data.calc_tangents(uvmap=uv_name)
    except RuntimeError as ex:
        raise RuntimeError(
            f"Could not calculate vertex tangents from UV layer '{uv_name}'. "
            f"Make sure the mesh is triangulated and not empty (delete any empty mesh). Error: {ex}"
        )
    loop_tangents = np.empty((loop_count, 3), dtype=np.float32)
    tri_mesh_data.loops.foreach_get("tangent", loop_tangents.ravel())
    loop_tangents = np_cross(loop_tangents, loop_normals)
    # Add default `w` components to tangents and bitangents (-1). May be negated into 1 below.
    minus_one = np.full((loop_count, 1), -1, dtype=np.float32)
    loop_tangents = np.concatenate((loop_tangents, minus_one), axis=1)
    # We need to check the determinant of every face's loop UVs to determine if the tangent should be negated
    # due to mirrored UV mapping. Fortunately, we're already set up for vectorization here.
    loop_tangent_signs = _get_face_uv_tangent_signs(loop_uvs[uv_name])
    loop_tangents_reshaped = loop_tangents.reshape(-1, 3, 4)  # temporary reshape for easy negation
    loop_tangents_reshaped *= loop_tangent_signs[:, np.newaxis, np.newaxis]
    loop_tangents = loop_tangents_reshaped.reshape(-1, 4)
    operator.debug(
        f"Detected {np.sum(loop_tangent_signs < 0)} / {loop_tangent_signs.size} face loops with mirrored UVs in "
        f"UV layer '{uv_name}' and negated their vertex tangents."
    )
    return loop_tangents


def _get_face_uv_tangent_signs(loop_uv_array: np.ndarray) -> np.ndarray:
    """Uses the determinant of the UV face to determine if the UV mapping is mirrored.

    Returns a 1D array matching face indices, with -1 indicating a mirrored face and 1 a non-mirrored face.
    """
    tangent_loop_uvs_reshaped = loop_uv_array.reshape(-1, 3, 2)  # every 3-row chunk now grouped by first dimension
    face_uv0 = tangent_loop_uvs_reshaped[:, 0, :]
    face_uv1 = tangent_loop_uvs_reshaped[:, 1, :]
    face_uv2 = tangent_loop_uvs_reshaped[:, 2, :]
    delta_u1 = face_uv1[:, 0] - face_uv0[:, 0]
    delta_v1 = face_uv1[:, 1] - face_uv0[:, 1]
    delta_u2 = face_uv2[:, 0] - face_uv0[:, 0]
    delta_v2 = face_uv2[:, 1] - face_uv0[:, 1]
    determinants = (delta_u1 * delta_v2) - (delta_u2 * delta_v1)
    return np.where(determinants < 0, -1, 1)


def _create_triangulated_mesh(
    bl_flver: BlenderFLVER, context: bpy.types.Context, do_data_transfer: bool = False
) -> bpy.types.Mesh:
    """Use `bmesh` and the Data Transfer Modifier to create a temporary triangulated copy of the mesh (required
    for FLVER models) that retains/interpolates critical information like custom split normals and vertex groups."""

    # Automatically triangulate the mesh.
    bm = bmesh.new()
    bm.from_mesh(bl_flver.mesh.data)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method="BEAUTY", ngon_method="BEAUTY")
    tri_mesh_data = bpy.data.meshes.new("__TEMP_FLVER__")  # will be deleted during `finally` block of caller
    # Probably not necessary, but we copy material slots over, just case it causes `face.material_index` problems.
    for bl_mat in bl_flver.mesh.data.materials:
        tri_mesh_data.materials.append(bl_mat)
    bm.to_mesh(tri_mesh_data)
    bm.free()
    del bm

    # Create an object for the mesh so we can apply the Data Transfer modifier to it.
    # noinspection PyTypeChecker
    tri_mesh_obj = new_mesh_object("__TEMP_FLVER_OBJ__", tri_mesh_data)
    context.scene.collection.objects.link(tri_mesh_obj)

    if do_data_transfer:
        # Add the Data Transfer Modifier to the triangulated mesh object.
        # TODO: This requires the new triangulated mesh to EXACTLY overlap the original mesh, so we should set its
        #  transform. (Any parent offsets will be hard to deal with, though...)
        # noinspection PyTypeChecker
        data_transfer_mod = tri_mesh_obj.modifiers.new(
            name="__TEMP_FLVER_DATA_TRANSFER__", type="DATA_TRANSFER"
        )  # type: bpy.types.DataTransferModifier
        data_transfer_mod.object = bl_flver.mesh
        # Enable custom normal data transfer and set the appropriate options.
        data_transfer_mod.use_loop_data = True
        data_transfer_mod.data_types_loops = {"CUSTOM_NORMAL"}
        if len(tri_mesh_data.loops) == len(bl_flver.mesh.data.loops):
            # Triangulation did not change the number of loops, so we can map custom normals directly.
            # TODO: Do I even need to transfer any data? I think the triangulation will have done it all.
            data_transfer_mod.loop_mapping = "TOPOLOGY"
        else:
            data_transfer_mod.loop_mapping = "NEAREST_POLYNOR"  # best for simple triangulation
        # Apply the modifier.
        bpy.context.view_layer.objects.active = tri_mesh_obj  # set the triangulated mesh as active
        bpy.ops.object.modifier_apply(modifier=data_transfer_mod.name)

    # Return the mesh data.
    return tri_mesh_obj.data


def _create_flver_bones(
    context: bpy.types.Context,
    command: _CreateFLVERCommand,
    read_bone_type: FLVERBoneDataType,
) -> tuple[list[FLVERBone], list[str], list[tuple[Vector3, Matrix3, Vector3]]]:
    """Create `FLVER` bones from Blender `armature` bones and get their armature space transforms.

    Bone transform data may be read from either EDIT mode (typical for characters and objects) or POSE mode (typical
    for map pieces). This is inferred from all materials and specified by `read_bone_type`.
    """

    # We need `EditBone` mode to retrieve custom properties, even if reading the actual transforms from pose later.
    # TODO: Still true for extension properties?
    armature = command.bl_flver.armature
    command.context.view_layer.objects.active = armature
    command.operator.to_edit_mode(context)

    edit_bone_names = [edit_bone.name for edit_bone in armature.data.edit_bones]

    game_bones = []
    game_bone_parent_indices = []  # type: list[int]
    game_arma_transforms = []  # type: list[tuple[Vector3, Matrix3, Vector3]]  # translate, rotate matrix, scale

    if len(set(edit_bone_names)) != len(edit_bone_names):
        raise FLVERExportError("Bone names in Blender Armature are not all unique.")

    for edit_bone in armature.data.edit_bones:

        if edit_bone.name not in edit_bone_names:
            continue  # ignore this bone (e.g. c0000 bones not used by equipment FLVER being exported)

        game_bone_name = edit_bone.name
        while re.match(r".*\.\d\d\d$", game_bone_name):
            # Bone names can be repeated in the FLVER. Remove Blender duplicate suffixes.
            game_bone_name = game_bone_name[:-4]
        while game_bone_name.endswith(" <DUPE>"):
            # Bone names can be repeated in the FLVER.
            game_bone_name = game_bone_name.removesuffix(" <DUPE>")

        bone_usage_flags = edit_bone.FLVER_BONE.get_flags()
        if (bone_usage_flags & FLVERBoneUsageFlags.UNUSED) != 0 and bone_usage_flags != 1:
            raise FLVERExportError(
                f"Bone '{edit_bone.name}' has 'Is Unused' enabled, but also has other usage flags set!"
            )
        game_bone = FLVERBone(name=game_bone_name, usage_flags=bone_usage_flags)

        if edit_bone.parent:
            parent_bone_name = edit_bone.parent.name
            parent_bone_index = edit_bone_names.index(parent_bone_name)
        else:
            parent_bone_index = -1

        if read_bone_type == FLVERBoneDataType.EDIT:
            # Get armature-space bone transform from rigged `EditBone` (characters and objects, typically).
            bl_translate = edit_bone.matrix.translation
            bl_rotmat = edit_bone.matrix.to_3x3()  # get rotation submatrix
            game_arma_translate = BL_TO_GAME_VECTOR3(bl_translate)
            game_arma_rotmat = BL_TO_GAME_MAT3(bl_rotmat)
            s = edit_bone.length / command.export_settings.base_edit_bone_length
            # NOTE: only uniform scale is supported for these "is_bind_pose" mesh bones
            game_arma_scale = s * Vector3.one()
            game_arma_transforms.append((game_arma_translate, game_arma_rotmat, game_arma_scale))

        game_bones.append(game_bone)
        game_bone_parent_indices.append(parent_bone_index)

    # Assign game bone parent references. Child and sibling bones are done by caller using FLVER method.
    for game_bone, parent_index in zip(game_bones, game_bone_parent_indices):
        game_bone.parent_bone = game_bones[parent_index] if parent_index >= 0 else None

    command.operator.to_object_mode(command.context)

    if read_bone_type == FLVERBoneDataType.CUSTOM:
        # Get armature-space bone transform from PoseBone (map pieces).
        # Note that non-uniform bone scale is supported here (and is actually used in some old vanilla map pieces).
        for game_bone, bl_bone_name in zip(game_bones, edit_bone_names):

            pose_bone = armature.pose.bones[bl_bone_name]

            game_arma_translate = BL_TO_GAME_VECTOR3(pose_bone.location)
            if pose_bone.rotation_mode == "QUATERNION":
                bl_rot_quat = pose_bone.rotation_quaternion
                bl_rotmat = bl_rot_quat.to_matrix()
                game_arma_rotmat = BL_TO_GAME_MAT3(bl_rotmat)
            elif pose_bone.rotation_mode == "XYZ":
                # TODO: Could this cause the same weird Blender gimbal lock errors as I was seeing with characters?
                #  If so, I may want to make sure I always set pose bone rotation to QUATERNION mode.
                bl_rot_euler = pose_bone.rotation_euler
                bl_rotmat = bl_rot_euler.to_matrix()
                game_arma_rotmat = BL_TO_GAME_MAT3(bl_rotmat)
            else:
                raise FLVERExportError(
                    f"Unsupported rotation mode '{pose_bone.rotation_mode}' for bone '{pose_bone.name}'. Must be "
                    f"'QUATERNION' or 'XYZ' (Euler)."
                )
            game_arma_scale = BL_TO_GAME_VECTOR3(pose_bone.scale)  # can be non-uniform
            game_arma_transforms.append(
                (
                    game_arma_translate,
                    game_arma_rotmat,
                    game_arma_scale,
                )
            )

    return game_bones, edit_bone_names, game_arma_transforms


def _get_des_texture_path_prefix_getter(model_name: str, flver_model_type: FLVERModelType) -> tp.Callable[[str], str]:
    """We use the texture prefix ('mAA_', 'cXXXX_', 'oXXXX_') to determine the path prefix where possible,
    and rely on the model type being exported for the default template."""

    match flver_model_type:
        case FLVERModelType.MapPiece:
            # TODO: Kind of want access to map stem (for area), but we'll guess it from the texture name prefix.
            #  (Can't guess it from export name in Demon's Souls because there's no 'AXX' model suffix.)
            template = "N:\\DemonsSoul\\data\\Model\\map\\mAA\\tex\\"  # TODO: unknown area placeholder

        case FLVERModelType.Character:
            template = f"N:\\DemonsSoul\\data\\Model\\chr\\{model_name}\\tex\\"

        case FLVERModelType.Object:
            template = f"N:\\DemonsSoul\\data\\Model\\obj\\{model_name.split('_')[0]}\\tex\\"

        case FLVERModelType.Equipment:

            match model_name[:2]:
                case "AM":
                    subdir = f"Arm\\{model_name.upper()}\\"
                case "BD":
                    subdir = f"Body\\{model_name.upper()}\\"
                case "HD":
                    subdir = f"Head\\{model_name.upper()}\\"
                case "HR":
                    subdir = f"Hair\\{model_name.upper()}\\"
                case "LG":
                    subdir = f"Leg\\{model_name.upper()}\\"
                case "WP":
                    subdir = f"Weapon\\{model_name.upper()}\\"
                case _:
                    subdir = ""

            template = f"N:\\DemonsSoul\\data\\Model\\parts\\{subdir}tex\\"

        case _:
            template = ""

    def get_prefix(texture_stem: str, default_template=template, model_type=flver_model_type):
        if re.match(r"^m\d\d_.*", texture_stem):
            return f"N:\\DemonsSoul\\data\\Model\\map\\{texture_stem[:3]}\\tex\\"
        if re.match(r"^c\d\d\d\d(_|$).*", texture_stem):
            return f"N:\\DemonsSoul\\data\\Model\\chr\\{texture_stem[:5]}\\tex\\"
        if re.match(r"^o\d\d\d\d(_|$).*", texture_stem):
            return f"N:\\DemonsSoul\\data\\Model\\obj\\{texture_stem[:5]}\\tex\\"
        if model_type == FLVERModelType.Equipment:
            if texture_stem.lower().startswith("ghost_") or "_body" in texture_stem:
                return "N:\\DemonsSoul\\data\\Model\\parts\\tex\\"
        if default_template:
            return default_template.format(texture_stem=texture_stem)
        return ""  # no prefix

    return get_prefix
