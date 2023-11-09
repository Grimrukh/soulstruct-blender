"""Property group exposing general, global parameters for the Soulstruct Blender plugin."""
from __future__ import annotations

__all__ = [
    "GameNames",
    "SoulstructSettings",
]

import typing as tp
from pathlib import Path

import bpy

from soulstruct.base.maps.msb import MSB as BaseMSB
from soulstruct.dcx import DCXType
from soulstruct.utilities.files import read_json, write_json

from soulstruct.base.models.mtd import MTDBND
from soulstruct.darksouls1ptde.models.mtd import MTDBND as PTDE_MTDBND
from soulstruct.darksouls1r.models.mtd import MTDBND as DS1R_MTDBND

_SETTINGS_PATH = Path(__file__).parent.parent / "SoulstructSettings.json"


class GameNames:
    # TODO: Should probably make use of my `games` module here to avoid repetition.

    PTDE = "PTDE"  # Dark Souls: Prepare to Die Edition
    DS1R = "DS1R"  # Dark Souls: Remastered
    BB = "BB"  # Bloodborne
    DS3 = "DS3"  # Dark Souls III
    ER = "ER"  # Elden Ring
    # TODO: A few more to add, obviously.


_MAP_STEM_ENUM_ITEMS = (None, [("0", "None", "None")])  # type: tuple[Path | None, list[tuple[str, str, str]]]


# noinspection PyUnusedLocal
def _get_map_stem_items(self, context: bpy.types.Context):
    """Get list of map stems in game directory."""
    settings = SoulstructSettings.get_scene_settings(context)
    game_directory = settings.game_directory
    global _MAP_STEM_ENUM_ITEMS

    if not game_directory:
        _MAP_STEM_ENUM_ITEMS = (None, [("0", "None", "None")])
        return _MAP_STEM_ENUM_ITEMS[1]

    map_dir_path = Path(game_directory, "map")
    if not map_dir_path.is_dir():
        _MAP_STEM_ENUM_ITEMS = (None, [("0", "None", "None")])
        return _MAP_STEM_ENUM_ITEMS[1]

    if _MAP_STEM_ENUM_ITEMS[0] == map_dir_path:
        return _MAP_STEM_ENUM_ITEMS[1]  # cached

    map_stem_names = []
    match settings.game:
        case GameNames.DS1R:
            map_stem_names = [map_stem.name for map_stem in sorted(map_dir_path.glob("m*_*_*_*")) if map_stem.is_dir()]
        case GameNames.PTDE:
            map_stem_names = [map_stem.name for map_stem in sorted(map_dir_path.glob("m*_*_*_*")) if map_stem.is_dir()]
        case GameNames.ER:
            for area in sorted(map_dir_path.glob("m*")):
                map_stem_names.extend([
                    f"{area.name}/{map_stem.name}"
                    for map_stem in sorted(area.glob("m*_*_*_*"))
                    if map_stem.is_dir()
                ])
        case _:
            pass  # leave empty

    _MAP_STEM_ENUM_ITEMS = (
        map_dir_path, [("0", "None", "None")] + [
            (name, name, f"Map {name}")
            for name in map_stem_names
        ]
    )

    return _MAP_STEM_ENUM_ITEMS[1]


