from __future__ import annotations

__all__ = ["SoulstructGameEnums"]

import re

import typing as tp
from pathlib import Path

import bpy

from soulstruct.containers import Binder
from soulstruct.darksouls1ptde.constants import CHARACTER_MODELS as DS1_CHARACTER_MODELS
from soulstruct.darksouls1r.maps import MSB

from .cached import get_cached_file
from .core import SoulstructSettings, BlenderGame

# Global variable to keep enum references alive, and the paths used to cache them.
# NOTE: Only Binder entries are used at the moment.
GAME_FILE_ENUMS = {
    # Loose files
    "MAP_PIECE": (None, [("0", "None", "None")]),
    "CHRBND": (None, [("0", "None", "None")]),
    "OBJBND": (None, [("0", "None", "None")]),
    "PARTSBND": (None, [("0", "None", "None")]),

    # Loose Binder entries
    "NVM": (None, [("0", "None", "None")]),  # entries in NVMBND
    "HKX_MAP_COLLISION": (None, [("0", "None", "None")]),  # entries in HKXBHD

    # MSB parts
    "MSB_MAP_PIECE": (None, [("0", "None", "None")]),
    "MSB_NAVMESH": (None, [("0", "None", "None")]),
    "MSB_HKX_MAP_COLLISION": (None, [("0", "None", "None")]),

}  # type: dict[str, tuple[None | Path, list[tuple[str, str, str]]]]


# noinspection PyUnusedLocal
def get_map_piece_items(self, context):
    """Collect quick-importable map piece FLVERs in selected game's selected 'map/mAA_BB_CC_DD' directory."""
    key = "MAP_PIECE"

    settings = SoulstructSettings.get_scene_settings(context)
    game_directory = settings.game_directory
    map_stem = settings.map_stem
    if not game_directory or map_stem in {"", "0"}:
        return _clear_items(key)

    # Find all map piece FLVER files in map directory.
    scan_directory = Path(game_directory, "map", map_stem)
    if not scan_directory.is_dir():
        return _clear_items(key)
    flver_glob = "*.flver"
    if settings.resolve_dcx_type("Auto", "FLVER", False, context).has_dcx_extension():
        flver_glob += ".dcx"
    return _scan_loose_files(key, scan_directory, flver_glob, lambda stem: f"{stem} in map {map_stem}")


# noinspection PyUnusedLocal
def get_msb_map_piece_items(self, context):
    """Collect quick-importable `MSBMapPiece` parts in the selected game's selected map MSB."""
    key = "MSB_MAP_PIECE"

    settings = SoulstructSettings.get_scene_settings(context)
    game_directory = settings.game_directory
    map_stem = settings.map_stem
    if not game_directory or map_stem in {"", "0"}:
        return _clear_items(key)

    # Open MSB and find all Map Piece parts. NOTE: We don't check here if the part's model is a valid file.
    # It's up to the importer to handle and report that error case.
    msb_dcx_type = settings.resolve_dcx_type("Auto", "MSB", False, context)
    msb_path = msb_dcx_type.process_path(Path(game_directory, "map/MapStudio", f"{map_stem}.msb"))

    if GAME_FILE_ENUMS[key][0] == msb_path:
        # Use cached enum items.
        # NOTE: Even if the MSB is written from Blender, Soulstruct cannot add or remove parts (yet).
        return GAME_FILE_ENUMS[key][1]

    try:
        msb_class = SoulstructSettings.get_game_msb_class(context)
        msb = get_cached_file(msb_path, msb_class)
    except (FileNotFoundError, ValueError) as ex:
        return _clear_items(key)
    msb: MSB  # TODO: hack to get standard part lists

    items = [("0", "None", "None")]
    for map_piece_part in msb.map_pieces:
        if not map_piece_part.model:
            continue
        full_model_name = map_piece_part.model.get_model_file_stem(map_stem)
        identifier = f"{map_piece_part.name}|{full_model_name}"
        items.append(
            (identifier, map_piece_part.name, f"{map_piece_part.name} (Model {full_model_name})")
        )

    # NOTE: The cache key is the MSB path.
    GAME_FILE_ENUMS[key] = (msb_path, items)
    return GAME_FILE_ENUMS[key][1]


