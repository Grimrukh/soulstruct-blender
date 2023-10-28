from __future__ import annotations

__all__ = ["ExportFLVER", "ExportFLVERIntoBinder", "QuickExportMapPieceFLVERs", "QuickExportCharacterFLVER"]

import time

import traceback
import typing as tp
from dataclasses import dataclass
from pathlib import Path

import numpy as np

import bpy
from bpy.props import StringProperty, FloatProperty, BoolProperty, IntProperty
from bpy_extras.io_utils import ExportHelper

from soulstruct.containers import Binder, BinderEntry, EntryNotFoundError
from soulstruct.base.models.flver import FLVER, Version, FLVERBone, Material, Texture, Dummy
from soulstruct.base.models.flver.vertex_array import *
from soulstruct.base.models.flver.mesh_tools import MergedMesh
from soulstruct.utilities.maths import Vector3, Matrix3

from io_soulstruct.general import *
from io_soulstruct.utilities import *
from .utilities import *

DEBUG_MESH_INDEX = None
DEBUG_VERTEX_INDICES = []


class ExportFLVERMixin:

    # Used by `ExportHelper`
    filename_ext = ".flver"

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

    @staticmethod
    def parse_flver_obj(obj: bpy.types.Object) -> tuple[bpy.types.MeshObject, tp.Optional[bpy.types.ArmatureObject]]:
        """Parse a Blender object into a Mesh and (optional) Armature object."""
        if obj.type == "MESH":
            mesh = obj
            armature = mesh.parent if mesh.parent is not None and mesh.parent.type == "ARMATURE" else None
        elif obj.type == "ARMATURE":
            armature = obj
            mesh_children = [child for child in armature.children if child.type == "MESH"]
            if not mesh_children:
                raise FLVERExportError(f"Armature '{armature.name}' has no Mesh children.")
            elif len(mesh_children) > 1:
                raise FLVERExportError(
                    f"Armature '{armature.name}' has multiple Mesh children. You must select the exact Mesh you want "
                    f"to export; this parent Armature will be used automatically."
                )
            mesh = mesh_children[0]
        else:
            raise FLVERExportError(f"Selected object '{obj.name}' is not a Mesh or Armature.")

        return mesh, armature

    @staticmethod
    def get_selected_flver(context) -> tuple[bpy.types.MeshObject, tp.Optional[bpy.types.ArmatureObject]]:
        """Get the Mesh and (optional) Armature components of a single selected FLVER object of either type."""
        if not context.selected_objects:
            raise FLVERExportError("No FLVER Mesh or Armature selected.")
        elif len(context.selected_objects) > 1:
            raise FLVERExportError("Multiple objects selected. Exactly one FLVER Mesh or Armature must be selected.")
        obj = context.selected_objects[0]
        return ExportFLVERMixin.parse_flver_obj(obj)

    @staticmethod
    def get_selected_flvers(context) -> list[tuple[bpy.types.MeshObject, tp.Optional[bpy.types.ArmatureObject]]]:
        """Get the Mesh and (optional) Armature components of ALL selected FLVER objects of either type."""
        if not context.selected_objects:
            raise FLVERExportError("No FLVER Meshes or Armatures selectesd.")
        return [
            ExportFLVERMixin.parse_flver_obj(obj)
            for obj in context.selected_objects
        ]

    def get_default_flver_stem(self, mesh, armature) -> str:
        """Returns the name that should be used (by default) for the exported FLVER, warning if the Mesh and Armature
        objects have different names."""
        name = mesh.name.split(" ")[0]
        if armature and (armature_name := armature.name.split(" ")[0]) != name:
            self.warning(
                f"Mesh '{name}' and Armature '{armature_name}' do not use the same FLVER name. Using Armature name."
            )
            return armature_name
        return name

    def get_export_settings(self, context):
        settings = GlobalSettings.get_scene_settings(context)
        return FLVERExportSettings(
            base_edit_bone_length=self.base_edit_bone_length,
            mtd_manager=settings.get_mtd_manager(context) if self.use_mtd_binder else None,
            allow_missing_textures=self.allow_missing_textures,
            allow_unknown_texture_types=self.allow_unknown_texture_types,
        )


