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

    load_msb_navmesh_names: bpy.props.BoolProperty(
        name="Load MSB Navmesh Names",
        description="Load navmesh part names from the map's MSB file and add them to names of created MCG edges",
        default=True,
    )

    def execute(self, context):
        print("Executing MCG import...")

        file_paths = [Path(self.directory, file.name) for file in self.files]

        mcgs = []
        for file_path in file_paths:
            try:
                mcg = MCG.from_path(file_path)
            except Exception as ex:
                self.warning(f"Error occurred while reading MCG file '{file_path.name}': {ex}")
            else:
                mcgs.append(mcg)

        navmesh_part_names = []
        if self.load_msb_navmesh_names:
            map_path_match = MAP_STEM_RE.match(Path(self.directory).stem)
            if not map_path_match:
                self.warning(f"Could not determine map name from directory '{self.directory}'.")
                # Continue with MCG import below.
            else:
                # NOTE: Still correct for DS1 `m12_00_00_01` MCG, which should be used over the _00 one anyway.
                msb_path = Path(self.directory).parent / f"MapStudio/{map_path_match.group(0)}.msb"
                msb = MSB.from_path(msb_path)
                navmesh_part_names = [navmesh.name for navmesh in msb.navmeshes]

        importer = MCGImporter(self, context)
        for i, mcg in enumerate(mcgs):
            # TODO: load navmesh part names from MSB (and check same count)
            importer.import_mcg(mcg, f"{file_paths[i].stem} MCG", navmesh_part_names=navmesh_part_names)

        return {'FINISHED'}


