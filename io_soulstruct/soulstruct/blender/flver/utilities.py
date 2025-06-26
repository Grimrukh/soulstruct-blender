from __future__ import annotations

__all__ = [
    "get_flvers_from_binder",
]

from pathlib import Path

from soulstruct.containers import Binder
from soulstruct.flver import FLVER

from soulstruct.blender.exceptions import *


def get_flvers_from_binder(
    binder: Binder,
    file_path: Path,
    allow_multiple=False,
) -> list[FLVER]:
    """Find all FLVER files (with or without DCX) in `binder`.

    By default, only one FLVER file is allowed. If `allow_multiple` is True, multiple FLVER files will be returned.
    """
    flver_entries = binder.find_entries_matching_name(r".*\.flver(\.dcx)?")
    if not flver_entries:
        raise FLVERImportError(f"Cannot find a FLVER file in binder {file_path}.")
    elif not allow_multiple and len(flver_entries) > 1:
        raise FLVERImportError(f"Found multiple FLVER files in binder {file_path}.")
    return [entry.to_binary_file(FLVER) for entry in flver_entries]
