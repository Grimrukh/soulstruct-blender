from __future__ import annotations

__all__ = ["get_cached_file"]

import typing as tp
from pathlib import Path

from soulstruct.utilities.binary import get_blake2b_hash

if tp.TYPE_CHECKING:
    from soulstruct.base.base_binary_file import BASE_BINARY_FILE_T


# Maps file paths to `(BaseBinaryFile, blake2b_hash)` tuples for caching. Useful for inspecting, say, MSB files
# repeatedly without modifying them.
_CACHED_FILES = {}


def get_cached_file(file_path: Path | str, file_type: tp.Type[BASE_BINARY_FILE_T]) -> BASE_BINARY_FILE_T:
    """Load a `BaseBinaryFile` from disk and cache it in a global dictionary.

    NOTE: Obviously, these cached `BaseBinaryFile` instances should be read-only, generally speaking, unless they are
     immediately written back to disk when modified!
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
