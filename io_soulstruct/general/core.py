"""Property group exposing general, global parameters for the Soulstruct Blender plugin."""
from __future__ import annotations

__all__ = [
    "SoulstructSettings",
    "CLEAR_MAP_STEM_ENUM",
]

import traceback

import shutil

import typing as tp
from pathlib import Path

import bpy

from soulstruct.base.base_binary_file import BaseBinaryFile
from soulstruct.base.models.matbin import MATBINBND
from soulstruct.base.models.mtd import MTDBND
from soulstruct.dcx import DCXType
from soulstruct.games import *
from soulstruct.utilities.files import read_json, write_json, create_bak

from io_soulstruct.exceptions import *
from io_soulstruct.utilities import *

if tp.TYPE_CHECKING:
    from soulstruct.base.models.shaders import MatDef
    from io_soulstruct.type_checking import MSB_TYPING
    from io_soulstruct.utilities import LoggingOperator

_SETTINGS_PATH = Path(__file__).parent.parent / "SoulstructSettings.json"

# Associates a game 'map' path and/or project 'map' path with a list of map choice enums.
# Also records filter mode used to generate that list.
_MAP_STEM_FILTER_MODE = ""
_MAP_STEM_ENUM = CachedEnumItems()

# Redirect files that do and do not use the latest version of map files (e.g. to handle Darkroot Garden in DS1).
# Managed in 100% sync with `_MAP_STEM_ENUM` and only used if `SoulstructSettings.smart_map_version_handling == True`.
_NEW_TO_OLD_MAP = {}  # e.g. {"m12_00_00_01": "m12_00_00_00"}
_OLD_TO_NEW_MAP = {}  # e.g. {"m12_00_00_00": "m12_00_00_01"}


def CLEAR_MAP_STEM_ENUM():
    global _MAP_STEM_FILTER_MODE, _MAP_STEM_ENUM, _NEW_TO_OLD_MAP, _OLD_TO_NEW_MAP
    _MAP_STEM_FILTER_MODE = ""
    _MAP_STEM_ENUM = CachedEnumItems()
    _NEW_TO_OLD_MAP = {}
    _OLD_TO_NEW_MAP = {}
    # TODO: Would love to reset map stem enum value to "0" here, but it doesn't seem to reliably be an option yet.


# Global holder for games that front-end users can currently select (or have auto-detected) for the `game` enum.
SUPPORTED_GAMES = [
    DARK_SOULS_PTDE,
    DARK_SOULS_DSR,
    BLOODBORNE,
    ELDEN_RING,
]


# Currently hard-coding maps that we expect to need versioning logic for, as it doesn't apply to m99 maps, etc.
_VERSIONED_MAPS = {
    DARK_SOULS_PTDE.variable_name: ("m12_00_00",),
    DARK_SOULS_DSR.variable_name: ("m12_00_00",),
}


# Indicates which file types prefer OLD versions of the map, and which prefer NEW.
_USE_OLD_MAP_VERSION = (".flver", ".hkxbhd", ".hkxbdt")
_USE_NEW_MAP_VERSION = (".msb", ".nvmbnd", ".mcg", ".mcp")


# Applicable to Elden Ring only. Other games don't need these map categories.
ELDEN_RING_MAP_STEM_FILTERS_RE = {
    "ALL": lambda map_stem: True,
    "LEGACY_DUNGEONS": lambda map_stem: map_stem.area < 30 or map_stem.area in {35, 39},
    "GENERIC_DUNGEONS": lambda map_stem: 30 <= map_stem.area <= 43 and map_stem.area not in {35, 39},
    "ALL_DUNGEONS": lambda map_stem: map_stem.area < 60,
    "OVERWORLD_SMALL": lambda map_stem: map_stem.area == 60 and map_stem.version == 0,
    "OVERWORLD_MEDIUM": lambda map_stem: map_stem.area == 60 and map_stem.version == 1,
    "OVERWORLD_LARGE": lambda map_stem: map_stem.area == 60 and map_stem.version == 2,
    "OVERWORLD_SMALL_V1": lambda map_stem: map_stem.area == 60 and map_stem.version == 10,
    "OVERWORLD_MEDIUM_V1": lambda map_stem: map_stem.area == 60 and map_stem.version == 11,
    "OVERWORLD_LARGE_V1": lambda map_stem: map_stem.area == 60 and map_stem.version == 12,
    "DLC_OVERWORLD_SMALL": lambda map_stem: map_stem.area == 61 and map_stem.version == 0,
    "DLC_OVERWORLD_MEDIUM": lambda map_stem: map_stem.area == 61 and map_stem.version == 1,
    "DLC_OVERWORLD_LARGE": lambda map_stem: map_stem.area == 61 and map_stem.version == 2,
}


