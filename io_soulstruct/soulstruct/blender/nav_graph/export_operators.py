from __future__ import annotations

__all__ = ["ExportAnyMCGMCP", "ExportMapMCGMCP"]

import traceback
from pathlib import Path

import bpy

from soulstruct.base.maps.navmesh.mcp import MCP
from soulstruct.dcx import DCXType

from soulstruct.blender.exceptions import SoulstructTypeError
from soulstruct.blender.utilities import *
from .types import BlenderMCG


class ExportAnyMCGMCP(LoggingExportOperator):
    """Export MCG from a Blender object containing a Nodes parent and an Edges parent.

    Can optionally use MSB and NVMBND to auto-generate MCP file as well, as MCP connectivity is inferred from MCG nodes.
    """
    bl_idname = "export_scene.mcg"
    bl_label = "Export Any MCG/MCP"
    bl_description = "Export Blender lists of nodes/edges to an MCG graph file and optional additional MCP file"

    filename_ext = ".mcg"

    filter_glob: bpy.props.StringProperty(
        default="*.mcg;*.mcg.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    dcx_type: get_dcx_enum_property(DCXType.Null)  # no compression in DS1

    auto_generate_mcp: bpy.props.BoolProperty(
        name="Auto-generate MCP",
        description="Auto-generate MCP file from new MCG and existing MSB and NVMBND",
        default=True,
    )

    custom_msb_path: bpy.props.StringProperty(
        name="Custom MSB Path",
        description="Custom MSB path to use for MCG export and auto-generated MCP. Leave blank to auto-find",
        default="",
    )

    custom_nvmbnd_path: bpy.props.StringProperty(
        name="Custom NVMBND Path",
        description="Custom NVMBND path to use for auto-generated MCP. Leave blank to auto-find",
        default="",
    )

    @classmethod
    def poll(cls, context) -> bool:
        """Requires a single selected Empty object with 'Edges' and 'Nodes children."""
        if len(context.selected_objects) != 1:
            return False
        try:
            BlenderMCG(context.selected_objects[0])
        except SoulstructTypeError:
            return False
        return True

    def invoke(self, context, _event):
        """Set default export name to name of object (before first space and without Blender dupe suffix)."""
        if not context.selected_objects:
            return super().invoke(context, _event)

        obj = BlenderMCG(context.selected_objects[0])
        self.filepath = obj.game_name + ".mcg"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        selected_objs = [obj for obj in context.selected_objects]
        if not selected_objs:
            return self.error("No Empty with Edges and Nodes child Empties selected for MCG export.")
        if len(selected_objs) > 1:
            return self.error("More than one object cannot be selected for MCG export.")

        mcg_path = Path(self.filepath)
        bl_mcg = BlenderMCG(selected_objs[0])

        msb_class = self.settings(context).game_config.msb_class

        if not self.custom_msb_path:
            msb_path = mcg_path.parent.parent / "MapStudio" / f"{mcg_path.name.split('.')[0]}.msb"
        else:
            msb_path = Path(self.custom_msb_path)
        if not msb_path.is_file():
            return self.error(f"Could not find MSB file '{msb_path}'.")
        try:
            msb = msb_class.from_path(msb_path)
        except Exception as ex:
            return self.error(f"Could not load MSB file '{msb_path}'. Error: {ex}")

        navmesh_part_indices = {navmesh.name: i for i, navmesh in enumerate(msb.navmeshes)}

        try:
            mcg = bl_mcg.to_soulstruct_obj(
                self,
                context,
                navmesh_part_indices,
            )
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported MCG. Error: {ex}")
        else:
            mcg.dcx_type = DCXType.from_member_name(self.dcx_type)

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
                mcp = MCP.from_msb_mcg_nvm_paths(msb_class, mcp_path, msb_path, mcg_path, nvmbnd_path)
                mcp.write(mcp_path)
            except Exception as ex:
                traceback.print_exc()
                self.warning(f"Error occurred when attempting to auto-generate MCP. Error: {ex}")
            else:
                self.info(f"Wrote MCP file successfully: {mcp_path.name}")

        return {"FINISHED"}


class ExportMapMCGMCP(LoggingOperator):
    """Export MCG from a Blender object containing a Nodes parent and an Edges parent, and regenerate MCP.

    Can optionally use MSB and NVMBND to auto-generate MCP file as well, as MCP connectivity is inferred from MCG nodes.
    """
    bl_idname = "export_scene.map_mcg_mcp"
    bl_label = "Export Map MCG/MCP"
    bl_description = "Export Blender lists of nodes/edges to MCG graph file and refresh MCP file in selected game map"

    auto_generate_mcp: bpy.props.BoolProperty(
        name="Auto-generate MCP",
        description="Auto-generate MCP file from new MCG and existing MSB and NVMBND",
        default=True,
    )

    @classmethod
    def poll(cls, context) -> bool:
        """Requires a single selected Empty object with 'Edges' and 'Nodes children.
        
        Also requires `SoulstructSettings` game.
        """
        settings = cls.settings(context)
        if not settings.can_auto_export:
            return False
        if not settings.map_stem:
            return False
        if not settings.game_config.supports_mcg:
            return False
        return BlenderMCG.is_active_obj_type(context)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        settings = self.settings(context)
        bl_mcg = BlenderMCG.from_active_object(context)

        if settings.auto_detect_export_map:
            map_stem = bl_mcg.name.split(" ")[0]
        else:
            map_stem = settings.map_stem  # validated in `poll()`

        if not MAP_STEM_RE.match(map_stem):
            raise ValueError(f"Invalid map stem: {map_stem}")

        relative_mcg_path = Path(f"map/{map_stem}/{map_stem}.mcg")  # no DCX

        # We prefer to read the MSB and NVMBND in the project directory if they exist. We do not prepare/copy them to
        # the project because they are not modified and the user may not want to include them in a mod package.
        import_roots = [settings.project_root, settings.game_root]
        msb_path = settings.get_first_existing_msb_path(import_roots, map_stem=map_stem)
        if not msb_path:
            return self.error(
                f"Could not find MSB file required for MCG export for map {map_stem} in project or game directory."
            )
        nvmbnd_path = settings.get_first_existing_map_file_path(
            f"{map_stem}.nvmbnd", roots=import_roots, map_stem=map_stem
        )
        if not nvmbnd_path:
            return self.error(
                f"Could not find NVMBND binder required for MCG export for map {map_stem} in project or game directory."
            )

        msb_class = settings.game_config.msb_class

        try:
            msb = msb_class.from_path(msb_path)
        except Exception as ex:
            return self.error(f"Could not load MSB file '{msb_path}'. Error: {ex}")

        navmesh_part_indices = {navmesh.name: i for i, navmesh in enumerate(msb.navmeshes)}

        try:
            mcg = bl_mcg.to_soulstruct_obj(
                self,
                context,
                navmesh_part_indices,
            )
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported MCG. Error: {ex}")
        else:
            mcg.dcx_type = DCXType.Null

        exported_paths = settings.export_file(self, mcg, relative_mcg_path)
        if not exported_paths:
            # MCG export failed. Don't bother trying to write MCP.
            return self.error("MCG export failed. No files written.")

        # Any error here will not affect MCG write (already done above).

        # This will be the MCG path just exported.
        export_roots = [settings.project_root]
        if settings.also_export_to_game:
            export_roots += [settings.game_root]
        mcg_path = settings.get_first_existing_file_path(relative_mcg_path, roots=export_roots)
        if not mcg_path:
            self.warning(f"Could not find MCG file just exported: {mcg_path}. MCP not auto-generated.")
            return {"FINISHED"}

        try:
            relative_mcp_path = Path(f"map/{map_stem}/{map_stem}.mcp")
            mcp = MCP.from_msb_mcg_nvm_paths(msb_class, relative_mcp_path, msb_path, mcg_path, nvmbnd_path)
            settings.export_file(self, mcp, relative_mcp_path)
        except Exception as ex:
            traceback.print_exc()
            self.warning(f"Error occurred when attempting to auto-generate MCP, but MCG still written. Error: {ex}")

        return {"FINISHED"}
