"""Property group exposing general, global parameters for the Soulstruct Blender plugin."""
from __future__ import annotations

__all__ = [
    "SoulstructSettings",
]

import traceback

import shutil

import typing as tp
from pathlib import Path

import bpy

from soulstruct.base.base_binary_file import BaseBinaryFile
from soulstruct.base.models.mtd import MTDBND
from soulstruct.dcx import DCXType
from soulstruct.games import *
from soulstruct.utilities.files import read_json, write_json, create_bak

if tp.TYPE_CHECKING:
    from io_soulstruct.type_checking import MSB_TYPING, MATBINBND_TYPING
    from io_soulstruct.utilities import LoggingOperator

_SETTINGS_PATH = Path(__file__).parent.parent / "SoulstructSettings.json"

_MAP_STEM_ENUM_ITEMS = (None, [("0", "None", "None")])  # type: tuple[Path | None, list[tuple[str, str, str]]]


# Global holder for games that front-end users can currently select (or have auto-detected) for the `game` enum.
SUPPORTED_GAMES = [
    DARK_SOULS_PTDE,
    DARK_SOULS_DSR,
]


# noinspection PyUnusedLocal
def _get_map_stem_items(self, context: bpy.types.Context):
    """Get list of map stems in project/game directory."""
    # TODO: Probably need to combine map stems in project and game...? Ugh.
    settings = SoulstructSettings.from_context(context)
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
    match settings.game_enum:
        case None:
            pass  # no choices
        case ELDEN_RING.variable_name:
            for area in sorted(map_dir_path.glob("m??")):
                map_stem_names.extend(
                    [
                        f"{area.name}/{map_stem.name}"
                        for map_stem in sorted(area.glob("m??_??_??_??"))
                        if map_stem.is_dir()
                    ]
                )
        case _:  # standard map stem names
            map_stem_names = [
                map_stem.name for map_stem in sorted(map_dir_path.glob("m??_??_??_??")) if map_stem.is_dir()
            ]

    _MAP_STEM_ENUM_ITEMS = (
        map_dir_path, [("0", "None", "None")] + [
            (name, name, f"Map {name}")
            for name in map_stem_names
        ]
    )

    return _MAP_STEM_ENUM_ITEMS[1]


