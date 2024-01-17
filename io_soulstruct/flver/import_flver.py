"""
Import FLVER files (with/without DCX) into Blender 3.3+ (Python 3.10+ scripting required).

Can find FLVERs in CHRBND, OBJBND, and PARTSBND binders (with or without DCX compression).

The FLVER is imported as an Armature object with all FLVER sub-meshes as Mesh children and model 'dummy points' as Empty
children.

New Blender materials will be created as needed that approximate in-game look (including conversion and loading of
located DDS textures), but existing materials with the same name as the FLVER materials will be used if the user selects
this option (on by default).

Critical FLVER information needed for export, but not represented anywhere else in Blender, is stored with custom
properties as necessary (on FLVER armatures, meshes, dummies, and materials).

NOTE: Currently only thoroughly tested for DS1/DSR.
"""
from __future__ import annotations

__all__ = [
    "ImportFLVER",
    "ImportMapPieceFLVER",
    "ImportCharacterFLVER",
    "ImportObjectFLVER",
    "ImportEquipmentFLVER",
    "FLVERImportSettings",
    "ImportMapPieceMSBPart",
    "ImportAllMapPieceMSBParts",
    "FLVERBatchImporter",
]

import fnmatch
import math
import numpy as np
import re
import time
import traceback
import typing as tp
from dataclasses import dataclass, field
from pathlib import Path

import bmesh
import bpy
import bpy.ops
from mathutils import Vector, Matrix

from soulstruct.base.models.flver import FLVER, FLVERBone, FLVERBoneUsageFlags, Dummy
from soulstruct.base.models.flver.mesh_tools import MergedMesh
from soulstruct.containers import Binder
from soulstruct.containers.tpf import TPFTexture, batch_get_tpf_texture_png_data
from soulstruct.games import *
from soulstruct.utilities.maths import Vector3

from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.utilities import *
from .materials import *
from .textures.import_textures import TextureImportManager, import_png_as_image
from .utilities import *

if tp.TYPE_CHECKING:
    from soulstruct.base.models.mtd import MTDBND as BaseMTDBND
    from soulstruct.eldenring.models.matbin import MATBINBND

    from io_soulstruct.general import SoulstructSettings, SoulstructGameEnums
    from io_soulstruct.type_checking import MSB_TYPING


FLVER_BINDER_RE = re.compile(r"^.*?\.(.*bnd)(\.dcx)?$")
MAP_NAME_RE = re.compile(r"^(m\d\d)_\d\d_\d\d_\d\d$")


class FLVERImportSettings(bpy.types.PropertyGroup):
    """Common FLVER import settings. Drawn manually in operator browser windows."""

    import_textures: bpy.props.BoolProperty(
        name="Import Textures",
        description="Import DDS textures from TPFs in expected locations for detected FLVER model source type",
        default=True,
    )

    material_blend_mode: bpy.props.EnumProperty(
        name="Alpha Blend Mode",
        description="Alpha mode to use for new single-texture FLVER materials",
        items=[
            ("OPAQUE", "Opaque", "Opaque Blend Mode"),
            ("CLIP", "Clip", "Clip Blend Mode"),
            ("HASHED", "Hashed", "Hashed Blend Mode"),
            ("BLEND", "Blend", "Sorted Blend Mode"),
        ],
        default="HASHED",
    )

    base_edit_bone_length: bpy.props.FloatProperty(
        name="Base Edit Bone Length",
        description="Length of edit bones corresponding to bone scale 1",
        default=0.2,
        min=0.01,
    )

    msb_part_name_match: bpy.props.StringProperty(
        name="MSB Part Name Match",
        description="Glob/Regex for filtering MSB part names when importing all parts",
        default="*",
    )

    msb_part_name_match_mode: bpy.props.EnumProperty(
        name="MSB Part Name Match Mode",
        description="Whether to use glob or regex for MSB part name matching",
        items=[
            ("GLOB", "Glob", "Use glob for MSB part name matching"),
            ("REGEX", "Regex", "Use regex for MSB part name matching"),
        ],
        default="GLOB",
    )


class BaseFLVERImportOperator(LoggingImportOperator):

    def draw(self, context):
        import_settings = context.scene.flver_import_settings  # type: FLVERImportSettings

        self.layout.prop(import_settings, "import_textures")
        self.layout.prop(import_settings, "material_blend_mode")
        self.layout.prop(import_settings, "base_edit_bone_length")

    def execute(self, context: bpy.types.Context):
        """Default import method for FLVERs."""

        start_time = time.perf_counter()

        flvers = []  # holds `(bl_name, FLVER)` pairs
        texture_manager = TextureImportManager(self.settings(context))

        import_settings = context.scene.flver_import_settings  # type: FLVERImportSettings

        for source_path in self.file_paths:

            if FLVER_BINDER_RE.match(source_path.name):
                # NOTE: Will always import all FLVERs found in Binder.
                binder = Binder.from_path(source_path)
                binder_flvers = get_flvers_from_binder(binder, source_path, allow_multiple=True)
                if import_settings.import_textures:
                    texture_manager.find_flver_textures(source_path, binder)
                    for flver in binder_flvers:
                        self.find_extra_textures(source_path, flver, texture_manager)
                for flver in binder_flvers:
                    flvers.append((flver.path.name.split(".")[0], flver))
            else:  # e.g. loose Map Piece FLVER
                flver = FLVER.from_path(source_path)
                if import_settings.import_textures:
                    texture_manager.find_flver_textures(source_path)
                    self.find_extra_textures(source_path, flver, texture_manager)
                flvers.append((source_path.name.split(".")[0], flver))

        settings = self.settings(context)
        settings.save_settings()
        importer = FLVERBatchImporter(
            self,
            context,
            settings,
            texture_import_manager=texture_manager,
        )

        bl_mesh = None
        for bl_name, flver in flvers:

            try:
                bl_armature, bl_mesh = importer.import_flver(flver, name=bl_name)
            except Exception as ex:
                # Delete any objects created prior to exception.
                importer.abort_import()
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import FLVER: {bl_name}. Error: {ex}")

        self.info(f"Imported {len(flvers)} FLVER(s) in {time.perf_counter() - start_time:.3f} seconds.")

        # Select and frame view on (final) newly imported Mesh.
        if bl_mesh:
            self.set_active_obj(bl_mesh)
            bpy.ops.view3d.view_selected(use_all_regions=False)

        return {"FINISHED"}

    def find_extra_textures(self, flver_source_path: Path, flver: FLVER, texture_manager: TextureImportManager):
        """Can be overridden by importers for specific FLVER model types that know where their textures are."""
        pass

    def set_blender_parent(self, context, bl_flver_armature: bpy.types.ArmatureObject):
        """Set parent of imported FLVER armature, if needed."""
        pass


