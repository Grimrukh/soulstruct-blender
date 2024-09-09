from __future__ import annotations

__all__ = [
    "MCGPropsPanel",
    "OBJECT_UL_nav_triangle",
    "MCGNodePropsPanel",
    "MCGEdgePropsPanel",
    "MCGImportExportPanel",
    "MCGDrawPanel",
    "MCGToolsPanel",
    "MCGGeneratorPanel",
]

import typing as tp

import bpy
from io_soulstruct.general.gui import map_stem_box
from io_soulstruct.types import SoulstructType
from .import_operators import *
from .export_operators import *
from .misc_operators import *


class MCGPropsPanel(bpy.types.Panel):
    """Draw a Panel in the Object properties window exposing the appropriate MCG fields for active object."""
    bl_label = "MCG Properties"
    bl_idname = "OBJECT_PT_mcg"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if not context.active_object:
            return False
        return context.active_object.soulstruct_type == SoulstructType.MCG

    def draw(self, context):
        bl_node = context.active_object
        props = bl_node.MCG
        for prop in props.__annotations__:
            self.layout.prop(props, prop)


class OBJECT_UL_nav_triangle(bpy.types.UIList):
    """Draws a list of items."""
    PROP_NAME: tp.ClassVar[str] = "index"

    def draw_item(
        self,
        context,
        layout,
        data,
        item,
        icon,
        active_data,
        active_property,
        index=0,
        flt_flag=0,
    ):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.label(text=f"Triangle {index}:")
            row.prop(item, self.PROP_NAME, text="", emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text=f"Triangle {index}:")
            layout.prop(item, self.PROP_NAME, text="", emboss=False)


class MCGNodePropsPanel(bpy.types.Panel):
    """Draw a Panel in the Object properties window exposing the appropriate MCG_NODE fields for active object."""
    bl_label = "MCG Node Properties"
    bl_idname = "OBJECT_PT_mcg_node"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if not context.active_object:
            return False
        return context.active_object.soulstruct_type == SoulstructType.MCG_NODE

    def draw(self, context):
        layout = self.layout
        bl_node = context.active_object
        props = bl_node.MCG_NODE

        layout.prop(props, "unknown_offset")
        layout.prop(props, "navmesh_a")
        layout.prop(props, "navmesh_b")

        layout.label(text="Navmesh A Triangles:")
        row = layout.row()
        row.template_list(
            listtype_name=OBJECT_UL_nav_triangle.__name__,
            list_id="",
            dataptr=bl_node.MCG_NODE,
            propname="navmesh_a_triangles",
            active_dataptr=bl_node.MCG_NODE,
            active_propname="navmesh_a_triangle_index",
        )
        col = row.column(align=True)
        col.operator(AddMCGNodeNavmeshATriangleIndex.bl_idname, icon='ADD', text="")
        col.operator(RemoveMCGNodeNavmeshATriangleIndex.bl_idname, icon='REMOVE', text="")

        layout.label(text="Navmesh B Triangles:")
        row = layout.row()
        row.template_list(
            listtype_name=OBJECT_UL_nav_triangle.__name__,
            list_id="",
            dataptr=bl_node.MCG_NODE,
            propname="navmesh_b_triangles",
            active_dataptr=bl_node.MCG_NODE,
            active_propname="navmesh_b_triangle_index",
        )
        col = row.column(align=True)
        col.operator(AddMCGNodeNavmeshBTriangleIndex.bl_idname, icon='ADD', text="")
        col.operator(RemoveMCGNodeNavmeshBTriangleIndex.bl_idname, icon='REMOVE', text="")


class MCGEdgePropsPanel(bpy.types.Panel):
    """Draw a Panel in the Object properties window exposing the appropriate MCG_EDGE fields for active object."""
    bl_label = "MCG Edge Properties"
    bl_idname = "OBJECT_PT_mcg_edge"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if not context.active_object:
            return False
        return context.active_object.soulstruct_type == SoulstructType.MCG_EDGE

    def draw(self, context):
        bl_edge = context.active_object
        props = bl_edge.MCG_EDGE
        for prop in props.__annotations__:
            self.layout.prop(props, prop)


