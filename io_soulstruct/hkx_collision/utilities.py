from __future__ import annotations

__all__ = [
    "HKXImportError",
    "HKXExportError",
    "HKX_MESH_TYPING",
    "get_msb_transforms",
]

import typing as tp
from pathlib import Path

from soulstruct.darksouls1r.maps import MSB, get_map

from io_soulstruct.utilities import Transform

class HKXImportError(Exception):
    """Exception raised during HKX import."""
    pass


class HKXExportError(Exception):
    """Exception raised during HKX export."""
    pass


HKX_MESH_TYPING = tuple[list[tp.Sequence[float]], list[tp.Sequence[int]]]


def get_msb_transforms(hkx_name: str, hkx_path: Path, msb_path: Path = None) -> list[tuple[str, Transform]]:
    """Search MSB at `msb_path` (autodetected from `hkx_path.parent` by default) and return
    `(collision_name, Transform)` pairs for all Collision entries using the `hkx_name` model."""
    model_name = hkx_name[:7]  # drop `AXX` suffix
    if model_name.startswith("l"):
        model_name = f"h{model_name[1:]}"  # models use 'h' prefix
    if msb_path is None:
        hkx_parent_dir = hkx_path.parent
        hkx_map = get_map(hkx_parent_dir.name)
        msb_path = hkx_parent_dir.parent / f"MapStudio/{hkx_map.msb_file_stem}.msb"
    if not msb_path.is_file():
        raise FileNotFoundError(f"Cannot find MSB file '{msb_path}'.")
    try:
        msb = MSB(msb_path)
    except Exception as ex:
        raise RuntimeError(
            f"Cannot open MSB: {ex}.\n"
            f"\nCurrently, only Dark Souls 1 (either version) MSBs are supported."
        )
    matches = []
    for collision in msb.parts.Collisions:
        if model_name == collision.model_name:
            matches.append(collision)
    if not matches:
        raise ValueError(f"Cannot find any MSB Collision entries using model '{model_name}' ({hkx_name}).")
    transforms = [(m.name, Transform.from_msb_part(m)) for m in matches]
    return transforms
