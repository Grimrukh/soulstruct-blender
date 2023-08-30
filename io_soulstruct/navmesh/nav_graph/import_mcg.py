"""
Import MCP/MCG files (with/without DCX) into Blender 3.3+ (Python 3.10+ scripting required).

MCP files contain AABBs that match up to Navmesh part instances in the map's MSB.

MCG files contain gate nodes and edges connecting them. Gate nodes lie on the boundaries between navmesh parts and edges
cross through a particular navmesh to connect two gate nodes.

This file format is only used in DeS and DS1 (PTDE/DSR).
"""
from __future__ import annotations

__all__ = ["ImportMCG"]

import re
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper

from soulstruct.darksouls1r.maps import MSB
from soulstruct.darksouls1r.maps.navmesh import MCG, GateNode, GateEdge

from io_soulstruct.utilities import *
from .utilities import MCGImportError

MCG_NAME_RE = re.compile(r"(?P<stem>.*)\.mcg(?P<dcx>\.dcx)?")


class ImportMCG(LoggingOperator, ImportHelper):
    bl_idname = "import_scene.mcg"
    bl_label = "Import MCG"
    bl_description = "Import an MCG navmesh node/edge graph file. Supports DCX-compressed files"

    filename_ext = ".mcg"

    filter_glob: bpy.props.StringProperty(
        default="*.mcg;*.mcg.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    files: bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    directory: bpy.props.StringProperty(
        options={'HIDDEN'},
    )

    custom_msb_path: bpy.props.StringProperty(
        name="Custom MSB Path",
        description="Custom MSB path to use for MCG import. Leave blank to auto-find",
        default="",
    )

    def execute(self, context):
        print("Executing MCG import...")

        file_paths = [Path(self.directory, file.name) for file in self.files]

        if not self.custom_msb_path:
            directory_path = Path(self.directory)
            msb_path = directory_path.parent / "MapStudio" / f"{directory_path.stem}.msb"
        else:
            msb_path = Path(self.custom_msb_path)
        if not msb_path.is_file():
            return self.error(f"Could not find MSB file '{msb_path}'.")
        try:
            msb = MSB.from_path(msb_path)
        except Exception as ex:
            return self.error(f"Could not load MSB file '{msb_path}'. Error: {ex}")

        navmesh_part_names = [navmesh.name for navmesh in msb.navmeshes]

        mcgs = []
        for file_path in file_paths:
            try:
                mcg = MCG.from_path(file_path)
            except Exception as ex:
                self.warning(f"Error occurred while reading MCG file '{file_path.name}': {ex}")
            else:
                mcgs.append(mcg)

        importer = MCGImporter(self, context)
        for i, mcg in enumerate(mcgs):
            map_stem = file_paths[i].name.split(".")[0]
            importer.import_mcg(mcg, map_stem=map_stem, navmesh_part_names=navmesh_part_names)

        return {'FINISHED'}


