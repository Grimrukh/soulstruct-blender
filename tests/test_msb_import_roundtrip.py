"""Headless MSB (map studio) import/export round-trip tests.

Covers Dark Souls PTDE and DSR (games with Soulstruct MSB support, handled by
``import_scene.any_msb`` / ``export_scene.any_msb``).

Round-trip methodology per case
---------------------------------
1. Import the MSB (no models, for speed) with ``import_scene.any_msb``.
2. Count MSB_PART / MSB_REGION / MSB_EVENT objects in the scene.
3. Locate the imported ``m??_??_??_?? MSB`` collection; set it as active layer collection.
4. Export with ``export_scene.any_msb`` to a temp ``.msb`` file.
5. Parse the exported file with the Soulstruct MSB class; compare counts.
6. Re-import the exported MSB; compare Blender counts (parts, regions, events).
7. Re-export to a second temp file; parse and compare with first export.
8. Clean up.

FILE PATHS
----------
Fill in ``directory`` / ``filename`` for the games you have installed.
Leave both as empty strings to auto-skip.

Run with:
    blender --background --python tests/test_msb_import_roundtrip.py
"""
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import bpy
import bl_test_utils as T
from soulstruct.config import Config
from soulstruct.darksouls1ptde.maps import MSB as PTDE_MSB
from soulstruct.darksouls1r.maps import MSB as DSR_MSB

T.enable_addon()

# ---------------------------------------------------------------------------
# Test case descriptor
# ---------------------------------------------------------------------------

@dataclass
class MSBImportCase(T.ImportCaseBase):
    """One MSB import/export round-trip test.

    ``directory`` is the MapStudio folder; ``filename`` is the ``.msb`` (or
    ``.msb.dcx``) file.
    """

    # If True, import linked FLVER/collision/navmesh models. Usually False for speed.
    import_models: bool = False

    # Expected counts (None = skip check).
    expect_part_count: int | None = None
    expect_region_count: int | None = None
    expect_event_count: int | None = None


# ---------------------------------------------------------------------------
# Test case definitions
# ---------------------------------------------------------------------------

MSB_TEST_CASES: list[MSBImportCase] = [

    # ------------------------------------------------------------------
    # Dark Souls PTDE
    # ------------------------------------------------------------------
    MSBImportCase(
        name="PTDE / Map m10_02 MSB (Firelink)",
        game_enum="DARK_SOULS_PTDE",
        directory=Config.PTDE_PATH / "map/MapStudio",
        filename="m10_02_00_00.msb",
        import_models=False,
        tags=["msb"],
    ),
    MSBImportCase(
        name="PTDE / Map m12_00 MSB (Darkroot v1)",
        game_enum="DARK_SOULS_PTDE",
        directory=Config.PTDE_PATH / "map/MapStudio",
        filename="m12_00_00_01.msb",
        import_models=False,
        tags=["msb"],
    ),

    # ------------------------------------------------------------------
    # Dark Souls Remastered
    # ------------------------------------------------------------------
    MSBImportCase(
        name="DSR / Map m10_02 MSB (Firelink)",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "map/MapStudio",
        filename="m10_02_00_00.msb",
        import_models=False,
        tags=["msb"],
    ),
    MSBImportCase(
        name="DSR / Map m12_00 MSB (Darkroot v1)",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "map/MapStudio",
        filename="m12_00_00_01.msb",
        import_models=False,
        tags=["msb"],
    ),
    MSBImportCase(
        name="DSR / Map m18_00 MSB (Kiln)",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "map/MapStudio",
        filename="m18_00_00_00.msb",
        import_models=False,
        tags=["msb"],
    ),
]


# ---------------------------------------------------------------------------
# MSB class lookup
# ---------------------------------------------------------------------------

_MSB_CLASS = {
    "DARK_SOULS_PTDE": PTDE_MSB,
    "DARK_SOULS_DSR": DSR_MSB,
}


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------

