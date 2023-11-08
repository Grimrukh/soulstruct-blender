"""
Import MCG files (with/without DCX) into Blender 3.3+ (Python 3.10+ scripting required).

MCG files contain gate nodes and edges connecting them. Gate nodes lie on the boundaries between navmesh parts and edges
cross through a particular navmesh to connect two gate nodes.

This file format is only used in DeS and DS1 (PTDE/DSR).
"""
from __future__ import annotations

__all__ = ["ImportMCG", "QuickImportMCG"]

import re
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper

from soulstruct.darksouls1r.maps import MSB
from soulstruct.darksouls1r.maps.navmesh import MCG, MCGNode, MCGEdge

from io_soulstruct.general import SoulstructSettings
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

    custom_msb_path: bpy.props.StringProperty(
        name="Custom MSB Path",
        description="Custom MSB path to use for MCG import. Leave blank to auto-find",
        default="",
    )

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'})

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
                mcg.set_navmesh_references(msb.navmeshes)
                mcgs.append(mcg)

        importer = MCGImporter(self, context)
        for i, mcg in enumerate(mcgs):
            map_stem = file_paths[i].name.split(".")[0]
            importer.import_mcg(mcg, map_stem=map_stem, navmesh_part_names=navmesh_part_names)

        return {'FINISHED'}


class QuickImportMCG(LoggingOperator):
    bl_idname = "import_scene.quick_mcg"
    bl_label = "Import MCG"
    bl_description = "Import MCG navmesh node/edge graph file from selected game map"

    # MSB always auto-found.

    def execute(self, context):

        settings = SoulstructSettings.get_scene_settings(context)
        game_directory = settings.game_directory
        map_stem = settings.map_stem
        if not game_directory or not map_stem:
            return self.error("Game directory or map stem not set in Soulstruct plugin settings.")
        mcg_path = Path(game_directory, "map", map_stem, f"{map_stem}.mcg")
        if not mcg_path.is_file():
            return self.error(f"Could not find MCG file '{mcg_path}'.")
        msb_path = Path(game_directory, "map", "MapStudio", f"{map_stem}.msb")
        if not msb_path.is_file():
            return self.error(f"Could not find MSB file '{msb_path}'.")
        try:
            msb = MSB.from_path(msb_path)
        except Exception as ex:
            return self.error(f"Could not load MSB file '{msb_path}'. Error: {ex}")

        navmesh_part_names = [navmesh.name for navmesh in msb.navmeshes]

        try:
            mcg = MCG.from_path(mcg_path)
        except Exception as ex:
            return self.error(f"Error occurred while reading MCG file '{mcg_path}': {ex}")

        # TODO: I don't think we want to set these?
        # mcg.set_navmesh_references(msb.navmeshes)

        importer = MCGImporter(self, context)
        importer.import_mcg(mcg, map_stem=map_stem, navmesh_part_names=navmesh_part_names)

        return {'FINISHED'}


