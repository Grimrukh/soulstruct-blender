from __future__ import annotations

__all__ = ["GameFiles"]

import re

import typing as tp
from pathlib import Path

import bpy

from soulstruct.containers import Binder
from soulstruct.darksouls1ptde.constants import CHARACTER_MODELS as DS1_CHARACTER_MODELS
from soulstruct.darksouls1r.maps import MSB

from .cached import get_cached_file
from .core import GlobalSettings, GameNames

# Global variable to keep enum references alive, and the paths used to cache them.
GAME_FILE_ENUMS = {
    "MAP_PIECE": (None, [("0", "None", "None")]),
    "CHRBND": (None, [("0", "None", "None")]),
    "OBJBND": (None, [("0", "None", "None")]),
    "NVM": (None, [("0", "None", "None")]),
    "HKX_MAP_COLLISION": (None, [("0", "None", "None")]),
}  # type: dict[str, tuple[None | Path, list[tuple[str, str, str]]]]


# noinspection PyUnusedLocal
def get_game_map_piece_items(self, context):
    """Collect quick-importable map pieces, which could be:
        - FLVERs in selected game's selected 'map/mAA_BB_CC_DD' directory
        - or `MSBMapPiece` parts in the selected game's selected map MSB.
    """
    settings = GlobalSettings.get_scene_settings(context)
    game_directory = settings.game_directory
    map_stem = settings.map_stem
    if not game_directory or map_stem in {"", "0"}:
        return _clear_items("MAP_PIECE")

    if settings.msb_import_mode:
        # Open MSB and find all Map Piece parts. NOTE: We don't check here if the part's model is a valid file.
        # It's up to the importer to handle and report that error case.
        msb_path = Path(game_directory, "map/MapStudio", f"{map_stem}.msb")

        if GAME_FILE_ENUMS["MAP_PIECE"][0] == msb_path:
            # Use cached enum items.
            # NOTE: Even if the MSB is written from Blender, Soulstruct cannot add or remove parts (yet).
            return GAME_FILE_ENUMS["MAP_PIECE"][1]

        try:
            msb_class = GlobalSettings.get_game_msb_class(context)
            msb = get_cached_file(msb_path, msb_class)
        except (FileNotFoundError, ValueError) as ex:
            return _clear_items("MAP_PIECE")
        msb: MSB  # TODO: hack to get standard part lists

        items = [("0", "None", "None")]
        for map_piece_part in msb.map_pieces:
            if not map_piece_part.model:
                continue
            full_model_name = map_piece_part.model.name + f"A{map_stem[1:3]}"
            identifier = f"{map_piece_part.name}|{full_model_name}"
            items.append(
                (identifier, map_piece_part.name, f"{map_piece_part.name} (Model {full_model_name})")
            )

        # NOTE: The cache key is the MSB path.
        GAME_FILE_ENUMS["MAP_PIECE"] = (msb_path, items)
        return GAME_FILE_ENUMS["MAP_PIECE"][1]

    # Find all map piece FLVER files in map directory.
    scan_directory = Path(game_directory, "map", map_stem)
    if not scan_directory.is_dir():
        return _clear_items("MAP_PIECE")
    flver_glob = "*.flver"
    if settings.resolve_dcx_type("Auto", "FLVER", False, context).has_dcx_extension():
        flver_glob += ".dcx"
    return _scan_loose_files("MAP_PIECE", scan_directory, flver_glob, lambda stem: f"{stem} in map {map_stem}")


# noinspection PyUnusedLocal
def get_chrbnd_items(self, context):
    """Collect CHRBNDs in selected game's s 'chr' directory."""
    settings = GlobalSettings.get_scene_settings(context)
    game_directory = settings.game_directory
    if not game_directory:
        return _clear_items("CHRBND")
    scan_directory = Path(game_directory, "chr")
    if not scan_directory.is_dir():
        return _clear_items("CHRBND")
    chrbnd_glob = "*.chrbnd"
    if settings.resolve_dcx_type("Auto", "Binder", False, context).has_dcx_extension():
        chrbnd_glob += ".dcx"

    if settings.game in {GameNames.PTDE, GameNames.DS1R}:
        # Use DS1 character model names in description.
        def desc_callback(chrbnd_stem: str):
            try:
                return DS1_CHARACTER_MODELS.get(int(chrbnd_stem[1:]), "Unknown")
            except ValueError:
                return "Unknown"
    else:
        def desc_callback(stem: str):
            return f"Character {stem}"

    return _scan_loose_files("CHRBND", scan_directory, chrbnd_glob, desc_callback)


