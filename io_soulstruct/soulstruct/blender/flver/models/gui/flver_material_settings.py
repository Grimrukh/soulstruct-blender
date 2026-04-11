from __future__ import annotations

__all__ = [
    "FLVERMaterialSettingsPanel",
    "draw_material_image_settings",
]

import bpy

from ....base.register import io_soulstruct_class
from ....bpy_base.panel import SoulstructPanel


@io_soulstruct_class
class FLVERMaterialSettingsPanel(SoulstructPanel):

    bl_label = "FLVER Material Settings"
    bl_idname = "SCENE_PT_flver_material_settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        draw_material_image_settings(context, self.layout)

        header, panel = self.layout.panel("Texture Export Settings", default_closed=True)
        header.label(text="Texture Export Settings")
        if panel:
            texture_export_settings = context.scene.texture_export_settings
            for prop_name in texture_export_settings.get_game_prop_names(context):
                panel.prop(texture_export_settings, prop_name)


def draw_material_image_settings(context: bpy.types.Context, layout: bpy.types.UILayout | None) -> None:
    """Draw material image settings in the given layout."""
    if not layout:
        return
    mat_settings = context.scene.flver_material_settings

    layout.label(text="Image Cache Root Directory:")
    layout.prop(mat_settings, "image_cache_root_str", text="")
    layout.label(text="Image Import/Export Settings:")
    layout.prop(mat_settings, "image_cache_format")
    layout.prop(mat_settings, "import_cached_images")
    layout.prop(mat_settings, "cache_new_game_images")
    layout.prop(mat_settings, "pack_image_data")
