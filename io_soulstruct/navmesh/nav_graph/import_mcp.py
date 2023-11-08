"""
Import MCP files (with/without DCX) into Blender 3.3+ (Python 3.10+ scripting required).

MCP files contain AABBs that match up to Navmesh part instances in the map's MSB.

This file format is only used in DeS and DS1 (PTDE/DSR).
"""
from __future__ import annotations

__all__ = ["ImportMCP", "QuickImportMCP"]

import re
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper

from soulstruct.darksouls1r.maps.navmesh import MCP, NavmeshAABB

from io_soulstruct.general import SoulstructSettings
from io_soulstruct.utilities import *

MCP_NAME_RE = re.compile(r"(?P<stem>.*)\.mcp(?P<dcx>\.dcx)?")


class ImportMCP(LoggingOperator, ImportHelper):
    bl_idname = "import_scene.mcp"
    bl_label = "Import MCP"
    bl_description = "Import an MCP file containing MSB navmesh AABBs and connections. Supports DCX-compressed files"

    filename_ext = ".mcp"

    filter_glob: bpy.props.StringProperty(
        default="*.mcp;*.mcp.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'})

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


class QuickImportMCP(LoggingOperator):
    bl_idname = "import_scene.quick_mcp"
    bl_label = "Import MCP"
    bl_description = "Import MCP file containing MSB navmesh AABBs and connections from selected game map"

    def execute(self, context):

        settings = SoulstructSettings.get_scene_settings(context)
        game_directory = settings.game_directory
        map_stem = settings.map_stem
        if not game_directory or not map_stem:
            return self.error("Game directory or map stem not set in Soulstruct plugin settings.")
        mcp_path = Path(game_directory, "map", map_stem, f"{map_stem}.mcp")
        if not mcp_path.is_file():
            return self.error(f"Could not find MCP file '{mcp_path}'.")

        try:
            mcp = MCP.from_path(mcp_path)
        except Exception as ex:
            return self.error(f"Error occurred while reading MCP file '{mcp_path}': {ex}")

        importer = MCPImporter(self, context)
        # TODO: load navmesh part names from MSB (and check same count)
        importer.import_mcp(mcp, f"{mcp_path.stem} MCP")

        return {'FINISHED'}


class MCPImporter:

    def __init__(
        self,
        operator: LoggingOperator,
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
