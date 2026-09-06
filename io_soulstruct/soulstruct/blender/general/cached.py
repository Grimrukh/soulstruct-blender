from __future__ import annotations

__all__ = [
    "get_cached_file",
    "get_cached_bxf",
]

import typing as tp
from pathlib import Path

from soulstruct.containers import Binder
from soulstruct.utilities.files import get_blake2b_hash_hex

if tp.TYPE_CHECKING:
    from soulstruct.base.base_binary_file import BaseBinaryFile


# Maps file paths to `(BaseBinaryFile, blake2b_hash_hex)` tuples for caching. Useful for inspecting, say, MSB files
# repeatedly without modifying them.
_CACHED_FILES = {}


def get_cached_file[BASE_BINARY_FILE_T: BaseBinaryFile](
    file_path: Path | str, file_type: type[BASE_BINARY_FILE_T]
) -> BASE_BINARY_FILE_T:
    """Load a `BaseBinaryFile` from disk and cache it in a global dictionary.

    NOTE: Obviously, these cached `BaseBinaryFile` instances should be read-only, generally speaking, unless they are
     immediately written back to disk when modified!
    """
    file_path = Path(file_path)
    if not file_path.is_file():
        # Not loaded, even if cached.
        _CACHED_FILES.pop(file_path, None)
        raise FileNotFoundError(f"Cannot find file '{file_path}'.")

    # `get_blake2b_hash_hex()` can hash straight from disk (streamed in chunks), so we don't need to load the full
    # file into memory just to check if it has changed. We only do the full `read_bytes()` if we actually need to
    # (re)parse the file below.
    file_path_hash = get_blake2b_hash_hex(file_path)
    if file_path in _CACHED_FILES:
        game_file, cached_hash = _CACHED_FILES[file_path]
        if cached_hash == file_path_hash:
            # Can return cached file.
            return game_file
        # Hash has changed, so update cache below.
    file_data = file_path.read_bytes()
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

    # `get_blake2b_hash_hex()` can hash straight from disk (streamed in chunks), so we avoid loading the (often huge)
    # BDT file into memory just to check if it has changed. We only do the full `read_bytes()` of both files if we
    # actually need to (re)parse them below. BHD and BDT hashes are tracked as a pair, since they are always paired.
    bhd_bdt_hash = (get_blake2b_hash_hex(bhd_path), get_blake2b_hash_hex(bdt_path))
    if bhd_path in _CACHED_FILES:
        bxf, cached_hash = _CACHED_FILES[bhd_path]
        if cached_hash == bhd_bdt_hash:
            # Can return cached split `Binder`.
            return bxf
        # Hash has changed, so update cache below.
    bhd_data = bhd_path.read_bytes()
    bdt_data = bdt_path.read_bytes()
    bxf = Binder.from_bytes(bhd_data, bdt_data)
    _CACHED_FILES[bhd_path] = (bxf, bhd_bdt_hash)
    return bxf
