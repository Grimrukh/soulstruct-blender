from __future__ import annotations

__all__ = [
    "FLVERMaterialSettingsPanel",
]

from soulstruct.blender.bpy_base.panel import SoulstructPanel


class FLVERMaterialSettingsPanel(SoulstructPanel):

    bl_label = "FLVER Material Settings"
    bl_idname = "SCENE_PT_flver_material_settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        settings = context.scene.soulstruct_settings
        mat_settings = context.scene.flver_material_settings

        if settings.game_config.uses_matbin:
            layout.label(text="Custom MATBINBND Path:")
            layout.prop(mat_settings, mat_settings.get_game_matbinbnd_path_prop_name(context), text="")
        else:
            layout.label(text="Custom MTDBND Path:")
            layout.prop(mat_settings, mat_settings.get_game_mtdbnd_path_prop_name(context), text="")

        layout.label(text="Image Cache Directory:")
        layout.prop(mat_settings, mat_settings.get_game_image_cache_path_prop_name(context), text="")
        layout.prop(mat_settings, "image_cache_format")
        layout.prop(mat_settings, "import_cached_images")
        layout.prop(mat_settings, "cache_new_game_images")
        layout.prop(mat_settings, "pack_image_data")

        header, panel = layout.panel("Texture Export Settings", default_closed=True)
        header.label(text="Texture Export Settings")
        if panel:
            texture_export_settings = context.scene.texture_export_settings
            for prop_name in texture_export_settings.get_game_prop_names(context):
                panel.prop(texture_export_settings, prop_name)
