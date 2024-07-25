from __future__ import annotations

__all__ = [
    "MCG_PT_ds1_mcg_import",
    "MCG_PT_ds1_mcg_export",
    "MCG_PT_ds1_mcg_draw",
    "MCG_PT_ds1_mcg_tools",
]

import bpy
from .import_operators import *
from .export_operators import *
from .misc_operators import *


class MCG_PT_ds1_mcg_import(bpy.types.Panel):
    bl_label = "DS1 MCG Import"
    bl_idname = "MCG_PT_ds1_mcg_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NavGraph (MCG)"
    bl_options = {'DEFAULT_CLOSED'}

    # noinspection PyUnusedLocal
    def draw(self, context):
        settings = context.scene.soulstruct_settings
        if settings.game_variable_name != "DARK_SOULS_DSR":
            self.layout.label(text="Dark Souls: Remastered only.")
            return

        import_loose_box = self.layout.box()
        import_loose_box.operator(ImportMCG.bl_idname)
        import_loose_box.operator(ImportMCP.bl_idname)

        quick_box = self.layout.box()
        quick_box.label(text="From Game/Project")
        quick_box.prop(context.scene.soulstruct_settings, "import_bak_file", text="From .BAK File")
        quick_box.prop(context.scene.soulstruct_game_enums, "nvm")
        quick_box.operator(ImportSelectedMapMCG.bl_idname)
        quick_box.operator(ImportSelectedMapMCP.bl_idname)


class MCG_PT_ds1_mcg_export(bpy.types.Panel):
    bl_label = "DS1 MCG Export"
    bl_idname = "MCG_PT_ds1_mcg_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NavGraph (MCG)"
    bl_options = {'DEFAULT_CLOSED'}

    # noinspection PyUnusedLocal
    def draw(self, context):
        settings = context.scene.soulstruct_settings
        if settings.game_variable_name != "DARK_SOULS_DSR":
            self.layout.label(text="Dark Souls: Remastered only.")
            return

        export_box = self.layout.box()
        export_box.operator(ExportMCG.bl_idname, text="Export MCG + MCP")

        map_export_box = self.layout.box()
        map_export_box.label(text="Export to Map")
        map_export_box.prop(
            context.window_manager.operator_properties_last(ExportMCGMCPToMap.bl_idname), "detect_map_from_parent"
        )
        map_export_box.operator(ExportMCGMCPToMap.bl_idname)


class MCG_PT_ds1_mcg_draw(bpy.types.Panel):
    bl_label = "DS1 MCG Drawing"
    bl_idname = "MCG_PT_ds1_mcg_draw"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Navmesh"
    bl_options = {'DEFAULT_CLOSED'}

    # noinspection PyUnusedLocal
    def draw(self, context):
        """Still shown if game is not DSR."""
        mcg_draw_settings = context.scene.mcg_draw_settings
        self.layout.prop(mcg_draw_settings, "mcg_parent")
        self.layout.prop(mcg_draw_settings, "mcg_graph_draw_enabled")
        self.layout.prop(mcg_draw_settings, "mcg_graph_draw_selected_nodes_only")
        self.layout.prop(mcg_draw_settings, "mcg_graph_color")
        self.layout.prop(mcg_draw_settings, "mcg_node_label_draw_enabled")
        self.layout.prop(mcg_draw_settings, "mcg_node_label_font_size")
        self.layout.prop(mcg_draw_settings, "mcg_node_label_font_color")
        self.layout.prop(mcg_draw_settings, "mcg_edge_label_font_size")
        # Color options in one row with no labels.
        self.layout.label(text="Edge Label Colors (Match, Close, Bad):")
        row = self.layout.row()
        row.prop(mcg_draw_settings, "mcg_edge_label_font_color", text="")
        row.prop(mcg_draw_settings, "mcg_almost_same_cost_edge_label_font_color", text="")
        row.prop(mcg_draw_settings, "mcg_bad_cost_edge_label_font_color", text="")
        self.layout.prop(mcg_draw_settings, "mcg_edge_triangles_highlight_enabled")



class MCG_PT_ds1_mcg_tools(bpy.types.Panel):
    bl_label = "DS1 MCG Tools"
    bl_idname = "MCG_PT_ds1_navmesh_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NavGraph (MCG)"
    bl_options = {'DEFAULT_CLOSED'}

    # noinspection PyUnusedLocal
    def draw(self, context):
        """Still shown if game is not DSR."""
        self.layout.operator(JoinMCGNodesThroughNavmesh.bl_idname)
        self.layout.operator(SetNodeNavmeshTriangles.bl_idname)
        self.layout.operator(RefreshMCGNames.bl_idname)
        compute_box = self.layout.box()
        compute_box.prop(context.scene.nav_graph_compute_settings, "select_path")
        compute_box.prop(context.scene.nav_graph_compute_settings, "wall_multiplier")
        compute_box.prop(context.scene.nav_graph_compute_settings, "obstacle_multiplier")
        compute_box.operator(RecomputeEdgeCost.bl_idname)
        compute_box.operator(FindCheapestPath.bl_idname)
        compute_box.operator(AutoCreateMCG.bl_idname)
