"""Tests for FLVER object operators (no game files required).

Covers:
  - AddFLVERSubmeshProperties     (flver.add_submesh_props)
  - ClearFLVERSubmeshProperties   (flver.clear_submesh_props)
  - FLVERMaterialSlotAdd          (flver.material_slot_add)
  - FLVERMaterialSlotRemove       (flver.material_slot_remove)
  - FLVERMaterialSlotMove         (flver.material_slot_move)
  - SelectMeshChildren            (object.select_mesh_children)
  - HideAllDummiesOperator        (object.hide_all_flver_dummies)
  - ShowAllDummiesOperator        (object.show_all_flver_dummies)

Run with:
    blender --background --python tests/test_flver_object_ops.py
"""
import sys
from pathlib import Path

# Ensure this tests/ directory is on the path so bl_test_utils is importable.
sys.path.insert(0, str(Path(__file__).parent))

import bpy
import bl_test_utils as T

T.enable_addon()
T.set_game("DARK_SOULS_DSR")

OBJECT_TESTS = []

# ---------------------------------------------------------------------------
# AddFLVERSubmeshProperties
# ---------------------------------------------------------------------------

@T.register_bl_test(OBJECT_TESTS)
def test_add_submesh_props_creates_one_per_slot():
    T.clear_scene()
    obj = T.make_flver_mesh_with_materials("m", ["MatA", "MatB", "MatC"])
    T.activate(obj)

    result = T.call_op("flver.add_submesh_props")
    T.assert_equal(result, {"FINISHED"}, "test_add_submesh_props_creates_one_per_slot/result")
    T.assert_equal(
        len(obj.FLVER.submesh_props), 3,
        "test_add_submesh_props_creates_one_per_slot/count",
        "Expected one submesh prop per material slot",
    )


@T.register_bl_test(OBJECT_TESTS)
def test_add_submesh_props_inherits_global_values():
    T.clear_scene()
    obj = T.make_flver_mesh_with_materials("m", ["MatA"])
    T.activate(obj)
    obj.FLVER.global_is_dynamic = False
    obj.FLVER.global_default_bone_index = 7
    obj.FLVER.global_face_set_count = 2

    T.call_op("flver.add_submesh_props")
    entry = obj.FLVER.submesh_props[0]
    T.assert_equal(entry.is_dynamic, False, "test_add_submesh_props_inherits_global_values/is_dynamic")
    T.assert_equal(entry.default_bone_index, 7, "test_add_submesh_props_inherits_global_values/bone_index")
    T.assert_equal(entry.face_set_count, 2, "test_add_submesh_props_inherits_global_values/face_set_count")
    T.assert_equal(
        entry.use_backface_culling, "MATERIAL",
        "test_add_submesh_props_inherits_global_values/backface_culling",
    )


@T.register_bl_test(OBJECT_TESTS)
def test_add_submesh_props_on_empty_mesh():
    """Object with no material slots should produce an empty submesh_props collection."""
    T.clear_scene()
    obj = T.make_flver_mesh("m_empty")
    T.activate(obj)

    T.call_op("flver.add_submesh_props")
    T.assert_equal(
        len(obj.FLVER.submesh_props), 0,
        "test_add_submesh_props_on_empty_mesh",
        "No slots → no submesh props",
    )


# ---------------------------------------------------------------------------
# ClearFLVERSubmeshProperties
# ---------------------------------------------------------------------------

@T.register_bl_test(OBJECT_TESTS)
def test_clear_submesh_props_empties_collection():
    T.clear_scene()
    obj = T.make_flver_mesh_with_materials("m", ["MatA", "MatB"])
    T.activate(obj)
    T.call_op("flver.add_submesh_props")
    assert len(obj.FLVER.submesh_props) == 2

    result = T.call_op("flver.clear_submesh_props")
    T.assert_equal(result, {"FINISHED"}, "test_clear_submesh_props_empties_collection/result")
    T.assert_equal(
        len(obj.FLVER.submesh_props), 0,
        "test_clear_submesh_props_empties_collection/count",
    )


# ---------------------------------------------------------------------------
# FLVERMaterialSlotAdd
# ---------------------------------------------------------------------------

@T.register_bl_test(OBJECT_TESTS)
def test_material_slot_add_without_submesh_props():
    """Adding a slot when not in per-slot mode should not create submesh props."""
    T.clear_scene()
    obj = T.make_flver_mesh("m")  # no submesh_props
    T.activate(obj)

    T.call_op("flver.material_slot_add")
    T.assert_equal(len(obj.material_slots), 1, "test_material_slot_add_without_submesh_props/slot_count")
    T.assert_equal(
        len(obj.FLVER.submesh_props), 0,
        "test_material_slot_add_without_submesh_props/no_submesh_props",
        "Should stay empty because per-slot mode is inactive",
    )