# noinspection PyUnusedLocal
def get_chrbnd_items(self, context):
    """Collect CHRBNDs in selected game's s 'chr' directory."""
    key = "CHRBND"

    settings = SoulstructSettings.get_scene_settings(context)
    game_directory = settings.game_directory
    if not game_directory:
        return _clear_items(key)
    scan_directory = Path(game_directory, "chr")
    if not scan_directory.is_dir():
        return _clear_items(key)
    chrbnd_glob = "*.chrbnd"
    if settings.resolve_dcx_type("Auto", "Binder", False, context).has_dcx_extension():
        chrbnd_glob += ".dcx"

    if settings.game in {BlenderGame.PTDE, BlenderGame.DS1R}:
        # Use DS1 character model names in description.
        def desc_callback(chrbnd_stem: str):
            try:
                return DS1_CHARACTER_MODELS.get(int(chrbnd_stem[1:]), "Unknown")
            except ValueError:
                return "Unknown"
    else:
        def desc_callback(stem: str):
            return f"Character {stem}"

    return _scan_loose_files(key, scan_directory, chrbnd_glob, desc_callback)


# noinspection PyUnusedLocal
def get_partsbnd_items(self, context):
    """Collect PARTSBNDs in selected game's s 'parts' directory."""
    key = "PARTSBND"

    settings = SoulstructSettings.get_scene_settings(context)
    game_directory = settings.game_directory
    if not game_directory:
        return _clear_items(key)
    scan_directory = Path(game_directory, "parts")
    if not scan_directory.is_dir():
        return _clear_items(key)
    partsbnd_glob = "*.partsbnd"
    if settings.resolve_dcx_type("Auto", "Binder", False, context).has_dcx_extension():
        partsbnd_glob += ".dcx"

    def desc_callback(stem: str):
        return f"Equipment {stem}"

    return _scan_loose_files(key, scan_directory, partsbnd_glob, desc_callback)


# noinspection PyUnusedLocal
def get_nvm_items(self, context):
    """Collect navmesh NVM entries in selected game map's 'mAA_BB_CC_DD.nvmbnd' binder."""
    key = "NVM"

    settings = SoulstructSettings.get_scene_settings(context)
    game_directory = settings.game_directory
    map_stem = settings.map_stem
    if not game_directory or map_stem in {"", "0"}:
        return _clear_items(key)
    map_path = Path(game_directory, "map", map_stem)
    if not map_path.is_dir():
        return _clear_items(key)
    dcx_type = settings.resolve_dcx_type("Auto", "Binder", False, context)
    nvmbnd_path = dcx_type.process_path(map_path / f"{map_stem}.nvmbnd")
    if not nvmbnd_path.is_file():
        return _clear_items(key)

    # Find all NVM entries in map NVMBND.
    if settings.resolve_dcx_type("Auto", "NVM", True, context).has_dcx_extension():
        pattern = re.compile(r".*\.nvm\.dcx")
    else:
        pattern = re.compile(r".*\.nvm")
    return _scan_binder_entries(key, nvmbnd_path, pattern)