class ExportFLVER(LoggingOperator, ExportHelper, ExportFLVERMixin):
    """Export one FLVER model from a Blender Armature parent to a file."""
    bl_idname = "export_scene.flver"
    bl_label = "Export Loose FLVER"
    bl_description = "Export Blender object hierarchy to a loose FromSoftware FLVER model file"

    filter_glob: StringProperty(
        default="*.flver;*.flver.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    @classmethod
    def poll(cls, context):
        """One FLVER Armature or Mesh object must be selected.

        If a Mesh is selected, it does not need an Armature parent - if it doesn't, a default FLVER skeleton with a
        single eponymous bone at the origin will be exported
        """
        return len(context.selected_objects) == 1 and context.selected_objects[0].type in {"MESH", "ARMATURE"}

    def execute(self, context):
        try:
            mesh, armature = self.get_selected_flver(context)
        except FLVERExportError as ex:
            return self.error(str(ex))

        dcx_type = GlobalSettings.resolve_dcx_type(self.dcx_type, "FLVER", False, context)

        flver_file_path = Path(self.filepath)
        self.to_object_mode()
        exporter = FLVERExporter(self, context, self.get_export_settings(context))
        name = flver_file_path.name.split(".")[0]

        try:
            flver = exporter.export_flver(mesh, armature, name=name)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported FLVER. Error: {ex}")

        flver.dcx_type = dcx_type
        try:
            # Will create a `.bak` file automatically if absent.
            written_path = flver.write(flver_file_path)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write exported FLVER. Error: {ex}")
        self.info(f"Exported FLVER to: {written_path}")

        return {"FINISHED"}


class ExportFLVERIntoBinder(LoggingOperator, ExportHelper, ExportFLVERMixin):
    """Export a single FLVER model from a Blender mesh into a chosen game binder (BND/BHD).

    TODO: Does not support multiple FLVERs yet, but some objects do have more than one.
    """
    bl_idname = "export_scene.flver_binder"
    bl_label = "Export FLVER Into Binder"
    bl_description = "Export a FLVER model file into a FromSoftware Binder (BND/BHD)"

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
        default=-1,  # TODO: default can very likely be set to 200 across all games
        min=-1,
    )

    default_entry_flags: IntProperty(
        name="Default Flags",
        description="Flags to set to Binder FLVER entry if it needs to be created",
        default=0x2,
    )

    default_entry_path: StringProperty(
        name="Default Path",
        description="Path to use for Binder FLVER entry if it needs to be created. Use {name} as a format "
                    "placeholder for the name of this FLVER object. Default is for DS1R `chrbnd.dcx` binders",
        default="N:\\FRPG\\data\\INTERROOT_x64\\chr\\{name}\\{name}.flver",
    )

    @classmethod
    def poll(cls, context):
        """At least one Blender mesh selected."""
        return len(context.selected_objects) == 1 and context.selected_objects[0].type in {"MESH", "ARMATURE"}

    def execute(self, context):
        try:
            mesh, armature = self.get_selected_flver(context)
        except FLVERExportError as ex:
            return self.error(str(ex))

        flver_stem = self.get_default_flver_stem(mesh, armature)

        dcx_type = GlobalSettings.resolve_dcx_type(self.dcx_type, "FLVER", True, context)

        self.to_object_mode()
        binder_file_path = Path(self.filepath)
        try:
            binder = Binder.from_path(binder_file_path)
        except Exception as ex:
            return self.error(f"Could not load Binder file '{binder_file_path}'. Error: {ex}.")

        exporter = FLVERExporter(self, context, self.get_export_settings(context))

        try:
            flver = exporter.export_flver(mesh, armature, name=flver_stem)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot create exported FLVER from Blender Mesh '{flver_stem}'. Error: {ex}")

        flver_entries = binder.find_entries_matching_name(r".*\.flver(\.dcx)?")
        if not flver_entries:
            if self.default_entry_id == -1:
                return self.error("No FLVER files found in Binder and default entry ID was left as -1.")
            try:
                flver_entry = binder.find_entry_id(self.default_entry_id)
            except EntryNotFoundError:
                # Create new entry.
                entry_path = self.default_entry_path.format(name=flver_stem)
                flver_entry = BinderEntry(
                    b"", entry_id=self.default_entry_id, path=entry_path, flags=self.default_entry_flags
                )
            else:
                if not self.overwrite_existing:
                    return self.error(
                        f"Binder entry {self.default_entry_id} already exists in Binder and overwrite is disabled."
                    )
        else:
            if not self.overwrite_existing:
                return self.error("FLVER file already exists in Binder and overwrite is disabled.")

            if len(flver_entries) > 1:
                self.warning(f"Multiple FLVER files found in Binder. Replacing first: {flver_entries[0].name}")
            flver_entry = flver_entries[0]

        flver.dcx_type = dcx_type

        try:
            flver_entry.set_from_binary_file(flver)  # DCX will default to `None` here from exporter function
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write exported FLVER. Error: {ex}")

        try:
            # Will create a `.bak` file automatically if absent.
            written_path = binder.write()
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write Binder with new FLVER. Error: {ex}")

        self.info(f"Exported FLVER into Binder file: {written_path}")

        return {"FINISHED"}


