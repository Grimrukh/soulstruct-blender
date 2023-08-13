"""
Import MCP/MCG files (with/without DCX) into Blender 3.3+ (Python 3.10+ scripting required).

MCP files contain AABBs that match up to Navmesh part instances in the map's MSB.

MCG files contain gate nodes and edges connecting them. Gate nodes lie on the boundaries between navmesh parts and edges
cross through a particular navmesh to connect two gate nodes.

This file format is only used in DeS and DS1 (PTDE/DSR).
"""
from __future__ import annotations

__all__ = ["ImportMCP", "ImportMCG"]

import re
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper

from soulstruct.darksouls1r.maps.navmesh import MCP, MCG, NavmeshAABB, GateNode, GateEdge

from io_soulstruct.utilities import *
from .utilities import hsv_color


MCP_NAME_RE = re.compile(r".*\.mcp(\.dcx)?")
MCG_NAME_RE = re.compile(r".*\.mcg(\.dcx)?")
MAP_NAME_RE = re.compile(r"^(m\d\d)_\d\d_\d\d_\d\d$")


class ImportMCP(LoggingOperator, ImportHelper):
    bl_idname = "import_scene.mcp"
    bl_label = "Import MCP"
    bl_description = "Import an MCP navmesh AABB file. Supports DCX-compressed files"

    filename_ext = ".mcp"

    filter_glob: bpy.props.StringProperty(
        default="*.mcp;*.mcp.dcx",
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

    def execute(self, context):
        print("Executing MCP import...")

        file_paths = [Path(self.directory, file.name) for file in self.files]

        mcps = []
        for file_path in file_paths:
            try:
                mcp = MCP.from_path(file_path)
            except Exception as ex:
                self.warning(f"Error occurred while reading MCP file '{file_path.name}': {ex}")
            else:
                mcps.append(mcp)

        importer = MCPImporter(self, context)
        for i, mcp in enumerate(mcps):
            # TODO: load navmesh part names from MSB (and check same count)
            importer.import_mcp(mcp, f"{file_paths[i].stem} MCP")

        return {'FINISHED'}


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

        importer = MCGImporter(self, context)
        for i, mcg in enumerate(mcgs):
            # TODO: load navmesh part names from MSB (and check same count)
            importer.import_mcg(mcg, f"{file_paths[i].stem} MCG")

        return {'FINISHED'}


class MCPImporter:

    def __init__(
        self,
        operator: ImportMCP,
        context,
    ):
        self.operator = operator
        self.context = context

        self.mcp = None
        self.bl_name = ""
        self.all_bl_objs = []

    def import_mcp(self, mcp: MCP, bl_name: str, navmesh_part_names: list[str] = None) -> bpy.types.Object:
        self.mcp = mcp
        self.bl_name = bl_name
        self.operator.info(f"Importing MCP: {bl_name}")

        # Set mode to OBJECT and deselect all objects.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action="DESELECT")
        if bpy.ops.object.mode_set.poll():  # just to be safe
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        mcp_parent = bpy.data.objects.new(bl_name, None)  # empty parent for all AABB meshes
        self.context.collection.objects.link(mcp_parent)
        self.all_bl_objs.append(mcp_parent)

        for i, aabb in enumerate(mcp.aabbs):
            aabb: NavmeshAABB
            bl_aabb = self.create_aabb(aabb)
            bl_aabb.name = f"AABB {i} ({navmesh_part_names[i]})" if navmesh_part_names else f"AABB {i}"
            bl_aabb.parent = mcp_parent
            self.all_bl_objs.append(bl_aabb)

        return mcp_parent

    @staticmethod
    def create_aabb(aabb: NavmeshAABB):
        """Create an AABB prism representing `aabb`. Position is baked into mesh data fully, just like the navmesh."""
        start_vec = GAME_TO_BL_VECTOR(aabb.aabb_start)
        end_vec = GAME_TO_BL_VECTOR(aabb.aabb_end)
        bpy.ops.mesh.primitive_cube_add()
        bl_box = bpy.context.active_object
        # noinspection PyTypeChecker
        box_data = bl_box.data  # type: bpy.types.Mesh
        for vertex in box_data.vertices:
            vertex.co[0] = start_vec.x if vertex.co[0] == -1.0 else end_vec.x
            vertex.co[1] = start_vec.y if vertex.co[1] == -1.0 else end_vec.y
            vertex.co[2] = start_vec.z if vertex.co[2] == -1.0 else end_vec.z
        bpy.ops.object.modifier_add(type="WIREFRAME")
        bl_box.modifiers[0].thickness = 0.2
        return bl_box


class MCGImporter:

    def __init__(
        self,
        operator: ImportMCP,
        context,
    ):
        self.operator = operator
        self.context = context

        self.mcg = None
        self.bl_name = ""
        self.all_bl_objs = []

    def import_mcg(self, mcg: MCG, bl_name: str, navmesh_part_names: list[str] = None) -> bpy.types.Object:
        self.mcg = mcg
        self.bl_name = bl_name
        self.operator.info(f"Importing MCG: {bl_name}")

        # Set mode to OBJECT and deselect all objects.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action="DESELECT")
        if bpy.ops.object.mode_set.poll():  # just to be safe
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        mcg_parent = bpy.data.objects.new(bl_name, None)  # empty parent for all AABB meshes
        self.context.collection.objects.link(mcg_parent)
        self.all_bl_objs.append(mcg_parent)

        try:
            bl_material = bpy.data.materials["Navmesh MCG"]
        except KeyError:
            # Create new material with green color.
            color = hsv_color(0.333, 0.9, 0.2)
            bl_material = create_basic_material("Navmesh MCG", color)

        for i, node in enumerate(mcg.nodes):
            node: GateNode
            bl_sphere = self.create_node(node)
            bl_sphere.name = f"Node {i}"
            bl_sphere.parent = mcg_parent
            bl_sphere.data.materials.append(bl_material)
            # TODO: other custom properties?
            bl_sphere["unknown_offset"] = node.unknown_offset
            self.all_bl_objs.append(bl_sphere)

        for i, edge in enumerate(mcg.edges):
            edge: GateEdge
            bl_edge = self.create_edge(edge)
            start_node_index = mcg.nodes.index(edge.start_node)
            end_node_index = mcg.nodes.index(edge.end_node)
            bl_edge.name = f"Edge {i} ({start_node_index} -> {end_node_index})"
            bl_edge.parent = mcg_parent
            bl_edge.data.materials.append(bl_material)

            # Custom properties
            bl_edge["start_node_index"] = start_node_index
            bl_edge["start_node_faces"] = edge.start_node_triangle_indices
            bl_edge["end_node_index"] = end_node_index
            bl_edge["end_node_faces"] = edge.end_node_triangle_indices
            bl_edge["navmesh_index"] = edge._navmesh_part_index  # TODO: not deferenced yet
            bl_edge["cost"] = edge.cost

            self.all_bl_objs.append(bl_edge)

        return mcg_parent

    @staticmethod
    def create_node(node: GateNode):
        """Create a sphere representing `node`. Its transform represents its position."""
        position = GAME_TO_BL_VECTOR(node.translate)
        bpy.ops.mesh.primitive_ico_sphere_add(4)
        bl_sphere = bpy.context.active_object
        bl_sphere.location = position
        bpy.ops.object.modifier_add(type="WIREFRAME")
        bl_sphere.modifiers[0].thickness = 0.05
        return bl_sphere

    @staticmethod
    def create_edge(edge: GateEdge):
        """Create a cylinder representing `edge` that connects two nodes."""
        # Calculate the distance and midpoint
        start = GAME_TO_BL_VECTOR(edge.start_node.translate)
        end = GAME_TO_BL_VECTOR(edge.end_node.translate)
        direction = end - start
        midpoint = (start + end) / 2.0

        # Add a cylinder
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.2,
            depth=direction.length,
            location=midpoint,
        )

        bl_cylinder = bpy.context.active_object
        # Rotate the cylinder to point from start to end
        bl_cylinder.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
        # bpy.ops.object.modifier_add(type="WIREFRAME")
        # bl_cylinder.modifiers[0].thickness = 0.03
        return bl_cylinder
