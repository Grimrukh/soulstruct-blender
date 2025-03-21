from __future__ import annotations

__all__ = [
    "MAP_STEM_RE",
    "BLENDER_DUPE_RE",
    "MapStem",
    "CheckDCXMode",
    "get_bl_custom_prop",
    "is_uniform",
    "is_path_and_file",
    "is_path_and_dir",
    "get_collection_map_stem",
    "remove_dupe_suffix",
    "replace_shared_prefix",
    "get_model_name",
]

import math
import re
import typing as tp
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import bpy
from mathutils import Vector
from soulstruct.utilities.maths import Vector3

MAP_STEM_RE = re.compile(r"^m(?P<area>\d\d)_(?P<block>\d\d)_(?P<cc>\d\d)_(?P<dd>\d\d)$")
BLENDER_DUPE_RE = re.compile(r"^(.*)\.(\d+)$")


@dataclass(slots=True, frozen=True)
class MapStem:
    aa: int
    bb: int
    cc: int
    dd: int

    @tp.overload
    def __init__(self, map_stem_str: str):
        ...

    @tp.overload
    def __init__(self, aa: int, bb: int, cc: int, dd: int):
        ...

    def __init__(self, *args):
        """Can be initialized with a map stem string or four integers."""
        if len(args) == 1:
            for key, value in zip(("aa", "bb", "cc", "dd"), self.string_to_ints(args[0])):
                object.__setattr__(self, key, value)
        elif len(args) == 4:
            for key, value in zip(("aa", "bb", "cc", "dd"), args):
                object.__setattr__(self, key, value)
        else:
            raise ValueError("Expected either a map stem string or four integers.")

    # region Component Aliases

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

    # endregion

    @staticmethod
    def string_to_ints(map_stem: str) -> tuple[int, int, int, int]:
        match = MAP_STEM_RE.match(map_stem)
        if match is None:
            raise ValueError(f"Map stem '{map_stem}' does not match expected pattern.")
        return (
            int(match.group("area")),
            int(match.group("block")),
            int(match.group("cc")),
            int(match.group("dd")),
        )

    def __eq__(self, other: MapStem) -> bool:
        return all(getattr(self, key) == getattr(other, key) for key in ("aa", "bb", "cc", "dd"))

    def __hash__(self) -> int:
        return hash((self.aa, self.bb, self.cc, self.dd))

    def __iter__(self) -> tp.Iterator[int]:
        return iter((self.aa, self.bb, self.cc, self.dd))

    def __str__(self) -> str:
        return f"m{self.aa:02d}_{self.bb:02d}_{self.cc:02d}_{self.dd:02d}"

    def __repr__(self) -> str:
        return f"MapStem({self.aa}, {self.bb}, {self.cc}, {self.dd})"


class CheckDCXMode(Enum):
    """Used as a variable to determine whether to check some disk source for DCX and/or non-DCX files."""
    BOTH = 0
    DCX_ONLY = 1
    NO_DCX = 2

    def get_paths(self, path: Path) -> list[Path]:
        """Get paths with and/or without '.dcx' extension."""
        if self == CheckDCXMode.DCX_ONLY:
            return [path.with_suffix(f"{path.suffix}.dcx")]
        if self == CheckDCXMode.NO_DCX:
            return [path.with_suffix(f"{path.suffix.removesuffix('.dcx')}")]
        return [path.with_suffix(f"{path.suffix}.dcx"), path.with_suffix(f"{path.suffix.removesuffix('.dcx')}")]

    def get_globs(self, pattern: str) -> list[str]:
        """Get glob patterns with and/or without '.dcx' extension."""
        pattern = pattern.removesuffix(".dcx")
        if self == CheckDCXMode.DCX_ONLY:
            return [pattern + ".dcx"]
        if self == CheckDCXMode.NO_DCX:
            return [pattern]
        return [pattern + ".dcx", pattern]


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


def get_model_name(name: str) -> str:
    """In this add-on, model names (FLVER, Collision, Navmesh) are always the first part of an object name,
    before the first space and/or period (so we don't have to separately remove a dupe suffix).

    Unlike other game name types, we do NOT support trailing spaces in model names, and such spaces never appear in
    vanilla MSBs.
    """
    return name.split(" ")[0].split(".")[0].strip()
