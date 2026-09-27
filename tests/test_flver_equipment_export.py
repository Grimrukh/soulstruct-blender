"""Tests for equipment (PARTSBND) FLVER import/export operators that need real game files.

Covers:
  - Export Equipment for PARTSBNDs holding multiple FLVERs (e.g. weapon + sheath `WP_A_0204_1`): exporting EITHER
    FLVER must write both into their own existing Binder entries, never overwrite the main FLVER's entry 200 with the
    sheath, and never fail to find a `WP_A_0204_1.partsbnd`.
  - Import Armor Set for Demon's Souls, whose PARTSBND names are lowercase ('am_a_8020.partsbnd.dcx').

Cases auto-skip if the relevant game files are absent.

Run with:
    blender --background --python tests/test_flver_equipment_export.py
"""
import sys
import tempfile
import types
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import bpy
import numpy as np

import bl_test_utils as T

T.enable_addon()

from soulstruct.config import Config
from soulstruct.containers import Binder
from soulstruct.flver import FLVER


def _get_armor_set_operator_class():
    """The REGISTERED operator class, whose `armor_set_id_choices` the enum property's items callback reads."""
    return bpy.types.Operator.bl_rna_get_subclass_py("IMPORT_SCENE_OT_armor_set_flvers")


@dataclass
class EquipmentExportCase(T.ImportCaseBase):
    # Game model name of the FLVER to make active before exporting.
    active_model_name: str = ""
    # Every FLVER expected in the PARTSBND (all must be exported, whichever is active).
    expected_model_names: tuple[str, ...] = ()


EXPORT_CASES = [
    EquipmentExportCase(
        name="DSR / WP_A_0204 (Broadsword) / export sheath",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "parts",
        filename="WP_A_0204.partsbnd.dcx",
        active_model_name="WP_A_0204_1",
        expected_model_names=("WP_A_0204", "WP_A_0204_1"),
    ),
    EquipmentExportCase(
        name="DSR / WP_A_0204 (Broadsword) / export sword",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "parts",
        filename="WP_A_0204.partsbnd.dcx",
        active_model_name="WP_A_0204",
        expected_model_names=("WP_A_0204", "WP_A_0204_1"),
    ),
]


# Blender Z offset applied to each FLVER's vertices before export, so each exported entry can be identified.
_Z_OFFSETS = (0.25, 0.5, 0.75)


def _flver_game_y_bounds(flver: FLVER) -> tuple[float, float]:
    """Vertex Y bounds (robust to export re-splitting/duplicating vertices, unlike a mean)."""
    ys = np.concatenate([mesh.vertices["position"][:, 1] for mesh in flver.meshes])
    return float(ys.min()), float(ys.max())


def _flver_entries_by_stem(binder: Binder) -> dict[str, "BinderEntry"]:
    return {
        entry.name.split(".")[0].upper(): entry
        for entry in binder.entries
        if ".flver" in entry.name.lower()
    }


