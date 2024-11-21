from __future__ import annotations

__all__ = [
    "GameStructure",
]

import typing as tp
from pathlib import Path

from soulstruct.dcx import DCXType
from soulstruct.games import *

if tp.TYPE_CHECKING:
    from .properties import SoulstructSettings


class GameStructure:
    """Wraps the root folder of a game-like file structure and provides utility methods for reading/writing files.

    Accessed as `SoulstructSettings.game_root` or `SoulstructSettings.project_root`.
    """

    settings: SoulstructSettings
    root: Path

    def __init__(self, settings: SoulstructSettings, root: Path | str):
        self.settings = settings
        self.root = Path(root).resolve()

    @property
    def game(self) -> Game:
        return self.settings.game

    @property
    def map_stem(self) -> str:
        return self.settings.map_stem

    def get_file_path(self, *parts: str | Path, if_exist=False, dcx_type: DCXType = None) -> Path | None:
        """Get path of arbitrary file relative to this root. Does NOT check if the file actually exists.

        At least one part must be given, as this is not permitted to return directories.

        If `dcx_type` is given (including `Null`), the path will be processed by that DCX type. Otherwise, the known
        game specific/default DCX type for the file type will be used.

        Will add `.bak` suffix to path if `import_bak_file` is enabled.
        """
        if not parts:
            raise ValueError("Must provide at least one part to `get_file_path()`.")
        file_path = self._process_file_dcx_path(Path(self.root, *parts), dcx_type)
        if if_exist and not file_path.is_file():
            return None
        return file_path

    def get_dir_path(self, *parts: str | Path, if_exist=False) -> Path | None:
        """Get path of arbitrary directory relative to this root. Does NOT check if the directory actually exists.

        If no parts are given, `root` will be returned.
        """
        dir_path = Path(self.root, *parts)
        if if_exist and not dir_path.is_dir():
            return None
        return dir_path

    def get_map_file_path(
        self, *parts: Path | str, if_exist=False, dcx_type: DCXType = None, map_stem: str = None
    ) -> Path | None:
        """Get the `map/{map_stem}` path, and optionally further, in the game directory.

        At least one part must be given, as this is not permitted to return directories.

        If `dcx_type` is given (including `Null`), the path will be processed by that DCX type. Otherwise, the known
        game specific/default DCX type for the file type will be used.
        """
        if not parts:
            raise ValueError("Must provide at least one file path part to `get_map_file_path()`.")

        map_stem = map_stem or self.map_stem
        if not map_stem:
            return None

        if self.settings.is_game(ELDEN_RING):
            # Area subfolders in 'map'.
            relative_file_path = Path(f"map/{map_stem[:3]}/{map_stem}", *parts)
        else:
            relative_file_path = Path(f"map/{map_stem}", *parts)

        true_map_stem = self.settings.process_file_map_stem_version(map_stem, relative_file_path.name)
        if true_map_stem != map_stem:
            # Replace all occurrences of `map stem[1:]` in relative file path.
            # We do this to catch 'nAA_BB_CC_DD', 'hAA_BB_CC_DD', etc.
            relative_file_path = Path(str(relative_file_path).replace(map_stem[1:], true_map_stem[1:]))

        print(f"File path: {relative_file_path}")

        file_path = Path(self.root, relative_file_path)
        file_path = self._process_file_dcx_path(file_path, dcx_type)
        if if_exist and not file_path.is_file():
            return None
        return file_path

    def get_map_dir_path(self, if_exist=False, map_stem: str = None) -> Path | None:
        """Get the `map/{map_stem}` path, and optionally further, in the game directory.

        If no parts are given, `{root}/map/{map_stem}` path will be returned.
        """
        map_stem = map_stem or self.map_stem
        if not map_stem:
            return None

        # No smart map version handling without any file.

        if self.settings.is_game(ELDEN_RING):
            # Area subfolders in 'map'.
            dir_path = Path(self.root, f"map/{map_stem[:3]}/{map_stem}")
        else:
            dir_path = Path(self.root, f"map/{map_stem}")

        if if_exist and not dir_path.is_dir():
            return None
        return dir_path

    def get_msb_path(self, if_exist=False, map_stem: str = None) -> Path | None:
        """Get the `map_stem` MSB path in the game `map/MapStudio` directory."""
        relative_msb_path = self.settings.get_relative_msb_path(map_stem)  # handles smart versioning
        if not relative_msb_path:
            return None
        return self.get_file_path(relative_msb_path, if_exist=if_exist)

    def _process_file_dcx_path(self, path: Path, dcx_type: DCXType | None) -> Path:
        """Process path with given `dcx_type`, or default game DCX type for file suffix if `dcx_type` is `None`."""
        path = dcx_type.process_path(path) if dcx_type is not None else self.game.process_dcx_path(path)
        if self.settings.import_bak_file:  # add extra '.bak' suffix
            return path.with_suffix(path.suffix + ".bak")
        return path
