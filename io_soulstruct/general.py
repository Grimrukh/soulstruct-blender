"""Property group exposing general, global parameters for the Soulstruct Blender plugin."""
from __future__ import annotations

__all__ = [
    "GameNames",
    "GAME_DEFAULTS",
    "GlobalSettings",
    "GameFiles",
    "GlobalSettingsPanel",
    "GlobalSettingsPanel_View",
    "SelectGameDirectory",
    "SelectMapDirectory",
    "SelectPNGCacheDirectory",
    "SelectCustomMTDBNDFile",
    "get_cached_file",
]

import typing as tp
from pathlib import Path

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper
from soulstruct.containers import Binder
from soulstruct.dcx import DCXType
from soulstruct.utilities.files import read_json, write_json
from soulstruct.utilities.binary import get_blake2b_hash

from .utilities import LoggingOperator, MTDBinderManager

if tp.TYPE_CHECKING:
    from soulstruct.base.base_binary_file import BASE_BINARY_FILE_T


_SETTINGS_PATH = Path(__file__).parent / "GlobalSettings.json"


class GameNames:
    # TODO: Should probably make use of my `games` module here to avoid repetition.

    PTDE = "PTDE"  # Dark Souls: Prepare to Die Edition
    DS1R = "DS1R"  # Dark Souls: Remastered
    BB = "BB"
    DS3 = "DS3"
    # TODO: More to add, obviously.
    ER = "ER"  # Elden Ring


GAME_DEFAULTS = {
    GameNames.DS1R: {
        "chrbnd_flver_id": 200,
        "chrbnd_flver_path": "N:\\FRPG\\data\\INTERROOT_x64\\chr\\{stem}\\{stem}.flver",
    },
}


class GlobalSettings(bpy.types.PropertyGroup):
    """Global settings for the Soulstruct Blender plugin."""

    game: bpy.props.EnumProperty(
        name="Game",
        description="Game to use when choosing default values, DCX compression, file paths/extensions, etc",
        items=[
            (GameNames.DS1R, GameNames.DS1R, "Dark Souls: Remastered"),
        ],
        default=GameNames.DS1R,
    )

    game_directory: bpy.props.StringProperty(
        name="Game Directory",
        description="Path of game directory",
        default="",
    )

    map_stem: bpy.props.StringProperty(
        name="Map Stem",
        description="Stem of map name to use when auto-importing or exporting map assets (e.g. 'm10_00_00_00')",
        default="",
    )

    png_cache_directory: bpy.props.StringProperty(
        name="PNG Cache Directory",
        description="Path of directory to read/write cached PNG textures (from game DDS textures)",
        default="",
    )

    mtdbnd_path: bpy.props.StringProperty(
        name="MTDBND Path",
        description="Path of custom MTDBND file. Default: '{game_directory}/mtd/mtd.mtdbnd{.dcx}')",
        default="",
    )

    @staticmethod
    def get_scene_settings(context: bpy.types.Context = None) -> GlobalSettings:
        if context is None:
            context = bpy.context
        return context.scene.soulstruct_global_settings

    @staticmethod
    def resolve_dcx_type(
        dcx_type_name: str, class_name: str, is_binder_entry=False, context: bpy.types.Context = None
    ) -> DCXType:
        if dcx_type_name != "Auto":
            # Manual DCX type given.
            return DCXType[dcx_type_name]

        _game = GlobalSettings.get_scene_settings(context).game
        match class_name.upper():
            case "BINDER":
                match _game:
                    case "DS1R":
                        return DCXType.DS1_DS2
            case "FLVER":
                match _game:
                    case "DS1R":
                        return DCXType.Null if is_binder_entry else DCXType.DS1_DS2
            case "HKX":
                match _game:
                    case "DS1R":
                        return DCXType.Null
        raise ValueError(f"Default DCX compression for class name '{class_name}' and game '{_game}' is unknown.")

    @staticmethod
    def get_mtd_manager(context: bpy.types.Context = None) -> MTDBinderManager | None:
        """Find MTDBND and return a manager that grants on-demand MTD access to the LAST MTD file in the binder."""
        settings = GlobalSettings.get_scene_settings(context)
        mtdbnd_path = settings.mtdbnd_path
        if not mtdbnd_path:
            if not settings.game_directory:
                return None  # cannot find MTDBND without game directory
            # Guess path.
            binder_dcx = settings.resolve_dcx_type("Auto", "BINDER", False, context)
            mtdbnd_name = "mtd.mtdbnd.dcx" if binder_dcx != DCXType.Null else "mtd.mtdbnd"
            mtdbnd_path = Path(bpy.context.scene.soulstruct_global_settings.game_directory, "mtd", mtdbnd_name)
            if not mtdbnd_path.is_file():
                return None

        mtdbnd = Binder.from_path(mtdbnd_path)
        return MTDBinderManager(mtdbnd)

    @staticmethod
    def load_settings():
        """Read settings from JSON file and set them in the scene."""
        try:
            json_settings = read_json(_SETTINGS_PATH)
        except FileNotFoundError:
            return  # do nothing
        settings = bpy.context.scene.soulstruct_global_settings
        settings.game = json_settings.get("game", "DS1R")
        settings.game_directory = json_settings.get("game_directory", "")
        settings.map_stem = json_settings.get("map_stem", "")
        settings.png_cache_directory = json_settings.get("png_cache_directory", "")
        settings.mtdbnd_path = json_settings.get("mtdbnd_path", "")

    @staticmethod
    def save_settings():
        """Write settings from scene to JSON file."""
        settings = bpy.context.scene.soulstruct_global_settings
        current_settings = {
            key: getattr(settings, key)
            for key in ("game", "game_directory", "map_stem", "png_cache_directory", "mtdbnd_path")
        }
        write_json(_SETTINGS_PATH, current_settings, indent=4)
        print(f"Saved settings to {_SETTINGS_PATH}")