class QuickExportMapPieceFLVERs(LoggingOperator, ExportFLVERMixin):
    bl_idname = "export_scene.quick_map_piece_flver"
    bl_label = "Quick Export Map Piece FLVERs"
    bl_description = (
        "Export selected Blender armatures/meshes to map piece FLVER model files in appropriate game map(s)"
    )

    @classmethod
    def poll(cls, context):
        """One or more 'm*' Armatures or Meshes selected."""
        return (
            len(context.selected_objects) > 0
            and all(obj.type in {"MESH", "ARMATURE"} and obj.name[0] == "m" for obj in context.selected_objects)
        )

    def execute(self, context):
        try:
            meshes_armatures = self.get_selected_flvers(context)
        except FLVERExportError as ex:
            return self.error(str(ex))

        settings = GlobalSettings.get_scene_settings(context)
        game_directory = settings.game_directory
        if not game_directory:
            return self.error("Game directory must be set in Blender's Soulstruct global settings for quick export.")
        if not settings.detect_map_from_parent and not settings.map_stem:
            return self.error("Game map stem must be set in Blender's Soulstruct global settings for quick export.")

        dcx_type = settings.resolve_dcx_type(self.dcx_type, "FLVER", False, context)

        settings.save_settings()

        self.to_object_mode()

        exporter = FLVERExporter(self, context, self.get_export_settings(context))

        for mesh, armature in meshes_armatures:

            if settings.detect_map_from_parent:
                parent = armature.parent if armature else mesh.parent
                if parent is None:
                    return self.error(
                        f"Object '{mesh.name}' has no parent. Deselect 'Detect Map from Parent' to use single "
                        f"game map specified in Soulstruct plugin settings."
                    )
                map_stem = parent.name.split(" ")[0]
                if not MAP_STEM_RE.match(map_stem):
                    return self.error(f"Parent object '{parent.name}' does not start with a valid map stem.")
            else:
                map_stem = settings.map_stem

            if not (map_dir_path := Path(game_directory, "map", map_stem)).is_dir():
                return self.error(f"Invalid game map directory: {map_dir_path}")

            flver_stem = self.get_default_flver_stem(mesh, armature)

            try:
                flver = exporter.export_flver(mesh, armature, name=flver_stem)
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Cannot get exported FLVER '{flver_stem}'. Error: {ex}")

            flver.dcx_type = dcx_type
            try:
                # Will create a `.bak` file automatically if absent, and add `.dcx` extension if necessary.
                written_path = flver.write(map_dir_path / f"{flver_stem}.flver")
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Cannot write exported FLVER '{flver_stem}'. Error: {ex}")
            self.info(f"Exported FLVER to: {written_path}")

        return {"FINISHED"}


