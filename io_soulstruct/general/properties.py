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
from soulstruct.base.models.matbin import MATBINBND
from soulstruct.base.models.mtd import MTDBND
from soulstruct.dcx import DCXType
from soulstruct.games import *
from soulstruct.utilities.files import read_json, write_json, create_bak
from io_soulstruct.exceptions import *
from io_soulstruct.utilities import *
from .game_config import GAME_CONFIG, GameConfig
from .game_structure import GameStructure
from .enums import BlenderImageFormat

if tp.TYPE_CHECKING:
    from soulstruct.base.models.shaders import MatDef
    from io_soulstruct.type_checking import MSB_TYPING
    from io_soulstruct.utilities import LoggingOperator

_SETTINGS_PATH = Path(__file__).parent.parent / "SoulstructSettings.json"


# Global holder for games that front-end users can currently select (or have auto-detected) for the `game` enum.
SUPPORTED_GAMES = [
    DEMONS_SOULS,
    DARK_SOULS_PTDE,
    DARK_SOULS_DSR,
    BLOODBORNE,
    ELDEN_RING,
]


class SoulstructSettings(bpy.types.PropertyGroup):
    """Global settings for the Soulstruct Blender plugin."""

    # region True Blender Properties

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

    # Directories are set and saved for each game, so you can switch between them without having to set this again.
    # The prefixes to these directories are identical to the `Game.submodule_name` attribute of that game and are
    # retrieved dynamically.

    # region Game/Project Directories
    demonssouls_game_root_str: bpy.props.StringProperty(
        name="DeS Game Root",
        description="Root (containing BIN) of game directory to import files from when they are missing from the "
                    "project directory, and optionally export to if 'Also Export to Game' is enabled. DeS files should "
                    "already be unpacked",
        default="",
        subtype="DIR_PATH",
    )

    demonssouls_project_root_str: bpy.props.StringProperty(
        name="DS1:PTDE Project Root",
        description="Project root directory with game-like structure to export to. Files for import and Binders needed "
                    "for exporting new entries will also be sourced here first if they exist",
        default="",
        subtype="DIR_PATH",
    )

    darksouls1ptde_game_root_str: bpy.props.StringProperty(
        name="DS1:PTDE Game Root",
        description="Root (containing EXE) of game directory to import files from when they are missing from the "
                    "project directory, and optionally export to if 'Also Export to Game' is enabled. Files must be "
                    "unpacked with UDSFM",
        default="",
        subtype="DIR_PATH",
    )

    darksouls1ptde_project_root_str: bpy.props.StringProperty(
        name="DS1:PTDE Project Root",
        description="Project root directory with game-like structure to export to. Files for import and Binders needed "
                    "for exporting new entries will also be sourced here first if they exist",
        default="",
        subtype="DIR_PATH",
    )

    darksouls1r_game_root_str: bpy.props.StringProperty(
        name="DS1R Game Root",
        description="Root (containing EXE) of game directory to import files from when they are missing from the "
                    "project directory, and optionally export to if 'Also Export to Game' is enabled. DS1R files "
                    "should already be unpacked",
        default="",
        subtype="DIR_PATH",
    )

    darksouls1r_project_root_str: bpy.props.StringProperty(
        name="DS1R Project Root",
        description="Project root directory with game-like structure to export to. Files for import and Binders needed "
                    "for exporting new entries will also be sourced here first if they exist",
        default="",
        subtype="DIR_PATH",
    )

    bloodborne_game_root_str: bpy.props.StringProperty(
        name="Bloodborne Game Root",
        description="Root (containing BIN) of game directory to import files from when they are missing from the "
                    "project directory, and optionally export to if 'Also Export to Game' is enabled. BB files "
                    "should already be unpacked",
        default="",
        subtype="DIR_PATH",
    )

    bloodborne_project_root_str: bpy.props.StringProperty(
        name="Bloodborne Project Root",
        description="Project root directory with game-like structure to export to. Files for import and Binders needed "
                    "for exporting new entries will also be sourced here first if they exist",
        default="",
        subtype="DIR_PATH",
    )

    eldenring_game_root_str: bpy.props.StringProperty(
        name="Elden Ring Game Root",
        description="Root (containing EXE) of game directory to import files from when they are missing from the "
                    "project directory, and optionally export to if 'Also Export to Game' is enabled. File must be "
                    "unpacked with UXM",
        default="",
        subtype="DIR_PATH",
    )

    eldenring_project_root_str: bpy.props.StringProperty(
        name="ER Project Directory",
        description="Project root directory with game-like structure to export to. Files for import and Binders needed "
                    "for exporting new entries will also be sourced here first if they exist",
        default="",
        subtype="DIR_PATH",
    )
    # endregion

    soulstruct_project_root_str: bpy.props.StringProperty(
        name="Soulstruct Project Root",
        description="Optional root directory of a 'Soulstruct GUI' project with MSB JSON files, EVS event scripts, "
                    "etc., which MSB JSONs can be automatically exported to in sync with MSB files",
        default="",
        subtype="DIR_PATH",
    )

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

    er_map_filter_mode: bpy.props.EnumProperty(
        name="Elden Ring Map Filter",
        description="Filter mode for Map Stem dropdown. Only used by Elden Ring",
        items=[
            ("ALL_DUNGEONS", "All Dungeons Only (m10-m59)", "Show only dungeons (with DLC"),
            ("LEGACY_DUNGEONS", "Legacy Dungeons Only (m10-m29)", "Show only legacy dungeons (with DLC)"),
            ("GENERIC_DUNGEONS", "Generic Dungeons Only (m30-m59)", "Show only generic dungeons (with DLC)"),

            ("OVERWORLD_SMALL", "Overworld (Small) Only", "Show only overworld small tiles"),
            ("OVERWORLD_MEDIUM", "Overworld (Medium) Only", "Show only overworld medium tiles"),
            ("OVERWORLD_LARGE", "Overworld (Large) Only", "Show only overworld large tiles"),
            ("OVERWORLD_SMALL_V1", "Overworld (Small V1) Only", "Show only small tiles (version 1)"),
            ("OVERWORLD_MEDIUM_V1", "Overworld (Medium V1) Only", "Show only medium tiles (version 1)"),
            ("OVERWORLD_LARGE_V1", "Overworld (Large V1) Only", "Show only large tiles (version 1)"),

            ("DLC_OVERWORLD_SMALL", "DLC Overworld (Small) Only", "Show only overworld small tiles"),
            ("DLC_OVERWORLD_MEDIUM", "DLC Overworld (Medium) Only", "Show only overworld medium tiles"),
            ("DLC_OVERWORLD_LARGE", "DLC Overworld (Large) Only", "Show only overworld large tiles"),
            ("DLC_OVERWORLD_SMALL_V1", "DLC Overworld (Small) Only", "Show only overworld small tiles (version 1"),
            ("DLC_OVERWORLD_MEDIUM_V1", "DLC Overworld (Medium) Only", "Show only overworld medium tiles (version 1"),
            ("DLC_OVERWORLD_LARGE_V1", "DLC Overworld (Large) Only", "Show only overworld large tiles (version 1"),
        ],
    )

    include_empty_map_tiles: bpy.props.BoolProperty(
        name="Include Empty Map Tiles",
        description="Include Elden Ring overworld small map tiles with compressed MSB size < 700 bytes",
        default=False,
    )

    map_stem: bpy.props.StringProperty(
        name="Map Stem",
        description="Subdirectory of game/project 'map' folder to use when importing or exporting map assets",
        default="",
    )

    str_mtdbnd_path: bpy.props.StringProperty(
        name="MTDBND Path",
        description="Path of custom MTDBND file for detecting material setups. "
                    "Defaults to an automatic known location in selected project (preferred) or game directory",
        default="",
        subtype="FILE_PATH",
    )

    str_matbinbnd_path: bpy.props.StringProperty(
        name="MATBINBND Path",
        description="Path of custom MATBINBND file for detecting material setups in Elden Ring only. "
                    "Defaults to an automatic known location in selected project (preferred) or game directory. "
                    "If '_dlc01' and '_dlc02' variants of path name are found, they will also be loaded",
        default="",
        subtype="FILE_PATH",
    )

    str_image_cache_directory: bpy.props.StringProperty(
        name="Image Cache Directory",
        description="Path of directory to read/write cached image textures (from game DDS textures)",
        default="",
        subtype="DIR_PATH",
    )

    image_cache_format: bpy.props.EnumProperty(
        name="Image Cache Format",
        description="Format of cached image textures. Both lossless; PNG files take up less space but load slower",
        items=[
            ("TARGA", "TGA", "TGA format (TARGA)"),
            ("PNG", "PNG", "PNG format"),
        ],
        default="TARGA",
    )

    @property
    def bl_image_format(self):
        return BlenderImageFormat(self.image_cache_format)

    read_cached_images: bpy.props.BoolProperty(
        name="Read Cached Images",
        description="Read cached images of the given format with matching stems from image cache directory if given, "
                    "rather than finding and converting DDS textures of imported FLVERs",
        default=True,
    )

    write_cached_images: bpy.props.BoolProperty(
        name="Write Cached Images",
        description="Write cached images of the given format of imported FLVER textures (converted from DDS files) to "
                    "image cache directory if given, so they can be loaded more quickly in the future or modified by "
                    "the user without DDS headaches",
        default=True,
    )

    pack_image_data: bpy.props.BoolProperty(
        name="Pack Image Data",
        description="Pack Blender Image texture data into Blend file, rather than simply linking to the cached "
                    "image file on disk (if it exists and is loaded). Uncached DDS texture data will always be packed",
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

    # region Wrapper Properties

    @property
    def game(self) -> Game | None:
        return get_game(self.game_enum) if self.game_enum else None

    @property
    def game_variable_name(self):
        game = self.game
        return game.variable_name if game else ""

    @property
    def game_root_path(self) -> Path | None:
        game_submodule_name = self.game.submodule_name
        prop_name = f"{game_submodule_name}_game_root_str"
        game_root_str = getattr(self, prop_name, "")
        return Path(game_root_str) if game_root_str else None

    @property
    def project_root_path(self) -> Path | None:
        game_submodule_name = self.game.submodule_name
        prop_name = f"{game_submodule_name}_project_root_str"
        project_root_str = getattr(self, prop_name, "")
        return Path(project_root_str) if project_root_str else None

    @property
    def game_root(self) -> GameStructure | None:
        return GameStructure(self, self.game_root_path) if self.game_root_path else None

    @property
    def project_root(self) -> GameStructure | None:
        return GameStructure(self, self.project_root_path) if self.project_root_path else None

    @property
    def soulstruct_project_root_path(self) -> Path | None:
        return Path(self.soulstruct_project_root_str) if self.soulstruct_project_root_str else None

    @property
    def mtdbnd_path(self) -> Path | None:
        return Path(self.str_mtdbnd_path) if self.str_mtdbnd_path else None

    @property
    def matbinbnd_path(self) -> Path | None:
        return Path(self.str_matbinbnd_path) if self.str_matbinbnd_path else None

    @property
    def image_cache_directory(self) -> Path | None:
        return Path(self.str_image_cache_directory) if self.str_image_cache_directory else None

    # endregion

    # region Constructors

    @staticmethod
    def from_context(context: bpy.types.Context = None) -> SoulstructSettings:
        if context is None:
            context = bpy.context
        return context.scene.soulstruct_settings

    # endregion

    # region Getter Methods

    def is_game(self, *name_or_game: str | Game) -> bool:
        """Check if any `name_or_game` is the selected `Game`."""
        for game in name_or_game:
            game = get_game(game)
            if game is self.game:
                return True
        return False

    def is_game_ds1(self) -> bool:
        """Checks if current game is either version of Dark Souls 1."""
        return self.is_game(DARK_SOULS_PTDE, DARK_SOULS_DSR)

    @property
    def game_config(self) -> GameConfig:
        return GAME_CONFIG[self.game]

    def get_game_split_mesh_kwargs(self) -> dict[str, int | bool]:
        """TODO: Need to check/handle all games correctly here."""
        if self.is_game_ds1():
            return dict(
                use_submesh_bone_indices=True,
                max_bones_per_submesh=38,
                max_submesh_vertex_count=65535,  # TODO: not sure if 32-bit vertex indices are possible in DS1
            )
        elif self.is_game("DEMONS_SOULS"):
            return dict(
                use_submesh_bone_indices=True,
                max_bones_per_submesh=28,  # hard-coded count for `FLVER0` submeshes
                max_submesh_vertex_count=65535,  # faces MUST use 16-bit vertex indices
            )

        return dict(
            use_submesh_bone_indices=False,
            max_submesh_vertex_count=4294967295,  # faces use 32-bit vertex indices
        )

    def get_game_root_prop_name(self):
        """Get the name of the game root property for the current game."""
        return f"{self.game.submodule_name}_game_root_str"

    def get_project_root_prop_name(self):
        """Get the name of the project root property for the current game."""
        return f"{self.game.submodule_name}_project_root_str"

    def auto_set_game(self):
        """Determine `game` enum value from `game_directory`."""
        if not self.game_root_path:
            return
        for game in SUPPORTED_GAMES:
            executable_path = Path(self.game_root_path, game.executable_name)
            if executable_path.is_file():
                self.game_enum = game.variable_name
                return

    @property
    def import_roots(self) -> tuple[GameStructure, GameStructure]:
        """Return game and project roots in order of preferred import."""
        if self.prefer_import_from_project:
            return self.project_root, self.game_root
        return self.game_root, self.project_root

    @staticmethod
    def get_first_existing_file_path(
        *parts: str | Path, roots: tp.Sequence[GameStructure], dcx_type: DCXType = None
    ) -> Path | None:
        """Check ordered `roots` for file path, returning first that exists."""
        for root in roots:
            if not root:
                continue
            path = root.get_file_path(*parts, if_exist=True, dcx_type=dcx_type)
            if path:
                return path
        return None

    @staticmethod
    def get_first_existing_dir_path(*parts: str | Path, roots: tp.Sequence[GameStructure]) -> Path | None:
        """Check ordered `roots` for file path, returning first that exists."""
        for root in roots:
            if not root:
                continue
            path = root.get_dir_path(*parts, if_exist=True)
            if path:
                return path
        return None

    @staticmethod
    def get_first_existing_map_file_path(
        *parts: str | Path, roots: tp.Sequence[GameStructure], dcx_type: DCXType = None, map_stem: str = None
    ) -> Path | None:
        """Check ordered `roots` for 'map' file path, returning first that exists."""
        for root in roots:
            if not root:
                continue
            path = root.get_map_file_path(*parts, if_exist=True, dcx_type=dcx_type, map_stem=map_stem)
            if path:
                return path
        return None

    @staticmethod
    def get_first_existing_map_dir_path(
        *parts: str | Path, roots: tp.Sequence[GameStructure], map_stem: str = None
    ) -> Path | None:
        """Check ordered `roots` for 'map' dir path, returning first that exists."""
        for root in roots:
            if not root:
                continue
            path = root.get_map_dir_path(*parts, if_exist=True, map_stem=map_stem)
            if path:
                return path
        return None

    @staticmethod
    def get_first_existing_msb_path(roots: tp.Sequence[GameStructure], map_stem: str = None) -> Path | None:
        """Check ordered `roots` for MSB file path, returning first that exists."""
        for root in roots:
            if not root:
                continue
            path = root.get_msb_path(if_exist=True, map_stem=map_stem)
            if path:
                return path
        return None

    def get_oldest_map_stem_version(self, map_stem: str = None):
        """Check if `smart_map_version_handling` is enabled and return the oldest version of the map stem if so."""
        if map_stem is None:
            map_stem = self.map_stem
        if not map_stem or not self.smart_map_version_handling or not self.game:
            return map_stem
        return GAME_CONFIG[self.game].new_to_old_map.get(map_stem, map_stem)

    def get_latest_map_stem_version(self, map_stem: str = None):
        """Check if `smart_map_version_handling` is enabled and return the latest version of the map stem if so."""
        if map_stem is None:
            map_stem = self.map_stem
        if not map_stem or not self.smart_map_version_handling or not self.game:
            return map_stem
        return GAME_CONFIG[self.game].old_to_new_map.get(map_stem, map_stem)

    def get_import_file_path(self, *parts: str | Path, dcx_type: DCXType = None) -> Path:
        """Try to get file path relative to project or game directory first, depending on `prefer_import_from_project`,
        then fall back to the same path relative to the other directory if the preferred file does not exist.

        Raises a `FileNotFoundError` if the path cannot be found in EITHER directory.

        If `dcx_type` is given (including `Null`), the path will be processed by that DCX type. Otherwise, the known
        game specific/default DCX type for the file type will be used.
        """
        path = self.get_first_existing_file_path(*parts, roots=self.import_roots, dcx_type=dcx_type)
        if not path:
            raise FileNotFoundError(f"File not found in project or game directory with parts: {parts}")
        return path

    def get_import_dir_path(self, *parts: str | Path) -> Path:
        """Try to get directory path relative to project or game directory first, depending on
        `prefer_import_from_project`, then fall back to the same path relative to the other directory if the preferred
        directory does not exist.

        Raises a `NotADirectoryError` if the path cannot be found in EITHER directory.
        """
        path = self.get_first_existing_dir_path(*parts, roots=self.import_roots)
        if not path:
            raise NotADirectoryError(f"Directory not found in project or game directory with parts: {parts}")
        return path

    def has_import_dir_path(self, *parts: str | Path) -> bool:
        """Check if import directory path exists."""
        try:
            self.get_import_dir_path(*parts)
            return True
        except NotADirectoryError:
            return False

    def get_import_map_file_path(self, *parts: str | Path, dcx_type: DCXType = None, map_stem: str = None) -> Path:
        """Get the 'map/{map_stem}' directory path, and optionally further, in the preferred directory.

        If `smart_map_version_handling` is enabled, this will redirect to the earliest or latest version of the map if
        the file is a known versioned type.
        """
        if not parts:
            raise ValueError("Must provide at least one part to get a map file path.")
        path = self.get_first_existing_map_file_path(
            *parts, roots=self.import_roots, dcx_type=dcx_type, map_stem=map_stem
        )
        if not path:
            # `parts` must be given.
            raise FileNotFoundError(f"Map file not found in project or game directory with parts: {parts}")
        return path

    def get_import_map_dir_path(self, *parts: str | Path, map_stem: str = None) -> Path:
        """Get the 'map/{map_stem}' directory path, and optionally further, in the preferred directory.

        Directory must exist, or a `NotADirectoryError` will be raised.
        """
        path = self.get_first_existing_map_dir_path(*parts, roots=self.import_roots, map_stem=map_stem)
        if not path:
            if parts:
                raise NotADirectoryError(f"Map subdirectory not found in project or game directory with parts: {parts}")
            raise NotADirectoryError(f"Map directory not found in project or game directory.")
        return path

    def get_import_msb_path(self, map_stem: str = None) -> Path:
        """Get the `map_stem` MSB path in the preferred `map/MapStudio` directory.

        MSB file must exist, or a `FileNotFoundError` will be raised.
        """
        path = self.get_first_existing_msb_path(roots=self.import_roots, map_stem=map_stem)
        if not path:
            raise FileNotFoundError(f"MSB file for map '{map_stem}' not found in project or game directory.")
        return path

    def get_cached_image_path(self, image_stem: str):
        """Get the path to a cached image file in the image cache directory."""
        if not self.str_image_cache_directory:
            raise NotADirectoryError("No image cache directory set.")
        return self.image_cache_directory / f"{image_stem}{self.bl_image_format.get_suffix()}"

    # endregion

    # region Export Methods

    @property
    def can_auto_export(self) -> bool:
        """Checks if `project_directory` is set and/or `game_directory` is set and `also_export_to_game`
        is enabled, in which case auto-export operators will poll `True`."""
        if self.project_root_path:
            return True  # can definitely export to project
        if self.game_root_path and self.also_export_to_game:
            return True  # can export to game, even if project not set
        return False

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
            operator.report({"ERROR"}, f"Failed to export {class_name if class_name else '<unknown>'} file: {e}")
            return {"CANCELLED"}

        return {"FINISHED"}

    def _export_file(self, operator: LoggingOperator, file: BaseBinaryFile, relative_path: Path, class_name=""):
        if not class_name:
            class_name = file.cls_name

        project_root = self.project_root
        game_root = self.game_root

        if project_root:
            project_path = project_root.get_file_path(relative_path)
            project_path.parent.mkdir(parents=True, exist_ok=True)
            written = file.write(project_path)  # will create '.bak' if appropriate
            operator.info(f"Exported {class_name} to: {written}")
            if game_root and self.also_export_to_game:
                # Copy all written files to game directory, rather than re-exporting.
                for written_path in written:
                    written_relative_path = written_path.relative_to(self.project_root_path)
                    game_path = game_root.get_file_path(written_relative_path)
                    if game_path.is_file():
                        create_bak(game_path)  # we may be about to replace it
                        operator.info(f"Created backup file in game directory: {game_path}")
                    else:
                        game_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(written_path, game_path)
                    operator.info(f"Copied exported {class_name} file to game directory: {game_path}")
        elif game_root and self.also_export_to_game:
            game_path = game_root.get_file_path(relative_path)
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
        """Version of `export_file` that takes raw `bytes` data instead of a `BaseBinaryFile` to export.

        `class_name` must be given for logging in this case because it cannot be automatically detected.
        """
        try:
            self._export_file_data(operator, data, relative_path, class_name)
        except Exception as e:
            traceback.print_exc()
            operator.report({"ERROR"}, f"Failed to export {class_name} file: {e}")
            return {"CANCELLED"}

        return {"FINISHED"}

    def _export_file_data(self, operator: LoggingOperator, data: bytes, relative_path: Path, class_name: str):

        project_root = self.project_root
        game_root = self.game_root

        if project_root:
            project_path = project_root.get_file_path(relative_path)
            if project_path.is_file():
                create_bak(project_path)
                operator.info(f"Created backup file in project directory: {project_path}")
            else:
                project_path.parent.mkdir(parents=True, exist_ok=True)
            project_path.write_bytes(data)
            operator.info(f"Exported {class_name} to: {project_path}")
            if game_root and self.also_export_to_game:
                # Copy to game directory.
                game_path = game_root.get_file_path(relative_path)
                if game_path.is_file():
                    create_bak(game_path)
                    operator.info(f"Created backup file in game directory: {game_path}")
                else:
                    game_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(project_path, game_path)
                operator.info(f"Copied exported {class_name} to game directory: {game_path}")
        elif game_root and self.also_export_to_game:
            game_path = game_root.get_file_path(relative_path)
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
        if relative_path.is_absolute():
            # Indicates a mistake in an operator.
            raise ValueError(f"Relative path for export must be relative to game root, not absolute: {relative_path}")
        try:
            self._export_text_file(operator, text, relative_path, encoding)
        except Exception as e:
            traceback.print_exc()
            operator.report({"ERROR"}, f"Failed to export text file: {e}")
            return {"CANCELLED"}

        return {"FINISHED"}

    def _export_text_file(self, operator: LoggingOperator, text: str, relative_path: Path, encoding: str):

        project_root = self.project_root
        game_root = self.game_root

        if project_root:
            project_path = project_root.get_file_path(relative_path, dcx_type=DCXType.Null)
            project_path.parent.mkdir(parents=True, exist_ok=True)
            if project_path.is_file():
                create_bak(project_path)
                operator.info(f"Created backup file in project directory: {project_path}")
            with project_path.open("w", encoding=encoding) as f:
                f.write(text)
            operator.info(f"Exported text file to: {project_path}")
            if game_root and self.also_export_to_game:
                # We still do a copy operation rather than a second write, so file metadata matches.
                game_path = game_root.get_file_path(relative_path, dcx_type=DCXType.Null)
                if game_path.is_file():
                    create_bak(game_path)  # we may be about to replace it
                    operator.info(f"Created backup file in game directory: {game_path}")
                else:
                    game_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(project_path, game_path)
                operator.info(f"Copied exported text file to game directory: {game_path}")
        elif game_root and self.also_export_to_game:
            game_path = game_root.get_file_path(relative_path, dcx_type=DCXType.Null)
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

        Returns the project file path.

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
        if overwrite_existing is None:
            overwrite_existing = not self.prefer_import_from_project

        if self.game_root_path:
            game_path = self.game_root.get_file_path(relative_path, dcx_type=dcx_type)
        else:
            game_path = None

        if self.project_root_path:
            project_path = self.project_root.get_file_path(relative_path, dcx_type=dcx_type)
        else:
            project_path = None

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

        return project_path

    # endregion

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

    # region Game Type Getters

    def resolve_dcx_type(self, dcx_type_name: str, class_name: str) -> DCXType:
        """Get DCX type associated with `class_name` for selected game.

        NOTE: Those should generally only be called for loose files or files inside uncompressed split BHD binders
        (usually TPFs). Files inside compressed BND binders never use DCX, as far as I'm aware.

        If `dcx_type_name` is not "AUTO", it is returned directly.
        """

        if dcx_type_name != "AUTO":
            # Manual DCX type given.
            return DCXType[dcx_type_name]
        return self.game.get_dcx_type(class_name)

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

    def get_mtdbnd(self, operator: LoggingOperator) -> MTDBND | None:
        """Load `MTDBND` from custom path, standard location in game directory, or bundled Soulstruct file."""
        if is_path_and_file(self.mtdbnd_path):
            return MTDBND.from_path(self.mtdbnd_path)

        # Try to find MTDBND in project or game directory. We know their names from the bundled versions in Soulstruct,
        # but only fall back to those actual bundled files if necessary.
        mtdbnd_names = [
            resource_path.name
            for resource_key, resource_path in self.game.bundled_resource_paths.items()
            if resource_key.endswith("MTDBND")
        ]

        if self.prefer_import_from_project:
            labelled_roots = (("project", self.project_root), ("game", self.game_root))
        else:
            labelled_roots = (("game", self.game_root), ("project", self.project_root))

        mtdbnd = None  # type: MTDBND | None
        for label, root in labelled_roots:
            if not root:
                continue
            for mtdbnd_name in mtdbnd_names:
                dir_mtdbnd_path = root.get_file_path(f"mtd/{mtdbnd_name}")
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
            labelled_roots = (("project", self.project_root), ("game", self.game_root))
        else:
            labelled_roots = (("game", self.game_root), ("project", self.project_root))

        matbinbnd = None  # type: MATBINBND | None
        for label, root in labelled_roots:
            if not root:
                continue
            for matbinbnd_name in matbinbnd_names:
                dir_matbinbnd_path = root.get_file_path(f"matbin/{matbinbnd_name}")
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

    # endregion

    # region Save/Load Settings

    def load_settings(self):
        """Read settings from a JSON file and set them to this group by scanning annotations."""
        try:
            json_settings = read_json(_SETTINGS_PATH)
        except FileNotFoundError:
            return  # do nothing

        # All JSON types are compatible (strings, ints, bools).
        for prop_name in self._get_bl_prop_names():
            json_value = json_settings.get(prop_name, None)
            if json_value is None:
                continue  # not saved
            setattr(self, prop_name, json_value)

    def save_settings(self):
        """Write these settings to a JSON file by scanning annotations."""
        current_settings = {
            prop_name: getattr(self, prop_name)
            for prop_name in self._get_bl_prop_names()
        }
        write_json(_SETTINGS_PATH, current_settings, indent=4)

    @classmethod
    def _get_bl_prop_names(cls) -> list[str]:
        prop_names = []
        for prop_name, prop_type in cls.__annotations__.items():
            if isinstance(prop_type, str):
                if "Property" in prop_type:
                    prop_names.append(prop_name)
            elif "Property" in prop_type.__name__:
                prop_names.append(prop_name)
        return prop_names

    # endregion

    # region Internal Methods

    def process_file_map_stem_version(self, map_stem: str, *parts: str | Path) -> str:
        """If `smart_map_version_handling` is enabled, this will redirect to the version of the given map stem
        (DD part) that is appropriate for the file type given in `parts` (if given)."""
        if not self.smart_map_version_handling or not parts:
            # Nothing to process.
            return map_stem
        return GAME_CONFIG[self.game].process_file_map_stem_version(map_stem, *parts)

    def get_relative_msb_path(self, map_stem: str = None) -> Path | None:
        """Get relative MSB path of given `map_stem` (or selected by default) for selected game.

        If `smart_map_version_handling` is enabled, this will redirect to the latest version of the MSB.
        """
        if map_stem is None:
            map_stem = self.map_stem
        if not map_stem:
            return None
        map_stem = self.process_file_map_stem_version(map_stem, f"{map_stem}.msb")
        return self.game.process_dcx_path(
            Path(self.game.default_file_paths["MapStudioDirectory"], f"{map_stem}.msb")
        )

    # endregion