# Global variables to keep enum references alive.
MAP_PIECE_FLVERS = [("0", "None", "None")]
CHRBNDS = [("0", "None", "None")]
OBJBNDS = [("0", "None", "None")]


def collect_map_piece_flvers(self, context):
    settings = GlobalSettings.get_scene_settings(context)
    game_directory = settings.game_directory
    map_stem = settings.map_stem

    MAP_PIECE_FLVERS.clear()
    MAP_PIECE_FLVERS.append(("0", "None", "None"))

    if game_directory and map_stem and (map_path := Path(game_directory, "map", map_stem)).is_dir():
        flver_glob = "*.flver"
        if settings.resolve_dcx_type("Auto", "FLVER", False, context) != DCXType.Null:
            flver_glob += ".dcx"
        MAP_PIECE_FLVERS.extend(
            [(str(f), f.name.split(".")[0], f.name.split(".")[0]) for f in map_path.glob(flver_glob)]
        )

    return MAP_PIECE_FLVERS


def collect_chrbnds(self, context):
    settings = GlobalSettings.get_scene_settings(context)
    game_directory = settings.game_directory

    CHRBNDS.clear()
    CHRBNDS.append(("0", "None", "None"))

    if game_directory and (chr_path := Path(game_directory, "chr")).is_dir():
        chrbnd_glob = "*.chrbnd"
        if settings.resolve_dcx_type("Auto", "BINDER", False, context) != DCXType.Null:
            chrbnd_glob += ".dcx"
        CHRBNDS.extend(
            [(str(f), f.name.split(".")[0], f.name.split(".")[0]) for f in chr_path.glob(chrbnd_glob)]
        )
    return CHRBNDS


class GameFiles(bpy.types.PropertyGroup):
    """Files of various types found in the game directory via scan."""

    map_piece_flver: bpy.props.EnumProperty(
        name="Map Piece FLVERs",
        items=collect_map_piece_flvers,
    )

    chrbnd: bpy.props.EnumProperty(
        name="Character Binders",
        items=collect_chrbnds,
    )

    # NOTE: Too many objects for an enum to handle well.
    objbnd_name: bpy.props.StringProperty(
        name="Object Name",
        description="Name of OBJBND object file to import",
    )


