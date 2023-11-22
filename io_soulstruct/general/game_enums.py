from __future__ import annotations

__all__ = ["SoulstructGameEnums"]

import re

import typing as tp
from pathlib import Path

import bpy

from soulstruct.containers import Binder
from soulstruct.games import *

from .cached import get_cached_file
from .core import SoulstructSettings

if tp.TYPE_CHECKING:
    from io_soulstruct.type_checking import MSB_TYPING

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
    """Collect quick-importable map piece FLVERs in selected game's selected 'map/mAA_BB_CC_DD' directory.

    TODO: Not used anymore, but leaving this here as a potential future template.
    """
    key = "MAP_PIECE"

    settings = SoulstructSettings.from_context(context)
    map_directory = settings.get_import_map_path()
    if not map_directory or not map_directory.is_dir():
        return _clear_items(key)

    # Find all map piece FLVER files in map directory.
    flver_glob = settings.game.process_dcx_path("*.flver")
    return _scan_loose_files(key, map_directory, flver_glob, lambda stem: f"{stem} in map {settings.map_stem}")


# noinspection PyUnusedLocal
def get_msb_map_piece_items(self, context):
    """Collect quick-importable `MSBMapPiece` parts in the selected game's selected map MSB.

    TODO: Many MSBs, especially in later games, have too many Map Piece parts to reasonably display in Blender's limited
     enum pop-up window. I'm thinking of writing all the parts as file names to a temporarily folder and then using the
     file browser to select one of those, then deleting the temp folder afterward.
    """
    key = "MSB_MAP_PIECE"

    settings = SoulstructSettings.from_context(context)
    msb_path = settings.get_import_msb_path()
    if not msb_path or not msb_path.is_file():
        return _clear_items(key)

    # Open MSB and find all Map Piece parts. NOTE: We don't check here if the part's model is a valid file.
    # It's up to the importer to handle and report that error case.
    if GAME_FILE_ENUMS[key][0] == msb_path:
        # Use cached enum items.
        # NOTE: Even if the MSB is written from Blender, Soulstruct cannot add or remove parts (yet).
        return GAME_FILE_ENUMS[key][1]

    try:
        msb_class = settings.get_game_msb_class()
        msb = get_cached_file(msb_path, msb_class)  # type: MSB_TYPING
    except (FileNotFoundError, ValueError) as ex:
        return _clear_items(key)

    items = [("0", "None", "None")]
    for map_piece_part in msb.map_pieces:
        if not map_piece_part.model:
            continue
        full_model_name = map_piece_part.model.get_model_file_stem(settings.map_stem)
        identifier = f"{map_piece_part.name}|{full_model_name}"
        items.append(
            (identifier, map_piece_part.name, f"{map_piece_part.name} (Model {full_model_name})")
        )

    # NOTE: The cache key is the MSB path.
    GAME_FILE_ENUMS[key] = (msb_path, items)
    return GAME_FILE_ENUMS[key][1]


# noinspection PyUnusedLocal
def get_nvm_items(self, context):
    """Collect navmesh NVM entries in selected game map's 'mAA_BB_CC_DD.nvmbnd' binder."""
    key = "NVM"

    settings = SoulstructSettings.from_context(context)
    map_path = settings.get_import_map_path()
    if not map_path or not map_path.is_dir():
        return _clear_items(key)
    nvmbnd_path = settings.game.process_dcx_path(map_path / f"{settings.map_stem}.nvmbnd")
    if not nvmbnd_path.is_file():
        return _clear_items(key)

    # Find all NVM entries in map NVMBND. (Never compressed.)
    pattern = re.compile(r".*\.nvm$")
    return _scan_binder_entries(key, nvmbnd_path, pattern)


# noinspection PyUnusedLocal
def get_nvm_part_items(self, context):
    """Collect MSB Navmesh entries in selected game map's MSB.

    TODO: See Map Pieces above re: too many parts to display.
    """
    key = "MSB_NAVMESH"

    settings = SoulstructSettings.from_context(context)
    msb_path = settings.get_import_msb_path()
    if not msb_path or not msb_path.is_file():
        return _clear_items(key)

    # Open MSB and find all Map Piece parts. NOTE: We don't check here if the part's model is a valid file.
    # It's up to the importer to handle and report that error case.
    if GAME_FILE_ENUMS[key][0] == msb_path:
        # Use cached enum items.
        # NOTE: Even if the MSB is written from Blender, Soulstruct cannot add or remove parts (yet).
        return GAME_FILE_ENUMS[key][1]

    try:
        msb_class = settings.get_game_msb_class()
        msb = get_cached_file(msb_path, msb_class)  # type: MSB_TYPING
    except (FileNotFoundError, ValueError) as ex:
        return _clear_items(key)

    items = [("0", "None", "None")]
    for navmesh_part in msb.navmeshes:
        if not navmesh_part.model:
            continue
        full_model_name = navmesh_part.model.get_model_file_stem(settings.map_stem)
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

    settings = SoulstructSettings.from_context(context)
    map_path = settings.get_import_map_path()
    if not map_path or not map_path.is_dir():
        return _clear_items(key)

    match settings.game:
        case {"name": DARK_SOULS_PTDE.name}:
            # Loose HKX files. TODO: Need code for finding adjacent loose lo-res collisions as well.
            # TODO: Easily found, but I haven't finished map collision support for Havok 2010 yet.
            #  Just need to set up the SS Havok class and test the packfile writing.
            # return _scan_loose_files(key, map_path, "h*.hkx")
            return _clear_items(key)
        case {"name": DARK_SOULS_DSR.name}:
            # Compressed HKX files inside HKXBHD binder.
            hkxbhd_path = settings.game.process_dcx_path(map_path / f"h{settings.map_stem[1:]}.hkxbhd")
            if not hkxbhd_path.is_file():
                return _clear_items(key)
            pattern = re.compile(r".*\.hkx.dcx")
            return _scan_binder_entries(key, hkxbhd_path, pattern)

    # TODO: HKX collision not supported for other games. Not sure if I can handle `hkcdSimdTree` yet.
    return _clear_items(key)


# noinspection PyUnusedLocal
def get_msb_hkx_map_collision_items(self, context):
    """Collect `MSBCollision` parts from selected game map's MSB."""
    key = "MSB_HKX_MAP_COLLISION"

    settings = SoulstructSettings.from_context(context)
    msb_path = settings.get_import_msb_path()
    if not msb_path or not msb_path.is_file():
        return _clear_items(key)

    # Open MSB and find all Map Piece parts. NOTE: We don't check here if the part's model is a valid file.
    # It's up to the importer to handle and report that error case.
    if GAME_FILE_ENUMS[key][0] == msb_path:
        # Use cached enum items.
        # NOTE: Even if the MSB is written from Blender, Soulstruct cannot add or remove parts (yet).
        return GAME_FILE_ENUMS[key][1]

    try:
        msb_class = settings.get_game_msb_class()
        msb = get_cached_file(msb_path, msb_class)  # type: MSB_TYPING
    except (FileNotFoundError, ValueError) as ex:
        return _clear_items(key)

    items = [("0", "None", "None")]
    for collision_part in msb.collisions:
        if not collision_part.model:
            continue
        full_model_name = collision_part.model.get_model_file_stem(settings.map_stem)
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

    # region Binder Entries

    nvm: bpy.props.EnumProperty(
        name="DS1 Navmesh",
        items=get_nvm_items,
    )

    hkx_map_collision: bpy.props.EnumProperty(
        name="HKX Map Collision",
        items=get_hkx_map_collision_items,
    )

    # endregion

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
