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
    "map_stem_box",
]

import bpy
from soulstruct.games import DEMONS_SOULS

from .operators import *
from .properties import SoulstructSettings


class _GlobalSettingsPanel_ViewMixin:
    """VIEW properties panel mix-in for Soulstruct global settings."""

    layout: bpy.types.UILayout

    def draw(self, context):
        settings = context.scene.soulstruct_settings  # type: SoulstructSettings
        layout = self.layout
        layout.prop(settings, "game_enum")

        game = settings.game
        if game:
            layout.label(text="Game Root:")
            layout.prop(settings, settings.get_game_root_prop_name(), text="")
            layout.label(text="Project Root:")
            layout.prop(settings, settings.get_project_root_prop_name(), text="")
        else:
            layout.label(text="Unsupported Game")

        header, panel = layout.panel("Import/Export Settings", default_closed=True)
        header.label(text="Import/Export Settings")
        if panel:
            panel.prop(settings, "import_bak_file")
            panel.prop(settings, "prefer_import_from_project")
            panel.prop(settings, "also_export_to_game")
            panel.prop(settings, "smart_map_version_handling")
            if settings.is_game(DEMONS_SOULS):
                panel.prop(settings, "export_des_debug_files")
            panel.label(text="Soulstruct GUI Project Path:")
            panel.prop(settings, "soulstruct_project_root_str", text="")

        map_stem_box(layout, settings)

        header, panel = layout.panel("Material/Texture Settings", default_closed=True)
        header.label(text="Material/Texture Settings")
        if panel:
            if settings.is_game("ELDEN_RING"):
                panel.label(text="Custom MATBINBND Path:")
                panel.prop(settings, "str_matbinbnd_path", text="")
            else:
                panel.label(text="Custom MTDBND Path:")
                panel.prop(settings, "str_mtdbnd_path", text="")

            panel.label(text="Image Cache Directory:")
            panel.prop(settings, "str_image_cache_directory", text="")
            panel.prop(settings, "image_cache_format")
            panel.prop(settings, "read_cached_images")
            panel.prop(settings, "write_cached_images")
            panel.prop(settings, "pack_image_data")

        # TODO: Not that useful anymore. Removing to keep GUI minimal.
        # layout.operator(LoadCollectionsFromBlend.bl_idname, text="Load BLEND Collections")

        # Convenience: expose Soulstruct Type of active object, for manual editing.
        if context.active_object:
            layout.label(text=f"Name: {context.active_object.name}")
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
    bl_options = {"DEFAULT_CLOSED"}


class GlobalSettingsPanel_MSBView(bpy.types.Panel, _GlobalSettingsPanel_ViewMixin):
    """VIEW properties panel for Soulstruct global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_msb"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MSB"
    bl_options = {"DEFAULT_CLOSED"}


class GlobalSettingsPanel_NavmeshView(bpy.types.Panel, _GlobalSettingsPanel_ViewMixin):
    """VIEW properties panel for Soulstruct global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_navmesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Navmesh"
    bl_options = {"DEFAULT_CLOSED"}


class GlobalSettingsPanel_NavGraphView(bpy.types.Panel, _GlobalSettingsPanel_ViewMixin):
    """VIEW properties panel for Soulstruct global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_navgraph"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NavGraph (MCG)"
    bl_options = {"DEFAULT_CLOSED"}


class GlobalSettingsPanel_AnimationView(bpy.types.Panel, _GlobalSettingsPanel_ViewMixin):
    """VIEW properties panel for Soulstruct Animation global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_animation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Animation"
    bl_options = {"DEFAULT_CLOSED"}


class GlobalSettingsPanel_CollisionView(bpy.types.Panel, _GlobalSettingsPanel_ViewMixin):
    """VIEW properties panel for Soulstruct Collision global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_collision"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Collision"
    bl_options = {"DEFAULT_CLOSED"}


class GlobalSettingsPanel_CutsceneView(bpy.types.Panel, _GlobalSettingsPanel_ViewMixin):
    """VIEW properties panel for Soulstruct global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_cutscene"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cutscene"
    bl_options = {"DEFAULT_CLOSED"}


def map_stem_box(layout: bpy.types.UILayout, settings: SoulstructSettings):
    map_box = layout.box()
    map_box.label(text="Selected Map:")
    map_box.prop(settings, "map_stem", text="")
    row = map_box.row()
    split = row.split(factor=0.5)
    split.column().operator(SelectGameMapDirectory.bl_idname, text="Select Game Map")
    split.column().operator(SelectProjectMapDirectory.bl_idname, text="Select Project Map")
