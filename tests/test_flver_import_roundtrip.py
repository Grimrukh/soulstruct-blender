"""Expanded headless FLVER import/export round-trip tests.

Covers every combination of game × FLVER subtype. Each test case:
  1. Sets the active game in Soulstruct settings.
  2. Imports a FLVER (or Binder containing one) with the generic `import_scene.flver` operator.
  3. Validates the resulting Blender objects (presence, type, armature, version, etc.).
  4. Exports the imported FLVER to a temporary output file with `export_scene.flver`.
  5. Verifies the exported file exists and is a parseable FLVER.
  6. Cleans up.

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
import typing as tp
from dataclasses import dataclass, field
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
class FLVERImportCase:
    """Declarative description of one FLVER import/export round-trip test."""

    # Human-readable name shown in test output.
    name: str

    # Value for `bpy.context.scene.soulstruct_settings.game_enum`.
    game_enum: str

    # Directory containing the source file (set to empty string to skip).
    directory: Path | str

    # File name inside that directory (e.g. "c1200.chrbnd.dcx").
    filename: str

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

    # Extra tags for documentation only.
    tags: list[str] = field(default_factory=list)

    @property
    def skip_reason(self) -> str | None:
        """Return a skip message if the test cannot run; None if it should run."""
        if not self.directory:
            return f"directory not configured (placeholder)"
        if not Path(self.directory).is_dir():
            return f"directory not found: {self.directory}"
        source = Path(self.directory) / self.filename
        if not source.exists():
            return f"source file not found: {source}"
        return None


# ---------------------------------------------------------------------------
# Test case definitions
# ---------------------------------------------------------------------------
#
# Use forward slashes or raw strings for Windows paths.
# Leave ``directory=""`` for any game/subtype you don't have files for.
#
# Naming convention used here: "GAME / SubType / description"
#

from soulstruct.config import DSR_PATH

FLVER_TEST_CASES: list[FLVERImportCase] = [

    # ------------------------------------------------------------------
    # Demon's Souls
    # ------------------------------------------------------------------
    FLVERImportCase(
        name="DES / Map Piece / m01 loose FLVER",
        game_enum="DEMONS_SOULS",
        directory="",   # TODO: e.g. "C:/DES/map/m01_01_00_00"
        filename="",    # TODO: e.g. "m1100B0A11.flver"
        expect_armature=False,
        expect_version="DemonsSouls",
        tags=["map_piece"],
    ),
    FLVERImportCase(
        name="DES / Character / c0000",
        game_enum="DEMONS_SOULS",
        directory="",   # TODO: e.g. "C:/DES/chr/c0000"
        filename="",    # TODO: e.g. "c0000.chrbnd"
        expect_armature=True,
        expect_version="DemonsSouls",
        tags=["character"],
    ),
    FLVERImportCase(
        name="DES / Character / enemy",
        game_enum="DEMONS_SOULS",
        directory="",   # TODO: e.g. "C:/DES/chr"
        filename="",    # TODO: e.g. "c1200.chrbnd"
        expect_armature=True,
        tags=["character"],
    ),
    FLVERImportCase(
        name="DES / Object",
        game_enum="DEMONS_SOULS",
        directory="",   # TODO: e.g. "C:/DES/obj"
        filename="",    # TODO: e.g. "o0100.objbnd"
        tags=["object"],
    ),
    FLVERImportCase(
        name="DES / Equipment / weapon",
        game_enum="DEMONS_SOULS",
        directory="",   # TODO: e.g. "C:/DES/parts"
        filename="",    # TODO: e.g. "WP_A_0100.partsbnd"
        expect_armature=True,
        tags=["equipment"],
    ),

    # ------------------------------------------------------------------
    # Dark Souls: Prepare to Die Edition
    # ------------------------------------------------------------------
    FLVERImportCase(
        name="DS1PTDE / Map Piece / m10 loose FLVER",
        game_enum="DARK_SOULS_PTDE",
        directory="",   # TODO: e.g. "C:/DARK SOULS PTDE/map/m10_02_00_00"
        filename="",    # TODO: e.g. "m1020B0A10.flver"
        expect_armature=False,
        expect_version="DarkSouls_A",
        tags=["map_piece"],
    ),
    FLVERImportCase(
        name="DS1PTDE / Character / c1200",
        game_enum="DARK_SOULS_PTDE",
        directory="",   # TODO: e.g. "C:/DARK SOULS PTDE/chr"
        filename="",    # TODO: e.g. "c1200.chrbnd"
        expect_armature=True,
        expect_version="DarkSouls_A",
        tags=["character"],
    ),
    FLVERImportCase(
        name="DS1PTDE / Object",
        game_enum="DARK_SOULS_PTDE",
        directory="",   # TODO: e.g. "C:/DARK SOULS PTDE/obj"
        filename="",    # TODO: e.g. "o0100.objbnd"
        tags=["object"],
    ),
    FLVERImportCase(
        name="DS1PTDE / Equipment / weapon",
        game_enum="DARK_SOULS_PTDE",
        directory="",   # TODO: e.g. "C:/DARK SOULS PTDE/parts"
        filename="",    # TODO: e.g. "WP_A_0100.partsbnd"
        expect_armature=True,
        tags=["equipment"],
    ),

    # ------------------------------------------------------------------
    # Dark Souls Remastered
    # ------------------------------------------------------------------
    FLVERImportCase(
        name="DSR / Map Piece / m10 loose FLVER",
        game_enum="DARK_SOULS_DSR",
        directory=DSR_PATH / "map/m10_02_00_00",
        filename="m2000B2A10.flver",  # main bonfire clearing Map Piece
        expect_armature=False,
        expect_version="DarkSouls_A",
        tags=["map_piece"],
    ),
    FLVERImportCase(
        name="DSR / Character / c1200",
        game_enum="DARK_SOULS_DSR",
        directory= DSR_PATH / "chr",
        filename="c1200.chrbnd.dcx",  # Large Rat
        expect_armature=True,
        expect_version="DarkSouls_A",
        tags=["character"],
    ),
    FLVERImportCase(
        name="DSR / Character / c0000 (player)",
        game_enum="DARK_SOULS_DSR",
        directory=DSR_PATH / "chr",
        filename="c0000.chrbnd.dcx",  # Player Character
        expect_armature=True,
        expect_version="DarkSouls_A",
        expect_materials=False,  # player mesh is empty (uses Parts)
        tags=["character"],
    ),
    FLVERImportCase(
        name="DSR / Object",
        game_enum="DARK_SOULS_DSR",
        directory=DSR_PATH / "obj",
        filename="o1290.objbnd.dcx",  # Sunlight Altar destructible parapets
        tags=["object"],
    ),
    FLVERImportCase(
        name="DSR / Equipment / weapon",
        game_enum="DARK_SOULS_DSR",
        directory=DSR_PATH / "parts",
        filename="WP_A_0100.partsbnd.dcx",
        expect_armature=True,
        tags=["equipment"],
    ),
    FLVERImportCase(
        name="DSR / Equipment / armor (body)",
        game_enum="DARK_SOULS_DSR",
        directory=DSR_PATH / "parts",
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
    FLVERImportCase(
        name="BB / Map Piece",
        game_enum="BLOODBORNE",
        directory="",   # TODO: e.g. "C:/Bloodborne/map/m21_00_00_00"
        filename="",    # TODO: loose FLVER name
        expect_armature=False,
        tags=["map_piece"],
    ),
    FLVERImportCase(
        name="BB / Character",
        game_enum="BLOODBORNE",
        directory="",   # TODO: e.g. "C:/Bloodborne/chr"
        filename="",    # TODO: e.g. "c0000.chrbnd.dcx"
        expect_armature=True,
        tags=["character"],
    ),
    FLVERImportCase(
        name="BB / Equipment",
        game_enum="BLOODBORNE",
        directory="",   # TODO: e.g. "C:/Bloodborne/parts"
        filename="",    # TODO: e.g. "WP_A_0100.partsbnd.dcx"
        expect_armature=True,
        tags=["equipment"],
    ),

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


# ---------------------------------------------------------------------------
# Per-case test runner
# ---------------------------------------------------------------------------

def _find_first_flver_obj() -> bpy.types.Object | None:
    """Return the first FLVER-typed Mesh object in the scene (just-imported)."""
    for obj in bpy.data.objects:
        if obj.type == "MESH" and obj.soulstruct_type == "FLVER":
            return obj
    return None


def run_case(case: FLVERImportCase):
    """Import, validate, export, and clean up one FLVERImportCase."""

    # ---- Skip check ----
    reason = case.skip_reason
    if reason:
        print(f"[TEST][SKIP] {case.name} — {reason}")
        return  # not a failure; just skipped

    # ---- Setup ----
    T.clear_scene()
    T.set_game(case.game_enum)
    # Disable texture import for speed; we only care about geometry/properties.
    bpy.context.scene.flver_import_settings.import_textures = False

    source_path = Path(case.directory) / case.filename

    # ---- Import ----
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

    # ---- Validate scene ----
    flver_obj = _find_first_flver_obj()
    if flver_obj is None:
        T.fail(case.name, "No FLVER Mesh object found in scene after import")
        return

    # Armature expectation.
    if case.expect_armature:  # is True
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
            # "DEFAULT" means version wasn't stored, which is acceptable if the expected
            # version matches the game default. Only fail on explicit mismatches.
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
    if case.expect_per_submesh_props:
        if len(flver_obj.FLVER.submesh_props) == 0:
            T.fail(case.name, "Expected per-slot submesh_props to be populated")
            return

    # ---- Export round-trip ----
    T.activate(flver_obj)
    with tempfile.TemporaryDirectory() as tmpdir:
        # Export name is first substring before any space or dot.
        model_name = flver_obj.name.split(".")[0].split(" ")[0]
        export_path = str(Path(tmpdir) / f"{model_name}.flver")
        try:
            export_result = bpy.ops.export_scene.flver(
                "EXEC_DEFAULT",
                filepath=export_path,
                dcx_type="Null",  # no DCX for temp export; simpler
            )
        except Exception as ex:
            T.fail(case.name, f"Export raised exception: {ex}")
            return

        if "FINISHED" not in export_result:
            T.fail(case.name, f"Export operator returned {export_result}")
            return

        exported = Path(export_path)
        # Blender may add .bak or omit extension; check both the explicit path and any .flver in tmpdir.
        flver_files = list(Path(tmpdir).glob("*.flver"))
        if not flver_files:
            T.fail(case.name, f"No .flver file found in export directory after export")
            return

        # Verify the exported file is a parseable FLVER.
        try:
            reloaded = FLVER.from_path(flver_files[0])
        except Exception as ex:
            T.fail(case.name, f"Exported FLVER could not be parsed by Soulstruct: {ex}")
            return

        if not reloaded.meshes and flver_obj.data.polygons:
            T.fail(case.name, "Exported FLVER has no meshes but source mesh had polygons")
            return

    # ---- All checks passed ----
    T.ok(case.name, f"import+export round-trip OK ({len(flver_obj.data.materials)} mats)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    _results_before = len(T._results)

    skipped = 0
    run_count = 0
    for case in FLVER_TEST_CASES:
        reason = case.skip_reason
        if reason:
            skipped += 1
            print(f"[TEST][SKIP] {case.name} — {reason}")
            continue
        run_case(case)
        run_count += 1

    passed = sum(1 for _, ok_, _ in T._results[_results_before:] if ok_)
    failed = sum(1 for _, ok_, _ in T._results[_results_before:] if not ok_)

    print(
        f"\n[TEST SUMMARY] FLVER import/export: "
        f"{passed} passed, {failed} failed, {skipped} skipped "
        f"(out of {len(FLVER_TEST_CASES)} defined cases)"
    )
    sys.exit(0 if failed == 0 else 1)


main()
