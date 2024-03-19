from __future__ import annotations

__all__ = [
    "MAP_STEM_RE",
    "CachedEnumItems",
    "get_bl_obj_stem",
    "get_bl_prop",
    "is_uniform",
    "natural_keys",
    "get_collection",
    "is_path_and_file",
    "is_path_and_dir",
    "get_collection_map_stem",
    "find_model_name",
    "process_model_name_map_area",
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

if tp.TYPE_CHECKING:
    from .operators import LoggingOperator


MAP_STEM_RE = re.compile(r"^m(?P<area>\d\d)_(?P<block>\d\d)_(?P<cc>\d\d)_(?P<dd>\d\d)$")


@dataclass(slots=True, frozen=True)
class CachedEnumItems:
    """Cache enum values by a game and/or project path.

    Blender's UI draw method calls dynamic enum item getters *constantly*, not just when, say, the dropdown is clicked.
    Since our enum options often depend on scanning folders or opening Binders, this is unacceptable, so this class
    exists to do Blender's job and cache the results by the paths used to retrieve the items.

    Note that when an enum DOES change, the caller should also reset the selected enum value to 0, generally, as the
    new list of items may be shorter than the old one, causing a ton of "invalid index" warnings in the Blender console.
    """

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
        """Compares both import paths to ensure they are the same as those used to create this CachedEnumItems."""
        return self.import_path_1 == import_path_1 and self.import_path_2 == import_path_2

    @classmethod
    def from_loose_files(
        cls,
        scan_directory_1: Path | None,
        scan_directory_2: Path | None,
        glob: str,
        use_value_source_suffix=True,
        desc_callback: tp.Callable[[str], str] = None,
    ) -> CachedEnumItems:
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

        return CachedEnumItems(scan_directory_1, scan_directory_2, items)

    @classmethod
    def from_binder_entries(
        cls,
        binder_path_1: Path | None,
        binder_path_2: Path | None,
        entry_name_pattern: re.Pattern,
        use_value_source_suffix=True,
        desc_callback: tp.Callable[[str], str] = None,
        is_split_binder=False,
    ) -> CachedEnumItems:
        """Scan a Binder's entries and cache them by path."""
        from io_soulstruct.general.cached import get_cached_file, get_cached_bxf

        items_1 = []
        if is_path_and_file(binder_path_1):
            binder_1 = get_cached_bxf(binder_path_1) if is_split_binder else get_cached_file(binder_path_1, Binder)
            for e in binder_1.find_entries_matching_name(entry_name_pattern):
                desc = e.minimal_stem if desc_callback is None else desc_callback(e.minimal_stem)
                items_1.append((e.name, e.minimal_stem, desc))

        if is_path_and_file(binder_path_2):
            binder_2 = get_cached_bxf(binder_path_2) if is_split_binder else get_cached_file(binder_path_2, Binder)
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

        return CachedEnumItems(binder_path_1, binder_path_2, items)


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


def get_collection(
    name: str,
    parent_collection: bpy.types.Collection = None,
    hide_viewport: bool = False,
) -> bpy.types.Collection:
    """Find or create collection `name`. If created, optionally hides collection in viewport (globally) as well."""
    try:
        return bpy.data.collections[name]
    except KeyError:
        collection = bpy.data.collections.new(name)
        if parent_collection:
            parent_collection.children.link(collection)
        # TODO: `hide_viewport` objbreaks import, as we can't enter Edit Mode.
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


def find_model_name(
    operator: LoggingOperator,
    obj: bpy.types.Object,
    process_default_model_name: tp.Callable[[str], str] = None,
    warn_property_mismatch=True,
) -> str:
    """Try to retrieve the model name from the object's custom properties, falling back to the object's name with
    optional processing. This works the same way for all types of model assets (FLVER, HKK, NVM).

    If the 'Model Name' custom property exists and does NOT match the default model name from the processed object name,
    a warning may be issued with the given `operator`.
    """
    default_model_name = get_bl_obj_stem(obj)
    if process_default_model_name:
        default_model_name = process_default_model_name(default_model_name)

    prop_model_name = obj.get("Model Name", None)
    if warn_property_mismatch and prop_model_name is not None and prop_model_name != default_model_name:
        operator.warning(
            f"Object '{obj.name}' has custom property 'Model Name' set to '{prop_model_name}', but the default "
            f"model name extracted from its Blender name is '{default_model_name}'."
        )

    # NOTE: Will return default model name if property model name is `None` or empty string.
    return prop_model_name or default_model_name


def process_model_name_map_area(map_stem: str, split_underscore=True) -> tp.Callable[[str], str]:
    """Construct a process callback for `find_model_name` that adds the area suffix to the model name if missing.

    If `split_underscore = True` (default), everything at and after the first underscore will also be discarded.

    TODO: Currently assumes DS1 format, i.e. seven characters without area and ten characters with.
    """

    def process_default_model_name(model_name: str) -> str:
        if split_underscore:
            model_name = model_name.split("_")[0]
        if len(model_name) == 7:
            return f"{model_name}A{map_stem[1:3]}"
        print(model_name)
        return model_name

    return process_default_model_name
