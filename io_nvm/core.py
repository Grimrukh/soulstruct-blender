from __future__ import annotations

__all__ = [
    "NVMImportError",
    "NVMExportError",
    "Transform",
    "BlenderTransform",
    "game_vec_to_blender_vec",
    "blender_vec_to_game_vec",
    "is_uniform",
    "get_msb_transforms",
    "natural_keys",
    "LoggingOperator",
]

import re
import typing as tp
from dataclasses import dataclass
from math import degrees, radians, isclose
from pathlib import Path

from soulstruct.utilities.maths import Vector3
from soulstruct.darksouls1r.maps import MSB, get_map

# noinspection PyUnresolvedReferences
from bpy.types import Operator
from mathutils import Euler, Vector


class NVMImportError(Exception):
    """Exception raised during NVM import."""
    pass


class NVMExportError(Exception):
    """Exception raised during NVM export."""
    pass


@dataclass(slots=True)
class Transform:
    """Store a FromSoft translate/rotate/scale combo, with property access to Blender conversions for all three."""

    translate: Vector3
    rotate: Vector3  # Euler angles
    scale: Vector3
    radians: bool = False

    @classmethod
    def from_msb_part(cls, part) -> Transform:
        return cls(part.translate, part.rotate, part.scale)

    @property
    def bl_translate(self) -> Vector:
        """In FromSoft games, -Z is forward and +Y is up. In Blender, +Y is forward and +Z is up."""
        return Vector((-self.translate.x, -self.translate.z, self.translate.y))

    @property
    def bl_rotate(self) -> Euler:
        """Euler angles in radians. Note that X is not negated, like in the translate, but Y (now Z) is."""
        if not self.radians:
            return Euler((radians(self.rotate.x), radians(self.rotate.z), -radians(self.rotate.y)))
        return Euler((self.rotate.x, self.rotate.z, -self.rotate.y))

    @property
    def bl_scale(self) -> Vector:
        """Just swaps Y and Z axes."""
        return Vector((self.scale.x, self.scale.z, self.scale.y))


@dataclass(slots=True)
class BlenderTransform:
    """Store a Blender translate/rotate/scale combo."""

    bl_translate: Vector
    bl_rotate: Euler
    bl_scale: Vector
    radians: bool = True

    @property
    def game_translate(self) -> Vector3:
        return Vector3(-self.bl_translate.x, self.bl_translate.z, -self.bl_translate.y)

    @property
    def game_rotate_deg(self) -> Vector3:
        if self.radians:
            return Vector3(degrees(self.bl_rotate.x), -degrees(self.bl_rotate.z), degrees(self.bl_rotate.y))
        return Vector3(self.bl_rotate.x, -self.bl_rotate.z, self.bl_rotate.y)

    @property
    def game_rotate_rad(self) -> Vector3:
        if not self.radians:
            return Vector3(radians(self.bl_rotate.x), -radians(self.bl_rotate.z), radians(self.bl_rotate.y))
        return Vector3(self.bl_rotate.x, -self.bl_rotate.z, self.bl_rotate.y)

    @property
    def game_scale(self) -> Vector3:
        """Just swaps Y and Z axes."""
        return Vector3(self.bl_scale.x, self.bl_scale.z, self.bl_scale.y)

    @classmethod
    def from_bl_obj(cls, bl_obj) -> BlenderTransform:
        return BlenderTransform(
            bl_obj.location,
            bl_obj.rotation_euler,
            bl_obj.scale,
        )

    def inverse(self) -> BlenderTransform:
        inv_rotate_mat = self.bl_rotate.to_matrix().inverted()
        inv_translate = -(inv_rotate_mat @ self.bl_translate)
        inv_scale = Vector((1.0 / self.bl_scale.x, 1.0 / self.bl_scale.y, 1.0 / self.bl_scale.z))
        return BlenderTransform(inv_translate, inv_rotate_mat.to_euler(), inv_scale)

    def compose(self, other: BlenderTransform):
        """Apply to another transform."""
        rot_mat = self.bl_rotate.to_matrix()
        new_translate = self.bl_translate + rot_mat @ other.bl_translate
        new_rotate = (rot_mat @ other.bl_rotate.to_matrix()).to_euler()
        new_scale = self.bl_scale * other.bl_scale
        return BlenderTransform(new_translate, new_rotate, new_scale)


def game_vec_to_blender_vec(game_vec) -> Vector:
    return Vector((-game_vec[0], -game_vec[2], game_vec[1]))


def blender_vec_to_game_vec(bl_vec: Vector) -> list[float]:
    return [-bl_vec.x, bl_vec.z, -bl_vec.y]


def is_uniform(vector: Vector3, rel_tol: float):
    xy_close = isclose(vector.x, vector.y, rel_tol=rel_tol)
    xz_close = isclose(vector.x, vector.z, rel_tol=rel_tol)
    yz_close = isclose(vector.y, vector.z, rel_tol=rel_tol)
    return xy_close and xz_close and yz_close


def get_msb_transforms(nvm_name: str, nvm_path: Path, msb_path: Path = None) -> list[tuple[str, Transform]]:
    """Search MSB at `msb_path` (autodetected from `nvm_path.parent` by default) and return
    `(navmesh_name, Transform)` pairs for all Navmesh entries using the `nvm_name` model."""
    if msb_path is None:
        nvm_parent_dir = nvm_path.parent
        nvm_map = get_map(nvm_parent_dir.name)
        msb_path = nvm_parent_dir.parent / f"MapStudio/{nvm_map.msb_file_stem}.msb"
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
    for navmesh in msb.parts.Navmeshes:
        if nvm_name == navmesh.model_name:
            matches.append(navmesh)
    if not matches:
        raise ValueError(f"Cannot find any MSB Navmesh entries using model '{nvm_name}'.")
    transforms = [(m.name, Transform.from_msb_part(m)) for m in matches]
    return transforms


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    """Key for `list.sort()` to sort in human/natural order (preserve numeric chunks).

    See:
        http://nedbatchelder.com/blog/200712/human_sorting.html
    """
    return [atoi(c) for c in re.split(r"(\d+)", text)]


class LoggingOperator(Operator):

    cleanup_callback: tp.Callable = None

    def info(self, msg: str):
        print(f"# INFO: {msg}")
        self.report({"INFO"}, msg)

    def warning(self, msg: str):
        print(f"# WARNING: {msg}")
        self.report({"WARNING"}, msg)

    def error(self, msg: str) -> set[str]:
        print(f"# ERROR: {msg}")
        if self.cleanup_callback:
            try:
                self.cleanup_callback()
            except Exception as ex:
                self.report({"ERROR"}, f"Error occurred during cleanup callback: {ex}")
        self.report({"ERROR"}, msg)
        return {"CANCELLED"}