@T.register_bl_test(OBJECT_TESTS)
def test_material_slot_add_with_submesh_props():
    """Adding a slot when in per-slot mode should append a submesh props entry."""
    T.clear_scene()
    obj = T.make_flver_mesh_with_materials("m", ["MatA"])
    T.activate(obj)
    T.call_op("flver.add_submesh_props")  # activate per-slot mode
    assert len(obj.FLVER.submesh_props) == 1

    T.call_op("flver.material_slot_add")
    T.assert_equal(len(obj.material_slots), 2, "test_material_slot_add_with_submesh_props/slot_count")
    T.assert_equal(
        len(obj.FLVER.submesh_props), 2,
        "test_material_slot_add_with_submesh_props/prop_count",
        "Submesh props must grow with slot count",
    )


# ---------------------------------------------------------------------------
# FLVERMaterialSlotRemove
# ---------------------------------------------------------------------------

@T.register_bl_test(OBJECT_TESTS)
def test_material_slot_remove_syncs_submesh_props():
    """Removing the active slot should remove the matching submesh props entry."""
    T.clear_scene()
    obj = T.make_flver_mesh_with_materials("m", ["MatA", "MatB", "MatC"])
    T.activate(obj)
    T.call_op("flver.add_submesh_props")
    # Modify middle entry so we can tell which one was kept.
    obj.FLVER.submesh_props[1].default_bone_index = 42

    # Remove middle slot (index 1).
    obj.active_material_index = 1
    T.call_op("flver.material_slot_remove")

    T.assert_equal(len(obj.material_slots), 2, "test_material_slot_remove_syncs_submesh_props/slot_count")
    T.assert_equal(len(obj.FLVER.submesh_props), 2, "test_material_slot_remove_syncs_submesh_props/prop_count")
    # The entry that was at index 2 (bone_index=0) should now be at index 1.
    T.assert_equal(
        obj.FLVER.submesh_props[1].default_bone_index, 0,
        "test_material_slot_remove_syncs_submesh_props/remaining_entry",
        "Old index-2 entry should now be at index 1",
    )


@T.register_bl_test(OBJECT_TESTS)
def test_material_slot_remove_first_slot():
    T.clear_scene()
    obj = T.make_flver_mesh_with_materials("m", ["MatA", "MatB"])
    T.activate(obj)
    T.call_op("flver.add_submesh_props")
    obj.FLVER.submesh_props[0].default_bone_index = 99  # mark slot 0

    obj.active_material_index = 0
    T.call_op("flver.material_slot_remove")

    T.assert_equal(len(obj.material_slots), 1, "test_material_slot_remove_first_slot/slot_count")
    T.assert_equal(
        obj.FLVER.submesh_props[0].default_bone_index, 0,
        "test_material_slot_remove_first_slot/remaining",
        "Old slot-1 entry (bone_index=0) should now be at index 0",
    )


# ---------------------------------------------------------------------------
# FLVERMaterialSlotMove
# ---------------------------------------------------------------------------

@T.register_bl_test(OBJECT_TESTS)
def test_material_slot_move_up_syncs_submesh_props():
    T.clear_scene()
    obj = T.make_flver_mesh_with_materials("m", ["MatA", "MatB", "MatC"])
    T.activate(obj)
    T.call_op("flver.add_submesh_props")
    obj.FLVER.submesh_props[0].default_bone_index = 10
    obj.FLVER.submesh_props[1].default_bone_index = 20
    obj.FLVER.submesh_props[2].default_bone_index = 30

    # Move slot at index 1 up to index 0.
    obj.active_material_index = 1
    T.call_op("flver.material_slot_move", direction="UP")

    T.assert_equal(
        obj.FLVER.submesh_props[0].default_bone_index, 20,
        "test_material_slot_move_up/new_index0",
    )
    T.assert_equal(
        obj.FLVER.submesh_props[1].default_bone_index, 10,
        "test_material_slot_move_up/new_index1",
    )
    T.assert_equal(
        obj.FLVER.submesh_props[2].default_bone_index, 30,
        "test_material_slot_move_up/index2_unchanged",
    )


@T.register_bl_test(OBJECT_TESTS)
def test_material_slot_move_down_syncs_submesh_props():
    T.clear_scene()
    obj = T.make_flver_mesh_with_materials("m", ["MatA", "MatB", "MatC"])
    T.activate(obj)
    T.call_op("flver.add_submesh_props")
    obj.FLVER.submesh_props[0].default_bone_index = 10
    obj.FLVER.submesh_props[1].default_bone_index = 20
    obj.FLVER.submesh_props[2].default_bone_index = 30

    # Move slot at index 1 down to index 2.
    obj.active_material_index = 1
    T.call_op("flver.material_slot_move", direction="DOWN")

    T.assert_equal(
        obj.FLVER.submesh_props[0].default_bone_index, 10,
        "test_material_slot_move_down/index0_unchanged",
    )
    T.assert_equal(
        obj.FLVER.submesh_props[1].default_bone_index, 30,
        "test_material_slot_move_down/new_index1",
    )
    T.assert_equal(
        obj.FLVER.submesh_props[2].default_bone_index, 20,
        "test_material_slot_move_down/new_index2",
    )