class SoulstructSettings(bpy.types.PropertyGroup):
    """Global settings for the Soulstruct Blender plugin."""

    game: bpy.props.EnumProperty(
        name="Game",
        description="Game to use when choosing default values, DCX compression, file paths/extensions, etc",
        items=[
            (GameNames.DS1R, GameNames.DS1R, "Dark Souls: Remastered"),
            # (GameNames.ER, GameNames.ER, "Elden Ring"),
        ],
        default=GameNames.DS1R,
    )

    game_directory: bpy.props.StringProperty(
        name="Game Directory",
        description="Unpacked game directory containing game executable",
        default="",
    )

    map_stem: bpy.props.EnumProperty(
        name="Map Stem",
        description="Directory in game 'map' folder to use when auto-importing or exporting map assets",
        items=_get_map_stem_items,
    )

    png_cache_directory: bpy.props.StringProperty(
        name="PNG Cache Directory",
        description="Path of directory to read/write cached PNG textures (from game DDS textures)",
        default="",
    )

    read_cached_pngs: bpy.props.BoolProperty(
        name="Read Cached PNGs",
        description="Read cached PNGs with matching stems from PNG cache (if given) rather than converting DDS "
                    "textures of imported FLVERs",
        default=True,
    )

    write_cached_pngs: bpy.props.BoolProperty(
        name="Write Cached PNGs",
        description="Write cached PNGs of imported FLVER textures (converted from DDS files) to PNG cache if given",
        default=True,
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
        description="Detect map stem from Blender parent when quick-exporting game map assets",
        default=True,
    )

    @staticmethod
    def get_scene_settings(context: bpy.types.Context = None) -> SoulstructSettings:
        if context is None:
            context = bpy.context
        return context.scene.soulstruct_settings

    @staticmethod
    def get_game_path(*parts: str, context: bpy.types.Context = None) -> Path:
        """Get path relative to game directory."""
        settings = SoulstructSettings.get_scene_settings(context)
        return Path(settings.game_directory, *parts)

    @staticmethod
    def get_selected_map_path(context: bpy.types.Context = None) -> Path | None:
        """Get the `map_stem` path in its game directory."""
        settings = SoulstructSettings.get_scene_settings(context)
        if not settings.game_directory or settings.map_stem in {"", "0"}:
            return None
        return Path(settings.game_directory, "map", settings.map_stem)

    @staticmethod
    def get_selected_map_msb_path(context: bpy.types.Context = None) -> Path | None:
        """Get the `map_stem` MSB path in its game directory."""
        settings = SoulstructSettings.get_scene_settings(context)
        if not settings.game_directory or settings.map_stem in {"", "0"}:
            return None
        return Path(settings.game_directory, "map/MapStudio", f"{settings.map_stem}.msb")

    @staticmethod
    def get_game_msb_class(context: bpy.types.Context = None) -> tp.Type[BaseMSB]:
        """Get the `MSB` class associated with the selected game."""
        settings = SoulstructSettings.get_scene_settings(context)
        match settings.game:
            case GameNames.DS1R:
                from soulstruct.darksouls1r.maps.msb import MSB
                return MSB
        raise ValueError(f"Game '{settings.game}' is not supported for MSB access.")

    @staticmethod
    def resolve_dcx_type(
        dcx_type_name: str, class_name: str, is_binder_entry=False, context: bpy.types.Context = None
    ) -> DCXType:
        """Get DCX type associated with `class_name` for selected game."""

        if dcx_type_name != "Auto":
            # Manual DCX type given.
            return DCXType[dcx_type_name]

        _game = SoulstructSettings.get_scene_settings(context).game
        match class_name.upper():
            case "BINDER":
                match _game:
                    case "DS1R":
                        return DCXType.DS1_DS2
                    case "ER":
                        return DCXType.DCX_KRAK
            case "FLVER":
                match _game:
                    case "DS1R":
                        return DCXType.Null if is_binder_entry else DCXType.DS1_DS2
                    case "ER":
                        return DCXType.Null if is_binder_entry else DCXType.DCX_KRAK  # no loose FLVERs I think
            case "TPF":
                match _game:
                    case "DS1R":
                        return DCXType.Null if is_binder_entry else DCXType.DS1_DS2
                    case "ER":
                        return DCXType.Null if is_binder_entry else DCXType.DCX_KRAK
            case "NVM":
                match _game:
                    case "DS1R":
                        return DCXType.Null  # never compressed in map BND
            case "MAPCOLLISIONHKX":
                match _game:
                    case "DS1R":
                        return DCXType.DS1_DS2  # compressed in map h/l BXF split binder
            case "ANIMATIONHKX":
                match _game:
                    case "DS1R":
                        return DCXType.Null  # never compressed in ANIBND
        raise ValueError(f"Default DCX compression for class name '{class_name}' and game '{_game}' is unknown.")

    @staticmethod
    def get_mtdbnd(context: bpy.types.Context = None) -> MTDBND | None:
        """Load `MTDBND` from custom path, standard location in game directory, or bundled Soulstruct file."""
        settings = SoulstructSettings.get_scene_settings(context)

        match settings.game:
            case GameNames.PTDE:
                mtdbnd_class = PTDE_MTDBND
                from_bundled = mtdbnd_class.from_bundled
            case GameNames.DS1R:
                mtdbnd_class = DS1R_MTDBND
                from_bundled = mtdbnd_class.from_bundled
            case _:
                # No MTDBND class for this game yet. Use generic base class (no bundled).
                mtdbnd_class = MTDBND
                from_bundled = None

        mtdbnd_path = settings.mtdbnd_path
        if not mtdbnd_path and settings.game_directory:
            # Guess MTDBND path.
            dcx_type = settings.resolve_dcx_type("Auto", "Binder", False, context)
            for mtdbnd_name in (
                "mtd.mtdbnd", "allmaterialbnd.mtdbnd"
            ):
                mtdbnd_path = dcx_type.process_path(Path(settings.game_directory, "mtd", mtdbnd_name))
                if mtdbnd_path.is_file():
                    print(f"Found MTDBND: {mtdbnd_path}")
                    break
        else:
            mtdbnd_path = Path(mtdbnd_path)

        if mtdbnd_path.is_file():
            return mtdbnd_class.from_path(mtdbnd_path)

        if from_bundled:
            print(f"Loading bundled MTDBND for game {settings.game}...")
            return from_bundled()
        return None

    @staticmethod
    def load_settings():
        """Read settings from JSON file and set them in the scene."""
        try:
            json_settings = read_json(_SETTINGS_PATH)
        except FileNotFoundError:
            return  # do nothing
        settings = bpy.context.scene.soulstruct_settings
        settings.game = json_settings.get("game", "DS1R")
        settings.game_directory = json_settings.get("game_directory", "")
        map_stem = json_settings.get("map_stem", "0")
        if not map_stem:
            map_stem = "0"  # null enum value
        settings.map_stem = map_stem
        settings.png_cache_directory = json_settings.get("png_cache_directory", "")
        settings.read_cached_pngs = json_settings.get("read_cached_pngs", True)
        settings.write_cached_pngs = json_settings.get("write_cached_pngs", True)
        settings.mtdbnd_path = json_settings.get("mtdbnd_path", "")
        settings.use_bak_file = json_settings.get("use_bak_file", False)
        settings.detect_map_from_parent = json_settings.get("detect_map_from_parent", True)

    @staticmethod
    def save_settings():
        """Write settings from scene to JSON file."""
        settings = bpy.context.scene.soulstruct_settings
        current_settings = {
            key: getattr(settings, key)
            for key in (
                "game", "game_directory", "map_stem",
                "png_cache_directory", "read_cached_pngs", "write_cached_pngs",
                "mtdbnd_path",
                "use_bak_file", "detect_map_from_parent",
            )
        }
        write_json(_SETTINGS_PATH, current_settings, indent=4)
        print(f"Saved settings to {_SETTINGS_PATH}")