# noinspection PyUnusedLocal
def _get_map_stem_items(self, context: bpy.types.Context) -> list[tuple[str, str, str]]:
    """Get list of map stems in game and/or project directory.

    Stems that are in the game or project directory ONLY are marked with a (G) or (P) suffix, respectively. However,
    since this map stem is only used to generate file paths and each import/export operation resolves the source or
    destination file itself, these suffixes are not used in any way internally.

    TODO: If this proves too problematic, I can always hard-code the list of available maps for each game, of course.

    TODO: Definitely need a separate system/enum to manage Elden Ring overworld tiles! Tile X/Y dropdowns...?
    """

    global _MAP_STEM_FILTER_MODE, _MAP_STEM_ENUM, _NEW_TO_OLD_MAP, _OLD_TO_NEW_MAP

    settings = SoulstructSettings.from_context(context)
    if settings.is_game("ELDEN_RING"):
        filter_mode = settings.map_stem_filter_mode
        include_empty_map_tiles = settings.include_empty_map_tiles
    else:
        filter_mode = "ALL"
        include_empty_map_tiles = True
    map_stem_filter_func = ELDEN_RING_MAP_STEM_FILTERS_RE[filter_mode]

    game_directory = settings.game_directory
    game_map_dir_path = Path(game_directory, "map") if game_directory else None
    project_directory = settings.project_directory
    project_map_dir_path = Path(project_directory, "map") if project_directory else None

    if not is_path_and_dir(game_map_dir_path) and not is_path_and_dir(project_map_dir_path):
        _MAP_STEM_FILTER_MODE = ""
        _MAP_STEM_ENUM = CachedEnumItems()  # reset
        _NEW_TO_OLD_MAP = {}
        _OLD_TO_NEW_MAP = {}
        return _MAP_STEM_ENUM.items

    if (
        _MAP_STEM_FILTER_MODE == f"{filter_mode} {include_empty_map_tiles}"
        and _MAP_STEM_ENUM.is_valid(game_map_dir_path, project_map_dir_path)
    ):
        # Filter hasn't changed and cached enum is still valid.
        return _MAP_STEM_ENUM.items

    game_map_stem_names = []
    project_map_stem_names = []
    match settings.game_enum:
        case None:
            pass  # no choices
        case ELDEN_RING.variable_name:
            # Maps are inside area subfolders like 'm10' or 'm60'.

            if not include_empty_map_tiles:
                # Extend filter function to check MSB size of small overworld tiles.
                def er_filter_func(map_dir_: Path):
                    map_stem_ = MapStem.from_string(map_dir_.name)
                    if not map_stem_filter_func(map_stem_):
                        return False
                    if map_stem_.area not in {60, 61} or map_stem_.version != 0:
                        return True  # never ignore non-small, non-V0, and/or non-overworld maps
                    msb_path = map_dir_ / f"../../mapstudio/{map_dir_.name}.msb.dcx"
                    if not msb_path.is_file():
                        return True  # to be safe
                    byte_count = msb_path.stat().st_size
                    if byte_count <= 700:  # rough threshold
                        return False  # no navmesh data
                    return True
            else:
                def er_filter_func(map_dir_: Path):
                    # Only need map stem.
                    return map_stem_filter_func(MapStem.from_string(map_dir_.name))

            if is_path_and_dir(game_map_dir_path):
                for area in sorted(game_map_dir_path.glob("m??")):
                    game_map_stem_names.extend(
                        [
                            f"{map_dir.name}"
                            for map_dir in sorted(area.glob("m??_??_??_??"))
                            if map_dir.is_dir() and er_filter_func(map_dir)
                        ]
                    )
            if is_path_and_dir(project_map_dir_path):
                for area in sorted(project_map_dir_path.glob("m??")):
                    project_map_stem_names.extend(
                        [
                            f"{map_dir.name}"
                            for map_dir in sorted(area.glob("m??_??_??_??"))
                            if map_dir.is_dir() and er_filter_func(map_dir)
                        ]
                    )
        case _:  # standard map stem names
            if is_path_and_dir(game_map_dir_path):
                game_map_stem_names = [
                    map_dir.name
                    for map_dir in sorted(game_map_dir_path.glob("m??_??_??_??"))
                    if map_dir.is_dir() and map_stem_filter_func(MapStem.from_string(map_dir.name))
                ]
            if is_path_and_dir(project_map_dir_path):
                project_map_stem_names = [
                    map_dir.name
                    for map_dir in sorted(project_map_dir_path.glob("m??_??_??_??"))
                    if map_dir.is_dir() and map_stem_filter_func(MapStem.from_string(map_dir.name))
                ]

    if not is_path_and_dir(game_map_dir_path):
        shared_map_stem_names = project_map_stem_names
    elif not is_path_and_dir(project_map_dir_path):
        shared_map_stem_names = game_map_stem_names
    else:
        shared_map_stem_names = sorted(set(game_map_stem_names) & set(project_map_stem_names))

    if settings.is_game("ELDEN_RING"):
        from soulstruct.eldenring.maps.constants import get_map

        def get_map_desc(map_stem: str) -> str:
            try:
                game_map = get_map(map_stem)
                return game_map.verbose_name
            except ValueError:
                return f"Map {map_stem}"

    else:
        def get_map_desc(map_stem: str) -> str:
            return f"Map {map_stem}"

    # TODO: Get rid of this (P) (G) rubbish?
    map_stems = [
        (name, name, get_map_desc(name))
        for name in shared_map_stem_names
    ] + [
        (name, f"{name} (G)", get_map_desc(name) + " (in game only)")
        for name in sorted(set(game_map_stem_names) - set(shared_map_stem_names))
    ] + [
        (name, f"{name} (P)", get_map_desc(name) + " (in project only)")
        for name in sorted(set(project_map_stem_names) - set(shared_map_stem_names))
    ]

    # Check for map stem version redirects when using 'smart' map version handling.
    # TODO: Functions currently assume that a matching MSB exists for each 'map' subdirectory.
    _NEW_TO_OLD_MAP = {}
    _OLD_TO_NEW_MAP = {}
    found_map_stems = set(map_stem for map_stem, _, _ in map_stems)
    if settings.game_enum in _VERSIONED_MAPS:
        for map_stem, _, _ in map_stems:
            if map_stem.startswith(_VERSIONED_MAPS[settings.game_enum]):
                if map_stem.endswith("00"):
                    new_map_stem = map_stem[:-2] + "01"
                    if new_map_stem in found_map_stems:
                        _OLD_TO_NEW_MAP[map_stem] = new_map_stem
                elif map_stem.endswith("01"):
                    old_map_stem = map_stem[:-2] + "00"
                    if old_map_stem in found_map_stems:
                        _NEW_TO_OLD_MAP[map_stem] = old_map_stem

    _MAP_STEM_FILTER_MODE = f"{filter_mode} {include_empty_map_tiles}"
    _MAP_STEM_ENUM = CachedEnumItems(game_map_dir_path, project_map_dir_path, map_stems)
    return _MAP_STEM_ENUM.items


