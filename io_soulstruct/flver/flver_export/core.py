from __future__ import annotations

__all__ = ["FLVERExporter"]

import time

import re
import typing as tp
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

import bmesh
import bpy

from soulstruct.base.models.flver import FLVER, Version, FLVERBone, FLVERBoneUsageFlags, Material, Texture, Dummy
from soulstruct.base.models.flver.vertex_array import *
from soulstruct.base.models.flver.mesh_tools import MergedMesh
from soulstruct.games import *
from soulstruct.utilities.maths import Vector3, Matrix3

from io_soulstruct.general import *
from io_soulstruct.utilities import *
from io_soulstruct.flver.materials import BaseMaterialShaderInfo, DS1MaterialShaderInfo
from io_soulstruct.flver.utilities import *

if tp.TYPE_CHECKING:
    from soulstruct.base.models.mtd import MTDBND as BaseMTDBND
    from soulstruct.eldenring.models.matbin import MATBINBND
    from .settings import FLVERExportSettings


@dataclass(slots=True)
class FLVERExporter:
    """Manages exports for a batch of FLVER files using the same settings.

    Call `export_flver()` to import a single FLVER file.
    """

    DEFAULT_VERSION: tp.ClassVar[str, Version] = {
        DARK_SOULS_PTDE.variable_name: Version.DarkSouls_A,
        DARK_SOULS_DSR.variable_name: Version.DarkSouls_A,
        BLOODBORNE.variable_name: Version.Bloodborne_DS3_A,
        DARK_SOULS_3.variable_name: Version.Bloodborne_DS3_A,
    }

    operator: LoggingOperator
    context: bpy.types.Context
    settings: SoulstructSettings

    # Loaded from `settings` if not given.
    mtdbnd: BaseMTDBND | None = None
    matbinbnd: MATBINBND | None = None

    # Collects Blender images corresponding to exported FLVER material textures. Should be used and cleared by the
    # caller as required.
    collected_texture_images: dict[str, bpy.types.Image] = field(default_factory=dict)

    def __post_init__(self):
        if self.mtdbnd is None:
            self.mtdbnd = self.settings.get_mtdbnd(self.operator)
        if self.matbinbnd is None:
            self.matbinbnd = self.settings.get_matbinbnd(self.operator)

    @staticmethod
    def _clear_temp_flver():
        try:
            bpy.data.meshes.remove(bpy.data.meshes["__TEMP_FLVER__"])
        except KeyError:
            pass

    def export_flver(
        self,
        mesh: bpy.types.MeshObject,
        armature: bpy.types.ArmatureObject | None,
        dummy_material_prefix: str,
        dummy_prefix_must_match: bool,
        default_bone_name="",
    ) -> FLVER:
        """Create an entire FLVER from Blender Mesh and (optional) Armature objects.

        The Mesh and Armature can have any number of Empty children, which are exported as dummies provided they have
        the appropriate custom data (created upon Soulstruct import). Note that only dummies parented to the Armature
        can be attached to Armature bones (which most will, realistically).

        If `armature` is None, a default skeleton with a single bone at the model's origin will be created (which is why
        `default_bone_name` must be passed in). This is fine for 99% of map pieces, for example.

        `dummy_material_prefix` is used to strip disambiguating prefixes from the Blender dummy children and materials
        used by this mesh. If `dummy_prefix_must_match = True`, then only dummy children that start with this prefix
        will be exported (e.g., for exporting equipment meshes parented to `c0000` FLVER).

        If `default_bone_name` is given, and the FLVER has no Armature or no bones (e.g. a simple Map Piece the user has
        created from scratch), a bone of this name (typically matching the model name with/without area) will be created
        at the origin and used for all vertices. Otherwise, an Armature must be present and all vertices must be
        weighted to one or more bones in it.

        If the Mesh object is missing certain 'FLVER' custom properties (see `get_flver_props`), they will be exported
        with default values based on the current selected game, if able.

        TODO: Currently only really tested for DS1 FLVERs.
        """
        self._clear_temp_flver()

        if mesh.type != "MESH":
            raise FLVERExportError("`mesh` object passed to FLVER exporter must be a Mesh.")
        if armature is not None and armature.type != "ARMATURE":
            raise FLVERExportError("`armature` object passed to FLVER exporter must be an Armature or `None`.")

        flver = FLVER(**self.get_flver_props(mesh, self.settings.game))

        bl_dummies = self.collect_dummies(
            mesh, armature, prefix=dummy_material_prefix, prefix_must_match=dummy_prefix_must_match
        )

        read_bone_type = self.detect_is_bind_pose(mesh)
        self.info(f"Exporting FLVER '{mesh.name}' with bone data from {read_bone_type.capitalize()}Bones.")
        if armature is None or not armature.pose.bones:
            if default_bone_name:
                self.info(  # not a warning
                    f"No Armature/bones to export. Creating FLVER skeleton with a single origin bone named "
                    f"'{default_bone_name}'."
                 )
                default_bone = FLVERBone(name=default_bone_name)  # default transform and other fields
                flver.bones = [default_bone]
                bl_bone_names = [default_bone.name]
                bl_bone_data = None
            else:
                raise FLVERExportError(
                    f"No Armature or bones to export and cannot use default bone name. "
                    f"Cannot export FLVER '{mesh.name}'."
                )
        else:
            flver.bones, bl_bone_names, bone_arma_transforms = self.create_bones(
                armature,
                read_bone_type,
            )
            flver.set_bone_children_siblings()  # only parents set in `create_bones`
            flver.set_bone_armature_space_transforms(bone_arma_transforms)
            bl_bone_data = armature.data.bones

        # Make `mesh` the active object again.
        self.context.view_layer.objects.active = mesh

        # noinspection PyUnresolvedReferences
        for bl_dummy, dummy_info in bl_dummies:
            flver_dummy = self.export_dummy(bl_dummy, dummy_info.reference_id, bl_bone_names, bl_bone_data)
            # Mark attach/parent bones as used. TODO: Set more specific flags in later games (2 here).
            if flver_dummy.attach_bone_index >= 0:
                flver.bones[flver_dummy.attach_bone_index].usage_flags &= ~1
            if flver_dummy.parent_bone_index >= 0:
                flver.bones[flver_dummy.parent_bone_index].usage_flags &= ~1
            flver.dummies.append(flver_dummy)

        # Material info for each Blender material is needed to determine which Blender UV layers to use for which loops.
        if self.settings.is_game(DARK_SOULS_PTDE, DARK_SOULS_DSR):
            material_infos = []
            for bl_material in mesh.data.materials:
                try:
                    mtd_name = Path(bl_material["MTD Path"]).name
                except KeyError:
                    raise FLVERExportError(
                        f"Material '{bl_material.name}' has no 'MTD Path' custom property. "
                        f"Cannot export FLVER."
                    )
                material_infos.append(
                    DS1MaterialShaderInfo.from_mtdbnd_or_name(self.operator, mtd_name, self.mtdbnd)
                )
        else:
            raise NotImplementedError(f"Cannot yet export FLVERs for game {self.settings.game}.")

        if not mesh.data.vertices:
            # No submeshes in FLVER (e.g. c0000). We also leave all bounding boxes as their default max/min values.
            # We don't warn for expected empty FLVERs c0000 and c1000.
            if dummy_material_prefix not in {"c0000", "c1000"}:
                self.warning(f"Exporting non-c0000/c1000 FLVER '{mesh.name}' with no mesh data.")
            return flver

        # TODO: Current choosing default vertex buffer layout (CHR vs. MAP PIECE) based on read bone type, which in
        #  turn depends on `mesh.is_bind_pose` at FLVER import. All a bit messily wired together...
        self.export_submeshes(
            flver,
            mesh,
            bl_bone_names,
            use_chr_layout=read_bone_type == "EDIT",
            strip_bl_material_prefix=dummy_material_prefix,
            material_infos=material_infos,
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


        return flver

    def collect_dummies(
        self,
        mesh: bpy.types.MeshObject,
        armature: bpy.types.ArmatureObject | None,
        prefix: str,
        prefix_must_match: bool,
    ) -> list[tuple[bpy.types.Object, DummyInfo]]:
        """Collect all Empty children of the Mesh and Armature objects with valid Dummy names including prefix
        `model_name`, and return them as a list of tuples of the form `(bl_empty, dummy_info)`.

        Dummies parented to the Mesh, rather than the Armature, will NOT be attached to any bones (though may still have
        custom `Parent Bone Name` data).

        Note that no dummies need exist in a FLVER (e.g. map pieces).
        """
        bl_dummies = []  # type: list[tuple[bpy.types.Object, DummyInfo]]
        empty_children = [child for child in mesh.children if child.type == "EMPTY"]
        if armature is not None:
            empty_children.extend([child for child in armature.children if child.type == "EMPTY"])
        for child in empty_children:
            if dummy_info := self.parse_dummy_empty(child):
                if prefix_must_match and dummy_info.model_name != prefix:
                    # Don't bother warning for standard c0000 case (exporting attached equipment FLVER).
                    if dummy_info.model_name != "c0000":
                        self.warning(
                            f"Ignoring Dummy '{child.name}' with non-matching model name prefix: "
                            f"{dummy_info.model_name}"
                        )
                else:
                    bl_dummies.append((child, dummy_info))
            else:
                self.warning(f"Ignoring Empty child '{child.name}' with invalid Dummy name.")

        # Sort dummies and meshes by 'human sorting' on Blender name (should match order in Blender hierarchy view).
        bl_dummies.sort(key=lambda o: natural_keys(o[0].name))
        return bl_dummies

    def parse_dummy_empty(self, bl_empty: bpy.types.Object) -> DummyInfo | None:
        """Check for required 'Unk x30' custom property to detect dummies."""
        if bl_empty.get("Unk x30") is None:
            self.warning(
                f"Empty child of FLVER '{bl_empty.name}' ignored. (Missing 'unk_x30' Dummy property and possibly "
                f"other required properties and proper Dummy name; see docs.)"
            )
            return None

        dummy_info = parse_dummy_name(bl_empty.name)
        if not dummy_info:
            self.warning(
                f"Could not interpret Dummy name: '{bl_empty.name}'. Ignoring it. Format should be: \n"
                f"    `{{MODEL_NAME}} Dummy<{{INDEX}}> [{{REFERENCE_ID}}]`\n"
                f"where 'MODEL_NAME' is optional but must match the name of the exported FLVER for non-Map Pieces."
            )

        return dummy_info

    def export_submeshes(
        self,
        flver: FLVER,
        bl_mesh: bpy.types.MeshObject,
        bl_bone_names: list[str],
        use_chr_layout: bool,
        strip_bl_material_prefix: str,
        material_infos: list[BaseMaterialShaderInfo],
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
        submesh_info = []  # type: list[tuple[Material, VertexArrayLayout, dict[str, tp.Any]]]
        for material_info, bl_material in zip(material_infos, bl_mesh.data.materials):
            # Some Blender materials may be variants representing distinct Submesh/FaceSet properties; these will be
            # mapped to the same FLVER `Material`/`VertexArrayLayout` combo (created here).
            flver_material = self.export_material(bl_material, material_info, strip_bl_material_prefix)
            if use_chr_layout:
                array_layout = material_info.get_character_layout()
            else:
                array_layout = material_info.get_map_piece_layout()
            submesh_kwargs = {
                "is_bind_pose": get_bl_prop(bl_material, "Is Bind Pose", int, default=use_chr_layout, callback=bool),
                "default_bone_index": get_bl_prop(bl_material, "Default Bone Index", int, default=0),
                "use_backface_culling": bl_material.use_backface_culling,
                "uses_bounding_box": True,  # TODO: assumption (DS1 and likely all later games)
            }

            submesh_info.append((flver_material, array_layout, submesh_kwargs))
            self.operator.info(f"Created FLVER material: {flver_material.name}")

        # 2. Extract UV layers.
        # Maps UV layer names to lists of `MeshUVLoop` instances (so they're converted only once across all materials).
        all_uv_layer_names_set = set()
        for material_info in material_infos:
            material_uv_layer_names = material_info.get_uv_layer_names()
            all_uv_layer_names_set |= set(material_uv_layer_names)
        uv_layer_names = sorted(all_uv_layer_names_set)  # e.g. ["UVMap1", "UVMap2", "UVMap3"]

        # Automatically triangulate the mesh.
        bm = bmesh.new()
        bm.from_mesh(bl_mesh.data)
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
        tri_mesh_data = bpy.data.meshes.new("__TEMP_FLVER__")  # will be deleted during `finally` block of caller
        # Probably not necessary, but we copy material slots over, just case it causes `face.material_index` problems.
        for bl_mat in bl_mesh.data.materials:
            tri_mesh_data.materials.append(bl_mat)
        bm.to_mesh(tri_mesh_data)
        bm.free()
        del bm

        # 3. Prepare Mesh data.
        # TODO: The tangent and bitangent of each vertex should be calculated from the UV map that is effectively
        #  serving as the normal map ('_n' displacement texture) for that vertex. However, for multi-texture mesh
        #  materials, vertex alpha blends two normal maps together, so the UV map for (bi)tangents will vary across
        #  the mesh and would require external calculation here. Working on that...
        #  For now, just calculating tangents from the first UV map.
        #  Also note that map piece FLVERs only have Bitangent data for materials with two textures. Suspicious?
        try:
            # TODO: This function calls the required `calc_normals_split()` automatically, but if it was replaced,
            #  a separate call of that would be needed to write the (rather inaccessible) custom split per-loop normal
            #  data (pink lines in 3D View overlay) and writes them to `loop.normal`.
            tri_mesh_data.calc_tangents(uvmap="UVMap1")
            # bl_mesh_data.calc_normals_split()
        except RuntimeError as ex:
            raise RuntimeError(
                "Could not calculate vertex tangents from 'UVMap1'. Make sure the mesh is triangulated and not "
                f"empty (delete any empty mesh). Error: {ex}"
            )

        # 4. Construct arrays from Blender data and pass into a new `MergedMesh`.

        # Slow part number 1: iterating over every Blender vertex to retrieve its position and bone weights/indices.
        # We at least know the size of the array in advance.
        vertex_count = len(tri_mesh_data.vertices)
        vertex_data_dtype = [
            ("position", "f", 3),  # TODO: support 4D position
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
            try:
                faces[i] = [*face.loop_indices, face.material_index]
            except ValueError:
                raise FLVERExportError(
                    f"Cannot export FLVER mesh '{bl_mesh.name}' with any non-triangle faces. "
                    f"Face index {i} has {len(face.loop_indices)} sides)."
                )
        self.info(f"Constructed combined face array with {len(faces)} rows in {time.perf_counter() - p} s.")

        # Finally, we iterate over (triangulated) loops and construct their arrays. Note that loop UV and vertex color
        # data IS copied over during the triangulation. Obviously, we will just have more loops.
        p = time.perf_counter()
        loop_count = len(tri_mesh_data.loops)

        # UV arrays correspond to FLVER-wide sorted UV layer names.
        loop_uvs = [
            np.zeros((loop_count, 2), dtype=np.float32)  # default: 0.0 (each material may only use a subset of UVs)
            for _ in uv_layer_names
        ]

        try:
            # Vertex colors have been triangulated.
            loop_colors_layer = tri_mesh_data.vertex_colors["VertexColors"]
        except KeyError:
            self.warning(f"FLVER mesh '{bl_mesh.name}' has no 'VertexColors' data layer. Using black.")
            loop_colors_layer = None
            # Default to black with alpha 1.
            black = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
            loop_vertex_color = np.tile(black, (loop_count, 1))
        else:
            # Prepare for loop filling.
            loop_vertex_color = np.empty((loop_count, 4), dtype=np.float32)

        loop_vertex_indices = np.empty(loop_count, dtype=np.int32)
        loop_normals = np.empty((loop_count, 3), dtype=np.float32)
        # TODO: Not exporting any real normal_w data yet. If used as a fake bone weight, it should be stored in a custom
        #  data layer.
        loop_normals_w = np.full((loop_count, 1), 127, dtype=np.uint8)
        # TODO: could check combined `dtype` now to skip these if not needed by any materials.
        #  (Related: mark these arrays as optional attributes in `MergedMesh`.)
        # TODO: Currently only exporting one `tangent` array. Need to calculate tangents for each UV map, per material.
        loop_tangents = np.empty((loop_count, 3), dtype=np.float32)
        loop_bitangents = np.empty((loop_count, 3), dtype=np.float32)

        tri_mesh_data.loops.foreach_get("vertex_index", loop_vertex_indices)
        tri_mesh_data.loops.foreach_get("normal", loop_normals.ravel())
        tri_mesh_data.loops.foreach_get("tangent", loop_tangents.ravel())
        # TODO: 99% sure that `bitangent` data in DS1 is used to store tangent data for the second texture group.
        #  So it should be calculated from "tangent" for loops that actually use it... ugh.
        tri_mesh_data.loops.foreach_get("bitangent", loop_bitangents.ravel())
        if loop_colors_layer:
            loop_colors_layer.data.foreach_get("color", loop_vertex_color.ravel())
        for uv_i, uv_layer_name in enumerate(uv_layer_names):
            uv_layer = tri_mesh_data.uv_layers[uv_layer_name]
            if len(uv_layer.data) == 0:
                raise FLVERExportError(f"UV layer {uv_layer.name} contains no data.")
            uv_layer.data.foreach_get("uv", loop_uvs[uv_i].ravel())

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
            loop_vertex_colors=[loop_vertex_color],
            loop_uvs=loop_uvs,
            faces=faces,
        )

        # Apply Blender -> FromSoft transformations.
        merged_mesh.swap_vertex_yz(tangents=True, bitangents=True)
        merged_mesh.invert_vertex_uv(invert_u=False, invert_v=True)

        p = time.perf_counter()
        flver.submeshes = merged_mesh.split_mesh(
            submesh_info,
            use_submesh_bone_indices=True,  # TODO: for DS1
            max_bones_per_submesh=38,  # TODO: for DS1
            unused_bone_indices_are_minus_one=True,
        )
        self.info(f"Split mesh into {len(flver.submeshes)} submeshes in {time.perf_counter() - p} s.")

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
        if get_bl_prop(edit_bone, "Is Unused", bool, default=False):
            flags |= FLVERBoneUsageFlags.UNUSED
        if get_bl_prop(edit_bone, "Is Used by Local Dummy", bool, default=False):
            flags |= FLVERBoneUsageFlags.DUMMY
        if get_bl_prop(edit_bone, "Is Used by Equipment", bool, default=False):
            flags |= FLVERBoneUsageFlags.cXXXX
        if get_bl_prop(edit_bone, "Is Used by Local Mesh", bool, default=False):
            flags |= FLVERBoneUsageFlags.MESH

        if bool(flags & FLVERBoneUsageFlags.UNUSED) and flags != 1:
            raise FLVERExportError(
                f"Bone '{edit_bone.name}' has 'Is Unused' enabled, but also has other usage flags set!"
            )

        return flags

    def export_dummy(
        self,
        bl_dummy: bpy.types.Object,
        reference_id: int,
        bl_bone_names: list[str],
        bl_bone_data: bpy.types.ArmatureBones,
    ) -> Dummy:
        """Create a single `FLVER.Dummy` from a Blender Dummy empty."""
        game_dummy = Dummy(
            reference_id=reference_id,  # stored in dummy name for editing convenience
            color_rgba=get_bl_prop(bl_dummy, "Color RGBA", tuple, default=(255, 255, 255, 255), callback=list),
            flag_1=get_bl_prop(bl_dummy, "Flag 1", int, default=True, callback=bool),
            use_upward_vector=get_bl_prop(bl_dummy, "Use Upward Vector", int, default=True, callback=bool),
            unk_x30=get_bl_prop(bl_dummy, "Unk x30", int, default=0),
            unk_x34=get_bl_prop(bl_dummy, "Unk x34", int, default=0),

        )
        parent_bone_name = get_bl_prop(bl_dummy, "Parent Bone Name", str, default="")
        if parent_bone_name and not bl_bone_data:
            self.warning(
                f"Tried to export dummy {bl_dummy.name} with parent bone '{parent_bone_name}', but this FLVER has "
                f"no armature. Dummy will be exported with parent bone index -1."
            )
            parent_bone_name = ""

        # We decompose the world matrix of the dummy to 'bypass' any attach bone to get its translate and rotate.
        # However, the translate may still be relative to a DIFFERENT parent bone, so we need to account for that below.
        bl_dummy_translate = bl_dummy.matrix_world.translation
        bl_dummy_rotmat = bl_dummy.matrix_world.to_3x3()

        if parent_bone_name:
            # Dummy's Blender 'world' translate is actually given in the space of this bone in the FLVER file.
            try:
                game_dummy.parent_bone_index = bl_bone_names.index(parent_bone_name)
            except ValueError:
                raise FLVERExportError(f"Dummy '{bl_dummy.name}' parent bone '{parent_bone_name}' not in Armature.")
            bl_parent_bone_matrix_inv = bl_bone_data[parent_bone_name].matrix_local.inverted()
            game_dummy.translate = BL_TO_GAME_VECTOR3(bl_parent_bone_matrix_inv @ bl_dummy_translate)
        else:
            game_dummy.parent_bone_index = -1
            game_dummy.translate = BL_TO_GAME_VECTOR3(bl_dummy_translate)

        forward, up = bl_rotmat_to_game_forward_up_vectors(bl_dummy_rotmat)
        game_dummy.forward = forward
        game_dummy.upward = up if game_dummy.use_upward_vector else Vector3.zero()

        if bl_dummy.parent_type == "BONE":  # NOTE: only possible for dummies parented to the Armature
            # Dummy has an 'attach bone' that is its Blender parent.
            try:
                game_dummy.attach_bone_index = bl_bone_names.index(bl_dummy.parent_bone)
            except ValueError:
                raise FLVERExportError(
                    f"Dummy '{bl_dummy.name}' attach bone (Blender parent) '{bl_dummy.parent_bone}' not in Armature."
                )
        else:
            # Dummy has no attach bone.
            game_dummy.attach_bone_index = -1

        return game_dummy

    def export_material(
        self,
        bl_material: bpy.types.Material,
        material_info: BaseMaterialShaderInfo,
        prefix: str,
    ) -> Material:
        """Create a FLVER material from Blender material custom properties and texture nodes.

        Texture nodes are validated against the provided MTD shader (by name or, preferably, direct MTD inspection). By
        default, the exporter will not permit any missing MTD textures (except 'g_DetailBumpmap') or any unknown texture
        nodes in the Blender shader. No other Blender shader information is used.

        Texture paths are taken from the 'Path[]' custom property on the Blender material, if it exists. Otherwise, the
        texture name is used as the path, with '.tga' appended.
        """
        name = bl_material.name.removeprefix(prefix).strip() if prefix else bl_material.name

        export_settings = self.context.scene.flver_export_settings  # type: FLVERExportSettings

        flver_material = Material(
            name=name,
            flags=get_bl_prop(bl_material, "Flags", int),
            mtd_path=get_bl_prop(bl_material, "MTD Path", str),
            unk_x18=get_bl_prop(bl_material, "Unk x18", int, default=0),
        )
        # TODO: Read `GXItem` custom properties.

        texture_nodes = {node.name: node for node in bl_material.node_tree.nodes if node.type == "TEX_IMAGE"}
        flver_textures = []
        for sampler_type in material_info.sampler_types:
            if sampler_type not in texture_nodes:
                # Only 'g_DetailBumpmap' can always be omitted from node tree entirely, as it's always empty (in DS1).
                if sampler_type != "g_DetailBumpmap":
                    raise FLVERExportError(
                        f"Could not find a shader node for required texture type '{sampler_type}' in material "
                        f"'{bl_material.name}'. You must create an Image Texture node and give it this name, "
                        f"then assign a Blender image to it. (You do not have to connect the node to any others.)"
                    )
                else:
                    texture_path = ""  # missing
            else:
                tex_node = texture_nodes.pop(sampler_type)
                if tex_node.image is None:
                    if sampler_type != "g_DetailBumpmap" and not export_settings.allow_missing_textures:
                        raise FLVERExportError(
                            f"Texture node '{tex_node.name}' in material '{bl_material.name}' has no image assigned. "
                            f"You must assign a Blender texture to this node, or enable 'Allow Missing Textures' in "
                            f"the FLVER export options."
                        )
                    texture_path = ""  # missing
                else:
                    texture_stem = Path(tex_node.image.name).stem
                    # Look for a custom 'Path[]' property on material, or default to lone texture name.
                    # Note that DS1, at least, works fine when full texture paths are omitted.
                    texture_path = bl_material.get(f"Path[{texture_stem}]", f"{texture_stem}.tga")

                    self.collected_texture_images[texture_stem] = tex_node.image

            flver_texture = Texture(
                path=texture_path,
                texture_type=sampler_type,
            )
            flver_textures.append(flver_texture)

        # TODO: Haven't quite figured out what the deal is with g_DetailBumpmap being present or absent, but for
        #  now, I'm allowing it to be written to the FLVER automatically.
        if "g_DetailBumpmap" in texture_nodes:
            tex_node = texture_nodes.pop("g_DetailBumpmap")
            if tex_node.image is None:
                texture_path = ""  # missing (fine)
            else:
                texture_stem = Path(tex_node.image.name).stem
                texture_path = bl_material.get(f"Path[{texture_stem}]", f"{texture_stem}.tga")
                self.collected_texture_images[texture_stem] = tex_node.image
            flver_texture = Texture(
                path=texture_path,
                texture_type="g_DetailBumpmap",
            )
            flver_textures.append(flver_texture)

        if texture_nodes:
            # Unknown node textures remain.
            if not export_settings.allow_unknown_texture_types:
                raise FLVERExportError(
                    f"Unknown texture types (node names) in material '{bl_material.name}': "
                    f"{list(texture_nodes.keys())}. You can enable 'Allow Unknown Texture Types' to export it anyway."
                )
            # TODO: Currently assuming that FLVER material texture order doesn't matter (due to texture type).
            #  If it does, we'll need to sort them here, probably based on node location Y.
            for unk_texture_type, tex_node in texture_nodes.items():
                sampler_type = tex_node.name
                if not tex_node.image:
                    if not export_settings.allow_missing_textures:
                        raise FLVERExportError(
                            f"Unknown texture node '{sampler_type}' in material '{bl_material.name}' has no image "
                            f"assigned. You must assign a Blender texture to this node, or enable 'Allow Missing "
                            f"Textures' in the FLVER export options."
                        )
                    texture_path = ""  # missing
                else:
                    texture_stem = Path(tex_node.image.name).stem
                    texture_path = bl_material.get(f"Path[{texture_stem}]", f"{texture_stem}.tga")
                    # TODO: Not collecting images of unknown texture types for export, currently.

                flver_texture = Texture(
                    path=texture_path,
                    texture_type=sampler_type,
                )
                flver_textures.append(flver_texture)

        flver_material.textures = flver_textures

        return flver_material

    def get_flver_props(self, bl_flver: bpy.types.MeshObject, game: Game) -> dict[str, tp.Any]:

        try:
            version_str = bl_flver["Version"]
        except KeyError:
            # Default is game-dependent.
            try:
                version = self.DEFAULT_VERSION[game.variable_name]
            except KeyError:
                raise ValueError(
                    f"Do not know default FLVER Version for game {game}. You must set 'Version' yourself on FLVER "
                    f"mesh '{bl_flver.name}' before exporting. It must be one of: {', '.join(v.name for v in Version)}"
                )
        else:
            try:
                version = Version[version_str]
            except KeyError:
                raise ValueError(
                    f"Invalid FLVER Version: '{version_str}'. It must be one of: {', '.join(v.name for v in Version)}"
                )

        # TODO: Any other game-specific fields?
        return dict(
            big_endian=get_bl_prop(bl_flver, "Is Big Endian", bool, default=False),
            version=version,
            unicode=get_bl_prop(bl_flver, "Unicode", bool, default=True),
            unk_x4a=get_bl_prop(bl_flver, "Unk x4a", bool, default=False),
            unk_x4c=get_bl_prop(bl_flver, "Unk x4c", int, default=0),
            unk_x5c=get_bl_prop(bl_flver, "Unk x5c", int, default=0),
            unk_x5d=get_bl_prop(bl_flver, "Unk x5d", int, default=0),
            unk_x68=get_bl_prop(bl_flver, "Unk x68", int, default=0),
        )

    def warning(self, msg: str):
        self.operator.report({"WARNING"}, msg)
        print(f"# WARNING: {msg}")

    def info(self, msg: str):
        self.operator.report({"INFO"}, msg)
        print(f"# INFO: {msg}")

    def detect_is_bind_pose(self, bl_flver_mesh: bpy.types.MeshObject) -> str:
        """Detect whether bone data should be read from EditBones or PoseBones.

        TODO: Best hack I can come up with, currently. I'm still not 100% sure if it's safe to assume that Submesh
         `is_bind_pose` is consistent (or SHOULD be consistent) across all submeshes in a single FLVER. Objects in
         particular could possibly lie somewhere between map pieces (False) and characters (True).
        """
        read_bone_type = ""
        warn_partial_bind_pose = False
        for bl_material in bl_flver_mesh.data.materials:
            is_bind_pose = get_bl_prop(bl_material, "Is Bind Pose", int, callback=bool)
            if is_bind_pose:  # typically: characters, objects, parts
                if not read_bone_type:
                    read_bone_type = "EDIT"  # write bone transforms from EditBones
                elif read_bone_type == "POSE":
                    warn_partial_bind_pose = True
                    read_bone_type = "EDIT"
                    break
            else:  # typically: map pieces
                if not read_bone_type:
                    read_bone_type = "POSE"  # write bone transforms from PoseBones
                elif read_bone_type == "EDIT":
                    warn_partial_bind_pose = True
                    break  # keep EDIT default
        if warn_partial_bind_pose:
            self.warning(
                "Some materials in FLVER use `Is Bind Pose = True` (bone data written to EditBones in Blender; typical "
                "for characters) and some do not (bone data written to PoseBones in Blender; typical for map pieces ). "
                "Soulstruct will read all bone data from EditBones for export."
            )
        return read_bone_type
