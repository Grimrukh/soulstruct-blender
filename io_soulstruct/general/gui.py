from __future__ import annotations

__all__ = [
    "GlobalSettingsPanel",
    "GlobalSettingsPanel_View",
]

import bpy

from .operators import *


class GlobalSettingsPanel(bpy.types.Panel):
    """SCENE properties panel for Soulstruct global settings."""
    bl_label = "Soulstruct Settings"
    bl_idname = "SCENE_PT_soulstruct_settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.soulstruct_global_settings, "game")

        row = layout.row(align=True)
        split = row.split(factor=0.75)
        split.column().prop(context.scene.soulstruct_global_settings, "game_directory")
        split.column().operator(SelectGameDirectory.bl_idname, text="Browse")

        row = layout.row()
        split = row.split(factor=0.75)
        split.column().prop(context.scene.soulstruct_global_settings, "map_stem")
        split.column().operator(SelectMapDirectory.bl_idname, text="Browse")

        row = layout.row()
        split = row.split(factor=0.75)
        split.column().prop(context.scene.soulstruct_global_settings, "png_cache_directory")
        split.column().operator(SelectPNGCacheDirectory.bl_idname, text="Browse")

        row = layout.row()
        split = row.split(factor=0.75)
        split.column().prop(context.scene.soulstruct_global_settings, "mtdbnd_path")
        split.column().operator(SelectCustomMTDBNDFile.bl_idname, text="Browse")


class GlobalSettingsPanel_View(bpy.types.Panel):
    """VIEW properties panel for Soulstruct global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.soulstruct_global_settings, "game")

        row = layout.row(align=True)
        split = row.split(factor=0.75)
        split.column().prop(context.scene.soulstruct_global_settings, "game_directory")
        split.column().operator(SelectGameDirectory.bl_idname, text="Browse")

        row = layout.row()
        split = row.split(factor=0.75)
        split.column().prop(context.scene.soulstruct_global_settings, "map_stem")
        split.column().operator(SelectMapDirectory.bl_idname, text="Browse")

        row = layout.row()
        split = row.split(factor=0.75)
        split.column().prop(context.scene.soulstruct_global_settings, "png_cache_directory")
        split.column().operator(SelectPNGCacheDirectory.bl_idname, text="Browse")

        row = layout.row()
        split = row.split(factor=0.75)
        split.column().prop(context.scene.soulstruct_global_settings, "mtdbnd_path")
        split.column().operator(SelectCustomMTDBNDFile.bl_idname, text="Browse")
