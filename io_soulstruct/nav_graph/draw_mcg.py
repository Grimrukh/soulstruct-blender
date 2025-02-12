from __future__ import annotations

__all__ = [
    "MCGDrawSettings",
    "update_mcg_draw_caches",
    "draw_mcg_nodes",
    "draw_mcg_edges",
    "draw_mcg_edge_cost_labels",
]

import typing as tp

import bpy
import blf
import gpu
from bpy_extras.view3d_utils import location_3d_to_region_2d
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from io_soulstruct.exceptions import SoulstructTypeError

from .types import *

if tp.TYPE_CHECKING:
    from gpu.types import GPUShader, GPUBatch


# Shader and cached batches for nodes/edges/triangles.
_CACHED_SHADER = None  # type: GPUShader | None
_CACHED_NODES_BATCH = None  # type: GPUBatch | None
_CACHED_EDGES_BATCH = None  # type: GPUBatch | None
_CACHED_TRIANGLES_A_BATCH = None  # type: GPUBatch | None
_CACHED_TRIANGLES_B_BATCH = None  # type: GPUBatch | None
# Store last computed geometry to know when to update.
_LAST_DRAWN_NODES = None  # type: list[Vector] | None
_LAST_DRAWN_EDGES = None  # type: list[Vector] | None  # flattened list of edge endpoint pairs
_LAST_DRAWN_TRIANGLES_A = None  # type: list[Vector] | None  # flattened list of triangle vertices
_LAST_DRAWN_TRIANGLES_B = None  # type: list[Vector] | None  # flattened list of triangle vertices


class MCGDrawSettings(bpy.types.PropertyGroup):
    mcg_parent: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="MCG Parent",
        description="Parent object of MCG nodes and edges.",
    )
    draw_graph: bpy.props.BoolProperty(name="Draw Graph", default=True)
    draw_selected_only: bpy.props.BoolProperty(name="Selected Only", default=True)
    color: bpy.props.FloatVectorProperty(
        name="Graph Color", subtype="COLOR", default=(0.5, 1.0, 0.5)
    )
    draw_edge_costs: bpy.props.BoolProperty(name="Draw Edge Costs", default=True)
    edge_label_font_size: bpy.props.IntProperty(name="Edge Label Size", default=18)
    edge_label_font_color: bpy.props.FloatVectorProperty(
        name="Edge Label Color (Match)", subtype="COLOR", default=(0.8, 1.0, 0.8)
    )
    close_cost_edge_label_font_color: bpy.props.FloatVectorProperty(
        name="Edge Label Color (Close)", subtype="COLOR", default=(1.0, 1.0, 0.7)
    )
    different_cost_edge_label_font_color: bpy.props.FloatVectorProperty(
        name="Edge Label Color (Different)", subtype="COLOR", default=(1.0, 0.8, 0.8)
    )
    highlight_edge_navmesh_triangles: bpy.props.BoolProperty(name="Highlight Edge Triangles", default=True)
    highlight_selected_only: bpy.props.BoolProperty(name="Selected Triangles Only", default=True)

    @property
    def mcg(self) -> BlenderMCG | None:
        try:
            return BlenderMCG(self.mcg_parent) if self.mcg_parent else None
        except SoulstructTypeError:
            return None


