from __future__ import annotations

__all__ = [
    "ADDON_PACKAGE_PATH",
]

from pathlib import Path


def ADDON_PACKAGE_PATH(*relative_parts) -> Path:
    """Returns resolved path of given files in `io_soulstruct` package directory. Path parts must start with
    "io_soulstruct" or it will be automatically added.

    Does not support `PyInstaller`, as this Blender add-on is not intended to be frozen.
    """
    if not relative_parts:
        # Return package directory.
        relative_path = Path("io_soulstruct")
    else:
        relative_path = Path(*relative_parts)
        if relative_path.parts[0] != "io_soulstruct":
            relative_path = Path("io_soulstruct", relative_path)

    # Standard Python package:
    parent = Path(__file__).parent
    while parent.name != "io_soulstruct":
        parent = parent.parent
    return (parent.parent / relative_path).resolve()
