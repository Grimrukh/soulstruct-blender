from __future__ import annotations

__all__ = [
    "FLVERImportError",
    "FLVERExportError",
    "get_msb_transforms",
    "game_forward_up_vectors_to_bl_euler",
    "bl_euler_to_game_forward_up_vectors",
]

from pathlib import Path

from mathutils import Euler
from soulstruct.utilities.maths import Vector3, Matrix3
from soulstruct.darksouls1r.maps import MSB, get_map

from io_soulstruct.utilities import Transform


class FLVERImportError(Exception):
    """Exception raised during FLVER import."""
    pass


class FLVERExportError(Exception):
    """Exception raised during FLVER export."""
    pass


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


def game_forward_up_vectors_to_bl_euler(forward: Vector3, up: Vector3) -> Euler:
    """Convert `forward` and `up` vectors to Euler angles `(x, y, z)` (in Blender coordinates).

    Mainly used for representing FLVER dummies in Blender.
    """
    right = up.cross(forward)
    rotation_matrix = Matrix3(
        right.x, up.x, forward.x,
        right.y, up.y, forward.y,
        right.z, up.z, forward.z,
    )
    euler_angles = rotation_matrix.to_euler_angles(radians=True, order="xzy")
    return Euler((euler_angles.x, euler_angles.z, -euler_angles.y))


def bl_euler_to_game_forward_up_vectors(euler: Euler) -> (Vector3, Vector3):
    game_euler = Euler((euler.x, -euler.z, euler.y))
    game_mat = game_euler.to_matrix()
    forward = Vector3(game_mat.col[2])
    up = Vector3(game_mat.col[1])
    return forward, up
