from __future__ import annotations

__all__ = [
    "get_dungeons_to_overworld_dict",
]

import ast
import csv
import typing as tp
from pathlib import Path

from soulstruct.eldenring.params.paramdef import WORLD_MAP_LEGACY_CONV_PARAM_ST
from soulstruct.utilities.maths import Vector3

ER_GRID_ORIGIN = (46, 49)  # (x, z) in small tile grid coordinates (center of Erdtree picture on world map)

# No need to recompute this in 99% of cases.
_CACHED_DUNGEONS_TO_OVERWORLD_DICT = None  # type: tp.Optional[dict[str, list[tuple[str, Vector3 | None, Vector3]]]]


# There are some entries in the Param that we want to ignore. Their original purpose is unknown - maybe just when
# a dungeon is VISIBLE (but not reachable) from elsewhere.
RESTRICTIONS = {
    "m13_00_00_00": "m60_51_43_00",  # Farum Azula connects to Bestial Sanctum ONLY
    "m15_00_00_00": "m60_48_57_00",  # Haligtree connects to Ordina ONLY
}


BAKED = {
    "m10_00_00_00": ("m60_39_39_00", Vector3((387.383, 273.608, -282.331))),
    "m10_01_00_00": ("m60_39_39_00", Vector3((-126.617004, 301.608, -82.33099))),
    "m11_00_00_00": ("m60_45_52_00", Vector3((16.679, 1087.521, -120.564))),
    "m11_05_00_00": ("m60_45_52_00", Vector3((16.662003, 1087.521, -120.564))),
    "m11_10_00_00": ("m60_40_35_00", Vector3((-36.017, 86.162, 250.169))),
    "m11_71_00_00": ("m60_45_52_00", Vector3((16.662003, 1087.521, -120.564))),
    "m12_01_00_00": ("m60_38_46_00", Vector3((-311.887, 268.156, 199.37201))),
    "m12_02_00_00": ("m60_48_39_00", Vector3((-1406.311, 418.431, -1667.11))),
    "m12_03_00_00": ("m60_38_46_00", Vector3((2178.7932, 176.91301, 1814.6599))),
    "m12_04_00_00": ("m60_38_46_00", Vector3((-1024, 0, -1280))),
    "m12_05_00_00": ("m60_51_38_00", Vector3((-2000, 370, -1250))),
    "m12_07_00_00": ("m60_48_39_00", Vector3((-1406.311, 418.431, -1667.11))),
    "m12_08_00_00": ("m60_48_39_00", Vector3((-1406.311, 418.431, -1667.11))),
    "m12_09_00_00": ("m60_48_39_00", Vector3((-1406.311, 418.431, -1667.11))),
    "m13_00_00_00": ("m60_51_43_00", Vector3((2472.9001, 1218.4, 668.33))),
    "m14_00_00_00": ("m60_35_45_00", Vector3((-112.058, 310.577, 194.278))),
    "m15_00_00_00": ("m60_48_57_00", Vector3((365.824, 626.76, 550.648))),
    "m16_00_00_00": ("m60_36_53_00", Vector3((11.901999, 978.952, 109.859))),
    "m18_00_00_00": ("m60_42_35_00", Vector3((147, 16, 154))),
    "m19_00_00_00": ("m60_45_52_00", Vector3((16.662003, 1087.521, -120.564))),
    "m20_00_00_00": ("m61_44_43_00", Vector3((108.45, 432.72, -90.97))),  # DLC
    "m20_01_00_00": ("m61_44_45_00", Vector3((128.45, 644.72, -77.97))),  # DLC
    "m21_00_00_00": ("m61_48_47_00", Vector3((50.25, 431, -153))),  # DLC
    "m21_01_00_00": ("m61_48_47_00", Vector3((50.25, 431, -153))),  # DLC
    "m21_02_00_00": ("m61_48_47_00", Vector3((50.25, 431, -153))),  # DLC
    "m22_00_00_00": ("m61_47_35_00", Vector3((512, -435, 112))),  # DLC
    "m25_00_00_00": ("m61_51_46_00", Vector3((-116.29, 467.82, -53.65))),  # DLC
    "m28_00_00_00": ("m61_48_40_00", Vector3((224, -571, 144))),  # DLC
    "m30_00_00_00": ("m60_43_33_00", Vector3((0, 0, 0))),
    "m30_01_00_00": ("m60_45_34_00", Vector3((0, 0, 0))),
    "m30_02_00_00": ("m60_41_37_00", Vector3((0, 0, 0))),
    "m30_03_00_00": ("m60_33_43_00", Vector3((0, 0, 0))),
    "m30_04_00_00": ("m60_43_38_00", Vector3((0, 0, 0))),
    "m30_05_00_00": ("m60_39_48_00", Vector3((0, 0, 0))),
    "m30_06_00_00": ("m60_39_41_00", Vector3((0, 0, 0))),
    "m30_07_00_00": ("m60_37_52_00", Vector3((256, 0, 0))),
    "m30_08_00_00": ("m60_40_52_00", Vector3((0, 0, 0))),
    "m30_09_00_00": ("m60_37_53_00", Vector3((0, 0, 0))),
    "m30_10_00_00": ("m60_45_51_00", Vector3((0, 0, 0))),
    "m30_11_00_00": ("m60_43_39_00", Vector3((0, 0, 0))),
    "m30_12_00_00": ("m60_36_51_00", Vector3((0, 0, 0))),
    "m30_13_00_00": ("m60_45_52_00", Vector3((0, 0, 0))),
    "m30_14_00_00": ("m60_47_40_00", Vector3((0, 0, 0))),
    "m30_15_00_00": ("m60_48_36_00", Vector3((0, 0, 0))),
    "m30_16_00_00": ("m60_52_40_00", Vector3((0, 0, 256))),
    "m30_17_00_00": ("m60_50_53_00", Vector3((0, 0, 0))),
    "m30_18_00_00": ("m60_50_53_00", Vector3((0, 0, 0))),
    "m30_19_00_00": ("m60_49_55_00", Vector3((256, 0, 0))),
    "m30_20_00_00": ("m60_48_53_00", Vector3((256, 0, 256))),
    "m31_00_00_00": ("m60_43_37_00", Vector3((0, 0, 0))),
    "m31_01_00_00": ("m60_44_34_00", Vector3((0, 0, 0))),
    "m31_02_00_00": ("m60_42_33_00", Vector3((0, 0, 0))),
    "m31_03_00_00": ("m60_42_37_00", Vector3((0, 0, 0))),
    "m31_04_00_00": ("m60_39_40_00", Vector3((0, 0, 0))),
    "m31_05_00_00": ("m60_36_41_00", Vector3((256, 0, 0))),
    "m31_06_00_00": ("m60_35_45_00", Vector3((-256, 0, 0))),
    "m31_07_00_00": ("m60_37_53_00", Vector3((0, 0, 0))),
    "m31_09_00_00": ("m60_37_55_00", Vector3((0, 0, 0))),
    "m31_10_00_00": ("m60_51_40_00", Vector3((0, 0, 0))),
    "m31_11_00_00": ("m60_50_39_00", Vector3((0, 0, 0))),
    "m31_12_00_00": ("m60_50_56_00", Vector3((0, 0, 0))),
    "m31_15_00_00": ("m60_41_35_00", Vector3((0, 0, 256))),
    "m31_17_00_00": ("m60_43_39_00", Vector3((0, 0, 0))),
    "m31_18_00_00": ("m60_41_51_00", Vector3((0, 0, 0))),
    "m31_19_00_00": ("m60_37_52_00", Vector3((0, 0, 0))),
    "m31_20_00_00": ("m60_48_39_00", Vector3((0, 0, 0))),
    "m31_21_00_00": ("m60_46_38_00", Vector3((256, 0, 0))),
    "m31_22_00_00": ("m60_53_56_00", Vector3((0, 0, 0))),
    "m32_00_00_00": ("m60_43_33_00", Vector3((0, 0, 0))),
    "m32_01_00_00": ("m60_42_37_00", Vector3((0, 0, 0))),
    "m32_02_00_00": ("m60_36_47_00", Vector3((256, 0, 0))),
    "m32_04_00_00": ("m60_38_52_00", Vector3((256, 0, 256))),
    "m32_05_00_00": ("m60_41_51_00", Vector3((0, 0, 256))),
    "m32_07_00_00": ("m60_46_39_00", Vector3((0, 0, 0))),
    "m32_08_00_00": ("m60_49_39_00", Vector3((0, 0, 0))),
    "m32_11_00_00": ("m60_47_55_00", Vector3((0, 0, 0))),
    "m34_10_00_00": ("m60_39_39_00", Vector3((387.383, 273.608, -282.331))),
    "m34_11_00_00": ("m60_39_44_00", Vector3((-26.6, 400.5, 38.3))),
    "m34_12_00_00": ("m60_43_50_00", Vector3((0, 0, 0))),
    "m34_13_00_00": ("m60_49_41_00", Vector3((0, 0, 0))),
    "m34_14_00_00": ("m60_45_52_00", Vector3((16.662003, 1087.521, -120.564))),
    "m34_15_00_00": ("m60_51_43_00", Vector3((265.20996, 273.78998, 1034.8))),
    "m34_16_00_00": ("m60_39_44_00", Vector3((-26.6, 400.5, 38.3))),
    "m35_00_00_00": ("m60_38_46_00", Vector3((1844.1202, 867.06, 1410.1719))),
    "m39_20_00_00": ("m60_37_50_00", Vector3((48.800003, 165.59998, 1416.6))),
    "m40_00_00_00": ("m61_46_45_00", Vector3((256, 0, 256))),  # DLC
    "m40_01_00_00": ("m61_44_46_00", Vector3((0, 0, 0))),  # DLC
    "m40_02_00_00": ("m61_51_43_00", Vector3((0, 0, 0))),  # DLC
    "m41_00_00_00": ("m61_45_43_00", Vector3((0, 0, 256))),  # DLC
    "m41_01_00_00": ("m61_50_43_00", Vector3((0, 0, 0))),  # DLC
    "m41_02_00_00": ("m61_46_40_00", Vector3((0, 0, 0))),  # DLC
    "m42_00_00_00": ("m61_47_42_00", Vector3((256, 0, 0))),  # DLC
    "m42_02_00_00": ("m61_48_43_00", Vector3((0, 0, 256))),  # DLC
    "m42_03_00_00": ("m61_48_47_00", Vector3((0, 0, 256))),  # DLC
    "m43_00_00_00": ("m61_46_44_00", Vector3((0, 0, 0))),  # DLC
    "m43_01_00_00": ("m61_48_41_00", Vector3((0, 0, 0))),  # DLC
    "m45_00_00_00": ("m60_45_52_00", Vector3((-342.761, 1120.261, -613.284))),
    "m45_01_00_00": ("m60_47_42_00", Vector3((-2.34, 150.4, -43.36))),
    "m45_02_00_00": ("m60_42_40_00", Vector3((-24.47, 208.82, -66.69))),
}


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
    global BAKED
    if BAKED:
        return {key: [(dest, None, delta)] for (key, (dest, delta)) in BAKED.items()}

    global _CACHED_DUNGEONS_TO_OVERWORLD_DICT

    if _CACHED_DUNGEONS_TO_OVERWORLD_DICT is not None:
        return _CACHED_DUNGEONS_TO_OVERWORLD_DICT

    rows = _get_dungeons_to_overworld_csv()

    # Two passes: first, implant dungeons into overworld tiles, then implant dungeons into other overworld-implanted
    # dungeons. (For example, Divine Tower of Limgrave connects to Stormveil Castle, which connects to m60_41_38_00...)

    dungeons_to_overworld = {}  # type: dict[str, list[tuple[str, Vector3 | None, Vector3]]]

    # First pass: dungeons to overworld small tiles.
    # Note that some dungeons connect to MULTIPLE tiles. We record all of them here. The resulting 'world' transform,
    # once the tiles are placed on the world grid, should obviously be identical!
    for row in rows:

        source_map_stem = f"m{row.SrcAreaNo}_{row.SrcGridXNo:02}_{row.SrcGridZNo:02}_00"
        dest_map_stem = f"m{row.DstAreaNo}_{row.DstGridXNo:02}_{row.DstGridZNo:02}_00"

        if row.DstAreaNo not in {60, 61} or not row.IsBasePoint:
            continue

        if source_map_stem in RESTRICTIONS and RESTRICTIONS[source_map_stem] != dest_map_stem:
            continue  # not the connection we want; TODO: but surely leads to same result?

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
        if any(ignore_area in {row.SrcAreaNo, row.DstAreaNo} for ignore_area in (37, 38, 60, 61, 70)):
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
