from __future__ import annotations

__all__ = [
    "CreateMCGEdgeOperator",
    "create_mcg_edge",
    "set_node_navmesh_name_triangles",
    "SetNodeNavmeshATriangles",
    "SetNodeNavmeshBTriangles",
    "RefreshMCGNames",
]

import bmesh
import bpy

from io_soulstruct.navmesh.nav_graph.utilities import MCGExportError
from io_soulstruct.utilities.operators import LoggingOperator
from io_soulstruct.utilities.misc import natural_keys


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
        context.scene.collection.objects.link(bl_edge)

    # Initial cost is twice the distance between the nodes.
    bl_edge["Cost"] = 2 * length
    bl_edge["Navmesh Name"] = navmesh.name
    bl_edge["Node A"] = f"Node {node_a_index}"
    bl_edge["Node B"] = f"Node {node_b_index}"


def set_node_navmesh_name_triangles(context, a_or_b: str):
    node = context.selected_objects[0]
    name_prop = f"Navmesh {a_or_b} Name"
    triangles_prop = f"Navmesh {a_or_b} Triangles"
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


class RefreshMCGNames(LoggingOperator):
    bl_idname = "io_soulstruct_scene.refresh_mcg_names"
    bl_label = "Refresh MCG Names"
    bl_description = "Refresh all MCG node and edge names in the selected MCG parent and update name references"

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "OBJECT"
            and len(context.selected_objects) == 1
            and context.selected_objects[0].type == "EMPTY"
            and context.selected_objects[0].name.endswith(" MCG")
        )

    def execute(self, context):

        parent = context.selected_objects[0]
        map_stem = parent.name.split(" ")[0]
        node_parent = edge_parent = None
        for child in parent.children:
            if child.name.endswith(" Nodes"):
                node_parent = child
                if edge_parent:
                    break
            elif child.name.endswith(" Edges"):
                edge_parent = child
                if node_parent:
                    break
        if not node_parent or not edge_parent:
            return self.error("MCG parent object does not have 'Nodes' and 'Edges' children.")

        # We do multiple passes over nodes and edges to validate current references before changing ANYTHING.

        # Map old node names to their new navmesh A/B model IDs (which fully determine new names):
        new_node_indices = {}
        indices_counts = {}  # counts number of nodes connecting the same two navmesh parts
        for node in sorted(node_parent.children, key=lambda o: natural_keys(o.name)):
            node_name = node.name.split("<")[0].strip()

            navmesh_a_name = node["Navmesh A Name"]
            try:
                a_id = int(navmesh_a_name[1:5])
            except ValueError:
                return self.error(
                    f"Node '{node.name}' has invalid Navmesh A name '{navmesh_a_name}'. Must start with 'n####'."
                )

            try:
                navmesh_b_name = node["Navmesh B Name"]
            except KeyError:
                # Use dead end navmesh name instead of B.
                try:
                    navmesh_b_name = node["Dead End Navmesh Name"]
                except KeyError:
                    return self.error(f"Node '{node.name}' has no Navmesh B Name or Dead End Navmesh Name.")
            try:
                b_id = int(navmesh_b_name[1:5])
            except ValueError:
                return self.error(
                    f"Node '{node.name}' has invalid Navmesh B name '{navmesh_b_name}'. Must start with 'n####'."
                )
            check_indices = (b_id, a_id) if a_id > b_id else (a_id, b_id)
            if check_indices not in indices_counts:
                indices_counts[check_indices] = 1
                new_node_indices[node_name] = f"[{a_id} | {b_id}]"  # first instance
            else:
                new_node_indices[node_name] = f"[{a_id} | {b_id}] ({indices_counts[check_indices]})"
                indices_counts[check_indices] += 1

        # Check all edge references to ensure they are valid.
        for edge in edge_parent.children:
            if edge["Node A"] not in new_node_indices:
                return self.error(f"Edge '{edge.name}' references non-existent start node '{edge['Node A']}'.")
            if edge["Node B"] not in new_node_indices:
                return self.error(f"Edge '{edge.name}' references non-existent end node '{edge['Node B']}'.")

        # Now update node names with new indices.
        node_prefix = f"{map_stem} Node "
        for node, new_indices in zip(
            sorted(node_parent.children, key=lambda o: natural_keys(o.name)), new_node_indices.values()
        ):
            node.name = f"{node_prefix}{new_indices}"
            if node["Dead End Navmesh Name"] != "":
                # Suffix for node object name only, not assigned to node name in edge.
                node.name += " <DEAD END>"

        # Finally, update edge references and names.
        edge_prefix = f"{map_stem} Edge "
        for edge in edge_parent.children:
            new_node_a_indices = new_node_indices[edge["Node A"]]  # already validated
            new_node_b_indices = new_node_indices[edge["Node B"]]  # already validated
            navmesh_name = edge["Navmesh Name"]
            edge.name = f"{edge_prefix}({new_node_a_indices} -> {new_node_b_indices}) <{navmesh_name}>"
            edge["Node A"] = f"{node_prefix}{new_node_a_indices}"
            edge["Node B"] = f"{node_prefix}{new_node_b_indices}"

        return {"FINISHED"}
