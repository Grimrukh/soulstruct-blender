"""Headless HKX Map Collision import/export round-trip tests.

Supports Dark Souls PTDE and DSR (the only games with Havok collision implemented in the
add-on at this time).  BB / ER use a different physics format that is not yet supported.

Round-trip methodology per case
---------------------------------
1. Import hi-res ``h*.hkx`` (loose) with ``import_scene.hkx_map_collision``.
2. Validate: at least one COLLISION-typed Mesh object was created.
3. Export back to a temp ``h*.hkx`` via ``export_scene.hkx_map_collision``.
4. Verify the exported file is parseable by Soulstruct (``MapCollisionModel.from_path``).
5. Re-import the exported file; compare Blender statistics (poly count, material count).
6. Re-export to a second temp file; compare Soulstruct statistics with the first export.
7. Clean up.

FILE PATHS
----------
Fill in ``directory`` / ``filename`` for the games you have installed.
Leave both as empty strings to auto-skip that case.

Run with:
    blender --background --python tests/test_collision_import_roundtrip.py
"""
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import bpy
import bl_test_utils as T
from soulstruct.havok.fromsoft.shared import MapCollisionModel

T.enable_addon()

# ---------------------------------------------------------------------------
# Game path constants
# ---------------------------------------------------------------------------

from soulstruct.config import Config

# ---------------------------------------------------------------------------
# Test case descriptor
# ---------------------------------------------------------------------------

@dataclass
class CollisionImportCase(T.ImportCaseBase):
    """One HKX collision import/export round-trip test.

    ``filename`` should be a hi-res ``h*.hkx`` (or ``l*.hkx``) loose file.
    The add-on will auto-locate the matching other-resolution file next to it.
    """

    # Expected number of hi-res sub-mesh materials (None = skip check).
    expect_hi_mat_count: int | None = None
    # Expected number of lo-res sub-mesh materials (None = skip check).
    expect_lo_mat_count: int | None = None


# ---------------------------------------------------------------------------
# Test case definitions
# ---------------------------------------------------------------------------

COLLISION_TEST_CASES: list[CollisionImportCase] = [

    # ------------------------------------------------------------------
    # Demon's Souls
    # ------------------------------------------------------------------
    CollisionImportCase(
        name="DeS / Map m01_00_00_00 / h0002b0",  # The Nexus
        game_enum="DEMONS_SOULS",
        directory=Config.DES_PATH / "map/m01_00_00_00",
        filename="h0002b0.hkx",
        tags=["map_collision"],
    ),
    CollisionImportCase(
        name="DeS / Map m07_00_00_00 / h0000b0",  # Northern Limits (unused)
        game_enum="DEMONS_SOULS",
        directory=Config.DES_PATH / "map/m07_00_00_00",
        filename="h0000b0.hkx",
        tags=["map_collision"],
    ),

    # ------------------------------------------------------------------
    # Dark Souls PTDE
    # ------------------------------------------------------------------
    CollisionImportCase(
        name="PTDE / Map m10_02_00_00 / h0000B2A10",
        game_enum="DARK_SOULS_PTDE",
        directory=Config.PTDE_PATH / "map/m10_02_00_00",
        filename="h0000B2A10.hkx",
        tags=["map_collision"],
    ),
    CollisionImportCase(
        name="PTDE / Map m12_00_00_00 / h0000B0A12",
        game_enum="DARK_SOULS_PTDE",
        directory=Config.PTDE_PATH / "map/m12_00_00_00",
        filename="h0000B0A12.hkx",
        tags=["map_collision"],
    ),

    # ------------------------------------------------------------------
    # Dark Souls Remastered
    # ------------------------------------------------------------------
    # NOTE: These tests take longer than usual due to the large number of Mopper calls
    # required for multiple full-map exports.
    CollisionImportCase(
        name="DSR / Map m10_02_00_00 / hkxbhd",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "map/m10_02_00_00",
        filename="h10_02_00_00.hkxbhd",
        tags=["map_collision"],
    ),
    CollisionImportCase(
        # QLOC accidentally included two lo-res 'B1A12' collisions.
        # These should be ignored when importing all from the binders, with a warning.
        name="DSR / Map m12_00_00_00 / hkxbhd",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "map/m12_00_00_00",
        filename="h12_00_00_00.hkxbhd",
        tags=["map_collision"],
    ),
]


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------

def _collision_scene_stats() -> dict:
    """Collect coarse statistics about all COLLISION Mesh objects in the scene."""
    objs = T.find_objects_by_soulstruct_type("COLLISION")
    poly_count = sum(len(o.data.polygons) for o in objs)
    mat_names = set()
    for o in objs:
        for mat in o.data.materials:
            if mat:
                mat_names.add(mat.name)
    return {
        "obj_count": len(objs),
        "poly_count": poly_count,
        "mat_count": len(mat_names),
    }


# ---------------------------------------------------------------------------
# Per-case test runner
# ---------------------------------------------------------------------------

