"""Shared utilities for headless Blender operator tests.

All test scripts should import from this module. Run individual test scripts with:

    blender --background --python tests/<test_file>.py

or run all at once:

    blender --background --python tests/run_all_tests.py

Each test file calls `run_tests()` at the end, which will `sys.exit(0)` on full pass
or `sys.exit(1)` on any failure.
"""
from __future__ import annotations

import logging
import re
import sys
import traceback
import typing as tp
from dataclasses import dataclass, field
from pathlib import Path

from pyrelink.core import Binder
from rich import print

import bpy

_LOGGER = logging.getLogger("soulstruct.blender")

# ---------------------------------------------------------------------------
# Binder entry filename helpers
# ---------------------------------------------------------------------------

# Matches "binder_filename[entry_name]", e.g. "c1200.chrbnd.dcx[c1200.flver]"
_BINDER_ENTRY_RE = re.compile(r"^(.+)\[(.+)\]$")

# Module-level Binder cache: full binder path → loaded Binder.
# Lives for the lifetime of the Python process (one Blender background run),
# so each binder file is read from disk at most once per session.
_binder_cache: dict[Path, Binder] = {}

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ADDON_MODULE = "bl_ext.user_default.io_soulstruct"

# ---------------------------------------------------------------------------
# Test case base
# ---------------------------------------------------------------------------

@dataclass
class ImportCaseBase:
    """Shared base for all import/export round-trip test case dataclasses.

    ``directory`` / ``filename`` always point to the primary source file for
    that test (e.g. the ANIBND for animation cases, the .msb for MSB cases).
    Subclasses may add extra path fields where a second source file is needed.
    """

    # Human-readable label shown in test output.
    name: str

    # Value for ``bpy.context.scene.soulstruct_settings.game_enum``.
    game_enum: str

    # Directory containing the source file (empty string → skip).
    directory: Path | str

    # File name inside that directory (empty string → skip).
    filename: str

    # Extra tags for documentation only.
    tags: list[str] = field(default_factory=list)

    # Convenience toggle for WIP tests.
    enabled: bool = True

    @property
    def _binder_match(self) -> re.Match | None:
        """Return the regex match if filename is in 'binder[entry]' format, else None."""
        return _BINDER_ENTRY_RE.match(self.filename) if self.filename else None

    @property
    def binder_filename(self) -> str | None:
        """The binder file name when filename is 'binder[entry]', else None."""
        m = self._binder_match
        return m.group(1) if m else None

    @property
    def binder_entry_name(self) -> str | None:
        """The entry name inside the binder when filename is 'binder[entry]', else None."""
        m = self._binder_match
        return m.group(2) if m else None

    @property
    def operator_filename(self) -> str:
        """Filename to pass as ``files=[{"name": ...}]`` to Blender import operators.

        For plain filenames this equals ``filename``.  For the ``binder[entry]``
        format this returns just the binder filename (the operator handles
        internal entry selection).
        """
        bn = self.binder_filename
        return bn if bn is not None else self.filename

    def get_binder(self) -> Binder:
        """Return the loaded Binder for a ``binder[entry]`` filename, using the
        module-level cache so each binder file is read at most once per session.

        Raises ``ValueError`` if ``filename`` is not in ``binder[entry]`` format,
        or any exception raised by ``Binder.from_path`` / ``find_entry_by_name``.
        """
        bn = self.binder_filename
        if bn is None:
            raise ValueError(
                f"get_binder() called on a case whose filename is not in "
                f"'binder[entry]' format: {self.filename!r}"
            )
        binder_path = Path(self.directory) / bn
        if binder_path not in _binder_cache:
            # TODO: Firelink support for auto-detect split path.
            if "bhd" in binder_path.name:
                bdt_path = binder_path.with_name(binder_path.name.replace("bhd", "bdt"))
                bhd_bytes = binder_path.read_bytes()
                bdt_bytes = bdt_path.read_bytes()
                _binder_cache[binder_path] = Binder.from_split_bytes(bhd_bytes, bdt_bytes)
            else:
                _binder_cache[binder_path] = Binder.from_path(binder_path)
        return _binder_cache[binder_path]

    @property
    def source_path(self) -> Path:
        """Path to the primary source for existence checks.

        For ``binder[entry]`` filenames this is the binder file itself.
        """
        bn = self.binder_filename
        return Path(self.directory) / (bn if bn is not None else self.filename)

    def check_skip_reason(self) -> str | None:
        """Return a human-readable skip message, or None if the test should run."""
        if not self.enabled:
            return "test not enabled"
        if not self.directory:
            return "directory not configured (placeholder)"
        if not Path(self.directory).is_dir():
            return f"directory not found: {self.directory}"
        if not self.filename:
            return "filename not configured (placeholder)"

        bn = self.binder_filename
        entry_name = self.binder_entry_name

        if bn is not None:
            # "binder[entry]" format — verify the binder exists and the entry is inside.
            binder_path = Path(self.directory) / bn
            if not binder_path.exists():
                return f"binder not found: {binder_path}"
            try:
                binder = self.get_binder()
                entry = binder.find_entry_by_name(entry_name)
                if entry is None:
                    return f"entry '{entry_name}' not found in binder: {bn}"
            except Exception as ex:
                return f"could not read binder '{bn}': {ex}"
        else:
            if not self.source_path.exists():
                return f"source file not found: {self.source_path}"

        return None


