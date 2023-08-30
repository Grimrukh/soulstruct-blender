from __future__ import annotations

__all__ = ["ExportMCG"]

import traceback
from pathlib import Path

from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ExportHelper

from soulstruct.containers import DCXType
from soulstruct.darksouls1r.maps import MSB
from soulstruct.darksouls1r.maps.navmesh.mcg import MCG, GateNode, GateEdge
from soulstruct.darksouls1r.maps.navmesh.mcp import MCP

from io_soulstruct.utilities import *
from .utilities import MCGExportError


DEBUG_MESH_INDEX = None
DEBUG_VERTEX_INDICES = []


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
            self.info(f"Wrote MCG successfully: {mcg_path.name}")
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write exported MCG. Error: {ex}")

        if self.auto_generate_mcp:
            # Any error here will not affect MCG write (already done above).
            self.write_mcp(msb_path, mcg_path)

        return {"FINISHED"}

    def write_mcp(self, msb_path: Path, mcg_path: Path):
        if not self.custom_nvmbnd_path:
            nvmbnd_path = mcg_path.parent / f"{mcg_path.name.split('.')[0]}.nvmbnd.dcx"
        else:
            nvmbnd_path = Path(self.custom_nvmbnd_path)
        if not nvmbnd_path.is_file():
            self.warning(f"Could not find NVMBND file '{nvmbnd_path}'. MCP file not auto-generated.")
        mcp_path = mcg_path.parent / f"{mcg_path.name.split('.')[0]}.mcp"
        try:
            mcp = MCP.from_msb_mcg_nvm_paths(mcp_path, msb_path, mcg_path, nvmbnd_path)
        except Exception as ex:
            traceback.print_exc()
            self.warning(f"Error occurred when attempting to auto-generate MCP. Error: {ex}")
        else:
            try:
                # Will create a `.bak` file automatically if absent.
                mcp.write(mcp_path)
                self.info(f"Wrote MCP successfully: {mcp_path.name}")
            except Exception as ex:
                traceback.print_exc()
                self.warning(f"Cannot write auto-generated MCP. Error: {ex}")


class MCGExporter:

    operator: LoggingOperator

    def __init__(self, operator: LoggingOperator, context):
        self.operator = operator
        self.context = context

        self.props = BlenderPropertyManager({
            "GateNode": {
                "dead_end_navmesh_name": BlenderProp(str, do_not_assign=True),
                "unknown_offset": BlenderProp(int, 0),
            },
            "GateEdge": {
                "cost": BlenderProp(float),
                "end_node_triangle_indices": BlenderProp(tuple, callback=list),
                "end_node_name": BlenderProp(str, do_not_assign=True),
                "navmesh_name": BlenderProp(str, do_not_assign=True),
                "start_node_triangle_indices": BlenderProp(tuple, callback=list),
                "start_node_name": BlenderProp(str, do_not_assign=True),
            },
        })

    def warning(self, msg: str):
        self.operator.report({"WARNING"}, msg)
        print(f"# WARNING: {msg}")

    def export_mcg(
        self,
        bl_nodes,
        bl_edges,
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
        node_prefix = f"m{map_id[0]:02d}_{map_id[1]:02d}_{map_id[2]:02d}_{map_id[3]:02d} Node "
        for i, bl_node in enumerate(bl_nodes):
            if bl_node.name.startswith(node_prefix):
                node_name = bl_node.name.removeprefix(node_prefix).split("<")[0].strip()  # ignore dead end suffix
                node_dict[f"Node {node_name}"] = i
            else:
                raise MCGExportError(f"Node '{bl_node.name}' does not start with '{node_prefix}'.")

        nodes = []
        for bl_node in bl_nodes:
            node = GateNode(translate=BL_TO_GAME_VECTOR3(bl_node.location))
            node_extra = self.props.get_all(bl_node, node, "GateNode")
            if node_extra["dead_end_navmesh_name"]:
                try:
                    node._dead_end_navmesh_index = navmesh_part_indices[node_extra["dead_end_navmesh_name"]]
                except KeyError:
                    raise MCGExportError(
                        f"Cannot find '{bl_node.name}' dead end navmesh: {node_extra['dead_end_navmesh_name']}"
                    )
            else:
                node._dead_end_navmesh_index = -1
            nodes.append(node)

        self.operator.info(f"Exporting {len(nodes)} MCG nodes...")

        edges = []
        for i, bl_edge in enumerate(bl_edges):
            edge = GateEdge(map_id=map_id)
            edge_extra = self.props.get_all(bl_edge, edge, "GateEdge")
            try:
                navmesh_index = navmesh_part_indices[edge_extra["navmesh_name"]]
            except KeyError:
                raise MCGExportError(f"Cannot find '{bl_edge.name}' navmesh: {edge_extra['navmesh_name']}")
            edge._navmesh_part_index = navmesh_index

            try:
                start_node_index = node_dict[edge_extra["start_node_name"]]
            except KeyError:
                raise MCGExportError(f"Cannot find '{bl_edge.name}' start node: {edge_extra['start_node_name']}")
            try:
                end_node_index = node_dict[edge_extra["end_node_name"]]
            except KeyError:
                raise MCGExportError(f"Cannot find '{bl_edge.name}' end node: {edge_extra['end_node_name']}")

            start_node = nodes[start_node_index]
            end_node = nodes[end_node_index]
            edge.start_node = start_node
            edge.end_node = end_node
            start_node.connected_nodes.append(end_node)
            start_node.connected_edges.append(edge)
            end_node.connected_nodes.append(start_node)
            end_node.connected_edges.append(edge)

            edges.append(edge)

        self.operator.info(f"Exporting {len(edges)} MCG edges...")

        mcg = MCG(nodes=nodes, edges=edges, unknowns=(0, 0, 0))

        return mcg