class QuickExportCharacterFLVER(LoggingOperator, ExportFLVERMixin):
    """Export a single FLVER model from a Blender mesh into a pre-selected CHRBND in the game directory."""
    bl_idname = "export_scene.quick_character_flver"
    bl_label = "Quick Export Character FLVER"
    bl_description = "Export a FLVER model file into appropriate game CHRBND"

    # NOTE: Always overwrites existing entry. DCX type and `BinderEntry` defaults are game-dependent.

    GAME_INFO = {
        GameNames.DS1R: {
            "chrbnd_flver_entry_id": 200,
            "chrbnd_flver_entry_path": "N:\\FRPG\\data\\INTERROOT_x64\\chr\\{character_name}\\{character_name}.flver",
        },
    }

    @classmethod
    def poll(cls, context):
        """Must select an Armature parent for a character FLVER. No chance of a default skeleton!

        Name of character must also start with 'c'.
        """
        game_lists = context.scene.game_files  # type: GameFiles
        if game_lists.chrbnd in {"", "0"}:
            return False
        return (
            len(context.selected_objects) == 1
            and context.selected_objects[0].type == "ARMATURE"
            and context.selected_objects[0].name.startswith("c")  # TODO: could require 'c####' template also
        )

    def execute(self, context):
        try:
            mesh, armature = self.get_selected_flver(context)
        except FLVERExportError as ex:
            return self.error(str(ex))
        if armature is None:
            return self.error("Must select an Armature parent to quick-export a character FLVER.")

        settings = GlobalSettings.get_scene_settings(context)
        game_lists = context.scene.game_files  # type: GameFiles

        chrbnd_path = game_lists.chrbnd
        if not chrbnd_path:
            return self.error("No CHRBND selected.")
        chrbnd_path = Path(chrbnd_path)
        if not chrbnd_path.is_file():
            return self.error(f"CHRBND path is not a file: {chrbnd_path}.")

        self.info(f"Exporting FLVER into CHRBND: {chrbnd_path}")

        chrbnd = Binder.from_path(chrbnd_path)
        character_name = chrbnd_path.name.split(".")[0]

        # We replace an existing FLVER entry if it exists, or use the game default ID otherwise.
        flver_entries = chrbnd.find_entries_matching_name(r".*\.flver(\.dcx)?")
        if not flver_entries:
            try:
                entry_id = self.GAME_INFO[settings.game]["chrbnd_flver_entry_id"]
            except KeyError:
                return self.error(f"No FLVER files found in CHRBND and don't know default ID for game {settings.game}.")

            try:
                flver_entry = chrbnd.find_entry_id(entry_id)
            except EntryNotFoundError:
                # Create new entry.
                try:
                    default_entry_path = self.GAME_INFO[settings.game]["chrbnd_flver_entry_path"].format(
                        character_name=character_name
                    )
                except KeyError:
                    return self.error(
                        f"Entry {entry_id} not found in CHRBND and don't know default path for game {settings.game}."
                    )

                flver_entry = BinderEntry(b"", entry_id=entry_id, path=default_entry_path, flags=0x2)
        else:
            if len(flver_entries) > 1:
                self.warning(f"Multiple FLVER files found in CHRBND. Replacing first: {flver_entries[0].name}")
            flver_entry = flver_entries[0]

        dcx_type = GlobalSettings.resolve_dcx_type(self.dcx_type, "FLVER", True, context)

        self.to_object_mode()
        exporter = FLVERExporter(self, context, self.get_export_settings(context))
        try:
            flver = exporter.export_flver(mesh, armature, name=character_name)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot create exported FLVER from Blender Mesh '{character_name}'. Error: {ex}")

        flver.dcx_type = dcx_type

        try:
            flver_entry.set_from_binary_file(flver)  # DCX will default to `None` here from exporter function
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write exported FLVER. Error: {ex}")

        try:
            # Will create a `.bak` file automatically if absent.
            written_path = chrbnd.write()
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write Binder with new FLVER. Error: {ex}")

        self.info(f"Exported FLVER into Binder file: {written_path}")

        return {"FINISHED"}


# TODO: Quick export object FLVER. Need to guess FLVER instance suffix from name, e.g. 'c0100_1.flver' entry.


@dataclass(slots=True)
class FLVERExportSettings:
    base_edit_bone_length: float = 0.2
    mtd_manager: MTDBinderManager | None = None
    allow_missing_textures: bool = False
    allow_unknown_texture_types: bool = False


