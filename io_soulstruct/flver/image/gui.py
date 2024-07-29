from __future__ import annotations

__all__ = [
    "TextureExportSettingsPanel",
]

import bpy


class TextureExportSettingsPanel(bpy.types.Panel):
    """Panel for Soulstruct FLVER texture export settings."""
    bl_label = "Texture Export Settings"
    bl_idname = "SCENE_PT_texture_export_settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        # TODO: These are DS1 fields. Need other games. (Use their own settings classes.)
        settings = context.scene.texture_export_settings
        for prop, split in (
            ("overwrite_existing_map_textures", 0),
            ("require_power_of_two", 0),
            ("_platform", 0.6),
            ("max_chrbnd_tpf_size", 0),
        ):
            if split > 0:
                row = self.layout.row(align=True)
                split = row.split(factor=split)
                split.column().label(text=prop.replace("_", " ").title())
                split.column().prop(settings, prop, text="")
            else:
                self.layout.prop(settings, prop)
