from __future__ import annotations

__all__ = [
    "MCGImportError",
    "MCGExportError",
    "CreateMCGEdge",
]

import bpy

from io_soulstruct.utilities import LoggingOperator


class MCGImportError(Exception):
    """Exception raised during NVM import."""
    pass


class MCGExportError(Exception):
    """Exception raised during NVM export."""
    pass


class CreateMCGEdge(LoggingOperator):
    """Create an MCG edge between two nodes on a navmesh."""
    bl_idname = "io_soulstruct_scene.create_mcg_edge"
    bl_label = "Create MCG Edge"
    bl_description = "Create an MCG edge between two selected nodes on a navmesh"

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" and len(context.selected_objects) == 3 and bpy.context.scene.mcg_draw_settings.mcg_parent_name != ""

    def execute(self, context):
        if not bpy.context.scene.mcg_draw_settings.mcg_parent_name:
            return self.error("No MCG parent object specified.")
        try:
            mcg_parent = bpy.data.objects[bpy.context.scene.mcg_draw_settings.mcg_parent_name]
        except KeyError:
            return self.error(f"MCG parent object '{bpy.context.scene.mcg_draw_settings.mcg_parent_name}' not found.")

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
            return self.error("MCG parent object does not have 'Nodes' and 'Edges' children.")

        try:
            start_node, end_node = [obj for obj in context.selected_objects if obj.type == "EMPTY"]
        except ValueError:
            return self.error("Must select exactly two MCG nodes (empties).")

        meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if len(meshes) > 1 or not meshes:
            return self.error("Must select exactly one navmesh.")
        navmesh = meshes[0]

        if start_node not in node_parent.children:
            return self.error(f"Start node '{start_node.name}' not a child of MCG nodes.")
        if end_node not in node_parent.children:
            return self.error(f"End node '{end_node.name}' not a child of MCG nodes.")

        # Find selected nodes
        map_stem = mcg_parent.name.split(" ")[0]
        node_prefix = f"{map_stem} Node "
        if start_node.name.startswith(node_prefix):
            start_node_index = start_node.name.removeprefix(node_prefix).split("<")[0].strip()  # ignore dead end suffix
        else:
            raise MCGExportError(f"Node '{start_node.name}' does not start with '{map_stem} Node '.")
        if end_node.name.startswith(node_prefix):
            end_node_index = end_node.name.removeprefix(node_prefix).split("<")[0].strip()  # ignore dead end suffix
        else:
            raise MCGExportError(f"Node '{end_node.name}' does not start with '{map_stem} Node '.")

        if int(end_node_index) < int(start_node_index):
            # Swap nodes.
            start_node_index, end_node_index = end_node_index, start_node_index
            start_node, end_node = end_node, start_node

        # Check edge names for duplicates (ignoring navmesh, which doesn't count toward edge uniqueness).
        edge_name = (
            f"{mcg_parent.name.split(' ')[0]} Edge ({start_node_index} -> {end_node_index})"
        )
        backwards_edge_name = (
            f"{mcg_parent.name.split(' ')[0]} Edge ({end_node_index} -> {start_node_index})"
        )
        existing_edge_names = {edge.name.split(" <")[0] for edge in edge_parent.children}
        if edge_name in existing_edge_names:
            return self.error(f"Edge '{edge_name}' already exists.")
        if backwards_edge_name in existing_edge_names:
            return self.error(f"Edge '{backwards_edge_name}' already exists.")

        edge_name += f" <{navmesh.name}>"

        start = start_node.location
        end = end_node.location
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

        bl_edge["start_node_name"] = f"Node {start_node_index}"
        bl_edge["start_node_triangle_indices"] = [0, 1]  # default
        bl_edge["end_node_name"] = f"Node {end_node_index}"
        bl_edge["end_node_triangle_indices"] = [0, 1]  # default
        bl_edge["cost"] = 1.0
        bl_edge["navmesh_name"] = navmesh.name

        return {"FINISHED"}
