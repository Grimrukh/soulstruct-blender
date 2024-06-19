from __future__ import annotations

__all__ = [
    "SelectGameDirectory",
    "SelectProjectDirectory",
    "SelectMapDirectory",
    "SelectPNGCacheDirectory",
    "SelectCustomMTDBNDFile",
    "SelectCustomMATBINBNDFile",
    "ClearCachedLists",
    "LoadCollectionsFromBlend",
]

import re
from pathlib import Path

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from io_soulstruct.utilities.operators import LoggingOperator
from .game_enums import CLEAR_GAME_FILE_ENUMS
from .core import CLEAR_MAP_STEM_ENUM


STEAM_COMMON_LOCATIONS = [
    Path(f"{drive}:/Program Files (x86)/Steam/steamapps/common")
    for drive in "CDEFGH"
]


class SelectGameDirectory(LoggingOperator, ImportHelper):
    """Browse for global game directory."""
    bl_idname = "soulstruct.select_game_directory"
    bl_label = "Select Game Directory"
    bl_description = "Select game directory with browser"

    directory: StringProperty()

    filter_glob: StringProperty(
        default="",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def invoke(self, context, _event):
        """Set the initial directory to browse in, if it exists."""
        for steam_common_location in STEAM_COMMON_LOCATIONS:
            if steam_common_location.is_dir():
                self.filepath = str(steam_common_location)
                break
        return super().invoke(context, _event)

    def execute(self, context):
        if self.filepath:
            # We use browser's current `directory`, not `filepath` itself.
            game_directory = Path(self.directory).resolve()
            settings = self.settings(context)
            settings.str_game_directory = str(game_directory)
            settings.auto_set_game()

            # Refresh cached enum lists.
            CLEAR_GAME_FILE_ENUMS()
            CLEAR_MAP_STEM_ENUM()

        return {"FINISHED"}


class SelectProjectDirectory(LoggingOperator, ImportHelper):
    """Browse for global project directory."""
    bl_idname = "soulstruct.select_project_directory"
    bl_label = "Select Project Directory"
    bl_description = "Select project directory with browser"

    directory: StringProperty()

    filter_glob: StringProperty(
        default="",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def invoke(self, context, _event):
        """Set the initial directory to browse in, if it exists."""
        for steam_common_location in STEAM_COMMON_LOCATIONS:
            if steam_common_location.is_dir():
                self.filepath = str(steam_common_location)
                break
        return super().invoke(context, _event)

    def execute(self, context):
        if self.filepath:
            # We use browser's current `directory`, not `filepath` itself.
            project_directory = Path(self.directory).resolve()
            settings = self.settings(context)
            settings.str_project_directory = str(project_directory)
            # We do NOT auto-set game here, because the user may be exporting to any folder.

            # Refresh cached enum lists.
            CLEAR_GAME_FILE_ENUMS()
            CLEAR_MAP_STEM_ENUM()

        return {"FINISHED"}


class SelectMapDirectory(LoggingOperator, ImportHelper):
    """Browse for game map directory to set both `game_directory` and `map_stem` settings."""
    bl_idname = "soulstruct.select_map_directory"
    bl_label = "Select Map Directory"
    bl_description = "Select game import directory AND map directory with browser"

    directory: StringProperty()

    filter_glob: StringProperty(
        default="",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def invoke(self, context, _event):
        """Set the initial directory."""
        settings = self.settings(context)
        if settings.str_game_directory:
            self.filepath = settings.str_game_directory
        else:
            for steam_common_location in STEAM_COMMON_LOCATIONS:
                if steam_common_location.is_dir():
                    self.filepath = str(steam_common_location)
                    break
        return super().invoke(context, _event)

    def execute(self, context):
        if self.directory:
            map_directory = Path(self.directory).resolve()
            if not re.match(r"m\d\d_\d\d_\d\d_\d\d", map_directory.name):
                self.warning("Selected directory does not appear to be a valid map directory name. Using anyway.")
            settings = self.settings(context)
            settings.map_stem = map_directory.name
            settings.str_game_directory = str(map_directory.parent.parent)  # parent of 'map' directory

            # Refresh cached enum lists.
            CLEAR_GAME_FILE_ENUMS()
            CLEAR_MAP_STEM_ENUM()

        return {"FINISHED"}


class SelectPNGCacheDirectory(LoggingOperator, ImportHelper):
    """Browse for global PNG texture cache directory."""
    bl_idname = "soulstruct.select_png_cache_directory"
    bl_label = "Select PNG Cache Directory"
    bl_description = "Select PNG texture cache directory with browser"

    directory: StringProperty()

    filter_glob: StringProperty(
        default="",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        if self.directory:
            png_cache_directory = Path(self.directory).resolve()
            settings = self.settings(context)
            settings.str_png_cache_directory = str(png_cache_directory)
        return {"FINISHED"}


class SelectCustomMTDBNDFile(LoggingOperator, ImportHelper):
    """Browse for custom MTDBND file."""
    bl_idname = "soulstruct.select_custom_mtdbnd_file"
    bl_label = "Select Custom MTDBND File"
    bl_description = "Select custom MTDBND file with browser"

    filename_ext = ".mtdbnd"
    filter_glob: StringProperty(default="*.mtdbnd;*.mtdbnd.dcx", options={"HIDDEN"})

    def execute(self, context):
        if self.filepath:
            mtdbnd_path = Path(self.filepath).resolve()
            settings = self.settings(context)
            settings.str_mtdbnd_path = str(mtdbnd_path)
        return {"FINISHED"}


class SelectCustomMATBINBNDFile(LoggingOperator, ImportHelper):
    """Browse for custom MATBINBND file."""
    bl_idname = "soulstruct.select_custom_matbinbnd_file"
    bl_label = "Select Custom MATBINBND File"
    bl_description = "Select custom MATBINBND file with browser"

    filename_ext = ".matbinbnd"
    filter_glob: StringProperty(default="*.matbinbnd;*.matbinbnd.dcx", options={"HIDDEN"})

    def execute(self, context):
        if self.filepath:
            matbinbnd_path = Path(self.filepath).resolve()
            settings = self.settings(context)
            settings.str_matbinbnd_path = str(matbinbnd_path)
        return {"FINISHED"}


class ClearCachedLists(LoggingOperator):
    """Clear all cached enum lists, including the list of map folder stems."""
    bl_idname = "soulstruct.clear_cached_lists"
    bl_label = "Clear Cached Lists"
    bl_description = "Clear all cached lists"

    def execute(self, context):
        CLEAR_GAME_FILE_ENUMS()
        CLEAR_MAP_STEM_ENUM()
        return {"FINISHED"}


class LoadCollectionsFromBlend(LoggingOperator, ImportHelper):
    """Load collections and objects from a '.blend' file by linking its root-level collections to this scene.

    Works best with Blend files created using `io_export_blend`, and also works best when all objects in the Blend are
    at least two collections deep.
    """
    bl_idname = "soulstruct.load_collections_from_blend"
    bl_label = "Load Collections from Blend"
    bl_description = "Load collections from a .blend file"

    filename_ext = ".blend"

    filter_glob: StringProperty(
        default="*.blend",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        if not self.filepath:
            return self.error("No file selected.")

        # Get the objects and collections from the file.
        with bpy.data.libraries.load(self.filepath, link=False) as (data_from, data_to):
            data_to.collections = data_from.collections
            data_to.objects = data_from.objects

        imported_collections = [col for col in data_to.collections if col is not None]

        def is_top_level_collection(collection):
            for col in imported_collections:
                if collection.name in col.children:
                    return False
            return True

        top_level_collections = [col for col in imported_collections if is_top_level_collection(col)]

        for top_level_collection in top_level_collections:
            bpy.context.scene.collection.children.link(top_level_collection)

        self.info(f"{len(top_level_collections)} top-level collections loaded from '{self.filepath}'.")

        for lib in bpy.data.libraries:
            if lib.name == Path(self.filepath).name:
                # Remove this library. We're not referencing it.
                bpy.data.libraries.remove(lib)

        return {"FINISHED"}