@dataclass(slots=True)
class FLVERExporter:

    operator: LoggingOperator
    context: bpy.types.Context
    settings: FLVERExportSettings

    def get_flver_props(self, bl_flver: bpy.types.MeshObject, game: str) -> dict[str, tp.Any]:

        try:
            version_str = bl_flver["Version"]
        except KeyError:
            # Default is game-dependent.
            match game:
                case GameNames.PTDE:
                    version = Version.DarkSouls_A
                case GameNames.DS1R:
                    version = Version.DarkSouls_A
                case GameNames.BB:
                    version = Version.Bloodborne_DS3_A
                case GameNames.DS3:
                    version = Version.Bloodborne_DS3_A
                case _:
                    self.warning(f"Unknown game '{game}' for FLVER '{bl_flver.name}'. Assuming DS1.")
                    version = Version.DarkSouls_A
        else:
            version = Version[version_str]

        # TODO: Any other game-specific fields?
        return dict(
            big_endian=get_bl_prop(bl_flver, "Is Big Endian", bool, default=False),
            version=version,
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

    def export_flver(
        self, mesh: bpy.types.MeshObject, armature: bpy.types.ArmatureObject | None, name: str
    ) -> FLVER | None:
        """Create an entire FLVER from Blender Mesh and (optional) Armature objects.

        The Mesh and Armature can have any number of Empty children, which are exported as dummies provided they have
        the appropriate custom data (created upon Soulstruct import). Note that only dummies parented to the Armature
        can be attached to Armature bones (which most will, realistically).

        If `armature` is None, a default skeleton with a single bone at the model's origin will be created (which is why
        `name` must be passed in). This is fine for 99% of map pieces, for example.

        If the Mesh object is missing certain 'FLVER' custom properties (see `get_flver_props`), they will be exported
        with default values based on the current selected game, if able.

        TODO: Currently only really tested for DS1 FLVERs.
        """
        if mesh.type != "MESH":
            raise FLVERExportError("`mesh` object passed to FLVER exporter must be a Mesh.")
        if armature and armature.type != "ARMATURE":
            raise FLVERExportError("`armature` object passed to FLVER exporter must be an Armature or `None`.")

        scene_settings = GlobalSettings.get_scene_settings(self.context)

        flver = FLVER(**self.get_flver_props(mesh, scene_settings.game))

        # TODO: Default can surely be auto-set from game.
        layout_data_type_unk_x00 = get_bl_prop(mesh, "Layout Member Unk x00", int, default=0)

        bl_dummies = self.collect_dummies(mesh, armature)

        read_bone_type = self.detect_is_bind_pose(mesh)
        self.info(f"Exporting FLVER '{mesh.name}' with bone data from {read_bone_type.capitalize()}Bones.")
        if not armature:
            self.info(  # not a warning
                f"No Armature to export. Creating FLVER skeleton with a single origin bone named '{name}'."
            )
            default_bone = FLVERBone(name=name)  # default transform and other fields
            flver.bones = [default_bone]
            bl_bone_names = [default_bone.name]
            bl_bone_data = None
        else:
            flver.bones, bl_bone_names, bone_arma_transforms = self.create_bones(armature, read_bone_type)
            flver.set_bone_armature_space_transforms(bone_arma_transforms)
            bl_bone_data = armature.data.bones

        # Make `mesh` the active object again.
        self.context.view_layer.objects.active = mesh

        # noinspection PyUnresolvedReferences
        for bl_dummy, dummy_dict in bl_dummies:
            flver_dummy = self.export_dummy(bl_dummy, dummy_dict["reference_id"], bl_bone_names, bl_bone_data)
            flver.dummies.append(flver_dummy)

        # `MTDInfo` for each Blender material is needed to determine which BLender UV layers to read for which loops.
        mtd_infos = [
            self.get_mtd_info(bl_material, self.settings.mtd_manager)
            for bl_material in mesh.data.materials
        ]

        # TODO: Current choosing default vertex buffer layout (CHR vs. MAP PIECE) based on read bone type, which in
        #  turn depends on `mesh.is_bind_pose` at FLVER import. All a bit messily wired together...
        self.export_submeshes(
            flver,
            mesh,
            bl_bone_names,
            use_chr_layout=read_bone_type == "EDIT",
            strip_bl_material_prefix=name,
            layout_data_type_unk_x00=layout_data_type_unk_x00,
            mtd_infos=mtd_infos,
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
        self, mesh: bpy.types.MeshObject, armature: bpy.types.ArmatureObject | None
    ) -> list[tuple[bpy.types.Object, dict[str, tp.Any]]]:
        """Collect all Empty children of the Mesh and Armature objects, and return them as a list of tuples of the
        form `(bl_empty, dummy_dict)`, where `dummy_dict` is the result of `parse_dummy_name` on the empty's name.

        Dummies parented to the Mesh, rather than the Armature, will NOT be attached to any bones (though may still have
        custom `Parent Bone Name` data).

        Note that no dummies need exist in a FLVER (e.g. map pieces).
        """
        bl_dummies = []  # type: list[tuple[bpy.types.Object, dict[str, tp.Any]]]
        children = list(mesh.children)
        if armature:
            children.extend(armature.children)
        for child in children:
            if child.type == "EMPTY":
                if dummy_dict := self.parse_dummy_empty(child, mesh.name):
                    bl_dummies.append((child, dummy_dict))
            elif child is not mesh and child is not armature:
                self.warning(f"Non-Empty child object '{child.name}' of Mesh/Armature ignored.")

        # Sort dummies and meshes by 'human sorting' on Blender name (should match order in Blender hierarchy view).
        bl_dummies.sort(key=lambda o: natural_keys(o[0].name))
        return bl_dummies

    def parse_dummy_empty(self, bl_empty: bpy.types.Object, expected_prefix: str) -> dict[str, tp.Any] | None:
        """Check for required 'Unk x30' custom property to detect dummies."""
        if bl_empty.get("Unk x30") is None:
            self.warning(
                f"Empty child of FLVER '{bl_empty.name}' ignored. (Missing 'unk_x30' Dummy property and possibly "
                f"other required properties and proper Dummy name; see docs.)"
            )
            return None

        dummy_dict = parse_dummy_name(bl_empty.name)
        if not dummy_dict:
            self.warning(
                f"Could not interpret Dummy name: '{bl_empty.name}'. Ignoring it. Format should be: \n"
                f"    `[other_model] {{Name}} Dummy<index> [reference_id]` "
                f"    where `[other_model]` is an optional prefix used only for attached equipment FLVERs"
            )
        # TODO: exclude dummies with WRONG 'other_model' prefix, depending on whether c0000 or that equipment
        #  is being exported. Currently excluding all dummies with any 'other_model' defined.
        if dummy_dict.get("other_model", False):
            return  # do not export

        if dummy_dict["flver_name"] != expected_prefix:
            self.warning(
                f"Dummy '{bl_empty.name}' has unexpected FLVER name prefix '{dummy_dict['flver_name']}. Exporting it "
                f"anyway."
            )
        return dummy_dict

    def get_mtd_info(self, bl_material: bpy.types.Material, mtd_manager: MTDBinderManager = None) -> MTDInfo:
        """Get `MTDInfo` for a FLVER material, which is needed for both material creation and assignment of vertex UV
        data to the correct Blender UV data layer during mesh creation.
        """
        mtd_name = Path(bl_material["MTD Path"]).name
        if not mtd_manager:
            return MTDInfo.from_mtd_name(mtd_name)

        # Use real MTD file (much less guesswork).
        try:
            mtd = mtd_manager[mtd_name]
        except KeyError:
            self.warning(
                f"Could not find MTD '{mtd_name}' from Blender material '{bl_material.name}' in MTD dict. "
                f"Guessing info from name."
            )
            return MTDInfo.from_mtd_name(mtd_name)
        return MTDInfo.from_mtd(mtd)

    def export_submeshes(
        self,
        flver: FLVER,
        bl_mesh: bpy.types.MeshObject,
        bl_bone_names: list[str],
        use_chr_layout: bool,
        strip_bl_material_prefix: str,
        layout_data_type_unk_x00: int,
        mtd_infos: list[MTDInfo],
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
        layout_factory = VertexArrayLayoutFactory(layout_data_type_unk_x00)
        for mtd_info, bl_material in zip(mtd_infos, bl_mesh.data.materials):
            # Some Blender materials may be variants representing distinct Submesh/FaceSet properties; these will be
            # mapped to the same FLVER `Material`/`VertexArrayLayout` combo (created here).
            flver_material = self.export_material(bl_material, mtd_info, strip_bl_material_prefix)
            if use_chr_layout:
                array_layout = layout_factory.get_ds1_chr_array_layout(mtd_info)
            else:
                array_layout = layout_factory.get_ds1_map_array_layout(mtd_info)
            submesh_kwargs = {
                "is_bind_pose": get_bl_prop(bl_material, "Is Bind Pose", int, default=use_chr_layout, callback=bool),
                "default_bone_index": get_bl_prop(bl_material, "Default Bone Index", int, default=0),
                "use_backface_culling": bl_material.use_backface_culling,
                "uses_bounding_box": True,  # TODO: assumption (DS1 and likely all later games)
            }

            submesh_info.append((flver_material, array_layout, submesh_kwargs))
            flver.materials.append(flver_material)
            self.operator.info(f"Created FLVER material: {flver_material.name}")

        # 2. Extract UV layers. (Yes, we iterate over Blender materials again, but it's worth the clarity of purpose.)
        # Maps UV layer names to lists of `MeshUVLoop` instances (so they're converted only once across all materials).
        all_uv_layer_names_set = set()
        for mtd_info in mtd_infos:
            all_uv_layer_names_set |= set(mtd_info.get_uv_layer_names())
        uv_layers = sorted(all_uv_layer_names_set)  # e.g. ["UVMap1", "UVMap2", "UVMap3", "UVMapWindA", "UVMapWindB"]
        uv_layer_data = [
            list(bl_mesh.data.uv_layers[uv_layer_name].data)
            for uv_layer_name in uv_layers
        ]

        # 3. Prepare Mesh data.
        mesh_data = bl_mesh.data  # type: bpy.types.Mesh
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
            mesh_data.calc_tangents(uvmap="UVMap1")
            # bl_mesh_data.calc_normals_split()
        except RuntimeError:
            raise RuntimeError(
                "Could not calculate vertex tangents from 'UVMap1'. Make sure the mesh is triangulated and not "
                "empty (delete any empty mesh)."
            )

        # 4. Construct arrays from Blender data and pass into a new `MergedMesh`.

        # Slow part number 1: iterating over every Blender vertex to retrieve its position and bone weights/indices.
        # We at least know the size of the array in advance.
        vertex_count = len(mesh_data.vertices)
        vertex_data_dtype = [
            ("position", "f", 3),  # TODO: support 4D position
            ("bone_weights", "f", 4),
            ("bone_indices", "i", 4),
        ]
        vertex_data = np.empty(vertex_count, dtype=vertex_data_dtype)
        vertex_positions = np.empty((vertex_count, 3), dtype=np.float32)
        vertex_bone_weights = np.zeros((vertex_count, 4), dtype=np.float32)  # default: 0.0
        vertex_bone_indices = np.full((vertex_count, 4), -1, dtype=np.int32)  # default: -1

        vertex_groups = bl_mesh.vertex_groups  # for bone indices/weights
        no_bone_warning_done = False

        # TODO: Due to the unfortunate need to access Python attributes one by one, we need a `for` loop. Given the
        #  retrieval of vertex bones, though, it's unlikely a simple `position` array assignment would remove the need.
        p = time.perf_counter()
        for i, vertex in enumerate(mesh_data.vertices):
            vertex_positions[i] = vertex.co
            # for j, (bone_weight, bone_name) in enumerate(zip(vertex.groups, vertex_bone_weights[i])):

            bone_indices = []  # global (splitter will make them local to submesh if appropriate)
            bone_weights = []
            for vertex_group in vertex.groups:  # only one for map pieces; max of 4 for other FLVER types
                # Find mesh vertex group with this index.
                for mesh_group in vertex_groups:
                    if vertex_group.group == mesh_group.index:
                        try:
                            bone_index = bl_bone_names.index(mesh_group.name)
                        except ValueError:
                            raise FLVERExportError(
                                f"Vertex is weighted to invalid bone name: '{mesh_group.name}'."
                            )
                        bone_indices.append(bone_index)
                        # don't waste time calling `weight()` for map pieces
                        if use_chr_layout:
                            bone_weights.append(mesh_group.weight(i))
                        break

            if len(bone_indices) > 4:
                raise FLVERExportError(
                    f"Vertex cannot be weighted to more than 4 bones ({len(bone_indices)} is too many)."
                )
            elif len(bone_indices) == 0:
                if len(bl_bone_names) == 1 and not use_chr_layout:
                    # Omitted bone indices can be assumed to be the only bone in the skeleton.
                    if not no_bone_warning_done:
                        self.warning(
                            f"WARNING: At least one vertex in mesh '{bl_mesh.name}' is not weighted to any bones. "
                            f"Weighting in 'map piece' mode to only bone in skeleton: '{bl_bone_names[0]}'"
                        )
                        no_bone_warning_done = True
                    bone_indices = [0]  # padded out below
                    # Leave weights as zero.
                else:
                    # Can't guess which bone to weight to. Raise error.
                    raise FLVERExportError("Vertex is not weighted to any bones (cannot guess from multiple).")

            if use_chr_layout:
                # Pad out bone weights and (unused) indices for rigged meshes.
                while len(bone_weights) < 4:
                    bone_weights.append(0.0)
                while len(bone_indices) < 4:
                    bone_indices.append(-1)
            else:  # map pieces
                if len(bone_indices) == 1:
                    bone_indices *= 4  # duplicate single-element list to four-element list
                else:
                    raise FLVERExportError(f"Non-CHR FLVER vertices must be weighted to exactly one bone (vertex {i}).")

            vertex_bone_indices[i] = bone_indices
            if bone_weights:  # rigged only
                vertex_bone_weights[i] = bone_weights

        vertex_data["position"] = vertex_positions
        vertex_data["bone_weights"] = vertex_bone_weights
        vertex_data["bone_indices"] = vertex_bone_indices

        self.info(f"Constructed combined vertex array in {time.perf_counter() - p} s.")

        # TODO: Again, due to the unfortunate need to access Python attributes one by one, we need a `for` loop.
        p = time.perf_counter()
        faces = np.empty((len(mesh_data.polygons), 4), dtype=np.int32)
        for i, face in enumerate(mesh_data.polygons):
            try:
                faces[i] = [*face.loop_indices, face.material_index]
            except ValueError:
                raise FLVERExportError(
                    f"Cannot export FLVER mesh '{bl_mesh.name}' with any non-triangle faces. "
                    f"Face index {i} has {len(face.loop_indices)} sides)."
                )
        self.info(f"Constructed combined face array in {time.perf_counter() - p} s.")

        # Finally, we iterate over loops and construct their arrays.
        p = time.perf_counter()
        loop_count = len(mesh_data.loops)
        loop_vertex_indices = np.empty(loop_count, dtype=np.int32)
        loop_normals = np.empty((loop_count, 3), dtype=np.float32)
        loop_normals_w = np.full((loop_count, 1), 127, dtype=np.uint8)
        # TODO: could check combined `dtype` now to skip these if not needed by any materials.
        #  (Related: mark these arrays as optional attributes in `MergedMesh`.)
        loop_tangents = np.empty((loop_count, 3), dtype=np.float32)
        loop_bitangents = np.empty((loop_count, 3), dtype=np.float32)

        # UV arrays correspond to FLVER-wide sorted UV layer names.
        loop_uvs = [
            np.zeros((loop_count, 2), dtype=np.float32)  # default: 0.0 (each material may only use a subset of UVs)
            for _ in uv_layers
        ]

        try:
            loop_colors_layer = mesh_data.vertex_colors["VertexColors"]
        except KeyError:
            self.warning(f"FLVER mesh '{bl_mesh.name}' has no 'VertexColors' data layer. Using black.")
            loop_colors_layer = None
            # Default to black with alpha 1.
            black = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
            loop_vertex_color = np.tile(black, (loop_count, 1))
        else:
            # Prepare for loop filling.
            loop_vertex_color = np.empty((loop_count, 4), dtype=np.float32)
        
        for i, loop in enumerate(mesh_data.loops):
            loop_vertex_indices[i] = loop.vertex_index
            loop_normals[i] = loop.normal
            loop_tangents[i] = loop.tangent
            # TODO: Use a `MergedMesh` method to construct all bitangents at once with `np.cross`? Maybe not.
            loop_bitangents[i] = loop.bitangent

            if loop_colors_layer:
                loop_vertex_color[i] = loop_colors_layer.data[i].color

            # TODO: Technically it's a waste of time writing the data from UV layers that aren't even used by a certain
            #  submesh (and will hence be discarded during split submesh creation), but I'd need to go back and retrieve
            #  the material index of this loop's parent face to know which UV layer names to export. Not worth it.
            for uv_i, uv_data in enumerate(uv_layer_data):
                loop_uvs[uv_i][i] = uv_data[i].uv

        # Add `w` components to tangents and bitangents (-1).
        minus_one = np.full((loop_count, 1), -1, dtype=np.float32)
        loop_tangents = np.concatenate((loop_tangents, minus_one), axis=1)
        loop_bitangents = np.concatenate((loop_bitangents, minus_one), axis=1)

        self.info(f"Constructed combined loop array in {time.perf_counter() - p} s.")

        merged_mesh = MergedMesh(
            vertex_data=vertex_data,
            loop_vertex_indices=loop_vertex_indices,
            loop_normals=loop_normals,
            loop_normals_w=loop_normals_w,
            loop_tangents=loop_tangents,
            loop_bitangents=loop_bitangents,
            loop_vertex_colors=[loop_vertex_color],
            loop_uvs=loop_uvs,
            faces=faces,
        )
        
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

        return flver

    def create_bones(
        self, armature_obj, read_bone_type: str
    ) -> tuple[list[FLVERBone], list[str], list[tuple[Vector3, Matrix3, Vector3]]]:
        """Create `FLVER` bones from Blender armature bones and get their armature space transforms.

        Bone transform data may be read from either EDIT mode (typical for characters and objects) or POSE mode (typical
        for map pieces). This is specified by `read_bone_type`.
        """

        # We need `EditBone` mode to retrieve custom properties, even if reading the actual transforms from pose later.
        self.context.view_layer.objects.active = armature_obj
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="EDIT", toggle=False)

        game_bones = []
        game_arma_transforms = []  # type: list[tuple[Vector3, Matrix3, Vector3]]  # translate, rotate matrix, scale
        edit_bone_names = [edit_bone.name for edit_bone in armature_obj.data.edit_bones]
        if len(set(edit_bone_names)) != len(edit_bone_names):
            raise FLVERExportError("Bone names of armature are not all unique.")

        for edit_bone in armature_obj.data.edit_bones:
            game_bone_name = edit_bone.name
            while game_bone_name.endswith(" <DUPE>"):
                game_bone_name = game_bone_name.removesuffix(" <DUPE>")

            game_bone = FLVERBone(
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
            for game_bone, pose_bone in zip(game_bones, armature_obj.pose.bones):

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
        mtd_info: MTDInfo,
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

        flver_material = Material(
            name=name,
            flags=get_bl_prop(bl_material, "Flags", int),
            gx_index=get_bl_prop(bl_material, "GX Index", int, default=-1),  # TODO: not yet supported
            mtd_path=get_bl_prop(bl_material, "MTD Path", str),
            unk_x18=get_bl_prop(bl_material, "Unk x18", int, default=0),
        )

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

        return flver_material
