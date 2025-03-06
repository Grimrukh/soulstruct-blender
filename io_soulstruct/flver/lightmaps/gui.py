from __future__ import annotations

__all__ = ["FLVERLightmapsPanel"]

import bpy

from .operators import BakeLightmapTextures


class FLVERLightmapsPanel(bpy.types.Panel):
    """Panel for Soulstruct FLVER operators."""
    bl_label = "FLVER Lightmaps"
    bl_idname = "SCENE_PT_flver_lightmaps"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        bake_lightmap_settings = context.scene.bake_lightmap_settings
        header, panel = layout.panel("Settings", default_closed=False)
        header.label(text="Settings")
        if panel:
            for prop_name in bake_lightmap_settings.__annotations__:
                panel.prop(bake_lightmap_settings, prop_name)
        layout.operator(BakeLightmapTextures.bl_idname)