def update_mcg_draw_caches():
    """Process selected MCG nodes/edges and update cached batches if necessary."""
    global _CACHED_SHADER, _CACHED_NODES_BATCH, _CACHED_EDGES_BATCH
    global _CACHED_TRIANGLES_A_BATCH, _CACHED_TRIANGLES_B_BATCH
    global _LAST_DRAWN_NODES, _LAST_DRAWN_EDGES
    global _LAST_DRAWN_TRIANGLES_A, _LAST_DRAWN_TRIANGLES_B

    draw_settings = bpy.context.scene.mcg_draw_settings
    if not draw_settings.draw_graph:
        # Don't erase caches.
        return

    bl_mcg = draw_settings.mcg
    if not bl_mcg:
        # Erase cached batches.
        _CACHED_NODES_BATCH = None
        _CACHED_EDGES_BATCH = None
        _CACHED_TRIANGLES_A_BATCH = None
        _CACHED_TRIANGLES_B_BATCH = None
        _LAST_DRAWN_NODES = None
        _LAST_DRAWN_EDGES = None
        _LAST_DRAWN_TRIANGLES_A = None
        _LAST_DRAWN_TRIANGLES_B = None
        return

    # Get nodes and (if needed) filter by selection.
    bl_nodes = bl_mcg.get_nodes()
    if draw_settings.draw_selected_only:
        bl_nodes = [node for node in bl_nodes if node.obj.select_get()]

    # Build the points list.
    points = [node.location.copy() for node in bl_nodes]

    # Only update nodes batch if the points have changed.
    if points != _LAST_DRAWN_NODES:
        # Cache (or create) the shader
        if _CACHED_SHADER is None:
            _CACHED_SHADER = gpu.shader.from_builtin("UNIFORM_COLOR")
        _CACHED_NODES_BATCH = batch_for_shader(_CACHED_SHADER, 'POINTS', {"pos": points})
        _LAST_DRAWN_NODES = points

    # Process edges/triangles similarly.
    all_edge_location_pairs = []
    node_a_triangles_coords = []
    node_b_triangles_coords = []
    edges_and_nodes = []  # for moving edges to midpoint if cache refreshed
    for bl_edge in bl_mcg.get_edges():
        try:
            bl_node_a = BlenderMCGNode(bl_edge.node_a)
            bl_node_b = BlenderMCGNode(bl_edge.node_b)
        except SoulstructTypeError:
            continue

        # If filtering by selection:
        if draw_settings.draw_selected_only:
            if not (bl_edge.obj.select_get() or bl_node_a.obj.select_get() or bl_node_b.obj.select_get()):
                continue

        all_edge_location_pairs.extend([bl_node_a.location.copy(), bl_node_b.location.copy()])
        edges_and_nodes.append((bl_edge, bl_node_a, bl_node_b))

        if draw_settings.highlight_edge_navmesh_triangles:
            if draw_settings.highlight_selected_only and not bl_edge.obj.select_get():
                continue
            # Draw triangles over faces linked to start and end nodes.
            navmesh = bl_edge.navmesh_part
            if navmesh is not None:
                if bl_node_a.navmesh_a == navmesh:
                    node_a_triangles = bl_node_a.navmesh_a_triangles
                elif bl_node_a.navmesh_b == navmesh:
                    node_a_triangles = bl_node_a.navmesh_b_triangles
                else:
                    node_a_triangles = []  # can't find
                for i in node_a_triangles:
                    if i >= len(navmesh.data.polygons):
                        continue  # invalid face index
                    face = navmesh.data.polygons[i]
                    for vert_index in face.vertices:
                        vert = navmesh.data.vertices[vert_index]
                        world_coord = navmesh.matrix_world @ vert.co
                        node_a_triangles_coords.append(world_coord)

                if bl_node_b.navmesh_a == navmesh:
                    node_b_triangles = bl_node_b.navmesh_a_triangles
                elif bl_node_b.navmesh_b == navmesh:
                    node_b_triangles = bl_node_b.navmesh_b_triangles
                else:
                    node_b_triangles = []  # can't find
                for i in node_b_triangles:
                    if i >= len(navmesh.data.polygons):
                        continue  # invalid face index
                    face = navmesh.data.polygons[i]
                    for vert_index in face.vertices:
                        vert = navmesh.data.vertices[vert_index]
                        world_coord = navmesh.matrix_world @ vert.co
                        node_b_triangles_coords.append(world_coord)

    if all_edge_location_pairs != _LAST_DRAWN_EDGES:
        if _CACHED_SHADER is None:
            _CACHED_SHADER = gpu.shader.from_builtin("UNIFORM_COLOR")
        _CACHED_EDGES_BATCH = batch_for_shader(_CACHED_SHADER, "LINES", {"pos": all_edge_location_pairs})
        _LAST_DRAWN_EDGES = all_edge_location_pairs

        # Reposition edge objects between their nodes for convenience.
        for bl_edge, bl_node_a, bl_node_b in edges_and_nodes:
            direction = bl_node_b.location - bl_node_a.location
            midpoint = (bl_node_a.location + bl_node_b.location) / 2.0
            bl_edge.location = midpoint
            # Point empty arrow in direction of edge.
            bl_edge.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()

    if draw_settings.highlight_edge_navmesh_triangles:
        if node_a_triangles_coords != _LAST_DRAWN_TRIANGLES_A:
            if _CACHED_SHADER is None:
                _CACHED_SHADER = gpu.shader.from_builtin("UNIFORM_COLOR")
            _CACHED_TRIANGLES_A_BATCH = batch_for_shader(_CACHED_SHADER, "TRIS", {"pos": node_a_triangles_coords})
            _LAST_DRAWN_TRIANGLES_A = node_a_triangles_coords
        if node_b_triangles_coords != _LAST_DRAWN_TRIANGLES_B:
            if _CACHED_SHADER is None:
                _CACHED_SHADER = gpu.shader.from_builtin("UNIFORM_COLOR")
            _CACHED_TRIANGLES_B_BATCH = batch_for_shader(_CACHED_SHADER, "TRIS", {"pos": node_b_triangles_coords})
            _LAST_DRAWN_TRIANGLES_B = node_b_triangles_coords