# noinspection PyUnusedLocal
def _update_map_stem(self, context):
    """Reset all selected game enums to "None" ("0"), as they will all change for a new map."""
    for key in bpy.context.scene.soulstruct_game_enums.__annotations__:
        try:
            setattr(bpy.context.scene.soulstruct_game_enums, key, "0")
        except TypeError:
            pass  # enum has no values


class SoulstructSettings(bpy.types.PropertyGroup):
    """Global settings for the Soulstruct Blender plugin."""

    # region Blender and Wrapper Properties

    game_enum: bpy.props.EnumProperty(
        name="Game",
        description="Game currently being worked on. Determines available features, default data values, "
                    "file paths/extensions/compression, etc. Must match selected game directory",
        items=[
            (game.variable_name, game.name, game.name)
            for game in SUPPORTED_GAMES
        ],
        default=DARK_SOULS_DSR.variable_name,
    )

    @property
    def game(self) -> Game | None:
        """Get selected Game object from `soulstruct.games`."""
        return get_game(self.game_enum) if self.game_enum else None

    str_game_directory: bpy.props.StringProperty(
        name="Game Directory",
        description="Root (containing EXE/BIN) of game directory to import files from when they are missing from the "
                    "project directory, and optionally export to if 'Also Export to Game' is enabled",
        default="",
    )

    @property
    def game_directory(self) -> Path | None:
        return Path(self.str_game_directory) if self.str_game_directory else None

    str_project_directory: bpy.props.StringProperty(
        name="Project Directory",
        description="Project root directory with game-like structure to export to. Files for import and Binders needed "
                    "for exporting new entries will also be sourced here first if they exist",
        default="",
    )

    @property
    def project_directory(self) -> Path | None:
        return Path(self.str_project_directory) if self.str_project_directory else None

    prefer_import_from_project: bpy.props.BoolProperty(
        name="Prefer Import from Project",
        description="When importing, prefer files/folders from project directory over game directory if they exist",
        default=True,
    )

    also_export_to_game: bpy.props.BoolProperty(
        name="Also Export to Game",
        description="Export files to the game directory in addition to the project directory (if given)",
        default=False,
    )

    map_stem_filter_mode: bpy.props.EnumProperty(
        name="Map Stem Filter Mode",
        description="Filter mode for Map Stem dropdown. Only used by Elden Ring",
        items=[
            ("ALL", "All", "Show all map stems. Dropdown may grow too large in Elden Ring"),
            ("LEGACY_DUNGEONS", "Legacy Dungeons Only", "Show only map stems for legacy dungeons and special maps"),
            ("GENERIC_DUNGEONS", "Generic Dungeons Only", "Show only map stems for generic (non-legacy) dungeons"),
            ("ALL_DUNGEONS", "All Dungeons Only", "Show only map stems for legacy/generic dungeons (not m60)"),
            ("OVERWORLD_SMALL", "Overworld (Small) Only", "Show only map stems for overworld small tiles"),
            ("OVERWORLD_MEDIUM", "Overworld (Medium) Only", "Show only map stems for overworld medium tiles"),
            ("OVERWORLD_LARGE", "Overworld (Large) Only", "Show only map stems for overworld large tiles"),
            ("OVERWORLD_SMALL_V1", "Overworld (Small V1) Only", "Show only map stems for small tiles (version 1)"),
            ("OVERWORLD_MEDIUM_V1", "Overworld (Medium V1) Only", "Show only map stems for medium tiles (version 1)"),
            ("OVERWORLD_LARGE_V1", "Overworld (Large V1) Only", "Show only map stems for large tiles (version 1)"),
            ("DLC_OVERWORLD_SMALL", "DLC Overworld (Small) Only", "Show only map stems for overworld small tiles"),
            ("DLC_OVERWORLD_MEDIUM", "DLC Overworld (Medium) Only", "Show only map stems for overworld medium tiles"),
            ("DLC_OVERWORLD_LARGE", "DLC Overworld (Large) Only", "Show only map stems for overworld large tiles"),
            # NOTE: There are V1 DLC overworld maps, but few enough that they can be included with the above filters.
        ],
    )

    include_empty_map_tiles: bpy.props.BoolProperty(
        name="Include Empty Map Tiles",
        description="Include Elden Ring overworld small map tiles with compressed MSB size < 700 bytes",
        default=False,
    )

    map_stem: bpy.props.EnumProperty(
        name="Map Stem",
        description="Directory in game/project 'map' folder to use when importing or exporting map assets",
        items=_get_map_stem_items,
        update=_update_map_stem,
    )

    str_mtdbnd_path: bpy.props.StringProperty(
        name="MTDBND Path",
        description="Path of custom MTDBND file for detecting material setups. "
                    "Defaults to an automatic known location in selected project (preferred) or game directory",
        default="",
    )

    @property
    def mtdbnd_path(self) -> Path | None:
        return Path(self.str_mtdbnd_path) if self.str_mtdbnd_path else None

    str_matbinbnd_path: bpy.props.StringProperty(
        name="MATBINBND Path",
        description="Path of custom MATBINBND file for detecting material setups in Elden Ring only. "
                    "Defaults to an automatic known location in selected project (preferred) or game directory. "
                    "If '_dlc01' and '_dlc02' variants of path name are found, they will also be loaded",
        default="",
    )

    @property
    def matbinbnd_path(self) -> Path | None:
        return Path(self.str_matbinbnd_path) if self.str_matbinbnd_path else None

    str_png_cache_directory: bpy.props.StringProperty(
        name="PNG Cache Directory",
        description="Path of directory to read/write cached PNG textures (from game DDS textures)",
        default="",
    )

    @property
    def png_cache_directory(self) -> Path | None:
        return Path(self.str_png_cache_directory) if self.str_png_cache_directory else None

    read_cached_pngs: bpy.props.BoolProperty(
        name="Read Cached PNGs",
        description="Read cached PNGs with matching stems from PNG cache (if given) rather than converting DDS "
                    "textures of imported FLVERs",
        default=True,
    )

    write_cached_pngs: bpy.props.BoolProperty(
        name="Write Cached PNGs",
        description="Write cached PNGs of imported FLVER textures (converted from DDS files) to PNG cache if given, so "
                    "they can be loaded more quickly in the future or modified by the user without DDS headaches",
        default=True,
    )

    pack_image_data: bpy.props.BoolProperty(
        name="Pack Image Data",
        description="Pack Blender Image texture data into Blend file, rather than simply linking to the cached PNG "
                    "image on disk (if it exists)",
        default=False,
    )

    import_bak_file: bpy.props.BoolProperty(
        name="Import BAK File",
        description="Import from '.bak' backup file when auto-importing from project/game directory. If enabled and a "
                    "'.bak' file is not found, the import will fail",
        default=False,
    )

    detect_map_from_collection: bpy.props.BoolProperty(
        name="Detect Map from Collection",
        description="Detect map stem (e.g. 'm10_00_00_00') from name of first map-like Blender collection name of "
                    "selected objects when exporting map assets",
        default=True,
    )

    smart_map_version_handling: bpy.props.BoolProperty(
        name="Use Smart Map Version Handling",
        description="If enabled, Blender auto-import/export will always use the latest versions of MSB, NVMBND, MCG, "
                    "and MCP map files, but will still use the original versions of FLVER and HKXBHD/BDT files. This "
                    "is the correct way to handle files for Darkroot Garden in DS1. Selecting map m12_00_00_00 vs. "
                    "m12_00_00_01 in the dropdown will therefore have no effect on auto-import/export",
        default=True,
    )

    # Generic enough to place here. Only used by certain operators.
    new_model_name: bpy.props.StringProperty(
        name="New Model Name",
        description="Name of the new model to create/rename",
        default="",  # default is operator-dependent
    )

    # endregion

    @staticmethod
    def from_context(context: bpy.types.Context = None) -> SoulstructSettings:
        if context is None:
            context = bpy.context
        return context.scene.soulstruct_settings

    def is_game(self, *name_or_game: str | Game) -> bool:
        """Check if any `name_or_game` is the selected `Game`."""
        for game in name_or_game:
            game = get_game(game)
            if game is self.game:
                return True
        return False

    @property
    def game_variable_name(self) -> str:
        game = self.game
        return game.variable_name if game else ""

    def auto_set_game(self):
        """Determine `game` enum value from `game_directory`."""
        if not self.str_game_directory:
            return
        for game in SUPPORTED_GAMES:
            executable_path = Path(self.str_game_directory, game.executable_name)
            if executable_path.is_file():
                self.game_enum = game.variable_name
                return

    def _process_path(self, path: Path, dcx_type: DCXType | None) -> Path:
        """Process path with given `dcx_type`, or default DCX type if `dcx_type` is `None` and the path name contains a
        period (i.e. doesn't look like a directory)."""
        if dcx_type is not None:
            path = dcx_type.process_path(path)
        elif "." in path.name:
            path = self.game.process_dcx_path(path)
        if "." in path.name and self.import_bak_file:  # add extra '.bak' suffix
            return path.with_suffix(path.suffix + ".bak")
        return path

    def get_game_path(self, *parts: str | Path, dcx_type: DCXType = None) -> Path | None:
        """Get path relative to selected game directory. Does NOT check if the file/directory actually exists.

        If `dcx_type` is given (including `Null`), the path will be processed by that DCX type. Otherwise, the known
        game specific/default DCX type for the file type will be used.

        Will add `.bak` suffix to path if `import_bak_file` is enabled.
        """
        if not self.str_game_directory:
            return None
        game_path = Path(self.str_game_directory, *parts)
        return self._process_path(game_path, dcx_type)

    def get_game_map_path(self, *parts, dcx_type: DCXType = None, map_stem="") -> Path | None:
        """Get the `map/{map_stem}` path, and optionally further, in the game directory.

        If `dcx_type` is given (including `Null`), the path will be processed by that DCX type. Otherwise, the known
        game specific/default DCX type for the file type will be used.
        """
        map_stem = self._process_map_stem_version(map_stem or self.map_stem, *parts)
        if not self.str_game_directory or map_stem in {"", "0"}:
            return None
        if self.is_game("ELDEN_RING"):
            # Area subfolders in 'map'.
            map_path = Path(self.str_game_directory, f"map/{map_stem[:3]}/{map_stem}", *parts)
        else:
            map_path = Path(self.str_game_directory, f"map/{map_stem}", *parts)
        return self._process_path(map_path, dcx_type)

    def get_game_msb_path(self, map_stem="") -> Path | None:
        """Get the `map_stem` MSB path in the game `map/MapStudio` directory."""
        map_stem = map_stem or self.map_stem
        if not self.str_game_directory or map_stem in {"", "0"}:
            return None
        return self.get_game_path(self.get_relative_msb_path(map_stem))

    def get_project_path(self, *parts: str | Path, dcx_type: DCXType = None) -> Path | None:
        """Get path relative to the selected project directory.

        If `dcx_type` is given (including `Null`), the path will be processed by that DCX type. Otherwise, the known
        game specific/default DCX type for the file type will be used.
        """
        if not self.str_project_directory:
            return None
        project_path = Path(self.str_project_directory, *parts)
        return self._process_path(project_path, dcx_type)

    def get_project_map_path(self, *parts, dcx_type: DCXType = None, map_stem="") -> Path | None:
        """Get the `map/{map_stem}` path, and optionally further, in the project directory.

        If `dcx_type` is given (including `Null`), the path will be processed by that DCX type. Otherwise, the known
        game specific/default DCX type for the file type will be used.
        """
        map_stem = self._process_map_stem_version(map_stem or self.map_stem, *parts)
        if not self.str_project_directory or map_stem in {"", "0"}:
            return None
        if self.is_game("ELDEN_RING"):
            # Area subfolders in 'map'.
            map_path = Path(self.str_game_directory, f"map/{map_stem[:3]}/{map_stem}", *parts)
        else:
            map_path = Path(self.str_project_directory, f"map/{map_stem}", *parts)
        return self._process_path(map_path, dcx_type)

    def get_project_msb_path(self, map_stem="") -> Path | None:
        """Get the `map_stem` MSB path in the project `map/MapStudio` directory."""
        map_stem = map_stem or self.map_stem
        if not self.str_project_directory or map_stem in {"", "0"}:
            return None
        return self.get_project_path(self.get_relative_msb_path(map_stem))

    def get_oldest_map_stem_version(self, map_stem=""):
        """Check if `smart_map_version_handling` is enabled and return the oldest version of the map stem if so."""
        map_stem = map_stem or self.map_stem
        if self.smart_map_version_handling and map_stem in _NEW_TO_OLD_MAP:
            return _NEW_TO_OLD_MAP[map_stem]
        return map_stem

    def get_latest_map_stem_version(self, map_stem=""):
        """Check if `smart_map_version_handling` is enabled and return the latest version of the map stem if so."""
        map_stem = map_stem or self.map_stem
        if self.smart_map_version_handling and map_stem in _OLD_TO_NEW_MAP:
            return _OLD_TO_NEW_MAP[map_stem]
        return map_stem

    def get_import_file_path(self, *parts: str | Path, dcx_type: DCXType = None) -> Path:
        """Try to get file path relative to project or game directory first, depending on `prefer_import_from_project`,
        then fall back to the same path relative to the other directory if the preferred file does not exist.

        Raises a `FileNotFoundError` if the path cannot be found in EITHER directory.

        If `dcx_type` is given (including `Null`), the path will be processed by that DCX type. Otherwise, the known
        game specific/default DCX type for the file type will be used.
        """
        if self.prefer_import_from_project:
            funcs = [self.get_project_path, self.get_game_path]
        else:
            funcs = [self.get_game_path, self.get_project_path]
        funcs: list[tp.Callable[..., Path]]
        for func in funcs:
            path = func(*parts, dcx_type=dcx_type)
            if is_path_and_file(path):
                return path
        raise FileNotFoundError(f"File not found in project or game directory with parts: {parts}")

    def get_import_dir_path(self, *parts: str | Path) -> Path | None:
        """Try to get directory path relative to project or game directory first, depending on
        `prefer_import_from_project`, then fall back to the same path relative to the other directory if the preferred
        directory does not exist.

        Raises a `NotADirectoryError` if the path cannot be found in EITHER directory.
        """
        if self.prefer_import_from_project:
            funcs = [self.get_project_path, self.get_game_path]
        else:
            funcs = [self.get_game_path, self.get_project_path]
        funcs: list[tp.Callable[..., Path]]
        for func in funcs:
            path = func(*parts)
            if is_path_and_dir(path):
                return path
        raise NotADirectoryError(f"Directory not found in project or game directory: {parts}")

    def has_import_dir_path(self, *parts: str | Path) -> bool:
        """Check if import directory path exists."""
        try:
            return bool(self.get_import_dir_path(*parts))
        except NotADirectoryError:
            return False

    def get_import_map_path(self, *parts: str | Path, map_stem="") -> Path | None:
        """Get the `map_stem` 'map' directory path, and optionally further, in the preferred directory.

        If `smart_map_version_handling` is enabled, this will redirect to the earliest or latest version of the map if
        the file is a known versioned type.
        """
        map_stem = self._process_map_stem_version(map_stem or self.map_stem, *parts)
        if map_stem in {"", "0"}:
            return None

        if self.is_game("ELDEN_RING"):
            # Area subfolders in 'map'.
            map_path = Path(self.str_game_directory, f"map/{map_stem[:3]}/{map_stem}", *parts)
        else:
            map_path = Path(f"map/{map_stem}", *parts)
        if "." in map_path.name:
            return self.get_import_file_path(map_path)
        return self.get_import_dir_path(map_path)

    def get_import_msb_path(self, map_stem="") -> Path | None:
        """Get the `map_stem` MSB path in the preferred `map/MapStudio` directory."""
        map_stem = map_stem or self.map_stem
        if map_stem in {"", "0"}:
            return None
        return self.get_import_file_path(self.get_relative_msb_path(map_stem))

    def get_modified_export_file_path(self, *parts: str | Path, dcx_type: DCXType = None) -> Path:
        """Get file path relative to project directory if set, and game directory otherwise.

        Used primarily to retrieve binders that are about to be modified, as we want to start with any modified project
        binders already exported to the project directory if they exist.
        """
        if self.prefer_import_from_project:
            funcs = [self.get_project_path, self.get_game_path]
        else:
            funcs = [self.get_game_path, self.get_project_path]
        funcs: list[tp.Callable[..., Path]]
        for func in funcs:
            path = func(*parts, dcx_type=dcx_type)
            if is_path_and_file(path):
                return path
        raise FileNotFoundError(f"File not found in project or game directory: {parts}")

    def get_relative_msb_path(self, map_stem="") -> Path | None:
        """Get relative MSB path of given `map_stem` (or selected by default) for selected game.

        If `smart_map_version_handling` is enabled, this will redirect to the latest version of the MSB.
        """
        map_stem = map_stem or self.map_stem
        if map_stem in {"", "0"}:
            return None
        # Check if a new MSB version exists to redirect to.
        map_stem = _OLD_TO_NEW_MAP.get(map_stem, map_stem)
        return self.game.process_dcx_path(
            Path(self.game.default_file_paths["MapStudioDirectory"], f"{map_stem}.msb")
        )

    @property
    def can_auto_export(self) -> bool:
        """Checks if `project_directory` is set and/or `game_directory` is set and `also_export_to_game`
        is enabled, in which case auto-export operators will poll `True`."""
        if self.str_project_directory:
            return True
        if self.str_game_directory and self.also_export_to_game:
            return True
        return False

    def export_file(
        self, operator: LoggingOperator, file: BaseBinaryFile, relative_path: Path, class_name=""
    ) -> set[str]:
        """Write `file` to `relative_path` in project directory (if given) and optionally also to game directory if
        `also_export_to_game` is enabled.

        `class_name` is used for logging and will be automatically detected from `file` if not given.
        """
        from .game_enums import CLEAR_GAME_FILE_ENUMS

        if relative_path.is_absolute():
            # Indicates a mistake in an operator.
            raise ValueError(f"Relative path for export must be relative to game root, not absolute: {relative_path}")
        try:
            self._export_file(operator, file, relative_path, class_name)
        except Exception as e:
            traceback.print_exc()
            operator.report({"ERROR"}, f"Failed to export {class_name if class_name else '<unknown>'} file: {e}")
            return {"CANCELLED"}

        # Clear enums so any new files/folders/entries can be detected.
        CLEAR_MAP_STEM_ENUM()
        CLEAR_GAME_FILE_ENUMS()

        return {"FINISHED"}

    def _export_file(self, operator: LoggingOperator, file: BaseBinaryFile, relative_path: Path, class_name=""):
        if not class_name:
            class_name = file.cls_name

        if self.project_directory:
            project_path = self.get_project_path(relative_path)
            project_path.parent.mkdir(parents=True, exist_ok=True)
            written = file.write(project_path)  # will create '.bak' if appropriate
            operator.info(f"Exported {class_name} to: {written}")
            if self.game_directory and self.also_export_to_game:
                # Copy all written files to game directory.
                for written_path in written:
                    written_relative_path = written_path.relative_to(self.project_directory)
                    game_path = self.get_game_path(written_relative_path)
                    if game_path.is_file():
                        create_bak(game_path)  # we may be about to replace it
                        operator.info(f"Created backup file in game directory: {game_path}")
                    else:
                        game_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(written_path, game_path)
                    operator.info(f"Copied exported {class_name} file to game directory: {game_path}")
        elif self.game_directory and self.also_export_to_game:
            game_path = self.get_game_path(relative_path)
            game_path.parent.mkdir(parents=True, exist_ok=True)
            written = file.write(game_path)
            operator.info(f"Exported {class_name} to game directory only: {written}")
        else:
            operator.warning(
                f"Cannot export {class_name} file. Project directory is not set and game directory is either not "
                f"set or 'Also Export to Game' is disabled."
            )

    def export_file_data(
        self, operator: LoggingOperator, data: bytes, relative_path: Path, class_name: str
    ) -> set[str]:
        """Version of `export_file` that takes raw `bytes` data instead of a `BaseBinaryFile`.

        `class_name` must be given in this case because it cannot be automatically detected.
        """
        from .game_enums import CLEAR_GAME_FILE_ENUMS

        try:
            self._export_file_data(operator, data, relative_path, class_name)
        except Exception as e:
            traceback.print_exc()
            operator.report({"ERROR"}, f"Failed to export {class_name} file: {e}")
            return {"CANCELLED"}

        # Clear enums so any new files/folders/entries can be detected.
        CLEAR_MAP_STEM_ENUM()
        CLEAR_GAME_FILE_ENUMS()

        return {"FINISHED"}

    def _export_file_data(self, operator: LoggingOperator, data: bytes, relative_path: Path, class_name: str):
        if self.project_directory:
            project_path = self.get_project_path(relative_path)
            if project_path.is_file():
                create_bak(project_path)
                operator.info(f"Created backup file in project directory: {project_path}")
            else:
                project_path.parent.mkdir(parents=True, exist_ok=True)
            project_path.write_bytes(data)
            operator.info(f"Exported {class_name} to: {project_path}")
            if self.game_directory and self.also_export_to_game:
                # Copy to game directory.
                game_path = self.get_game_path(relative_path)
                if game_path.is_file():
                    create_bak(game_path)
                    operator.info(f"Created backup file in game directory: {game_path}")
                else:
                    game_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(project_path, game_path)
                operator.info(f"Copied exported {class_name} to game directory: {game_path}")
        elif self.game_directory and self.also_export_to_game:
            game_path = self.get_game_path(relative_path)
            if game_path.is_file():
                create_bak(game_path)
                operator.info(f"Created backup file in game directory: {game_path}")
            else:
                game_path.parent.mkdir(parents=True, exist_ok=True)
            game_path.write_bytes(data)
            operator.info(f"Exported {class_name} to game directory only: {game_path}")
        else:
            operator.warning(
                f"Cannot export {class_name} file. Project directory is not set and game directory is either not "
                f"set or 'Also Export to Game' is disabled."
            )

    def export_text_file(self, operator: LoggingOperator, text: str, relative_path: Path, encoding="utf-8") -> set[str]:
        """Write `text` string to `relative_path` in project directory (if given) and optionally also to game directory
        if `also_export_to_game` is enabled.
        """
        from .game_enums import CLEAR_GAME_FILE_ENUMS

        if relative_path.is_absolute():
            # Indicates a mistake in an operator.
            raise ValueError(f"Relative path for export must be relative to game root, not absolute: {relative_path}")
        try:
            self._export_text_file(operator, text, relative_path, encoding)
        except Exception as e:
            traceback.print_exc()
            operator.report({"ERROR"}, f"Failed to export text file: {e}")
            return {"CANCELLED"}

        # Clear enums so any new files/folders/entries can be detected.
        # Probably not necessary for writing text files, but still good practice.
        CLEAR_MAP_STEM_ENUM()
        CLEAR_GAME_FILE_ENUMS()

        return {"FINISHED"}

    def _export_text_file(self, operator: LoggingOperator, text: str, relative_path: Path, encoding: str):

        if self.project_directory:
            project_path = self.get_project_path(relative_path, dcx_type=DCXType.Null)
            project_path.parent.mkdir(parents=True, exist_ok=True)
            if project_path.is_file():
                create_bak(project_path)
                operator.info(f"Created backup file in project directory: {project_path}")
            with project_path.open("w", encoding=encoding) as f:
                f.write(text)
            operator.info(f"Exported text file to: {project_path}")
            if self.game_directory and self.also_export_to_game:
                # We still do a copy operation rather than a second write, so file metadata matches.
                game_path = self.get_game_path(relative_path, dcx_type=DCXType.Null)
                if game_path.is_file():
                    create_bak(game_path)  # we may be about to replace it
                    operator.info(f"Created backup file in game directory: {game_path}")
                else:
                    game_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(project_path, game_path)
                operator.info(f"Copied exported text file to game directory: {game_path}")
        elif self.game_directory and self.also_export_to_game:
            game_path = self.get_game_path(relative_path, dcx_type=DCXType.Null)
            game_path.parent.mkdir(parents=True, exist_ok=True)
            with game_path.open("w", encoding=encoding) as f:
                f.write(text)
            operator.info(f"Exported text file to game directory only: {game_path}")
        else:
            operator.warning(
                f"Cannot export text file: {relative_path}. Project directory is not set and game directory is either "
                f"not set or 'Also Export to Game' is disabled."
            )

    def prepare_project_file(
        self,
        relative_path: Path,
        overwrite_existing: bool = None,
        must_exist=False,
        dcx_type: DCXType = None,
    ) -> Path | None:
        """Copy file from game directory to project directory, if both are set.

        Useful for creating initial Binders and MSBs in project directory that are only being partially modified with
        new exported entries.

        Does nothing if project directory is not set, in which case you are either exporting to the game directory only
        or will likely hit an exception later on.

        Never creates a `.bak` backup file.

        Args:
            relative_path: Path relative to game root directory.
            overwrite_existing: If `False`, the file will not be copied if it already exists in the project directory.
                If `True`, the file will always be copied, overwriting any existing project file.
                If `None` (default), the file will be copied if and only if `prefer_import_from_project = False`, so
                that the initial file used comes from the game.
            must_exist: If `True`, the file must already exist in the project directory or successfully be copied from
                the game directory (assuming the project directory is set).
            dcx_type: If given, will manually override the file type's DCX type.
        """
        from .game_enums import CLEAR_GAME_FILE_ENUMS

        if overwrite_existing is None:
            overwrite_existing = not self.prefer_import_from_project

        game_path = self.get_game_path(relative_path, dcx_type=dcx_type)
        project_path = self.get_project_path(relative_path, dcx_type=dcx_type)

        if not is_path_and_file(game_path) and not is_path_and_file(project_path):
            # Neither file exists.
            if must_exist:
                raise FileNotFoundError(f"File does not exist in project or game directory: {relative_path}")
            return None

        if project_path is None:
            # Project directory not set. No chance of copying anything.
            if game_path.is_file():
                return game_path
            elif must_exist:
                raise FileNotFoundError(
                    f"Project directory is not set and file does not exist in game directory: {relative_path}"
                )
            return None  # no project directory and game file does not exist

        if is_path_and_file(project_path) and not overwrite_existing:
            return project_path  # already exists

        if not is_path_and_file(game_path):
            # Game file is missing. Project file either already exists or doesn't exist (possible exception).
            if project_path.is_file():  # already known not to be `None`
                return project_path
            elif must_exist:
                raise FileNotFoundError(f"File does not exist in game or project directory: {relative_path}")
            return None  # nothing to copy (may or may not already exist in project)

        # Copy game file to project directory and use new project file path.
        try:
            project_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(game_path, project_path)
        except Exception as ex:
            raise RuntimeError(f"Failed to copy file '{game_path.name}' from game directory to project directory: {ex}")

        # Clear enums so any new files/folders/entries can be detected.
        CLEAR_MAP_STEM_ENUM()
        CLEAR_GAME_FILE_ENUMS()

        return project_path

    def get_map_stem_for_export(self, obj: bpy.types.Object = None, oldest=False, latest=False) -> str:
        """Get map stem for export based on `obj` name, or fall back to settings map stem."""
        if oldest and latest:
            raise ValueError("Cannot specify both `oldest` and `latest` as True when getting map stem for export.")
        if obj and self.detect_map_from_collection:
            map_stem = get_collection_map_stem(obj)
        else:
            map_stem = self.map_stem
        if oldest:
            map_stem = self.get_oldest_map_stem_version(map_stem)
        elif latest:
            map_stem = self.get_latest_map_stem_version(map_stem)
        return map_stem

    def get_game_msb_class(self) -> type[MSB_TYPING]:
        """Get the `MSB` class associated with the selected game."""
        try:
            return self.game.from_game_submodule_import("maps.msb", "MSB")
        except ImportError:
            # TODO: Specific exception type?
            raise UnsupportedGameError(f"Game {self.game} does not have an MSB class in Soulstruct.")

    def get_game_matdef_class(self) -> type[MatDef]:
        """Get the `MatDef` class associated with the selected game."""
        try:
            return self.game.from_game_submodule_import("models.shaders", "MatDef")
        except ImportError:
            # TODO: Specific exception type?
            raise UnsupportedGameError(f"Game {self.game} does not have a MatDef class in Soulstruct.")

    def resolve_dcx_type(self, dcx_type_name: str, class_name: str) -> DCXType:
        """Get DCX type associated with `class_name` for selected game.

        NOTE: Those should generally only be called for loose files or files inside uncompressed split BHD binders
        (usually TPFs). Files inside compressed BND binders never use DCX, as far as I'm aware.

        If `dcx_type_name` is not "Auto", it is returned directly.
        """

        if dcx_type_name != "Auto":
            # Manual DCX type given.
            return DCXType[dcx_type_name]
        return self.game.get_dcx_type(class_name)

    def get_mtdbnd(self, operator: LoggingOperator) -> MTDBND | None:
        """Load `MTDBND` from custom path, standard location in game directory, or bundled Soulstruct file."""
        if is_path_and_file(self.mtdbnd_path):
            return MTDBND.from_path(self.mtdbnd_path)

        # Try to find MTDBND in project or game directory.
        mtdbnd_names = [
            resource_path.name
            for resource_key, resource_path in self.game.bundled_resource_paths.items()
            if resource_key.endswith("MTDBND")
        ]

        if self.prefer_import_from_project:
            dirs = (("project", self.project_directory), ("game", self.game_directory))
        else:
            dirs = (("game", self.game_directory), ("project", self.project_directory))

        mtdbnd = None  # type: MTDBND | None
        for label, directory in dirs:
            if not directory:
                continue
            for mtdbnd_name in mtdbnd_names:
                dir_mtdbnd_path = directory / f"mtd/{mtdbnd_name}"
                if dir_mtdbnd_path.is_file():
                    operator.info(
                        f"Found MTDBND '{dir_mtdbnd_path.name}' in {label} directory: {dir_mtdbnd_path}"
                    )
                    if mtdbnd is None:
                        mtdbnd = MTDBND.from_path(dir_mtdbnd_path)
                    else:
                        mtdbnd |= MTDBND.from_path(dir_mtdbnd_path)
        if mtdbnd is not None:  # found
            return mtdbnd

        operator.info(f"Loading bundled MTDBND for game {self.game.name}...")
        return MTDBND.from_bundled(self.game)

    def get_matbinbnd(self, operator: LoggingOperator) -> MATBINBND | None:
        """Load `MATBINBND` from custom path, standard location in game directory, or bundled Soulstruct file."""
        if is_path_and_file(self.matbinbnd_path):
            return MATBINBND.from_path(self.matbinbnd_path)

        # Try to find MATBINBND in project or game directory.
        matbinbnd_names = [
            resource_path.name
            for resource_key, resource_path in self.game.bundled_resource_paths.items()
            if resource_key.endswith("MATBINBND")
        ]

        if self.prefer_import_from_project:
            dirs = (("project", self.project_directory), ("game", self.game_directory))
        else:
            dirs = (("game", self.game_directory), ("project", self.project_directory))

        matbinbnd = None  # type: MATBINBND | None
        for label, directory in dirs:
            if not directory:
                continue
            for matbinbnd_name in matbinbnd_names:
                dir_matbinbnd_path = directory / f"matbin/{matbinbnd_name}"
                if dir_matbinbnd_path.is_file():
                    operator.info(
                        f"Found MATBINBND '{dir_matbinbnd_path.name}' in {label} directory: {dir_matbinbnd_path}"
                    )
                    if matbinbnd is None:
                        matbinbnd = MATBINBND.from_path(dir_matbinbnd_path)
                    else:
                        matbinbnd |= MATBINBND.from_path(dir_matbinbnd_path)
        if matbinbnd is not None:  # found
            return matbinbnd

        operator.info(f"Loading bundled MATBINBND for game {self.game.name}...")
        return MATBINBND.from_bundled(self.game)

    def _process_map_stem_version(self, map_stem: str, *parts: str | Path) -> str:
        if not self.smart_map_version_handling or not parts:
            return map_stem

        if not self.is_game("DARK_SOULS_PTDE", "DARK_SOULS_DSR"):
            return map_stem  # only for DS1 at the moment (untested for other games)

        # Check if an older or newer version of the map exists to redirect to, depending on file type.
        last_part = str(parts[-1]).lower().removesuffix(".dcx")
        if map_stem in _OLD_TO_NEW_MAP and last_part.endswith(_USE_NEW_MAP_VERSION):
            # Redirect to NEW map version.
            return _OLD_TO_NEW_MAP[map_stem]
        elif map_stem in _NEW_TO_OLD_MAP and last_part.endswith(_USE_OLD_MAP_VERSION):
            # Redirect to OLD map version.
            return _NEW_TO_OLD_MAP[map_stem]
        return map_stem

    def load_settings(self):
        """Read settings from JSON file and set them in the scene."""
        try:
            json_settings = read_json(_SETTINGS_PATH)
        except FileNotFoundError:
            return  # do nothing
        self.game_enum = json_settings.get("game_enum", DARK_SOULS_DSR.variable_name)
        self.str_game_directory = json_settings.get("str_game_directory", "")
        self.str_project_directory = json_settings.get("str_project_directory", "")
        self.prefer_import_from_project = json_settings.get("prefer_import_from_project", True)
        self.also_export_to_game = json_settings.get("also_export_to_game", False)
        map_stem = json_settings.get("map_stem", "0")
        if not map_stem:
            map_stem = "0"  # null enum value
        self.map_stem = map_stem
        self.str_mtdbnd_path = json_settings.get("str_mtdbnd_path", "")
        self.str_matbinbnd_path = json_settings.get("str_matbinbnd_path", "")
        self.str_png_cache_directory = json_settings.get("str_png_cache_directory", "")
        self.read_cached_pngs = json_settings.get("read_cached_pngs", True)
        self.write_cached_pngs = json_settings.get("write_cached_pngs", True)
        self.pack_image_data = json_settings.get("pack_image_data", False)
        self.import_bak_file = json_settings.get("import_bak_file", False)
        self.detect_map_from_collection = json_settings.get("detect_map_from_collection", True)
        self.smart_map_version_handling = json_settings.get("smart_map_version_handling", True)

    def save_settings(self):
        """Write settings from scene to JSON file."""
        current_settings = {
            key: getattr(self, key)
            for key in (
                "game_enum",
                "str_game_directory",
                "str_project_directory",
                "prefer_import_from_project",
                "also_export_to_game",
                "map_stem",
                "str_mtdbnd_path",
                "str_matbinbnd_path",
                "str_png_cache_directory",
                "read_cached_pngs",
                "write_cached_pngs",
                "pack_image_data",
                "import_bak_file",
                "detect_map_from_collection",
                "smart_map_version_handling",
            )
        }
        write_json(_SETTINGS_PATH, current_settings, indent=4)
        # print(f"Saved settings to {_SETTINGS_PATH}")
