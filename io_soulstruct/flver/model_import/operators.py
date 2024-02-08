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
]

import re
import time
import traceback
import typing as tp
from pathlib import Path

import bpy
import bpy.ops

from soulstruct.base.models.flver import FLVER
from soulstruct.containers import Binder

from io_soulstruct.utilities import *
from io_soulstruct.flver.textures.import_textures import TextureImportManager
from io_soulstruct.flver.utilities import *
from .core import FLVERImporter

if tp.TYPE_CHECKING:
    from .settings import FLVERImportSettings


FLVER_BINDER_RE = re.compile(r"^.*?\.(.*bnd)(\.dcx)?$")


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
        importer = FLVERImporter(
            self,
            context,
            settings,
            texture_import_manager=texture_manager,
            mtdbnd=settings.get_mtdbnd(self),
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
    """Import weapon/armor FLVER from a `partsbnd` Binder.

    NOTE: Earlier versions of Soulstruct forced you to select an imported `c0000` model, and the mesh and dummies of
    this equipment FLVER would be parented to that model. However, this was actually destructive, as it prevented the
    user from viewing or editing the partial c0000 Armature that is actually present in the equipment FLVER.

    If you want to animate equipment with c0000 animations, you can simply set those animations to this FLVER -- the
    Armature bones should all be compatible.
    """
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
