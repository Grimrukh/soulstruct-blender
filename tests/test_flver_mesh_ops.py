"""Tests for FLVER mesh operators (no game files required).

Covers:
  - SelectUnweightedVertices   (mesh.select_unweighted_vertices)

Note: operators that require EDIT_MESH mode (SelectDisplayMaskID, SetSmoothCustomNormals,
SetVertexAlpha, InvertVertexAlpha, ReboneVertices, FastUVUnwrap, RotateUVMap*) are not
exercised from headless mode because `bmesh.from_edit_mesh()` requires an interactive
viewport context. SelectUnweightedVertices works because it reads vertex groups in Object
mode before switching to Edit mode.

Run with:
    blender --background --python tests/test_flver_mesh_ops.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import bpy
import bl_test_utils as T

T.enable_addon()
T.set_game("DARK_SOULS_DSR")

MESH_TESTS = []


# ---------------------------------------------------------------------------
# SelectUnweightedVertices
# ---------------------------------------------------------------------------

def _make_simple_mesh_with_geometry(name: str, vertex_count: int = 4) -> bpy.types.Object:
    """Create a plain Mesh object (not FLVER-typed) with some vertices."""
    mesh = bpy.data.meshes.new(name)
    # Build a minimal mesh: just vertices, no faces.
    mesh.vertices.add(vertex_count)
    for i in range(vertex_count):
        mesh.vertices[i].co = (float(i), 0.0, 0.0)
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


@T.register_bl_test(MESH_TESTS)
def test_select_unweighted_selects_all_when_no_groups():
    """With no vertex groups on any vertex, all vertices should be selected."""
    T.clear_scene()
    obj = _make_simple_mesh_with_geometry("NoGroups", vertex_count=4)
    T.activate(obj)

    result = T.call_op("mesh.select_unweighted_vertices")
    T.assert_equal(result, {"FINISHED"}, "test_select_unweighted_no_groups/result")

    # Must switch back to Object mode to read vertex selection state.
    bpy.ops.object.mode_set(mode="OBJECT")
    all_selected = all(v.select for v in obj.data.vertices)
    T.assert_true(all_selected, "test_select_unweighted_no_groups/all_selected")


@T.register_bl_test(MESH_TESTS)
def test_select_unweighted_does_not_select_weighted_vertices():
    """Vertices that belong to a vertex group should NOT be selected."""
    T.clear_scene()
    obj = _make_simple_mesh_with_geometry("WithGroups", vertex_count=4)
    T.activate(obj)

    # Weight vertices 0 and 1 to a group.
    vg = obj.vertex_groups.new(name="BoneA")
    vg.add([0, 1], 1.0, "REPLACE")

    result = T.call_op("mesh.select_unweighted_vertices")
    T.assert_equal(result, {"FINISHED"}, "test_select_unweighted_weighted/result")

    bpy.ops.object.mode_set(mode="OBJECT")
    T.assert_true(
        not obj.data.vertices[0].select,
        "test_select_unweighted_weighted/v0_not_selected",
        "vertex 0 is weighted, should not be selected",
    )
    T.assert_true(
        not obj.data.vertices[1].select,
        "test_select_unweighted_weighted/v1_not_selected",
        "vertex 1 is weighted, should not be selected",
    )
    T.assert_true(
        obj.data.vertices[2].select,
        "test_select_unweighted_weighted/v2_selected",
        "vertex 2 is unweighted, should be selected",
    )
    T.assert_true(
        obj.data.vertices[3].select,
        "test_select_unweighted_weighted/v3_selected",
        "vertex 3 is unweighted, should be selected",
    )


@T.register_bl_test(MESH_TESTS)
def test_select_unweighted_selects_none_when_all_weighted():
    """If every vertex is weighted, none should be selected."""
    T.clear_scene()
    obj = _make_simple_mesh_with_geometry("AllWeighted", vertex_count=3)
    T.activate(obj)

    vg = obj.vertex_groups.new(name="BoneA")
    vg.add([0, 1, 2], 1.0, "REPLACE")

    T.call_op("mesh.select_unweighted_vertices")

    bpy.ops.object.mode_set(mode="OBJECT")
    none_selected = not any(v.select for v in obj.data.vertices)
    T.assert_true(none_selected, "test_select_unweighted_all_weighted/none_selected")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

T.run_tests(MESH_TESTS)
