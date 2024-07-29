from __future__ import annotations

__all__ = [
    "GameStructure",
]

import typing as tp
from functools import wraps
from pathlib import Path

from soulstruct.dcx import DCXType
from soulstruct.games import *

if tp.TYPE_CHECKING:
    from .properties import SoulstructSettings


def _auto_map_stem(func: tp.Callable) -> tp.Callable:
    """Decorator to automatically pass selected `map_stem` to decorated method as default."""

    @wraps(func)
    def wrapper(self: GameStructure, *args, map_stem="", **kwargs):
        map_stem = map_stem or self.map_stem
        return func(self, *args, map_stem=map_stem, **kwargs)

    return wrapper


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
        file_path = self.process_file_dcx_path(Path(self.root, *parts), dcx_type)
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

    @_auto_map_stem
    def get_map_file_path(self, *parts, if_exist=False, dcx_type: DCXType = None, map_stem="") -> Path | None:
        """Get the `map/{map_stem}` path, and optionally further, in the game directory.

        At least one part must be given, as this is not permitted to return directories.

        If `dcx_type` is given (including `Null`), the path will be processed by that DCX type. Otherwise, the known
        game specific/default DCX type for the file type will be used.
        """
        if not parts:
            raise ValueError("Must provide at least one part to `get_map_file_path()`.")
        if not map_stem:
            return None
        map_stem = self.settings.process_file_map_stem_version(map_stem)
        if self.settings.is_game(ELDEN_RING):
            # Area subfolders in 'map'.
            file_path = Path(self.root, f"map/{map_stem[:3]}/{map_stem}", *parts)
        else:
            file_path = Path(self.root, f"map/{map_stem}", *parts)
        file_path = self.process_file_dcx_path(file_path, dcx_type)
        if if_exist and not file_path.is_file():
            return None
        return file_path

    @_auto_map_stem
    def get_map_dir_path(self, *parts, if_exist=False, map_stem="") -> Path | None:
        """Get the `map/{map_stem}` path, and optionally further, in the game directory.

        If no parts are given, `{root}/map/{map_stem}` path will be returned.
        """
        if not map_stem:
            return None
        map_stem = self.settings.process_file_map_stem_version(map_stem, *parts)  # TODO: never changes anything?
        if self.settings.is_game(ELDEN_RING):
            # Area subfolders in 'map'.
            dir_path = Path(self.root, f"map/{map_stem[:3]}/{map_stem}", *parts)
        else:
            dir_path = Path(self.root, f"map/{map_stem}", *parts)
        if if_exist and not dir_path.is_dir():
            return None
        return dir_path

    @_auto_map_stem
    def get_msb_path(self, if_exist=False, map_stem="") -> Path | None:
        """Get the `map_stem` MSB path in the game `map/MapStudio` directory."""
        if not map_stem:
            return None
        return self.get_file_path(self.settings.get_relative_msb_path(map_stem), if_exist=if_exist)

    def process_file_dcx_path(self, path: Path, dcx_type: DCXType | None) -> Path:
        """Process path with given `dcx_type`, or default game DCX type for file suffix if `dcx_type` is `None`."""
        path = dcx_type.process_path(path) if dcx_type is not None else self.game.process_dcx_path(path)
        if self.settings.import_bak_file:  # add extra '.bak' suffix
            return path.with_suffix(path.suffix + ".bak")
        return path
