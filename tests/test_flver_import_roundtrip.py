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

    # If True, expect two FLVERS to be imported from the source BND, not 1.
    expect_two_flvers: bool = False


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
        filename="m0001b0.flver.dcx",
        expect_armature=True,  # has non-trivial bones
        expect_version="DemonsSouls",
        tags=["map_piece"],
    ),
    FLVERImportCase(
        name="DES / Character / c0000 (Player)",
        game_enum="DEMONS_SOULS",
        directory=Config.DES_PATH / "chr/c0000",
        filename="c0000.chrbnd.dcx",
        expect_armature=True,
        expect_materials=False,
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
        # TODO: Bug: exporter tries to write >28 bones in one Mesh.
    ),
    FLVERImportCase(
        name="DES / Object / o0100",
        game_enum="DEMONS_SOULS",
        directory=Config.DES_PATH / "obj",
        filename="o0100.objbnd.dcx",
        tags=["object"],
    ),
    FLVERImportCase(
        name="DES / Equipment / wp_a_1500",
        game_enum="DEMONS_SOULS",
        directory=Config.DES_PATH / "parts",
        filename="wp_a_1500.partsbnd.dcx",
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
        # TODO: Bug: exporter tries to write >28 bones in one Mesh.
    ),

    # ------------------------------------------------------------------
    # Dark Souls: Prepare to Die Edition
    # ------------------------------------------------------------------
    FLVERImportCase(
        name="DS1PTDE / Map Piece / m10_02 loose FLVER",
        game_enum="DARK_SOULS_PTDE",
        directory=Config.PTDE_PATH / "map/m10_02_00_00",
        filename="m2000B2A10.flver",
        expect_armature=True,
        expect_version="DarkSouls_A",
        tags=["map_piece"],
    ),
    # TODO: Test a Map Piece with no real bones.
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
        # TODO: Bug: second export fails, vertex 410 not weighted to a bone.
    ),
    FLVERImportCase(
        name="DS1PTDE / Equipment / WP_A_0100",
        game_enum="DARK_SOULS_PTDE",
        directory=Config.PTDE_PATH / "parts",
        filename="WP_A_0100.partsbnd",
        expect_armature=True,
        expect_two_flvers=True,
        tags=["equipment"],
    ),
    FLVERImportCase(
        name="DS1PTDE / Equipment / AM_A_1000",
        game_enum="DARK_SOULS_PTDE",
        directory=Config.PTDE_PATH / "parts",
        filename="AM_A_1000.partsbnd",
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
        filename="m2000B2A10.flver.dcx",  # main bonfire clearing Map Piece
        expect_armature=True,
        expect_version="DarkSouls_A",
        tags=["map_piece"],
    ),
    # TODO: Test a Map Piece with no real bones.
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

    # TODO: Bugged. Vertices weighted to child bones are not weighted on export.
    FLVERImportCase(
        name="DSR / Object / o1290",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "obj",
        filename="o1290.objbnd.dcx",  # Sunlight Altar destructible parapets
        tags=["object"],
    ),
    FLVERImportCase(
        name="DSR / Equipment / WP_A_0100",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "parts",
        filename="WP_A_0100.partsbnd.dcx",
        expect_armature=True,
        expect_two_flvers=True,
        tags=["equipment"],
    ),
    FLVERImportCase(
        name="DSR / Equipment / AM_A_1000",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "parts",
        filename="AM_A_1000.partsbnd.dcx",
        expect_armature=True,
        tags=["equipment"],
    ),

    # ------------------------------------------------------------------
    # Dark Souls 2 (SotFS)
    # ------------------------------------------------------------------
    # FLVERImportCase(
    #     name="DS2 / Map Piece",
    #     game_enum="DARK_SOULS_2",
    #     directory="",   # TODO: e.g. "C:/Dark Souls 2/map/m10_02_00_00"
    #     filename="",    # TODO: e.g. "m10_02_00_00.flver"
    #     expect_armature=False,
    #     tags=["map_piece"],
    # ),
    # FLVERImportCase(
    #     name="DS2 / Character",
    #     game_enum="DARK_SOULS_2",
    #     directory="",   # TODO: e.g. "C:/Dark Souls 2/chr"
    #     filename="",    # TODO: e.g. "c0000.chrbnd"
    #     expect_armature=True,
    #     tags=["character"],
    # ),
    # FLVERImportCase(
    #     name="DS2 / Object",
    #     game_enum="DARK_SOULS_2",
    #     directory="",   # TODO: e.g. "C:/Dark Souls 2/obj"
    #     filename="",    # TODO: e.g. "o0100.objbnd"
    #     tags=["object"],
    # ),
    # FLVERImportCase(
    #     name="DS2 / Equipment",
    #     game_enum="DARK_SOULS_2",
    #     directory="",   # TODO: e.g. "C:/Dark Souls 2/parts"
    #     filename="",    # TODO: e.g. "WP_A_0100.partsbnd"
    #     expect_armature=True,
    #     tags=["equipment"],
    # ),

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
    # FLVERImportCase(
    #     name="DS3 / Map Piece",
    #     game_enum="DARK_SOULS_3",
    #     directory="",   # TODO: e.g. "C:/DARK SOULS III/map/m30_00_00_00"
    #     filename="",    # TODO: e.g. "m30_00_00_00.mapbnd.dcx"
    #     expect_armature=False,
    #     tags=["map_piece"],
    # ),
    # FLVERImportCase(
    #     name="DS3 / Character / c0000",
    #     game_enum="DARK_SOULS_3",
    #     directory="",   # TODO: e.g. "C:/DARK SOULS III/chr"
    #     filename="",    # TODO: e.g. "c0000.chrbnd.dcx"
    #     expect_armature=True,
    #     tags=["character"],
    # ),
    # FLVERImportCase(
    #     name="DS3 / Character / enemy",
    #     game_enum="DARK_SOULS_3",
    #     directory="",   # TODO: e.g. "C:/DARK SOULS III/chr"
    #     filename="",    # TODO: e.g. "c1000.chrbnd.dcx"
    #     expect_armature=True,
    #     tags=["character"],
    # ),
    # FLVERImportCase(
    #     name="DS3 / Object",
    #     game_enum="DARK_SOULS_3",
    #     directory="",   # TODO: e.g. "C:/DARK SOULS III/obj"
    #     filename="",    # TODO: e.g. "o100000.objbnd.dcx"
    #     tags=["object"],
    # ),
    # FLVERImportCase(
    #     name="DS3 / Equipment / weapon",
    #     game_enum="DARK_SOULS_3",
    #     directory="",   # TODO: e.g. "C:/DARK SOULS III/parts"
    #     filename="",    # TODO: e.g. "WP_A_0100.partsbnd.dcx"
    #     expect_armature=True,
    #     tags=["equipment"],
    # ),

    # ------------------------------------------------------------------
    # Sekiro
    # ------------------------------------------------------------------
    # FLVERImportCase(
    #     name="Sekiro / Map Piece",
    #     game_enum="SEKIRO",
    #     directory="",   # TODO: e.g. "C:/Sekiro/map/m10_00_00_00"
    #     filename="",    # TODO: loose FLVER or mapbnd
    #     expect_armature=False,
    #     tags=["map_piece"],
    # ),
    # FLVERImportCase(
    #     name="Sekiro / Character / c0100",
    #     game_enum="SEKIRO",
    #     directory="",   # TODO: e.g. "C:/Sekiro/chr"
    #     filename="",    # TODO: e.g. "c0100.chrbnd.dcx"
    #     expect_armature=True,
    #     expect_version="Sekiro_EldenRing",
    #     tags=["character"],
    # ),
    # FLVERImportCase(
    #     name="Sekiro / Equipment",
    #     game_enum="SEKIRO",
    #     directory="",   # TODO: e.g. "C:/Sekiro/parts"
    #     filename="",    # TODO: e.g. "WP_A_0001.partsbnd.dcx"
    #     expect_armature=True,
    #     tags=["equipment"],
    # ),

    # ------------------------------------------------------------------
    # Elden Ring
    # ------------------------------------------------------------------
    # FLVERImportCase(
    #     name="ER / Map Piece / m60 overworld",
    #     game_enum="ELDEN_RING",
    #     directory="",   # TODO: e.g. "C:/ELDEN RING/Game/map/m60/m60_47_52_0"
    #     filename="",    # TODO: e.g. "m60_47_52_0.mapbnd.dcx"
    #     expect_armature=False,
    #     expect_version="Sekiro_EldenRing",
    #     tags=["map_piece"],
    # ),
    # FLVERImportCase(
    #     name="ER / Map Piece / m10 dungeon",
    #     game_enum="ELDEN_RING",
    #     directory="",   # TODO: e.g. "C:/ELDEN RING/Game/map/m10/m10_00_00_00"
    #     filename="",    # TODO: e.g. "m10_00_00_00.mapbnd.dcx"
    #     expect_armature=False,
    #     expect_version="Sekiro_EldenRing",
    #     tags=["map_piece"],
    # ),
    # FLVERImportCase(
    #     name="ER / Character / c0000",
    #     game_enum="ELDEN_RING",
    #     directory="",   # TODO: e.g. "C:/ELDEN RING/Game/chr"
    #     filename="",    # TODO: e.g. "c0000.chrbnd.dcx"
    #     expect_armature=True,
    #     expect_version="Sekiro_EldenRing",
    #     tags=["character"],
    # ),
    # FLVERImportCase(
    #     name="ER / Character / enemy",
    #     game_enum="ELDEN_RING",
    #     directory="",   # TODO: e.g. "C:/ELDEN RING/Game/chr"
    #     filename="",    # TODO: e.g. "c1000.chrbnd.dcx"
    #     expect_armature=True,
    #     expect_version="Sekiro_EldenRing",
    #     tags=["character"],
    # ),
    # FLVERImportCase(
    #     name="ER / Asset / aeg001",
    #     game_enum="ELDEN_RING",
    #     directory="",   # TODO: e.g. "C:/ELDEN RING/Game/asset/aeg/aeg001"
    #     filename="",    # TODO: e.g. "aeg001_003.geombnd.dcx"
    #     tags=["asset"],
    # ),
    # FLVERImportCase(
    #     name="ER / Equipment / weapon",
    #     game_enum="ELDEN_RING",
    #     directory="",   # TODO: e.g. "C:/ELDEN RING/Game/parts"
    #     filename="",    # TODO: e.g. "WP_A_0100.partsbnd.dcx"
    #     expect_armature=True,
    #     expect_version="Sekiro_EldenRing",
    #     tags=["equipment"],
    # ),
    # FLVERImportCase(
    #     name="ER / Equipment / armor (body)",
    #     game_enum="ELDEN_RING",
    #     directory="",   # TODO: e.g. "C:/ELDEN RING/Game/parts"
    #     filename="",    # TODO: e.g. "AM_A_0100.partsbnd.dcx"
    #     expect_armature=True,
    #     tags=["equipment"],
    # ),
]


