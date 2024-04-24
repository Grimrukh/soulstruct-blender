from __future__ import annotations

__all__ = [
    "get_dungeons_to_overworld_dict",
]

import ast
import csv
import json
import typing as tp
from pathlib import Path

from soulstruct.eldenring.params.paramdef import WORLD_MAP_LEGACY_CONV_PARAM_ST
from soulstruct.utilities.maths import Vector3
from soulstruct.utilities.files import write_json

ER_GRID_ORIGIN = (46, 49)  # (x, z) in small tile grid coordinates (center of Erdtree picture on world map)

# No need to recompute this in 99% of cases.
_CACHED_DUNGEONS_TO_OVERWORLD_DICT = None  # type: tp.Optional[dict[str, list[tuple[str, Vector3 | None, Vector3]]]]


class Vector3_JSONEncoder(json.JSONEncoder):
    """Converts Vector3 to list."""
    def default(self, obj):
        if isinstance(obj, Vector3):
            return list(obj)


def get_dungeons_to_overworld_dict() -> dict[str, list[tuple[str, Vector3 | None, Vector3]]]:
    """Use baked `WorldMapLegacyConvParam` Param to build a dictionary that maps dungeon map stems to a list of small
    overworld map tiles they connect to, with the source connection point (often the dungeon entrance) and the delta
    translation that should be applied to move that dungeon to that tile's coordinates (NOT world coordinates).

    Some dungeons only connect to other dungeons, not directly to the overworld. In this case, the delta translation is
    computed by chaining through connected dungeons until an overworld tile is reached, but the source connection point
    is not recorded.

    The translation deltas returned are in GAME coordinates (Y is up), not Blender coordinates.

    Fortunately, no rotation is required here.
    """
    global _CACHED_DUNGEONS_TO_OVERWORLD_DICT

    # if _CACHED_DUNGEONS_TO_OVERWORLD_DICT is not None:
    #     return _CACHED_DUNGEONS_TO_OVERWORLD_DICT

    # TODO: Having Elden Ring Param problems, so using a bundled CSV.
    # gameparambnd = GameParamBND.from_encrypted_path(er_regulation_path)
    # conv_param = gameparambnd.get_param("WorldMapLegacyConvParam")  # type: Param[WORLD_MAP_LEGACY_CONV_PARAM_ST]
    # rows = list(conv_param.rows.values())

    rows = _get_dungeons_to_overworld_csv()

    # There are some entries in the Param that we want to ignore. Their original purpose is unknown - maybe just when
    # a dungeon is VISIBLE (but not reachable) from elsewhere.
    restrictions = {
        "m13_00_00_00": "m60_51_43_00",  # Farum Azula connects to Bestial Sanctum ONLY
        "m15_00_00_00": "m60_48_57_00",  # Haligtree connects to Ordina ONLY
    }

    # Two passes: first, implant dungeons into overworld tiles, then implant dungeons into other overworld-implanted
    # dungeons. (For example, Divine Tower of Limgrave connects to Stormveil Castle, which connects to m60_41_38_00...)

    dungeons_to_overworld = {}  # type: dict[str, list[tuple[str, Vector3 | None, Vector3]]]

    # First pass: dungeons to overworld small tiles.
    # Note that some dungeons connect to MULTIPLE tiles. We record all of them here. The resulting 'world' transform,
    # once the tiles are placed on the world grid, should obviously be identical!
    for row in rows:

        source_map_stem = f"m{row.SrcAreaNo}_{row.SrcGridXNo:02}_{row.SrcGridZNo:02}_00"
        dest_map_stem = f"m{row.DstAreaNo}_{row.DstGridXNo:02}_{row.DstGridZNo:02}_00"

        if row.DstAreaNo != 60 or not row.IsBasePoint:
            continue

        if source_map_stem in restrictions and restrictions[source_map_stem] != dest_map_stem:
            continue  # invalid mapping, not sure why it's in the Param

        overworld_connections = dungeons_to_overworld.setdefault(source_map_stem, [])

        source_map_offset = Vector3((row.SrcPosX, row.SrcPosY, row.SrcPosZ))
        dest_map_offset = Vector3((row.DstPosX, row.DstPosY, row.DstPosZ))
        source_to_overworld = dest_map_offset - source_map_offset

        # Dungeon implanted into an overworld tile (always a small tile).
        overworld_connections.append((dest_map_stem, source_map_offset, source_to_overworld))

    # Some dungeons may be "three dungeons deep", e.g. Leyndell -> Shunning-Grounds -> Deeproot Depths.
    # We collect them, then iterate over them until all dungeons have been mapped to a world tile.
    pending_dungeons_to_dungeons_rows = []

    # Second pass: dungeons to other dungeons.
    for row in rows:
        if any(ignore_area in {row.SrcAreaNo, row.DstAreaNo} for ignore_area in (37, 38, 60, 70)):
            continue
        pending_dungeons_to_dungeons_rows.append(row)

    i = 0
    while pending_dungeons_to_dungeons_rows:
        still_pending_dungeons_to_dungeons_rows = []
        for row in pending_dungeons_to_dungeons_rows:

            source_map_stem = f"m{row.SrcAreaNo}_{row.SrcGridXNo:02}_{row.SrcGridZNo:02}_00"
            dest_map_stem = f"m{row.DstAreaNo}_{row.DstGridXNo:02}_{row.DstGridZNo:02}_00"

            if source_map_stem in dungeons_to_overworld:
                continue  # already mapped to overworld

            if dest_map_stem not in dungeons_to_overworld:
                # Try again next time, maybe this chain will complete.
                still_pending_dungeons_to_dungeons_rows.append(row)
                print(f"    Can't yet resolve {source_map_stem} -> {dest_map_stem} mapping.")
                continue

            # Success! Calculate the mapping up to the overworld.

            # We just use the FIRST connection to a tile.
            overworld_map_stem, _, dest_to_overworld = dungeons_to_overworld[dest_map_stem][0]
            source_map_offset = Vector3((row.SrcPosX, row.SrcPosY, row.SrcPosZ))
            dest_map_offset = Vector3((row.DstPosX, row.DstPosY, row.DstPosZ))

            source_to_dest = dest_map_offset - source_map_offset

            # Add that translation to the source map's translation into the overworld.
            # We don't record a source offset, though, as for dungeon-to-dungeon connections, it seems to often be
            # fairly meaningless.
            source_to_overworld = source_to_dest + dest_to_overworld
            dungeons_to_overworld[source_map_stem] = [(overworld_map_stem, None, source_to_overworld)]

        pending_dungeons_to_dungeons_rows = still_pending_dungeons_to_dungeons_rows
        print(f"Finished dungeon map chaining: {i}. Remaining rows: {len(pending_dungeons_to_dungeons_rows)}")
        i += 1

    # Add a few manual connections for weird maps.

    # Ending Cutscenes (in Ashen Leyndell)
    dungeons_to_overworld["m11_71_00_00"] = dungeons_to_overworld["m11_05_00_00"].copy()

    # Royal Colosseum
    leyndell_dest, _, leyndell_to_overworld = dungeons_to_overworld["m11_00_00_00"][0]
    colosseum_to_leyndell = Vector3((-359.44, 32.74, -492.72))
    dungeons_to_overworld["m45_00_00_00"] = [(leyndell_dest, _, colosseum_to_leyndell + leyndell_to_overworld)]

    # Caelid Colosseum
    dungeons_to_overworld["m45_01_00_00"] = [("m60_47_42_00", _, Vector3((-2.34, 150.4, -43.36)))]

    # Limgrave Colosseum
    dungeons_to_overworld["m45_02_00_00"] = [("m60_42_40_00", _, Vector3((-24.47, 208.82, -66.69)))]

    # Sort keys.
    dungeons_to_overworld = dict(sorted(dungeons_to_overworld.items()))

    _CACHED_DUNGEONS_TO_OVERWORLD_DICT = dungeons_to_overworld

    # Write JSON.
    # write_json(
    #     Path("~/dungeons_to_overworld.json").expanduser(),
    #     _CACHED_DUNGEONS_TO_OVERWORLD_DICT,
    #     indent=4,
    #     encoder=Vector3_JSONEncoder,
    # )

    return dungeons_to_overworld


def _get_dungeons_to_overworld_csv() -> list[WORLD_MAP_LEGACY_CONV_PARAM_ST]:
    csv_path = Path(__file__).parent / "WorldMapLegacyConvParam.csv"
    metadata = WORLD_MAP_LEGACY_CONV_PARAM_ST.get_all_field_metadata()
    param_rows = []
    with csv_path.open("r", newline="") as csv_file:
        conv_param_csv = csv.reader(csv_file, delimiter=";")
        header = []
        for row in conv_param_csv:
            if not header:
                header = row
            else:
                row_dict = {}
                for field, value in zip(header, row):
                    row_dict[field] = value
                row_id = row_dict.pop("Row ID")
                row_name = row_dict.pop("Row Name")
                typed_dict = {}
                for key, value_str in row_dict.items():
                    key = f"{key[0].upper()}{key[1:].replace('_', '')}"
                    py_type = metadata[key].game_type  # always a Python primitive here
                    typed_dict[key] = py_type(ast.literal_eval(value_str))
                param_row = WORLD_MAP_LEGACY_CONV_PARAM_ST(Name=row_name, **typed_dict)
                param_rows.append(param_row)

    return param_rows