def _msb_scene_stats() -> dict:
    """Count MSB_PART / MSB_REGION / MSB_EVENT objects in the current scene."""
    return {
        "part_count": len(T.find_objects_by_soulstruct_type("MSB_PART")),
        "region_count": len(T.find_objects_by_soulstruct_type("MSB_REGION")),
        "event_count": len(T.find_objects_by_soulstruct_type("MSB_EVENT")),
    }


def _set_active_msb_collection(map_stem: str) -> bool:
    """Make the ``m??_??_??_?? MSB`` layer collection active; return True on success."""
    coll_name = f"{map_stem} MSB"
    layer_coll = T.find_layer_collection(
        bpy.context.view_layer.layer_collection, coll_name
    )
    if layer_coll is None:
        return False
    bpy.context.view_layer.active_layer_collection = layer_coll
    return True


# ---------------------------------------------------------------------------
# Per-case test runner
# ---------------------------------------------------------------------------

def run_case(case: MSBImportCase):
    """Full round-trip: import → export → compare soulstruct → re-import → compare Blender."""

    msb_class = _MSB_CLASS.get(case.game_enum)
    if msb_class is None:
        T.fail(case.name, f"No MSB class registered for game_enum '{case.game_enum}'")
        return

    map_stem = case.filename.split(".")[0]  # e.g. "m10_02_00_00"

    # ---- 1. Import MSB ----
    T.clear_scene()
    T.set_game(case.game_enum)

    # Disable model imports for speed (unless the case requests them).
    msb_import_settings = bpy.context.scene.msb_import_settings
    msb_import_settings.import_map_piece_models = case.import_models
    msb_import_settings.import_object_models = case.import_models
    msb_import_settings.import_character_models = case.import_models
    msb_import_settings.import_collision_models = case.import_models
    msb_import_settings.import_navmesh_models = case.import_models

    try:
        result = bpy.ops.import_scene.any_msb(
            "EXEC_DEFAULT",
            filepath=str(case.source_path),
        )
    except Exception as ex:
        T.fail(case.name, f"Import raised exception: {ex}")
        return
    if "FINISHED" not in result:
        T.fail(case.name, f"Import returned {result}")
        return

    # ---- 2. Validate ----
    stats_1 = _msb_scene_stats()
    total_1 = stats_1["part_count"] + stats_1["region_count"] + stats_1["event_count"]
    if total_1 == 0:
        T.fail(case.name, "No MSB_PART / MSB_REGION / MSB_EVENT objects after import")
        return

    if case.expect_part_count is not None and stats_1["part_count"] != case.expect_part_count:
        T.fail(case.name, f"Expected {case.expect_part_count} parts, got {stats_1['part_count']}")
        return
    if case.expect_region_count is not None and stats_1["region_count"] != case.expect_region_count:
        T.fail(case.name, f"Expected {case.expect_region_count} regions, got {stats_1['region_count']}")
        return
    if case.expect_event_count is not None and stats_1["event_count"] != case.expect_event_count:
        T.fail(case.name, f"Expected {case.expect_event_count} events, got {stats_1['event_count']}")
        return

    # ---- 3. Set active MSB collection for export ----
    if not _set_active_msb_collection(map_stem):
        T.fail(case.name, f"Could not find collection '{map_stem} MSB' in view layer")
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        # ---- 4. First export ----
        export_path_1 = str(Path(tmpdir) / f"{map_stem}.msb")
        try:
            export_result = bpy.ops.export_scene.any_msb(
                "EXEC_DEFAULT",
                filepath=export_path_1,
            )
        except Exception as ex:
            T.fail(case.name, f"First export raised exception: {ex}")
            return
        if "FINISHED" not in export_result:
            T.fail(case.name, f"First export returned {export_result}")
            return

        msb_files = [p for p in Path(tmpdir).glob("*.msb") if not p.name.endswith(".bak")]
        if not msb_files:
            T.fail(case.name, "No .msb file found after first export")
            return

        # ---- 5. Parse exported MSB and compare counts ----
        try:
            msb1 = msb_class.from_path(msb_files[0])
        except Exception as ex:
            T.fail(case.name, f"Exported MSB not parseable: {ex}")
            return

        exported_part_count = len(msb1.get_parts())
        exported_region_count = len(msb1.get_regions())
        exported_event_count = len(msb1.get_events())

        if stats_1["part_count"] != exported_part_count:
            T.fail(
                case.name,
                f"Part count mismatch: Blender {stats_1['part_count']} vs MSB {exported_part_count}",
            )
            return
        if stats_1["region_count"] != exported_region_count:
            T.fail(
                case.name,
                f"Region count mismatch: Blender {stats_1['region_count']} vs MSB {exported_region_count}",
            )
            return
        if stats_1["event_count"] != exported_event_count:
            T.fail(
                case.name,
                f"Event count mismatch: Blender {stats_1['event_count']} vs MSB {exported_event_count}",
            )
            return

        # ---- 6. Re-import exported MSB ----
        T.clear_scene()
        T.set_game(case.game_enum)
        msb_import_settings = bpy.context.scene.msb_import_settings
        msb_import_settings.import_map_piece_models = False
        msb_import_settings.import_object_models = False
        msb_import_settings.import_character_models = False
        msb_import_settings.import_collision_models = False
        msb_import_settings.import_navmesh_models = False
        try:
            result2 = bpy.ops.import_scene.any_msb(
                "EXEC_DEFAULT",
                filepath=str(msb_files[0]),
            )
        except Exception as ex:
            T.fail(case.name, f"Re-import raised exception: {ex}")
            return
        if "FINISHED" not in result2:
            T.fail(case.name, f"Re-import returned {result2}")
            return

        stats_2 = _msb_scene_stats()
        if stats_1["part_count"] != stats_2["part_count"]:
            T.fail(
                case.name,
                f"Part count differs after re-import: {stats_1['part_count']} → {stats_2['part_count']}",
            )
            return
        if stats_1["region_count"] != stats_2["region_count"]:
            T.fail(
                case.name,
                f"Region count differs after re-import: {stats_1['region_count']} → {stats_2['region_count']}",
            )
            return
        if stats_1["event_count"] != stats_2["event_count"]:
            T.fail(
                case.name,
                f"Event count differs after re-import: {stats_1['event_count']} → {stats_2['event_count']}",
            )
            return

        # ---- 7. Second export ----
        if not _set_active_msb_collection(map_stem):
            T.fail(case.name, f"Could not find collection '{map_stem} MSB' after re-import")
            return
        export_path_2 = str(Path(tmpdir) / f"{map_stem}_2.msb")
        try:
            export_result_2 = bpy.ops.export_scene.any_msb(
                "EXEC_DEFAULT",
                filepath=export_path_2,
            )
        except Exception as ex:
            T.fail(case.name, f"Second export raised exception: {ex}")
            return
        if "FINISHED" not in export_result_2:
            T.fail(case.name, f"Second export returned {export_result_2}")
            return

        msb_files_2 = [p for p in Path(tmpdir).glob("*_2.msb")]
        if not msb_files_2:
            T.fail(case.name, "No *_2.msb found after second export")
            return

        # ---- 8. Compare second export with first ----
        try:
            msb2 = msb_class.from_path(msb_files_2[0])
        except Exception as ex:
            T.fail(case.name, f"Second exported MSB not parseable: {ex}")
            return

        if len(msb1.get_parts()) != len(msb2.get_parts()):
            T.fail(
                case.name,
                f"Part count differs between exports: "
                f"{len(msb1.get_parts())} vs {len(msb2.get_parts())}",
            )
            return
        if len(msb1.get_regions()) != len(msb2.get_regions()):
            T.fail(
                case.name,
                f"Region count differs between exports: "
                f"{len(msb1.get_regions())} vs {len(msb2.get_regions())}",
            )
            return

    T.ok(
        case.name,
        f"MSB round-trip OK — parts={stats_1['part_count']}, "
        f"regions={stats_1['region_count']}, events={stats_1['event_count']}",
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    T.run_case_list(MSB_TEST_CASES, run_case, suite_name="MSB import/export")


main()

