"""Property group exposing general, global parameters for the Soulstruct Blender plugin."""
from __future__ import annotations

__all__ = [
    "GameNames",
    "GlobalSettings",
    "MTDBinderManager",
]

from pathlib import Path

import bpy

from soulstruct.containers import Binder
from soulstruct.dcx import DCXType
from soulstruct.base.models.mtd import MTD
from soulstruct.utilities.files import read_json, write_json


_SETTINGS_PATH = Path(__file__).parent.parent / "GlobalSettings.json"


class GameNames:
    # TODO: Should probably make use of my `games` module here to avoid repetition.

    PTDE = "PTDE"  # Dark Souls: Prepare to Die Edition
    DS1R = "DS1R"  # Dark Souls: Remastered
    BB = "BB"  # Bloodborne
    DS3 = "DS3"  # Dark Souls III
    ER = "ER"  # Elden Ring
    # TODO: A few more to add, obviously.


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
        description="Unpacked game directory containing game executable",
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
        description="Path of custom MTDBND file for detecting material setups. "
                    "Defaults to: '{game_directory}/mtd/mtd.mtdbnd{.dcx}')",
        default="",
    )

    use_bak_file: bpy.props.BoolProperty(
        name="Use BAK File",
        description="Use BAK file when quick-importing from game directory (and fail if missing)",
        default=False,
    )

    detect_map_from_parent: bpy.props.BoolProperty(
        name="Detect Map from Parent",
        description="Detect map stem from Blender parent when quick-exporting map assets",
        default=False,
    )

    @staticmethod
    def get_scene_settings(context: bpy.types.Context = None) -> GlobalSettings:
        if context is None:
            context = bpy.context
        return context.scene.soulstruct_global_settings

    @staticmethod
    def get_selected_map_path(context: bpy.types.Context = None) -> Path | None:
        """Get the `map_stem` path in its game directory."""
        settings = GlobalSettings.get_scene_settings(context)
        if not settings.game_directory or not settings.map_stem:
            return None
        return Path(settings.game_directory, "map", settings.map_stem)

    @staticmethod
    def resolve_dcx_type(
        dcx_type_name: str, class_name: str, is_binder_entry=False, context: bpy.types.Context = None
    ) -> DCXType:
        """Get DCX type associated with `class_name` for selected game."""

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
            case "NVM":
                match _game:
                    case "DS1R":
                        return DCXType.Null  # never compressed in map BND
            case "HKX":
                match _game:
                    case "DS1R":
                        return DCXType.DS1_DS2  # compressed in map h/l BXF split binder
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
            dcx_type = settings.resolve_dcx_type("Auto", "Binder", False, context)
            mtdbnd_name = dcx_type.process_path("mtd.mtdbnd")
            mtdbnd_path = Path(settings.game_directory, "mtd", mtdbnd_name)
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


class MTDBinderManager:
    """Holds an opened `MTDBND` Binder and reads/caches `MTD` contents only as requested."""

    mtdbnd: Binder
    _mtds: dict[str, MTD]

    def __init__(self, mtdbnd: Binder):
        self.mtdbnd = mtdbnd
        self._mtds = {}

    def __getitem__(self, mtd_name: str) -> MTD:
        try:
            return self._mtds[mtd_name]
        except KeyError:
            try:
                # Uses LAST MTD found in Binder, as there are a few duplicates.
                mtd_entry = self.mtdbnd.find_entries_matching_name(mtd_name, escape=True)[-1]
            except IndexError:
                raise KeyError(f"Cannot find MTD '{mtd_name}' in MTD Binder '{self.mtdbnd.path}'.")
            mtd = mtd_entry.to_binary_file(MTD)
            self._mtds[mtd_name] = mtd
            return mtd