@T.register_bl_test(OBJECT_TESTS)
def test_material_slot_move_up_at_top_is_noop():
    """Moving the first slot UP should leave order unchanged."""
    T.clear_scene()
    obj = T.make_flver_mesh_with_materials("m", ["MatA", "MatB"])
    T.activate(obj)
    T.call_op("flver.add_submesh_props")
    obj.FLVER.submesh_props[0].default_bone_index = 10
    obj.FLVER.submesh_props[1].default_bone_index = 20

    obj.active_material_index = 0
    T.call_op("flver.material_slot_move", direction="UP")

    T.assert_equal(
        obj.FLVER.submesh_props[0].default_bone_index, 10,
        "test_material_slot_move_up_at_top_is_noop/slot0",
    )
    T.assert_equal(
        obj.FLVER.submesh_props[1].default_bone_index, 20,
        "test_material_slot_move_up_at_top_is_noop/slot1",
    )


# ---------------------------------------------------------------------------
# SelectMeshChildren
# ---------------------------------------------------------------------------

@T.register_bl_test(OBJECT_TESTS)
def test_select_mesh_children_selects_children_and_deselects_armature():
    T.clear_scene()

    # Create an armature with two mesh children and one non-mesh child.
    arm_data = bpy.data.armatures.new("TestArm")
    arm_obj = bpy.data.objects.new("TestArm", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)

    child_mesh_a = T.make_flver_mesh("ChildA")
    child_mesh_b = T.make_flver_mesh("ChildB")
    child_mesh_a.parent = arm_obj
    child_mesh_b.parent = arm_obj

    # Select only the armature.
    bpy.ops.object.select_all(action="DESELECT")
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    result = T.call_op("object.select_mesh_children")
    T.assert_equal(result, {"FINISHED"}, "test_select_mesh_children/result")
    T.assert_true(child_mesh_a.select_get(), "test_select_mesh_children/child_a_selected")
    T.assert_true(child_mesh_b.select_get(), "test_select_mesh_children/child_b_selected")
    T.assert_true(not arm_obj.select_get(), "test_select_mesh_children/armature_deselected")


# ---------------------------------------------------------------------------
# HideAllDummiesOperator / ShowAllDummiesOperator
# ---------------------------------------------------------------------------

def _make_flver_with_dummies() -> tuple[bpy.types.Object, list[bpy.types.Object]]:
    """Create a FLVER mesh with two FLVER_DUMMY empty children."""
    T.clear_scene()
    obj = T.make_flver_mesh_with_armature_parent("TestFLVER")
    dummies = []
    for i in range(2):
        dummy = bpy.data.objects.new(f"TestFLVER Dummy<{i}> [0]", None)  # Empty
        dummy.soulstruct_type = "FLVER_DUMMY"
        dummy.parent = obj.parent  # Armature
        bpy.context.scene.collection.objects.link(dummy)
        dummies.append(dummy)
    T.activate(obj)
    return obj, dummies


@T.register_bl_test(OBJECT_TESTS)
def test_hide_all_dummies():
    obj, dummies = _make_flver_with_dummies()
    for d in dummies:
        d.hide_viewport = False

    result = T.call_op("object.hide_all_flver_dummies")
    T.assert_equal(result, {"FINISHED"}, "test_hide_all_dummies/result")
    for i, d in enumerate(dummies):
        T.assert_true(d.hide_viewport, f"test_hide_all_dummies/dummy_{i}_hidden")


@T.register_bl_test(OBJECT_TESTS)
def test_show_all_dummies():
    obj, dummies = _make_flver_with_dummies()
    for d in dummies:
        d.hide_viewport = True

    result = T.call_op("object.show_all_flver_dummies")
    T.assert_equal(result, {"FINISHED"}, "test_show_all_dummies/result")
    for i, d in enumerate(dummies):
        T.assert_true(not d.hide_viewport, f"test_show_all_dummies/dummy_{i}_visible")


@T.register_bl_test(OBJECT_TESTS)
def test_hide_then_show_dummies():
    obj, dummies = _make_flver_with_dummies()
    T.call_op("object.hide_all_flver_dummies")
    T.call_op("object.show_all_flver_dummies")
    for i, d in enumerate(dummies):
        T.assert_true(not d.hide_viewport, f"test_hide_then_show/dummy_{i}_visible_after_show")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

T.run_tests(OBJECT_TESTS)
