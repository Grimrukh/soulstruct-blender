from __future__ import annotations

__all__ = ["ExportMCG", "ExportMCGMCPToMap"]

import traceback
from pathlib import Path

import bpy
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ExportHelper

from soulstruct.dcx import DCXType
from soulstruct.darksouls1r.maps import MSB
from soulstruct.darksouls1r.maps.navmesh.mcg import MCG, MCGNode, MCGEdge
from soulstruct.darksouls1r.maps.navmesh.mcp import MCP
from soulstruct.games import DARK_SOULS_DSR

from io_soulstruct.utilities import *
from .utilities import MCGExportError


class ExportMCG(LoggingOperator, ExportHelper):
    """Export MCG from a Blender object containing a Nodes parent and an Edges parent.

    Can optionally use MSB and NVMBND to auto-generate MCP file as well, as MCP connectivity is inferred from MCG nodes.
    """
    bl_idname = "export_scene.mcg"
    bl_label = "Export MCG"
    bl_description = "Export Blender lists of nodes/edges to an MCG graph file"

    filename_ext = ".mcg"

    filter_glob: StringProperty(
        default="*.mcg;*.mcg.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    dcx_type: get_dcx_enum_property(DCXType.Null)  # no compression in DS1

    auto_generate_mcp: BoolProperty(
        name="Auto-generate MCP",
        description="Auto-generate MCP file from new MCG and existing MSB and NVMBND",
        default=True,
    )

    custom_msb_path: StringProperty(
        name="Custom MSB Path",
        description="Custom MSB path to use for MCG export and auto-generated MCP. Leave blank to auto-find",
        default="",
    )

    custom_nvmbnd_path: StringProperty(
        name="Custom NVMBND Path",
        description="Custom NVMBND path to use for auto-generated MCP. Leave blank to auto-find",
        default="",
    )

    @classmethod
    def poll(cls, context):
        """Requires a single selected Empty object with 'Edges' and 'Nodes children."""
        if len(context.selected_objects) != 1:
            return False
        obj = context.selected_objects[0]
        if obj.type != "EMPTY":
            return False
        if len(obj.children) != 2:
            return False
        if "Edges" in obj.children[0].name and "Nodes" in obj.children[1].name:
            return True
        if "Nodes" in obj.children[0].name and "Edges" in obj.children[1].name:
            return True
        return False

    def invoke(self, context, _event):
        """Set default export name to name of object (before first space and without Blender dupe suffix)."""
        if not context.selected_objects:
            return super().invoke(context, _event)

        obj = context.selected_objects[0]
        self.filepath = obj.name.split(" ")[0].split(".")[0] + ".mcg"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        selected_objs = [obj for obj in context.selected_objects]
        if not selected_objs:
            return self.error("No Empty with Edges and Nodes child Empties selected for MCG export.")
        if len(selected_objs) > 1:
            return self.error("More than one object cannot be selected for MCG export.")

        mcg_path = Path(self.filepath)
        if not (match := MAP_STEM_RE.match(mcg_path.stem)):
            raise ValueError(f"Could not infer map ID from stem of MCG path: {mcg_path}")
        map_id = (int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4)))

        node_parent = edge_parent = None
        for child in selected_objs[0].children:
            if "Nodes" in child.name:
                node_parent = child
            elif "Edges" in child.name:
                edge_parent = child
        if not node_parent or not edge_parent:
            return self.error("Selected object must have 'Nodes' and 'Edges' child Empties.")

        exporter = MCGExporter(self, context)

        if not self.custom_msb_path:
            msb_path = mcg_path.parent.parent / "MapStudio" / f"{mcg_path.name.split('.')[0]}.msb"
        else:
            msb_path = Path(self.custom_msb_path)
        if not msb_path.is_file():
            return self.error(f"Could not find MSB file '{msb_path}'.")
        try:
            msb = MSB.from_path(msb_path)
        except Exception as ex:
            return self.error(f"Could not load MSB file '{msb_path}'. Error: {ex}")

        navmesh_part_indices = {navmesh.name: i for i, navmesh in enumerate(msb.navmeshes)}

        bl_nodes = [obj for obj in node_parent.children]
        bl_nodes.sort(key=lambda obj: natural_keys(obj.name))
        bl_edges = [obj for obj in edge_parent.children]
        bl_edges.sort(key=lambda obj: natural_keys(obj.name))

        try:
            mcg = exporter.export_mcg(bl_nodes, bl_edges, navmesh_part_indices, map_id)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported MCG. Error: {ex}")
        else:
            mcg.dcx_type = DCXType[self.dcx_type]

        try:
            # Will create a `.bak` file automatically if absent.
            mcg.write(mcg_path)
            self.info(f"Wrote MCG file successfully: {mcg_path.name}")
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write exported MCG. Error: {ex}")

        if self.auto_generate_mcp:
            # Any error here will not affect MCG write (already done above).
            if not self.custom_nvmbnd_path:
                nvmbnd_path = mcg_path.parent / f"{mcg_path.name.split('.')[0]}.nvmbnd.dcx"
            else:
                nvmbnd_path = Path(self.custom_nvmbnd_path)
            try:
                mcp_path = mcg_path.with_name(mcg_path.name.replace(".mcg", ".mcp"))
                mcp = MCP.from_msb_mcg_nvm_paths(mcp_path, msb_path, mcg_path, nvmbnd_path)
                mcp.write(mcp_path)
            except Exception as ex:
                traceback.print_exc()
                self.warning(f"Error occurred when attempting to auto-generate MCP. Error: {ex}")
            else:
                self.info(f"Wrote MCP file successfully: {mcp_path.name}")

        return {"FINISHED"}


