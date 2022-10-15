from __future__ import annotations

__all__ = ["FLVERImportError", "FLVERExportError", "Transform", "get_msb_transforms"]

import math
from pathlib import Path

from soulstruct.utilities.maths import Vector3
from soulstruct.darksouls1r.maps import MSB, get_map


class FLVERImportError(Exception):
    """Exception raised during FLVER import."""
    pass


class FLVERExportError(Exception):
    """Exception raised during FLVER export."""
    pass


class Transform:
    """Store a FromSoft translate/rotate/scale combo, with property access to Blender conversions for all three."""

    def __init__(
        self,
        game_translate: Vector3,
        game_rotate: Vector3,
        game_scale: Vector3,
    ):
        self.translate = game_translate
        self.rotate = game_rotate
        self.scale = game_scale

    @classmethod
    def from_msb_part(cls, part):
        return cls(part.translate, part.rotate, part.scale)

    @property
    def bl_translate(self):
        """In FromSoft games, -Z is forward and +Y is up. In Blender, +Y is forward and +Z is up."""
        return -self.translate.x, -self.translate.z, self.translate.y

    @property
    def bl_rotate(self):
        """Euler angles in radians. Note that X is not negated, like in the translate, but Y (now Z) is."""
        return math.radians(self.rotate.x), math.radians(self.rotate.z), -math.radians(self.rotate.y)

    @property
    def bl_scale(self):
        """Just swaps Y and Z axes."""
        return self.scale.x, self.scale.z, self.scale.y


def get_msb_transforms(flver_path: Path, msb_path: Path = None) -> list[tuple[str, Transform]]:
    """Search MSB at `msb_path` (autodetected from `flver_path.parent` by default) and return
    `(map_piece_name, Transform)` pairs for all Map Piece entries using the `flver_path` model."""
    if msb_path is None:
        flver_parent_dir = flver_path.parent
        flver_map = get_map(flver_parent_dir.name)
        msb_path = flver_parent_dir.parent / f"MapStudio/{flver_map.msb_file_stem}.msb"
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
    for map_piece in msb.parts.MapPieces:
        if flver_path.name.startswith(map_piece.model_name):
            matches.append(map_piece)
    if not matches:
        raise ValueError(f"Cannot find any MSB Map Piece entries using model '{flver_path.name}'.")
    transforms = [(m.name, Transform.from_msb_part(m)) for m in matches]
    return transforms