# noinspection PyUnusedLocal
def get_nvm_items(self, context):
    """Collect navmesh NVM entries in selected game map's 'mAA_BB_CC_DD.nvmbnd' binder."""
    settings = GlobalSettings.get_scene_settings(context)
    game_directory = settings.game_directory
    map_stem = settings.map_stem
    if not game_directory or map_stem in {"", "0"}:
        return _clear_items("NVM")
    map_path = Path(game_directory, "map", map_stem)
    if not map_path.is_dir():
        return _clear_items("NVM")
    dcx_type = settings.resolve_dcx_type("Auto", "Binder", False, context)
    nvmbnd_path = dcx_type.process_path(map_path / f"{map_stem}.nvmbnd")
    if not nvmbnd_path.is_file():
        return _clear_items("NVM")

    if settings.msb_import_mode:
        # Open MSB and find all Navmesh parts. NOTE: We don't check here if the part's model is a valid file.
        # It's up to the importer to handle and report that error case.
        msb_path = Path(game_directory, "map/MapStudio", f"{map_stem}.msb")

        if GAME_FILE_ENUMS["NVM"][0] == msb_path:
            # Use cached enum items.
            # NOTE: Even if the MSB is written from Blender, Soulstruct cannot add or remove parts (yet).
            return GAME_FILE_ENUMS["NVM"][1]

        try:
            msb_class = GlobalSettings.get_game_msb_class(context)
            msb = get_cached_file(msb_path, msb_class)
        except (FileNotFoundError, ValueError) as ex:
            return _clear_items("NVM")
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
        GAME_FILE_ENUMS["NVM"] = (msb_path, items)
        return GAME_FILE_ENUMS["NVM"][1]

    # Find all NVM entries in map NVMBND.
    if settings.resolve_dcx_type("Auto", "NVM", True, context).has_dcx_extension():
        pattern = re.compile(r".*\.nvm\.dcx")
    else:
        pattern = re.compile(r".*\.nvm")
    return _scan_binder_entries("NVM", nvmbnd_path, pattern)


# noinspection PyUnusedLocal
def get_hkx_map_collision_items(self, context):
    """Collect (hi-res) map collision HKX entries in selected game map's 'hAA_BB_CC_DD.hkxbhd' binder."""
    settings = GlobalSettings.get_scene_settings(context)
    game_directory = settings.game_directory
    map_stem = settings.map_stem
    if not game_directory or map_stem in {"", "0"}:
        return _clear_items("HKX_MAP_COLLISION")
    map_path = Path(game_directory, "map", map_stem)
    if not map_path.is_dir():
        return _clear_items("HKX_MAP_COLLISION")
    hkxbhd_path = map_path / f"h{map_stem[1:]}.hkxbhd"  # never DCX
    if not hkxbhd_path.is_file():
        return _clear_items("HKX_MAP_COLLISION")

    if settings.msb_import_mode:
        # Open MSB and find all Collision parts. NOTE: We don't check here if the part's model is a valid file.
        # It's up to the importer to handle and report that error case.
        msb_path = Path(game_directory, "map/MapStudio", f"{map_stem}.msb")

        if GAME_FILE_ENUMS["HKX_MAP_COLLISION"][0] == msb_path:
            # Use cached enum items.
            # NOTE: Even if the MSB is written from Blender, Soulstruct cannot add or remove parts (yet).
            return GAME_FILE_ENUMS["HKX_MAP_COLLISION"][1]

        try:
            msb_class = GlobalSettings.get_game_msb_class(context)
            msb = get_cached_file(msb_path, msb_class)
        except (FileNotFoundError, ValueError) as ex:
            return _clear_items("HKX_MAP_COLLISION")
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
        GAME_FILE_ENUMS["HKX_MAP_COLLISION"] = (msb_path, items)
        return GAME_FILE_ENUMS["HKX_MAP_COLLISION"][1]

    hkx_dcx_type = settings.resolve_dcx_type("Auto", "MapCollisionHKX", True, context)
    pattern = re.compile(r"h.*\.hkx\.dcx") if hkx_dcx_type.has_dcx_extension() else re.compile(r"h.*\.hkx")
    return _scan_binder_entries("HKX_MAP_COLLISION", hkxbhd_path, pattern)


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


class GameFiles(bpy.types.PropertyGroup):
    """Files of various types found in the game directory via on-demand scan."""

    map_piece: bpy.props.EnumProperty(
        name="Map Piece",
        items=get_game_map_piece_items,
    )

    chrbnd: bpy.props.EnumProperty(
        name="Character",
        items=get_chrbnd_items,
    )

    # NOTE: Too many objects for an enum choice pop-up to feasibly handle.
    objbnd_name: bpy.props.StringProperty(
        name="Object Name",
        description="Name of OBJBND object file to import",
    )

    nvm: bpy.props.EnumProperty(
        name="DS1 Navmesh",
        items=get_nvm_items,
    )

    hkx_map_collision: bpy.props.EnumProperty(
        name="HKX Map Collision",
        items=get_hkx_map_collision_items,
    )
