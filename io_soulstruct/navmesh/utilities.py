from __future__ import annotations

__all__ = [
    "NVMImportError",
    "NVMExportError",
    "NVM_MESH_TYPING",
    "get_msb_transforms",
]

from pathlib import Path
import typing as tp

from soulstruct.darksouls1r.maps import MSB, get_map

from io_soulstruct.utilities import Transform


class NVMImportError(Exception):
    """Exception raised during NVM import."""
    pass


class NVMExportError(Exception):
    """Exception raised during NVM export."""
    pass


NVM_MESH_TYPING = tuple[list[tp.Sequence[float]], list[tp.Sequence[int]]]


def get_msb_transforms(nvm_name: str, nvm_path: Path, msb_path: Path = None) -> list[tuple[str, Transform]]:
    """Search MSB at `msb_path` (autodetected from `nvm_path.parent` by default) and return
    `(navmesh_name, Transform)` pairs for all Navmesh entries using the `nvm_name` model."""
    model_name = nvm_name[:7]  # drop `AXX` suffix
    if msb_path is None:
        nvm_parent_dir = nvm_path.parent
        nvm_map = get_map(nvm_parent_dir.name)
        msb_path = nvm_parent_dir.parent / f"MapStudio/{nvm_map.msb_file_stem}.msb"
    if not msb_path.is_file():
        raise FileNotFoundError(f"Cannot find MSB file '{msb_path}'.")
    try:
        msb = MSB.from_path(msb_path)
    except Exception as ex:
        raise RuntimeError(
            f"Cannot open MSB: {ex}.\n"
            f"\nCurrently, only Dark Souls 1 (either version) MSBs are supported."
        )
    matches = []
    for navmesh in msb.navmeshes:
        if model_name == navmesh.model.name:
            matches.append(navmesh)
    if not matches:
        raise ValueError(f"Cannot find any MSB Navmesh entries using model '{model_name}' ({nvm_name}).")
    transforms = [(m.name, Transform.from_msb_part(m)) for m in matches]
    return transforms
