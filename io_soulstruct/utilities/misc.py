from __future__ import annotations

__all__ = [
    "MAP_STEM_RE",
    "BLENDER_DUPE_RE",
    "MapStem",
    "get_bl_custom_prop",
    "is_uniform",
    "get_collection",
    "is_path_and_file",
    "is_path_and_dir",
    "get_bl_obj_tight_name",
    "get_collection_map_stem",
    "remove_dupe_suffix",
]

import math
import re
import typing as tp
from pathlib import Path

import bpy
from mathutils import Vector
from soulstruct.utilities.maths import Vector3

MAP_STEM_RE = re.compile(r"^m(?P<area>\d\d)_(?P<block>\d\d)_(?P<cc>\d\d)_(?P<dd>\d\d)$")
BLENDER_DUPE_RE = re.compile(r"^(.*)\.(\d+)$")


class MapStem(tp.NamedTuple):
    aa: int
    bb: int
    cc: int
    dd: int

    @property
    def area(self):
        return self.aa

    @property
    def block(self):
        return self.bb

    @property
    def version(self):
        return self.dd

    @property
    def tile_x(self):
        return self.cc

    @property
    def tile_z(self):
        return self.dd

    @classmethod
    def from_string(cls, map_stem: str) -> MapStem:
        match = MAP_STEM_RE.match(map_stem)
        if match is None:
            raise ValueError(f"Map stem '{map_stem}' does not match expected pattern.")
        return cls(
            aa=int(match.group("area")),
            bb=int(match.group("block")),
            cc=int(match.group("cc")),
            dd=int(match.group("dd")),
        )

    def to_string(self) -> str:
        return f"m{self.aa:02d}_{self.bb:02d}_{self.cc:02d}_{self.dd:02d}"


def get_bl_custom_prop(bl_obj, name: str, prop_type: tp.Type, default=None, callback: tp.Callable = None) -> tp.Any:
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


def get_collection(
    name: str,
    parent_collection: bpy.types.Collection = None,
) -> bpy.types.Collection:
    """Find or create collection `name`."""
    try:
        return bpy.data.collections[name]
    except KeyError:
        collection = bpy.data.collections.new(name)
        if parent_collection:
            parent_collection.children.link(collection)
        return collection


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


def get_bl_obj_tight_name(obj: bpy.types.Object, new_ext="") -> str:
    """Simply gets part of string before first space AND first dot, whichever comes first.

    Can optionally add a new extension to the end of the stem.
    """
    return obj.name.split(" ")[0].split(".")[0] + new_ext


def get_collection_map_stem(obj: bpy.types.Object) -> str:
    if not obj.users_collection:
        raise ValueError(f"Object '{obj.name}' is not in any Blender collection.")
    map_stem = None
    for collection in obj.users_collection:
        new_match = MAP_STEM_RE.match(collection.name.split(" ")[0])
        if new_match:
            if map_stem:
                raise ValueError(f"Object '{obj.name}' is in multiple Blender collections that match map stem pattern.")
            map_stem = collection.name.split(" ")[0]
    if not map_stem:
        raise ValueError(f"Object '{obj.name}' is not in a Blender collection that matches map stem pattern.")
    return map_stem


def remove_dupe_suffix(name):
    match = BLENDER_DUPE_RE.match(name)
    return match.group(1) if match else name
