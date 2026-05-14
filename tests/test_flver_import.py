import bpy
import sys
import traceback
from pathlib import Path

ADDON_MODULE = "bl_ext.user_default.io_soulstruct"
IMPORT_FLVER_OP = "import_scene.flver"
EXPORT_FLVER_OP = "export_scene.flver"

DIRECTORY = "C:/Program Files (x86)/Steam/steamapps/common/DARK SOULS REMASTERED/chr/"
FILES = [{"name": "c1200.chrbnd.dcx"}]
# FILES = [{"name": str(file_path.name)} for file_path in Path(DIRECTORY).glob("c2*.chrbnd.dcx")]

def fail(msg: str, code: int = 1):
    print(f"[TEST][FAIL] {msg}")
    sys.exit(code)

def ok(msg: str):
    print(f"[TEST][OK] {msg}")

try:
    # Ensure add-on is enabled in this Blender session.
    bpy.ops.preferences.addon_enable(module=ADDON_MODULE)
    ok(f"Enabled add-on: {ADDON_MODULE}")
except Exception as ex:
    traceback.print_exc()
    fail(f"Could not enable add-on '{ADDON_MODULE}'. Error: {ex}")


# Set up add-on.
bpy.context.scene.soulstruct_settings.game_enum = "DARK_SOULS_DSR"

try:
    # Check operator exists and can run in current context.
    op_fn = bpy.ops
    for part in IMPORT_FLVER_OP.split("."):
        op_fn = getattr(op_fn, part)

    # Optional poll check (if context-sensitive):
    if not op_fn.poll():
        fail(f"Operator poll() failed: {IMPORT_FLVER_OP}")

    result = op_fn(
        "EXEC_DEFAULT",  # or "INVOKE_DEFAULT" where appropriate
        directory=DIRECTORY,
        files=FILES,
    )
    ok(f"Import operator returned: {result}")
except Exception as ex:
    traceback.print_exc()
    fail(f"Import operator execution failed: {IMPORT_FLVER_OP}. Error: {ex}")

try:
    # Try exporting first FLVER.
    bl_flver = bpy.data.objects[0]
    ok(f"Found first FLVER: {bl_flver.name}")

    # Check operator exists and can run in current context.
    op_fn = bpy.ops
    for part in EXPORT_FLVER_OP.split("."):
        op_fn = getattr(op_fn, part)

    # Optional poll check (if context-sensitive):
    if not op_fn.poll():
        fail(f"Operator poll() failed: {EXPORT_FLVER_OP}")

    result = op_fn(
        "EXEC_DEFAULT",  # or "INVOKE_DEFAULT" where appropriate
        filepath=str(Path(__file__).parent / f"{bl_flver.name.split('.')[0]}.flver"),
    )
    ok(f"Export operator returned: {result}")

except Exception as ex:
    traceback.print_exc()
    fail(f"Export operator execution failed: {EXPORT_FLVER_OP}. Error: {ex}")

ok("Headless operator test passed")
sys.exit(0)
