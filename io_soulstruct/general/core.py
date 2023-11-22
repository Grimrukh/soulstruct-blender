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
    """Get list of map stems in game import directory."""
    settings = SoulstructSettings.from_context(context)
    game_import_directory = settings.game_import_directory
    global _MAP_STEM_ENUM_ITEMS

    if not game_import_directory:
        _MAP_STEM_ENUM_ITEMS = (None, [("0", "None", "None")])
        return _MAP_STEM_ENUM_ITEMS[1]

    map_dir_path = Path(game_import_directory, "map")
    if not map_dir_path.is_dir():
        _MAP_STEM_ENUM_ITEMS = (None, [("0", "None", "None")])
        return _MAP_STEM_ENUM_ITEMS[1]

    if _MAP_STEM_ENUM_ITEMS[0] == map_dir_path:
        return _MAP_STEM_ENUM_ITEMS[1]  # cached

    map_stem_names = []
    match settings.game:
        case None:
            pass  # no choices
        case {"name": ELDEN_RING.name}:
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
        return get_game(self.game_enum)

    str_game_import_directory: bpy.props.StringProperty(
        name="Import Directory",
        description="Root (containing EXE/BIN) of game directory to import from and optionally export to",
        default="",
    )

    @property
    def game_import_directory(self) -> Path | None:
        return Path(self.str_game_import_directory) if self.str_game_import_directory else None

    str_game_export_directory: bpy.props.StringProperty(
        name="Export Directory",
        description="Root game-like directory to export to",
        default="",
    )

    @property
    def game_export_directory(self) -> Path | None:
        return Path(self.str_game_export_directory) if self.str_game_export_directory else None

    also_export_to_import: bpy.props.BoolProperty(
        name="Also Export to Import Directory",
        description="Also export to the game import directory when exporting",
        default=False,
    )

    map_stem: bpy.props.EnumProperty(
        name="Map Stem",
        description="Directory in game 'map' folder to use when auto-importing or exporting map assets",
        items=_get_map_stem_items,
    )

    str_mtdbnd_path: bpy.props.StringProperty(
        name="MTDBND Path",
        description="Path of custom MTDBND file for detecting material setups. "
                    "Defaults to an automatic game-specific location in selected game directory",
        default="",
    )

    @property
    def mtdbnd_path(self) -> Path | None:
        return Path(self.str_mtdbnd_path) if self.str_mtdbnd_path else None

    str_matbinbnd_path: bpy.props.StringProperty(
        name="MATBINBND Path",
        description="Path of custom MATBINBND file for detecting material setups (Elden Ring only). "
                    "Defaults to an automatic game-specific location in selected game directory",
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
        description="Write cached PNGs of imported FLVER textures (converted from DDS files) to PNG cache if given",
        default=True,
    )

    import_bak_file: bpy.props.BoolProperty(
        name="Import BAK File",
        description="Import from '.bak' backup file when quick-importing from game directory (and fail if missing)",
        default=False,
    )

    detect_map_from_parent: bpy.props.BoolProperty(
        name="Detect Map from Parent",
        description="Detect map stem from Blender parent when quick-exporting game map assets",
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
        """Determine `game` enum value from `game_import_directory`."""
        if not self.str_game_import_directory:
            return
        for game in SUPPORTED_GAMES:
            executable_path = Path(self.str_game_import_directory, game.executable_name)
            if executable_path.is_file():
                self.game_enum = game.variable_name
                return

    def get_import_path(self, *parts: str | Path, dcx_type: DCXType.Null = None) -> Path | None:
        """Get path relative to game import directory.

        If `dcx_type` is given (including `Null`), the path will be processed by that DCX type. Otherwise, the known
        game specific/default DCX type will be used.

        Will add `.bak` suffix to path if `import_bak_file` is enabled.
        """
        if not self.game:
            return None
        import_path = Path(self.str_game_import_directory, *parts)
        if dcx_type is not None:
            import_path = dcx_type.process_path(import_path)
        if "." in import_path.name:
            import_path = self.game.process_dcx_path(import_path)
            if self.import_bak_file:  # add extra '.bak' suffix
                return import_path.with_suffix(import_path.suffix + ".bak")
        return import_path

    def get_import_map_path(self, *parts, dcx_type: DCXType.Null = None) -> Path | None:
        """Get the `map_stem` path in the game import 'map' directory.

        If `dcx_type` is given (including `Null`), the path will be processed by that DCX type. Otherwise, the known
        game specific/default DCX type will be used.
        """
        if not self.game or not self.str_game_import_directory or self.map_stem in {"", "0"}:
            return None
        import_path = Path(self.str_game_import_directory, f"map/{self.map_stem}", *parts)
        if "." in import_path.name:
            if dcx_type is not None:
                import_path = dcx_type.process_path(import_path)
            else:
                import_path = self.game.process_dcx_path(import_path)
            if self.import_bak_file:  # add extra '.bak' suffix
                return import_path.with_suffix(import_path.suffix + ".bak")
        return import_path

    def get_import_msb_path(self, map_stem="") -> Path | None:
        """Get the `map_stem` MSB path in its game import 'MapStudio' directory."""
        if not map_stem:
            map_stem = self.map_stem
        if not self.game or not self.str_game_import_directory or map_stem in {"", "0"}:
            return None
        msb_dcx_type = self.resolve_dcx_type("Auto", "MSB")
        relative_msb_path = Path(self.game.default_file_paths["MapStudioDirectory"], f"{map_stem}.msb")
        if self.import_bak_file:  # add extra '.bak' suffix
            relative_msb_path = relative_msb_path.with_suffix(relative_msb_path.suffix + ".bak")
        return msb_dcx_type.process_path(Path(self.str_game_import_directory, relative_msb_path))

    def get_export_path(self, *parts: str | Path, dcx_type: DCXType.Null = None) -> Path | None:
        """Get path relative to game export directory.

        If `dcx_type` is given (including `Null`), the path will be processed by that DCX type. Otherwise, the known
        game specific/default DCX type will be used.
        """
        if not self.game:
            return None
        export_path = Path(self.str_game_export_directory, *parts)
        if "." in export_path.name:
            if dcx_type is not None:
                return dcx_type.process_path(export_path)
            return self.game.process_dcx_path(export_path)
        return export_path

    def get_export_map_path(self, *parts, dcx_type: DCXType.Null = None) -> Path | None:
        """Get the `map_stem` path in the game export 'map' directory.

        If `dcx_type` is given (including `Null`), the path will be processed by that DCX type. Otherwise, the known
        game specific/default DCX type will be used.
        """
        if not self.str_game_export_directory or self.map_stem in {"", "0"}:
            return None
        export_path = Path(self.str_game_export_directory, f"map/{self.map_stem}", *parts)
        if "." in export_path.name:
            if dcx_type is not None:
                return dcx_type.process_path(export_path)
            return self.game.process_dcx_path(export_path)
        return export_path

    def get_export_msb_path(self) -> Path | None:
        """Get the `map_stem` MSB path in its game export 'MapStudio' directory."""
        if not self.str_game_export_directory or self.map_stem in {"", "0"}:
            return None
        msb_dcx_type = self.resolve_dcx_type("Auto", "MSB")
        relative_msb_path = Path(self.game.default_file_paths["MapStudioDirectory"], f"{self.map_stem}.msb")
        return msb_dcx_type.process_path(Path(self.str_game_export_directory, relative_msb_path))

    @property
    def can_export(self) -> bool:
        """Checks if `game_export_directory` is set and/or `game_import_directory` is set and `also_export_to_import`
        is enabled, in which case quick-export operators will poll `True`."""
        if self.str_game_export_directory:
            return True
        if self.str_game_import_directory and self.also_export_to_import:
            return True
        return False

    def export_file(
        self, operator: LoggingOperator, file: BaseBinaryFile, relative_path: Path, class_name=""
    ) -> set[str]:
        if relative_path.is_absolute():
            # Indicates a mistake in an operator.
            raise ValueError(f"Relative path for export must be relative to game directory: {relative_path}")
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

        if self.game_export_directory:
            export_path = self.get_export_path(relative_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            written = file.write(export_path)
            operator.info(f"Exported {class_name} to: {written}")
            if self.game_import_directory and self.also_export_to_import:
                # Copy to import directory.
                import_path = self.get_import_path(relative_path)
                if import_path.is_file():
                    create_bak(import_path)  # we may be about to replace it
                    operator.info(f"Created backup file: {import_path}")
                else:
                    import_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(export_path, import_path)
                operator.info(f"Copied exported {class_name} to import directory: {import_path}")
        elif self.game_import_directory and self.also_export_to_import:
            import_path = self.get_import_path(relative_path)
            import_path.parent.mkdir(parents=True, exist_ok=True)
            written = file.write(import_path)
            operator.info(f"Exported {class_name} to import directory only: {written}")
        else:
            operator.warning(
                f"Cannot export {class_name} file. Game export directory is not set and game import directory is not "
                f"set (or writing to import directory is disabled)."
            )

    def export_file_data(
        self, operator: LoggingOperator, data: bytes, relative_path: Path, class_name: str
    ) -> set[str]:
        try:
            self._export_file_data(operator, data, relative_path, class_name)
        except Exception as e:
            traceback.print_exc()
            operator.report({"ERROR"}, f"Failed to export {class_name} file: {e}")
            return {"CANCELLED"}
        return {"FINISHED"}

    def _export_file_data(self, operator: LoggingOperator, data: bytes, relative_path: Path, class_name: str):
        if self.game_export_directory:
            export_path = self.get_export_path(relative_path)
            if export_path.is_file():
                create_bak(export_path)
                operator.info(f"Created backup file: {export_path}")
            else:
                export_path.parent.mkdir(parents=True, exist_ok=True)
            export_path.write_bytes(data)
            operator.info(f"Exported {class_name} to: {export_path}")
            if self.game_import_directory and self.also_export_to_import:
                # Copy to import directory.
                import_path = self.get_import_path(relative_path)
                if import_path.is_file():
                    create_bak(import_path)
                    operator.info(f"Created backup file: {import_path}")
                else:
                    import_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(export_path, import_path)
                operator.info(f"Copied exported {class_name} to import directory: {import_path}")
        elif self.game_import_directory and self.also_export_to_import:
            import_path = self.get_import_path(relative_path)
            if import_path.is_file():
                create_bak(import_path)
                operator.info(f"Created backup file: {import_path}")
            else:
                import_path.parent.mkdir(parents=True, exist_ok=True)
            import_path.write_bytes(data)
            operator.info(f"Exported {class_name} to import directory only: {import_path}")
        else:
            operator.warning(
                f"Cannot export {class_name} file. Game export directory is not set and game import directory is not "
                f"set (or writing to import directory is disabled)."
            )

    def copy_file_import_to_export(self, relative_path: Path, overwrite_existing=False, must_exist=False) -> bool:
        """Copy file from import directory to export directory, if both are set.

        If `overwrite_existing` is `False` (default), the file will not be copied if it already exists in the export
        directory. If `must_exist` is `True`, the file must already exist in the export directory or successfully be
        copied from the import directory.
        """
        import_path = self.get_import_path(relative_path)
        export_path = self.get_export_path(relative_path)
        if not export_path:
            raise ValueError(
                f"Export directory not set. Cannot copy file from import to export directory: {relative_path}"
            )
        if not import_path or not import_path.is_file():
            if must_exist and not export_path.is_file():
                raise FileNotFoundError(f"Cannot copy file from import to export directory: {import_path}")
            return False  # nothing to copy
        if export_path and export_path.is_file() and not overwrite_existing:
            return False  # already exists
        export_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(import_path, export_path)
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

        if not mtdbnd_path and self.game_import_directory:
            # Try to find MTDBND in game import directory.
            for mtdbnd_name in (
                "mtd.mtdbnd", "allmaterialbnd.mtdbnd"
            ):
                mtdbnd_path = self.game.process_dcx_path(self.game_import_directory / f"mtd/{mtdbnd_name}")
                if mtdbnd_path.is_file():
                    print(f"Found MTDBND in game directory: {mtdbnd_path}")
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

        if not matbinbnd_path and self.game_import_directory:
            # Try to find MATBINBND in game import directory.
            matbinbnd_path = self.game.process_dcx_path(self.game_import_directory / "material/allmaterial.matbinbnd")
            if matbinbnd_path.is_file():
                print(f"Found MATBINBND in game directory: {matbinbnd_path}")

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
        self.game_enum = json_settings.get("game", DARK_SOULS_DSR.variable_name)
        self.str_game_import_directory = json_settings.get("game_import_directory", "")
        self.str_game_export_directory = json_settings.get("game_export_directory", "")
        self.also_export_to_import = json_settings.get("also_export_to_import", False)
        map_stem = json_settings.get("map_stem", "0")
        if not map_stem:
            map_stem = "0"  # null enum value
        self.map_stem = map_stem
        self.str_mtdbnd_path = json_settings.get("mtdbnd_path", "")
        self.str_matbinbnd_path = json_settings.get("matbinbnd_path", "")
        self.str_png_cache_directory = json_settings.get("png_cache_directory", "")
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
                "str_game_import_directory",
                "str_game_export_directory",
                "also_export_to_import",
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
        print(f"Saved settings to {_SETTINGS_PATH}")
