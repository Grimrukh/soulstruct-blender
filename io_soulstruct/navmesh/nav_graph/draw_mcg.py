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


if bpy.app.version[0] == 4:
    UNIFORM_COLOR_SHADER = "UNIFORM_COLOR"
else:
    UNIFORM_COLOR_SHADER = "3D_UNIFORM_COLOR"


class MCGDrawSettings(bpy.types.PropertyGroup):
    mcg_parent_name: bpy.props.StringProperty(name="MCG Parent", default="")
    mcg_graph_draw_enabled: bpy.props.BoolProperty(name="Draw Graph", default=True)
    mcg_graph_draw_selected_nodes_only: bpy.props.BoolProperty(name="Selected Only", default=False)
    mcg_graph_color: bpy.props.FloatVectorProperty(
        name="Graph Color", subtype="COLOR", default=(0.5, 1.0, 0.5)
    )
    mcg_node_label_draw_enabled: bpy.props.BoolProperty(name="Draw Labels", default=True)
    mcg_node_label_font_size: bpy.props.IntProperty(name="Label Size", default=24)
    mcg_node_label_font_color: bpy.props.FloatVectorProperty(
        name="Label Color", subtype="COLOR", default=(1.0, 1.0, 1.0)
    )
    mcg_edge_triangles_highlight_enabled: bpy.props.BoolProperty(name="Highlight Edge Triangles", default=True)


def draw_mcg_nodes():
    """Draw MCG nodes points."""
    settings = bpy.context.scene.mcg_draw_settings  # type: MCGDrawSettings
    if not settings.mcg_graph_draw_enabled:
        return

    mcg_parent_name = settings.mcg_parent_name
    if not mcg_parent_name:
        return

    try:
        mcg_parent = bpy.data.objects[mcg_parent_name]
    except KeyError:
        return  # invalid MCG parent name

    for child in mcg_parent.children:
        if child.name.endswith(" Nodes"):
            node_parent = child
            break
    else:
        return  # No node parent found.

    try:
        color = (*settings.mcg_graph_color, 1.0)
    except AttributeError:
        color = (0.5, 1.0, 0.5, 1.0)

    nodes = node_parent.children

    if settings.mcg_graph_draw_selected_nodes_only:
        # Filter nodes by selected status.
        nodes = [node for node in nodes if node.select_get()]

    points = [node.location for node in nodes]

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
    settings = bpy.context.scene.mcg_draw_settings  # type: MCGDrawSettings
    if not settings.mcg_node_label_draw_enabled:
        return

    mcg_parent_name = settings.mcg_parent_name
    if not mcg_parent_name:
        return

    try:
        mcg_parent = bpy.data.objects[mcg_parent_name]
    except KeyError:
        return  # invalid MCG parent name

    node_parent = edge_parent = None
    for child in mcg_parent.children:
        if child.name.endswith(" Nodes"):
            node_parent = child
            if edge_parent:
                break
        if child.name.endswith(" Edges"):  # needed to get nodes connected to selected
            edge_parent = child
            if node_parent:
                break
    else:
        return  # No node parent found.

    if settings.mcg_graph_draw_selected_nodes_only:
        # Use edges to detect connected nodes.
        node_name_map = {}
        node_prefix = node_parent.name[:-1]  # just drop 's'
        for node in node_parent.children:
            if node.name.startswith(node_prefix):
                node_name = "Node " + node.name.removeprefix(node_prefix).split("<")[0].strip()
                node_name_map[node_name] = node.name

        selected_node_names = {node.name for node in node_parent.children if node.select_get()}
        all_node_names = selected_node_names.copy()
        for edge in edge_parent.children:
            node_a_name = node_name_map.get(edge["Node A"])
            node_b_name = node_name_map.get(edge["Node B"])
            if edge.select_get():
                all_node_names.add(node_a_name)
                all_node_names.add(node_b_name)
            if node_a_name in selected_node_names:
                all_node_names.add(node_b_name)
            elif node_b_name in selected_node_names:
                all_node_names.add(node_a_name)

        nodes_to_label = [bpy.data.objects[node_name] for node_name in all_node_names]
    else:
        nodes_to_label = node_parent.children  # label all nodes

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
    for node in nodes_to_label:
        try:
            node_index = node.name.removeprefix(node_prefix).split(" ")[0]
        except IndexError:
            continue  # invalid node name
        label_position = location_3d_to_region_2d(bpy.context.region, bpy.context.region_data, node.location)
        if not label_position:
            continue  # node is not in view
        blf.position(font_id, label_position.x + 10, label_position.y + 10, 0.0)
        blf.draw(font_id, node_index)