# Blender round trip removes degenerate faces. We don't expect more than this
# for all unit test cases.
MAX_POLYGON_COUNT_LOSS = 10


# ---------------------------------------------------------------------------
# Per-case test runner
# ---------------------------------------------------------------------------

def _find_all_flver_objs() -> list[bpy.types.Object]:
    """Return all FLVER-typed Mesh object in the scene (just-imported)."""
    return T.find_objects_by_soulstruct_type("FLVER")


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
    flver_objs = _find_all_flver_objs()
    if not flver_objs:
        T.fail(case.name, "No FLVER Mesh object found in scene after import")
        return
    if case.expect_two_flvers and len(flver_objs) != 2:
        T.fail(case.name, f"Expected two FLVER Mesh Objects in scene after import. Found: {flver_objs[0].name}")
        return
    elif not case.expect_two_flvers and len(flver_objs) != 1:
        T.fail(case.name, f"Expected one FLVER Mesh Object after import. Found: {','.join(o.name for o in flver_objs)}")
        return

    if case.expect_two_flvers:
        # Name of second FLVER should be name of first plus '_1' suffix.
        if flver_objs[1].name != flver_objs[0].name + "_1":
            T.fail(case.name, f"Expected second FLVER Mesh Object to be named '{flver_objs[0].name}_1' after import")

    for flver_obj in flver_objs:

        # Armature expectation.
        if case.expect_armature:
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

    with tempfile.TemporaryDirectory() as tmpdir:

        # Export each imported FLVER separately.
        exported_paths_1 = []
        for flver_obj in flver_objs:

            model_name = flver_obj.name.split(".")[0].split(" ")[0]

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

            exported_paths_1.append(export_path_1)

        flver_files_1 = sorted(list(Path(tmpdir).glob("*.flver")))
        if not flver_files_1:
            T.fail(case.name, "No .flver found in temp dir after first export")
            return
        if case.expect_two_flvers and len(flver_files_1) != 2:
            T.fail(case.name, "Expected two .flver objects after first export")
            return
        elif not case.expect_two_flvers and len(flver_files_1) != 1:
            T.fail(case.name, "Expected one .flver object after first export")
            return

        reloaded_1 = []  # type: list[FLVER]
        for flver_obj, flver_file in zip(flver_objs, flver_files_1, strict=True):

            # Verify parseable.
            try:
                reloaded = FLVER.from_path(flver_file)
            except Exception as ex:
                T.fail(case.name, f"First exported FLVER not parseable by Soulstruct: {ex}")
                return

            if not reloaded.meshes and flver_obj.data.polygons:
                T.fail(case.name, "First exported FLVER has no meshes but source had polygons")
                return

            reloaded_1.append(reloaded)

        # ---- 4. Re-import the exported FLVER(s) ----
        T.clear_scene()
        T.set_game(case.game_enum)
        bpy.context.scene.flver_import_settings.import_textures = False

        for flver_file in flver_files_1:
            try:
                result2 = bpy.ops.import_scene.flver(
                    "EXEC_DEFAULT",
                    directory=str(Path(tmpdir)),
                    files=[{"name": flver_file.name}],
                )
            except Exception as ex:
                T.fail(case.name, f"Re-import raised exception: {ex}")
                return
            if "FINISHED" not in result2:
                T.fail(case.name, f"Re-import returned {result2}")
                return

        flver_objs_2 = _find_all_flver_objs()
        if not flver_objs_2:
            T.fail(case.name, "No FLVER object found after re-import")
            return
        if case.expect_two_flvers and len(flver_objs_2) != 2:
            T.fail(case.name, "Expected two FLVER Mesh Objects in scene after re-import")
            return
        elif not case.expect_two_flvers and len(flver_objs_2) != 1:
            T.fail(case.name, "Expected one FLVER Mesh Object after re-import")
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
        exported_paths_2 = []
        for flver_obj_2 in flver_objs_2:

            model_name = flver_obj_2.name.split(".")[0].split(" ")[0]

            T.activate(flver_obj_2)
            export_path_2 = str(Path(tmpdir) / f"{model_name}_RE.flver")
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
            exported_paths_2.append(export_path_2)

        # ---- 7. Compare Soulstruct representations ----
        for reloaded in reloaded_1:

            # Have to be careful to find the matching FLVER -- don't rely on sorting.
            flver_file_2 = Path(tmpdir) / f"{reloaded.path_minimal_stem}_RE.flver"
            if not flver_file_2.is_file():
                T.fail(case.name, f"FLVER file {flver_file_2.name} not found in temp dir after second export")
                return

            try:
                reloaded_2 = FLVER.from_path(flver_file_2)
            except Exception as ex:
                T.fail(case.name, f"Second exported FLVER not parseable by Soulstruct: {ex}")
                return

            # Blender export may merge previously separate FLVER submeshes but should never add meshes.
            if len(reloaded.meshes) < len(reloaded_2.meshes):
                T.fail(
                    case.name,
                    f"Mesh count of {reloaded.path_name} vs. {reloaded_2.path_name} "
                    f"increased between export 1 and 2: {len(reloaded.meshes)} vs {len(reloaded_2.meshes)}",
                )
                return
            if len(reloaded.bones) != len(reloaded_2.bones):
                T.fail(
                    case.name,
                    f"Bone count of {reloaded.path} vs. {reloaded_2.path_name} "
                    f"differs between export 1 and 2: {len(reloaded.bones)} vs {len(reloaded_2.bones)}",
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
    T.run_case_list(FLVER_TEST_CASES, run_case, suite_name="FLVER import/export", filter_test_names="DS1PTDE / Map Piece")


main()
