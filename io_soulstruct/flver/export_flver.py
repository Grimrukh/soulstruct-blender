from __future__ import annotations

__all__ = ["ExportFLVER", "ExportFLVERIntoBinder", "ExportFLVERToMapDirectory"]

import traceback
import typing as tp
from dataclasses import dataclass
from pathlib import Path

import bpy
from bpy.props import StringProperty, FloatProperty, BoolProperty, IntProperty
from bpy_extras.io_utils import ExportHelper

from soulstruct.containers import Binder, BinderEntry
from soulstruct.base.models.flver import FLVER, Version
from soulstruct.base.models.flver.material import Material, Texture
from soulstruct.base.models.flver.vertex import VertexBuffer, BufferLayout, MemberType
from soulstruct.base.models.mtd import MTD
from soulstruct.utilities.maths import Vector3, Matrix3

from io_soulstruct.utilities import *
from io_soulstruct.general import GlobalSettings
from .utilities import *

DEBUG_MESH_INDEX = None
DEBUG_VERTEX_INDICES = []


class MeshBuilder(tp.NamedTuple):
    """Holds data for a potentially multiprocessed mesh-building job."""
    bl_mesh: tp.Any
    game_mesh: FLVER.Mesh
    layout: BufferLayout
    buffer: VertexBuffer
    uv_count: int
    face_set_count: int
    cull_back_faces: bool


class MeshBuildResult(tp.NamedTuple):
    """Sent back to main process in a Queue."""
    game_vertices: list[FLVER.Mesh.Vertex]
    game_face_sets: list[FLVER.Mesh.FaceSet]
    local_bone_indices: list[int]


class ExportFLVERMixin:

    # Type hints for `LoggingOperator`.
    error: tp.Callable[[str], set[str]]
    warning: tp.Callable[[str], set[str]]
    info: tp.Callable[[str], set[str]]

    dcx_type: get_dcx_enum_property()

    base_edit_bone_length: FloatProperty(
        name="Base Edit Bone Length",
        description="Length of edit bones corresponding to bone scale 1",
        default=0.2,
        min=0.01,
    )

    use_mtd_binder: BoolProperty(
        name="Use MTD Binder",
        description="Try to find MTD shaders in game 'mtd' folder to validate node texture names",
        default=True,
    )

    allow_missing_textures: BoolProperty(
        name="Allow Missing Textures",
        description="Allow MTD-defined textures to have no node image data in Blender",
        default=False,
    )

    allow_unknown_texture_types: BoolProperty(
        name="Allow Unknown Texture Types",
        description="Allow and export Blender texture nodes that have non-MTD-defined texture types",
        default=False,
    )

    def get_single_selected_flver(self, context):
        if not context.selected_objects:
            return self.error("No FLVER mesh selected.")
        elif len(context.selected_objects) > 1:
            return self.error("Multiple objects selected. Exactly one FLVER mesh object must be selected.")
        bl_flver_root = context.selected_objects[0]
        if bl_flver_root.type != "MESH":
            return self.error(f"Selected object '{bl_flver_root.name}' is not a Mesh.")
        return bl_flver_root

    def get_export_settings(self, context):
        settings = GlobalSettings.get_scene_settings(context)
        return FLVERExportSettings(
            base_edit_bone_length=self.base_edit_bone_length,
            mtd_dict=settings.get_mtd_dict(context) if self.use_mtd_binder else None,
            allow_missing_textures=self.allow_missing_textures,
            allow_unknown_texture_types=self.allow_unknown_texture_types,
        )


