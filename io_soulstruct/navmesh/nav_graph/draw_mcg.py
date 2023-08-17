from __future__ import annotations

__all__ = [
    "MCGDrawSettings",
    "draw_mcg_nodes",
    "draw_mcg_node_labels",
    "draw_mcg_edges",
]

import bpy
import blf
import gpu
from bpy_extras.view3d_utils import location_3d_to_region_2d
from gpu_extras.batch import batch_for_shader


class MCGDrawSettings(bpy.types.PropertyGroup):
    mcg_node_parent_name: bpy.props.StringProperty(name="Nodes Parent", default="")
    mcg_edge_parent_name: bpy.props.StringProperty(name="Edges Parent", default="")
    mcg_node_draw_enabled: bpy.props.BoolProperty(name="Draw Nodes", default=True)
    mcg_node_label_draw_enabled: bpy.props.BoolProperty(name="Draw Labels", default=True)
    mcg_edge_draw_enabled: bpy.props.BoolProperty(name="Draw Edges", default=True)
    mcg_node_label_font_size: bpy.props.IntProperty(name="Label Size", default=24)
    mcg_node_label_font_color: bpy.props.FloatVectorProperty(
        name="Label Color", subtype="COLOR", default=(1.0, 1.0, 1.0)
    )


def draw_mcg_nodes():
    """Draw MCG nodes and labels."""
    if not getattr(bpy.context.scene.mcg_draw_settings, "mcg_node_draw_enabled", False):
        return

    try:
        node_parent_name = bpy.context.scene.mcg_draw_settings.mcg_node_parent_name
    except AttributeError:
        return

    if node_parent_name == "":
        return

    try:
        node_parent = bpy.data.objects[node_parent_name]
    except KeyError:
        return

    nodes = node_parent.children
    points = [node.location for node in nodes]

    shader = gpu.shader.from_builtin("3D_UNIFORM_COLOR")
    gpu.state.blend_set("ALPHA")
    gpu.state.depth_test_set("LESS_EQUAL")
    gpu.state.point_size_set(10)
    batch_sphere = batch_for_shader(shader, 'POINTS', {"pos": points})
    shader.bind()
    shader.uniform_float("color", (0, 1, 0, 1))  # green
    batch_sphere.draw(shader)

    gpu.state.blend_set("NONE")
    gpu.state.depth_test_set("NONE")


def draw_mcg_node_labels():
    """Draw MCG node labels."""
    if not getattr(bpy.context.scene.mcg_draw_settings, "mcg_node_label_draw_enabled", False):
        return

    try:
        node_parent_name = bpy.context.scene.mcg_draw_settings.mcg_node_parent_name
    except AttributeError:
        return

    if node_parent_name == "":
        return

    try:
        node_parent = bpy.data.objects[node_parent_name]
    except KeyError:
        return

    font_id = 0
    try:
        blf.size(font_id, bpy.context.scene.mcg_draw_settings.mcg_node_label_font_size)
    except AttributeError:
        blf.size(font_id, 24)  # default
    try:
        blf.color(font_id, *bpy.context.scene.mcg_draw_settings.mcg_node_label_font_color, 1.0)
    except AttributeError:
        blf.color(font_id, 1, 1, 1, 1)  # default (white)

    nodes = node_parent.children
    for node in nodes:
        try:
            node_index = node.name.split(" ")[1]
        except IndexError:
            continue
        label_position = location_3d_to_region_2d(bpy.context.region, bpy.context.region_data, node.location)
        if not label_position:
            continue  # Node is not in view
        blf.position(font_id, label_position.x + 10, label_position.y + 10, 0.0)
        blf.draw(font_id, node_index)


def draw_mcg_edges():
    if not getattr(bpy.context.scene.mcg_draw_settings, "mcg_edge_draw_enabled", False):
        return

    try:
        edge_parent_name = bpy.context.scene.mcg_draw_settings.mcg_edge_parent_name
    except AttributeError:
        return

    if edge_parent_name == "":
        return

    try:
        edge_parent = bpy.data.objects[edge_parent_name]
    except KeyError:
        return

    shader = gpu.shader.from_builtin("3D_UNIFORM_COLOR")
    # gpu.state.blend_set("ALPHA")

    all_edge_vertex_pairs = []

    # Draw edges
    for edge in edge_parent.children:
        try:
            start_node_name = edge["start_node_name"]
            end_node_name = edge["end_node_name"]
        except KeyError:
            continue  # Edge is not properly configured (can't find node names)

        start_node = end_node = None
        for obj in bpy.data.objects:
            if obj.name == start_node_name or obj.name.startswith(start_node_name + " "):
                start_node = obj
            elif obj.name == end_node_name or obj.name.startswith(end_node_name + " "):
                end_node = obj
        if start_node is None or end_node is None:
            continue  # Edge is not properly configured (can't find nodes)

        start_pos = start_node.location
        end_pos = end_node.location
        all_edge_vertex_pairs.extend([start_pos, end_pos])

    batch = batch_for_shader(shader, "LINES", {"pos": all_edge_vertex_pairs})
    shader.bind()
    shader.uniform_float("color", (0.5, 1, 0.5, 1))  # green color
    batch.draw(shader)

    # gpu.state.blend_set("NONE")
