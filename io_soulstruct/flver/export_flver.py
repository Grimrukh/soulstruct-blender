from __future__ import annotations

__all__ = ["ExportFLVER", "ExportFLVERIntoBinder", "ExportFLVERToMapDirectory", "ExportMapDirectorySettings"]

import traceback
import typing as tp
from multiprocessing import Pool, Queue
from pathlib import Path

import bmesh
import bpy
from bpy.props import StringProperty, FloatProperty, BoolProperty, IntProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper
from soulstruct.containers.dcx import DCXType

from soulstruct.containers import Binder, BinderEntry
from soulstruct.base.models.flver import FLVER, Version
from soulstruct.base.models.flver.vertex import VertexBuffer, BufferLayout, LayoutMember, MemberType, MemberFormat
from soulstruct.base.models.flver.material import MTDInfo
from soulstruct.utilities.maths import Vector2, Vector3, Matrix3

from io_soulstruct.utilities import *
from .utilities import *

# TODO: Doesn't work yet, as I can't pickle Blender Objects at least.
#    - Would need to convert all the triangles/faces/loops/UVs etc. to Python data first.
USE_MULTIPROCESSING = False

DEBUG_MESH_INDEX = None
DEBUG_VERTEX_INDICES = []


TEXTURE_TYPES = (
    "g_Diffuse",
    "g_Specular",
    "g_Bumpmap",
    "g_Diffuse_2",
    "g_Specular_2",
    "g_Bumpmap_2",
    "g_Bumpmap_3",
    "g_Height",
    "g_Lightmap",
    "g_DetailBumpmap",
)


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


class ExportMapDirectorySettings(bpy.types.PropertyGroup):
    """Manages settings for quickly exporting Map Piece FLVERs into a game's `map` directory."""

    game_directory: bpy.props.StringProperty(
        name="Game Directory",
        description="Directory of FromSoftware game files",
        subtype="DIR_PATH",
        default=get_last_game_directory(),
    )

    map_stem: bpy.props.StringProperty(
        name="Map Stem",
        description="Stem of FromSoftware game map name (e.g. 'm10_00_00_00')",
    )

    dcx_type: get_dcx_enum_property(DCXType.DS1_DS2)  # map FLVERs in DS1 are compressed


class ExportFLVERToMapDirectory(LoggingOperator):
    """Export FLVER model from a Blender Armature parent to an auto-named map piece file in the given map directory."""
    bl_idname = "export_scene_map.flver"
    bl_label = "Export FLVER to Map Directory"
    bl_description = (
        "Export a prepared Blender object hierarchy to a FromSoftware "
        "FLVER model file in a given `map` directory"
    )

    base_edit_bone_length: FloatProperty(
        name="Base Edit Bone Length",
        description="Length of edit bones corresponding to bone scale 1",
        default=0.2,
        min=0.01,
    )

    @classmethod
    def poll(cls, context):
        try:
            return context.selected_objects[0].type == "ARMATURE"
        except IndexError:
            return False

    def execute(self, context):
        game_directory = context.scene.export_map_directory_settings.game_directory
        map_stem = context.scene.export_map_directory_settings.map_stem
        dcx_type = DCXType[context.scene.export_map_directory_settings.dcx_type]

        # Save last `game_directory` (even if this function fails).
        last_game_directory_path = Path(__file__).parent / "../game_directory.txt"
        last_game_directory_path.write_text(game_directory)

        map_dir_path = Path(game_directory) / f"map/{map_stem}"

        if not map_dir_path.is_dir():
            return self.error(f"Invalid game map directory: {map_dir_path}")

        selected_objs = [obj for obj in context.selected_objects]
        if not selected_objs:
            return self.error("No FLVER parent object selected.")
        elif len(selected_objs) > 1:
            return self.error("Multiple objects selected. Exactly one FLVER parent object must be selected.")
        flver_parent_obj = selected_objs[0]
        flver_name = flver_parent_obj.name.split(" ")[0] + ".flver"  # DCX will be added automatically below if needed
        if bpy.ops.object.mode_set.poll():
            # Must be in OBJECT mode for export, as some data (e.g. UVs) is not accessible in EDIT mode.
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        exporter = FLVERExporter(self, context, base_edit_bone_length=self.base_edit_bone_length)

        try:
            flver = exporter.export_flver(flver_parent_obj)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported FLVER. Error: {ex}")
        else:
            flver.dcx_type = dcx_type
            try:
                # Will create a `.bak` file automatically if absent, and add `.dcx` extension if necessary.
                flver.write(map_dir_path / flver_name)
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Cannot write exported FLVER. Error: {ex}")
            self.info(f"Exported FLVER to: {map_dir_path / flver_name}")

        return {"FINISHED"}


