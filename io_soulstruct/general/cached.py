from __future__ import annotations

__all__ = ["get_cached_file", "get_cached_bxf"]

import typing as tp
from pathlib import Path

from soulstruct.containers import Binder
from soulstruct.utilities.binary import get_blake2b_hash

if tp.TYPE_CHECKING:
    from soulstruct.base.base_binary_file import BASE_BINARY_FILE_T


# Maps file paths to `(BaseBinaryFile, blake2b_hash)` tuples for caching. Useful for inspecting, say, MSB files
# repeatedly without modifying them.
_CACHED_FILES = {}


def get_cached_file(file_path: Path | str, file_type: type[BASE_BINARY_FILE_T]) -> BASE_BINARY_FILE_T:
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


def get_cached_bxf(bhd_path: Path | str) -> Binder:
    """Load a `BaseBinaryFile` from disk and cache it in a global dictionary.

    NOTE: Obviously, these cached `BaseBinaryFile` instances should be read-only, generally speaking, unless they are
     immediately written back to disk when modified!
    """
    bhd_path = Path(bhd_path)

    # Try to auto-detect BDT file next to `bhd_path`.
    name_parts = bhd_path.name.split(".")
    bdt_name = name_parts[0] + "." + ".".join(name_parts[1:]).replace("bhd", "bdt")
    if bdt_name == bhd_path.name:
        raise ValueError(f"Could not guess name of BDT file from BHD file: {bhd_path}")
    bdt_path = bhd_path.with_name(bdt_name)

    if not bhd_path.is_file() or not bdt_path.is_file():
        # Not loaded, even if cached.
        _CACHED_FILES.pop(bhd_path, None)
        _CACHED_FILES.pop(bdt_path, None)
        raise FileNotFoundError(f"Cannot find file '{bhd_path}' and/or file '{bdt_path}'.")

    # The hashing process reads the file anyway, so we may as well save the second read if it's actually needed.
    # Here, we hash both BHD and BDT files together, since they are always paired.
    bhd_data = bhd_path.read_bytes()
    bdt_data = bdt_path.read_bytes()
    bhd_bdt_hash = get_blake2b_hash(bhd_data + bdt_data)
    if bhd_path in _CACHED_FILES:
        bxf, cached_hash = _CACHED_FILES[bhd_path]
        if cached_hash == bhd_bdt_hash:
            # Can return cached split `Binder`.
            return bxf
        # Hash has changed, so update cache below.
    bxf = Binder.from_bytes(bhd_data, bdt_data)
    _CACHED_FILES[bhd_path] = (bxf, bhd_bdt_hash)
    return bxf
