from __future__ import annotations

__all__ = [
    "FLVERImportError",
    "FLVERExportError",
    "PrintGameTransform",
    "parse_dummy_name",
    "HideAllDummiesOperator",
    "ShowAllDummiesOperator",
    "get_flver_from_binder",
    "get_map_piece_msb_transforms",
    "game_forward_up_vectors_to_bl_euler",
    "bl_euler_to_game_forward_up_vectors",
    "bl_rotmat_to_game_forward_up_vectors",
    "VertexArrayLayoutFactory",
    "MTDInfo",
]

import re
from pathlib import Path

from mathutils import Euler, Matrix

from soulstruct import Binder, FLVER
from soulstruct.utilities.maths import Vector3, Matrix3
from soulstruct.darksouls1r.maps import MSB, get_map
from soulstruct.base.models.flver.layout_repair import VertexArrayLayoutFactory
from soulstruct.base.models.mtd import MTDInfo

from io_soulstruct.utilities import (
    Transform, BlenderTransform, GAME_TO_BL_EULER, BL_TO_GAME_EULER, BL_TO_GAME_MAT3, LoggingOperator
)
from io_soulstruct.general import get_cached_file


DUMMY_NAME_RE = re.compile(  # accepts and ignores Blender '.001' suffix and anything else after the `[ref_id]` in name
    r"^(?P<other_model>\[\w+\] +)?(?P<flver_name>.+) +Dummy<(?P<index>\d+)> *(?P<reference_id>\[\d+\]) *(\.\d+)?$"
)


class FLVERImportError(Exception):
    """Exception raised during FLVER import."""
    pass


class FLVERExportError(Exception):
    """Exception raised during FLVER export."""
    pass


class HideAllDummiesOperator(LoggingOperator):
    """Simple operator to hide all dummy children of a selected FLVER armature."""
    bl_idname = "io_scene_soulstruct.hide_all_dummies"
    bl_label = "Hide All Dummies"
    bl_description = "Hide all dummy point children in the selected armature (Empties with 'Dummy' in name)"

    @classmethod
    def poll(cls, context):
        """At least one Blender Mesh selected."""
        return len(context.selected_objects) > 0 and all(obj.type == "MESH" for obj in context.selected_objects)

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        armature = context.selected_objects[0]
        for child in armature.children:
            if child.type == "EMPTY" and "dummy" in child.name.lower():
                child.hide_viewport = True
        return {"FINISHED"}


class ShowAllDummiesOperator(LoggingOperator):
    """Simple operator to show all dummy children of a selected FLVER armature."""
    bl_idname = "io_scene_soulstruct.show_all_dummies"
    bl_label = "Show All Dummies"
    bl_description = "Show all dummy point children in the selected armature (Empties with 'Dummy' in name)"

    @classmethod
    def poll(cls, context):
        try:
            return context.selected_objects[0].type == "ARMATURE"
        except IndexError:
            return False

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        armature = context.selected_objects[0]
        for child in armature.children:
            if child.type == "EMPTY" and "dummy" in child.name.lower():
                child.hide_viewport = False
        return {"FINISHED"}


class PrintGameTransform(LoggingOperator):
    """Simple operator that prints the Blender transform of a selected object to console in game coordinates."""
    bl_idname = "io_scene_soulstruct.print_game_transform"
    bl_label = "Print Game Transform"
    bl_description = "Print the selected object's transform in game coordinates to console."

    @classmethod
    def poll(cls, context):
        return context.object is not None

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        obj = context.object
        if obj:
            bl_transform = BlenderTransform(obj.location, obj.rotation_euler, obj.scale)
            print(
                f"FromSoftware game transform of object '{obj.name}':\n"
                f"    translate = {repr(bl_transform.game_translate)}\n"
                f"    rotate = {repr(bl_transform.game_rotate_rad)}\n"
                f"    scale = {repr(bl_transform.game_scale)}"
            )
        return {"FINISHED"}


