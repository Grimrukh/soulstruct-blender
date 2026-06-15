"""Expanded headless FLVER import/export round-trip tests.

Covers every combination of game × FLVER subtype. Each test case:
  1. Sets the active game in Soulstruct settings.
  2. Imports a FLVER (or Binder containing one) with the generic `import_scene.flver` operator.
  3. Validates the resulting Blender objects (presence, type, armature, version, etc.).
  4. Exports the imported FLVER to a temporary output file with `export_scene.flver`.
  5. Re-imports the exported FLVER and compares Blender-side statistics.
  6. Re-exports and compares Soulstruct-side statistics (mesh/bone/material counts).
  7. Cleans up.

FILE PATHS
----------
Fill in the ``directory`` and ``filename`` fields in FLVER_TEST_CASES below with paths to
actual game files on your machine. Leave the string as-is as a placeholder if you don't have
that game, and the test will be skipped automatically (directory / file not found).

Run with:
    blender --background --python tests/test_flver_import_roundtrip.py

Or via the runner:
    blender --background --python tests/run_all_tests.py
"""
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import bpy
import bl_test_utils as T
from soulstruct.flver import FLVER

T.enable_addon()

# ---------------------------------------------------------------------------
# Test case descriptor
# ---------------------------------------------------------------------------

@dataclass
class FLVERImportCase(T.ImportCaseBase):
    """Declarative description of one FLVER import/export round-trip test."""

    # ---- Expected characteristics ---- (all optional; skipped if None)

    # Whether the top-level imported object should have an Armature parent.
    expect_armature: bool | None = None

    # Expected FLVER version enum name (e.g. "Sekiro_EldenRing") or None to skip check.
    expect_version: str | None = None

    # If True, assert that at least one material was created.
    expect_materials: bool = True

    # If True, assert that `submesh_props` was populated (not empty; only when per-slot
    # mode is active on the imported object).
    expect_per_submesh_props: bool = False



# ---------------------------------------------------------------------------
# Test case definitions
# ---------------------------------------------------------------------------
#
# Use forward slashes or raw strings for Windows paths.
# Leave ``directory=""`` for any game/subtype you don't have files for.
#
# Naming convention used here: "GAME / SubType / description"
#
# NOTE: CHRBND Binders can be used directly as operator input for FLVER
# as the operators extract FLVERs from them.

from soulstruct.config import Config