# Maps file paths to `(BaseBinaryFile, blake2b_hash)` tuples for caching. Useful for inspecting, say, MSB files
# repeatedly without modifying them.
_CACHED_FILES = {}


def get_cached_file(file_path: Path | str, file_type: tp.Type[BASE_BINARY_FILE_T]) -> BASE_BINARY_FILE_T:
    """Load a `BaseBinaryFile` from disk and cache it in a global dictionary.

    NOTE: Obviously, these cached `BaseBinaryFile` instances should be read-only, generally speaking!
    """
    file_path = Path(file_path)
    if not file_path.is_file():
        # Not loaded, even if cached.
        _CACHED_FILES.pop(file_path, None)
        raise FileNotFoundError(f"Cannot find file '{file_path}'.")

    # The hashing process reads the file anyway, so we may as well save the second read if it's actually needed.
    file_data = file_path.read_bytes()
    file_path_hash = get_blake2b_hash(file_data)
    if file_path in _CACHED_FILES:
        game_file, cached_hash = _CACHED_FILES[file_path]
        if cached_hash == file_path_hash:
            # Can return cached file.
            return game_file
        # Hash has changed, so update cache below.
    game_file = file_type.from_bytes(file_data)
    _CACHED_FILES[file_path] = (game_file, file_path_hash)
    return game_file


class GlobalSettingsPanel(bpy.types.Panel):
    """Properties panel for Soulstruct global settings."""
    bl_label = "Soulstruct Settings"
    bl_idname = "SCENE_PT_soulstruct_settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.soulstruct_global_settings, "game")

        row = layout.row(align=True)
        split = row.split(factor=0.75)
        split.column().prop(context.scene.soulstruct_global_settings, "game_directory")
        split.column().operator(SelectGameDirectory.bl_idname, text="Browse")

        row = layout.row()
        split = row.split(factor=0.75)
        split.column().prop(context.scene.soulstruct_global_settings, "map_stem")
        split.column().operator(SelectMapDirectory.bl_idname, text="Browse")

        row = layout.row()
        split = row.split(factor=0.75)
        split.column().prop(context.scene.soulstruct_global_settings, "png_cache_directory")
        split.column().operator(SelectPNGCacheDirectory.bl_idname, text="Browse")

        row = layout.row()
        split = row.split(factor=0.75)
        split.column().prop(context.scene.soulstruct_global_settings, "mtdbnd_path")
        split.column().operator(SelectCustomMTDBNDFile.bl_idname, text="Browse")


class GlobalSettingsPanel_View(bpy.types.Panel):
    """Properties panel for Soulstruct global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.soulstruct_global_settings, "game")

        row = layout.row(align=True)
        split = row.split(factor=0.75)
        split.column().prop(context.scene.soulstruct_global_settings, "game_directory")
        split.column().operator(SelectGameDirectory.bl_idname, text="Browse")

        row = layout.row()
        split = row.split(factor=0.75)
        split.column().prop(context.scene.soulstruct_global_settings, "map_stem")
        split.column().operator(SelectMapDirectory.bl_idname, text="Browse")

        row = layout.row()
        split = row.split(factor=0.75)
        split.column().prop(context.scene.soulstruct_global_settings, "png_cache_directory")
        split.column().operator(SelectPNGCacheDirectory.bl_idname, text="Browse")

        row = layout.row()
        split = row.split(factor=0.75)
        split.column().prop(context.scene.soulstruct_global_settings, "mtdbnd_path")
        split.column().operator(SelectCustomMTDBNDFile.bl_idname, text="Browse")


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
        """Set the initial directory."""
        steam_common = Path("C:/Program Files (x86)/Steam/steamapps/common")
        if steam_common.is_dir():
            self.filepath = steam_common
        return super().invoke(context, _event)

    def execute(self, context):
        if self.filepath:
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
            steam_common = Path("C:/Program Files (x86)/Steam/steamapps/common")
            if steam_common.is_dir():
                self.filepath = steam_common
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
