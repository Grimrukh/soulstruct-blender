from pathlib import Path

import math

from soulstruct.darksouls1r.maps import MSB
from soulstruct.utilities.maths import Vector3


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


def get_msb_transforms(file_path: Path) -> list[tuple[str, Transform]]:
    """Look for MSB JSON file (created by `MSB` manually in Soulstruct) and get transforms of entries using the
    given FLVER model."""
    msb_path = file_path.parent.parent / f"MapStudio/{file_path.parent.name}.msb"
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
        if file_path.name.startswith(map_piece.model_name):
            matches.append(map_piece)
    if not matches:
        raise ValueError(f"Cannot find any MSB Map Piece entries using model '{file_path.name}'.")
    transforms = [(m.name, Transform.from_msb_part(m)) for m in matches]
    return transforms
