"""Utilities shared by different file formats."""
from __future__ import annotations

__all__ = [
    "MAP_STEM_RE",
    "GAME_TO_BL_VECTOR",
    "GAME_TO_BL_EULER",
    "GAME_TO_BL_MAT3",
    "BL_TO_GAME_VECTOR3",
    "BL_TO_GAME_VECTOR4",
    "BL_TO_GAME_VECTOR3_LIST",
    "BL_TO_GAME_EULER",
    "BL_TO_GAME_MAT3",
    "BL_EDIT_BONE_DEFAULT_QUAT",
    "BL_EDIT_BONE_DEFAULT_QUAT_INV",
    "Transform",
    "BlenderTransform",
    "get_bl_prop",
    "is_uniform",
    "natural_keys",
    "LoggingOperator",
    "get_dcx_enum_property",
    "read_settings",
    "write_settings",
    "profile_execute",
    "hsv_color",
    "create_basic_material",
]

import cProfile
import functools
import math
import pstats
import re
import typing as tp
from dataclasses import dataclass
from pathlib import Path

import bpy
from bpy.props import EnumProperty
# noinspection PyUnresolvedReferences
from bpy.types import Operator
from mathutils import Color, Euler, Vector, Matrix

from soulstruct.containers import DCXType
from soulstruct.utilities.files import read_json, write_json
from soulstruct.utilities.maths import Vector3, Vector4, Matrix3


MAP_STEM_RE = re.compile(r"^m(?P<area>\d\d)_(?P<block>\d\d)_(?P<cc>\d\d)_(?P<dd>\d\d)$")

_SETTINGS_PATH = Path(__file__).parent / "UserSettings.json"


def GAME_TO_BL_VECTOR(game_vector: Vector3 | tp.Sequence[float, float, float]) -> Vector:
    """Just swaps Y and Z axes. X increases to the right in both systems; the game is left-handed and Blender is
    right-handed.

    This function is its own inverse, but an explicit converter that produces a Soulstruct class is given below.
    """
    return Vector((game_vector[0], game_vector[2], game_vector[1]))


def BL_TO_GAME_VECTOR3(bl_vector: Vector):
    """See above."""
    return Vector3((bl_vector.x, bl_vector.z, bl_vector.y))


def BL_TO_GAME_VECTOR4(bl_vector: Vector, w=0.0):
    """See above."""
    return Vector4((bl_vector.x, bl_vector.z, bl_vector.y, w))


def BL_TO_GAME_VECTOR3_LIST(bl_vector: Vector) -> list[float, float, float]:
    """Faster version that just returns a list."""
    return [bl_vector.x, bl_vector.z, bl_vector.y]


def GAME_TO_BL_EULER(game_euler) -> Euler:
    """All three Euler angles need negating to preserve rotations.

    This function is its own inverse, but an explicit converted that produces a Soulstruct class is given below.

    NOTE: Blender Euler rotation mode should be 'XYZ' (corresponding to game 'XZY').
    """
    return Euler((-game_euler[0], -game_euler[2], -game_euler[1]))


def GAME_TO_BL_MAT3(game_mat3: Matrix3) -> Matrix:
    """Converts a 3x3 rotation matrix from the game to a Blender Matrix.

    Swaps columns 1 and 2, and rows 1 and 2.
    """
    r = game_mat3
    return Matrix((
        (r[0, 0], r[0, 2], r[0, 1]),
        (r[2, 0], r[2, 2], r[2, 1]),
        (r[1, 0], r[1, 2], r[1, 1]),
    ))


def BL_TO_GAME_MAT3(bl_mat3: Matrix) -> Matrix3:
    """Converts a 3x3 rotation matrix from Blender to the game.

    This is the same transformation as GAME_TO_BL_MAT3, but the types are swapped.
    """
    r = bl_mat3
    return Matrix3((
        (r[0][0], r[0][2], r[0][1]),
        (r[2][0], r[2][2], r[2][1]),
        (r[1][0], r[1][2], r[1][1]),
    ))


def BL_TO_GAME_EULER(bl_euler: Euler) -> Vector3:
    """See above."""
    return Vector3((-bl_euler.x, -bl_euler.z, -bl_euler.y))


BL_EDIT_BONE_DEFAULT_QUAT = Euler((0.0, 1.0, 0.0)).to_quaternion()
BL_EDIT_BONE_DEFAULT_QUAT_INV = BL_EDIT_BONE_DEFAULT_QUAT.inverted()


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
        return BL_TO_GAME_VECTOR3(self.bl_translate)

    @property
    def game_rotate_deg(self) -> Vector3:
        return 180.0 / math.pi * self.game_rotate_rad

    @property
    def game_rotate_rad(self) -> Vector3:
        return BL_TO_GAME_EULER(self.bl_rotate)

    @property
    def game_scale(self) -> Vector3:
        return BL_TO_GAME_VECTOR3(self.bl_scale)

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