class ExportMCGMCPToMap(LoggingOperator):
    """Export MCG from a Blender object containing a Nodes parent and an Edges parent, and regenerate MCP.

    Can optionally use MSB and NVMBND to auto-generate MCP file as well, as MCP connectivity is inferred from MCG nodes.
    """
    bl_idname = "export_scene.map_mcg_mcp"
    bl_label = "Export MCG + MCP to Map"
    bl_description = "Export Blender lists of nodes/edges to MCG graph file and refresh MCP file in selected game map"

    # This setting is exposed in the GUI panel.
    detect_map_from_parent: bpy.props.BoolProperty(
        name="Detect Map from Parent",
        description="Use the map stem from the selected MCG to detect the map to export to, rather than map settings",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        """Requires a single selected Empty object with 'Edges' and 'Nodes children.
        
        Also requires `SoulstructSettings` game.
        """
        settings = cls.settings(context)
        if not settings.can_auto_export:
            return False
        if not settings.is_game(DARK_SOULS_DSR):
            return False
        if len(context.selected_objects) != 1:
            return False
        obj = context.selected_objects[0]
        if obj.type != "EMPTY":
            return False
        if len(obj.children) != 2:
            return False
        if "Edges" in obj.children[0].name and "Nodes" in obj.children[1].name:
            return True
        if "Nodes" in obj.children[0].name and "Edges" in obj.children[1].name:
            return True
        return False

    def execute(self, context):
        selected_objs = [obj for obj in context.selected_objects]
        if not selected_objs:
            return self.error("No Empty with Edges and Nodes child Empties selected for MCG export.")
        if len(selected_objs) > 1:
            return self.error("More than one object cannot be selected for MCG export.")

        mcg_parent = selected_objs[0]

        settings = self.settings(context)
        if self.detect_map_from_parent:
            map_stem = mcg_parent.name.split(" ")[0]
        elif settings.map_stem:
            map_stem = settings.map_stem
        else:
            return self.error("No map stem specified in settings.")
        if not (match := MAP_STEM_RE.match(map_stem)):
            raise ValueError(f"Invalid map stem: {map_stem}")
        map_id = (int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4)))

        relative_mcg_path = Path(f"map/{map_stem}/{map_stem}.mcg")  # no DCX
        # We prefer to read the MSB and NVMBND in the project directory if they exist. We do not prepare/copy them to
        # the project because they are not modified and the user may not want to include them in a mod package.
        msb_path = settings.get_project_msb_path(map_stem)
        if not is_path_and_file(msb_path):
            msb_path = settings.get_game_msb_path(map_stem)
        if not is_path_and_file(msb_path):
            return self.error(
                f"Could not find MSB file required for MCG export for map {map_stem} in project or game directory."
            )
        nvmbnd_path = settings.get_project_path(f"map/{map_stem}/{map_stem}.nvmbnd")
        if not is_path_and_file(nvmbnd_path):
            nvmbnd_path = settings.get_game_path(f"map/{map_stem}/{map_stem}.nvmbnd")
        if not is_path_and_file(nvmbnd_path):
            return self.error(
                f"Could not find NVMBND binder required for MCG export for map {map_stem} in project or game directory."
            )
        
        node_parent = edge_parent = None
        for child in mcg_parent.children:
            if "Nodes" in child.name:
                node_parent = child
            elif "Edges" in child.name:
                edge_parent = child
        if not node_parent or not edge_parent:
            return self.error("Selected object must have 'Nodes' and 'Edges' child Empties.")

        exporter = MCGExporter(self, context)
        
        try:
            msb = MSB.from_path(msb_path)
        except Exception as ex:
            return self.error(f"Could not load MSB file '{msb_path}'. Error: {ex}")

        navmesh_part_indices = {navmesh.name: i for i, navmesh in enumerate(msb.navmeshes)}

        bl_nodes = [obj for obj in node_parent.children]
        bl_nodes.sort(key=lambda obj: natural_keys(obj.name))
        bl_edges = [obj for obj in edge_parent.children]
        bl_edges.sort(key=lambda obj: natural_keys(obj.name))

        try:
            mcg = exporter.export_mcg(bl_nodes, bl_edges, navmesh_part_indices, map_id)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported MCG. Error: {ex}")
        else:
            mcg.dcx_type = DCXType.Null

        mcg_result = settings.export_file(self, mcg, relative_mcg_path)
        if mcg_result == {"CANCELLED"}:
            # MCG export failed. Don't bother trying to write MCP.
            return mcg_result

        # Any error here will not affect MCG write (already done above).

        # This will be the MCG path just exported.
        mcg_path = settings.get_project_path(relative_mcg_path)
        if not is_path_and_file(mcg_path) and settings.also_export_to_game:
            mcg_path = settings.get_game_path(relative_mcg_path)
        if not is_path_and_file(mcg_path):
            self.warning(f"Could not find MCG file just exported: {mcg_path}. MCP not auto-generated.")
            return {"FINISHED"}

        try:
            relative_mcp_path = Path(f"map/{map_stem}/{map_stem}.mcp")
            mcp = MCP.from_msb_mcg_nvm_paths(relative_mcp_path, msb_path, mcg_path, nvmbnd_path)
            settings.export_file(self, mcp, relative_mcp_path)
        except Exception as ex:
            traceback.print_exc()
            self.warning(f"Error occurred when attempting to auto-generate MCP, but MCG still written. Error: {ex}")

        return {"FINISHED"}