def run_case(case: CollisionImportCase):
    """Full round-trip: import → export → re-import → compare → re-export → compare."""

    # ---- 1. Import from game file ----
    T.clear_scene()
    T.set_game(case.game_enum)

    try:
        result = bpy.ops.import_scene.hkx_map_collision(
            "EXEC_DEFAULT",
            directory=str(case.directory),
            files=[{"name": case.filename}],
            import_all_from_binder=True,
        )
    except Exception as ex:
        T.fail(case.name, f"Import raised exception: {ex}")
        return
    if "FINISHED" not in result:
        T.fail(case.name, f"Import returned {result}")
        return

    # ---- 2. Validate ----
    coll_objs = T.find_objects_by_soulstruct_type("COLLISION")
    if not coll_objs:
        T.fail(case.name, "No COLLISION objects found after import")
        return

    # Optional material-count checks.
    if case.expect_hi_mat_count is not None:
        hi_mats = {m.name for o in coll_objs for m in o.data.materials if m and "Hi" in m.name}
        if len(hi_mats) != case.expect_hi_mat_count:
            T.fail(
                case.name,
                f"Expected {case.expect_hi_mat_count} hi-res material(s), got {len(hi_mats)}",
            )
            return

    stats_1 = _collision_scene_stats()

    with tempfile.TemporaryDirectory() as tmpdir:

        # ---- 3. First export ----

        for coll_obj in coll_objs:

            model_stem = coll_obj.name.split(".")[0].split(" ")[0]

            T.activate(coll_obj)
            try:
                export_result = bpy.ops.export_scene.hkx_map_collision(
                    "EXEC_DEFAULT",
                    filepath=str(Path(tmpdir) / f"{model_stem}.hkx"),
                    dcx_type="Null",
                    write_other_resolution=True,
                )
            except Exception as ex:
                T.fail(case.name, f"First export raised exception: {ex}")
                return
            if "FINISHED" not in export_result:
                T.fail(case.name, f"First export returned {export_result}")
                return

        hkx_files_1 = list(Path(tmpdir).glob("*.hkx"))
        if not hkx_files_1:
            T.fail(case.name, "No .hkx file found after first export")
            return

        # ---- 4. Verify parseable ----
        hi_files = [p for p in hkx_files_1 if p.name.startswith("h")]
        if not hi_files:
            T.fail(case.name, "No hi-res .hkx file ('h*') found after first export")
            return
        lo_files = [p for p in hkx_files_1 if p.name.startswith("l")]
        if not lo_files:
            T.fail(case.name, "No lo-res .hkx file ('l*') found after first export")
            return
        try:
            mc1 = MapCollisionModel.from_path(hi_files[0])
        except Exception as ex:
            T.fail(case.name, f"First exported HKX not parseable: {ex}")
            return

        # ---- 5. Re-import exported file(s) ----
        T.clear_scene()
        T.set_game(case.game_enum)
        try:
            # Importer will find matching lo-res file for each hi-res file path.
            result2 = bpy.ops.import_scene.hkx_map_collision(
                "EXEC_DEFAULT",
                directory=str(Path(tmpdir)),
                files=[{"name": hi_file.name} for hi_file in hi_files],
            )
        except Exception as ex:
            T.fail(case.name, f"Re-import raised exception: {ex}")
            return
        if "FINISHED" not in result2:
            T.fail(case.name, f"Re-import returned {result2}")
            return

        coll_objs_2 = T.find_objects_by_soulstruct_type("COLLISION")
        if not coll_objs_2:
            T.fail(case.name, "No COLLISION objects after re-import")
            return

        # ---- 6. Compare Blender statistics ----
        stats_2 = _collision_scene_stats()
        if stats_1["obj_count"] != stats_2["obj_count"]:
            T.fail(
                case.name,
                f"Object count differs after re-import: {stats_1['obj_count']} → {stats_2['obj_count']}",
            )
            return
        if stats_1["poly_count"] != stats_2["poly_count"]:
            T.fail(
                case.name,
                f"Poly count differs after re-import: {stats_1['poly_count']} → {stats_2['poly_count']}",
            )
            return
        if stats_1["mat_count"] != stats_2["mat_count"]:
            T.fail(
                case.name,
                f"Material count differs after re-import: {stats_1['mat_count']} → {stats_2['mat_count']}",
            )
            return

        # ---- 7. Second export ----

        for coll_obj_2 in coll_objs_2:

            T.activate(coll_obj_2)
            coll_stem_2 = coll_obj_2.name.split(".")[0].split(" ")[0]
            try:
                export_result_2 = bpy.ops.export_scene.hkx_map_collision(
                    "EXEC_DEFAULT",
                    filepath=str(Path(tmpdir) / f"{coll_stem_2}_2.hkx"),
                    dcx_type="Null",
                    write_other_resolution=True,
                )
            except Exception as ex:
                T.fail(case.name, f"Second export raised exception: {ex}")
                return
            if "FINISHED" not in export_result_2:
                T.fail(case.name, f"Second export returned {export_result_2}")
                return

        hi_files_2 = [p for p in Path(tmpdir).glob("h*_2.hkx")]
        if not hi_files_2:
            # Fallback: any new hi-res file that wasn't there before.
            hi_files_2 = [p for p in Path(tmpdir).glob("h*.hkx") if p not in hi_files]
        if not hi_files_2:
            T.fail(case.name, "No second hi-res .hkx file found after second export")
            return

        try:
            mc2 = MapCollisionModel.from_path(hi_files_2[0])
        except Exception as ex:
            T.fail(case.name, f"Second exported HKX not parseable: {ex}")
            return

        # ---- 8. Compare Soulstruct statistics ----
        if len(mc1.meshes) != len(mc2.meshes):
            T.fail(
                case.name,
                f"Mesh count differs between exports: {len(mc1.meshes)} vs {len(mc2.meshes)}",
            )
            return

    T.ok(
        case.name,
        f"collision round-trip OK — {stats_1['obj_count']} obj(s), "
        f"{stats_1['poly_count']} poly(s), {stats_1['mat_count']} mat(s)",
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    T.run_case_list(COLLISION_TEST_CASES, run_case, suite_name="HKX Collision import/export")


main()

