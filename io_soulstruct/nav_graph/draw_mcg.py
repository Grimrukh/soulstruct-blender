from __future__ import annotations

__all__ = [
    "MCGDrawSettings",
    "draw_mcg_nodes",
    "draw_mcg_node_labels",
    "draw_mcg_edges",
    "draw_mcg_edge_cost_labels",
]

import re

import bpy
import blf
import gpu
from bpy_extras.view3d_utils import location_3d_to_region_2d
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from io_soulstruct.exceptions import SoulstructTypeError

from .types import *


if bpy.app.version[0] == 4:
    UNIFORM_COLOR_SHADER = "UNIFORM_COLOR"
else:
    UNIFORM_COLOR_SHADER = "3D_UNIFORM_COLOR"


class MCGDrawSettings(bpy.types.PropertyGroup):
    mcg_parent: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="MCG Parent",
        description="Parent object of MCG nodes and edges.",
    )
    draw_graph: bpy.props.BoolProperty(name="Draw Graph", default=True)
    draw_selected_only: bpy.props.BoolProperty(name="Selected Only", default=False)
    color: bpy.props.FloatVectorProperty(
        name="Graph Color", subtype="COLOR", default=(0.5, 1.0, 0.5)
    )
    draw_node_labels: bpy.props.BoolProperty(name="Draw Node Names", default=True)
    draw_edge_costs: bpy.props.BoolProperty(name="Draw Edge Costs", default=True)
    node_label_font_size: bpy.props.IntProperty(name="Node Label Size", default=24)
    node_label_font_color: bpy.props.FloatVectorProperty(
        name="Node Label Color", subtype="COLOR", default=(1.0, 1.0, 1.0)
    )
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

    @property
    def mcg(self) -> BlenderMCG | None:
        try:
            return BlenderMCG(self.mcg_parent) if self.mcg_parent else None
        except SoulstructTypeError:
            return None


NODE_INDEX_RE = re.compile(r"Node (\d+)")


def draw_mcg_nodes():
    """Draw MCG nodes points."""
    draw_settings = bpy.context.scene.mcg_draw_settings
    if not draw_settings.draw_graph:
        return

    bl_mcg = draw_settings.mcg
    if not bl_mcg:
        return
    bl_nodes = bl_mcg.get_nodes()

    try:
        color = (*draw_settings.color, 1.0)
    except AttributeError:
        color = (0.5, 1.0, 0.5, 1.0)

    if draw_settings.draw_selected_only:
        # Filter nodes by selected status.
        bl_nodes = [bl_node for bl_node in bl_nodes if bl_node.obj.select_get()]

    points = [node.location for node in bl_nodes]

    shader = gpu.shader.from_builtin(UNIFORM_COLOR_SHADER)

    gpu.state.blend_set("ALPHA")
    gpu.state.depth_test_set("LESS_EQUAL")
    gpu.state.point_size_set(10)
    batch_sphere = batch_for_shader(shader, 'POINTS', {"pos": points})
    shader.bind()
    shader.uniform_float("color", color)  # green
    batch_sphere.draw(shader)

    gpu.state.blend_set("NONE")
    gpu.state.depth_test_set("NONE")


def draw_mcg_node_labels():
    """Draw MCG node labels."""
    draw_settings = bpy.context.scene.mcg_draw_settings
    if not draw_settings.draw_node_labels:
        return
    bl_mcg = draw_settings.mcg
    if not bl_mcg:
        return

    bl_nodes = bl_mcg.get_nodes()

    if draw_settings.draw_selected_only:
        # Only label selected nodes or nodes connected by a selected edge.
        selected_edge_node_names = set()
        selected_edges = [bl_edge for bl_edge in bl_mcg.get_edges() if bl_edge.obj.select_get()]
        for bl_edge in selected_edges:
            selected_edge_node_names.add(bl_edge.node_a.name)
            selected_edge_node_names.add(bl_edge.node_b.name)

        bl_nodes = [
            bl_node for bl_node in bl_nodes
            if bl_node.obj.select_get() or bl_node.name in selected_edge_node_names
        ]

    font_id = 0
    try:
        blf.size(font_id, bpy.context.scene.mcg_draw_settings.node_label_font_size)
    except AttributeError:
        blf.size(font_id, 24)  # default
    try:
        blf.color(font_id, *bpy.context.scene.mcg_draw_settings.node_label_font_color, 1.0)
    except AttributeError:
        blf.color(font_id, 1, 1, 1, 1)  # default (white)

    for bl_node in bl_nodes:
        if match := NODE_INDEX_RE.search(bl_node.name):
            label = match.group(1)  # str
        else:
            continue  # invalid node name
        label_position = location_3d_to_region_2d(bpy.context.region, bpy.context.region_data, bl_node.location)
        if not label_position:
            continue  # node is not in view
        blf.position(font_id, label_position.x + 10, label_position.y + 10, 0.0)
        blf.draw(font_id, label)