def draw_mcg_edges():
    settings = bpy.context.scene.mcg_draw_settings  # type: MCGDrawSettings
    if not settings.mcg_graph_draw_enabled and not settings.mcg_edge_triangles_highlight_enabled:
        return

    mcg_parent_name = settings.mcg_parent_name
    if not mcg_parent_name:
        return

    try:
        mcg_parent = bpy.data.objects[mcg_parent_name]
    except KeyError:
        return  # invalid MCG parent name

    node_parent = edge_parent = None
    for child in mcg_parent.children:
        if not node_parent and child.name.endswith(" Nodes"):
            node_parent = child
        elif not edge_parent and child.name.endswith(" Edges"):
            edge_parent = child

    if not node_parent or not edge_parent:
        return  # No node or edge parent found.

    try:
        color = (*settings.mcg_graph_color, 1.0)
    except AttributeError:
        color = (0.5, 1.0, 0.5, 1.0)

    shader = gpu.shader.from_builtin(UNIFORM_COLOR_SHADER)
    # gpu.state.blend_set("ALPHA")

    all_edge_vertex_pairs = []
    map_stem = mcg_parent_name.split(" ")[0]

    # Iterate over all Blender objects ONCE to build a dictionary of Nodes that ignores 'dead end' navmesh suffixes.
    node_objects = {}
    node_prefix = f"{map_stem} Node "
    for node in node_parent.children:
        if node.name.startswith(node_prefix):
            node_name = node.name.removeprefix(map_stem).split("<")[0].strip()
            node_objects[node_name] = node

    node_a_triangles_coords = []
    node_b_triangles_coords = []
    selected_node_a = selected_node_b = None
    for edge in edge_parent.children:
        try:
            node_a_name = edge["Node A"]
            node_b_name = edge["Node B"]
        except KeyError:
            continue  # Edge is not properly configured (can't find node names)

        node_a = node_objects.get(node_a_name)
        node_b = node_objects.get(node_b_name)
        if node_a is None or node_b is None:
            continue  # edge is not properly configured (can't find nodes)

        if (
            settings.mcg_graph_draw_selected_nodes_only
            and not edge.select_get()
            and not (node_a.select_get() or node_b.select_get())
        ):
            # At least one of the edge's nodes must be selected to draw it, if this setting is enabled.
            continue

        all_edge_vertex_pairs.extend([node_a.location, node_b.location])

        # Also move edge object itself for convenience.
        direction = node_b.location - node_a.location
        midpoint = (node_a.location + node_b.location) / 2.0
        edge.location = midpoint
        # Point empty arrow in direction of edge.
        edge.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()

        if settings.mcg_edge_triangles_highlight_enabled and bpy.context.active_object == edge:
            # Draw triangles over faces linked to start and end nodes.
            try:
                navmesh = bpy.data.objects[edge["Navmesh Name"]]
            except KeyError:
                pass  # can't draw
            else:
                if node_a["Navmesh A Name"] == navmesh.name:
                    node_a_triangles = node_a["Navmesh A Triangles"]
                elif node_a["Navmesh B Name"] == navmesh.name:
                    node_a_triangles = node_a["Navmesh B Triangles"]
                else:
                    node_a_triangles = []  # can't find
                for i in node_a_triangles:
                    if i >= len(navmesh.data.polygons):
                        continue  # invalid
                    face = navmesh.data.polygons[i]
                    for vert_index in face.vertices:
                        vert = navmesh.data.vertices[vert_index]
                        world_coord = navmesh.matrix_world @ vert.co
                        node_a_triangles_coords.append(world_coord)
                if node_b["Navmesh A Name"] == navmesh.name:
                    node_b_triangles = node_b["Navmesh A Triangles"]
                elif node_b["Navmesh B Name"] == navmesh.name:
                    node_b_triangles = node_b["Navmesh B Triangles"]
                else:
                    node_b_triangles = []  # can't find
                for i in node_b_triangles:
                    if i >= len(navmesh.data.polygons):
                        continue  # invalid
                    face = navmesh.data.polygons[i]
                    for vert_index in face.vertices:
                        vert = navmesh.data.vertices[vert_index]
                        world_coord = navmesh.matrix_world @ vert.co
                        node_b_triangles_coords.append(world_coord)
                selected_node_a = node_a
                selected_node_b = node_b

    if settings.mcg_graph_draw_enabled and all_edge_vertex_pairs:
        batch = batch_for_shader(shader, "LINES", {"pos": all_edge_vertex_pairs})
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)

    if settings.mcg_edge_triangles_highlight_enabled:
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
    if selected_node_a:
        gpu.state.depth_test_set("LESS_EQUAL")
        gpu.state.point_size_set(30)
        batch_sphere = batch_for_shader(shader, 'POINTS', {"pos": [selected_node_a.location]})
        shader.bind()
        shader.uniform_float("color", (1.0, 0.1, 0.1, 0.5))  # red
        batch_sphere.draw(shader)
    if selected_node_b:
        gpu.state.depth_test_set("LESS_EQUAL")
        gpu.state.point_size_set(30)
        batch_sphere = batch_for_shader(shader, 'POINTS', {"pos": [selected_node_b.location]})
        shader.bind()
        shader.uniform_float("color", (0.1, 0.1, 1.0, 0.5))  # blue
        batch_sphere.draw(shader)

    # gpu.state.blend_set("NONE")