class MCGImporter:

    def __init__(
        self,
        operator: ImportMCG,
        context,
    ):
        self.operator = operator
        self.context = context

        self.mcg = None
        self.bl_name = ""
        self.all_bl_objs = []

    def import_mcg(self, mcg: MCG, bl_name: str, navmesh_part_names: list[str] = ()) -> bpy.types.Object:
        self.mcg = mcg
        self.bl_name = bl_name
        self.operator.info(f"Importing MCG: {bl_name}")

        if navmesh_part_names:
            highest_navmesh_index = max(edge._navmesh_part_index for edge in mcg.edges)
            if highest_navmesh_index >= len(navmesh_part_names):
                self.operator.warning(
                    f"Highest MCG edge navmesh part index ({highest_navmesh_index}) exceeds number of navmesh part "
                    f"names provided ({len(navmesh_part_names)}. Ignoring these part names."
                )
                navmesh_part_names = []
            # NOTE: navmesh count can exceed highest edge index, as some navmeshes may have no edges in them.

        # Set mode to OBJECT and deselect all objects.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action="DESELECT")
        if bpy.ops.object.mode_set.poll():  # just to be safe
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        mcg_parent = bpy.data.objects.new(bl_name, None)  # empty parent for MCG node and edge parents
        self.context.collection.objects.link(mcg_parent)
        self.all_bl_objs.append(mcg_parent)
        
        node_parent = bpy.data.objects.new(f"{bl_name} Nodes", None)
        self.context.collection.objects.link(node_parent)
        self.all_bl_objs.append(node_parent)
        node_parent.parent = mcg_parent
        
        edge_parent = bpy.data.objects.new(f"{bl_name} Edges", None)
        self.context.collection.objects.link(edge_parent)
        self.all_bl_objs.append(edge_parent)
        edge_parent.parent = mcg_parent

        # Automatically set node and edge parents for drawing.
        self.context.scene.mcg_draw_settings.mcg_node_parent_name = node_parent.name
        self.context.scene.mcg_draw_settings.mcg_edge_parent_name = edge_parent.name

        # try:
        #     bl_material = bpy.data.materials["Navmesh MCG"]
        # except KeyError:
        #     # Create new material with green color.
        #     color = hsv_color(0.333, 0.9, 0.2)
        #     bl_material = create_basic_material("Navmesh MCG", color)

        bl_node_names = []  # type: list[str]
        for i, node in enumerate(mcg.nodes):
            node: GateNode
            name = f"Node {i}"
            if node._dead_end_navmesh_index >= 0 and navmesh_part_names:
                # NOTE: For inspection convenience only. The true navmesh part name/index is stored in properties.
                name += f" <Dead End: {navmesh_part_names[node._dead_end_navmesh_index]}>"

            bl_node = self.create_node(node, name, as_sphere=False)
            self.context.collection.objects.link(bl_node)
            self.all_bl_objs.append(bl_node)
            bl_node.parent = node_parent
            # bl_node.data.materials.append(bl_material)
            
            if navmesh_part_names:
                try:
                    bl_node["dead_end_navmesh_name"] = navmesh_part_names[node._dead_end_navmesh_index]
                except IndexError:
                    raise ValueError(f"Node {i} has invalid dead-end navmesh index {node._dead_end_navmesh_index}.")
            else:
                bl_node["dead_end_navmesh_index"] = node._dead_end_navmesh_index
            bl_node["unknown_offset"] = node.unknown_offset
            bl_node["connected_node_indices"] = [mcg.nodes.index(n) for n in node.connected_nodes]
            bl_node["connected_edge_indices"] = [mcg.edges.index(e) for e in node.connected_edges]
            self.all_bl_objs.append(bl_node)
            bl_node_names.append(bl_node.name)

        for i, edge in enumerate(mcg.edges):
            edge: GateEdge
            start_node_index = mcg.nodes.index(edge.start_node)
            end_node_index = mcg.nodes.index(edge.end_node)
            name = f"Edge {i} ({start_node_index} -> {end_node_index})"
            if navmesh_part_names:
                # NOTE: For inspection convenience only. The true navmesh part name/index is stored in properties.
                name += f" <{navmesh_part_names[edge._navmesh_part_index]}>"

            bl_edge = self.create_edge(edge, name, as_cylinder=False)
            self.context.collection.objects.link(bl_edge)
            self.all_bl_objs.append(bl_edge)
            bl_edge.parent = edge_parent
            # bl_edge.data.materials.append(bl_material)

            try:
                bl_edge["start_node_name"] = bl_node_names[start_node_index]
            except IndexError:
                raise ValueError(f"Edge {i} has invalid start node index {start_node_index}.")
            bl_edge["start_node_faces"] = edge.start_node_triangle_indices
            try:
                bl_edge["end_node_name"] = bl_node_names[end_node_index]
            except IndexError:
                raise ValueError(f"Edge {i} has invalid end node index {end_node_index}.")
            bl_edge["end_node_faces"] = edge.end_node_triangle_indices
            if navmesh_part_names:
                try:
                    bl_edge["navmesh_name"] = navmesh_part_names[edge._navmesh_part_index]
                except IndexError:
                    raise ValueError(f"Edge {i} has invalid navmesh index {edge._navmesh_part_index}.")
            else:
                bl_edge["navmesh_index"] = edge._navmesh_part_index
            bl_edge["cost"] = edge.cost

            self.all_bl_objs.append(bl_edge)

        return mcg_parent

    @staticmethod
    def create_node(node: GateNode, name: str, as_sphere=False):
        """Create an Empty or Icosphere representing `node`. Its transform represents its position."""
        position = GAME_TO_BL_VECTOR(node.translate)
        if as_sphere:
            bpy.ops.mesh.primitive_ico_sphere_add(4)
            bl_node = bpy.context.active_object
            bpy.ops.object.modifier_add(type="WIREFRAME")
            bl_node.modifiers[0].thickness = 0.05
            bl_node.name = name
        else:
            bl_node = bpy.data.objects.new(name, None)
            bl_node.empty_display_type = "SPHERE"
        bl_node.location = position
        return bl_node

    @staticmethod
    def create_edge(edge: GateEdge, name: str, as_cylinder=False):
        """Create an Empty or Cylinder representing `edge` that connects two nodes."""

        # Calculate the distance and midpoint
        start = GAME_TO_BL_VECTOR(edge.start_node.translate)
        end = GAME_TO_BL_VECTOR(edge.end_node.translate)
        direction = end - start
        midpoint = (start + end) / 2.0

        if as_cylinder:
            # Add a cylinder
            bpy.ops.mesh.primitive_cylinder_add(
                radius=0.2,
                depth=direction.length,
                location=midpoint,
            )
            bl_edge = bpy.context.active_object
            bl_edge.name = name
        else:
            bl_edge = bpy.data.objects.new(name, None)
            bl_edge.empty_display_type = "SINGLE_ARROW"
            bl_edge.location = midpoint

        # Point cylinder OR empty arrow in direction of edge.
        bl_edge.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()

        return bl_edge