# noinspection PyUnusedLocal
def get_nvm_part_items(self, context):
    """Collect MSB Navmesh entries in selected game map's MSB."""
    key = "MSB_NAVMESH"

    settings = SoulstructSettings.get_scene_settings(context)
    game_directory = settings.game_directory
    map_stem = settings.map_stem
    if not game_directory or map_stem in {"", "0"}:
        return _clear_items(key)
    map_path = Path(game_directory, "map", map_stem)
    if not map_path.is_dir():
        return _clear_items(key)
    dcx_type = settings.resolve_dcx_type("Auto", "Binder", False, context)
    nvmbnd_path = dcx_type.process_path(map_path / f"{map_stem}.nvmbnd")
    if not nvmbnd_path.is_file():
        return _clear_items(key)

    # Open MSB and find all Navmesh parts. NOTE: We don't check here if the part's model is a valid file.
    # It's up to the importer to handle and report that error case.
    msb_path = Path(game_directory, "map/MapStudio", f"{map_stem}.msb")

    if GAME_FILE_ENUMS[key][0] == msb_path:
        # Use cached enum items.
        # NOTE: Even if the MSB is written from Blender, Soulstruct cannot add or remove parts (yet).
        return GAME_FILE_ENUMS[key][1]

    try:
        msb_class = SoulstructSettings.get_game_msb_class(context)
        msb = get_cached_file(msb_path, msb_class)
    except (FileNotFoundError, ValueError) as ex:
        return _clear_items(key)
    msb: MSB  # TODO: hack to get standard part lists

    items = [("0", "None", "None")]
    for navmesh_part in msb.navmeshes:
        if not navmesh_part.model:
            continue
        full_model_name = navmesh_part.model.name + f"A{map_stem[1:3]}"
        identifier = f"{navmesh_part.name}|{full_model_name}"
        items.append(
            (identifier, navmesh_part.name, f"{navmesh_part.name} (Model {full_model_name})")
        )

    # NOTE: The cache key is the MSB path.
    GAME_FILE_ENUMS[key] = (msb_path, items)
    return GAME_FILE_ENUMS[key][1]


# noinspection PyUnusedLocal
def get_hkx_map_collision_items(self, context):
    """Collect (hi-res) map collision HKX entries in selected game map's 'hAA_BB_CC_DD.hkxbhd' binder."""
    key = "HKX_MAP_COLLISION"

    settings = SoulstructSettings.get_scene_settings(context)
    game_directory = settings.game_directory
    map_stem = settings.map_stem
    if not game_directory or map_stem in {"", "0"}:
        return _clear_items(key)
    map_path = Path(game_directory, "map", map_stem)
    if not map_path.is_dir():
        return _clear_items(key)
    hkxbhd_path = map_path / f"h{map_stem[1:]}.hkxbhd"  # never DCX
    if not hkxbhd_path.is_file():
        return _clear_items(key)

    hkx_dcx_type = settings.resolve_dcx_type("Auto", "MapCollisionHKX", True, context)
    pattern = re.compile(r"h.*\.hkx\.dcx") if hkx_dcx_type.has_dcx_extension() else re.compile(r"h.*\.hkx")
    return _scan_binder_entries(key, hkxbhd_path, pattern)


# noinspection PyUnusedLocal
def get_msb_hkx_map_collision_items(self, context):
    """Collect `MSBCollision` parts from selected game map's MSB."""
    key = "MSB_HKX_MAP_COLLISION"

    settings = SoulstructSettings.get_scene_settings(context)
    game_directory = settings.game_directory
    map_stem = settings.map_stem
    if not game_directory or map_stem in {"", "0"}:
        return _clear_items(key)
    map_path = Path(game_directory, "map", map_stem)
    if not map_path.is_dir():
        return _clear_items(key)
    hkxbhd_path = map_path / f"h{map_stem[1:]}.hkxbhd"  # never DCX
    if not hkxbhd_path.is_file():
        return _clear_items(key)

    # Open MSB and find all Collision parts. NOTE: We don't check here if the part's model is a valid file.
    # It's up to the importer to handle and report that error case.
    msb_path = Path(game_directory, "map/MapStudio", f"{map_stem}.msb")

    if GAME_FILE_ENUMS[key][0] == msb_path:
        # Use cached enum items.
        # NOTE: Even if the MSB is written from Blender, Soulstruct cannot add or remove parts (yet).
        return GAME_FILE_ENUMS[key][1]

    try:
        msb_class = SoulstructSettings.get_game_msb_class(context)
        msb = get_cached_file(msb_path, msb_class)
    except (FileNotFoundError, ValueError) as ex:
        return _clear_items(key)
    msb: MSB  # TODO: hack to get standard part lists

    items = [("0", "None", "None")]
    for collision_part in msb.collisions:
        if not collision_part.model:
            continue
        full_model_name = collision_part.model.name + f"A{map_stem[1:3]}"
        identifier = f"{collision_part.name}|{full_model_name}"
        items.append(
            (identifier, collision_part.name, f"{collision_part.name} (Model {full_model_name})")
        )

    # NOTE: The cache key is the MSB path.
    GAME_FILE_ENUMS[key] = (msb_path, items)
    return GAME_FILE_ENUMS[key][1]