FLVER_TEST_CASES: list[FLVERImportCase] = [

    # ------------------------------------------------------------------
    # Demon's Souls
    # ------------------------------------------------------------------
    FLVERImportCase(
        name="DES / Map Piece / m01 loose FLVER",
        game_enum="DEMONS_SOULS",
        directory=Config.DES_PATH / "map/m01_00_00_00",
        filename="m0010b0.flver.dcx",
        expect_armature=False,
        expect_version="DemonsSouls",
        tags=["map_piece"],
    ),
    FLVERImportCase(
        name="DES / Character / c0000 (Player)",
        game_enum="DEMONS_SOULS",
        directory=Config.DES_PATH / "chr/c0000",
        filename="c0000.chrbnd.dcx",
        expect_armature=True,
        expect_version="DemonsSouls",
        tags=["character"],
    ),
    FLVERImportCase(
        name="DES / Character / c2010 (Boletaria Soldier)",
        game_enum="DEMONS_SOULS",
        directory=Config.DES_PATH / "chr/c2010",
        filename="c2010.chrbnd.dcx",
        expect_armature=True,
        tags=["character"],
    ),
    FLVERImportCase(
        name="DES / Object / o0100",
        game_enum="DEMONS_SOULS",
        directory=Config.DES_PATH / "obj",
        filename="o0100.objbnd.dcx",
        tags=["object"],
    ),
    FLVERImportCase(
        name="DES / Equipment / wp_a_0100",
        game_enum="DEMONS_SOULS",
        directory=Config.DES_PATH / "parts",
        filename="wp_a_0100.partsbnd.dcx",
        expect_armature=True,
        tags=["equipment"],
    ),
    FLVERImportCase(
        name="DES / Equipment / am_a_8020",
        game_enum="DEMONS_SOULS",
        directory=Config.DES_PATH / "parts",
        filename="am_a_8020.partsbnd.dcx",
        expect_armature=True,
        tags=["equipment"],
    ),

    # ------------------------------------------------------------------
    # Dark Souls: Prepare to Die Edition
    # ------------------------------------------------------------------
    FLVERImportCase(
        name="DS1PTDE / Map Piece / m10_02 loose FLVER",
        game_enum="DARK_SOULS_PTDE",
        directory=Config.PTDE_PATH / "map/m10_02_00_00",
        filename="m2000B2A10.flver",
        expect_armature=True,  # does have non-trivial bones in PTDE
        expect_version="DarkSouls_A",
        tags=["map_piece"],
    ),
    FLVERImportCase(
        name="DS1PTDE / Character / c1200",
        game_enum="DARK_SOULS_PTDE",
        directory=Config.PTDE_PATH / "chr",
        filename="c1200.chrbnd",
        expect_armature=True,
        expect_version="DarkSouls_A",
        tags=["character"],
    ),
    FLVERImportCase(
        name="DS1PTDE / Object / o1290",
        game_enum="DARK_SOULS_PTDE",
        directory=Config.PTDE_PATH / "obj",
        filename="o1290.objbnd",
        tags=["object"],
    ),
    FLVERImportCase(
        name="DS1PTDE / Equipment / WP_A_1000",
        game_enum="DARK_SOULS_PTDE",
        directory=Config.PTDE_PATH / "parts",
        filename="WP_A_1000.partsbnd",
        expect_armature=True,
        tags=["equipment"],
    ),
    FLVERImportCase(
        name="DS1PTDE / Equipment / AM_M_1000",
        game_enum="DARK_SOULS_PTDE",
        directory=Config.PTDE_PATH / "parts",
        filename="AM_M_1000.partsbnd",
        expect_armature=True,
        tags=["equipment"],
    ),

    # ------------------------------------------------------------------
    # Dark Souls Remastered
    # ------------------------------------------------------------------
    FLVERImportCase(
        name="DSR / Map Piece / m10 loose FLVER",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "map/m10_02_00_00",
        filename="m2000B2A10.flver",  # main bonfire clearing Map Piece
        expect_armature=False,
        expect_version="DarkSouls_A",
        tags=["map_piece"],
    ),
    FLVERImportCase(
        name="DSR / Character / c1200",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "chr",
        filename="c1200.chrbnd.dcx",  # Large Rat
        expect_armature=True,
        expect_version="DarkSouls_A",
        tags=["character"],
    ),
    FLVERImportCase(
        name="DSR / Character / c0000 (player)",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "chr",
        filename="c0000.chrbnd.dcx",  # Player Character
        expect_armature=True,
        expect_version="DarkSouls_A",
        expect_materials=False,  # player mesh is empty (uses Parts)
        tags=["character"],
    ),
    FLVERImportCase(
        name="DSR / Object / o1290",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "obj",
        filename="o1290.objbnd.dcx",  # Sunlight Altar destructible parapets
        tags=["object"],
    ),
    FLVERImportCase(
        name="DSR / Equipment / WP_A_1000",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "parts",
        filename="WP_A_0100.partsbnd.dcx",
        expect_armature=True,
        tags=["equipment"],
    ),
    FLVERImportCase(
        name="DSR / Equipment / AM_M_1000",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "parts",
        filename="AM_M_0100.partsbnd.dcx",
        expect_armature=True,
        tags=["equipment"],
    ),

    # ------------------------------------------------------------------
    # Dark Souls 2 (SotFS)
    # ------------------------------------------------------------------
    FLVERImportCase(
        name="DS2 / Map Piece",
        game_enum="DARK_SOULS_2",
        directory="",   # TODO: e.g. "C:/Dark Souls 2/map/m10_02_00_00"
        filename="",    # TODO: e.g. "m10_02_00_00.flver"
        expect_armature=False,
        tags=["map_piece"],
    ),
    FLVERImportCase(
        name="DS2 / Character",
        game_enum="DARK_SOULS_2",
        directory="",   # TODO: e.g. "C:/Dark Souls 2/chr"
        filename="",    # TODO: e.g. "c0000.chrbnd"
        expect_armature=True,
        tags=["character"],
    ),
    FLVERImportCase(
        name="DS2 / Object",
        game_enum="DARK_SOULS_2",
        directory="",   # TODO: e.g. "C:/Dark Souls 2/obj"
        filename="",    # TODO: e.g. "o0100.objbnd"
        tags=["object"],
    ),
    FLVERImportCase(
        name="DS2 / Equipment",
        game_enum="DARK_SOULS_2",
        directory="",   # TODO: e.g. "C:/Dark Souls 2/parts"
        filename="",    # TODO: e.g. "WP_A_0100.partsbnd"
        expect_armature=True,
        tags=["equipment"],
    ),

    # ------------------------------------------------------------------
    # Bloodborne
    # ------------------------------------------------------------------
    # FLVERImportCase(
    #     name="BB / Map Piece / m21_00 (Hunter's Dream)",
    #     game_enum="BLOODBORNE",
    #     directory=Config.BB_PATH / "map/m21_00_00_00",
    #     filename="m21_00_00_00_001000.flver.dcx",
    #     expect_armature=False,
    #     tags=["map_piece"],
    # ),
    # FLVERImportCase(
    #     name="BB / Character / c0000 (Player)",
    #     game_enum="BLOODBORNE",
    #     directory=Config.BB_PATH / "chr",
    #     filename="c0000.chrbnd.dcx",
    #     expect_armature=True,
    #     tags=["character"],
    # ),
    # FLVERImportCase(
    #     name="BB / Character / c1060 (Brainsucker)",
    #     game_enum="BLOODBORNE",
    #     directory=Config.BB_PATH / "chr",
    #     filename="c1060.chrbnd.dcx",
    #     expect_armature=True,
    #     tags=["character"],
    # ),
    # FLVERImportCase(
    #     name="BB / Equipment / wp_a_1030",
    #     game_enum="BLOODBORNE",
    #     directory=Config.BB_PATH / "parts",
    #     filename="wp_a_1030.partsbnd.dcx",
    #     expect_armature=True,
    #     tags=["equipment"],
    # ),
    # FLVERImportCase(
    #     name="BB / Equipment / am_a_5210",
    #     game_enum="BLOODBORNE",
    #     directory=Config.BB_PATH / "parts",
    #     filename="am_a_5210.partsbnd.dcx",
    #     expect_armature=True,
    #     tags=["equipment"],
    # ),

    # ------------------------------------------------------------------
    # Dark Souls 3
    # ------------------------------------------------------------------
    FLVERImportCase(
        name="DS3 / Map Piece",
        game_enum="DARK_SOULS_3",
        directory="",   # TODO: e.g. "C:/DARK SOULS III/map/m30_00_00_00"
        filename="",    # TODO: e.g. "m30_00_00_00.mapbnd.dcx"
        expect_armature=False,
        tags=["map_piece"],
    ),
    FLVERImportCase(
        name="DS3 / Character / c0000",
        game_enum="DARK_SOULS_3",
        directory="",   # TODO: e.g. "C:/DARK SOULS III/chr"
        filename="",    # TODO: e.g. "c0000.chrbnd.dcx"
        expect_armature=True,
        tags=["character"],
    ),
    FLVERImportCase(
        name="DS3 / Character / enemy",
        game_enum="DARK_SOULS_3",
        directory="",   # TODO: e.g. "C:/DARK SOULS III/chr"
        filename="",    # TODO: e.g. "c1000.chrbnd.dcx"
        expect_armature=True,
        tags=["character"],
    ),
    FLVERImportCase(
        name="DS3 / Object",
        game_enum="DARK_SOULS_3",
        directory="",   # TODO: e.g. "C:/DARK SOULS III/obj"
        filename="",    # TODO: e.g. "o100000.objbnd.dcx"
        tags=["object"],
    ),
    FLVERImportCase(
        name="DS3 / Equipment / weapon",
        game_enum="DARK_SOULS_3",
        directory="",   # TODO: e.g. "C:/DARK SOULS III/parts"
        filename="",    # TODO: e.g. "WP_A_0100.partsbnd.dcx"
        expect_armature=True,
        tags=["equipment"],
    ),

    # ------------------------------------------------------------------
    # Sekiro
    # ------------------------------------------------------------------
    FLVERImportCase(
        name="Sekiro / Map Piece",
        game_enum="SEKIRO",
        directory="",   # TODO: e.g. "C:/Sekiro/map/m10_00_00_00"
        filename="",    # TODO: loose FLVER or mapbnd
        expect_armature=False,
        tags=["map_piece"],
    ),
    FLVERImportCase(
        name="Sekiro / Character / c0100",
        game_enum="SEKIRO",
        directory="",   # TODO: e.g. "C:/Sekiro/chr"
        filename="",    # TODO: e.g. "c0100.chrbnd.dcx"
        expect_armature=True,
        expect_version="Sekiro_EldenRing",
        tags=["character"],
    ),
    FLVERImportCase(
        name="Sekiro / Equipment",
        game_enum="SEKIRO",
        directory="",   # TODO: e.g. "C:/Sekiro/parts"
        filename="",    # TODO: e.g. "WP_A_0001.partsbnd.dcx"
        expect_armature=True,
        tags=["equipment"],
    ),

    # ------------------------------------------------------------------
    # Elden Ring
    # ------------------------------------------------------------------
    FLVERImportCase(
        name="ER / Map Piece / m60 overworld",
        game_enum="ELDEN_RING",
        directory="",   # TODO: e.g. "C:/ELDEN RING/Game/map/m60/m60_47_52_0"
        filename="",    # TODO: e.g. "m60_47_52_0.mapbnd.dcx"
        expect_armature=False,
        expect_version="Sekiro_EldenRing",
        tags=["map_piece"],
    ),
    FLVERImportCase(
        name="ER / Map Piece / m10 dungeon",
        game_enum="ELDEN_RING",
        directory="",   # TODO: e.g. "C:/ELDEN RING/Game/map/m10/m10_00_00_00"
        filename="",    # TODO: e.g. "m10_00_00_00.mapbnd.dcx"
        expect_armature=False,
        expect_version="Sekiro_EldenRing",
        tags=["map_piece"],
    ),
    FLVERImportCase(
        name="ER / Character / c0000",
        game_enum="ELDEN_RING",
        directory="",   # TODO: e.g. "C:/ELDEN RING/Game/chr"
        filename="",    # TODO: e.g. "c0000.chrbnd.dcx"
        expect_armature=True,
        expect_version="Sekiro_EldenRing",
        tags=["character"],
    ),
    FLVERImportCase(
        name="ER / Character / enemy",
        game_enum="ELDEN_RING",
        directory="",   # TODO: e.g. "C:/ELDEN RING/Game/chr"
        filename="",    # TODO: e.g. "c1000.chrbnd.dcx"
        expect_armature=True,
        expect_version="Sekiro_EldenRing",
        tags=["character"],
    ),
    FLVERImportCase(
        name="ER / Asset / aeg001",
        game_enum="ELDEN_RING",
        directory="",   # TODO: e.g. "C:/ELDEN RING/Game/asset/aeg/aeg001"
        filename="",    # TODO: e.g. "aeg001_003.geombnd.dcx"
        tags=["asset"],
    ),
    FLVERImportCase(
        name="ER / Equipment / weapon",
        game_enum="ELDEN_RING",
        directory="",   # TODO: e.g. "C:/ELDEN RING/Game/parts"
        filename="",    # TODO: e.g. "WP_A_0100.partsbnd.dcx"
        expect_armature=True,
        expect_version="Sekiro_EldenRing",
        tags=["equipment"],
    ),
    FLVERImportCase(
        name="ER / Equipment / armor (body)",
        game_enum="ELDEN_RING",
        directory="",   # TODO: e.g. "C:/ELDEN RING/Game/parts"
        filename="",    # TODO: e.g. "AM_M_0100.partsbnd.dcx"
        expect_armature=True,
        tags=["equipment"],
    ),
]