class SoulstructSettings(bpy.types.PropertyGroup):
    """Global settings for the Soulstruct Blender plugin."""

    # region Blender and Wrapper Properties

    game_enum: bpy.props.EnumProperty(
        name="Game",
        description="Game to use when choosing default values, DCX compression, file paths/extensions, etc",
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

    also_export_to_game: bpy.props.BoolProperty(
        name="Also Export to Game",
        description="Export files to the game directory in addition to the project directory (if given)",
        default=False,
    )

    map_stem: bpy.props.EnumProperty(
        name="Map Stem",
        description="Directory in game/project 'map' folder to use when importing or exporting map assets",
        items=_get_map_stem_items,
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
                    "Defaults to an automatic known location in selected project (preferred) or game directory",
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

    import_bak_file: bpy.props.BoolProperty(
        name="Import BAK File",
        description="Import from '.bak' backup file when auto-importing from project/game directory. If enabled and a "
                    "'.bak' file is not found, the import will fail",
        default=False,
    )

    detect_map_from_parent: bpy.props.BoolProperty(
        name="Detect Map from Parent",
        description="Detect map stem (e.g. 'm10_00_00_00') from name of selected objects' Blender parent(s) when "
                    "auto-exporting map assets",
        default=True,
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
            if isinstance(game, Game) and game is self.game:
                return True
            elif get_game(game) is self.game:
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
        import_path = Path(self.str_game_directory, *parts)
        return self._process_path(import_path, dcx_type)

    def get_game_map_path(self, *parts, dcx_type: DCXType = None) -> Path | None:
        """Get the `map/{map_stem}` path, and optionally further, in the game directory.

        If `dcx_type` is given (including `Null`), the path will be processed by that DCX type. Otherwise, the known
        game specific/default DCX type for the file type will be used.
        """
        if not self.str_game_directory or self.map_stem in {"", "0"}:
            return None
        import_path = Path(self.str_game_directory, f"map/{self.map_stem}", *parts)
        return self._process_path(import_path, dcx_type)

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
        export_path = Path(self.str_project_directory, *parts)
        return self._process_path(export_path, dcx_type)

    def get_project_map_path(self, *parts, dcx_type: DCXType = None) -> Path | None:
        """Get the `map/{map_stem}` path, and optionally further, in the project directory.

        If `dcx_type` is given (including `Null`), the path will be processed by that DCX type. Otherwise, the known
        game specific/default DCX type for the file type will be used.
        """
        if not self.str_project_directory or self.map_stem in {"", "0"}:
            return None
        export_path = Path(self.str_project_directory, f"map/{self.map_stem}", *parts)
        return self._process_path(export_path, dcx_type)

    def get_project_msb_path(self, map_stem="") -> Path | None:
        """Get the `map_stem` MSB path in the project `map/MapStudio` directory."""
        map_stem = map_stem or self.map_stem
        if not self.str_project_directory or map_stem in {"", "0"}:
            return None
        return self.get_project_path(self.get_relative_msb_path(map_stem))

    def get_project_or_game_file_path(self, *parts: str | Path, dcx_type: DCXType = None) -> Path | None:
        """Try to get file path relative to project directory first, then fall back to the same path relative to the
        game directory if the file does not exist in the project directory.

        Raises a `FileNotFoundError` if the path cannot be found in EITHER directory.

        If `dcx_type` is given (including `Null`), the path will be processed by that DCX type. Otherwise, the known
        game specific/default DCX type for the file type will be used.
        """
        if self.str_project_directory:
            project_path = self.get_project_path(*parts, dcx_type=dcx_type)
            if project_path.is_file():
                return project_path
        game_path = self.get_game_path(*parts, dcx_type=dcx_type)
        if game_path and game_path.is_file():
            return game_path
        raise FileNotFoundError(f"File not found in project or game directory: {parts}")

    @property
    def can_auto_export(self) -> bool:
        """Checks if `project_directory` is set and/or `game_directory` is set and `also_export_to_game`
        is enabled, in which case auto-export operators will poll `True`."""
        if self.str_project_directory:
            return True
        if self.str_game_directory and self.also_export_to_game:
            return True
        return False

    def get_relative_msb_path(self, map_stem="") -> Path | None:
        """Get relative MSB path of given `map_stem` (or selected by default) for selected game."""
        map_stem = map_stem or self.map_stem
        if map_stem in {"", "0"}:
            return None
        return self.game.process_dcx_path(
            Path(self.game.default_file_paths["MapStudioDirectory"], f"{map_stem}.msb")
        )

    def export_file(
        self, operator: LoggingOperator, file: BaseBinaryFile, relative_path: Path, class_name=""
    ) -> set[str]:
        """Write `file` to `relative_path` in project directory (if given) and optionally also to game directory if
        `also_export_to_game` is enabled.

        `class_name` is used for logging and will be automatically detected from `file` if not given.
        """
        if relative_path.is_absolute():
            # Indicates a mistake in an operator.
            raise ValueError(f"Relative path for export must be relative to game root, not absolute: {relative_path}")
        try:
            self._export_file(operator, file, relative_path, class_name)
        except Exception as e:
            traceback.print_exc()
            operator.report({"ERROR"}, f"Failed to export {class_name} file: {e}")
            return {"CANCELLED"}
        return {"FINISHED"}

    def _export_file(self, operator: LoggingOperator, file: BaseBinaryFile, relative_path: Path, class_name=""):
        if not class_name:
            class_name = file.cls_name

        if self.project_directory:
            project_path = self.get_project_path(relative_path)
            project_path.parent.mkdir(parents=True, exist_ok=True)
            written = file.write(project_path)
            operator.info(f"Exported {class_name} to: {written}")
            if self.game_directory and self.also_export_to_game:
                # Copy to game directory.
                game_path = self.get_game_path(relative_path)
                if game_path.is_file():
                    create_bak(game_path)  # we may be about to replace it
                    operator.info(f"Created backup file in game directory: {game_path}")
                else:
                    game_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(project_path, game_path)
                operator.info(f"Copied exported {class_name} to game directory: {game_path}")
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
        try:
            self._export_file_data(operator, data, relative_path, class_name)
        except Exception as e:
            traceback.print_exc()
            operator.report({"ERROR"}, f"Failed to export {class_name} file: {e}")
            return {"CANCELLED"}
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

    def prepare_project_file(
        self, relative_path: Path, overwrite_existing=False, must_exist=False, dcx_type: DCXType = None
    ) -> bool:
        """Copy file from game directory to project directory, if both are set.

        Useful for creating initial Binders in project directory that are only being partially modified with new
        exported entries.

        Does nothing if project directory is not set, in which case you are either exporting to the game directory only
        or will likely hit an exception later on due.

        If `overwrite_existing` is `False` (default), the file will not be copied if it already exists in the project
        directory. If `must_exist` is `True`, the file must already exist in the project directory or successfully be
        copied from the game directory (assuming the project directory is set).

        Never creates a `.bak` backup file.
        """
        game_path = self.get_game_path(relative_path, dcx_type=dcx_type)
        project_path = self.get_project_path(relative_path, dcx_type=dcx_type)
        if not project_path:
            return False  # no project directory
        if not game_path or not game_path.is_file():
            if must_exist and not project_path.is_file():
                raise FileNotFoundError(f"File does not exist in game or project directory: {relative_path}")
            return False  # nothing to copy (may or may not already exist in project)
        if project_path and project_path.is_file() and not overwrite_existing:
            return False  # already exists
        project_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(game_path, project_path)
        return True

    def get_game_msb_class(self) -> type[MSB_TYPING]:
        """Get the `MSB` class associated with the selected game."""
        try:
            return self.game.from_game_submodule_import("maps.msb", "MSB")
        except ImportError:
            # TODO: Specific exception type?
            raise ValueError(f"Game {self.game} does not have an MSB class in Soulstruct.")

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

    def get_mtdbnd(self) -> MTDBND | None:
        """Load `MTDBND` from custom path, standard location in game directory, or bundled Soulstruct file."""

        try:
            mtdbnd_class = self.game.from_game_submodule_import("models.mtd", "MTDBND")
        except ImportError:
            mtdbnd_class = MTDBND

        mtdbnd_path = self.mtdbnd_path

        if not mtdbnd_path:
            # Try to find MTDBND in project or game directory.
            for label, directory in (("project", self.project_directory), ("game", self.game_directory)):
                if not directory:
                    continue
                for mtdbnd_name in ("mtd.mtdbnd", "allmaterialbnd.mtdbnd"):
                    try_mtdbnd_path = self.game.process_dcx_path(directory / f"mtd/{mtdbnd_name}")
                    if try_mtdbnd_path.is_file():
                        mtdbnd_path = try_mtdbnd_path
                        print(f"Found MTDBND in {label} directory: {mtdbnd_path}")
                        break
                if mtdbnd_path:  # found
                    break

        if mtdbnd_path.is_file():
            return mtdbnd_class.from_path(mtdbnd_path)

        from_bundled = getattr(mtdbnd_class, "from_bundled", None)
        if from_bundled:
            print(f"Loading bundled MTDBND for game {self.game.name}...")
            return from_bundled()
        return None

    def get_matbinbnd(self) -> MATBINBND_TYPING | None:
        """Load `MATBINBND` from custom path, standard location in game directory, or bundled Soulstruct file."""

        try:
            matbinbnd_class = self.game.from_game_submodule_import("models.matbin", "MATBINBND")
        except ImportError:
            # No generic support.
            return None

        matbinbnd_path = self.matbinbnd_path

        if not matbinbnd_path:
            # Try to find MATABINBND in project or game directory.
            for label, directory in (("project", self.project_directory), ("game", self.game_directory)):
                if not directory:
                    continue
                try_matbinbnd_path = self.game.process_dcx_path(directory / f"material/allmaterial.matbinbnd")
                if try_matbinbnd_path.is_file():
                    matbinbnd_path = try_matbinbnd_path
                    print(f"Found MATBINBND in {label} directory: {matbinbnd_path}")
                    break

        if matbinbnd_path.is_file():
            return matbinbnd_class.from_path(matbinbnd_path)

        from_bundled = getattr(matbinbnd_class, "from_bundled", None)
        if from_bundled:
            print(f"Loading bundled MATBINBND for game {self.game.name}...")
            return from_bundled()
        return None

    def load_settings(self):
        """Read settings from JSON file and set them in the scene."""
        try:
            json_settings = read_json(_SETTINGS_PATH)
        except FileNotFoundError:
            return  # do nothing
        self.game_enum = json_settings.get("game_enum", DARK_SOULS_DSR.variable_name)
        self.str_game_directory = json_settings.get("str_game_directory", "")
        self.str_project_directory = json_settings.get("str_project_directory", "")
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
        self.import_bak_file = json_settings.get("import_bak_file", False)
        self.detect_map_from_parent = json_settings.get("detect_map_from_parent", True)

    def save_settings(self):
        """Write settings from scene to JSON file."""
        current_settings = {
            key.lstrip("_"): getattr(self, key)
            for key in (
                "game_enum",
                "str_game_directory",
                "str_project_directory",
                "also_export_to_game",
                "map_stem",
                "str_mtdbnd_path",
                "str_matbinbnd_path",
                "str_png_cache_directory",
                "read_cached_pngs",
                "write_cached_pngs",
                "import_bak_file",
                "detect_map_from_parent",
            )
        }
        write_json(_SETTINGS_PATH, current_settings, indent=4)
        # print(f"Saved settings to {_SETTINGS_PATH}")