class MCGImporter:

    def __init__(
        self,
        operator: LoggingOperator,
        context,
    ):
        self.operator = operator
        self.context = context

        self.all_bl_objs = []

    def import_mcg(self, mcg: MCG, map_stem: str, navmesh_part_names: list[str]) -> bpy.types.Object:
        self.operator.info(f"Importing MCG: {map_stem}")

        highest_navmesh_index = max(edge.navmesh_index for edge in mcg.edges)
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

        # Actual MCG binary file stores navmesh node triangle indices for every edge, which is extremely redundant, as
        # every node touches exactly two navmeshes and its connected edges in each of those two navmeshes always use
        # consistent triangles. So we store them on the NODES in Blender and write them back to edges on export. (This
        # is strictly a Blender thing - the Soulstruct `MCGEdge` classes still hold their node triangle indices - but
        # does use a Soulstruct `MCG` method to verify the triangles used on a node-by-node basis rather than by edge.)
        # NOTE: If a node uses inconsistent triangles in different edges in the same navmesh, the first indices will be
        # used a warning logged. If a node seemingly has edges in more than two navmeshes, import will fail, as the MCG
        # file is not valid (for DS1 at least).
        node_triangle_indices = mcg.get_navmesh_triangles_by_node()

        for i, (node, triangle_indices) in enumerate(zip(mcg.nodes, node_triangle_indices)):
            node: MCGNode
            name = f"{map_stem} Node {i}"

            bl_node = self.create_node(node, name)
            self.context.collection.objects.link(bl_node)
            self.all_bl_objs.append(bl_node)
            bl_node.parent = node_parent
            
            if node.dead_end_navmesh_index >= 0:
                try:
                    dead_end_navmesh_name = navmesh_part_names[node.dead_end_navmesh_index]
                except IndexError:
                    raise ValueError(f"Node {i} has invalid dead-end navmesh index: {node.dead_end_navmesh_index}")
                bl_node["Dead End Navmesh Name"] = dead_end_navmesh_name
                # NOTE: For inspection convenience only. The true navmesh part name/index is stored in properties.
                bl_node.name += f" <Dead End: {dead_end_navmesh_name}>"
            else:
                bl_node["Dead End Navmesh Name"] = ""
            bl_node["Unk Offset"] = node.unknown_offset
            # Triangle indices are stored on the node, not the edge, for convenience, as they should be the same.
            for navmesh_key in ("a", "b"):
                key_caps = navmesh_key.capitalize()
                if triangle_indices[navmesh_key]:
                    navmesh_a_index, navmesh_a_triangles = triangle_indices[navmesh_key]
                    try:
                        bl_node[f"Navmesh {key_caps} Name"] = navmesh_part_names[navmesh_a_index]
                    except IndexError:
                        raise ValueError(f"Node {i} has invalid navmesh {key_caps} index: {navmesh_a_index}")
                    bl_node[f"Navmesh {key_caps} Triangles"] = navmesh_a_triangles

            # Connected node/edge indices not kept; inferred from edges.
            self.all_bl_objs.append(bl_node)

        for i, edge in enumerate(mcg.edges):
            edge: MCGEdge  # TODO: remove when PyCharm fixed
            node_a_index = mcg.nodes.index(edge.node_a)
            node_b_index = mcg.nodes.index(edge.node_b)
            if node_a_index >= len(mcg.nodes):
                raise ValueError(f"Edge {i} has invalid node A index: {node_a_index}")
            if node_b_index >= len(mcg.nodes):
                raise ValueError(f"Edge {i} has invalid node B index: {node_b_index}")
            try:
                navmesh_name = navmesh_part_names[edge.navmesh_index]
            except IndexError:
                raise ValueError(f"Edge {i} has invalid navmesh index {edge.navmesh_index}.")
            # NOTE: Suffix is for inspection convenience only. The true navmesh part name/index is stored in properties.
            # Also note that we don't include the edge index in the name (unlike nodes) because it is unused elsewhere.
            # The start and end node indices are enough to uniquely identify an edge.
            name = f"{map_stem} Edge ({node_a_index} -> {node_b_index}) <{navmesh_name}>"
            bl_edge = self.create_edge(edge, name)
            self.context.collection.objects.link(bl_edge)
            self.all_bl_objs.append(bl_edge)
            bl_edge.parent = edge_parent

            bl_edge["Cost"] = edge.cost
            bl_edge["Navmesh Name"] = navmesh_name
            bl_edge["Node A"] = f"Node {node_a_index}"
            bl_edge["Node B"] = f"Node {node_b_index}"
            # Triangles are stored on the nodes (above) as they should be identical for all edges on the same navmesh.

            self.all_bl_objs.append(bl_edge)

        # Automatically set node and edge parents for drawing.
        self.context.scene.mcg_draw_settings.mcg_parent_name = mcg_parent.name

        return mcg_parent

    @staticmethod
    def create_node(node: MCGNode, name: str):
        """Create an Empty representing `node`."""
        position = GAME_TO_BL_VECTOR(node.translate)
        bl_node = bpy.data.objects.new(name, None)
        bl_node.empty_display_type = "SPHERE"
        bl_node.location = position
        return bl_node

    @staticmethod
    def create_edge(edge: MCGEdge, name: str):
        """Create an Empty representing `edge` that connects two nodes."""
        start = GAME_TO_BL_VECTOR(edge.node_a.translate)
        end = GAME_TO_BL_VECTOR(edge.node_b.translate)
        direction = end - start
        midpoint = (start + end) / 2.0
        bl_edge = bpy.data.objects.new(name, None)
        bl_edge.empty_display_type = "PLAIN_AXES"
        bl_edge.location = midpoint
        # Point empty arrow in direction of edge.
        bl_edge.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
        return bl_edge