def draw_mcg_nodes():
    global _CACHED_SHADER, _CACHED_NODES_BATCH
    draw_settings = bpy.context.scene.mcg_draw_settings
    if not draw_settings.draw_graph:
        return

    if _CACHED_SHADER is None or _CACHED_NODES_BATCH is None:
        return

    # Set GPU states once and draw.
    gpu.state.blend_set("ALPHA")
    gpu.state.depth_test_set("LESS_EQUAL")
    gpu.state.point_size_set(10)

    _CACHED_SHADER.bind()
    try:
        color = (*draw_settings.color, 1.0)
    except AttributeError:
        color = (0.5, 1.0, 0.5, 1.0)
    _CACHED_SHADER.uniform_float("color", color)
    _CACHED_NODES_BATCH.draw(_CACHED_SHADER)

    gpu.state.blend_set("NONE")
    gpu.state.depth_test_set("NONE")


def draw_mcg_edges():
    global _CACHED_SHADER, _CACHED_EDGES_BATCH, _CACHED_TRIANGLES_A_BATCH, _CACHED_TRIANGLES_B_BATCH
    draw_settings = bpy.context.scene.mcg_draw_settings
    # For edges, you might not need to draw if the graph isn’t active.
    if not draw_settings.draw_graph:
        return

    if _CACHED_SHADER is None or _CACHED_EDGES_BATCH is None:
        return

    _CACHED_SHADER.bind()
    try:
        color = (*draw_settings.color, 1.0)
    except AttributeError:
        color = (0.5, 1.0, 0.5, 1.0)
    _CACHED_SHADER.uniform_float("color", color)
    _CACHED_EDGES_BATCH.draw(_CACHED_SHADER)

    if draw_settings.highlight_edge_navmesh_triangles:
        if _CACHED_TRIANGLES_A_BATCH is not None:
            _CACHED_SHADER.uniform_float("color", (1.0, 0.3, 0.3, 0.2))  # red
            _CACHED_TRIANGLES_A_BATCH.draw(_CACHED_SHADER)
        if _CACHED_TRIANGLES_B_BATCH is not None:
            _CACHED_SHADER.uniform_float("color", (0.3, 0.3, 1.0, 0.2))  # blue
            _CACHED_TRIANGLES_B_BATCH.draw(_CACHED_SHADER)

    gpu.state.blend_set("NONE")
    gpu.state.depth_test_set("NONE")


def draw_mcg_edge_cost_labels():
    """Draw MCG edge cost labels using `blf` (text-blitting) module."""
    draw_settings = bpy.context.scene.mcg_draw_settings
    if not draw_settings.draw_edge_costs:
        return

    bl_mcg = draw_settings.mcg
    if not bl_mcg:
        return

    font_id = 0
    try:
        blf.size(font_id, draw_settings.edge_label_font_size)
    except AttributeError:
        blf.size(font_id, 18)  # default
    try:
        blf.color(font_id, *draw_settings.edge_label_font_color, 1.0)
    except AttributeError:
        blf.color(font_id, 0.8, 1.0, 0.8, 1)  # default (green)

    almost_match_font_id = 1
    try:
        blf.size(almost_match_font_id, draw_settings.edge_label_font_size)
    except AttributeError:
        blf.size(almost_match_font_id, 18)  # default
    try:
        blf.color(
            almost_match_font_id, *draw_settings.close_cost_edge_label_font_color, 1.0
        )
    except AttributeError:
        blf.color(almost_match_font_id, 1.0, 1.0, 0.7, 1)  # default (yellow)

    bad_match_font_id = 2
    try:
        blf.size(bad_match_font_id, draw_settings.edge_label_font_size)
    except AttributeError:
        blf.size(bad_match_font_id, 18)  # default
    try:
        blf.color(bad_match_font_id, *draw_settings.different_cost_edge_label_font_color, 1.0)
    except AttributeError:
        blf.color(bad_match_font_id, 1.0, 0.8, 0.8, 1)  # default (red)

    for bl_edge in bl_mcg.get_edges():
        cost = bl_edge.cost

        label_position = location_3d_to_region_2d(bpy.context.region, bpy.context.region_data, bl_edge.location)
        if not label_position:
            continue  # edge is not in view

        try:
            new_cost = bl_edge["New Cost"]
        except KeyError:
            blf.position(font_id, label_position.x + 10, label_position.y + 10, 0.0)
            blf.draw(font_id, f"{cost:.3f}")
        else:
            if abs(cost - new_cost) > 1:
                font = bad_match_font_id
                label = f"{cost:.3f} ({new_cost:.3f})"
            elif abs(cost - new_cost) > 0.0001:
                font = almost_match_font_id
                label = f"{cost:.3f} ({new_cost:.3f})"
            else:
                # Good match.
                font = font_id
                label = f"{cost:.3f} (✓)"
            blf.position(font, label_position.x + 10, label_position.y + 10, 0.0)
            blf.draw(font, label)