class MCGExporter:

    operator: LoggingOperator

    def __init__(self, operator: LoggingOperator, context):
        self.operator = operator
        self.context = context

    def warning(self, msg: str):
        self.operator.report({"WARNING"}, msg)
        print(f"# WARNING: {msg}")

    def export_mcg(
        self,
        bl_nodes: list[bpy.types.Object],
        bl_edges: list[bpy.types.Object],
        navmesh_part_indices: dict[str, int],
        map_id: tuple[int, int, int, int],
    ) -> MCG:
        """Create MCG from Blender nodes and edges.

        `bl_nodes` and `bl_edges` are assumed to be correctly ordered for MCG indexing. This should generally match the
        order they appear in Blender.

        Requires a dictionary mapping navmesh part names to indices (from MSB) for export, and a `map_id` for edges.
        """

        # Iterate over all nodes to build a dictionary of Nodes that ignores 'dead end' navmesh suffixes.
        node_dict = {}
        map_stem = f"m{map_id[0]:02d}_{map_id[1]:02d}_{map_id[2]:02d}_{map_id[3]:02d}"
        node_prefix = f"{map_stem} Node "
        for i, bl_node in enumerate(bl_nodes):
            if bl_node.name.startswith(node_prefix):
                node_name = bl_node.name.split("<")[0].strip()  # ignore dead end suffix
                node_dict[node_name] = i
            else:
                raise MCGExportError(f"Node '{bl_node.name}' does not start with '{node_prefix}'.")

        # List of all created nodes in the order they will be written in the file.
        nodes = []  # type: list[MCGNode]

        # List of dicts that map EXACTLY two navmesh names to triangles for edges to write (as Soulstruct stores the
        # triangle indices on the nodes rather than the edges).
        node_navmesh_triangles = []  # type: list[dict[str, list[int]]]
        for bl_node in bl_nodes:
            node = MCGNode(
                translate=BL_TO_GAME_VECTOR3(bl_node.location),
                unknown_offset=get_bl_prop(bl_node, "Unk Offset", int, default=0),
            )

            # Check dead end navmesh. Property is optional; absent implies no dead end, so both Navmesh A and Navmesh B
            # must be defined below. Otherwise, if a dead end navmesh is given, only Navmesh A must be defined.
            if dead_end_navmesh_name := get_bl_prop(bl_node, "Dead End Navmesh Name", str, default=""):
                try:
                    node.dead_end_navmesh_index = navmesh_part_indices[dead_end_navmesh_name]
                except KeyError:
                    raise MCGExportError(
                        f"Cannot find '{bl_node.name}' dead end navmesh: {dead_end_navmesh_name}"
                    )
            else:
                node.dead_end_navmesh_index = -1

            node_navmesh_info = {}

            # Get navmesh A (must ALWAYS be present).
            navmesh_a_name = get_bl_prop(bl_node, f"Navmesh A Name", str)
            navmesh_a_triangles = get_bl_prop(bl_node, f"Navmesh A Triangles", tuple, callback=list)
            node_navmesh_info[navmesh_a_name] = navmesh_a_triangles

            # Get navmesh B (if node doesn't have a dead end navmesh).
            if not dead_end_navmesh_name:
                navmesh_b_name = get_bl_prop(bl_node, f"Navmesh B Name", str)
                navmesh_b_triangles = get_bl_prop(bl_node, f"Navmesh B Triangles", tuple, callback=list)
                node_navmesh_info[navmesh_b_name] = navmesh_b_triangles
            elif get_bl_prop(bl_node, f"Navmesh B Name", str, default=""):
                raise MCGExportError(
                    f"Node '{bl_node.name}' has a Dead End Navmesh but also specifies a Navmesh B name."
                )

            nodes.append(node)
            node_navmesh_triangles.append(node_navmesh_info)

        self.operator.info(f"Exporting {len(nodes)} MCG nodes...")

        edges = []
        for i, bl_edge in enumerate(bl_edges):
            edge = MCGEdge(
                map_id=map_id,
                cost=get_bl_prop(bl_edge, "Cost", float),
            )
            navmesh_name = get_bl_prop(bl_edge, "Navmesh Name", str)
            try:
                navmesh_index = navmesh_part_indices[navmesh_name]
            except KeyError:
                raise MCGExportError(f"Cannot find '{bl_edge.name}' navmesh: {navmesh_name}")
            edge.navmesh_index = navmesh_index

            node_a_name = get_bl_prop(bl_edge, "Node A", str)
            if node_a_name.startswith("Node"):
                node_a_name = f"{map_stem} {node_a_name}"
            node_b_name = get_bl_prop(bl_edge, "Node B", str)
            if node_b_name.startswith("Node"):
                node_b_name = f"{map_stem} {node_b_name}"
            try:
                node_a_index = node_dict[node_a_name]
            except KeyError:
                raise MCGExportError(f"Cannot find '{bl_edge.name}' start node: '{node_a_name}'")
            try:
                node_b_index = node_dict[node_b_name]
            except KeyError:
                raise MCGExportError(f"Cannot find '{bl_edge.name}' end node: '{node_b_name}'")

            node_a = nodes[node_a_index]
            node_b = nodes[node_b_index]
            edge.node_a = node_a
            edge.node_b = node_b
            node_a.connected_nodes.append(node_b)
            node_a.connected_edges.append(edge)
            node_b.connected_nodes.append(node_a)
            node_b.connected_edges.append(edge)

            try:
                edge.node_a_triangles = node_navmesh_triangles[node_a_index][navmesh_name]
            except KeyError:
                raise MCGExportError(
                    f"Node {node_a_name} does not specify triangles for navmesh {navmesh_name} (edge {bl_edge.name}). "
                    "You must fix your navmeshes and navmesh graph in Blender first."
                )
            try:
                edge.node_b_triangles = node_navmesh_triangles[node_b_index][navmesh_name]
            except KeyError:
                raise MCGExportError(
                    f"Node {node_b_name} does not specify triangles for navmesh {navmesh_name} (edge {bl_edge.name}). "
                    "You must fix your navmeshes and navmesh graph in Blender first."
                )

            edges.append(edge)

        self.operator.info(f"Exporting {len(edges)} MCG edges...")

        mcg = MCG(nodes=nodes, edges=edges, unknowns=(0, 0, 0))

        return mcg