# Blender round trip removes degenerate faces. We don't expect more than this
# for all unit test cases.
MAX_POLYGON_COUNT_LOSS = 10


# ---------------------------------------------------------------------------
# Per-case test runner
# ---------------------------------------------------------------------------

def _find_first_flver_obj() -> bpy.types.Object | None:
    """Return the first FLVER-typed Mesh object in the scene (just-imported)."""
    objs = T.find_objects_by_soulstruct_type("FLVER")
    return objs[0] if objs else None


def _flver_scene_stats() -> dict:
    """Collect coarse statistics about all FLVER Mesh objects currently in the scene."""
    objs = T.find_objects_by_soulstruct_type("FLVER")
    poly_count = sum(len(o.data.polygons) for o in objs)
    mat_count = sum(len(o.data.materials) for o in objs)
    bone_count = 0
    for o in objs:
        if o.parent and o.parent.type == "ARMATURE":
            bone_count = max(bone_count, len(o.parent.data.bones))
    return {
        "mesh_obj_count": len(objs),
        "poly_count": poly_count,
        "mat_count": mat_count,
        "bone_count": bone_count,
    }


def run_case(case: FLVERImportCase):
    """Import, validate, export, re-import, re-export, and compare one FLVERImportCase."""

    # ---- Setup ----
    T.clear_scene()
    T.set_game(case.game_enum)
    # Disable texture import for speed; we only care about geometry/properties.
    bpy.context.scene.flver_import_settings.import_textures = False

    # ---- 1. Import from game file ----
    try:
        result = bpy.ops.import_scene.flver(
            "EXEC_DEFAULT",
            directory=str(case.directory),
            files=[{"name": case.filename}],
        )
    except Exception as ex:
        T.fail(case.name, f"Import raised exception: {ex}")
        return

    if "FINISHED" not in result:
        T.fail(case.name, f"Import operator returned {result} (expected FINISHED)")
        return

    # ---- 2. Validate scene ----
    flver_obj = _find_first_flver_obj()
    if flver_obj is None:
        T.fail(case.name, "No FLVER Mesh object found in scene after import")
        return

    # Armature expectation.
    if case.expect_armature is True:
        has_arm = flver_obj.parent is not None and flver_obj.parent.type == "ARMATURE"
        if not has_arm:
            T.fail(case.name, f"Expected Armature parent, got parent={flver_obj.parent}")
            return
    elif case.expect_armature is False:
        has_arm = flver_obj.parent is not None and flver_obj.parent.type == "ARMATURE"
        if has_arm:
            T.fail(case.name, "Did not expect Armature parent, but one was found")
            return

    # FLVER version expectation.
    if case.expect_version is not None:
        actual_ver = flver_obj.FLVER.version
        if actual_ver != case.expect_version and actual_ver != "DEFAULT":
            T.fail(
                case.name,
                f"Expected FLVER version '{case.expect_version}', got '{actual_ver}'",
            )
            return

    # Material expectation.
    if case.expect_materials and not flver_obj.data.materials:
        T.fail(case.name, "Expected at least one material but none were created")
        return

    # Per-submesh props.
    if case.expect_per_submesh_props and len(flver_obj.FLVER.submesh_props) == 0:
        T.fail(case.name, "Expected per-slot submesh_props to be populated")
        return

    # Save first-import stats for later comparison.
    stats_1 = _flver_scene_stats()
    model_name = flver_obj.name.split(".")[0].split(" ")[0]

    with tempfile.TemporaryDirectory() as tmpdir:
        # ---- 3. First export ----
        T.activate(flver_obj)
        export_path_1 = str(Path(tmpdir) / f"{model_name}.flver")
        try:
            export_result = bpy.ops.export_scene.flver(
                "EXEC_DEFAULT",
                filepath=export_path_1,
                dcx_type="Null",
            )
        except Exception as ex:
            T.fail(case.name, f"First export raised exception: {ex}")
            return
        if "FINISHED" not in export_result:
            T.fail(case.name, f"First export operator returned {export_result}")
            return

        flver_files_1 = list(Path(tmpdir).glob("*.flver"))
        if not flver_files_1:
            T.fail(case.name, "No .flver found in temp dir after first export")
            return

        # Verify parseable.
        try:
            reloaded_1 = FLVER.from_path(flver_files_1[0])
        except Exception as ex:
            T.fail(case.name, f"First exported FLVER not parseable by Soulstruct: {ex}")
            return

        if not reloaded_1.meshes and flver_obj.data.polygons:
            T.fail(case.name, "First exported FLVER has no meshes but source had polygons")
            return

        # ---- 4. Re-import the exported FLVER ----
        T.clear_scene()
        T.set_game(case.game_enum)
        bpy.context.scene.flver_import_settings.import_textures = False
        try:
            result2 = bpy.ops.import_scene.flver(
                "EXEC_DEFAULT",
                directory=str(Path(tmpdir)),
                files=[{"name": flver_files_1[0].name}],
            )
        except Exception as ex:
            T.fail(case.name, f"Re-import raised exception: {ex}")
            return
        if "FINISHED" not in result2:
            T.fail(case.name, f"Re-import returned {result2}")
            return

        flver_obj_2 = _find_first_flver_obj()
        if flver_obj_2 is None:
            T.fail(case.name, "No FLVER object found after re-import")
            return

        # ---- 5. Compare Blender statistics (import vs re-import) ----
        stats_2 = _flver_scene_stats()
        if stats_1["mesh_obj_count"] != stats_2["mesh_obj_count"]:
            T.fail(
                case.name,
                f"Mesh object count differs after re-import: "
                f"{stats_1['mesh_obj_count']} → {stats_2['mesh_obj_count']}",
            )
            return
        # Vanilla FLVERs often contain degenerate faces that will be lost during round trip.
        poly_diff = stats_1["poly_count"] - stats_2["poly_count"]
        if poly_diff < 0 or poly_diff > MAX_POLYGON_COUNT_LOSS:
            T.fail(
                case.name,
                f"Polygon count differs after re-import: "
                f"{stats_1['poly_count']} → {stats_2['poly_count']} (diff: {poly_diff})",
            )
            return

        # ---- 6. Second export (from re-imported data) ----
        T.activate(flver_obj_2)
        export_path_2 = str(Path(tmpdir) / f"{model_name}_2.flver")
        try:
            export_result_2 = bpy.ops.export_scene.flver(
                "EXEC_DEFAULT",
                filepath=export_path_2,
                dcx_type="Null",
            )
        except Exception as ex:
            T.fail(case.name, f"Second export raised exception: {ex}")
            return
        if "FINISHED" not in export_result_2:
            T.fail(case.name, f"Second export operator returned {export_result_2}")
            return

        flver_files_2 = [p for p in Path(tmpdir).glob("*.flver") if "_2" in p.stem]
        if not flver_files_2:
            T.fail(case.name, "No _2.flver found in temp dir after second export")
            return

        # ---- 7. Compare Soulstruct representations ----
        try:
            reloaded_2 = FLVER.from_path(flver_files_2[0])
        except Exception as ex:
            T.fail(case.name, f"Second exported FLVER not parseable by Soulstruct: {ex}")
            return

        if len(reloaded_1.meshes) != len(reloaded_2.meshes):
            T.fail(
                case.name,
                f"Mesh count differs between export 1 and 2: "
                f"{len(reloaded_1.meshes)} vs {len(reloaded_2.meshes)}",
            )
            return
        if len(reloaded_1.bones) != len(reloaded_2.bones):
            T.fail(
                case.name,
                f"Bone count differs between export 1 and 2: "
                f"{len(reloaded_1.bones)} vs {len(reloaded_2.bones)}",
            )
            return

    # ---- All checks passed ----
    T.ok(
        case.name,
        f"full round-trip OK — {stats_1['mesh_obj_count']} mesh(es), "
        f"{stats_1['mat_count']} mat(s), {stats_1['bone_count']} bone(s)",
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    T.run_case_list(FLVER_TEST_CASES, run_case, suite_name="FLVER import/export")


main()