class MCGImportExportPanel(bpy.types.Panel):
    bl_label = "MCG Import/Export"
    bl_idname = "MCG_PT_mcg_import_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NavGraph (MCG)"
    bl_options = {"DEFAULT_CLOSED"}

    # noinspection PyUnusedLocal
    def draw(self, context):
        settings = context.scene.soulstruct_settings

        if not settings.is_game("DARK_SOULS_DSR"):
            self.layout.label(text="NavGraph (MCG) supported for DSR only.")
            return

        layout = self.layout
        map_stem_box(layout, settings)
        header, panel = layout.panel("Import", default_closed=False)
        header.label(text="Import")
        if panel:
            if settings.map_stem:
                panel.label(text=f"From {settings.map_stem}:")
                panel.operator(ImportSelectedMapMCG.bl_idname)
                panel.operator(ImportSelectedMapMCP.bl_idname)
            else:
                panel.label(text="No game map selected.")
            panel.operator(ImportMCG.bl_idname, text="Import Any MCG")
            panel.operator(ImportMCP.bl_idname, text="Import Any MCP")

        header, panel = layout.panel("Export", default_closed=False)
        header.label(text="Export")
        if panel:
            panel.label(text="Export to Game/Project:")
            panel.prop(
                context.window_manager.operator_properties_last(ExportMCGMCPToMap.bl_idname), "detect_map_from_parent"
            )
            panel.operator(ExportMCGMCPToMap.bl_idname)
            panel.label(text="Generic Export:")
            panel.operator(ExportMCG.bl_idname, text="Export MCG + MCP")


class MCGDrawPanel(bpy.types.Panel):
    bl_label = "MCG Drawing"
    bl_idname = "MCG_PT_mcg_draw"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NavGraph (MCG)"
    bl_options = {"DEFAULT_CLOSED"}

    # noinspection PyUnusedLocal
    def draw(self, context):
        """Still shown if game is not DSR."""
        layout = self.layout
        mcg_draw_settings = context.scene.mcg_draw_settings

        layout.label(text="MCG Parent Object:")
        layout.prop(mcg_draw_settings, "mcg_parent", text="")
        layout.prop(mcg_draw_settings, "draw_graph")
        drawn = {
            "mcg_parent",
            "draw_graph",
            "edge_label_font_color",
            "close_cost_edge_label_font_color",
            "different_cost_edge_label_font_color",
        }

        header, panel = layout.panel("Detailed Settings", default_closed=False)
        header.label(text="Detailed Settings")
        if panel:
            for prop_name in mcg_draw_settings.__annotations__:
                if prop_name in drawn:
                    continue
                layout.prop(mcg_draw_settings, prop_name)

        layout.label(text="Edge Cost Label Colors:")
        row = layout.row()
        for label, prop_name in [
            ("Match", "edge_label_font_color"),
            ("Almost", "close_cost_edge_label_font_color"),
            ("Bad", "different_cost_edge_label_font_color"),
        ]:
            column = row.column()
            column.label(text=label)
            column.prop(mcg_draw_settings, prop_name, text="")


class MCGToolsPanel(bpy.types.Panel):
    bl_label = "MCG Tools"
    bl_idname = "MCG_PT_navmesh_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NavGraph (MCG)"
    bl_options = {"DEFAULT_CLOSED"}

    # noinspection PyUnusedLocal
    def draw(self, context):
        """Still shown if game is not DSR."""
        layout = self.layout
        layout.operator(JoinMCGNodesThroughNavmesh.bl_idname)
        layout.operator(SetNodeNavmeshTriangles.bl_idname)
        layout.operator(RefreshMCGNames.bl_idname)


class MCGGeneratorPanel(bpy.types.Panel):
    bl_label = "MCG Generator"
    bl_idname = "MCG_PT_navmesh_generator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NavGraph (MCG)"
    bl_options = {"DEFAULT_CLOSED"}

    # noinspection PyUnusedLocal
    def draw(self, context):
        """Still shown if game is not DSR."""
        layout = self.layout

        header, panel = layout.panel("Settings", default_closed=False)
        header.label(text="Settings")
        if panel:
            nav_graph_compute_settings = context.scene.nav_graph_compute_settings
            panel.prop(nav_graph_compute_settings, "select_path")
            panel.prop(nav_graph_compute_settings, "wall_multiplier")
            panel.prop(nav_graph_compute_settings, "obstacle_multiplier")

        layout.operator(RecomputeEdgeCost.bl_idname)
        layout.operator(FindCheapestPath.bl_idname)
        layout.label(text="Complete MCG Generation:")
        layout.operator(AutoCreateMCG.bl_idname)