# ---------------------------------------------------------------------------
# Scene query helpers
# ---------------------------------------------------------------------------

def find_objects_by_soulstruct_type(stype: str) -> list[bpy.types.Object]:
    """Return every scene object whose ``soulstruct_type`` property equals *stype*."""
    return [obj for obj in bpy.data.objects if obj.soulstruct_type == stype]


def find_layer_collection(layer_coll: bpy.types.LayerCollection, name: str):
    """Recursively search for a ``LayerCollection`` by its underlying collection name."""
    if layer_coll.collection.name == name:
        return layer_coll
    for child in layer_coll.children:
        result = find_layer_collection(child, name)
        if result:
            return result
    return None


# ---------------------------------------------------------------------------
# Pass / fail helpers
# ---------------------------------------------------------------------------

_results: list[tuple[str, bool, str]] = []  # (test_name, passed, message)


def ok(test_name: str, msg: str = ""):
    full = f"[green]\\[OK][/green]   {test_name}" + (f" — {msg}" if msg else "")
    print(f"\\[TEST]{full}")
    _results.append((test_name, True, msg))


def fail(test_name: str, msg: str, code: int = 1):
    full = f"[red]\\[FAIL][/red] {test_name} — {msg}"
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
    """Wipe all user-created data from bpy.data to ensure a clean state between tests."""
    _DATA_COLLECTIONS = [
        bpy.data.objects,
        bpy.data.meshes,
        bpy.data.armatures,
        bpy.data.materials,
        bpy.data.textures,
        bpy.data.images,
        bpy.data.curves,
        bpy.data.lights,
        bpy.data.cameras,
        bpy.data.actions,
        bpy.data.collections,
        bpy.data.node_groups,
        bpy.data.lattices,
        bpy.data.metaballs,
        bpy.data.particles,
    ]
    for collection in _DATA_COLLECTIONS:
        for item in list(collection):
            try:
                item.use_fake_user = False
                collection.remove(item)
            except Exception:
                pass  # built-in/protected data blocks can't be removed


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


def make_flver_mesh_with_materials(name: str = "TestFLVER", mat_names: tp.Sequence[str] = ()) -> bpy.types.Object:
    """Create a FLVER Mesh object with the given materials already assigned."""
    obj = make_flver_mesh(name)
    for mat_name in mat_names:
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

# ---------------------------------------------------------------------------
# Case-list runner
# ---------------------------------------------------------------------------

def run_case_list(
    case_list: list[ImportCaseBase],
    run_case_fn: tp.Callable,
    suite_name: str = "",
    filter_test_names: str = "",
):
    """Run every case in *case_list* through *run_case_fn*, print a summary, then exit.

    Skipped cases (``check_skip_reason()`` is not None) are reported but do not count
    as failures.  Exits with code 0 on full pass, 1 on any failure.
    """

    # Increase "soulstruct.blender" logging thresholds to WARNING to avoid INFO spam.
    _LOGGER.setLevel(logging.WARNING)
    _LOGGER.blender_log_level = logging.WARNING

    before = len(_results)
    skipped = 0
    for case in case_list:
        if filter_test_names and filter_test_names not in case.name:
            continue  # manually skipped
        reason = case.check_skip_reason()
        if reason:
            skipped += 1
            print(f"\\[TEST][yellow]\\[SKIP][/yellow] {case.name} — {reason}")
            continue
        run_test(case.name, lambda c=case: run_case_fn(c))

    passed = sum(1 for _, ok_, _ in _results[before:] if ok_)
    failed = sum(1 for _, ok_, _ in _results[before:] if not ok_)
    label = f" [{suite_name}]" if suite_name else ""
    print(
        f"\n\\[TEST SUMMARY]{label} "
        f"{passed} [green]passed[/green], "
        f"{failed} {'[red]failed[/red]' if failed else 'failed'}, "
        f"{skipped} [yellow]skipped[/yellow]  (out of {len(case_list)} defined cases)"
    )
    sys.exit(0 if failed == 0 else 1)
