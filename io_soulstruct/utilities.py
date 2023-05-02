"""Utilities shared by different file formats."""
from __future__ import annotations

__all__ = [
    "GAME_TO_BL_VECTOR",
    "GAME_TO_BL_EULER",
    "BL_TO_GAME_VECTOR",
    "BL_TO_GAME_VECTOR_LIST",
    "BL_TO_GAME_EULER",
    "Transform",
    "BlenderTransform",
    "BlenderProp",
    "BlenderPropertyManager",
    "is_uniform",
    "natural_keys",
    "LoggingOperator",
]

import math
import re
import typing as tp
from dataclasses import dataclass

# noinspection PyUnresolvedReferences
from bpy.types import Operator
from mathutils import Euler, Vector, Matrix

from soulstruct.utilities.maths import Vector3


def GAME_TO_BL_VECTOR(game_vector) -> Vector:
    """Just swaps Y and Z axes. X increases to the right in both systems; the game is left-handed and Blender is
    right-handed.

    This function is its own inverse, but an explicit converter that produces a Soulstruct class is given below.
    """
    return Vector((game_vector[0], game_vector[2], game_vector[1]))


def BL_TO_GAME_VECTOR(bl_vector: Vector):
    """See above."""
    return Vector3((bl_vector.x, bl_vector.z, bl_vector.y))


def BL_TO_GAME_VECTOR_LIST(bl_vector: Vector):
    """Faster version that just returns a list."""
    return [bl_vector.x, bl_vector.z, bl_vector.y]


def GAME_TO_BL_EULER(game_euler) -> Euler:
    """All three Euler angles need negating to preserve rotations.

    This function is its own inverse, but an explicit converted that produces a Soulstruct class is given below.

    NOTE: Blender Euler rotation mode should be 'XYZ' (corresponding to game 'XZY').
    """
    return Euler((-game_euler[0], -game_euler[2], -game_euler[1]))


def BL_TO_GAME_EULER(bl_euler: Euler) -> Vector3:
    """See above."""
    return Vector3((-bl_euler.x, -bl_euler.z, -bl_euler.y))


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
        return GAME_TO_BL_VECTOR(self.translate)

    @property
    def bl_rotate(self) -> Euler:
        if not self.radians:
            return GAME_TO_BL_EULER(math.pi / 180.0 * self.rotate)
        return GAME_TO_BL_EULER(self.rotate)

    @property
    def bl_scale(self) -> Vector:
        return GAME_TO_BL_VECTOR(self.scale)


@dataclass(slots=True)
class BlenderTransform:
    """Store a Blender translate/rotate/scale combo."""

    bl_translate: Vector
    bl_rotate: Euler  # radians
    bl_scale: Vector

    @property
    def game_translate(self) -> Vector3:
        return BL_TO_GAME_VECTOR(self.bl_translate)

    @property
    def game_rotate_deg(self) -> Vector3:
        return 180.0 / math.pi * self.game_rotate_rad

    @property
    def game_rotate_rad(self) -> Vector3:
        return BL_TO_GAME_EULER(self.bl_rotate)

    @property
    def game_scale(self) -> Vector3:
        return BL_TO_GAME_VECTOR(self.bl_scale)

    @classmethod
    def from_bl_obj(cls, bl_obj) -> BlenderTransform:
        return BlenderTransform(
            bl_obj.location,
            bl_obj.rotation_euler,
            bl_obj.scale,
        )

    def to_matrix(self) -> Matrix:
        return Matrix.LocRotScale(self.bl_translate, self.bl_rotate, self.bl_scale)

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


class BlenderProp(tp.NamedTuple):
    bl_type: tp.Type
    default: tp.Any = None
    callback: tp.Callable = None
    do_not_assign: bool = False


class BlenderPropertyManager:

    properties: dict[str, dict[str, BlenderProp]]

    def __init__(self, property_dict: dict[str, dict[str, BlenderProp]]):
        self.properties = property_dict

    def get(self, bl_obj, prop_class: str, bl_prop_name: str, py_prop_name: str = None):
        if py_prop_name is None:
            py_prop_name = bl_prop_name
        try:
            prop = self.properties[prop_class][py_prop_name]
        except KeyError:
            raise KeyError(f"Invalid Blender HKX property class/name: {prop_class}, {bl_prop_name}")

        prop_value = bl_obj.get(bl_prop_name, prop.default)

        if prop_value is None:
            raise KeyError(f"Object '{bl_obj.name}' does not have required `{prop_class}` property '{bl_prop_name}'.")
        if prop.bl_type is tuple:
            # Blender type is an `IDPropertyArray` with `typecode = 'i'` or `'d'`.
            if type(prop_value).__name__ != "IDPropertyArray":
                raise KeyError(
                    f"Object '{bl_obj.name}' property '{bl_prop_name}' does not have type `IDPropertyArray`."
                )
            if not prop.callback:
                prop_value = tuple(prop_value)  # convert `IDPropertyArray` to `tuple` by default
        elif not isinstance(prop_value, prop.bl_type):
            raise KeyError(f"Object '{bl_obj.name}' property '{bl_prop_name}' does not have type `{prop.bl_type}`.")

        if prop.callback:
            prop_value = prop.callback(prop_value)

        return prop_value

    def get_all(self, bl_obj, py_obj, prop_class: str, bl_prop_prefix: str = "") -> dict[str, tp.Any]:
        """Assign all class properties from Blender object `bl_obj` as attributes of Soulstruct object `py_obj`."""
        unassigned = {}
        for prop_name, prop in self.properties[prop_class].items():
            prop_value = self.get(bl_obj, prop_class, bl_prop_prefix + prop_name, py_prop_name=prop_name)
            if prop.do_not_assign:
                unassigned[prop_name] = prop_value
            else:
                setattr(py_obj, prop_name, prop_value)
        return unassigned


def is_uniform(vector: Vector3, rel_tol: float):
    xy_close = math.isclose(vector.x, vector.y, rel_tol=rel_tol)
    xz_close = math.isclose(vector.x, vector.z, rel_tol=rel_tol)
    yz_close = math.isclose(vector.y, vector.z, rel_tol=rel_tol)
    return xy_close and xz_close and yz_close


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
