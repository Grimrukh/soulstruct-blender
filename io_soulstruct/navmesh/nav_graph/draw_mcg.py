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
    mcg_parent_name: bpy.props.StringProperty(name="MCG Parent", default="")
    mcg_graph_draw_enabled: bpy.props.BoolProperty(name="Draw Graph", default=True)
    mcg_graph_color: bpy.props.FloatVectorProperty(
        name="Graph Color", subtype="COLOR", default=(0.5, 1.0, 0.5)
    )
    mcg_node_label_draw_enabled: bpy.props.BoolProperty(name="Draw Labels", default=True)
    mcg_node_label_font_size: bpy.props.IntProperty(name="Label Size", default=24)
    mcg_node_label_font_color: bpy.props.FloatVectorProperty(
        name="Label Color", subtype="COLOR", default=(1.0, 1.0, 1.0)
    )


def draw_mcg_nodes():
    """Draw MCG nodes and labels."""
    if not getattr(bpy.context.scene.mcg_draw_settings, "mcg_graph_draw_enabled", False):
        return

    try:
        mcg_parent_name = bpy.context.scene.mcg_draw_settings.mcg_parent_name
    except AttributeError:
        return

    if mcg_parent_name == "":
        return

    try:
        mcg_parent = bpy.data.objects[mcg_parent_name]
    except KeyError:
        return

    for child in mcg_parent.children:
        if child.name.endswith(" Nodes"):
            node_parent = child
            break
    else:
        return  # No node parent found.

    try:
        color = (*bpy.context.scene.mcg_draw_settings.mcg_graph_color, 1.0)
    except AttributeError:
        color = (0.5, 1.0, 0.5, 1.0)

    nodes = node_parent.children
    points = [node.location for node in nodes]

    shader = gpu.shader.from_builtin("3D_UNIFORM_COLOR")
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
    if not getattr(bpy.context.scene.mcg_draw_settings, "mcg_node_label_draw_enabled", False):
        return

    try:
        mcg_parent_name = bpy.context.scene.mcg_draw_settings.mcg_parent_name
    except AttributeError:
        return

    if mcg_parent_name == "":
        return

    try:
        mcg_parent = bpy.data.objects[mcg_parent_name]
    except KeyError:
        return

    for child in mcg_parent.children:
        if child.name.endswith(" Nodes"):
            node_parent = child
            break
    else:
        return  # No node parent found.

    font_id = 0
    try:
        blf.size(font_id, bpy.context.scene.mcg_draw_settings.mcg_node_label_font_size)
    except AttributeError:
        blf.size(font_id, 24)  # default
    try:
        blf.color(font_id, *bpy.context.scene.mcg_draw_settings.mcg_node_label_font_color, 1.0)
    except AttributeError:
        blf.color(font_id, 1, 1, 1, 1)  # default (white)

    map_stem = mcg_parent_name.split(" ")[0]
    node_prefix = f"{map_stem} Node "
    for node in node_parent.children:
        try:
            node_index = node.name.removeprefix(node_prefix).split(" ")[0]
        except IndexError:
            continue
        label_position = location_3d_to_region_2d(bpy.context.region, bpy.context.region_data, node.location)
        if not label_position:
            continue  # Node is not in view
        blf.position(font_id, label_position.x + 10, label_position.y + 10, 0.0)
        blf.draw(font_id, node_index)


def draw_mcg_edges():
    if not getattr(bpy.context.scene.mcg_draw_settings, "mcg_graph_draw_enabled", False):
        return

    try:
        mcg_parent_name = bpy.context.scene.mcg_draw_settings.mcg_parent_name
    except AttributeError:
        return

    if mcg_parent_name == "":
        return

    try:
        mcg_parent = bpy.data.objects[mcg_parent_name]
    except KeyError:
        return

    node_parent = edge_parent = None
    for child in mcg_parent.children:
        if not node_parent and child.name.endswith(" Nodes"):
            node_parent = child
        elif not edge_parent and child.name.endswith(" Edges"):
            edge_parent = child

    if not node_parent or not edge_parent:
        return  # No node or edge parent found.

    try:
        color = (*bpy.context.scene.mcg_draw_settings.mcg_graph_color, 1.0)
    except AttributeError:
        color = (0.5, 1.0, 0.5, 1.0)

    shader = gpu.shader.from_builtin("3D_UNIFORM_COLOR")
    # gpu.state.blend_set("ALPHA")

    all_edge_vertex_pairs = []
    map_stem = mcg_parent_name.split(" ")[0]

    # Iterate over all Blender objects ONCE to build a dictionary of Nodes that ignores 'dead end' navmesh suffixes.
    node_objects = {}
    node_prefix = f"{map_stem} Node "
    for obj in node_parent.children:
        if obj.name.startswith(node_prefix):
            node_name = obj.name.removeprefix(map_stem).split("<")[0].strip()
            node_objects[node_name] = obj

    # Draw edges
    for edge in edge_parent.children:
        try:
            start_node_name = edge["start_node_name"]
            end_node_name = edge["end_node_name"]
        except KeyError:
            continue  # Edge is not properly configured (can't find node names)

        start_node = node_objects.get(start_node_name)
        end_node = node_objects.get(end_node_name)
        if start_node is None or end_node is None:
            continue  # Edge is not properly configured (can't find nodes)

        all_edge_vertex_pairs.extend([start_node.location, end_node.location])

    batch = batch_for_shader(shader, "LINES", {"pos": all_edge_vertex_pairs})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)

    # gpu.state.blend_set("NONE")