def parse_dummy_name(dummy_name: str) -> dict[str, str | int]:
    """Parse a FLVER dummy name into its component parts: `other_model`, `flver_name`, `index`, and `reference_id`.

    Returns a dictionary with keys `other_model` (str, optional), `flver_name` (str), `index` (int), and
    (most importantly) `reference_id` (int).

    If the dummy name is invalid, an empty dictionary is returned.
    """
    match = DUMMY_NAME_RE.match(dummy_name)
    if match is None:
        return {}  # invalid name
    other_model = match.group("other_model")
    return {
        "other_model": other_model.strip()[1:-1] if other_model else "",  # exclude brackets
        "flver_name": match.group("flver_name"),
        "index": int(match.group("index")),
        "reference_id": int(match.group("reference_id")[1:-1]),  # exclude brackets
    }


def get_flver_from_binder(binder: Binder, file_path: Path) -> FLVER:
    flver_entries = binder.find_entries_matching_name(r".*\.flver(\.dcx)?")
    if not flver_entries:
        raise FLVERImportError(f"Cannot find a FLVER file in binder {file_path}.")
    elif len(flver_entries) > 1:
        raise FLVERImportError(f"Found multiple FLVER files in binder {file_path}.")
    return flver_entries[0].to_binary_file(FLVER)


def get_map_piece_msb_transforms(flver_path: Path, msb_path: Path = None) -> list[tuple[str, Transform]]:
    """Search MSB at `msb_path` (autodetected from `flver_path.parent` by default) and return
    `(map_piece_name, Transform)` pairs for all Map Piece entries using the `flver_path` model.

    Uses cached MSB if possible.

    TODO: Use settings game directory rather than guessing from FLVER path, if possible.
    """
    if msb_path is None:
        flver_parent_dir = flver_path.parent
        flver_map = get_map(flver_parent_dir.name)
        msb_path = flver_parent_dir.parent / f"MapStudio/{flver_map.msb_file_stem}.msb"
    if not msb_path.is_file():
        raise FileNotFoundError(f"Cannot find MSB file '{msb_path}'.")
    try:
        msb = get_cached_file(msb_path, MSB)
    except Exception as ex:
        raise RuntimeError(
            f"Cannot open MSB: {ex}.\n"
            f"\nCurrently, only Dark Souls 1 (either version) MSBs are supported."
        )
    matches = []
    for map_piece in msb.map_pieces:
        if flver_path.name.startswith(map_piece.model.name):
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
    rotation_matrix = Matrix3([
        [right.x, up.x, forward.x],
        [right.y, up.y, forward.y],
        [right.z, up.z, forward.z],
    ])
    game_euler = rotation_matrix.to_euler_angles(radians=True)
    return GAME_TO_BL_EULER(game_euler)


def bl_euler_to_game_forward_up_vectors(bl_euler: Euler) -> tuple[Vector3, Vector3]:
    """Convert a Blender `Euler` to its forward-axis and up-axis vectors in game space (for `FLVER.Dummy`)."""
    game_euler = BL_TO_GAME_EULER(bl_euler)
    game_mat = Matrix3.from_euler_angles(game_euler)
    forward = Vector3((game_mat[0][2], game_mat[1][2], game_mat[2][2]))  # third column (Z)
    up = Vector3((game_mat[0][1], game_mat[1][1], game_mat[2][1]))  # second column (Y)
    return forward, up


def bl_rotmat_to_game_forward_up_vectors(bl_rotmat: Matrix) -> tuple[Vector3, Vector3]:
    """Convert a Blender `Matrix` to its game equivalent's forward-axis and up-axis vectors (for `FLVER.Dummy`)."""
    game_mat = BL_TO_GAME_MAT3(bl_rotmat)
    forward = Vector3((game_mat[0][2], game_mat[1][2], game_mat[2][2]))  # third column (Z)
    up = Vector3((game_mat[0][1], game_mat[1][1], game_mat[2][1]))  # second column (Y)
    return forward, up
