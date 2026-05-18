"""Shared utilities for headless Blender operator tests.

All test scripts should import from this module. Run individual test scripts with:

    blender --background --python tests/<test_file>.py

or run all at once:

    blender --background --python tests/run_all_tests.py

Each test file calls `run_tests()` at the end, which will `sys.exit(0)` on full pass
or `sys.exit(1)` on any failure.
"""
from __future__ import annotations

import sys
import traceback
import typing as tp
from rich import print

import bpy

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ADDON_MODULE = "bl_ext.user_default.io_soulstruct"

# ---------------------------------------------------------------------------
# Pass / fail helpers
# ---------------------------------------------------------------------------

_results: list[tuple[str, bool, str]] = []  # (test_name, passed, message)


def ok(test_name: str, msg: str = ""):
    full = f"[green]\\[OK][/green]  {test_name}" + (f" — {msg}" if msg else "")
    print(f"\\[TEST]{full}")
    _results.append((test_name, True, msg))


def fail(test_name: str, msg: str, code: int = 1):
    full = f"[red]\\[FAIL][/red]{test_name} — {msg}"
    print(f"\\[TEST]{full}")
    _results.append((test_name, False, msg))


def assert_true(condition: bool, test_name: str, msg: str = ""):
    if condition:
        ok(test_name, msg)
    else:
        fail(test_name, msg or "assertion failed")


def assert_equal(a, b, test_name: str, msg: str = ""):
    if a == b:
        ok(test_name, msg or f"{a!r} == {b!r}")
    else:
        fail(test_name, msg or f"expected {b!r}, got {a!r}")


def run_test(test_name: str, fn: tp.Callable):
    """Run a single test function, catching any exception as a failure."""
    try:
        fn()
        # fn() calls ok/fail itself; we only catch unexpected exceptions here
    except Exception as ex:
        traceback.print_exc()
        fail(test_name, f"Unexpected exception: {ex}")


def run_tests(test_fns: list[tp.Callable]):
    """Run all test functions and exit with 0/1 based on results."""
    _results.clear()
    for fn in test_fns:
        run_test(fn.__name__, fn)

    passed = sum(1 for _, ok_, _ in _results if ok_)
    failed = sum(1 for _, ok_, _ in _results if not ok_)
    fail_msg = "[red]failed[/red]" if failed > 0 else "failed"
    print(f"\n\\[TEST SUMMARY] {passed} [green]passed[/green], {failed} {fail_msg} out of {len(_results)} tests.")
    sys.exit(0 if failed == 0 else 1)


# ---------------------------------------------------------------------------
# Addon setup
# ---------------------------------------------------------------------------

def enable_addon():
    """Enable the io_soulstruct addon. Call once at the top of each test script."""
    try:
        bpy.ops.preferences.addon_enable(module=ADDON_MODULE)
        print(f"\\[TEST] Enabled add-on: {ADDON_MODULE}")
    except Exception as ex:
        traceback.print_exc()
        print(f"\\[TEST][red]\\[FATAL][/red] Could not enable add-on '{ADDON_MODULE}': {ex}")
        sys.exit(2)


def set_game(game_enum: str = "DARK_SOULS_DSR"):
    """Set the active game in Soulstruct settings."""
    bpy.context.scene.soulstruct_settings.game_enum = game_enum


# ---------------------------------------------------------------------------
# Scene helpers
# ---------------------------------------------------------------------------

def clear_scene():
    """Delete all objects in the current scene."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    # Also remove orphaned mesh/material data
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        if mat.users == 0:
            bpy.data.materials.remove(mat)


def make_flver_mesh(name: str = "TestFLVER") -> bpy.types.Object:
    """Create a minimal FLVER Mesh object linked to the active scene collection."""
    mesh_data = bpy.data.meshes.new(name=name)
    obj = bpy.data.objects.new(name=name, object_data=mesh_data)
    obj.soulstruct_type = "FLVER"
    bpy.context.scene.collection.objects.link(obj)
    return obj


def make_flver_mesh_with_armature_parent(name: str = "TestFLVER") -> bpy.types.Object:
    """Create a minimal FLVER Mesh object linked to the active scene collection."""
    mesh_data = bpy.data.meshes.new(name=name)
    obj = bpy.data.objects.new(name=name, object_data=mesh_data)
    obj.soulstruct_type = "FLVER"
    bpy.context.scene.collection.objects.link(obj)

    armature_data = bpy.data.armatures.new(name=f"{name} Armature")
    armature_obj = bpy.data.objects.new(name=f"{name} Armature", object_data=armature_data)
    bpy.context.scene.collection.objects.link(armature_obj)

    obj.parent = armature_obj

    # Still return Mesh child.
    return obj


def make_flver_mesh_with_materials(name: str = "TestFLVER", mat_names: list[str] = None) -> bpy.types.Object:
    """Create a FLVER Mesh object with the given materials already assigned."""
    obj = make_flver_mesh(name)
    for mat_name in (mat_names or []):
        mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
        obj.data.materials.append(mat)
    return obj


def activate(obj: bpy.types.Object):
    """Deselect all, select and activate `obj`, ensure Object mode."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


def call_op(op_path: str, mode: str = "EXEC_DEFAULT", **kwargs) -> set[str]:
    """Call a bpy.ops operator by dotted path and return the result set."""
    fn = bpy.ops
    for part in op_path.split("."):
        fn = getattr(fn, part)
    return fn(mode, **kwargs)


def register_bl_test(test_list: list[tp.Callable]) -> tp.Callable:
    """Decorate a test to register it for auto-calling in a given list of test functions.

    Decorator generator.
    """

    def decorator(test_func: tp.Callable) -> tp.Callable:

        test_list.append(test_func)
        return test_func

    return decorator
