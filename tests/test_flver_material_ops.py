"""Tests for FLVER material operators (no game files required).

Covers:
  - MergeFLVERMaterials  (object.merge_flver_materials)

RegenerateFLVERMaterialShaders and RegenerateAllFLVERMaterialShaders are NOT covered here
because they require a game MTDBND/MATBINBND on disk. Test them separately with game files
present.

Run with:
    blender --background --python tests/test_flver_material_ops.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import bpy
import bl_test_utils as T

T.enable_addon()
T.set_game("DARK_SOULS_DSR")


MATERIAL_OPS_TESTS = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_flver_material(name: str, mat_def_path: str = "M[DB][M].mtd") -> bpy.types.Material:
    """Create a minimal FLVER material with `mat_def_path` set so it is recognizable."""
    mat = bpy.data.materials.new(name)
    # `mat_def_path` is stored as a custom property on FLVER_MATERIAL PropertyGroup.
    mat.FLVER_MATERIAL.mat_def_path = mat_def_path
    return mat


def _make_two_flver_objects_same_material(
    obj_a_name="ObjA",
    obj_b_name="ObjB",
    mat_name="SharedMat",
    mat_def="M[DB][M].mtd",
) -> tuple[bpy.types.Object, bpy.types.Object, bpy.types.Material]:
    mat = _make_flver_material(mat_name, mat_def)
    obj_a = T.make_flver_mesh(obj_a_name)
    obj_a.data.materials.append(mat)
    obj_b = T.make_flver_mesh(obj_b_name)
    obj_b.data.materials.append(mat)
    return obj_a, obj_b, mat


# ---------------------------------------------------------------------------
# MergeFLVERMaterials: poll checks
# ---------------------------------------------------------------------------

@T.register_bl_test(MATERIAL_OPS_TESTS)
def test_merge_materials_poll_passes_with_two_flver_objects():
    T.clear_scene()
    obj_a = T.make_flver_mesh("ObjA")
    obj_b = T.make_flver_mesh("ObjB")
    bpy.ops.object.select_all(action="DESELECT")
    obj_a.select_set(True)
    obj_b.select_set(True)
    bpy.context.view_layer.objects.active = obj_a

    can_run = bpy.ops.object.merge_flver_materials.poll()
    T.assert_true(can_run, "test_merge_materials_poll_two_objects")


# ---------------------------------------------------------------------------
# MergeFLVERMaterials: merge behaviour
# ---------------------------------------------------------------------------

def _select_objects(*objects):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]


@T.register_bl_test(MATERIAL_OPS_TESTS)
def test_merge_identical_materials_across_two_objects():
    """Two materials with identical mat_def_path and no other distinguishing properties
    should be merged into a single material shared by both objects."""
    T.clear_scene()

    # Create two distinct material instances that have the same mat_def_path and default
    # properties — they should hash identically.
    mat_a = _make_flver_material("MatA_orig", "M[DB][M].mtd")
    mat_b = _make_flver_material("MatB_orig", "M[DB][M].mtd")

    obj_a = T.make_flver_mesh("ObjA")
    obj_a.data.materials.append(mat_a)
    obj_b = T.make_flver_mesh("ObjB")
    obj_b.data.materials.append(mat_b)

    _select_objects(obj_a, obj_b)

    result = T.call_op(
        "object.merge_flver_materials",
        rename_unique_materials=True,
    )
    T.assert_equal(result, {"FINISHED"}, "test_merge_identical/result")

    # After merge, both objects should reference the same material object.
    T.assert_true(
        obj_a.data.materials[0] is obj_b.data.materials[0],
        "test_merge_identical/same_material_instance",
        "Both objects must share one merged material",
    )


@T.register_bl_test(MATERIAL_OPS_TESTS)
def test_merge_does_not_merge_different_mat_def_paths():
    """Materials with different mat_def_paths must NOT be merged."""
    T.clear_scene()

    mat_a = _make_flver_material("MatDiff_A", "M[DB][M].mtd")
    mat_b = _make_flver_material("MatDiff_B", "M[D][M].mtd")  # different matdef

    obj_a = T.make_flver_mesh("ObjA")
    obj_a.data.materials.append(mat_a)
    obj_b = T.make_flver_mesh("ObjB")
    obj_b.data.materials.append(mat_b)

    _select_objects(obj_a, obj_b)
    T.call_op("object.merge_flver_materials", rename_unique_materials=False)

    T.assert_true(
        obj_a.data.materials[0] is not obj_b.data.materials[0],
        "test_merge_different_matdefs/stays_separate",
        "Different mat_def_paths should not be merged",
    )


@T.register_bl_test(MATERIAL_OPS_TESTS)
def test_merge_already_same_material_instance_is_noop():
    """If both objects already share the exact same material object, no new merged
    material should be created."""
    T.clear_scene()
    mat = _make_flver_material("SharedMat", "M[DB][M].mtd")

    obj_a = T.make_flver_mesh("ObjA")
    obj_a.data.materials.append(mat)
    obj_b = T.make_flver_mesh("ObjB")
    obj_b.data.materials.append(mat)

    mat_count_before = len(bpy.data.materials)
    _select_objects(obj_a, obj_b)
    T.call_op("object.merge_flver_materials", rename_unique_materials=False)
    mat_count_after = len(bpy.data.materials)

    T.assert_equal(
        mat_count_before, mat_count_after,
        "test_merge_same_instance_noop/no_new_material",
        "Sharing the same instance already — no new material should be created",
    )
    T.assert_true(
        obj_a.data.materials[0] is obj_b.data.materials[0],
        "test_merge_same_instance_noop/still_same",
    )


@T.register_bl_test(MATERIAL_OPS_TESTS)
def test_merge_rename_unique_materials():
    """With `rename_unique_materials=True`, a unique material should be renamed."""
    T.clear_scene()
    mat = _make_flver_material("OrigName", "M[DB][M].mtd")

    obj_a = T.make_flver_mesh("ObjA")
    obj_a.data.materials.append(mat)
    obj_b = T.make_flver_mesh("ObjB")
    # obj_b has a *different* mat with a different matdef — so mat stays unique.
    obj_b.data.materials.append(_make_flver_material("OtherMat", "M[D][M].mtd"))

    _select_objects(obj_a, obj_b)
    T.call_op("object.merge_flver_materials", rename_unique_materials=True)

    # The material should have been renamed (no longer "OrigName").
    T.assert_true(
        mat.name != "OrigName",
        "test_merge_rename_unique/renamed",
        f"Material was not renamed from 'OrigName'; got '{mat.name}'",
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

T.run_tests(MATERIAL_OPS_TESTS)
