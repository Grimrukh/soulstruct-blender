from __future__ import annotations

__all__ = [
    "CreateMCGEdgeOperator",
    "create_mcg_edge",
    "set_node_navmesh_name_triangles",
    "SetNodeNavmeshATriangles",
    "SetNodeNavmeshBTriangles",
]

import bmesh
import bpy

from io_soulstruct.navmesh.nav_graph.utilities import MCGExportError
from io_soulstruct.utilities.operators import LoggingOperator


class MCGEdgeCreationError(Exception):
    """Exception raised during MCG edge creation."""
    pass


class CreateMCGEdgeOperator(LoggingOperator):
    """Create an MCG edge between two nodes on a navmesh."""
    bl_idname = "io_soulstruct_scene.create_mcg_edge"
    bl_label = "Create MCG Edge"
    bl_description = "Create an MCG edge between two selected nodes on the selected navmesh"

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "OBJECT"
            and len(context.selected_objects) == 3
            and bpy.context.scene.mcg_draw_settings.mcg_parent_name != ""
        )

    def execute(self, context):

        try:
            create_mcg_edge(context, bpy.data)
        except Exception as ex:
            return self.error(str(ex))

        return {"FINISHED"}


def create_mcg_edge(context, data):
    if not context.scene.mcg_draw_settings.mcg_parent_name:
        raise MCGEdgeCreationError("No MCG parent object specified.")
    try:
        mcg_parent = data.objects[bpy.context.scene.mcg_draw_settings.mcg_parent_name]
    except KeyError:
        raise MCGEdgeCreationError(
            f"MCG parent object '{bpy.context.scene.mcg_draw_settings.mcg_parent_name}' not found."
        )

    node_parent = edge_parent = None
    for child in mcg_parent.children:
        if not node_parent and child.name.endswith(" Nodes"):
            node_parent = child
            if edge_parent:
                break
        elif not edge_parent and child.name.endswith(" Edges"):
            edge_parent = child
            if node_parent:
                break
    if not node_parent or not edge_parent:
        raise MCGEdgeCreationError("MCG parent object does not have 'Nodes' and 'Edges' children.")

    try:
        node_a, node_b = [obj for obj in context.selected_objects if obj.type == "EMPTY"]
    except ValueError:
        raise MCGEdgeCreationError("Must select exactly two MCG nodes (empties).")

    meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
    if len(meshes) > 1 or not meshes:
        raise MCGEdgeCreationError("Must select exactly one navmesh.")
    navmesh = meshes[0]

    if node_a not in node_parent.children:
        raise MCGEdgeCreationError(f"Start node '{node_a.name}' not a child of MCG nodes.")
    if node_b not in node_parent.children:
        raise MCGEdgeCreationError(f"End node '{node_b.name}' not a child of MCG nodes.")

    # Find selected nodes
    map_stem = mcg_parent.name.split(" ")[0]
    node_prefix = f"{map_stem} Node "
    if node_a.name.startswith(node_prefix):
        node_a_index = node_a.name.removeprefix(node_prefix).split("<")[0].strip()  # ignore dead end suffix
    else:
        raise MCGExportError(f"Node '{node_a.name}' does not start with '{map_stem} Node '.")
    if node_b.name.startswith(node_prefix):
        node_b_index = node_b.name.removeprefix(node_prefix).split("<")[0].strip()  # ignore dead end suffix
    else:
        raise MCGExportError(f"Node '{node_b.name}' does not start with '{map_stem} Node '.")

    if int(node_b_index) < int(node_a_index):
        # Swap nodes.
        node_a_index, node_b_index = node_b_index, node_a_index
        node_a, node_b = node_b, node_a

    # Check edge names for duplicates (ignoring navmesh, which doesn't count toward edge uniqueness).
    edge_name = (
        f"{mcg_parent.name.split(' ')[0]} Edge ({node_a_index} -> {node_b_index})"
    )
    backwards_edge_name = (
        f"{mcg_parent.name.split(' ')[0]} Edge ({node_b_index} -> {node_a_index})"
    )
    existing_edge_names = {edge.name.split(" <")[0] for edge in edge_parent.children}
    if edge_name in existing_edge_names:
        raise MCGEdgeCreationError(f"Edge '{edge_name}' already exists.")
    if backwards_edge_name in existing_edge_names:
        raise MCGEdgeCreationError(f"Edge '{backwards_edge_name}' already exists.")

    edge_name += f" <{navmesh.name}>"

    start = node_a.location
    end = node_b.location
    length = (end - start).length
    direction = end - start
    midpoint = (start + end) / 2.0
    bl_edge = bpy.data.objects.new(edge_name, None)
    bl_edge.empty_display_type = "PLAIN_AXES"
    bl_edge.location = midpoint
    bl_edge.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    bl_edge.parent = edge_parent

    # Add edge to same collection(s) as parent.
    for collection in mcg_parent.users_collection:
        collection.objects.link(bl_edge)
    if not mcg_parent.users_collection:
        # Add to context collection if parent has no collections.
        context.collection.objects.link(bl_edge)

    # Initial cost is twice the distance between the nodes.
    bl_edge["Cost"] = 2 * length
    bl_edge["Navmesh Name"] = navmesh.name
    bl_edge["Node A"] = f"Node {node_a_index}"
    bl_edge["Node B"] = f"Node {node_b_index}"


def set_node_navmesh_name_triangles(context, a_or_b: str):
    node = context.selected_objects[0]
    name_prop = f"Navmesh {a_or_b} Name"
    if node.get(name_prop, None) is None:
        raise MCGEdgeCreationError(f"Selected node does not have a '{name_prop}' property.")
    triangles_prop = f"Navmesh {a_or_b} Triangles"
    if node.get(triangles_prop, None) is None:
        raise MCGEdgeCreationError(f"Selected node does not have a '{triangles_prop}' property.")
    navmesh = context.edit_object
    node[name_prop] = navmesh.name
    bm = bmesh.from_edit_mesh(navmesh.data)
    node[triangles_prop] = [f.index for f in bm.faces if f.select]
    del bm


class SetNodeNavmeshATriangles(LoggingOperator):
    bl_idname = "io_soulstruct_scene.set_node_navmesh_a_triangles"
    bl_label = "Set Node Navmesh A Triangles"
    bl_description = "Use edited mesh to set the navmesh name and triangle indices of Navmesh A on selected MCG node"

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "EDIT_MESH"
            and 0 < len(context.selected_objects) <= 2
            and context.selected_objects[0].type == "EMPTY"
            # NOTE: We don't explicitly poll for 'Navmesh A Name' and 'Navmesh A Triangles' properties, so that the
            # user can see an informative error message about their absence if missing.
        )

    def execute(self, context):

        try:
            set_node_navmesh_name_triangles(context, "A")
        except Exception as ex:
            return self.error(str(ex))

        return {"FINISHED"}


class SetNodeNavmeshBTriangles(LoggingOperator):
    bl_idname = "io_soulstruct_scene.set_node_navmesh_b_triangles"
    bl_label = "Set Node Navmesh B Triangles"
    bl_description = "Use edited mesh to set the navmesh name and triangle indices of Navmesh B on selected MCG node"

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "EDIT_MESH"
            and 0 < len(context.selected_objects) <= 2
            and context.selected_objects[0].type == "EMPTY"
            # NOTE: We don't explicitly poll for 'Navmesh A Name' and 'Navmesh A Triangles' properties, so that the
            # user can see an informative error message about their absence if missing.
        )

    def execute(self, context):

        try:
            set_node_navmesh_name_triangles(context, "B")
        except Exception as ex:
            return self.error(str(ex))

        return {"FINISHED"}