class ImportFLVER(BaseFLVERImportOperator):
    """This appears in the tooltip of the operator and in the generated docs."""
    bl_idname = "import_scene.flver"
    bl_label = "Import FLVER"
    bl_description = "Import a FromSoftware FLVER model file. Can import from BNDs and supports DCX-compressed files."

    filename_ext = ".flver"

    filter_glob: bpy.props.StringProperty(
        default="*.flver;*.flver.dcx;*.chrbnd;*.chrbnd.dcx;*.objbnd;*.objbnd.dcx;"
                "*.partsbnd;*.partsbnd.dcx;*.mapbnd;*.mapbnd.dcx;*.geombnd;*.geombnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'})

    def invoke(self, context, _event):
        """Set the initial directory based on Global Settings."""
        game_directory = self.settings(context).game_directory
        if game_directory and game_directory.is_dir():
            self.directory = str(game_directory)
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        return super().invoke(context, _event)


# region Game Folder Importers

class ImportMapPieceFLVER(BaseFLVERImportOperator):
    """Import a map piece FLVER from selected game map directory."""
    bl_idname = "import_scene.map_piece_flver"
    bl_label = "Import Map Piece"
    bl_description = "Import a Map Piece FLVER from selected game map directory"

    filename_ext = ".flver"

    filter_glob: bpy.props.StringProperty(
        default="*.flver;*.flver.dcx;*.mapbnd;*.mapbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return bool(cls.settings(context).get_import_map_path())

    def invoke(self, context, _event):
        """Set the initial directory based on Global Settings."""
        settings = self.settings(context)
        # Map Piece FLVERs come from the oldest version of the map.
        map_path = settings.get_import_map_path(map_stem=settings.get_oldest_map_stem_version())
        if map_path and Path(map_path).is_dir():
            self.directory = str(map_path)
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        return super().invoke(context, _event)

    def find_extra_textures(self, flver_source_path: Path, flver: FLVER, texture_manager: TextureImportManager):
        """Check all textures in FLVER for specific map 'mAA_' prefix textures and register TPFBHDs in those maps."""
        area_re = re.compile(r"^m\d\d_")
        texture_map_areas = {
            texture_path.stem[:3]
            for texture_path in flver.get_all_texture_paths()
            if re.match(area_re, texture_path.stem)
        }
        for map_area in texture_map_areas:
            map_area_dir = (flver_source_path.parent / f"../{map_area}").resolve()
            texture_manager.find_specific_map_textures(map_area_dir)

    def set_blender_parent(self, context, bl_flver_armature: bpy.types.ArmatureObject):
        """Find or create Map Piece parent."""
        map_stem = self.settings(context).map_stem
        map_piece_parent = find_or_create_bl_empty(f"{map_stem} Map Pieces", context)
        bl_flver_armature.parent = map_piece_parent


class ImportCharacterFLVER(BaseFLVERImportOperator):
    """Shortcut for browsing for CHRBND Binders in game 'chr' directory."""
    bl_idname = "import_scene.character_flver"
    bl_label = "Import Character"
    bl_description = "Import character FLVER from a CHRBND in selected game 'chr' directory"

    filename_ext = ".chrbnd"

    filter_glob: bpy.props.StringProperty(
        default="*.chrbnd;*.chrbnd.dcx;*.chrbnd.bak;*.chrbnd.dcx.bak;",
        options={'HIDDEN'},
        maxlen=255,
    )

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return bool(cls.settings(context).get_import_dir_path("chr"))

    def invoke(self, context, _event):
        chr_dir = self.settings(context).get_import_dir_path("chr")
        if chr_dir and chr_dir.is_dir():
            self.directory = str(chr_dir)
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        return super().invoke(context, _event)

    # Base `execute` method is fine.


class ImportObjectFLVER(BaseFLVERImportOperator):
    """Shortcut for browsing for OBJBND Binders in game 'obj' directory."""
    bl_idname = "import_scene.object_flver"
    bl_label = "Import Object"
    bl_description = "Import object FLVER from an OBJBND in selected game 'obj' directory"

    filename_ext = ".objbnd"

    filter_glob: bpy.props.StringProperty(
        default="*.objbnd;*.objbnd.dcx;",
        options={'HIDDEN'},
        maxlen=255,
    )

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return bool(cls.settings(context).get_import_dir_path("obj"))

    def invoke(self, context, _event):
        obj_dir = self.settings(context).get_import_dir_path("obj")
        if obj_dir and obj_dir.is_dir():
            self.directory = str(obj_dir)
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        return super().invoke(context, _event)

    # Base `execute` method is fine.


class ImportEquipmentFLVER(BaseFLVERImportOperator):
    """Import weapon/armor FLVER from a `partsbnd` binder and attach it to selected armature (c0000)."""
    bl_idname = "import_scene.equipment_flver"
    bl_label = "Import Equipment"
    bl_description = "Import equipment FLVER from a PARTSBND in selected game 'parts' directory"

    filename_ext = ".partsbnd"

    filter_glob: bpy.props.StringProperty(
        default="*.partsbnd;*.partsbnd.dcx;",
        options={'HIDDEN'},
        maxlen=255,
    )

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'}, )
    directory: bpy.props.StringProperty(options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return bool(cls.settings(context).get_import_dir_path("parts"))

    def invoke(self, context, _event):
        parts_dir = self.settings(context).get_import_dir_path("parts")
        if parts_dir and parts_dir.is_dir():
            self.directory = str(parts_dir)
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        return super().invoke(context, _event)

    # Base `execute` method is fine.

# endregion


# region MSB Mode Importers

class ImportMapPieceMSBPart(LoggingOperator):
    """Import the model of an enum-selected MSB Map Piece part, and its MSB transform."""
    bl_idname = "import_scene.msb_map_piece_flver"
    bl_label = "Import Map Piece Part"
    bl_description = "Import FLVER model and MSB transform of selected Map Piece MSB part"

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)
        msb_path = settings.get_import_msb_path()
        if not is_path_and_file(msb_path):
            return False
        game_enums = context.scene.soulstruct_game_enums  # type: SoulstructGameEnums
        if game_enums.map_piece_parts in {"", "0"}:
            return False
        return True  # MSB exists and a Map Piece part name is selected from enum

    def execute(self, context):

        start_time = time.perf_counter()

        settings = self.settings(context)
        settings.save_settings()

        flver_import_settings = context.scene.flver_import_settings  # type: FLVERImportSettings

        try:
            part_name, flver_stem = context.scene.soulstruct_game_enums.map_piece_parts.split("|")
        except ValueError:
            return self.error("Invalid MSB map piece selection.")
        msb_path = settings.get_import_msb_path()  # will automatically use latest MSB version if known and enabled

        # Get MSB part transform.
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING
        map_piece_part = msb.map_pieces.find_entry_name(part_name)
        transform = Transform.from_msb_part(map_piece_part)
        flver_path = settings.get_import_map_path(f"{flver_stem}.flver")
        bl_name = part_name

        self.info(f"Importing map piece FLVER: {flver_path}")

        flver = FLVER.from_path(flver_path)

        if flver_import_settings.import_textures:
            texture_manager = TextureImportManager(settings)
            texture_manager.find_flver_textures(flver_path)
            area_re = re.compile(r"^m\d\d_")
            texture_map_areas = {
                texture_path.stem[:3]
                for texture_path in flver.get_all_texture_paths()
                if re.match(area_re, texture_path.stem)
            }
            for map_area in texture_map_areas:
                map_area_dir = (flver_path.parent / f"../{map_area}").resolve()
                texture_manager.find_specific_map_textures(map_area_dir)
        else:
            texture_manager = None

        importer = FLVERBatchImporter(
            self,
            context,
            settings,
            texture_import_manager=texture_manager,
        )

        try:
            bl_armature, bl_mesh = importer.import_flver(flver, name=bl_name)
        except Exception as ex:
            # Delete any objects created prior to exception.
            importer.abort_import()
            traceback.print_exc()  # for inspection in Blender console
            return self.error(f"Cannot import FLVER: {flver_path.name}. Error: {ex}")

        # Set 'Model File Stem' to ensure the model file stem is recorded, since the object name is the part name.
        bl_mesh["Model File Stem"] = flver_stem

        # Find or create Map Piece parent.
        map_piece_parent = find_or_create_bl_empty(f"{settings.map_stem} Map Pieces", context)
        bl_armature.parent = map_piece_parent

        # Set transform.
        bl_armature.location = transform.bl_translate
        bl_armature.rotation_euler = transform.bl_rotate
        bl_armature.scale = transform.bl_scale

        # Select and frame view on (final) newly imported Mesh.
        if bl_mesh:
            self.set_active_obj(bl_mesh)
            bpy.ops.view3d.view_selected(use_all_regions=False)

        self.info(f"Imported map piece FLVER in {time.perf_counter() - start_time:.3f} seconds.")

        return {"FINISHED"}


class ImportAllMapPieceMSBParts(LoggingOperator):
    """Import ALL MSB map piece parts and their transforms. Will take a long time!"""
    bl_idname = "import_scene.all_msb_map_piece_flver"
    bl_label = "Import All Map Piece Parts (SLOW)"
    bl_description = "Import FLVER model and MSB transform of every Map Piece MSB part (SLOW)"

    link_model_data: bpy.props.BoolProperty(
        name="Link Model Data",
        description="Use instances of Armature and Mesh data for repeated models instead of duplicating objects",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)
        msb_path = settings.get_import_msb_path()
        if not is_path_and_file(msb_path):
            return False
        return True  # MSB exists

    def execute(self, context):

        start_time = time.perf_counter()

        settings = self.settings(context)
        settings.save_settings()

        flver_import_settings = context.scene.flver_import_settings  # type: FLVERImportSettings
        if flver_import_settings.import_textures:
            texture_manager = TextureImportManager(settings)
        else:
            texture_manager = None

        part_name_match = flver_import_settings.msb_part_name_match
        match flver_import_settings.msb_part_name_match_mode:
            case "GLOB":
                def is_name_match(name: str):
                    return part_name_match in {"", "*"} or fnmatch.fnmatch(name, part_name_match)
            case "REGEX":
                pattern = re.compile(part_name_match)
                def is_name_match(name: str):
                    return part_name_match == "" or re.match(pattern, name)
            case _:  # should never happen
                return self.error(f"Invalid MSB part name match mode: {flver_import_settings.msb_part_name_match_mode}")

        msb_path = settings.get_import_msb_path()  # will automatically use latest MSB version if known and enabled
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING

        # Maps FLVER model stems to Armature and Mesh already created.
        loaded_models = {}  # type: dict[str, tuple[bpy.types.ArmatureObject, bpy.types.MeshObject]]

        importer = FLVERBatchImporter(
            self,
            context,
            settings,
            texture_import_manager=texture_manager,
        )

        part_count = 0

        bl_mesh = None  # for getting final mesh to select

        for map_piece_part in msb.map_pieces:

            if not is_name_match(map_piece_part.name):
                # MSB map piece name (part, not model) does not match glob/regex.
                continue

            model_stem = map_piece_part.model.get_model_file_stem(settings.map_stem)
            transform = Transform.from_msb_part(map_piece_part)

            if self.link_model_data and model_stem in loaded_models:
                # Use existing Armature and Mesh data.
                existing_armature, existing_mesh = loaded_models[model_stem]
                bl_armature = bpy.data.objects.new(map_piece_part.name, existing_armature.data)
                bl_mesh = bpy.data.objects.new(map_piece_part.name, existing_mesh.data)
                context.scene.collection.objects.link(bl_armature)
                context.scene.collection.objects.link(bl_mesh)

                # Parent mesh to armature. This is critical for proper animation behavior (especially with root motion).
                bl_mesh.parent = bl_armature
                # noinspection PyTypeChecker
                importer.create_mesh_armature_modifier(bl_mesh, bl_armature)

                # Copy FLVER properties to new mesh (as a new FLVER is exportable from any duplicate).
                self.copy_bl_mesh_props(existing_mesh, bl_mesh)

                self.info(
                    f"Created duplicate armature/mesh for MSB part '{map_piece_part.name}' in Blender linked to model "
                    f"data of part '{existing_armature.name}'."
                )

            else:
                # Import new FLVER.
                flver_path = settings.get_import_map_path(f"{model_stem}.flver")

                self.info(f"Importing map piece FLVER: {flver_path}")

                flver = FLVER.from_path(flver_path)
                if texture_manager:
                    texture_manager.find_flver_textures(flver_path)
                    area_re = re.compile(r"^m\d\d_")
                    texture_map_areas = {
                        texture_path.stem[:3]
                        for texture_path in flver.get_all_texture_paths()
                        if re.match(area_re, texture_path.stem)
                    }
                    for map_area in texture_map_areas:
                        map_area_dir = (flver_path.parent / f"../{map_area}").resolve()
                        texture_manager.find_specific_map_textures(map_area_dir)

                try:
                    bl_armature, bl_mesh = importer.import_flver(flver, name=map_piece_part.name)
                except Exception as ex:
                    # Delete any objects created prior to exception.
                    importer.abort_import()
                    traceback.print_exc()  # for inspection in Blender console
                    self.error(f"Cannot import FLVER: {flver_path.name}. Error: {ex}")
                    continue

            # Set 'Model File Stem' to ensure the model file stem is recorded, since the object name is the part name.
            bl_mesh["Model File Stem"] = model_stem

            # Find or create Map Piece parent.
            map_piece_parent = find_or_create_bl_empty(f"{settings.map_stem} Map Pieces", context)
            bl_armature.parent = map_piece_parent

            # Set transform.
            if transform is not None:
                bl_armature.location = transform.bl_translate
                bl_armature.rotation_euler = transform.bl_rotate
                bl_armature.scale = transform.bl_scale

            # Record model for future Part instances.
            loaded_models[model_stem] = (bl_armature, bl_mesh)
            part_count += 1

        self.info(
            f"Imported {len(loaded_models)} map piece FLVER models and {part_count} / {len(msb.map_pieces)} Parts in "
            f"{time.perf_counter() - start_time:.3f} seconds."
        )

        # Select and frame view on (final) newly imported Mesh.
        if bl_mesh:
            self.set_active_obj(bl_mesh)
            bpy.ops.view3d.view_selected(use_all_regions=False)

        return {"FINISHED"}

    @staticmethod
    def copy_bl_mesh_props(source_mesh: bpy.types.Object, target_mesh: bpy.types.Object):
        """Copy custom properties from source to target mesh."""
        for prop_name in source_mesh.keys():
            target_mesh[prop_name] = source_mesh[prop_name]

# endregion


@dataclass(slots=True)
class FLVERBatchImporter:
    """Manages imports for a batch of FLVER files using the same settings.

    Call `import_flver()` to import a single FLVER file.
    """

    operator: LoggingOperator
    context: bpy.types.Context
    settings: SoulstructSettings
    texture_import_manager: TextureImportManager | None = None

    # Loaded from `settings` if not given.
    mtdbnd: BaseMTDBND | None = None
    matbinbnd: MATBINBND | None = None

    # Per-FLVER settings.
    flver: FLVER | None = None  # current FLVER being imported
    name: str = ""  # name of root Blender mesh object that will be created
    bl_bone_names: list[str] = field(default_factory=list)  # list of Blender bone names in order of FLVER bones
    new_objs: list[bpy.types.Object] = field(default_factory=list)  # all new objects created during import
    new_images: list[bpy.types.Image] = field(default_factory=list)  # all new images created during import
    new_materials: list[bpy.types.Material] = field(default_factory=list)  # all new materials created during import

    def __post_init__(self):
        if self.mtdbnd is None:
            self.mtdbnd = self.settings.get_mtdbnd(self.operator)
        if self.matbinbnd is None:
            self.matbinbnd = self.settings.get_matbinbnd(self.operator)

    def abort_import(self):
        """Delete all Blender objects, images, and materials created during this import."""
        for obj in self.new_objs:
            try:
                bpy.data.objects.remove(obj)
            except ReferenceError:
                pass
        for img in self.new_images:
            try:
                bpy.data.images.remove(img)
            except ReferenceError:
                pass
        for mat in self.new_materials:
            try:
                bpy.data.materials.remove(mat)
            except ReferenceError:
                pass
        self.flver = None
        self.name = ""
        self.bl_bone_names.clear()
        self.new_objs.clear()
        self.new_images.clear()
        self.new_materials.clear()

    def import_flver(
        self,
        flver: FLVER,
        name: str,
    ) -> tuple[bpy.types.ArmatureObject, bpy.types.MeshObject]:
        """Read a FLVER into a Blender mesh and Armature.

        If `existing_armature` is passed, the skeleton of `flver` will not be imported as a new Armature, and the FLVER
        mesh will be rigged to the bones of `existing_armature` instead (e.g. for parenting equipment models to c0000).
        Dummies should generally not be present in these FLVERs, but if they do exist, they will also be parented to the
        armature with their original FLVER name as a prefix to distinguish them from the dummies of `existing_armature`.
        In this mode, if `flver` vertices are weighted to any bones not in `existing_armature`, they will be ignored and
        a warning will be logged.
        """
        # start_time = time.perf_counter()

        self.flver = flver
        self.name = name
        self.bl_bone_names.clear()
        self.new_objs.clear()
        self.new_images.clear()
        self.new_materials.clear()

        # Create FLVER bone index -> Blender bone name dictionary. (Blender names are UTF-8.)
        # This is done even when `existing_armature` is given, as the order of bones in this new FLVER may be different
        # and the vertex weight indices need to be directed to the names of bones in `existing_armature` correctly.
        for bone in flver.bones:
            # Just using actual bone names to avoid the need for parsing rules on export. However, duplicate names
            # need to be handled with suffixes.
            bl_bone_name = f"{bone.name} <DUPE>" if bone.name in self.bl_bone_names else bone.name
            self.bl_bone_names.append(bl_bone_name)

        import_settings = self.context.scene.flver_import_settings  # type: FLVERImportSettings

        bl_armature_obj = self.create_armature(import_settings.base_edit_bone_length)
        dummy_prefix = ""
        self.new_objs.append(bl_armature_obj)

        submesh_bl_material_indices, bl_material_uv_layer_names = self.create_materials(
            flver, import_settings.material_blend_mode
        )

        bl_flver_mesh = self.create_flver_mesh(
            flver, self.name, submesh_bl_material_indices, bl_material_uv_layer_names
        )

        # Assign basic FLVER header information as custom props.
        # TODO: Configure a full-exporter dropdown/choice of game version that defaults as many of these as possible.
        #  - `Version` and `Unicode` can be detected from selected game, and possibly the other unknowns
        #  - `Is Big Endian` can be a global settings bool
        bl_flver_mesh["Is Big Endian"] = flver.big_endian  # bool
        bl_flver_mesh["Version"] = flver.version.name  # str
        bl_flver_mesh["Unicode"] = flver.unicode  # bool
        bl_flver_mesh["Unk x4a"] = flver.unk_x4a  # bool
        bl_flver_mesh["Unk x4c"] = flver.unk_x4c  # int
        bl_flver_mesh["Unk x5c"] = flver.unk_x5c  # int
        bl_flver_mesh["Unk x5d"] = flver.unk_x5d  # int
        bl_flver_mesh["Unk x68"] = flver.unk_x68  # int

        # Parent mesh to armature. This is critical for proper animation behavior (especially with root motion).
        bl_flver_mesh.parent = bl_armature_obj
        self.create_mesh_armature_modifier(bl_flver_mesh, bl_armature_obj)

        for i, dummy in enumerate(flver.dummies):
            self.create_dummy(dummy, index=i, bl_armature=bl_armature_obj, dummy_prefix=dummy_prefix)

        # self.operator.info(f"Created FLVER Blender mesh '{name}' in {time.perf_counter() - start_time:.3f} seconds.")

        return bl_armature_obj, bl_flver_mesh  # might be used by other importers

    def create_mesh_armature_modifier(self, bl_mesh: bpy.types.MeshObject, bl_armature: bpy.types.ArmatureObject):
        self.operator.set_active_obj(bl_mesh)
        bpy.ops.object.modifier_add(type="ARMATURE")
        armature_mod = bl_mesh.modifiers["Armature"]
        armature_mod.object = bl_armature
        armature_mod.show_in_editmode = True
        armature_mod.show_on_cage = True

    def create_materials(
        self,
        flver: FLVER,
        material_blend_mode: str,
    ) -> tuple[list[int], list[list[str]]]:
        """Create Blender materials needed for `flver`.

        Returns a list of Blender material indices for each submesh, and a list of UV layer names for each Blender
        material (NOT each submesh).
        """
        if self.texture_import_manager or self.settings.png_cache_directory:
            p = time.perf_counter()
            self.new_images = self.load_texture_images(self.texture_import_manager)
            if self.new_images:
                self.operator.info(f"Loaded {len(self.new_images)} textures in {time.perf_counter() - p:.3f} seconds.")
        else:
            self.operator.info("No imported textures or PNG cache folder given. No textures loaded for FLVER.")

        # Maps FLVER submeshes to their Blender material index to store per-face in the merged mesh.
        # Submeshes that originally indexed the same FLVER material may have different Blender 'variant' materials that
        # hold certain Submesh/FaceSet properties like `use_backface_culling`.
        # Conversely, Submeshes that only serve to handle per-submesh bone maximums (e.g. 38 in DS1) will use the same
        # Blender material and be split again automatically on export (but likely not in an indentical way!).
        submesh_bl_material_indices = []
        # UV layer name lists for each Blender material index.
        bl_material_uv_layer_names = []  # type: list[list[str]]

        # Map FLVER material hashes to the indices of variant Blender materials sourced from them, which hold distinct
        # Submesh/FaceSet properties.
        flver_material_hash_variants = {}

        # Map FLVER material hashes to their MTD info and UV layer names.
        flver_material_infos = {}  # type: dict[int, BaseMaterialShaderInfo]
        flver_material_uv_layer_names = {}  # type: dict[int, list[str]]
        for submesh in flver.submeshes:
            material_hash = hash(submesh.material)  # TODO: should hash ignore material name?
            if material_hash in flver_material_infos:
                continue  # material already created (used by a previous submesh)

            if self.settings.is_game(DARK_SOULS_PTDE, DARK_SOULS_DSR):
                material_info = DS1MaterialShaderInfo.from_mtdbnd_or_name(
                    self.operator, submesh.material.mtd_name, self.mtdbnd
                )
            elif self.settings.is_game(BLOODBORNE):
                material_info = BBMaterialShaderInfo.from_mtdbnd_or_name(
                    self.operator, submesh.material.mtd_name, self.mtdbnd
                )
            else:
                raise FLVERImportError(f"FLVER import not implemented for game {self.settings.game.name}.")
            flver_material_infos[material_hash] = material_info
            flver_material_uv_layer_names[material_hash] = material_info.get_uv_layer_names()

        self.new_materials = []
        for submesh in flver.submeshes:
            material = submesh.material
            material_hash = hash(material)  # NOTE: if there are duplicate FLVER materials, this will combine them

            if material_hash not in flver_material_hash_variants:
                # First time this FLVER material has been encountered. Create it in Blender now.
                # NOTE: Vanilla material names are unused and essentially worthless. They can also be the same for
                #  materials that actually use different lightmaps, EVEN INSIDE the same FLVER model. Names are changed
                #  here to just reflect the index. The original name is NOT kept to avoid stacking up formatting on
                #  export/import and because it is so useless anyway.
                flver_material_index = len(flver_material_hash_variants)
                bl_material_index = len(self.new_materials)
                bl_material = get_submesh_blender_material(
                    self.operator,
                    material,
                    material_name=f"{self.name} Material {flver_material_index}",  # no Variant suffix
                    material_info=flver_material_infos[material_hash],
                    submesh=submesh,
                    blend_mode=material_blend_mode,
                    warn_missing_textures=self.texture_import_manager is not None,
                )  # type: bpy.types.Material

                submesh_bl_material_indices.append(bl_material_index)
                flver_material_hash_variants[material_hash] = [bl_material_index]

                self.new_materials.append(bl_material)
                bl_material_uv_layer_names.append(flver_material_uv_layer_names[material_hash])

                continue

            existing_variant_bl_indices = flver_material_hash_variants[material_hash]

            # Check if Blender material needs to be duplicated as a variant with different Mesh properties.
            found_existing_material = False
            for existing_bl_material_index in existing_variant_bl_indices:
                # NOTE: We do not care about enforcing any maximum submesh local bone count in Blender! The FLVER
                # exporter will create additional split submeshes as necessary for that.
                existing_bl_material = self.new_materials[existing_bl_material_index]
                if (
                    bool(existing_bl_material["Is Bind Pose"]) == submesh.is_bind_pose
                    and existing_bl_material["Default Bone Index"] == submesh.default_bone_index
                    and existing_bl_material["Face Set Count"] == len(submesh.face_sets)
                    and existing_bl_material.use_backface_culling == submesh.use_backface_culling
                ):
                    # Blender material already exists with the same Mesh properties. No new variant neeed.
                    submesh_bl_material_indices.append(existing_bl_material_index)
                    found_existing_material = True
                    break

            if found_existing_material:
                continue

            # No match found. New Blender material variant is needed to hold unique submesh data.
            variant_index = len(existing_variant_bl_indices)
            first_material = self.new_materials[existing_variant_bl_indices[0]]
            variant_name = first_material.name + f" <Variant {variant_index}>"
            bl_material = get_submesh_blender_material(
                self.operator,
                material,
                material_name=variant_name,
                material_info=flver_material_infos[material_hash],
                submesh=submesh,
                blend_mode=material_blend_mode,
            )  # type: bpy.types.Material

            new_bl_material_index = len(self.new_materials)
            submesh_bl_material_indices.append(new_bl_material_index)
            flver_material_hash_variants[material_hash].append(new_bl_material_index)
            self.new_materials.append(bl_material)
            bl_material_uv_layer_names.append(flver_material_uv_layer_names[material_hash])

        return submesh_bl_material_indices, bl_material_uv_layer_names

    def create_armature(self, base_edit_bone_length: float) -> bpy.types.ArmatureObject:
        """Create a new Blender armature to serve as the parent object for the entire FLVER."""

        self.operator.to_object_mode()
        self.operator.deselect_all()

        bl_armature_data = bpy.data.armatures.new(f"{self.name} Armature")
        bl_armature_obj = self.create_obj(f"{self.name}", bl_armature_data)
        self.create_bones(bl_armature_obj, base_edit_bone_length)

        # noinspection PyTypeChecker
        return bl_armature_obj

    def load_texture_images(self, texture_manager: TextureImportManager = None) -> list[bpy.types.Image]:
        """Load texture images from either `png_cache` folder or TPFs found with `texture_import_manager`.

        Will NEVER load an image that is already in Blender's data, regardless of image type (identified by stem only).
        """
        bl_image_stems = set()
        image_stems_to_replace = set()
        for image in bpy.data.images:
            stem = Path(image.name).stem
            if image.size[:] == (1, 1) and image.pixels[:] == (1.0, 0.0, 1.0, 1.0):
                image_stems_to_replace.add(stem)
            else:
                bl_image_stems.add(stem)
        new_loaded_images = []

        textures_to_load = {}  # type: dict[str, TPFTexture]
        for texture_path in self.flver.get_all_texture_paths():
            texture_stem = texture_path.stem
            if texture_stem in bl_image_stems:
                continue  # already loaded
            if texture_stem in textures_to_load:
                continue  # already queued to load below

            if self.settings.read_cached_pngs and self.settings.png_cache_directory:
                png_path = Path(self.settings.png_cache_directory, f"{texture_stem}.png")
                if png_path.is_file():
                    bl_image = bpy.data.images.load(str(png_path))
                    new_loaded_images.append(bl_image)
                    bl_image_stems.add(texture_stem)
                    continue

            if texture_manager:
                try:
                    texture = texture_manager.get_flver_texture(texture_stem)
                except KeyError as ex:
                    self.warning(str(ex))
                else:
                    textures_to_load[texture_stem] = texture
                    continue

            self.warning(f"Could not find TPF or cached PNG '{texture_path.stem}' for FLVER '{self.name}'.")

        if textures_to_load:
            for texture_stem in textures_to_load:
                self.operator.info(f"Loading texture into Blender: {texture_stem}")
            from time import perf_counter
            t = perf_counter()
            all_png_data = batch_get_tpf_texture_png_data(list(textures_to_load.values()))
            if self.settings.png_cache_directory and self.settings.write_cached_pngs:
                write_png_directory = Path(self.settings.png_cache_directory)
            else:
                write_png_directory = None
            self.operator.info(
                f"Converted images in {perf_counter() - t} s (cached = {self.settings.write_cached_pngs})"
            )
            for texture_stem, png_data in zip(textures_to_load.keys(), all_png_data):
                if png_data is None:
                    continue  # failed to convert this texture
                bl_image = import_png_as_image(
                    texture_stem,
                    png_data,
                    write_png_directory,
                    replace_existing=texture_stem in image_stems_to_replace,
                )
                new_loaded_images.append(bl_image)

        return new_loaded_images

    def create_flver_mesh(
        self,
        flver: FLVER,
        name: str,
        submesh_bl_material_indices: list[int],
        submesh_uv_layer_names: list[list[str]],
    ) -> bpy.types.MeshObject:
        """Create a single Blender mesh that combines all FLVER submeshes, using multiple material slots.

        NOTE: FLVER (for DS1 at least) supports a maximum of 38 bones per sub-mesh. When this maximum is reached, a new
        FLVER submesh is created. All of these sub-meshes are unified in Blender under the same material slot, and will
        be split again on export as needed.

        Some FLVER submeshes also use the same material, but have different `Mesh` or `FaceSet` properties such as
        `use_backface_culling`. Backface culling is a material option in Blender, so these submeshes will use different
        Blender material 'variants' even though they use the same FLVER material. The FLVER exporter will start by
        creating a FLVER material for every Blender material slot, then unify any identical FLVER material instances and
        redirect any differences like `use_backface_culling` or `is_bind_pose` to the FLVER mesh.

        Breakdown:
            - Blender stores POSITION, BONE WEIGHTS, and BONE INDICES on vertices. Any differences here will require
            genuine vertex duplication in Blender. (Of course, vertices at the same position in the same sub-mesh should
            essentially ALWAYS have the same bone weights and indices.)
            - Blender stores MATERIAL SLOT INDEX on faces. This is how different FLVER submeshes are represented.
            - Blender stores UV COORDINATES, VERTEX COLORS, and NORMALS on face loops ('vertex instances'). This gels
            with what FLVER meshes want to do.
            - Blender does not import tangents or bitangents. These are calculated on export.
        """
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        # Armature parent object uses simply `name`. Mesh data/object has 'Mesh' suffix.
        bl_mesh = bpy.data.meshes.new(name=f"{name} Mesh")

        for material in self.new_materials:
            bl_mesh.materials.append(material)

        if not flver.submeshes:
            # FLVER has no meshes (e.g. c0000). Leave empty.
            # noinspection PyTypeChecker
            return self.create_obj(f"{name} Mesh <EMPTY>", bl_mesh)

        if any(mesh.invalid_layout for mesh in flver.submeshes):
            # Corrupted submeshes (e.g. some DS1R map pieces). Leave empty.
            # noinspection PyTypeChecker
            return self.create_obj(f"{name} Mesh <INVALID>", bl_mesh)

        # p = time.perf_counter()
        # Create merged mesh.
        merged_mesh = MergedMesh.from_flver(
            flver,
            submesh_bl_material_indices,
            material_uv_layers=submesh_uv_layer_names,
        )
        # self.operator.info(f"Merged FLVER submeshes in {time.perf_counter() - p} s")

        bl_vert_bone_weights, bl_vert_bone_indices = self.create_bm_mesh(bl_mesh, merged_mesh)

        # noinspection PyTypeChecker
        bl_mesh_obj = self.create_obj(f"{name} Mesh", bl_mesh)  # type: bpy.types.MeshObject

        self.create_bone_vertex_groups(bl_mesh_obj, bl_vert_bone_weights, bl_vert_bone_indices)

        return bl_mesh_obj

    def create_bm_mesh(self, bl_mesh: bpy.types.Mesh, merged_mesh: MergedMesh) -> tuple[np.ndarray, np.ndarray]:
        """BMesh is more efficient for mesh construction and loop data layer assignment.

        Returns two arrays of bone indices and bone weights for the created Blender vertices.
        """

        # p = time.perf_counter()

        merged_mesh.swap_vertex_yz(tangents=False, bitangents=False)
        merged_mesh.invert_vertex_uv(invert_u=False, invert_v=True)
        merged_mesh.normalize_normals()

        bm = bmesh.new()
        bm.from_mesh(bl_mesh)  # bring over UV and vertex color data layers

        if len(merged_mesh.loop_vertex_colors) > 1:
            self.warning("More than one vertex color layer detected. Only the first will be imported into Blender!")

        # CREATE BLENDER VERTICES
        for position in merged_mesh.vertex_data["position"]:
            bm.verts.new(position)
        bm.verts.ensure_lookup_table()

        # Loop indices of `merged_mesh` that actually make it into Blender, as degenerate/duplicate faces are ignored.
        # TODO: I think `MergedMesh` already removes all duplicate faces now, so if I also used it to remove degenerate
        #  faces, I wouldn't have to keep track here.
        valid_loop_indices = []
        # TODO: go back to reporting occurrences per-submesh (`faces[:, 3]`)?
        duplicate_face_count = 0
        degenerate_face_count = 0

        for face in merged_mesh.faces:

            loop_indices = face[:3]
            vertex_indices = merged_mesh.loop_vertex_indices[loop_indices]
            bm_verts = [bm.verts[v_i] for v_i in vertex_indices]

            try:
                bm_face = bm.faces.new(bm_verts)
            except ValueError as ex:
                if "face already exists" in str(ex):
                    # This is a duplicate face (happens rarely in vanilla FLVERs). We can ignore it.
                    # No lasting harm done as, by assertion, no new BMesh vertices were created above. We just need
                    # to remove the last three normals.
                    duplicate_face_count += 1
                    continue
                if "found the same (BMVert) used multiple times" in str(ex):
                    # Degenerate FLVER face (e.g. a line or point). These are not supported by Blender.
                    degenerate_face_count += 1
                    continue

                print(f"Unhandled error for BMFace. Vertices: {[v.co for v in bm_verts]}")
                raise ex

            bm_face.material_index = face[3]
            valid_loop_indices.extend(loop_indices)

        # self.operator.info(f"Created Blender mesh in {time.perf_counter() - p} s")

        if degenerate_face_count or duplicate_face_count:
            self.warning(
                f"{degenerate_face_count} degenerate and {duplicate_face_count} duplicate faces were ignored during "
                f"FLVER import."
            )

        # TODO: Delete all unused vertices at this point (i.e. vertices that were only used by degen faces)?

        bm.to_mesh(bl_mesh)
        bm.free()

        # Create and populate UV and vertex color data layers.
        for i, uv_layer_name in enumerate(merged_mesh.all_uv_layers):
            try:
                merged_loop_uv_array = merged_mesh.loop_uvs[i]
            except IndexError:
                last_i = len(merged_mesh.loop_uvs) - 1
                self.warning(
                    f"UV layer index {i} ('{uv_layer_name}') was not found in merged FLVER. "
                    f"Loading data from last UV index instead: {last_i} ('{merged_mesh.all_uv_layers[last_i]}')"
                )
                merged_loop_uv_array = merged_mesh.loop_uvs[last_i]

            # Create new Blender UV layer.
            uv_layer = bl_mesh.uv_layers.new(name=uv_layer_name, do_init=False)
            loop_uv_data = merged_loop_uv_array[valid_loop_indices].ravel()
            uv_layer.data.foreach_set("uv", loop_uv_data)

        # TODO: Support multiple colors.
        color_layer = bl_mesh.vertex_colors.new(name="VertexColors")
        loop_color_data = merged_mesh.loop_vertex_colors[0][valid_loop_indices].ravel()
        color_layer.data.foreach_set("color", loop_color_data)

        # Enable custom split normals and assign them.
        loop_normal_data = merged_mesh.loop_normals[valid_loop_indices]  # NOT raveled
        bl_mesh.create_normals_split()
        bl_mesh.normals_split_custom_set(loop_normal_data)  # one normal per loop
        bl_mesh.use_auto_smooth = True  # required for custom split normals to actually be used (rather than just face)
        bl_mesh.calc_normals_split()  # copy custom split normal data into API mesh loops

        bl_mesh.update()

        return merged_mesh.vertex_data["bone_weights"], merged_mesh.vertex_data["bone_indices"]

    def create_bone_vertex_groups(
        self,
        bl_mesh_obj: bpy.types.MeshObject,
        bl_vert_bone_weights: np.ndarray,
        bl_vert_bone_indices: np.ndarray,
    ):
        # Naming a vertex group after a Blender bone will automatically link it in the Armature modifier below.
        # NOTE: For imports that use an existing Armature (e.g. equipment), invalid bone names such as the root dummy
        # equipment bones have already been removed from `bl_bone_names` here.
        bone_vertex_groups = [
            bl_mesh_obj.vertex_groups.new(name=bone_name)
            for bone_name in self.bl_bone_names
        ]  # type: list[bpy.types.VertexGroup]

        # Awkwardly, we need a separate call to `VertexGroups[bone_index].add(indices, weight)` for each combination
        # of `bone_index` and `weight`, so the dictionary keys constructed above are a tuple of those two to minimize
        # the number of Blender group `add()` calls needed at the end of this function.
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

    def create_bones(
        self,
        bl_armature_obj: bpy.types.Object,
        base_edit_bone_length: float,
    ):
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
        """

        write_bone_type = ""
        warn_partial_bind_pose = False
        for mesh in self.flver.submeshes:
            if mesh.is_bind_pose:  # characters, objects, parts
                if not write_bone_type:
                    write_bone_type = "EDIT"  # write bone transforms to EditBones
                elif write_bone_type == "POSE":
                    warn_partial_bind_pose = True
                    write_bone_type = "EDIT"
                    break
            else:  # map pieces
                if not write_bone_type:
                    write_bone_type = "POSE"  # write bone transforms to PoseBones
                elif write_bone_type == "EDIT":
                    warn_partial_bind_pose = True
                    break  # keep EDIT default

        if not write_bone_type:
            # TODO: FLVER has no submeshes?
            self.warning(f"FLVER {self.name} has no submeshes. Bones written to EditBones.")
            write_bone_type = "EDIT"

        if warn_partial_bind_pose:
            self.warning(
                f"Some meshes in FLVER {self.name} use `is_bind_pose` (bone data written to EditBones) and some do not "
                f"(bone data written to PoseBones). Writing all bone data to EditBones."
            )

        # TODO: Theoretically, we could handled mixed bind pose/non-bind pose meshes IF AND ONLY IF they did not use the
        #  same bones. The bind pose bones could have their data written to EditBones, and the non-bind pose bones could
        #  have their data written to PoseBones. The 'is_bind_pose' custom property of each mesh can likewise be used on
        #  export, once it's confirmed that the same bone does not appear in both types of mesh.

        self.context.view_layer.objects.active = bl_armature_obj
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="EDIT", toggle=False)

        # noinspection PyTypeChecker
        armature_data = bl_armature_obj.data  # type: bpy.types.Armature
        # Create all edit bones. Head/tail are not set yet (depends on `write_bone_type` below).
        edit_bones = self.create_edit_bones(armature_data)

        # NOTE: Bones that have no vertices weighted to them are left as 'unused' root bones in the FLVER skeleton.
        # They may be animated by HKX animations (and will affect their children appropriately) but will not actually
        # affect any vertices in the mesh.

        if write_bone_type == "EDIT":
            self.write_data_to_edit_bones(edit_bones, base_edit_bone_length)
            del edit_bones  # clear references to edit bones as we exit EDIT mode
            if bpy.ops.object.mode_set.poll():
                bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        elif write_bone_type == "POSE":
            # This method will change back to OBJECT mode internally before setting pose bone data.
            self.write_data_to_pose_bones(bl_armature_obj, edit_bones, base_edit_bone_length)
        else:
            # Should not be possible to reach.
            raise ValueError(f"Invalid `write_bone_type`: {write_bone_type}")

    def create_edit_bones(self, bl_armature_data: bpy.types.Armature) -> list[bpy.types.EditBone]:
        """Create all edit bones from FLVER bones in `bl_armature`."""
        edit_bones = []  # all bones
        for game_bone, bl_bone_name in zip(self.flver.bones, self.bl_bone_names, strict=True):
            game_bone: FLVERBone
            edit_bone = bl_armature_data.edit_bones.new(bl_bone_name)  # '<DUPE>' suffixes already added to names
            edit_bone: bpy.types.EditBone

            # Storing 'Unused' flag for now. TODO: If later games' other flags can't be safely auto-detected, store too.
            edit_bone["Is Unused"] = bool(game_bone.usage_flags & FLVERBoneUsageFlags.UNUSED)

            # If this is `False`, then a bone's rest pose rotation will NOT affect its relative pose basis translation.
            # That is, pose basis translation will be interpreted as being in parent space (or object for root bones)
            # rather than in the 'rest pose space' of this bone. We don't want such behavior, particularly for FLVER
            # root bones like 'Pelvis'.
            edit_bone.use_local_location = True

            # FLVER bones never inherit scale.
            edit_bone.inherit_scale = "NONE"

            # We don't bother storing child or sibling bones. They are generated from parents on export.
            edit_bones.append(edit_bone)
        return edit_bones

    def write_data_to_edit_bones(self, edit_bones: list[bpy.types.EditBone], base_edit_bone_length: float):

        game_arma_transforms = self.flver.get_bone_armature_space_transforms()

        for game_bone, edit_bone, game_arma_transform in zip(
            self.flver.bones, edit_bones, game_arma_transforms, strict=True
        ):
            game_bone: FLVERBone
            game_translate, game_rotmat, game_scale = game_arma_transform

            if not is_uniform(game_scale, rel_tol=0.001):
                self.warning(f"Bone {game_bone.name} has non-uniform scale: {game_scale}. Left as identity.")
                bone_length = base_edit_bone_length
            elif any(c < 0.0 for c in game_scale):
                self.warning(f"Bone {game_bone.name} has negative scale: {game_scale}. Left as identity.")
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
                parent_bone_index = game_bone.parent_bone.get_bone_index(self.flver.bones)
                parent_edit_bone = edit_bones[parent_bone_index]
                edit_bone.parent = parent_edit_bone
                # edit_bone.use_connect = True

    def write_data_to_pose_bones(
        self,
        bl_armature_obj: bpy.types.Object,
        edit_bones: list[bpy.types.EditBone],
        base_edit_bone_length: float,
    ):
        for game_bone, edit_bone in zip(self.flver.bones, edit_bones, strict=True):
            # All edit bones are just Blender-Y-direction ("forward") stubs of base length.
            # This rigging makes map piece 'pose' bone data transform as expected for showing accurate vertex positions.
            edit_bone.head = Vector((0, 0, 0))
            edit_bone.tail = Vector((0, base_edit_bone_length, 0))

        del edit_bones  # clear references to edit bones as we exit EDIT mode
        self.operator.to_object_mode()

        pose_bones = bl_armature_obj.pose.bones
        for game_bone, pose_bone in zip(self.flver.bones, pose_bones):
            # TODO: Pose bone transforms are relative to parent (in both FLVER and Blender).
            #  Confirm map pieces still behave as expected, though (they shouldn't even have child bones).
            pose_bone.rotation_mode = "QUATERNION"  # should already be default, but being explicit
            game_translate, game_bone_rotate = game_bone.translate, game_bone.rotate
            pose_bone.location = GAME_TO_BL_VECTOR(game_translate)
            pose_bone.rotation_quaternion = GAME_TO_BL_EULER(game_bone_rotate).to_quaternion()
            pose_bone.scale = GAME_TO_BL_VECTOR(game_bone.scale)

    def create_dummy(
        self, game_dummy: Dummy, index: int, bl_armature: bpy.types.ArmatureObject, dummy_prefix=""
    ) -> bpy.types.Object:
        """Create an empty object that represents a FLVER 'dummy' (a generic 3D point).

        The reference ID of the dummy (the value used to refer to it in other game files/code) is included in the name,
        so that it can be easily modified. The format of the dummy name should therefore not be changed. (Note that the
        order of dummies does not matter, and multiple dummies can have the same reference ID.)

        All dummies are children of the armature, and most are children of a specific bone given in 'attach_bone_name'.
        As much as I'd like to nest them under another empty object, to properly attach them to the armature, they have
        to be direct children.
        """
        if dummy_prefix:
            name = f"[{dummy_prefix}] {self.name} Dummy<{index}> [{game_dummy.reference_id}]"
        else:
            name = f"{self.name} Dummy<{index}> [{game_dummy.reference_id}]"
        bl_dummy = self.create_obj(name)  # no data (Empty)
        bl_dummy.parent = bl_armature
        bl_dummy.empty_display_type = "ARROWS"  # best display type/size I've found (single arrow not sufficient)
        bl_dummy.empty_display_size = 0.05

        if game_dummy.use_upward_vector:
            bl_rotation_euler = game_forward_up_vectors_to_bl_euler(game_dummy.forward, game_dummy.upward)
        else:  # TODO: I assume this is right (up-ignoring dummies only rotate around vertical axis)
            bl_rotation_euler = game_forward_up_vectors_to_bl_euler(game_dummy.forward, Vector3((0, 1, 0)))

        if game_dummy.parent_bone_index != -1:
            # Bone's FLVER translate is in the space of (i.e. relative to) this parent bone.
            # NOTE: This is NOT the same as the 'attach' bone, which is used as the actual Blender parent and
            # controls how the dummy moves during armature animations.
            bl_bone_name = self.bl_bone_names[game_dummy.parent_bone_index]
            bl_dummy["Parent Bone Name"] = bl_bone_name
            bl_parent_bone_matrix = bl_armature.data.bones[bl_bone_name].matrix_local
            bl_location = bl_parent_bone_matrix @ GAME_TO_BL_VECTOR(game_dummy.translate)
        else:
            # Bone's location is in armature space.
            bl_dummy["Parent Bone Name"] = ""
            bl_location = GAME_TO_BL_VECTOR(game_dummy.translate)

        # Dummy moves with this bone during animations.
        if game_dummy.attach_bone_index != -1:
            bl_dummy.parent_bone = self.bl_bone_names[game_dummy.attach_bone_index]
            bl_dummy.parent_type = "BONE"

        # We need to set the dummy's world matrix, rather than its local matrix, to bypass its possible bone
        # attachment above.
        bl_dummy.matrix_world = Matrix.LocRotScale(bl_location, bl_rotation_euler, Vector((1.0, 1.0, 1.0)))

        # NOTE: Reference ID not included as a property.
        # bl_dummy["reference_id"] = dummy.reference_id  # int
        bl_dummy["Color RGBA"] = game_dummy.color_rgba  # RGBA  # TODO: Use in actual display somehow?
        bl_dummy["Flag 1"] = game_dummy.flag_1  # bool
        bl_dummy["Use Upward Vector"] = game_dummy.use_upward_vector  # bool
        # NOTE: These two properties are only ever non-zero in Sekiro (and probably Elden Ring).
        bl_dummy["Unk x30"] = game_dummy.unk_x30  # int
        bl_dummy["Unk x34"] = game_dummy.unk_x34  # int

        return bl_dummy

    def create_obj(self, name: str, data=None):
        """Create a new Blender object with given `data` and link it to the scene's object collection."""
        obj = bpy.data.objects.new(name, data)
        self.context.scene.collection.objects.link(obj)
        self.new_objs.append(obj)
        return obj

    def warning(self, warning: str):
        self.operator.report({"WARNING"}, warning)

    @property
    def flver_root(self):
        """Always the first object created."""
        return self.new_objs[0]