class ExportFLVER(LoggingOperator, ExportHelper):
    """Export FLVER model from a Blender Armature parent to a file."""
    bl_idname = "export_scene.flver"
    bl_label = "Export FLVER"
    bl_description = "Export a prepared Blender object hierarchy to a FromSoftware FLVER model file."

    # ExportHelper mixin class uses this
    filename_ext = ".flver"

    filter_glob: StringProperty(
        default="*.flver;*.flver.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    dcx_type: get_dcx_enum_property(DCXType.DS1_DS2)  # standalone DSR FLVERs are compressed

    base_edit_bone_length: FloatProperty(
        name="Base Edit Bone Length",
        description="Length of edit bones corresponding to bone scale 1",
        default=0.2,
        min=0.01,
    )

    # TODO: Options to:
    #   - Detect appropriate MSB and update transform of this model instance (if unique) (low priority).

    @classmethod
    def poll(cls, context):
        try:
            return context.selected_objects[0].type == "ARMATURE"
        except IndexError:
            return False

    def execute(self, context):
        selected_objs = [obj for obj in context.selected_objects]
        if not selected_objs:
            return self.error("No FLVER parent object selected.")
        elif len(selected_objs) > 1:
            return self.error("Multiple objects selected. Exactly one FLVER parent object must be selected.")
        flver_parent_obj = selected_objs[0]
        if bpy.ops.object.mode_set.poll():
            # Must be in OBJECT mode for export, as some data (e.g. UVs) is not accessible in EDIT mode.
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        exporter = FLVERExporter(self, context, base_edit_bone_length=self.base_edit_bone_length)

        try:
            flver = exporter.export_flver(flver_parent_obj)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported FLVER. Error: {ex}")
        else:
            flver.dcx_type = DCXType[self.dcx_type]
            try:
                # Will create a `.bak` file automatically if absent.
                flver.write(Path(self.filepath))
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Cannot write exported FLVER. Error: {ex}")
            self.info(f"Exported FLVER to: {self.filepath}")

        return {"FINISHED"}


class ExportFLVERIntoBinder(LoggingOperator, ImportHelper):
    """Export FLVER model from a Blender Armature parent into a chosen game binder (BND/BHD)."""
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

    dcx_type: get_dcx_enum_property(DCXType.Null)  # no compression in DSR binders

    base_edit_bone_length: FloatProperty(
        name="Base Edit Bone Length",
        description="Length of edit bones corresponding to bone scale 1",
        default=0.2,
        min=0.01,
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
        try:
            return context.selected_objects[0].type == "ARMATURE"
        except IndexError:
            return False

    def execute(self, context):
        print("Executing export...")

        selected_objs = [obj for obj in context.selected_objects]
        if not selected_objs:
            return self.error("No FLVER parent object selected.")
        elif len(selected_objs) > 1:
            return self.error("Multiple objects selected. Exactly one FLVER parent object must be selected.")
        flver_parent_obj = selected_objs[0]
        if bpy.ops.object.mode_set.poll():
            # Must be in OBJECT mode for export, as some data (e.g. UVs) is not accessible in EDIT mode.
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        exporter = FLVERExporter(self, context, base_edit_bone_length=self.base_edit_bone_length)

        try:
            flver = exporter.export_flver(flver_parent_obj)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported FLVER. Error: {ex}")

        try:
            binder = Binder.from_path(self.filepath)
        except Exception as ex:
            return self.error(f"Could not load Binder file. Error: {ex}.")

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
                # Create new entry. TODO: Currently no DCX.
                entry_path = self.default_entry_path.format(name=flver_parent_obj.name)
                flver_entry = BinderEntry(
                    b"", entry_id=self.default_entry_id, path=entry_path, flags=self.default_entry_flags
                )
        else:
            if not self.overwrite_existing:
                return self.error("FLVER file already exists in Binder and overwrite is disabled.")

            if len(flver_entries) > 1:
                self.warning(f"Multiple FLVER files found in Binder. Replacing first: {flver_entries[0].name}")
            flver_entry = flver_entries[0]

        dcx_type = DCXType[self.dcx_type]
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


class FLVERExporter:

    operator: LoggingOperator
    name: str
    layout_member_unk_x00: int
    props: BlenderPropertyManager
    base_edit_bone_length: float

    def __init__(self, operator: LoggingOperator, context, base_edit_bone_length=0.2):
        self.operator = operator
        self.context = context
        self.base_edit_bone_length = base_edit_bone_length
        self.props = BlenderPropertyManager({  # TODO: DS1 values (tailored for map pieces, specifically)
            "FLVER": {
                "big_endian": BlenderProp(int, False, bool),
                "version": BlenderProp(str, "DarkSouls_A", Version.__getitem__),
                "unicode": BlenderProp(int, True, bool),
                "unk_x4a": BlenderProp(int, False, bool),
                "unk_x4c": BlenderProp(int, 0),
                "unk_x5c": BlenderProp(int, 0),
                "unk_x5d": BlenderProp(int, 0),
                "unk_x68": BlenderProp(int, 0),
                "layout_member_unk_x00": BlenderProp(int, 0, do_not_assign=True),
            },
            "Bone": {
                "unk_x3c": BlenderProp(int, 0),
            },
            "Mesh": {
                "face_set_count": BlenderProp(int, 1, do_not_assign=True),
                "cull_back_faces": BlenderProp(int, False, bool, do_not_assign=True),
                "default_bone_index": BlenderProp(int, 0),
                "is_bind_pose": BlenderProp(int, False, bool),  # default suitable for Map Pieces
            },
            "Material": {
                "flags": BlenderProp(int),
                "mtd_path": BlenderProp(str),
                "texture_count": BlenderProp(int, do_not_assign=True),
                "gx_index": BlenderProp(int, -1),
                "unk_x18": BlenderProp(int, 0),
                "texture_path_prefix": BlenderProp(str, "", do_not_assign=True),
            },
            "Texture": {
                "texture_type": BlenderProp(str),
                "path_suffix": BlenderProp(str, do_not_assign=True),  # added to material prefix above
                "unk_x10": BlenderProp(int, 1),
                "unk_x11": BlenderProp(int, True, bool),
                "unk_x14": BlenderProp(float, 0.0),
                "unk_x18": BlenderProp(float, 0.0),
                "unk_x1C": BlenderProp(float, 0.0),
                "scale": BlenderProp(tuple, (1.0, 1.0), Vector2),
            },
            "LayoutMember": {
                "unk_x00": BlenderProp(int, 0),
            },
            "Dummy": {
                "color_rgba": BlenderProp(tuple, (255, 255, 255, 255), list),
                # "reference_id": BlenderProp(int),  # stored in dummy name for editing convenience
                "parent_bone_name": BlenderProp(str, "", do_not_assign=True),
                "flag_1": BlenderProp(int, True, bool),
                "use_upward_vector": BlenderProp(int, True, bool),
                "unk_x30": BlenderProp(int, 0),
                "unk_x34": BlenderProp(int, 0),
            },
        })

    def warning(self, msg: str):
        self.operator.report({"WARNING"}, msg)
        print(f"# WARNING: {msg}")

    def member(self, member_type: MemberType, member_format: MemberFormat, index=0):
        return LayoutMember(
            member_type=member_type,
            member_format=member_format,
            index=index,
            unk_x00=self.layout_member_unk_x00,
        )

    def detect_is_bind_pose(self, bl_meshes) -> str:
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
                f"Some meshes in FLVER {self.name} use `is_bind_pose` (bone data written to EditBones) and some do not "
                f"(bone data written to PoseBones). Writing all bone data to EditBones."
            )
        return read_bone_type

    def export_flver(self, bl_armature) -> tp.Optional[FLVER]:
        """Create an entire FLVER from a Blender object.

        Expected object structure:

            Armature
                Dummies (Empty)
                    ... (probably none for map pieces)
                Mesh 0 Obj (Mesh)
                Mesh 1 Obj (Mesh)
                Mesh 2 Obj (Mesh)
                ...

        TODO: Currently only really tested for DS1 FLVERs.
        """
        self.name = bl_armature.name  # should just be original/intended FLVER file stem, e.g. `c1234` or `m1000B0A12`
        flver = FLVER()
        extra_flver_props = self.props.get_all(bl_armature, flver, "FLVER")
        self.layout_member_unk_x00 = extra_flver_props["layout_member_unk_x00"]

        bl_child_objs = [obj for obj in bpy.data.objects if obj.parent is bl_armature]
        bl_meshes = []
        bl_dummies = []

        # Scan children of Armature for meshes (Blender meshes)and dummies (Blender empties).
        for child in bl_child_objs:
            if child.type == "MESH":
                bl_meshes.append(child)
            elif child.type == "EMPTY":
                # Check for required 'unk_x30' custom property to detect dummies.
                if child.get("unk_x30") is None:
                    self.warning(
                        f"Empty child of FLVER '{child.name}' ignored. (Missing 'unk_x30' Dummy property and possibly "
                        f"other required properties and proper Dummy name; see docs.)"
                    )
                    continue

                dummy_dict = parse_dummy_name(child.name)
                if dummy_dict is None:
                    self.warning(
                        f"Could not interpret Dummy name: '{child.name}'. Ignoring it. Format should be: \n"
                        f"    `[other_model] Dummy<index> [reference_id]` "
                        f"    where `[other_model]` is an optional prefix used only for attached equipment FLVERs"
                    )
                # TODO: exclude dummies with wrong 'other_model' prefix, depending on whether c0000 or that equipment
                #  is being exported. Currently excluding all dummies with any 'other_model'.
                if not dummy_dict["other_model"]:
                    bl_dummies.append((child, dummy_dict))
            else:
                self.warning(f"Non-Mesh, non-Empty Child object '{child.name}' of FLVER ignored.")

        if not bl_meshes:
            self.operator.report({"ERROR"}, f"No mesh children of {self.name} found to export.")
            return None

        # Sort dummies/meshes by 'human sorting' on Blender name (should match order in Blender hierarchy view).
        bl_dummies.sort(key=lambda obj: natural_keys(obj[0].name))
        bl_meshes.sort(key=lambda obj: natural_keys(obj.name))

        read_bone_type = self.detect_is_bind_pose(bl_meshes)
        self.operator.info(f"Exporting FLVER '{self.name}' with bone data from {read_bone_type.capitalize()}Bones.")
        flver.bones, bl_bone_names, bone_arma_transforms = self.create_bones(bl_armature, read_bone_type)
        flver.set_bone_armature_space_transforms(bone_arma_transforms)

        bl_bone_data = bl_armature.data.bones
        for bl_dummy, dummy_dict in bl_dummies:
            game_dummy = self.create_dummy(bl_dummy, dummy_dict["reference_id"], bl_bone_names, bl_bone_data)
            flver.dummies.append(game_dummy)

        # Set up basic Mesh properties.
        mesh_builders = []
        material_hashes = []
        for bl_mesh in bl_meshes:
            # TODO: Current choosing default vertex buffer layout based on read bone type, which in terms depends on
            #  `mesh.is_bind_pose` at FLVER import. All a bit messily wired together...
            game_mesh, game_material, game_layout, mesh_builder = self.create_mesh_material_layout(
                bl_mesh, flver.buffer_layouts, use_chr_layout=read_bone_type == "EDIT"
            )
            # Check if a `Material` with the same hash already exists and re-use that if so.
            material_hash = hash(game_material)
            try:
                game_mesh.material_index = material_hashes.index(material_hash)
            except ValueError:  # new unique `Material` (including its `Texture`s)
                game_mesh.material_index = len(flver.materials)
                flver.materials.append(game_material)
                material_hashes.append(material_hash)
            flver.meshes.append(game_mesh)
            if game_layout is not None:
                flver.buffer_layouts.append(game_layout)
            mesh_builders.append(mesh_builder)

        # Process mesh vertices, faces, and bones.
        if USE_MULTIPROCESSING:
            queue = Queue()  # type: Queue[MeshBuildResult]

            worker_args = [
                (builder, bl_bone_names, queue)
                for builder in mesh_builders
            ]

            with Pool() as pool:
                pool.starmap(build_game_mesh_mp, worker_args)  # blocks here until all done

            builder_index = 0
            while not queue.empty():
                build_result = queue.get()
                game_mesh = mesh_builders[builder_index].game_mesh
                game_mesh.vertices = build_result.game_vertices
                game_mesh.face_sets = build_result.game_face_sets
                game_mesh.bone_indices = build_result.local_bone_indices
                # mesh_builders[builder_index].buffer.vertex_count = len(build_result.game_vertices)
        else:
            for builder in mesh_builders:
                print(f"Building FLVER mesh: {builder.bl_mesh.name}")
                game_vertices, game_face_sets, mesh_local_bone_indices = build_game_mesh(
                    builder, bl_bone_names
                )
                print(f"    --> {len(game_vertices)} vertices")
                if not game_vertices or not game_face_sets:
                    raise ValueError(
                        f"Cannot export a FLVER mesh with no vertices and/or faces: {builder.bl_mesh.name}"
                    )
                builder.game_mesh.vertices = game_vertices
                builder.game_mesh.face_sets = game_face_sets
                builder.game_mesh.bone_indices = mesh_local_bone_indices

        flver.sort_mesh_bone_indices()
        flver.refresh_bounding_boxes(refresh_bone_bounding_boxes=True)

        return flver

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
            raise ValueError(f"Bone names of '{self.name}' armature are not all unique.")

        for edit_bone in bl_armature_obj.data.edit_bones:
            game_bone_name = edit_bone.name
            while game_bone_name.endswith(" <DUPE>"):
                game_bone_name = game_bone_name.removesuffix(" <DUPE>")

            game_bone = FLVER.Bone(name=game_bone_name)

            self.props.get_all(edit_bone, game_bone, "Bone")
            if edit_bone.parent:
                parent_bone_name = edit_bone.parent.name
                game_bone.parent_index = edit_bone_names.index(parent_bone_name)
            else:
                game_bone.parent_index = -1
            child_name = edit_bone.get("child_name", None)
            if child_name is not None:
                # TODO: Check if this is set IFF bone has exactly one child, which can be auto-detected.
                try:
                    game_bone.child_index = edit_bone_names.index(child_name)
                except IndexError:
                    raise ValueError(f"Cannot find child '{child_name}' of bone '{edit_bone.name}'.")
            else:
                game_bone.child_index = -1
            next_sibling_name = edit_bone.get("next_sibling_name", None)
            if next_sibling_name is not None:
                try:
                    game_bone.next_sibling_index = edit_bone_names.index(next_sibling_name)
                except IndexError:
                    raise ValueError(f"Cannot find next sibling '{next_sibling_name}' of bone '{edit_bone.name}'.")
            else:
                game_bone.next_sibling_index = -1
            prev_sibling_name = edit_bone.get("previous_sibling_name", None)
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
                s = edit_bone.length / self.base_edit_bone_length
                game_arma_scale = s * Vector3.one()
                game_arma_transforms.append((game_arma_translate, game_arma_rotmat, game_arma_scale))

            game_bones.append(game_bone)

        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        if read_bone_type == "POSE":
            # Get armature-space bone transform from PoseBone (map pieces).
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
                # Warn if scale is not uniform, then use X scale anyway.
                if not is_uniform(pose_bone.scale, rel_tol=0.001):
                    self.warning(
                        f"Non-uniform scale detected on bone '{pose_bone.name}' of armature '{bl_armature_obj.name}'. "
                        f"Using X scale only: {pose_bone.scale.x}"
                    )
                game_arma_scale = pose_bone.scale.x * Vector3.one()  # always forced to be uniform in FLVER
                game_arma_transforms.append((
                    game_arma_translate,
                    game_arma_rotmat,
                    game_arma_scale,
                ))

        return game_bones, edit_bone_names, game_arma_transforms

    def create_dummy(self, bl_dummy, reference_id: int, bl_bone_names: list[str], bl_bone_data: list) -> FLVER.Dummy:
        """Create a single `FLVER.Dummy` from a Blender Dummy empty."""
        game_dummy = FLVER.Dummy(reference_id=reference_id)
        extra_props = self.props.get_all(bl_dummy, game_dummy, "Dummy")

        # We decompose the world matrix of the dummy to 'bypass' any attach bone to get its translate and rotate.
        # However, the translate may still be relative to a parent bone, so we need to account for that below.
        bl_dummy_translate = bl_dummy.matrix_world.translation
        bl_dummy_rotmat = bl_dummy.matrix_world.to_3x3()

        if parent_bone_name := extra_props["parent_bone_name"]:
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

    def create_mesh_material_layout(
        self, bl_mesh, buffer_layouts: list[BufferLayout], use_chr_layout: bool
    ) -> tuple[FLVER.Mesh, FLVER.Material, tp.Optional[BufferLayout], MeshBuilder]:
        game_mesh = FLVER.Mesh()
        extra_mesh_props = self.props.get_all(bl_mesh, game_mesh, "Mesh")

        # Process material.
        if len(bl_mesh.material_slots) != 1:
            raise ValueError(f"Mesh {bl_mesh.name} must have exactly one material.")
        bl_material = bl_mesh.material_slots[0].material
        game_material = FLVER.Material()
        game_material.name = bl_material.name.removeprefix(self.name).strip()
        extra_mat_props = self.props.get_all(bl_material, game_material, "Material", bl_prop_prefix="material_")
        texture_path_prefix = extra_mat_props["texture_path_prefix"]
        found_texture_types = set()
        for i in range(extra_mat_props["texture_count"]):
            game_texture = FLVER.Material.Texture()
            extra_tex_props = self.props.get_all(bl_material, game_texture, "Texture", bl_prop_prefix=f"texture[{i}]_")
            if extra_tex_props["path_suffix"]:
                game_texture.path = texture_path_prefix + extra_tex_props["path_suffix"]
            else:  # empty suffix means entire path is empty
                game_texture.path = ""
            tex_type = game_texture.texture_type
            if tex_type not in TEXTURE_TYPES:
                self.warning(f"Unrecognized FLVER Texture type: {tex_type}")
            if tex_type in found_texture_types:
                self.warning(f"Ignoring duplicate of texture type '{tex_type}' in Material {game_material.name}.")
            else:
                found_texture_types.add(tex_type)
                game_material.textures.append(game_texture)

        # NOTE: Extra textures not required by this shader (e.g., 'g_DetailBumpmap' for most of them) are still
        # written, but missing required textures will raise an error here.
        mtd_name = game_material.mtd_name
        mtd_info = game_material.get_mtd_info()
        self.validate_found_textures(mtd_info, found_texture_types, mtd_name)

        # TODO: Choose default layout factory with an export enum.
        if use_chr_layout:
            game_layout = self.get_ds1_chr_buffer_layout(
                is_multiple=mtd_info.multiple,
            )
        else:
            game_layout = self.get_ds1_map_buffer_layout(
                is_multiple=mtd_info.multiple,
                is_lightmap=mtd_info.lightmap,
                is_foliage=mtd_info.foliage,
                no_tangents=mtd_info.no_tangents,
            )
        uv_count = game_layout.get_uv_count()

        return_layout = True
        if game_layout in buffer_layouts:
            # Already defined.
            vertex_buffer = VertexBuffer(layout_index=buffer_layouts.index(game_layout))
            return_layout = False
        else:
            vertex_buffer = VertexBuffer(layout_index=len(buffer_layouts))
            # Returned `buffer_layout` will be added to FLVER.

        game_mesh.vertex_buffers = [vertex_buffer]

        mesh_builder = MeshBuilder(
            bl_mesh,
            game_mesh,
            game_layout,
            vertex_buffer,
            uv_count,
            extra_mesh_props.get("face_set_count", 1),
            extra_mesh_props.get("cull_back_faces", False),
        )

        return game_mesh, game_material, (game_layout if return_layout else None), mesh_builder

    @staticmethod
    def validate_found_textures(mtd_info: MTDInfo, found_texture_types: set[str], mtd_name: str):
        for tex_type in ("Diffuse", "Specular", "Bumpmap"):
            if getattr(mtd_info, tex_type.lower()):
                if f"g_{tex_type}" not in found_texture_types:
                    raise ValueError(f"Texture type 'g_{tex_type}' required for material with MTD '{mtd_name}'.")
                if mtd_info.multiple and f"g_{tex_type}_2" not in found_texture_types:
                    raise ValueError(f"Texture type 'g_{tex_type}_2' required for material with MTD '{mtd_name}'.")
        for tex_type in ("Lightmap", "Height"):
            if getattr(mtd_info, tex_type.lower()) and f"g_{tex_type}" not in found_texture_types:
                raise ValueError(f"Texture type 'g_{tex_type}' required for material with MTD '{mtd_name}'.")

    def get_ds1_map_buffer_layout(
        self, is_multiple=False, is_lightmap=False, is_foliage=False, no_tangents=False
    ) -> BufferLayout:
        members = [  # always present
            self.member(MemberType.Position, MemberFormat.Float3),
            self.member(MemberType.BoneIndices, MemberFormat.Byte4B),
            self.member(MemberType.Normal, MemberFormat.Byte4C),
            # Tangent/Bitangent will be inserted here if needed.
            self.member(MemberType.VertexColor, MemberFormat.Byte4C),
            # UV/UVPair will be appended here if needed.
        ]

        if not no_tangents:
            members.insert(3, self.member(MemberType.Tangent, MemberFormat.Byte4C))
            if is_multiple:  # has Bitangent
                members.insert(4, self.member(MemberType.Bitangent, MemberFormat.Byte4C))
        elif is_multiple:  # has Bitangent but not Tangent (probably never happens)
            members.insert(3, self.member(MemberType.Bitangent, MemberFormat.Byte4C))

        if is_foliage:  # four UVs (regardless of lightmap, and never has multiple)
            members.append(self.member(MemberType.UV, MemberFormat.UVPair))
            members.append(self.member(MemberType.UV, MemberFormat.UVPair))
        elif is_multiple and is_lightmap:  # three UVs
            members.append(self.member(MemberType.UV, MemberFormat.UVPair))
            members.append(self.member(MemberType.UV, MemberFormat.UV, index=1))
        elif is_multiple or is_lightmap:  # two UVs
            members.append(self.member(MemberType.UV, MemberFormat.UVPair))
        else:  # one UV
            members.append(self.member(MemberType.UV, MemberFormat.UV))

        return BufferLayout(members)

    def get_ds1_chr_buffer_layout(self, is_multiple=False) -> BufferLayout:
        """Default buffer layout for character (and probably object) materials in DS1R."""
        members = [
            self.member(MemberType.Position, MemberFormat.Float3),
            self.member(MemberType.BoneIndices, MemberFormat.Byte4B),
            self.member(MemberType.BoneWeights, MemberFormat.Short4ToFloat4A),
            self.member(MemberType.Normal, MemberFormat.Byte4C),
            self.member(MemberType.Tangent, MemberFormat.Byte4C),
            self.member(MemberType.VertexColor, MemberFormat.Byte4C),
        ]
        if is_multiple:  # has Bitangent and UVPair
            members.insert(5, self.member(MemberType.Bitangent, MemberFormat.Byte4C))
            members.append(self.member(MemberType.UV, MemberFormat.UVPair))
        else:  # one UV
            members.append(self.member(MemberType.UV, MemberFormat.UV))

        return BufferLayout(members)


def build_game_mesh_mp(builder: MeshBuilder, bone_names: list[str], queue: Queue):
    game_vertices, game_face_sets, local_bone_indices = build_game_mesh(builder, bone_names)
    build_result = MeshBuildResult(game_vertices, game_face_sets, local_bone_indices)
    queue.put(build_result)


def build_game_mesh(
    mesh_builder: MeshBuilder, bl_bone_names: list[str],
) -> tuple[list[FLVER.Mesh.Vertex], list[FLVER.Mesh.FaceSet], list[int]]:
    """Process Blender vertices, faces, and bone-weighted vertex groups into FLVER equivalents."""

    bl_mesh = mesh_builder.bl_mesh.data
    mesh_vertex_groups = mesh_builder.bl_mesh.vertex_groups
    layout = mesh_builder.layout

    bl_mesh.calc_normals_split()  # TODO: I think `calc_tangents` calls this automatically.
    try:
        bl_mesh.calc_tangents(uvmap="UVMap1")
    except RuntimeError:
        # TODO: should I ever use UVMap2?
        # try:
        #     bl_mesh.calc_tangents(uvmap="UVMap2")
        # except RuntimeError:
        raise RuntimeError("Could not find UVMap1 or UVMap2. If this mesh is empty, delete it.")

    # Temporary BMesh is triangulated, but is never saved back to Blender.
    bm = bmesh.new()
    bm.from_mesh(bl_mesh)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # Dictionary that maps created FLVER vertex indices to `(position, uvs, colors)` triples that mark them as unique.
    flver_v_indices = {}

    game_face_sets = [
        FLVER.Mesh.FaceSet(
            flags=i,
            unk_x06=0,  # TODO: define default in dict
            triangle_strip=False,  # vertices are ALWAYS exported as triangles, not strips (too hard to compute)
            cull_back_faces=mesh_builder.cull_back_faces,
            vertex_indices=[],
        )
        for i in range(mesh_builder.face_set_count)
    ]

    # NOTE: Vertices that do not appear in any Blender faces will NOT be exported.
    triangles = bm.calc_loop_triangles()

    game_vertices = []
    mesh_local_bone_indices = []

    # Create defaults once to reuse. Though mutable, these will never be modified here.
    empty = []
    v3_zero = [0.0] * 3
    v4_zero = [0.0] * 4
    v4_int_zero = [0] * 4

    # noinspection PyTypeChecker
    for f_i, face in enumerate(triangles):
        flver_face = []
        for loop in face:
            v_i = loop.vert.index
            mesh_loop = bl_mesh.loops[loop.index]

            if layout.has_member_type(MemberType.Position):
                position = BL_TO_GAME_VECTOR_LIST(bm.verts[v_i].co)
            else:
                position = v3_zero  # should never happen

            if layout.has_member_type(MemberType.BoneIndices):

                has_weights = layout.has_member_type(MemberType.BoneWeights)

                bl_v = bl_mesh.vertices[v_i]
                global_bone_indices = []
                bone_weights = []
                for vertex_group in bl_v.groups:  # only one for map pieces; max of 4 for other FLVER types
                    # Find mesh vertex group with this index.
                    for mesh_group in mesh_vertex_groups:
                        if vertex_group.group == mesh_group.index:
                            try:
                                bone_index = bl_bone_names.index(mesh_group.name)
                            except ValueError:
                                raise ValueError(f"Vertex is weighted to invalid bone name: '{mesh_group.name}'.")
                            global_bone_indices.append(bone_index)
                            if has_weights:  # don't waste time calling `weight()` for non-weight layouts (map pieces)
                                bone_weights.append(mesh_group.weight(v_i))
                            break
                if len(global_bone_indices) > 4:
                    raise ValueError(f"Vertex cannot be weighted to >4 bones ({len(global_bone_indices)} is too many).")

                bone_indices = []  # local
                for global_bone_index in global_bone_indices:
                    try:
                        # Check if mesh already has this bone index from a previous vertex.
                        bone_indices.append(mesh_local_bone_indices.index(global_bone_index))
                    except ValueError:
                        # First vertex to be weighted to this bone index in mesh.
                        # NOTE: Unfortunately, to sort the mesh bone indices, we would have to iterate over all vertices
                        # a second time, so we just append them in the order they appear. There is an optional `FLVER`
                        # method that sorts them, but the user must call it themselves.
                        bone_indices.append(len(mesh_local_bone_indices))
                        mesh_local_bone_indices.append(global_bone_index)

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

            if layout.has_member_type(MemberType.Normal):
                # TODO: 127 is the only value seen in DS1 models thus far for `normal[3]`. Will need to store as a
                #  custom vertex property for other games that use it.
                normal = [*BL_TO_GAME_VECTOR_LIST(mesh_loop.normal), 127.0]
            else:
                normal = v4_zero

            # Get UVs from loop. We always need to do this because even if the vertex has already been filled, we need
            # to check if this loop has different UVs and create a duplicate vertex if so.
            if layout.has_member_type(MemberType.UV):
                uvs = []
                for uv_index in range(1, mesh_builder.uv_count + 1):
                    try:
                        uv_layer = bl_mesh.uv_layers[f"UVMap{uv_index}"]
                    except KeyError:
                        raise KeyError(
                            f"Expected {mesh_builder.uv_count} UVs for mesh, but could not find 'UVMap{uv_index}'."
                        )
                    bl_uv = uv_layer.data[loop.index].uv
                    uvs.append((bl_uv[0], 1 - bl_uv[1], 0.0))  # FLVER UV always has Z coordinate (usually 0)
            else:
                uvs = empty

            if layout.has_member_type(MemberType.Tangent):
                tangents = [[*BL_TO_GAME_VECTOR_LIST(mesh_loop.tangent), -1.0]]
            else:
                tangents = empty  # happens very rarely (e.g. `[Dn]` shaders)

            if layout.has_member_type(MemberType.Bitangent):
                bitangent = [*BL_TO_GAME_VECTOR_LIST(mesh_loop.bitangent), -1.0]
            else:
                bitangent = v4_zero

            # Same with vertex colors. Though they are stored as a list, there should always only be one color layer.
            if layout.has_member_type(MemberType.VertexColor):
                colors = [tuple(bl_mesh.vertex_colors["VertexColors"].data[loop.index].color)]
            else:
                colors = empty  # not yet observed (all DS1 materials use vertex colors)

            v_key = (tuple(position), tuple(bone_indices), tuple(bone_weights), tuple(uvs), tuple(colors))  # hashable

            try:
                game_v_i = flver_v_indices[v_key]
            except KeyError:
                # Create new `Vertex`.
                game_v_i = flver_v_indices[v_key] = len(flver_v_indices)
                game_vertices.append(FLVER.Mesh.Vertex(
                    position=position,
                    bone_weights=bone_weights,
                    bone_indices=bone_indices,
                    normal=normal,
                    uvs=uvs,
                    tangents=tangents,
                    bitangent=bitangent,
                    colors=colors,
                ))
            flver_face.append(game_v_i)

        game_face_sets[0].vertex_indices += flver_face

    # All LOD face sets are duplicated from the first.
    # TODO: Setting up actual face sets (which share vertices) in Blender would be very annoying.
    for lod_face_set in game_face_sets[1:]:
        lod_face_set.vertex_indices = game_face_sets[0].vertex_indices.copy()

    return game_vertices, game_face_sets, mesh_local_bone_indices
