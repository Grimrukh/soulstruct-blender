from __future__ import annotations

__all__ = [
    "SelectGameDirectory",
    "SelectMapDirectory",
    "SelectPNGCacheDirectory",
    "SelectCustomMTDBNDFile",
]

from pathlib import Path

from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from io_soulstruct.utilities.operators import LoggingOperator
from .core import GlobalSettings


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
            GlobalSettings.get_scene_settings(context).game_directory = str(game_directory)

        return {'FINISHED'}


class SelectMapDirectory(LoggingOperator, ImportHelper):
    """Browse for game map directory to set both `game_directory` and `map_stem` settings."""
    bl_idname = "soulstruct.select_map_directory"
    bl_label = "Select Map Directory"
    bl_description = "Select game and map directory with browser"

    directory: StringProperty()

    filter_glob: StringProperty(
        default="",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def invoke(self, context, _event):
        """Set the initial directory."""
        game_directory = GlobalSettings.get_scene_settings(context).game_directory
        if game_directory:
            self.filepath = game_directory
        else:
            for steam_common_location in STEAM_COMMON_LOCATIONS:
                if steam_common_location.is_dir():
                    self.filepath = str(steam_common_location)
                    break
        return super().invoke(context, _event)

    def execute(self, context):
        if self.directory:
            map_directory = Path(self.directory).resolve()
            settings = GlobalSettings.get_scene_settings(context)
            settings.map_stem = map_directory.name
            settings.game_directory = str(map_directory.parent.parent)  # parent of 'map' directory

        return {'FINISHED'}


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
            GlobalSettings.get_scene_settings(context).png_cache_directory = str(png_cache_directory)
        return {'FINISHED'}


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
            GlobalSettings.get_scene_settings(context).mtdbnd_path = str(mtdbnd_path)
        return {'FINISHED'}