def run_export_case(case: EquipmentExportCase):
    T.clear_scene()
    T.set_game(case.game_enum)
    settings = bpy.context.scene.soulstruct_settings
    game_root = Path(case.directory).parent
    project_root = Path(tempfile.mkdtemp(prefix="ss_equipment_export_"))
    settings.game_settings.game_root_str = str(game_root)
    settings.game_settings.project_root_str = str(project_root)
    settings.also_export_to_game = False
    bpy.context.scene.flver_import_settings.import_textures = False
    bpy.context.scene.flver_export_settings.export_textures = False

    result = bpy.ops.import_scene.equipment_flver(
        "EXEC_DEFAULT", directory=str(case.directory), files=[{"name": case.filename}]
    )
    if "FINISHED" not in result:
        return T.fail(case.name, f"Import returned {result}")

    meshes = {
        obj.name.split(" ")[0].split(".")[0].upper(): obj
        for obj in bpy.data.objects
        if obj.type == "MESH" and obj.soulstruct_type == "FLVER"
    }
    T.assert_equal(
        sorted(meshes), sorted(case.expected_model_names), f"{case.name}/imported_flvers"
    )

    # Offset each FLVER's vertices by a distinct amount.
    z_offsets = dict(zip(case.expected_model_names, _Z_OFFSETS))
    for model_name, z_offset in z_offsets.items():
        for vertex in meshes[model_name].data.vertices:
            vertex.co.z += z_offset

    # Select ONLY the chosen FLVER (siblings must still be found for export).
    for obj in bpy.data.objects:
        obj.select_set(False)
    active = meshes[case.active_model_name]
    active.select_set(True)
    bpy.context.view_layer.objects.active = active

    result = bpy.ops.export_scene.equipment_flver("EXEC_DEFAULT")
    if "FINISHED" not in result:
        return T.fail(case.name, f"Export returned {result}")

    exported_paths = list((project_root / "parts").glob(f"{case.expected_model_names[0]}.partsbnd*"))
    stray_paths = [
        path for path in (project_root / "parts").glob("*.partsbnd*") if path not in exported_paths
    ]
    T.assert_equal(stray_paths, [], f"{case.name}/no_stray_partsbnds")
    if len(exported_paths) != 1:
        return T.fail(case.name, f"Expected one exported PARTSBND, found: {exported_paths}")

    original = Binder.from_path(Path(case.directory) / case.filename)
    exported = Binder.from_path(exported_paths[0])
    original_entries = _flver_entries_by_stem(original)
    exported_entries = _flver_entries_by_stem(exported)

    T.assert_equal(
        {stem: (e.entry_id, e.path) for stem, e in exported_entries.items()},
        {stem: (e.entry_id, e.path) for stem, e in original_entries.items()},
        f"{case.name}/flver_entry_ids_and_paths",
    )

    for model_name, z_offset in z_offsets.items():
        original_flver = FLVER.from_binder_entry(original_entries[model_name.upper()])
        exported_flver = FLVER.from_binder_entry(exported_entries[model_name.upper()])
        (orig_min, orig_max), (new_min, new_max) = _flver_game_y_bounds(original_flver), _flver_game_y_bounds(exported_flver)
        shifts = (new_min - orig_min, new_max - orig_max)
        T.assert_true(
            all(abs(shift - z_offset) < 1e-3 for shift in shifts),
            f"{case.name}/{model_name}_exported_into_own_entry",
            f"expected game Y bounds shift {z_offset}, got {tuple(round(x, 4) for x in shifts)}",
        )


def test_des_armor_set_ids():
    """DeS PARTSBND names are lowercase ('am_a_8020.partsbnd.dcx'), which used to yield no armor set IDs at all."""
    parts_dir = Config.DES_PATH / "parts"
    if not parts_dir.is_dir():
        print(f"\\[TEST][yellow]\\[SKIP][/yellow] test_des_armor_set_ids — missing {parts_dir}")
        return
    stub_operator = types.SimpleNamespace(warning=print)
    armor_set_ids = _get_armor_set_operator_class().find_armor_set_ids(stub_operator, parts_dir)
    T.assert_true(8020 in armor_set_ids, "test_des_armor_set_ids", f"found {len(armor_set_ids)} armor set IDs")


def test_des_import_armor_set():
    parts_dir = Config.DES_PATH / "parts"
    if not (parts_dir / "am_a_8020.partsbnd.dcx").is_file():
        print(f"\\[TEST][yellow]\\[SKIP][/yellow] test_des_import_armor_set — missing {parts_dir}")
        return
    T.clear_scene()
    T.set_game("DEMONS_SOULS")
    settings = bpy.context.scene.soulstruct_settings
    settings.game_settings.game_root_str = str(Config.DES_PATH)
    settings.game_settings.project_root_str = ""
    bpy.context.scene.flver_import_settings.import_textures = False
    _get_armor_set_operator_class().armor_set_id_choices = [("8020", "8020", "8020")]
    result = bpy.ops.import_scene.armor_set_flvers("EXEC_DEFAULT", armor_set_id="8020", use_c0000_armature=False)
    T.assert_true("FINISHED" in result, "test_des_import_armor_set/result", str(result))
    names = sorted(obj.name for obj in bpy.data.objects if obj.type == "MESH" and obj.soulstruct_type == "FLVER")
    T.assert_true(
        any(name.upper().startswith("AM_A_8020") for name in names),
        "test_des_import_armor_set/imported",
        f"imported FLVERs: {names}",
    )


def main():
    test_fns = []
    for case in EXPORT_CASES:
        reason = case.check_skip_reason()
        if reason:
            print(f"\\[TEST][yellow]\\[SKIP][/yellow] {case.name} — {reason}")
            continue
        fn = lambda c=case: run_export_case(c)
        fn.__name__ = case.name
        test_fns.append(fn)
    T.run_tests(test_fns + [test_des_armor_set_ids, test_des_import_armor_set])


main()