def get_bl_prop(bl_obj, name: str, prop_type: tp.Type, default=None, callback: tp.Callable = None):
    """Try to get custom property `name` from Blender object `bl_obj`, with type `prop_type`.

    Optional `default` value will be returned if the property is not found (`None` is not a valid default value).
    Value will be passed through optional one-arg `callback` if given.
    """
    prop_value = bl_obj.get(name, default)

    if prop_value is None:
        raise KeyError(f"Object '{bl_obj.name}' does not have required `{prop_type}` property '{name}'.")
    if prop_type is tuple:
        # Blender type is an `IDPropertyArray` with `typecode = 'i'` or `'d'`.
        if type(prop_value).__name__ != "IDPropertyArray":
            raise KeyError(
                f"Object '{bl_obj.name}' property '{name}' does not have type `IDPropertyArray`."
            )
        if not callback:
            prop_value = tuple(prop_value)  # convert `IDPropertyArray` to `tuple` by default
    elif not isinstance(prop_value, prop_type):
        raise KeyError(f"Object '{bl_obj.name}' property '{name}' does not have required type `{prop_type}`.")

    if callback:
        return callback(prop_value)
    return prop_value


def is_uniform(vector: Vector | Vector3, rel_tol: float):
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


def get_dcx_enum_property(
    default: str | DCXType = "Null",
    name="Compression",
    description="Type of DCX compression to apply to exported file (typically not used in Binder)",
):
    """Create a Blender `EnumProperty` for selecting DCX compression type.

    Will default to `default` string, which should be one of the items below. The "default default" is "Null", which
    means no DCX compression will be applied.
    """
    return EnumProperty(
        name=name,
        items=[
            ("Null", "None", "Export without any DCX compression"),
            ("DCX_EDGE", "DES", "Demon's Souls compression"),
            ("DCX_DFLT_10000_24_9", "DS1/DS2", "Dark Souls 1/2 compression"),
            ("DCX_DFLT_10000_44_9", "BB/DS3", "Bloodborne/Dark Souls 3 compression"),
            ("DCX_DFLT_11000_44_9", "Sekiro", "Sekiro compression (requires Oodle DLL)"),
            ("DCX_KRAK", "Elden Ring", "Elden Ring compression (requires Oodle DLL)"),
        ],
        description=description,
        default=default if isinstance(default, str) else default.name,
    )


def read_settings() -> dict[str, tp.Any]:
    try:
        return read_json(_SETTINGS_PATH)
    except FileNotFoundError:
        return {}


def write_settings(**settings):
    settings = read_settings()
    settings.update(settings)
    write_json(_SETTINGS_PATH, settings)


def profile_execute(execute_method: tp.Callable):
    """Profiles the given `execute` method and prints the results to the console."""

    @functools.wraps(execute_method)
    def decorated(self, context):

        with cProfile.Profile() as pr:
            result = execute_method(self, context)
        p = pstats.Stats(pr)
        p = p.strip_dirs()
        p.sort_stats("cumtime").print_stats(40)

        return result

    return decorated


def hsv_color(hue: float, saturation: float, value: float, alpha=1.0) -> tuple[float, float, float, float]:
    color = Color()
    color.hsv = (hue, saturation, value)
    return color.r, color.g, color.b, alpha


def create_basic_material(material_name: str, color: tuple[float, float, float, float], wireframe_pixel_width=0.0):
    """Create a very basic material with a single diffuse `color`.

    If `wireframe_pixel_width > 0`, the material will also render a wireframe with lines of the given width.
    """
    bl_material = bpy.data.materials.new(name=material_name)
    bl_material.use_nodes = True
    nodes = bl_material.node_tree.nodes
    nodes.clear()
    links = bl_material.node_tree.links

    diffuse = nodes.new(type="ShaderNodeBsdfDiffuse")
    diffuse.inputs["Color"].default_value = color
    diffuse.location = (0, 0)

    material_output = nodes.new(type="ShaderNodeOutputMaterial")
    material_output.location = (400, 0)

    if wireframe_pixel_width <= 0.0:
        # No wireframe. Just connect BSDF to output.
        links.new(diffuse.outputs["BSDF"], material_output.inputs["Surface"])
        return bl_material

    wireframe = nodes.new(type="ShaderNodeWireframe")
    wireframe.location = (0, 150)
    wireframe.inputs["Size"].default_value = wireframe_pixel_width
    wireframe.use_pixel_size = True

    emission = nodes.new(type="ShaderNodeEmission")
    emission.location = (0, -150)
    emission.inputs["Strength"].default_value = 1.0
    emission.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)  # black

    mix_shader = nodes.new(type="ShaderNodeMixShader")
    mix_shader.location = (200, 0)

    links.new(wireframe.outputs["Fac"], mix_shader.inputs["Fac"])
    links.new(diffuse.outputs["BSDF"], mix_shader.inputs[1])
    links.new(emission.outputs["Emission"], mix_shader.inputs[2])
    links.new(mix_shader.outputs["Shader"], material_output.inputs["Surface"])

    return bl_material
