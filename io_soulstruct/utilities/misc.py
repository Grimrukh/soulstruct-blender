from __future__ import annotations

__all__ = [
    "MAP_STEM_RE",
    "get_bl_obj_stem",
    "get_bl_prop",
    "is_uniform",
    "natural_keys",
    "find_or_create_bl_empty",
    "is_path_and_file",
    "is_path_and_dir",
]

import math
import re
import typing as tp
from pathlib import Path

import bpy
from mathutils import Vector

from soulstruct.utilities.maths import Vector3


MAP_STEM_RE = re.compile(r"^m(?P<area>\d\d)_(?P<block>\d\d)_(?P<cc>\d\d)_(?P<dd>\d\d)$")


def get_bl_obj_stem(bl_obj: bpy.types.Object) -> str:
    """Get part of name before first period and space."""
    return bl_obj.name.split(".")[0].split(" ")[0]


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
        if default is None and type(prop_value).__name__ != "IDPropertyArray":
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


def find_or_create_bl_empty(name: str, context):
    """Find Blender object `name` or create an Empty object with that name in the current scene."""
    try:
        obj = bpy.data.objects[name]
    except KeyError:
        obj = bpy.data.objects.new(name, None)
        if context is None:
            context = bpy.context
        context.scene.collection.objects.link(obj)
    return obj


def is_path_and_file(path: str | Path | None) -> bool:
    """Return True if `path` is a valid path to a file."""
    if path is None:
        return False
    return Path(path).is_file()


def is_path_and_dir(path: str | Path | None) -> bool:
    """Return True if `path` is a valid path to a directory."""
    if path is None:
        return False
    return Path(path).is_dir()
