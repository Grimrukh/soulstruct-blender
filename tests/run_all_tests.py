"""Run all headless operator tests in sequence.

Usage:
    blender --background --python tests/run_all_tests.py

Each sub-script is run as a fresh subprocess so that scene state does not bleed between
suites. Exit code is 0 only if every suite passes.
"""
import subprocess
import sys
from pathlib import Path

BLENDER_EXE = sys.argv[0]  # Blender passes itself as sys.argv[0] when --background is used
TESTS_DIR = Path(__file__).parent

TEST_SCRIPTS = [
    # Pure scene-manipulation tests (no game files needed):
    "test_flver_object_ops.py",
    "test_flver_mesh_ops.py",
    "test_flver_material_ops.py",
    # Import/export round-trip tests (game files required; cases auto-skip if not present):
    "test_flver_import_roundtrip.py",
    "test_collision_import_roundtrip.py",
    "test_nvm_import_roundtrip.py",
    "test_msb_import_roundtrip.py",
    "test_hkx_animation_import_roundtrip.py",
]

overall_pass = True
for script in TEST_SCRIPTS:
    script_path = TESTS_DIR / script
    print(f"\n{'='*60}")
    print(f"Running: {script}")
    print("=" * 60)
    proc = subprocess.run(
        [BLENDER_EXE, "--background", "--python", str(script_path)],
        capture_output=False,
    )
    if proc.returncode != 0:
        print(f"[SUITE FAIL] {script} exited with code {proc.returncode}")
        overall_pass = False
    else:
        print(f"[SUITE PASS] {script}")

print(f"\n{'='*60}")
if overall_pass:
    print("[green][bold]ALL SUITES PASSED[/bold][/green]")
    sys.exit(0)
else:
    print("[red][bold]ONE OR MORE SUITES FAILED[/bold][/red]")
    sys.exit(1)
