from __future__ import annotations

__all__ = [
    "GlobalSettingsPanel",
    "GlobalSettingsPanel_FLVERView",
    "GlobalSettingsPanel_MSBView",
    "GlobalSettingsPanel_NavmeshView",
    "GlobalSettingsPanel_NavGraphView",
    "GlobalSettingsPanel_AnimationView",
    "GlobalSettingsPanel_CollisionView",
    "GlobalSettingsPanel_CutsceneView",
]

import bpy

from .operators import *


class _GlobalSettingsPanel_ViewMixin:
    """VIEW properties panel mix-in for Soulstruct global settings."""

    layout: bpy.types.UILayout

    def draw(self, context):
        settings = context.scene.soulstruct_settings
        layout = self.layout
        layout.prop(settings, "game_enum")

        layout.label(text="Game Directory:")
        layout.prop(settings, "str_game_directory", text="")
        layout.label(text="Project Directory:")
        layout.prop(settings, "str_project_directory", text="")

        box = layout.box()
        box.prop(settings, "import_bak_file")
        box.prop(settings, "prefer_import_from_project")
        box.prop(settings, "also_export_to_game")
        box.prop(settings, "smart_map_version_handling")

        layout.operator(LoadCollectionsFromBlend.bl_idname, text="Load BLEND Collections")

        layout.label(text="Selected Map:")
        layout.prop(settings, "map_stem", text="")
        layout.operator(SelectGameMapDirectory.bl_idname)
        layout.operator(SelectProjectMapDirectory.bl_idname)

        if settings.is_game("ELDEN_RING"):
            layout.label(text="Custom MATBINBND Path:")
            layout.prop(settings, "str_matbinbnd_path", text="")
        else:
            layout.label(text="Custom MTDBND Path:")
            layout.prop(settings, "str_mtdbnd_path", text="")

        layout.label(text="PNG Cache Directory:")
        layout.prop(settings, "str_png_cache_directory", text="")
        layout.row().prop(settings, "read_cached_pngs")
        layout.row().prop(settings, "write_cached_pngs")
        layout.row().prop(settings, "pack_image_data")

        # Convenience: expose Soulstruct Type of active object, for manual editing.
        if context.active_object:
            layout.prop(context.active_object, "soulstruct_type", text="Active Object Type")


class GlobalSettingsPanel(bpy.types.Panel, _GlobalSettingsPanel_ViewMixin):
    """SCENE properties panel for Soulstruct global settings."""
    bl_label = "Soulstruct Settings"
    bl_idname = "SCENE_PT_soulstruct_settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"


class GlobalSettingsPanel_FLVERView(bpy.types.Panel, _GlobalSettingsPanel_ViewMixin):
    """VIEW properties panel for Soulstruct global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_flver"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"


class GlobalSettingsPanel_MSBView(bpy.types.Panel, _GlobalSettingsPanel_ViewMixin):
    """VIEW properties panel for Soulstruct global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_msb"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MSB"


class GlobalSettingsPanel_NavmeshView(bpy.types.Panel, _GlobalSettingsPanel_ViewMixin):
    """VIEW properties panel for Soulstruct global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_navmesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Navmesh"


class GlobalSettingsPanel_NavGraphView(bpy.types.Panel, _GlobalSettingsPanel_ViewMixin):
    """VIEW properties panel for Soulstruct global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_cutscene"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NavGraph (MCG)"


class GlobalSettingsPanel_AnimationView(bpy.types.Panel, _GlobalSettingsPanel_ViewMixin):
    """VIEW properties panel for Soulstruct Animation global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_animation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Animation"


class GlobalSettingsPanel_CollisionView(bpy.types.Panel, _GlobalSettingsPanel_ViewMixin):
    """VIEW properties panel for Soulstruct Collision global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_collision"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Collision"


class GlobalSettingsPanel_CutsceneView(bpy.types.Panel, _GlobalSettingsPanel_ViewMixin):
    """VIEW properties panel for Soulstruct global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_cutscene"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cutscene"
