from __future__ import annotations

__all__ = ["FLVERExporter"]

import ast
import re
import time
import typing as tp
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

import bmesh
import bpy

from soulstruct.base.models.flver import FLVER, FLVERBone, FLVERBoneUsageFlags, Dummy
from soulstruct.base.models.flver.material import Material, Texture, GXItem
from soulstruct.base.models.flver.mesh_tools import MergedMesh, SplitSubmeshDef
from soulstruct.base.models.shaders import MatDef
from soulstruct.games import *
from soulstruct.utilities.maths import Vector3, Matrix3

from io_soulstruct.exceptions import *
from io_soulstruct.general import *
from io_soulstruct.utilities import *
from io_soulstruct.flver.types import BlenderFLVER, BlenderFLVERDummy

if tp.TYPE_CHECKING:
    from soulstruct.base.models.matbin import MATBINBND
    from soulstruct.base.models.mtd import MTDBND
    from .settings import FLVERExportSettings
    from ..properties import FLVERMaterialProps, FLVERBoneProps, FLVERGXItemProps


@dataclass(slots=True)
class FLVERExporter:
    """Manages exports for a batch of FLVER files using the same settings.

    Call `export_flver()` to import a single FLVER file.
    """

    # These are cached per-game on first load, which also preserves lazily loaded MATBINs. They can be cleared with
    # `FLVERExporter.clear_matdef_caches()`.
    _CACHED_MTDBNDS: tp.ClassVar[dict[Game, MTDBND]] = {}
    _CACHED_MATBINBNDS: tp.ClassVar[dict[Game, MATBINBND]] = {}

    operator: LoggingOperator
    context: bpy.types.Context
    settings: SoulstructSettings

    # Loaded from `settings` if not given, unless already cached.
    mtdbnd: MTDBND | None = None
    matbinbnd: MATBINBND | None = None

    # Collects Blender images corresponding to exported FLVER material textures. Should be used and cleared by the
    # caller as required.
    collected_texture_images: dict[str, bpy.types.Image] = field(default_factory=dict)

    def __post_init__(self):
        if self.mtdbnd is None and not self.settings.is_game(ELDEN_RING):
            if self.settings.game not in self._CACHED_MTDBNDS:
                self._CACHED_MTDBNDS[self.settings.game] = self.settings.get_mtdbnd(self.operator)
            self.mtdbnd = self._CACHED_MTDBNDS[self.settings.game]
        if self.matbinbnd is None and self.settings.is_game(ELDEN_RING):
            if self.settings.game not in self._CACHED_MATBINBNDS:
                self._CACHED_MATBINBNDS[self.settings.game] = self.settings.get_matbinbnd(self.operator)
            self.matbinbnd = self._CACHED_MATBINBNDS[self.settings.game]

    def export_flver(self, bl_flver: BlenderFLVER) -> FLVER:
        """Create an entire FLVER from a Blender FLVER model."""
        self.clear_temp_flver()

        export_settings = self.context.scene.flver_export_settings  # type: FLVERExportSettings

        flver = bl_flver.to_empty_flver(self.settings)
        bl_dummies = bl_flver.get_dummies(self.operator)
        read_bone_type = bl_flver.guess_bone_read_type(self.operator)
        self.info(f"Exporting FLVER '{bl_flver.name}' with bone data from {read_bone_type.capitalize()}Bones.")

        if bl_flver.armature is None or not bl_flver.armature.pose.bones:
            self.info(  # not a warning
                f"No Armature/bones to export. Creating FLVER skeleton with a single origin bone named "
                f"'{bl_flver.flver_stem}'."
             )
            default_bone = FLVERBone(name=bl_flver.flver_stem)  # default transform and other fields
            flver.bones = [default_bone]
            bl_bone_names = [default_bone.name]
            bl_bone_data = None
        else:
            flver.bones, bl_bone_names, bone_arma_transforms = self.create_bones(
                bl_flver.armature,
                read_bone_type,
            )
            flver.set_bone_children_siblings()  # only parents set in `create_bones`
            flver.set_bone_armature_space_transforms(bone_arma_transforms)
            bl_bone_data = bl_flver.armature.data.bones

        # Make Mesh the active object again.
        self.context.view_layer.objects.active = bl_flver.mesh

        for bl_dummy in bl_dummies:
            flver_dummy = self.export_dummy(bl_dummy, bl_bone_names, bl_bone_data)
            # Mark attach/parent bones as used. TODO: Set more specific flags in later games (2 here).
            if flver_dummy.attach_bone_index >= 0:
                flver.bones[flver_dummy.attach_bone_index].usage_flags &= ~1
            if flver_dummy.parent_bone_index >= 0:
                flver.bones[flver_dummy.parent_bone_index].usage_flags &= ~1
            flver.dummies.append(flver_dummy)

        # `MatDef` for each Blender material is needed to determine which Blender UV layers to use for which loops.
        try:
            matdef_class = self.settings.get_game_matdef_class()
        except UnsupportedGameError:
            raise UnsupportedGameError(f"Cannot yet export FLVERs for game {self.settings.game}. (No `MatDef` class.)")

        matdefs = []
        for bl_material in bl_flver.mesh.data.materials:
            mat_def_name = Path(bl_material.flver_material.mat_def_path).name
            if GAME_CONFIG[self.settings.game].uses_matbin:
                matdef = matdef_class.from_matbinbnd_or_name(mat_def_name, self.matbinbnd)
            else:
                matdef = matdef_class.from_mtdbnd_or_name(mat_def_name, self.mtdbnd)
            matdefs.append(matdef)

        if not bl_flver.mesh.data.vertices:
            # No submeshes in FLVER (e.g. c0000). We also leave all bounding boxes as their default max/min values.
            # We don't warn for expected empty FLVERs c0000 and c1000.
            if bl_flver.name[:5] not in {"c0000", "c1000"}:
                self.warning(f"Exporting non-c0000/c1000 FLVER '{bl_flver.name}' with no mesh data.")
            return flver

        # TODO: Current choosing default vertex buffer layout (CHR vs. MAP PIECE) based on read bone type, which in
        #  turn depends on `mesh.is_bind_pose` at FLVER import. All a bit messily wired together...
        self.export_submeshes(
            flver,
            bl_flver.mesh,
            bl_bone_names,
            use_chr_layout=read_bone_type == "EDIT",
            normal_tangent_dot_max=export_settings.normal_tangent_dot_max,
            create_lod_face_sets=export_settings.create_lod_face_sets,
            matdefs=matdefs,
        )

        # TODO: Bone bounding box space seems to be always local to the bone for characters and always in armature space
        #  for map pieces. Not sure about objects, could be some of each (haven't found any non-origin bones that any
        #  vertices are weighted to with `is_bind_pose=True`). This is my temporary hack since we are already using
        #  'read_bone_type == POSE' as a marker for map pieces.
        # TODO: Better heuristic is likely to use the bone weights themselves (missing or all zero -> armature space).
        flver.refresh_bone_bounding_boxes(in_local_space=read_bone_type == "EDIT")

        # Refresh `Submesh` and FLVER-wide bounding boxes.
        # TODO: Partially redundant since splitter does this for submeshes automatically. Only need FLVER-wide bounds.
        flver.refresh_bounding_boxes()

        # Should be called in `finally` block by caller anyway.
        self.clear_temp_flver()

        return flver

    def export_submeshes(
        self,
        flver: FLVER,
        bl_mesh: bpy.types.MeshObject,
        bl_bone_names: list[str],
        use_chr_layout: bool,
        normal_tangent_dot_max: float,
        create_lod_face_sets: bool,
        matdefs: list[MatDef],
    ):
        """
        Construct a `MergedMesh` from Blender data, in a straightforward way (unfortunately using `for` loops over
        vertices, faces, and loops), then split it into `Submesh` instances based on Blender materials.

        Also creates `Material` and `VertexArrayLayout` instances for each Blender material, and assigns them to the
        appropriate `Submesh` instances. Any duplicate instances here will be merged when FLVER is packed.
        """
        # 1. Create per-submesh info. Note that every Blender material index is guaranteed to be mapped to AT LEAST ONE
        #    split `Submesh` in the exported FLVER (more if submesh bone maximum is exceeded). This allows the user to
        #    also split their submeshes manually in Blender, if they wish.
        split_submesh_defs = []  # type: list[SplitSubmeshDef]
        for matdef, bl_material in zip(matdefs, bl_mesh.data.materials):
            split_submesh_def = self.get_split_submesh_def(
                bl_material, create_lod_face_sets, matdef, use_chr_layout
            )
            split_submesh_defs.append(split_submesh_def)

        # 2. Validate UV layers: ensure all required material UV layer names are present, and warn if any unexpected
        #    Blender UV layers are present.
        bl_uv_layer_names = bl_mesh.data.uv_layers.keys()
        remaining_bl_uv_layer_names = set(bl_uv_layer_names)
        used_uv_layer_names = set()
        for matdef, bl_material in zip(matdefs, bl_mesh.data.materials):
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
            self.warning(
                f"UV layer '{remaining_bl_uv_layer_name}' is present in Blender mesh '{bl_mesh.name}' but is not "
                f"used by any FLVER material shader. Ignoring it."
            )

        # 3. Create a triangulated copy of the mesh, so the user doesn't have to triangulate it themselves (though they
        #  may want to do this anyway for absolute approval of the final asset). Custom split normals are copied to the
        #  triangulated mesh using an applied Data Transfer modifier (UPDATE: disabled for now as it ruins sharp edges
        #  even for existing triangles). Materials are copied over. Nothing else needs to be copied, as it is either
        #  done automatically by triangulation (e.g. UVs, vertex colors) or is part of the unchanged vertex data (e.g.
        #  bone weights) in the original mesh.
        tri_mesh_data = self.create_triangulated_mesh(bl_mesh, do_data_transfer=False)

        # TODO: The tangent and bitangent of each vertex should be calculated from the UV map that is effectively
        #  serving as the normal map ('_n' displacement texture) for that vertex. However, for multi-texture mesh
        #  materials, vertex alpha blends two normal maps together, so the UV map for (bi)tangents will vary across
        #  the mesh and would require external calculation here. Working on that...
        #  For now, just calculating tangents from the first UV map.
        #  Also note that map piece FLVERs only have Bitangent data for materials with two textures. Suspicious?
        try:
            # TODO: This function calls the required `calc_normals_split()` automatically, but if it was replaced,
            #  a separate call of that would be needed to write the (rather inaccessible) custom split per-loop normal
            #  data (pink lines in 3D View overlay) to each `loop.normal`. (Pre-4.1 only.)
            tri_mesh_data.calc_tangents(uvmap="UVTexture0")
            # bl_mesh_data.calc_normals_split()
        except RuntimeError as ex:
            # TODO: Some FLVER materials actually have no UVs, like 'C[Fur]_cloth' shader in Elden Ring. A FLVER made
            #  entirely of these materials would genuinely have no UVs in the merged Blender mesh -- but of course,
            #  that doesn't exist in vanilla files. (Also, it DOES have tangent data, which we'd need to calcualte
            #  somehow).
            raise RuntimeError(
                f"Could not calculate vertex tangents from UV layer 'UVTexture0', which every FLVER mesh should have. "
                f"Make sure the mesh is triangulated and not empty (delete any empty mesh). Error: {ex}"
            )

        # 4. Construct arrays from Blender data and pass into a new `MergedMesh` for splitting.

        # Slow part number 1: iterating over every Blender vertex to retrieve its position and bone weights/indices.
        # We at least know the size of the array in advance.
        vertex_count = len(tri_mesh_data.vertices)
        vertex_data_dtype = [
            ("position", "f", 3),  # TODO: support 4D position (see, e.g., Rykard slime in ER: c4711)
            ("bone_weights", "f", 4),
            ("bone_indices", "i", 4),
        ]
        vertex_data = np.empty(vertex_count, dtype=vertex_data_dtype)
        vertex_positions = np.empty((vertex_count, 3), dtype=np.float32)
        vertex_bone_weights = np.zeros((vertex_count, 4), dtype=np.float32)  # default: 0.0
        vertex_bone_indices = np.full((vertex_count, 4), -1, dtype=np.int32)  # default: -1

        vertex_groups_dict = {group.index: group for group in bl_mesh.vertex_groups}  # for bone indices/weights
        no_bone_warning_done = False
        used_bone_indices = set()

        # TODO: Due to the unfortunate need to access Python attributes one by one, we need a `for` loop. Given the
        #  retrieval of vertex bones, though, it's unlikely a simple `position` array assignment would remove the need.
        # TODO: Surely I can use `vertices.foreach_get("co" / "groups")`?
        p = time.perf_counter()

        # NOTE: We iterate over the original, non-triangulated mesh, as the vertices should be the same and these
        # vertices have their bone vertex groups (which cannot easily be transferred to the triangulated copy).
        for i, vertex in enumerate(bl_mesh.data.vertices):
            vertex_positions[i] = vertex.co  # TODO: would use `foreach_get` but still have to iterate for bones?

            bone_indices = []  # global (splitter will make them local to submesh if appropriate)
            bone_weights = []
            for vertex_group in vertex.groups:  # only one for map pieces; max of 4 for other FLVER types
                mesh_group = vertex_groups_dict[vertex_group.group]
                try:
                    bone_index = bl_bone_names.index(mesh_group.name)
                except ValueError:
                    raise FLVERExportError(f"Vertex is weighted to invalid bone name: '{mesh_group.name}'.")
                bone_indices.append(bone_index)
                # We don't waste time calling retrieval method `weight()` for map pieces.
                if use_chr_layout:
                    # TODO: `vertex_group` has `group` (int) and `weight` (float) on it already?
                    bone_weights.append(mesh_group.weight(i))

            if len(bone_indices) > 4:
                raise FLVERExportError(
                    f"Vertex cannot be weighted to {len(bone_indices)} bones (max 1 for Map Pieces, 4 for others)."
                )
            elif len(bone_indices) == 0:
                if len(bl_bone_names) == 1 and not use_chr_layout:
                    # Omitted bone indices can be assumed to be the only bone in the skeleton.
                    if not no_bone_warning_done:
                        self.warning(
                            f"WARNING: At least one vertex in mesh '{bl_mesh.name}' is not weighted to any bones. "
                            f"Weighting in 'Map Piece' mode to only bone in skeleton: '{bl_bone_names[0]}'"
                        )
                        no_bone_warning_done = True
                    bone_indices = [0]  # padded out below
                    # Leave weights as zero.
                else:
                    # Can't guess which bone to weight to. Raise error.
                    raise FLVERExportError("Vertex is not weighted to any bones (cannot guess from multiple).")

            # Before padding out bone indices with zeroes, mark these FLVER bones as used.
            for bone_index in bone_indices:
                used_bone_indices.add(bone_index)

            if use_chr_layout:
                # Pad out bone weights and (unused) indices for rigged meshes.
                while len(bone_weights) < 4:
                    bone_weights.append(0.0)
                while len(bone_indices) < 4:
                    # NOTE: we use -1 here to optimize the mesh splitting process; it will be changed to 0 for write.
                    bone_indices.append(-1)
            else:  # map pieces
                if len(bone_indices) == 1:
                    bone_indices *= 4  # duplicate single-element list to four-element list
                else:
                    raise FLVERExportError(f"Non-CHR FLVER vertices must be weighted to exactly one bone (vertex {i}).")

            vertex_bone_indices[i] = bone_indices
            if bone_weights:  # rigged only
                vertex_bone_weights[i] = bone_weights

        for used_bone_index in used_bone_indices:
            flver.bones[used_bone_index].usage_flags &= ~1
            if self.settings.is_game(ELDEN_RING):  # TODO: Probably started in an earlier game.
                flver.bones[used_bone_index].usage_flags |= 8

        vertex_data["position"] = vertex_positions
        vertex_data["bone_weights"] = vertex_bone_weights
        vertex_data["bone_indices"] = vertex_bone_indices

        self.info(f"Constructed combined vertex array in {time.perf_counter() - p} s.")

        # TODO: Again, due to the unfortunate need to access Python attributes one by one, we need a `for` loop.
        # NOTE: We now iterate over the faces of the triangulated copy. Material index has been properly triangulated.
        p = time.perf_counter()
        faces = np.empty((len(tri_mesh_data.polygons), 4), dtype=np.int32)
        for i, face in enumerate(tri_mesh_data.polygons):
            # Since we've triangulated the mesh, no need to check face loop count here.
            faces[i] = [*face.loop_indices, face.material_index]

        self.info(f"Constructed combined face array with {len(faces)} rows in {time.perf_counter() - p} s.")

        # Finally, we iterate over (triangulated) loops and construct their arrays. Note that loop UV and vertex color
        # data IS copied over during the triangulation. Obviously, we will just have more loops.
        p = time.perf_counter()
        loop_count = len(tri_mesh_data.loops)

        # UV arrays correspond to FLVER-wide sorted UV layer names.
        # Default UV data is 0.0 (each material may only use a subset of UVs).
        loop_uvs = {
            uv_layer_name: np.zeros((loop_count, 2), dtype=np.float32)
            for uv_layer_name in used_uv_layer_names
        }

        # Retrieve vertex colors.
        # TODO: Like UVs, it's extremely unlikely -- and probably untrue in any vanilla FLVER -- that NO FLVER material
        #  uses even one vertex color. In this case, though, the default black color generated here will simply never
        #  make it to any of the `MatDef`-based submesh array layouts after this.
        loop_colors = []
        try:
            colors_layer_0 = tri_mesh_data.vertex_colors["VertexColors0"]
        except KeyError:
            self.warning(f"FLVER mesh '{bl_mesh.name}' has no 'VertexColors0' data layer. Using black.")
            colors_layer_0 = None
            # Default to black with alpha 1.
            black = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
            loop_colors.append(np.tile(black, (loop_count, 1)))
        else:
            # Prepare for loop filling.
            loop_colors.append(np.empty((loop_count, 4), dtype=np.float32))

        try:
            colors_layer_1 = tri_mesh_data.vertex_colors["VertexColors1"]
        except KeyError:
            # Fine. This submesh only uses one colors layer.
            colors_layer_1 = None
        else:
            # Prepare for loop filling.
            loop_colors.append(np.empty((loop_count, 4), dtype=np.float32))
        # TODO: Check for arbitrary additional vertex colors? Or first, scan all layouts to check what's expected.

        loop_vertex_indices = np.empty(loop_count, dtype=np.int32)
        loop_normals = np.empty((loop_count, 3), dtype=np.float32)
        # TODO: Not exporting any real `normal_w` data yet. If used as a fake bone weight, it should be stored in a
        #  custom data layer or something.
        loop_normals_w = np.full((loop_count, 1), 127, dtype=np.uint8)
        # TODO: could check combined `dtype` now to skip these if not needed by any materials.
        #  (Related: mark these arrays as optional attributes in `MergedMesh`.)
        # TODO: Currently only exporting one `tangent` array. Need to calculate tangents for each UV map, per material.
        loop_tangents = np.empty((loop_count, 3), dtype=np.float32)
        loop_bitangents = np.empty((loop_count, 3), dtype=np.float32)

        tri_mesh_data.loops.foreach_get("vertex_index", loop_vertex_indices)
        tri_mesh_data.loops.foreach_get("normal", loop_normals.ravel())
        tri_mesh_data.loops.foreach_get("tangent", loop_tangents.ravel())
        # TODO: 99% sure that `bitangent` data in DS1 is used to store tangent data for the second normal map, which
        #  later games do by actually using a second tangent buffer.
        tri_mesh_data.loops.foreach_get("bitangent", loop_bitangents.ravel())
        if colors_layer_0:
            colors_layer_0.data.foreach_get("color", loop_colors[0].ravel())
        if colors_layer_1:
            colors_layer_1.data.foreach_get("color", loop_colors[1].ravel())
        for uv_layer_name in used_uv_layer_names:
            uv_layer = tri_mesh_data.uv_layers[uv_layer_name]
            if len(uv_layer.data) == 0:
                raise FLVERExportError(f"UV layer {uv_layer.name} contains no data.")
            uv_layer.data.foreach_get("uv", loop_uvs[uv_layer_name].ravel())

        # Rotate tangents and bitangents to what FromSoft expects using cross product with normals.
        loop_tangents = np_cross(loop_tangents, loop_normals)
        loop_bitangents = np_cross(loop_bitangents, loop_normals)

        # Add default `w` components to tangents and bitangents (-1).
        minus_one = np.full((loop_count, 1), -1, dtype=np.float32)
        loop_tangents = np.concatenate((loop_tangents, minus_one), axis=1)
        loop_bitangents = np.concatenate((loop_bitangents, minus_one), axis=1)

        self.info(f"Constructed combined loop array in {time.perf_counter() - p} s.")

        merged_mesh = MergedMesh(
            vertex_data=vertex_data,
            loop_vertex_indices=loop_vertex_indices,
            loop_normals=loop_normals,
            loop_normals_w=loop_normals_w,
            loop_tangents=[loop_tangents],
            loop_bitangents=loop_bitangents,
            loop_vertex_colors=loop_colors,
            loop_uvs=loop_uvs,
            faces=faces,
        )

        # Apply Blender -> FromSoft transformations.
        merged_mesh.swap_vertex_yz(tangents=True, bitangents=True)
        merged_mesh.invert_vertex_uv(invert_u=False, invert_v=True)

        p = time.perf_counter()
        flver.submeshes = merged_mesh.split_mesh(
            split_submesh_defs,
            use_submesh_bone_indices=True,  # TODO: for DS1... when did this stop?
            max_bones_per_submesh=38,  # TODO: for DS1... what about other games?
            unused_bone_indices_are_minus_one=True,  # saves some time within the splitter (no ambiguous zeroes)
            normal_tangent_dot_threshold=normal_tangent_dot_max,
            # NOTE: DS1 has a maximum submesh vertex count of 65535, as face vertex indices must be 16-bit globally.
            # Later games use 32-bit face vertex indices (max 4294967295).
            max_submesh_vertex_count=65535 if self.settings.is_game(DARK_SOULS_PTDE, DARK_SOULS_DSR) else 4294967295,
        )
        self.info(f"Split mesh into {len(flver.submeshes)} submeshes in {time.perf_counter() - p} s.")

    def get_split_submesh_def(
        self,
        bl_material: bpy.types.Material,
        create_lod_face_sets: bool,
        matdef: MatDef,
        use_chr_layout: bool,
    ) -> SplitSubmeshDef:
        """Use given `matdef` to create a `SplitSubmeshDef` for the given Blender material with either a character
        layout or a map piece layout, depending on `use_chr_layout`."""

        # Some Blender materials may be variants representing distinct Submesh/FaceSet properties; these will be
        # mapped to the same FLVER `Material`/`VertexArrayLayout` combo (created here).
        flver_material = self.export_material(bl_material, matdef)
        if use_chr_layout:
            array_layout = matdef.get_character_layout()
        else:
            array_layout = matdef.get_map_piece_layout()

        # noinspection PyUnresolvedReferences
        props = bl_material.flver_material  # type: FLVERMaterialProps
        # We only respect 'Face Set Count' if requested in export options. (Duplicating the main face set is only
        # viable in older games with low-res meshes, but those same games don't even really need LODs anyway.)
        face_set_count = props.face_set_count if create_lod_face_sets else 1
        use_backface_culling = (
            bl_material.use_backface_culling
            if props.use_backface_culling == "DEFAULT"
            else props.use_backface_culling == "ENABLED"
        )
        submesh_kwargs = {
            "is_bind_pose": props.is_bind_pose,
            "default_bone_index": props.default_bone_index,
            "use_backface_culling": use_backface_culling,
            "uses_bounding_box": True,  # TODO: assumption (DS1 and likely all later games)
            "face_set_count": face_set_count,
        }
        used_uv_layer_names = [layer.name for layer in matdef.get_used_uv_layers()]
        self.operator.info(f"Created FLVER material: {flver_material.name} with UV layers: {used_uv_layer_names}")
        return SplitSubmeshDef(
            flver_material,
            array_layout,
            submesh_kwargs,
            used_uv_layer_names,
        )

    def create_triangulated_mesh(
        self,
        bl_mesh: bpy.types.MeshObject,
        do_data_transfer: bool = False,
    ) -> bpy.types.Mesh:
        """Use `bmesh` and the Data Transfer Modifier to create a temporary triangulated copy of the mesh (required
        for FLVER models) that retains/interpolates critical information like custom split normals and vertex groups."""

        # Automatically triangulate the mesh.
        bm = bmesh.new()
        bm.from_mesh(bl_mesh.data)
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
        tri_mesh_data = bpy.data.meshes.new("__TEMP_FLVER__")  # will be deleted during `finally` block of caller
        if bpy.app.version < (4, 1):
            # Removed in Blender 4.1. (Now implicit from the presence of custom normals.)
            tri_mesh_data.use_auto_smooth = True
        # Probably not necessary, but we copy material slots over, just case it causes `face.material_index` problems.
        for bl_mat in bl_mesh.data.materials:
            tri_mesh_data.materials.append(bl_mat)
        bm.to_mesh(tri_mesh_data)
        bm.free()
        del bm

        # Create an object for the mesh so we can apply the Data Transfer modifier to it.
        # noinspection PyTypeChecker
        tri_mesh_obj = new_mesh_object("__TEMP_FLVER_OBJ__", tri_mesh_data)
        self.context.collection.objects.link(tri_mesh_obj)

        if do_data_transfer:
            # Add the Data Transfer Modifier to the triangulated mesh object.
            # TODO: This requires the new triangulated mesh to EXACTLY overlap the original mesh, so we should set its
            #  transform. (Any parent offsets will be hard to deal with, though...)
            # noinspection PyTypeChecker
            data_transfer_mod = tri_mesh_obj.modifiers.new(
                name="__TEMP_FLVER_DATA_TRANSFER__", type="DATA_TRANSFER"
            )  # type: bpy.types.DataTransferModifier
            data_transfer_mod.object = bl_mesh
            # Enable custom normal data transfer and set the appropriate options.
            data_transfer_mod.use_loop_data = True
            data_transfer_mod.data_types_loops = {"CUSTOM_NORMAL"}
            if len(tri_mesh_data.loops) == len(bl_mesh.data.loops):
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

    def create_bones(
        self,
        armature: bpy.types.ArmatureObject,
        read_bone_type: str,
    ) -> tuple[list[FLVERBone], list[str], list[tuple[Vector3, Matrix3, Vector3]]]:
        """Create `FLVER` bones from Blender `armature` bones and get their armature space transforms.

        Bone transform data may be read from either EDIT mode (typical for characters and objects) or POSE mode (typical
        for map pieces). This is specified by `read_bone_type`.
        """

        # We need `EditBone` mode to retrieve custom properties, even if reading the actual transforms from pose later.
        self.context.view_layer.objects.active = armature
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="EDIT", toggle=False)

        edit_bone_names = [edit_bone.name for edit_bone in armature.data.edit_bones]

        game_bones = []
        game_bone_parent_indices = []  # type: list[int]
        game_arma_transforms = []  # type: list[tuple[Vector3, Matrix3, Vector3]]  # translate, rotate matrix, scale

        if len(set(edit_bone_names)) != len(edit_bone_names):
            raise FLVERExportError("Bone names in Blender Armature are not all unique.")

        export_settings = self.context.scene.flver_export_settings  # type: FLVERExportSettings

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

            usage_flags = self.get_bone_usage_flags(edit_bone)
            game_bone = FLVERBone(name=game_bone_name, usage_flags=usage_flags)

            if edit_bone.parent:
                parent_bone_name = edit_bone.parent.name
                parent_bone_index = edit_bone_names.index(parent_bone_name)
            else:
                parent_bone_index = -1

            if read_bone_type == "EDIT":
                # Get armature-space bone transform from rigged `EditBone` (characters and objects, typically).
                bl_translate = edit_bone.matrix.translation
                bl_rotmat = edit_bone.matrix.to_3x3()  # get rotation submatrix
                game_arma_translate = BL_TO_GAME_VECTOR3(bl_translate)
                game_arma_rotmat = BL_TO_GAME_MAT3(bl_rotmat)
                s = edit_bone.length / export_settings.base_edit_bone_length
                # NOTE: only uniform scale is supported for these "is_bind_pose" mesh bones
                game_arma_scale = s * Vector3.one()
                game_arma_transforms.append((game_arma_translate, game_arma_rotmat, game_arma_scale))

            game_bones.append(game_bone)
            game_bone_parent_indices.append(parent_bone_index)

        # Assign game bone parent references. Child and sibling bones are done by caller using FLVER method.
        for game_bone, parent_index in zip(game_bones, game_bone_parent_indices):
            game_bone.parent_bone = game_bones[parent_index] if parent_index >= 0 else None

        self.operator.to_object_mode()

        if read_bone_type == "POSE":
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

    @staticmethod
    def get_bone_usage_flags(edit_bone: bpy.types.EditBone) -> int:
        """Get bone usage flags from custom properties on `edit_bone`.

        NOTE: The `FLVER` write method will automatically redirect non-1 values to 0 for early FLVER versions.
        """
        flags = 0
        # noinspection PyUnresolvedReferences
        props = edit_bone.flver_bone  # type: FLVERBoneProps
        if props.is_unused:
            flags |= FLVERBoneUsageFlags.UNUSED
        if props.is_used_by_local_dummy:
            flags |= FLVERBoneUsageFlags.DUMMY
        if props.is_used_by_equipment:
            flags |= FLVERBoneUsageFlags.cXXXX
        if props.is_used_by_local_mesh:
            flags |= FLVERBoneUsageFlags.MESH

        if bool(flags & FLVERBoneUsageFlags.UNUSED) and flags != 1:
            raise FLVERExportError(
                f"Bone '{edit_bone.name}' has 'Is Unused' enabled, but also has other usage flags set!"
            )

        return flags

    def export_dummy(
        self,
        bl_dummy: BlenderFLVERDummy,
        bl_bone_names: list[str],
        bl_bone_data: bpy.types.ArmatureBones | None,
    ) -> Dummy:
        """Create a single `FLVER.Dummy` from a Blender Dummy empty."""
        game_dummy = Dummy(
            reference_id=bl_dummy.reference_id,  # stored in dummy name for editing convenience
            color_rgba=list(bl_dummy.color_rgba),
            flag_1=bl_dummy.flag_1,
            use_upward_vector=bl_dummy.use_upward_vector,
            unk_x30=bl_dummy.unk_x30,
            unk_x34=bl_dummy.unk_x34,
        )

        # We decompose the world matrix of the dummy to 'bypass' any attach bone to get its translate and rotate.
        # However, the translate may still be relative to a DIFFERENT parent bone, so we need to account for that below.
        bl_dummy_translate = bl_dummy.obj.matrix_world.translation
        bl_dummy_rotmat = bl_dummy.obj.matrix_world.to_3x3()

        parent_bone = bl_dummy.parent_bone
        if parent_bone is not None and not bl_bone_data:
            self.warning(
                f"Tried to export dummy {bl_dummy.name} with parent bone '{parent_bone.name}', but this FLVER has "
                f"no armature. Dummy will be exported with parent bone index -1."
            )
            parent_bone = None

        if parent_bone:
            # Dummy's Blender 'world' translate is actually given in the space of this bone in the FLVER file.
            try:
                game_dummy.parent_bone_index = bl_bone_names.index(parent_bone.name)
            except ValueError:
                raise FLVERExportError(f"Dummy '{bl_dummy.name}' parent bone '{parent_bone.name}' not in Armature.")
            bl_parent_bone_matrix_inv = bl_bone_data[parent_bone.name].matrix_local.inverted()
            game_dummy.translate = BL_TO_GAME_VECTOR3(bl_parent_bone_matrix_inv @ bl_dummy_translate)
        else:
            game_dummy.parent_bone_index = -1
            game_dummy.translate = BL_TO_GAME_VECTOR3(bl_dummy_translate)

        forward, up = bl_rotmat_to_game_forward_up_vectors(bl_dummy_rotmat)
        game_dummy.forward = forward
        game_dummy.upward = up if game_dummy.use_upward_vector else Vector3.zero()

        if bl_dummy.obj.parent_type == "BONE":  # NOTE: only possible for dummies parented to the Armature
            # Dummy has an 'attach bone' that is its Blender parent.
            try:
                game_dummy.attach_bone_index = bl_bone_names.index(bl_dummy.obj.parent_bone.name)
            except ValueError:
                raise FLVERExportError(
                    f"Dummy '{bl_dummy.name}' attach bone (Blender parent) '{bl_dummy.obj.parent_bone.name}' "
                    f"not in Armature."
                )
        else:
            # Dummy has no attach bone.
            game_dummy.attach_bone_index = -1

        return game_dummy

    def export_material(
        self,
        bl_material: bpy.types.Material,
        matdef: MatDef,
        split_square_brackets=True,
    ) -> Material:
        """Create a FLVER material from Blender material custom properties and texture nodes.

        Texture paths are collected using the provided `MatDef` samplers. For each sampler, if 'Path[sampler.name]' is
        given (even if empty), that is used as the texture path. Otherwise, the texture node named after the alias
        (preferred) or game-specific name for that sampler is searched for, and the name of the Blender Image assigned
        to that node is used as the texture path, even if the Blender Image is a placeholder pixel.

        If a 'Sampler Prefix' custom property is given on the Blender material, it is used to prefix all sampler names.
        This allows node names to be shorted on import, especially for newer games with the full shader name baked into
        every sampler name. (Note that this only matters if the texture node is NOT already an alias, which is mapped
        to the game-specific sampler name using the `MatDef`.)

        If a sampler defines a non-empty `matbin_texture_path`, and that texture's STEM matches the stem of a found
        Blender texture, the FLVER texture is left EMPTY. In this case, the MATBIN already uses that texture; it was
        imported for FLVER viewing convenience, but does not need to be written to the FLVER as a texture path override.
        If the FLVER texture is different, it is written to the FLVER as an override. (Note that older games' MTD-based
        `MatDef`s never have this issue, as they do not provide a `matbin_texture_path`.)

        If an unrecognized sampler name/alias is found on an Image Texture node or as a 'Path[sampler.name]' property,
        the user is warned and that sampler/texture will be ignored, UNLESS `allow_unknown_texture_types` is enabled in
        FLVER export settings. In that case, the texture will be exported to the FLVER material as that texture type
        directly -- but unless you are a wizard who has modified shaders and MTDs/MATBINs, I cannot imagine a use case
        for this.

        If an expected `MatDef` sampler name/alias is MISSING from both 'Path[sampler.name]' properties and texture
        node names, a `FLVERExportError` will be raised, except in the following cases:
            - If `allow_missing_textures` is enabled, ANY sampler name can be missing.
            - If `MatDef.matbin` is given (newer games) and that MATBIN also does not specify a texture path for that
            sampler, we assume that this material/shader does not require that texture.
            - If `MatDef.matbin` is NOT given and the sampler name is 'Detail 0 Normal', it is allowed to be missing,
            because this is clearly an optional and frequently omitted sampler in many shaders in older games.
        In all of these cases, an empty texture path will be written for that texture in the FLVER material. Empty
        texture paths are always permitted if the sampler name is found. Note that the FLVER material importer will
        always create empty Image Texture nodes or empty string properties for samplers with no texture path.
        """
        name = bl_material.name
        if split_square_brackets:
            name = name.split("[")[0].rstrip()  # remove all the suffixes we added (plus any Blender duplicate suffix)

        export_settings = self.context.scene.flver_export_settings  # type: FLVERExportSettings

        # noinspection PyUnresolvedReferences
        props = bl_material.flver_material  # type: FLVERMaterialProps

        flver_material = Material(
            name=name,
            flags=props.flags,
            mat_def_path=props.mat_def_path,
            unk_x18=props.unk_x18,
        )

        for gx_item_prop in props.gx_items:
            gx_item_prop: FLVERGXItemProps
            gx_item_data = ast.literal_eval(gx_item_prop.data)  # str -> bytes
            gx_item = GXItem(
                category=gx_item_prop.category,
                index=gx_item_prop.index,
                size=len(gx_item_data) + 12,  # extra 12 bytes for dummy item at end of list
            )
            gx_item.data = gx_item_data  # not an init field
            flver_material.gx_items.append(gx_item)

        sampler_prefix = props.sampler_prefix
        # FLVER material texture path extension doesn't actually matter, but we try to be faithful.
        path_ext = ".tif" if self.settings.is_game(ELDEN_RING) else ".tga"  # TODO: also TIF in Sekiro?

        if matdef.matbin:
            # Any sampler that does NOT have a path given in MATBIN is allowed to be missing (lack of MATBIN path
            # implies to us that this MATBIN does not use this sampler in the shader).
            allowed_missing_sampler_names = {
                sampler.name for sampler in matdef.samplers if not sampler.matbin_texture_path
            }
        else:
            # Manual specification: 'Detail 0 Normal' is allowed to be missing.
            # TODO: Only for certain older games like DS1R?
            allowed_missing_sampler_names = {"Detail 0 Normal"}

        texture_nodes = {
            node.name: node
            for node in bl_material.node_tree.nodes
            if node.type == "TEX_IMAGE"
        }

        for sampler in matdef.samplers:

            texture_stem = ""
            sampler_name = sampler.name.removeprefix(sampler_prefix)
            sampler_found = False

            # Check custom property.
            path_prop = f"Path[{sampler_name}]"
            if path_prop in bl_material:
                prop_texture_path = get_bl_custom_prop(bl_material, path_prop, str)  # to assert `str` type
                texture_stem = Path(prop_texture_path).stem
                sampler_found = True
            else:
                # Check node named with sampler alias or game-specific name (sans any 'Sampler Prefix').
                for key in (sampler.alias, sampler_name):
                    if key in texture_nodes:
                        node_image = texture_nodes.pop(key).image  # consumes node
                        if node_image:
                            texture_stem = Path(node_image.name).stem
                        sampler_found = True

            if texture_stem and texture_stem == sampler.matbin_texture_stem:
                # Texture path in shader is the same as the MATBIN texture path -- that is, it was imported for
                # FLVER visualization using the MATBIN but does NOT need to be written to the FLVER as an override.
                texture_stem = ""
            elif not sampler_found:
                # Could not find a property or node for sampler.
                if export_settings.allow_missing_textures:
                    pass  # always ignored
                elif sampler.name in allowed_missing_sampler_names:  # full sampler name!
                    pass  # permitted case
                else:
                    raise FLVERExportError(
                        f"Could not find a texture path for sampler '{sampler.name}' in material '{bl_material.name}'. "
                        f"You must create a 'Path[{sampler_name}]' for it (even if empty), or create an Image Texture "
                        f"node for it with a , or "
                        f"enable 'Allow Missing Textures' in FLVER export options."
                    )

            flver_material.textures.append(
                Texture(
                    path=(texture_stem + path_ext) if texture_stem else "",
                    texture_type=sampler_name,
                )
            )

        for node_name, node in texture_nodes.items():
            # Some texture nodes were not used, as they do not match sampler names/aliases.
            if not export_settings.allow_unknown_texture_types:
                self.warning(
                    f"Unknown sampler type (node name) in material '{bl_material.name}': {node_name}. You can enable "
                    f"'Allow Unknown Texture Types' in FLVER export settings to forcibly export it to the FLVER "
                    f"material as this texture type. This would be unusual, though!"
                )
            else:
                self.warning(
                    f"Unknown texture type (node name) in material '{bl_material.name}': {node_name}. Exporting "
                    f"to the FLVER material as this texture type."
                )
                texture_stem = Path(node.image.name).stem
                flver_material.textures.append(
                    Texture(
                        path=(texture_stem + path_ext) if node.image else "",
                        texture_type=node_name,
                    )
                )

        return flver_material

    def warning(self, msg: str):
        self.operator.report({"WARNING"}, msg)
        print(f"# WARNING: {msg}")

    def info(self, msg: str):
        self.operator.report({"INFO"}, msg)
        print(f"# INFO: {msg}")

    @classmethod
    def clear_matdef_caches(cls):
        cls._CACHED_MTDBNDS.clear()
        cls._CACHED_MATBINBNDS.clear()

    @staticmethod
    def clear_temp_flver():
        try:
            bpy.data.objects.remove(bpy.data.objects["__TEMP_FLVER_OBJ__"])
        except KeyError:
            pass

        try:
            bpy.data.meshes.remove(bpy.data.meshes["__TEMP_FLVER__"])
        except KeyError:
            pass
