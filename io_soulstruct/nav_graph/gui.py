from __future__ import annotations

__all__ = [
    "MCGPropsPanel",
    "NavTriangleUIList",
    "MCGNodePropsPanel",
    "MCGEdgePropsPanel",
    "NavGraphImportExportPanel",
    "NavGraphDrawPanel",
    "NavGraphToolsPanel",
    "MCGGeneratorPanel",
]

import typing as tp

import bpy

from io_soulstruct.bpy_base.panel import SoulstructPanel
from io_soulstruct.types import SoulstructType

from .import_operators import *
from .export_operators import *
from .misc_operators import *


class MCGPropsPanel(SoulstructPanel):
    """Draw a Panel in the Object properties window exposing the appropriate MCG fields for active object."""
    bl_label = "MCG Properties"
    bl_idname = "OBJECT_PT_mcg"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context) -> bool:
        if not context.active_object:
            return False
        return context.active_object.soulstruct_type == SoulstructType.MCG

    def draw(self, context):
        bl_node = context.active_object
        props = bl_node.MCG
        for prop in props.__annotations__:
            self.layout.prop(props, prop)


class NavTriangleUIList(bpy.types.UIList):
    """Draws a list of items."""
    PROP_NAME: tp.ClassVar[str] = "index"

    bl_idname = "OBJECT_UL_nav_triangle"

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


class MCGNodePropsPanel(SoulstructPanel):
    """Draw a Panel in the Object properties window exposing the appropriate MCG_NODE fields for active object."""
    bl_label = "MCG Node Properties"
    bl_idname = "OBJECT_PT_mcg_node"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context) -> bool:
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
            listtype_name=NavTriangleUIList.bl_idname,
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
            listtype_name=NavTriangleUIList.bl_idname,
            list_id="",
            dataptr=bl_node.MCG_NODE,
            propname="navmesh_b_triangles",
            active_dataptr=bl_node.MCG_NODE,
            active_propname="navmesh_b_triangle_index",
        )
        col = row.column(align=True)
        col.operator(AddMCGNodeNavmeshBTriangleIndex.bl_idname, icon='ADD', text="")
        col.operator(RemoveMCGNodeNavmeshBTriangleIndex.bl_idname, icon='REMOVE', text="")


class MCGEdgePropsPanel(SoulstructPanel):
    """Draw a Panel in the Object properties window exposing the appropriate MCG_EDGE fields for active object."""
    bl_label = "MCG Edge Properties"
    bl_idname = "OBJECT_PT_mcg_edge"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context) -> bool:
        if not context.active_object:
            return False
        return context.active_object.soulstruct_type == SoulstructType.MCG_EDGE

    def draw(self, context):
        bl_edge = context.active_object
        props = bl_edge.MCG_EDGE
        for prop in props.__annotations__:
            self.layout.prop(props, prop)


class NavGraphImportExportPanel(SoulstructPanel):
    bl_label = "MCG Import/Export"
    bl_idname = "MCG_PT_mcg_import_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NavGraph (MCG)"
    bl_options = {"DEFAULT_CLOSED"}

    # noinspection PyUnusedLocal
    def draw(self, context):
        settings = context.scene.soulstruct_settings

        if not settings.game_config.supports_mcg:
            self.layout.label(text="Game does not use NavGraph (MCG).")
            return

        layout = self.layout

        header, panel = layout.panel("Import", default_closed=False)
        header.label(text="Import")
        if panel:
            self.draw_active_map(context, layout)
            if settings.map_stem:
                panel.operator(ImportMapMCG.bl_idname)
                panel.operator(ImportMapMCP.bl_idname)
            else:
                panel.label(text="No game map selected.")
            panel.operator(ImportAnyMCG.bl_idname)
            panel.operator(ImportAnyMCP.bl_idname)

        header, panel = layout.panel("Export", default_closed=False)
        header.label(text="Export")
        if panel:
            panel.prop(settings, "auto_detect_export_map")
            if settings.auto_detect_export_map:
                self.draw_detected_map(context, layout, use_latest_version=True)
            else:
                self.draw_active_map(context, layout)
            panel.operator(ExportMapMCGMCP.bl_idname)
            panel.operator(ExportAnyMCGMCP.bl_idname)


class NavGraphDrawPanel(SoulstructPanel):
    bl_label = "MCG Drawing"
    bl_idname = "MCG_PT_mcg_draw"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NavGraph (MCG)"
    bl_options = {"DEFAULT_CLOSED"}

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
            for prop_name in mcg_draw_settings.get_all_prop_names():
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


class NavGraphToolsPanel(SoulstructPanel):
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


class MCGGeneratorPanel(SoulstructPanel):
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
        nav_graph_compute_settings = context.scene.nav_graph_compute_settings
        if panel:
            panel.prop(nav_graph_compute_settings, "select_path")
            panel.prop(nav_graph_compute_settings, "wall_multiplier")
            panel.prop(nav_graph_compute_settings, "obstacle_multiplier")

        layout.operator(RecomputeEdgeCost.bl_idname)
        layout.operator(FindCheapestPath.bl_idname)
        layout.label(text="Complete MCG Generation:")
        layout.prop(nav_graph_compute_settings, "connected_exit_vertex_distance")
        layout.operator(AutoCreateMCG.bl_idname)
