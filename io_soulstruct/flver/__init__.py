from __future__ import annotations

__all__ = [
    "ImportFLVER",
    "ImportFLVERWithMSBChoice",
    "ExportFLVER",
    "ExportFLVERIntoBinder",
    "ExportFLVERToMapDirectory",
    "ExportMapDirectorySettings",
    "ImportDDS",
    "ExportTexturesIntoBinder",
    "LightmapBakeProperties",
    "BakeLightmapTextures",
    "ExportLightmapTextures",
    "FLVER_PT_flver_tools",
    "FLVER_PT_bake_subpanel",
]

import bpy

from io_soulstruct.flver.import_flver import ImportFLVER, ImportFLVERWithMSBChoice
from io_soulstruct.flver.export_flver import (
    ExportFLVER, ExportFLVERIntoBinder, ExportFLVERToMapDirectory, ExportMapDirectorySettings
)
from io_soulstruct.flver.textures import *


def CUSTOM_ENUM(choices):
    CUSTOM_ENUM.choices = choices


CUSTOM_ENUM.choices = []


class FLVER_PT_flver_tools(bpy.types.Panel):
    """Panel for Soulstruct FLVER operators."""
    bl_label = "FLVER Tools"
    bl_idname = "FLVER_PT_flver_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"

    def draw(self, context):
        import_box = self.layout.box()
        import_box.operator("import_scene.flver")

        export_box = self.layout.box()
        export_box.operator("export_scene.flver")
        export_box.operator("export_scene.flver_binder")

        export_map_settings = context.scene.export_map_directory_settings
        export_to_map_box = self.layout.box()
        export_to_map_box.prop(export_map_settings, "game_directory")
        export_to_map_box.prop(export_map_settings, "map_stem")
        export_to_map_box.prop(export_map_settings, "dcx_type")
        export_to_map_box.operator("export_scene_map.flver")

        textures_box = self.layout.box()
        textures_box.operator("import_image.dds")
        textures_box.operator("export_image.texture_binder")


class FLVER_PT_bake_subpanel(bpy.types.Panel):
    """Panel for Soulstruct FLVER lightmap texture baking."""
    bl_label = "Lightmaps"
    bl_idname = "FLVER_PT_bake_subpanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_parent_id = "FLVER_PT_flver_tools"

    def draw(self, context):
        self.layout.row().prop(context.scene.lightmap_bake_props, "bake_margin")
        self.layout.row().prop(context.scene.lightmap_bake_props, "bake_edge_shaders")
        self.layout.row().prop(context.scene.lightmap_bake_props, "bake_rendered_only")
        self.layout.row().operator("bake.lightmaps")

        self.layout.box().operator("export_image.lightmaps")

