from __future__ import annotations

__all__ = [
    "MAP_STEM_RE",
    "CachedEnum",
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
from dataclasses import dataclass, field
from pathlib import Path

import bpy
from mathutils import Vector

from soulstruct.containers import Binder
from soulstruct.utilities.maths import Vector3


MAP_STEM_RE = re.compile(r"^m(?P<area>\d\d)_(?P<block>\d\d)_(?P<cc>\d\d)_(?P<dd>\d\d)$")


@dataclass(slots=True, frozen=True)
class CachedEnum:
    """Cache enum values by a game and/or project path."""

    import_path_1: Path | None = None
    import_path_2: Path | None = None
    items: list[tuple[str, str, str]] = field(default_factory=lambda: [("0", "None", "None")])

    def __post_init__(self):
        """Adds 'None' default value to start of list."""
        if not self.items:
            object.__setattr__(self, "items", [("0", "None", "None")])
        elif self.items[0] != ("0", "None", "None"):
            self.items.insert(0, ("0", "None", "None"))

    def is_valid(self, import_path_1: Path | None, import_path_2: Path | None) -> bool:
        """Compares both import paths to ensure they are the same as those used to create this CachedEnum."""
        return self.import_path_1 == import_path_1 and self.import_path_2 == import_path_2

    @classmethod
    def from_loose_files(
        cls,
        scan_directory_1: Path | None,
        scan_directory_2: Path | None,
        glob: str,
        use_value_source_suffix=True,
        desc_callback: tp.Callable[[str], str] = None,
    ) -> CachedEnum:
        """Scan a directory for files and cache them by path."""
        items_1 = []
        if is_path_and_dir(scan_directory_1):
            for f in (file for file in sorted(scan_directory_1.glob(glob)) if file.is_file()):
                minimal_stem = f.name.split(".")[0]
                desc = minimal_stem if desc_callback is None else desc_callback(minimal_stem)
                items_1.append((str(f), minimal_stem, desc))

        if is_path_and_dir(scan_directory_2):
            items_2 = []
            for f in (file for file in sorted(scan_directory_2.glob(glob)) if file.is_file()):
                minimal_stem = f.name.split(".")[0]
                desc = minimal_stem if desc_callback is None else desc_callback(minimal_stem)
                items_2.append((str(f), minimal_stem, desc))
            # Items that appear in only one source list have suffixes added to their names, their descriptions, and (by
            # default) their values. Common items appear first, followed by (G) items and (P) items.
            items = []
            common_items = set([f[0] for f in items_1]).intersection(set([f[0] for f in items_2]))

            for item in items_1:
                if item[0] in common_items:
                    items.append(item)  # as is
                else:
                    # Add game-only suffix.
                    items.append((
                        f"{item[0]} (G)" if use_value_source_suffix else item[0],
                        f"{item[1]} (G)",
                        f"{item[2]} (in game only)"
                    ))
            for item in items_2:
                if item[0] not in common_items:
                    # Add project-only suffix.
                    items.append((
                        f"{item[0]} (P)" if use_value_source_suffix else item[0],
                        f"{item[1]} (P)",
                        f"{item[2]} (in project only)"
                    ))
        else:
            items = items_1

        return CachedEnum(scan_directory_1, scan_directory_2, items)

    @classmethod
    def from_binder_entries(
        cls,
        binder_path_1: Path | None,
        binder_path_2: Path | None,
        entry_name_pattern: re.Pattern,
        use_value_source_suffix=True,
        desc_callback: tp.Callable[[str], str] = None,
    ) -> CachedEnum:
        """Scan a Binder's entries and cache them by path."""

        items_1 = []
        if binder_path_1.is_file():
            binder_1 = Binder.from_path(binder_path_1)
            for e in binder_1.find_entries_matching_name(entry_name_pattern):
                desc = e.minimal_stem if desc_callback is None else desc_callback(e.minimal_stem)
                items_1.append((e.name, e.minimal_stem, desc))

        if is_path_and_file(binder_path_2):
            binder_2 = Binder.from_path(binder_path_2)
            items_2 = []
            for e in binder_2.find_entries_matching_name(entry_name_pattern):
                desc = e.minimal_stem if desc_callback is None else desc_callback(e.minimal_stem)
                items_2.append((e.name, e.minimal_stem, desc))

            # Items that appear in only one source list have suffixes added to their names, their descriptions, and (by
            # default) their values. Common items appear first, followed by (G) items and (P) items.
            items = []
            common_values = set([f[0] for f in items_1]).intersection(set([f[0] for f in items_2]))

            for item in items_1:
                if item[0] in common_values:
                    items.append(item)  # as is
                else:
                    # Add game-only suffix.
                    items.append(
                        (
                            f"{item[0]} (G)" if use_value_source_suffix else item[0],
                            f"{item[1]} (G)",
                            f"{item[2]} (in game only)"
                        )
                    )
            for item in items_2:
                if item[0] not in common_values:
                    # Add project-only suffix.
                    items.append(
                        (
                            f"{item[0]} (P)" if use_value_source_suffix else item[0],
                            f"{item[1]} (P)",
                            f"{item[2]} (in project only)"
                        )
                    )

        else:
            items = items_1

        return CachedEnum(binder_path_1, binder_path_2, items)


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


def atoi(text: str):
    return int(text) if text.isdigit() else text


def natural_keys(text: str):
    """Key for `sorted` or `list.sort()` to sort in human/natural order (preserve numeric chunks).

    See: http://nedbatchelder.com/blog/200712/human_sorting.html
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
