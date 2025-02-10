from __future__ import annotations

__all__ = [
    "MAP_STEM_RE",
    "BLENDER_DUPE_RE",
    "MapStem",
    "get_bl_custom_prop",
    "is_uniform",
    "get_or_create_collection",
    "is_path_and_file",
    "is_path_and_dir",
    "get_bl_obj_tight_name",
    "get_collection_map_stem",
    "remove_dupe_suffix",
    "replace_shared_prefix",
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


def get_or_create_collection(
    root_collection: bpy.types.Collection,
    *names: str,
    hide_viewport=False,
) -> bpy.types.Collection:
    """Find or create Collection `names[-1]`. If it doesn't exist, create it, nested inside the given `names` hierarchy,
    starting at `root_collection`.

    `hide_viewport` is only used if a new Collection is created.
    """
    names = list(names)
    if not names:
        raise ValueError("At least one Collection name must be provided.")
    target_name = names.pop()
    try:
        return bpy.data.collections[target_name]
    except KeyError:
        collection = bpy.data.collections.new(target_name)
        # TODO: Prevents Armatures from being put into Edit mode.
        #  Could temporarily enable collection when needed for new Armature.
        # if hide_viewport:
        #     collection.hide_viewport = True
        if not names:
            # Reached top of hierarchy.
            if root_collection:
                root_collection.children.link(collection)
            return collection
        parent_collection = get_or_create_collection(root_collection, *names, hide_viewport=hide_viewport)
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
    """Get the map stem of the collection that the object is in.

    Supports multiple containing collections as long as only one looks like a map stem.
    """
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


def replace_shared_prefix(old_model_name: str, new_model_name: str, old_instance_name: str) -> str:
    """Find the shared prefix between the old model name and the old instance name, and replace that prefix with the
    same number of characters from the new model name.

    Obviously, there's nothing about this function that is specific to model/instance strings, but that's the main usage
    here and the easiest way to remember the argument order.

    If the old model and instance names are identical -- which should not be possible if the arguments are Blender
    object names -- then `new_model_name` will simply be returned.
    """
    if old_instance_name == old_model_name:
        return new_model_name

    for i, (a, b) in enumerate(zip(old_instance_name, old_model_name)):
        if a != b:
            new_instance_prefix = new_model_name[:i]  # take same length prefix from new model name
            new_instance_suffix = old_instance_name[i:]  # keep old suffix ('_0000', '_CASTLE', whatever).
            return f"{new_instance_prefix}{new_instance_suffix}"

    # This should not be reachable, as we already checked if the old names were identical. Just in case, we won't
    # change the name.
    return old_instance_name