class MCGImporter:

    def __init__(
        self,
        operator: ImportMCG,
        context,
    ):
        self.operator = operator
        self.context = context

        self.all_bl_objs = []

    def import_mcg(self, mcg: MCG, map_stem: str, navmesh_part_names: list[str]) -> bpy.types.Object:
        self.operator.info(f"Importing MCG: {map_stem}")

        highest_navmesh_index = max(edge._navmesh_part_index for edge in mcg.edges)
        if highest_navmesh_index >= len(navmesh_part_names):
            raise MCGImportError(
                f"Highest MCG edge navmesh part index ({highest_navmesh_index}) exceeds number of navmesh part "
                f"names provided ({len(navmesh_part_names)}."
            )
        # NOTE: navmesh count can exceed highest edge index, as some navmeshes may have no edges in them.

        # Set mode to OBJECT and deselect all objects.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action="DESELECT")
        if bpy.ops.object.mode_set.poll():  # just to be safe
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        mcg_parent = bpy.data.objects.new(f"{map_stem} MCG", None)  # empty parent for MCG node and edge parents
        self.context.collection.objects.link(mcg_parent)
        self.all_bl_objs.append(mcg_parent)
        
        node_parent = bpy.data.objects.new(f"{map_stem} Nodes", None)
        self.context.collection.objects.link(node_parent)
        self.all_bl_objs.append(node_parent)
        node_parent.parent = mcg_parent
        
        edge_parent = bpy.data.objects.new(f"{map_stem} Edges", None)
        self.context.collection.objects.link(edge_parent)
        self.all_bl_objs.append(edge_parent)
        edge_parent.parent = mcg_parent

        # Automatically set node and edge parents for drawing.
        self.context.scene.mcg_draw_settings.mcg_parent_name = mcg_parent.name

        for i, node in enumerate(mcg.nodes):
            node: GateNode
            name = f"{map_stem} Node {i}"
            if node._dead_end_navmesh_index >= 0 and navmesh_part_names:
                # NOTE: For inspection convenience only. The true navmesh part name/index is stored in properties.
                name += f" <Dead End: {navmesh_part_names[node._dead_end_navmesh_index]}>"

            bl_node = self.create_node(node, name)
            self.context.collection.objects.link(bl_node)
            self.all_bl_objs.append(bl_node)
            bl_node.parent = node_parent
            
            if node._dead_end_navmesh_index >= 0:
                try:
                    bl_node["dead_end_navmesh_name"] = navmesh_part_names[node._dead_end_navmesh_index]
                except IndexError:
                    raise ValueError(f"Node {i} has invalid dead-end navmesh index {node._dead_end_navmesh_index}.")
            else:
                bl_node["dead_end_navmesh_name"] = ""
            bl_node["unknown_offset"] = node.unknown_offset
            # Connected node/edge indices not kept; inferred from edges.
            self.all_bl_objs.append(bl_node)

        for i, edge in enumerate(mcg.edges):
            edge: GateEdge
            start_node_index = mcg.nodes.index(edge.start_node)
            end_node_index = mcg.nodes.index(edge.end_node)
            if start_node_index >= len(mcg.nodes):
                raise ValueError(f"Edge {i} has invalid start node index {start_node_index}.")
            if end_node_index >= len(mcg.nodes):
                raise ValueError(f"Edge {i} has invalid end node index {end_node_index}.")
            try:
                navmesh_name = navmesh_part_names[edge._navmesh_part_index]
            except IndexError:
                raise ValueError(f"Edge {i} has invalid navmesh index {edge._navmesh_part_index}.")
            # NOTE: Suffix is for inspection convenience only. The true navmesh part name/index is stored in properties.
            # Also note that we don't include the edge index in the name (unlike nodes) because it is unused elsewhere.
            # The start and end node indices are enough to uniquely identify an edge.
            name = f"{map_stem} Edge ({start_node_index} -> {end_node_index}) <{navmesh_name}>"
            bl_edge = self.create_edge(edge, name)
            self.context.collection.objects.link(bl_edge)
            self.all_bl_objs.append(bl_edge)
            bl_edge.parent = edge_parent

            bl_edge["start_node_name"] = f"Node {start_node_index}"
            bl_edge["start_node_triangle_indices"] = edge.start_node_triangle_indices
            bl_edge["end_node_name"] = f"Node {end_node_index}"
            bl_edge["end_node_triangle_indices"] = edge.end_node_triangle_indices
            bl_edge["navmesh_name"] = navmesh_name
            bl_edge["cost"] = edge.cost

            self.all_bl_objs.append(bl_edge)

        return mcg_parent

    @staticmethod
    def create_node(node: GateNode, name: str):
        """Create an Empty representing `node`."""
        position = GAME_TO_BL_VECTOR(node.translate)
        bl_node = bpy.data.objects.new(name, None)
        bl_node.empty_display_type = "SPHERE"
        bl_node.location = position
        return bl_node

    @staticmethod
    def create_edge(edge: GateEdge, name: str):
        """Create an Empty representing `edge` that connects two nodes."""
        start = GAME_TO_BL_VECTOR(edge.start_node.translate)
        end = GAME_TO_BL_VECTOR(edge.end_node.translate)
        direction = end - start
        midpoint = (start + end) / 2.0
        bl_edge = bpy.data.objects.new(name, None)
        bl_edge.empty_display_type = "PLAIN_AXES"
        bl_edge.location = midpoint
        # Point empty arrow in direction of edge.
        bl_edge.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
        return bl_edge