def _clear_items(enum_key: str) -> list[tuple[str, str, str]]:
    GAME_FILE_ENUMS[enum_key] = (None, [("0", "None", "None")])
    return GAME_FILE_ENUMS[enum_key][1]


def _scan_loose_files(
    enum_key: str, scan_directory: Path, glob: str, desc_callback: tp.Callable[[str], str] = None,
) -> list[tuple[str, str, str]]:
    """Scan a directory for files and cache them by path."""
    if GAME_FILE_ENUMS[enum_key][0] != scan_directory:
        # Scan and cache.
        items = [("0", "None", "None")]
        for f in scan_directory.glob(glob):
            if f.is_file():
                minimal_stem = f.name.split(".")[0]
                desc = minimal_stem if desc_callback is None else desc_callback(minimal_stem)
                items.append((str(f), minimal_stem, desc))
        GAME_FILE_ENUMS[enum_key] = (scan_directory, items)
    return GAME_FILE_ENUMS[enum_key][1]


def _scan_binder_entries(
    enum_key: str, binder_path: Path, entry_name_pattern: re.Pattern, desc_callback: tp.Callable[[str], str] = None,
) -> list[tuple[str, str, str]]:
    """Scan a Binder's entries and cache them by path."""
    if GAME_FILE_ENUMS[enum_key][0] != binder_path:
        # Scan and cache.
        items = [("0", "None", "None")]
        for e in Binder.from_path(binder_path).find_entries_matching_name(entry_name_pattern):
            desc = e.minimal_stem if desc_callback is None else desc_callback(e.minimal_stem)
            items.append((e.name, e.minimal_stem, desc))
        GAME_FILE_ENUMS[enum_key] = (binder_path, items)
    return GAME_FILE_ENUMS[enum_key][1]


class SoulstructGameEnums(bpy.types.PropertyGroup):
    """Files, Binder entries, and MSB entries of various types found in the game directory via on-demand scan."""

    # map_piece: bpy.props.EnumProperty(
    #     name="Map Piece",
    #     items=get_map_piece_items,
    # )

    # chrbnd: bpy.props.EnumProperty(
    #     name="Character",
    #     items=get_chrbnd_items,
    # )

    # NOTE: Too many objects for an enum choice pop-up to feasibly handle.
    # objbnd_name: bpy.props.StringProperty(
    #     name="Object Name",
    #     description="Name of OBJBND object file to import",
    # )

    # partsbnd: bpy.props.EnumProperty(
    #     name="Equipment",
    #     items=get_partsbnd_items,
    # )

    nvm: bpy.props.EnumProperty(
        name="DS1 Navmesh",
        items=get_nvm_items,
    )

    hkx_map_collision: bpy.props.EnumProperty(
        name="HKX Map Collision",
        items=get_hkx_map_collision_items,
    )

    # region MSB Parts

    map_piece_parts: bpy.props.EnumProperty(
        name="MSB Map Piece Part",
        items=get_msb_map_piece_items,
    )

    nvm_parts: bpy.props.EnumProperty(
        name="MSB Navmesh Part",
        items=get_nvm_part_items,
    )

    hkx_map_collision_parts: bpy.props.EnumProperty(
        name="MSB Map Collision Part",
        items=get_msb_hkx_map_collision_items,
    )

    # endregion