def draw_mcg_edges():
    draw_settings = bpy.context.scene.mcg_draw_settings
    if not draw_settings.draw_graph and not draw_settings.highlight_edge_navmesh_triangles:
        return
    bl_mcg = draw_settings.mcg
    if not bl_mcg:
        return

    try:
        color = (*draw_settings.color, 1.0)
    except AttributeError:
        color = (0.5, 1.0, 0.5, 1.0)

    shader = gpu.shader.from_builtin(UNIFORM_COLOR_SHADER)
    # gpu.state.blend_set("ALPHA")

    all_edge_location_pairs = []  # type: list[Vector]

    node_a_triangles_coords = []
    node_b_triangles_coords = []

    selected_node_a_loc = selected_node_b_loc = None

    for bl_edge in bl_mcg.get_edges():
        try:
            bl_node_a = BlenderMCGNode(bl_edge.node_a)
            bl_node_b = BlenderMCGNode(bl_edge.node_b)
        except SoulstructTypeError:
            # Cannot draw edge.
            continue

        if (
            draw_settings.draw_selected_only
            and not bl_edge.obj.select_get()
            and not (bl_node_a.obj.select_get() or bl_node_b.obj.select_get())
        ):
            # At least one of the edge's nodes must be selected to draw it, if this setting is enabled.
            continue

        all_edge_location_pairs.extend([bl_node_a.location, bl_node_b.location])

        # Also move edge object itself for convenience.
        direction = bl_node_b.location - bl_node_a.location
        midpoint = (bl_node_a.location + bl_node_b.location) / 2.0
        bl_edge.location = midpoint
        # Point empty arrow in direction of edge.
        bl_edge.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()

        if draw_settings.highlight_edge_navmesh_triangles and bpy.context.active_object == bl_edge.obj:
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
                selected_node_a_loc = bl_node_a.location
                selected_node_b_loc = bl_node_b.location

    if draw_settings.draw_graph and all_edge_location_pairs:
        batch = batch_for_shader(shader, "LINES", {"pos": all_edge_location_pairs})
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)

    if draw_settings.highlight_edge_navmesh_triangles:
        if node_a_triangles_coords:
            batch = batch_for_shader(shader, "TRIS", {"pos": node_a_triangles_coords})
            shader.bind()
            shader.uniform_float("color", (1.0, 0.3, 0.3, 0.2))  # red
            batch.draw(shader)
        if node_b_triangles_coords:
            batch = batch_for_shader(shader, "TRIS", {"pos": node_b_triangles_coords})
            shader.bind()
            shader.uniform_float("color", (0.3, 0.3, 1.0, 0.2))  # blue
            batch.draw(shader)

    # Highlight nodes of selected edge.
    if selected_node_a_loc:
        gpu.state.depth_test_set("LESS_EQUAL")
        gpu.state.point_size_set(30)
        batch_sphere = batch_for_shader(shader, 'POINTS', {"pos": [selected_node_a_loc]})
        shader.bind()
        shader.uniform_float("color", (1.0, 0.1, 0.1, 0.5))  # red
        batch_sphere.draw(shader)
    if selected_node_b_loc:
        gpu.state.depth_test_set("LESS_EQUAL")
        gpu.state.point_size_set(30)
        batch_sphere = batch_for_shader(shader, 'POINTS', {"pos": [selected_node_b_loc]})
        shader.bind()
        shader.uniform_float("color", (0.1, 0.1, 1.0, 0.5))  # blue
        batch_sphere.draw(shader)

    # gpu.state.blend_set("NONE")


def draw_mcg_edge_cost_labels():
    """Draw MCG edge cost labels."""
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