class ExportFLVER(LoggingOperator, ExportHelper, ExportFLVERMixin):
    """Export one FLVER model from a Blender Armature parent to a file."""
    bl_idname = "export_scene.flver"
    bl_label = "Export FLVER"
    bl_description = "Export Blender object hierarchy to a FromSoftware FLVER model file"

    # ExportHelper mixin class uses this
    filename_ext = ".flver"

    filter_glob: StringProperty(
        default="*.flver;*.flver.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    @classmethod
    def poll(cls, context):
        """One FLVER mesh root object selected."""
        return len(context.selected_objects) == 1 and context.selected_objects[0].type == "MESH"

    def execute(self, context):
        bl_flver_root = self.get_single_selected_flver(context)
        dcx_type = GlobalSettings.resolve_dcx_type(self.dcx_type, "FLVER", False, context)

        flver_file_path = Path(self.filepath)
        self.to_object_mode()
        exporter = FLVERExporter(self, context, self.get_export_settings(context))

        try:
            flver = exporter.export_flver(bl_flver_root)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported FLVER. Error: {ex}")

        flver.dcx_type = dcx_type
        try:
            # Will create a `.bak` file automatically if absent.
            flver.write(flver_file_path)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write exported FLVER. Error: {ex}")
        self.info(f"Exported FLVER to: {flver_file_path}")

        return {"FINISHED"}


class ExportFLVERIntoBinder(LoggingOperator, ExportHelper, ExportFLVERMixin):
    """Export a single FLVER model from a Blender mesh into a chosen game binder (BND/BHD)."""
    bl_idname = "export_scene.flver_binder"
    bl_label = "Export FLVER Into Binder"
    bl_description = "Export a FLVER model file into a FromSoftware Binder (BND/BHD)"

    # ImportHelper mixin class uses this
    filename_ext = ".chrbnd"

    filter_glob: StringProperty(
        default="*.chrbnd;*.chrbnd.dcx;*.objbnd;*.objbnd.dcx;*.partsbnd;*.partsbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    overwrite_existing: BoolProperty(
        name="Overwrite Existing",
        description="Overwrite first existing '.flver{.dcx}' entry in Binder",
        default=True,
    )

    default_entry_id: IntProperty(
        name="Default ID",
        description="Binder entry ID to use if a '.flver{.dcx}' entry does not already exist in Binder. If left as -1, "
                    "an existing entry MUST be found for export to proceed",
        default=-1,
        min=-1,
    )

    default_entry_flags: IntProperty(
        name="Default Flags",
        description="Flags to set to Binder entry if it needs to be created",
        default=0x2,
    )

    default_entry_path: StringProperty(
        name="Default Path",
        description="Path to use for Binder entry if it needs to be created. Use {name} as a format "
                    "placeholder for the name of this FLVER object. Default is for DS1R `chrbnd.dcx` files",
        default="N:\\FRPG\\data\\INTERROOT_x64\\chr\\{name}\\{name}.flver",
    )

    @classmethod
    def poll(cls, context):
        """At least one Blender mesh selected."""
        return len(context.selected_objects) == 1 and all(obj.type == "MESH" for obj in context.selected_objects)

    def execute(self, context):
        bl_flver_root = self.get_single_selected_flver(context)

        dcx_type = GlobalSettings.resolve_dcx_type(self.dcx_type, "FLVER", True, context)

        self.to_object_mode()
        binder_file_path = Path(self.filepath)
        try:
            binder = Binder.from_path(binder_file_path)
        except Exception as ex:
            return self.error(f"Could not load Binder file '{binder_file_path}'. Error: {ex}.")

        exporter = FLVERExporter(self, context, self.get_export_settings(context))

        try:
            flver = exporter.export_flver(bl_flver_root)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot create exported FLVER from Blender object '{bl_flver_root}'. Error: {ex}")

        flver_entries = binder.find_entries_matching_name(r".*\.flver(\.dcx)?")
        if not flver_entries:
            if self.default_entry_id == -1:
                return self.error("No FLVER files found in Binder and default entry ID was left as -1.")
            if self.default_entry_id in binder.entries_by_id:
                if not self.overwrite_existing:
                    return self.error(
                        f"Binder entry {self.default_entry_id} already exists in Binder and overwrite is disabled."
                    )
                flver_entry = binder.entries_by_id[self.default_entry_id]
            else:
                # Create new entry.
                entry_path = self.default_entry_path.format(name=bl_flver_root.name)
                flver_entry = BinderEntry(
                    b"", entry_id=self.default_entry_id, path=entry_path, flags=self.default_entry_flags
                )
        else:
            if not self.overwrite_existing:
                return self.error("FLVER file already exists in Binder and overwrite is disabled.")

            if len(flver_entries) > 1:
                self.warning(f"Multiple FLVER files found in Binder. Replacing first: {flver_entries[0].name}")
            flver_entry = flver_entries[0]

        flver.dcx_type = dcx_type

        try:
            flver_entry.set_from_binary_file(flver)  # DCX will default to None here from exporter function
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write exported FLVER. Error: {ex}")

        try:
            # Will create a `.bak` file automatically if absent.
            binder.write()
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write Binder with new FLVER. Error: {ex}")

        return {"FINISHED"}


class ExportFLVERToMapDirectory(LoggingOperator, ExportHelper, ExportFLVERMixin):
    bl_idname = "export_scene_map.flver"
    bl_label = "Export Map Piece"
    bl_description = (
        "Export selected Blender meshes to same-named FLVER map piece model files in game `map` directory"
    )

    @classmethod
    def poll(cls, context):
        """One or more Meshes selected."""
        return (
            len(context.selected_objects) > 0
            and all(obj.type == "MESH" and obj.name[0] == "m" for obj in context.selected_objects)
        )

    def execute(self, context):
        if not context.selected_objects:
            return self.error("No FLVER mesh objects selected.")
        for flver_obj in context.selected_objects:
            if flver_obj.type != "MESH":
                return self.error(f"Selected object '{flver_obj.name}' is not a Mesh.")

        settings = GlobalSettings.get_scene_settings(context)
        game_directory = settings.game_directory
        map_stem = settings.map_stem
        dcx_type = settings.resolve_dcx_type(self.dcx_type, "FLVER", False, context)

        if not game_directory or not map_stem:
            return self.error("Game directory and map stem must be set in Blender's Soulstruct global settings.")

        settings.save_settings()

        if not (map_dir_path := Path(game_directory, "map", map_stem)).is_dir():
            return self.error(f"Invalid game map directory: {map_dir_path}")

        if not context.selected_objects:
            return self.error("No FLVER mesh objects selected.")

        self.to_object_mode()

        exporter = FLVERExporter(self, context, self.get_export_settings(context))

        for flver_obj in context.selected_objects:
            if flver_obj.type != "MESH":
                return self.error(f"Selected object '{flver_obj.name}' is not a Mesh.")
            flver_obj: bpy.types.MeshObject
            flver_name = flver_obj.name.split(" ")[0] + ".flver"  # DCX will be added automatically below if needed
            try:
                flver = exporter.export_flver(flver_obj)
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Cannot get exported FLVER. Error: {ex}")
            flver.dcx_type = dcx_type
            try:
                # Will create a `.bak` file automatically if absent, and add `.dcx` extension if necessary.
                flver.write(map_dir_path / flver_name)
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Cannot write exported FLVER. Error: {ex}")
            self.info(f"Exported FLVER to: {map_dir_path / flver_name}")

        return {"FINISHED"}


# TODO: 'Export FLVER To CHRBND' auto operator


@dataclass(slots=True)
class FLVERExportSettings:
    base_edit_bone_length: float = 0.2
    mtd_dict: dict[str, MTD] | None = None
    allow_missing_textures: bool = False
    allow_unknown_texture_types: bool = False


@dataclass(slots=True)
class FLVERExporter:

    operator: LoggingOperator
    context: bpy.types.Context
    settings: FLVERExportSettings

    @staticmethod
    def get_flver_props(bl_flver: bpy.types.Object) -> dict[str, tp.Any]:
        # TODO: Fields and defaults are tailored to DS1 map pieces.
        return dict(
            big_endian=get_bl_prop(bl_flver, "Is Big Endian", bool, default=False),
            version=get_bl_prop(bl_flver, "Version", str, default="DarkSouls_A", callback=Version.__getitem__),
            unicode=get_bl_prop(bl_flver, "Unicode", bool, default=True),
            unk_x4a=get_bl_prop(bl_flver, "Unk x4a", int, default=False, callback=bool),
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

    def detect_is_bind_pose(self, bl_meshes) -> str:
        """Detect whether bone data should be read from EditBones or PoseBones."""
        read_bone_type = ""
        warn_partial_bind_pose = False
        for mesh in bl_meshes:
            is_bind_pose = bool(mesh.get("is_bind_pose", False))
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
                "Some meshes in FLVER use `is_bind_pose` (bone data written to EditBones) and some do not "
                "(bone data written to PoseBones). Writing all bone data to EditBones."
            )
        return read_bone_type

    def export_flver(self, bl_flver_root: bpy.types.MeshObject) -> tp.Optional[FLVER]:
        """Create an entire FLVER from a Blender object.

        Exporter will recursively collect all meshes (1+), armatures (exactly 1), and 'dummy' empties (0+) for export.

        Root object must have certain 'FLVER' custom properties (see above).

        TODO: Currently only really tested for DS1 FLVERs.
        """
        if bl_flver_root.type != "MESH":
            raise FLVERExportError("Root FLVER object in Blender must be a Mesh.")

        flver = FLVER(**self.get_flver_props(bl_flver_root))
        layout_member_unk_x00 = get_bl_prop(bl_flver_root, "Layout Member Unk x00", int, default=0)

        bl_meshes = [bl_flver_root]  # type: list[bpy.types.MeshObject]
        bl_armature = None  # type: bpy.types.ArmatureObject | None
        bl_dummies = []  # type: list[tuple[bpy.types.Object, dict[str, tp.Any]]]

        for obj in bl_flver_root.children_recursive:
            obj: bpy.types.ArmatureObject | bpy.types.MeshObject | bpy.types.Object
            if obj.type == "ARMATURE":
                if bl_armature is not None:
                    self.warning(f"Multiple Armature objects found under FLVER root. Ignoring: {obj.name}")
                    continue
                # noinspection PyTypeChecker
                bl_armature = obj
            elif obj.type == "MESH":
                # Manually-separated submeshes found.
                # TODO: Maybe remove support for this, as it prevents genuine convenient nesting of meshes (e.g. Parts).
                bl_meshes.append(obj)
            elif obj.type == "EMPTY":
                # Check for required 'unk_x30' custom property to detect dummies.
                if obj.get("Unk x30") is None:
                    self.warning(
                        f"Empty child of FLVER '{obj.name}' ignored. (Missing 'unk_x30' Dummy property and possibly "
                        f"other required properties and proper Dummy name; see docs.)"
                    )
                    continue

                dummy_dict = parse_dummy_name(obj.name)
                if dummy_dict is None:
                    self.warning(
                        f"Could not interpret Dummy name: '{obj.name}'. Ignoring it. Format should be: \n"
                        f"    `[other_model] {{Name}} Dummy<index> [reference_id]` "
                        f"    where `[other_model]` is an optional prefix used only for attached equipment FLVERs"
                    )
                # TODO: exclude dummies with wrong 'other_model' prefix, depending on whether c0000 or that equipment
                #  is being exported. Currently excluding all dummies with any 'other_model'.
                if not dummy_dict["other_model"]:
                    bl_dummies.append((obj, dummy_dict))
                if dummy_dict["name"] != bl_flver_root.name:
                    self.warning(
                        f"Dummy '{obj.name}' has unexpected FLVER name prefix '{dummy_dict['name']}. Exporting anyway."
                    )
            else:
                self.warning(f"Non-Mesh, non-Empty Child object '{obj.name}' of FLVER ignored.")

        if not bl_armature:
            raise FLVERExportError(f"No Armature child of {bl_flver_root.name} found to export.")
        # There do not have to be any dummies.

        # Sort dummies and meshes by 'human sorting' on Blender name (should match order in Blender hierarchy view).
        bl_dummies.sort(key=lambda o: natural_keys(o[0].name))
        bl_meshes.sort(key=lambda o: natural_keys(o.name))

        read_bone_type = self.detect_is_bind_pose(bl_meshes)
        self.info(
            f"Exporting FLVER '{bl_flver_root.name}' with bone data from {read_bone_type.capitalize()}Bones."
        )
        flver.bones, bl_bone_names, bone_arma_transforms = self.create_bones(bl_armature, read_bone_type)
        flver.set_bone_armature_space_transforms(bone_arma_transforms)

        # Make FLVER root active object again.
        self.context.view_layer.objects.active = bl_flver_root

        # noinspection PyUnresolvedReferences
        bl_bone_data = bl_armature.data.bones  # type: bpy.types.ArmatureBones
        for bl_dummy, dummy_dict in bl_dummies:
            game_dummy = self.create_dummy(bl_dummy, dummy_dict["reference_id"], bl_bone_names, bl_bone_data)
            flver.dummies.append(game_dummy)

        # TODO: Current choosing default vertex buffer layout based on read bone type, which in terms depends on
        #  `mesh.is_bind_pose` at FLVER import. All a bit messily wired together...
        self.create_meshes_materials_layouts(
            flver,
            bl_meshes,
            bl_bone_names,
            use_chr_layout=read_bone_type == "EDIT",
            material_prefix=bl_flver_root.name,
            layout_member_unk_x00=layout_member_unk_x00,
        )

        flver.sort_mesh_bone_indices()

        # TODO: Bone bounding box space seems to be always local to the bone for characters and always in armature space
        #  for map pieces. Not sure about objects, could be some of each (haven't found any non-origin bones that any
        #  vertices are weighted to with `is_bind_pose=True`). This is my temporary hack since we are already using
        #  'read_bone_type == POSE' as a marker for map pieces.
        flver.refresh_bounding_boxes(
            refresh_bone_bounding_boxes=True,
            bone_bounding_boxes_in_armature_space=read_bone_type == "POSE",
        )

        return flver

    def create_meshes_materials_layouts(
        self,
        flver: FLVER,
        bl_meshes,
        bl_bone_names: list[str],
        use_chr_layout: bool,
        material_prefix: str,
        layout_member_unk_x00: int,
    ):
        """Iterate over all FLVER meshes (usually just one), split them based on material, and create those materials
        if necessary.

        NOTE: Separately Blender mesh objects will ALWAYS be split in the FLVER (possibly with the same `Material`).
        That is, only split your Blender meshes up to manually split the FLVER meshes up. (This is generally not
        necessary or recommended!)

        NOTE: Does NOT check if two materials are identical. Every Blender material that is actually used by at least
        one Blender mesh face will be exported as a separate FLVER material. The string `material_prefix` (plus a space)
        will be removed from these Blender material names if applicable (as material names are NOT unique identifiers
        across FromSoft models and may co-exist in one Blend file).
        """

        # Maps Blender material names to created FLVER material index, corresponding buffer layout index, and UV counts,
        # as the same material may be re-used across sub-meshes.
        bl_to_flver_materials = {}  # type: dict[str, tuple[int, int, int]]

        # Create vertex member defaults for re-use. Though mutable, these will never be modified here.
        # TODO: If the FLVER returned by the exporter ever becomes modifiable by the user before writing, these defaults
        #  will all need to be copied per vertex to avoid complete catastrophe.
        empty = []
        v3_zero = [0.0] * 3
        v4_zero = [0.0] * 4
        v4_int_zero = [0] * 4

        self.info(f"Exporting {len(bl_meshes)} Blender meshes to FLVER model...")

        for bl_mesh in bl_meshes:
            bl_mesh_data = bl_mesh.data  # type: bpy.types.Mesh
            bl_mesh_props = self.get_mesh_props(bl_mesh)

            # Create all FLVER materials for this Blender mesh (even if they are not used by any faces) unless already
            # created by a previous Blender mesh. Also track max UV count for layer access.
            uv_counts = []
            for bl_material in bl_mesh.data.materials:
                if bl_material.name in bl_to_flver_materials:
                    uv_counts.append(bl_to_flver_materials[bl_material.name][2])
                    continue  # material already created
                flver_material, mtd_info = self.create_material(bl_material, prefix=material_prefix)
                # TODO: Choose default layout factory with an export enum.
                layout_factory = BufferLayoutFactory(layout_member_unk_x00)
                if use_chr_layout:
                    buffer_layout = layout_factory.get_ds1_chr_buffer_layout(
                        has_two_texture_slots=mtd_info.has_two_slots,
                    )
                else:
                    buffer_layout = layout_factory.get_ds1_map_buffer_layout(
                        is_multiple=mtd_info.has_two_slots,
                        is_lightmap=mtd_info.has_lightmap,
                        extra_uv_maps=mtd_info.extra_uv_maps,
                        no_tangents=mtd_info.no_tangents,
                    )
                # Check if the same layout has already been defined to support another material. Layouts can be
                # freely re-used across different materials if they are identical.
                try:
                    buffer_layout_index = flver.buffer_layouts.index(buffer_layout)
                except ValueError:
                    buffer_layout_index = len(flver.buffer_layouts)
                    flver.buffer_layouts.append(buffer_layout)

                uv_count = buffer_layout.get_uv_count()

                bl_to_flver_materials[bl_material.name] = (
                    len(flver.materials),
                    buffer_layout_index,
                    uv_count,
                )
                flver.materials.append(flver_material)
                uv_counts.append(uv_count)
                self.operator.info(f"Created FLVER material: {bl_material.name} (UV count: {uv_count})")

            # Maps Blender face material index to FLVER mesh and buffer layout instances (for this Blender mesh).
            flver_mesh_data = {}  # type: dict[int, tuple[FLVER.Mesh, dict[int, FLVER.Mesh.Vertex], BufferLayout]]

            # Mesh data layer accessors.
            try:
                uv_layers = [bl_mesh_data.uv_layers.get(f"UVMap{i}") for i in range(1, max(uv_counts) + 1)]
            except KeyError:
                raise FLVERExportError(
                    f"Expected {max(uv_counts)} UV maps named 'UVMap1', 'UVMap2', etc. for mesh {bl_mesh.name}."
                )
            vertex_color_layer = bl_mesh_data.vertex_colors.get("VertexColors")

            # Extract all layer loop data now.
            # TODO: Did this to solve some weird address issue in Blender, but will want this for eventual NumPy accel
            #  anyway.
            loops_uvs = [list(uv_layer.data) for uv_layer in uv_layers]
            loop_vertex_colors = list(vertex_color_layer.data)

            vertex_groups = bl_mesh.vertex_groups  # for bone indices/weights

            bl_mesh_data = bl_mesh.data  # type: bpy.types.Mesh
            # TODO: The tangent and bitangent of each vertex should be calculated from the UV map that is effectively
            #  serving as the normal map ('_n' displacement texture) for that vertex. However, for multi-texture mesh
            #  materials, vertex alpha blends two normal maps together, so the UV map for (bi)tangents will vary across
            #  the mesh and would require external calculation here. Working on that...
            #  For now, just calculating tangents from the first UV map.
            try:
                # TODO: This function calls the required `calc_normals_split()` automatically, but if it was replaced,
                #  a separate call of that would be needed. I believe it reads the (rather inaccessible) custom split
                #  per-loop normal data (pink lines in overlay) and writes them to `loop.normal`.
                bl_mesh_data.calc_tangents(uvmap="UVMap1")
                # bl_mesh_data.calc_normals_split()
            except RuntimeError:
                raise RuntimeError(
                    "Could not calculate vertex tangents from 'UVMap1'. Make sure the mesh is triangulated and not "
                    "empty (delete any empty mesh)."
                )

            bl_loop_normals = [loop.normal for loop in bl_mesh_data.loops]

            no_bone_warning_done = False

            # TODO: This is the slow part: iterating over every face, and every loop of each face.
            #  If the faces, loops, and relevant data layers can be retrieved in bulk and passed to a C++ module, that
            #  could be a big boost.
            for face in bl_mesh_data.polygons:
                if len(face.loop_indices) != 3:
                    raise FLVERExportError(
                        f"Cannot export a FLVER mesh with non-triangular faces. "
                        f"Please triangulate mesh: {bl_mesh.name}"
                    )

                if face.material_index not in flver_mesh_data:
                    # New Mesh creation for this Blender submesh (even if material already exists in FLVER).
                    mesh = FLVER.Mesh()
                    flver.meshes.append(mesh)
                    bl_material = bl_mesh_data.materials[face.material_index]
                    mesh.material_index, buffer_layout_index, uv_count = bl_to_flver_materials[bl_material.name]
                    mesh.default_bone_index = bl_mesh_props["Default Bone Index"][face.material_index]
                    mesh.vertex_buffers = [VertexBuffer(layout_index=buffer_layout_index)]
                    mesh.face_sets = [
                        FLVER.Mesh.FaceSet(
                            flags=i,
                            unk_x06=0,  # TODO: define default in 'game-specific' dict?
                            triangle_strip=False,  # triangle strips are too hard to compute
                            cull_back_faces=bl_mesh_props["Cull Back Faces"][face.material_index],
                            vertex_indices=[],
                        )
                        for i in range(bl_mesh_props["Face Set Count"][face.material_index])
                    ]

                    layout = flver.buffer_layouts[buffer_layout_index]
                    mesh_vert_dict = {}
                    flver_mesh_data[face.material_index] = (mesh, mesh_vert_dict, layout)
                else:
                    # Add face to an existing FLVER mesh already created for this Blender submesh and this material.
                    mesh, mesh_vert_dict, layout = flver_mesh_data[face.material_index]

                flver_face = []

                for loop_index in face.loop_indices:
                    loop = bl_mesh_data.loops[loop_index]
                    v_i = loop.vertex_index
                    bl_v = bl_mesh_data.vertices[v_i]

                    # We construct the hashable 'unique vertex key' and only re-use an existing FLVER vertex if
                    # it has the same key (which will usually be the case). In FLVER files, a change in essentially ANY
                    # vertex member (position, normal, UV, color, bone weights, etc.) will create a new vertex, as the
                    # FLVER file has no concept of 'loops' (per-face vertex 'instances').

                    if layout.has_member_type(MemberType.Position):
                        position = BL_TO_GAME_VECTOR3_LIST(bl_v.co)
                    else:
                        position = v3_zero  # should never happen

                    if layout.has_member_type(MemberType.BoneIndices):

                        has_weights = layout.has_member_type(MemberType.BoneWeights)

                        global_bone_indices = []
                        bone_weights = []
                        for vertex_group in bl_v.groups:  # only one for map pieces; max of 4 for other FLVER types
                            # Find mesh vertex group with this index.
                            for mesh_group in vertex_groups:
                                if vertex_group.group == mesh_group.index:
                                    try:
                                        bone_index = bl_bone_names.index(mesh_group.name)
                                    except ValueError:
                                        raise ValueError(
                                            f"Vertex is weighted to invalid bone name: '{mesh_group.name}'."
                                            )
                                    global_bone_indices.append(bone_index)
                                    # don't waste time calling `weight()` for non-weight layouts (map pieces)
                                    if has_weights:
                                        bone_weights.append(mesh_group.weight(v_i))
                                    break
                        if len(global_bone_indices) > 4:
                            raise ValueError(
                                f"Vertex cannot be weighted to >4 bones ({len(global_bone_indices)} is too many)."
                            )
                        elif len(global_bone_indices) == 0:
                            if len(bl_bone_names) == 1:
                                # Omitted bone indices can be assumed to be the only bone in the skeleton.
                                if not no_bone_warning_done:
                                    print(
                                        f"WARNING: Vertex in mesh '{bl_mesh.name}' is not weighted to any bones. "
                                        f"Weighting in 'map piece' mode to only bone in skeleton: '{bl_bone_names[0]}'"
                                    )
                                    no_bone_warning_done = True
                                global_bone_indices = v4_int_zero
                                bone_weights = v4_zero
                            else:
                                # Can't guess which bone to weight to. Raise error.
                                raise ValueError(
                                    "Vertex is not weighted to any bones, and there are >1 bones to choose from."
                                )

                        bone_indices = []  # local
                        for global_bone_index in global_bone_indices:
                            try:
                                # Check if mesh already has this bone index from a previous vertex.
                                bone_indices.append(mesh.bone_indices.index(global_bone_index))
                            except ValueError:
                                # First vertex to be weighted to this bone index in mesh.
                                # NOTE: Unfortunately, to sort the mesh bone indices, we would have to iterate over all
                                # vertices a second time, so we just append them in the order they appear. There is an
                                # optional `FLVER` method that sorts them, but the user must call it themselves.
                                bone_indices.append(len(mesh.bone_indices))
                                mesh.bone_indices.append(global_bone_index)

                        while len(bone_weights) < 4:
                            bone_weights.append(0.0)

                        if has_weights:
                            while len(bone_indices) < 4:
                                bone_indices.append(0)  # zero-weight indices are zero
                        elif len(bone_indices) == 1:
                            bone_indices *= 4  # duplicate single-element list to four-element list
                        else:  # vertex (likely new) with no bone indices
                            bone_indices = v4_int_zero
                    else:
                        bone_indices = v4_int_zero
                        bone_weights = v4_zero

                    if not bone_indices:
                        raise FLVERExportError(
                            f"Vertex with position {position} has no bone indices. Every vertex must have at least one."
                        )

                    if layout.has_member_type(MemberType.Normal):
                        # TODO: 127 is the only value seen in DS1 models thus far for `normal[3]`. Will need to store as
                        #  a custom vertex property for other games that use it.
                        normal = [*BL_TO_GAME_VECTOR3_LIST(bl_loop_normals[loop_index]), 127.0]
                    else:
                        normal = v4_zero

                    if layout.has_member_type(MemberType.UV):
                        uv_count = layout.get_uv_count()
                        uvs = []
                        for uv_index in range(uv_count):
                            # bl_uv = uv_layers[uv_index].data[loop_index].uv
                            bl_uv = loops_uvs[uv_index][loop_index].uv
                            uvs.append((bl_uv[0], 1 - bl_uv[1], 0.0))  # V inverted and zero Z coordinate
                    else:
                        uvs = empty

                    if layout.has_member_type(MemberType.Tangent):
                        # TODO: Only supports one tangent (DS1). (I'm surprised multi-texture materials don't use 2+?)
                        tangents = [[*BL_TO_GAME_VECTOR3_LIST(loop.tangent), -1.0]]
                    else:
                        tangents = empty  # happens very rarely (e.g. `[Dn]` shaders)

                    if layout.has_member_type(MemberType.Bitangent):
                        bitangent = [*BL_TO_GAME_VECTOR3_LIST(loop.bitangent), -1.0]
                    else:
                        bitangent = v4_zero

                    if layout.has_member_type(MemberType.VertexColor):
                        # TODO: Only supports one color (DS1).
                        colors = [tuple(loop_vertex_colors[loop_index].color)]
                    else:
                        colors = empty  # not yet observed (all DS1 materials use vertex colors)

                    # Hashable vertex key, to find if a suitable vertex already exists for this face.
                    v_key = hash(tuple((tuple(x) for x in (
                        position, bone_indices, bone_weights, uvs, colors, normal, tangents[0], bitangent
                    ))))

                    try:
                        mesh_vertex_index = mesh_vert_dict[v_key]
                    except KeyError:
                        # Create new `Vertex`.
                        mesh_vertex_index = mesh_vert_dict[v_key] = len(mesh_vert_dict)
                        mesh.vertices.append(
                            FLVER.Mesh.Vertex(
                                position=position,
                                bone_weights=bone_weights,
                                bone_indices=bone_indices,
                                normal=normal,
                                uvs=uvs,
                                tangents=tangents,
                                bitangent=bitangent,
                                colors=colors,
                            )
                        )
                    flver_face.append(mesh_vertex_index)

                mesh.face_sets[0].vertex_indices += flver_face

        # All LOD face sets are duplicated from the first.
        # TODO: Setting up actual face sets (which share vertices but are decimated) in Blender would be very annoying.
        #  Would basically need a 'mesh decimating' algorithm that ONLY removes vertices. Not outrageous...
        for mesh in flver.meshes:
            for lod_face_set in mesh.face_sets[1:]:
                lod_face_set.vertex_indices = mesh.face_sets[0].vertex_indices.copy()

        return flver

    def get_mesh_props(self, bl_mesh_obj: bpy.types.MeshObject) -> dict[str, list[bool | int]]:
        """Each property can be a single value (all materials) or an array matching the mesh material count."""
        material_count = len(bl_mesh_obj.material_slots)
        props = {}

        for prop_name, prop_type, default_value in (
            ("Is Bind Pose", bool, False),  # NOTE: default is suitable for Map Pieces but not Characters
            ("Cull Back Faces", bool, False),
            ("Default Bone Index", int, 0),
            ("Face Set Count", int, 1),
        ):
            material_prop_values = []
            for material_index in range(material_count):
                try:
                    material_prop_value = bl_mesh_obj[f"Material[{material_index}] {prop_name}"]
                except KeyError:
                    self.info(
                        f"Setting FLVER Mesh '{prop_name}' to default {default_value} for material {material_index}."
                    )
                    material_prop_values.append(default_value)
                else:
                    material_prop_values.append(prop_type(material_prop_value))
            props[prop_name] = material_prop_values
        return props

    def create_bones(
        self, bl_armature_obj, read_bone_type: str
    ) -> tuple[list[FLVER.Bone], list[str], list[tuple[Vector3, Matrix3, Vector3]]]:
        """Create `FLVER` bones from Blender armature bones and get their armature space transforms.

        Bone transform data may be read from either EDIT mode (typical for characters and objects) or POSE mode (typical
        for map pieces). This is specified by `read_bone_type`.
        """

        # We need `EditBone` mode to retrieve custom properties, even if reading the actual transforms from pose later.
        self.context.view_layer.objects.active = bl_armature_obj
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="EDIT", toggle=False)

        game_bones = []
        game_arma_transforms = []  # type: list[tuple[Vector3, Matrix3, Vector3]]  # translate, rotate matrix, scale
        edit_bone_names = [edit_bone.name for edit_bone in bl_armature_obj.data.edit_bones]
        if len(set(edit_bone_names)) != len(edit_bone_names):
            raise FLVERExportError("Bone names of armature are not all unique.")

        for edit_bone in bl_armature_obj.data.edit_bones:
            game_bone_name = edit_bone.name
            while game_bone_name.endswith(" <DUPE>"):
                game_bone_name = game_bone_name.removesuffix(" <DUPE>")

            game_bone = FLVER.Bone(
                name=game_bone_name,
                unk_x3c=get_bl_prop(edit_bone, "Unk x3c", int, default=0),
            )

            if edit_bone.parent:
                parent_bone_name = edit_bone.parent.name
                game_bone.parent_index = edit_bone_names.index(parent_bone_name)
            else:
                game_bone.parent_index = -1
            child_name = edit_bone.get("Child Name", None)
            if child_name is not None:
                try:
                    game_bone.child_index = edit_bone_names.index(child_name)
                except IndexError:
                    raise ValueError(f"Cannot find child '{child_name}' of bone '{edit_bone.name}'.")
            else:
                game_bone.child_index = -1
            next_sibling_name = edit_bone.get("Next Sibling Name", None)
            if next_sibling_name is not None:
                try:
                    game_bone.next_sibling_index = edit_bone_names.index(next_sibling_name)
                except IndexError:
                    raise ValueError(f"Cannot find next sibling '{next_sibling_name}' of bone '{edit_bone.name}'.")
            else:
                game_bone.next_sibling_index = -1
            prev_sibling_name = edit_bone.get("Previous Sibling Name", None)
            if prev_sibling_name is not None:
                try:
                    game_bone.previous_sibling_index = edit_bone_names.index(prev_sibling_name)
                except IndexError:
                    raise ValueError(f"Cannot find previous sibling '{prev_sibling_name}' of bone '{edit_bone.name}'.")
            else:
                game_bone.previous_sibling_index = -1

            if read_bone_type == "EDIT":
                # Get armature-space bone transform from rigged `EditBone` (characters and objects, typically).
                bl_translate = edit_bone.matrix.translation
                bl_rotmat = edit_bone.matrix.to_3x3()  # get rotation submatrix
                game_arma_translate = BL_TO_GAME_VECTOR3(bl_translate)
                game_arma_rotmat = BL_TO_GAME_MAT3(bl_rotmat)
                s = edit_bone.length / self.settings.base_edit_bone_length
                # NOTE: only uniform scale is supported for these "is_bind_pose" mesh bones
                game_arma_scale = s * Vector3.one()
                game_arma_transforms.append((game_arma_translate, game_arma_rotmat, game_arma_scale))

            game_bones.append(game_bone)

        self.operator.to_object_mode()

        if read_bone_type == "POSE":
            # Get armature-space bone transform from PoseBone (map pieces).
            # Note that non-uniform bone scale is supported here (and is actually used in some old vanilla map pieces).
            for game_bone, pose_bone in zip(game_bones, bl_armature_obj.pose.bones):

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
                game_arma_transforms.append((
                    game_arma_translate,
                    game_arma_rotmat,
                    game_arma_scale,
                ))

        return game_bones, edit_bone_names, game_arma_transforms

    @staticmethod
    def create_dummy(
        bl_dummy: bpy.types.Object,
        reference_id: int,
        bl_bone_names: list[str],
        bl_bone_data: bpy.types.ArmatureBones,
    ) -> FLVER.Dummy:
        """Create a single `FLVER.Dummy` from a Blender Dummy empty."""
        game_dummy = FLVER.Dummy(
            reference_id=reference_id,  # stored in dummy name for editing convenience
            color_rgba=get_bl_prop(bl_dummy, "Color RGBA", tuple, default=(255, 255, 255, 255), callback=list),
            flag_1=get_bl_prop(bl_dummy, "Flag 1", int, default=True, callback=bool),
            use_upward_vector=get_bl_prop(bl_dummy, "Use Upward Vector", int, default=True, callback=bool),
            unk_x30=get_bl_prop(bl_dummy, "Unk x30", int, default=0),
            unk_x34=get_bl_prop(bl_dummy, "Unk x34", int, default=0),

        )
        parent_bone_name = get_bl_prop(bl_dummy, "parent_bone_name", str, default="")

        # We decompose the world matrix of the dummy to 'bypass' any attach bone to get its translate and rotate.
        # However, the translate may still be relative to a parent bone, so we need to account for that below.
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

        if bl_dummy.parent_type == "BONE":
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

    def create_material(self, bl_material: bpy.types.Material, prefix: str) -> tuple[Material, MTDInfo]:
        """Create a FLVER material from Blender material custom properties and texture nodes.

        Texture nodes are validated against the provided MTD shader (by name or, preferably, direct MTD inspection). By
        default, the exporter will not permit any missing MTD textures (except 'g_DetailBumpmap') or any unknown texture
        nodes in the Blender shader. No other Blender shader information is used.

        Texture paths are taken from the 'Path[]' custom property on the Blender material, if it exists. Otherwise, the
        texture name is used as the path, with '.tga' appended.
        """
        name = bl_material.name.removeprefix(prefix).strip() if prefix else bl_material.name

        flver_material = Material(
            name=name,
            flags=get_bl_prop(bl_material, "Flags", int),
            gx_index=get_bl_prop(bl_material, "GX Index", int, default=-1),  # TODO: not yet supported
            mtd_path=get_bl_prop(bl_material, "MTD Path", str),
            unk_x18=get_bl_prop(bl_material, "Unk x18", int, default=0),
        )

        mtd_info = None  # type: MTDInfo | None
        if self.settings.mtd_dict:
            if flver_material.mtd_name in self.settings.mtd_dict:
                mtd_info = MTDInfo.from_mtd(self.settings.mtd_dict[flver_material.mtd_name])
            else:
                self.warning(f"MTD '{flver_material.mtd_name}' not found in MTD dict. Guessing textures from name...")
        if mtd_info is None:
            mtd_info = MTDInfo.from_mtd_name(flver_material.mtd_name)

        node_textures = {node.name: node for node in bl_material.node_tree.nodes if node.type == "TEX_IMAGE"}
        flver_textures = []
        for texture_type in mtd_info.texture_types:
            if texture_type not in node_textures:
                # Only 'g_DetailBumpmap' can always be omitted from node tree entirely, as it's always empty (in DS1).
                if texture_type != "g_DetailBumpmap":
                    raise FLVERExportError(
                        f"Could not find a shader node for required texture type '{texture_type}' in material "
                        f"'{bl_material}'."
                    )
                else:
                    texture_path = ""  # missing
            else:
                tex_node = node_textures.pop(texture_type)
                if tex_node.image is None:
                    if texture_type != "g_DetailBumpmap" and not self.settings.allow_missing_textures:
                        raise FLVERExportError(
                            f"Texture node '{tex_node.name}' in material '{bl_material}' has no image assigned."
                        )
                    texture_path = ""  # missing
                else:
                    texture_stem = Path(tex_node.image.name).stem
                    # Look for a custom 'Path[]' property on material, or default to lone texture name.
                    # Note that DS1, at least, works fine when full texture paths are omitted.
                    texture_path = bl_material.get(f"Path[{texture_stem}]", f"{texture_stem}.tga")
            flver_texture = Texture(
                path=texture_path,
                texture_type=texture_type,
            )
            flver_textures.append(flver_texture)

        if node_textures:
            # Unknown node textures remain.
            if not self.settings.allow_unknown_texture_types:
                raise FLVERExportError(
                    f"Unknown texture types (node names) in material '{bl_material}': {list(node_textures.keys())}"
                )
            # TODO: Currently assuming that FLVER material texture order doesn't matter (due to texture type).
            #  If it does, we'll need to sort them here, probably based on node location Y.
            for unk_texture_type, tex_node in node_textures.items():
                texture_type = tex_node.name
                if not tex_node.image:
                    if not self.settings.allow_missing_textures:
                        raise FLVERExportError(
                            f"Unknown texture node '{texture_type}' in material '{bl_material}' has no image assigned."
                        )
                    texture_path = ""  # missing
                else:
                    texture_stem = Path(tex_node.image.name).stem
                    texture_path = bl_material.get(f"Path[{texture_stem}]", f"{texture_stem}.tga")
                flver_texture = Texture(
                    path=texture_path,
                    texture_type=texture_type,
                )
                flver_textures.append(flver_texture)

        flver_material.textures = flver_textures

        return flver_material, mtd_info
