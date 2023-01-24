from __future__ import annotations

__all__ = [
    "ImportFLVER",
    "ImportFLVERWithMSBChoice",
    "ExportFLVER",
    "ExportFLVERIntoBinder",
    "ImportDDS",
    "ExportTexturesIntoBinder",
    "LightmapBakeProperties",
    "BakeLightmapTextures",
    "ExportLightmapTextures",
    "FLVER_PT_flver_tools",
    "FLVER_PT_bake_subpanel",
]

import importlib
import sys

import bpy

if "FLVER_PT_flver_tools" in locals():
    print("Reloading add-on module...")
    importlib.reload(sys.modules["io_soulstruct.flver.core"])
    importlib.reload(sys.modules["io_soulstruct.flver.export_flver"])
    importlib.reload(sys.modules["io_soulstruct.flver.import_flver"])
    importlib.reload(sys.modules["io_soulstruct.flver.textures"])
    importlib.reload(sys.modules["io_soulstruct.flver.textures_utils"])

from io_soulstruct.flver.import_flver import ImportFLVER, ImportFLVERWithMSBChoice
from io_soulstruct.flver.export_flver import ExportFLVER, ExportFLVERIntoBinder
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

