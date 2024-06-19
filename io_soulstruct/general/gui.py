from __future__ import annotations

__all__ = [
    "GlobalSettingsPanel",
    "GlobalSettingsPanel_FLVERView",
    "GlobalSettingsPanel_MSBView",
    "GlobalSettingsPanel_NavmeshView",
    "GlobalSettingsPanel_AnimationView",
    "GlobalSettingsPanel_CollisionView",
]

import bpy

from .core import SoulstructSettings
from .operators import *


class _GlobalSettingsPanel_ViewMixin:
    """VIEW properties panel mix-in for Soulstruct global settings."""

    layout: bpy.types.UILayout

    def draw(self, context):
        settings = context.scene.soulstruct_settings  # type: SoulstructSettings
        layout = self.layout
        layout.prop(settings, "game_enum")

        row = layout.row(align=True)
        split = row.split(factor=0.75)
        split.column().prop(settings, "str_game_directory")
        split.column().operator(SelectGameDirectory.bl_idname, text="Browse")

        row = layout.row(align=True)
        split = row.split(factor=0.75)
        split.column().prop(settings, "str_project_directory")
        split.column().operator(SelectProjectDirectory.bl_idname, text="Browse")

        layout.row().prop(settings, "import_bak_file")
        layout.row().prop(settings, "prefer_import_from_project")
        layout.row().prop(settings, "also_export_to_game")
        layout.row().prop(settings, "smart_map_version_handling")
        layout.row().operator(ClearCachedLists.bl_idname, text="Refresh File/Folder Dropdowns")
        layout.row().operator(LoadCollectionsFromBlend.bl_idname, text="Load BLEND Collections")

        if settings.is_game("ELDEN_RING"):
            layout.row().prop(settings, "map_stem_filter_mode")
            layout.row().prop(settings, "include_empty_map_tiles")
        layout.row().prop(settings, "map_stem")

        if settings.game_variable_name == "ELDEN_RING":
            row = layout.row()
            split = row.split(factor=0.75)
            split.column().prop(settings, "str_matbinbnd_path")
            split.column().operator(SelectCustomMATBINBNDFile.bl_idname, text="Browse")
        else:
            # TODO: Elden Ring still has an MTDBND that FLVERs may occasionally use?
            row = layout.row()
            split = row.split(factor=0.75)
            split.column().prop(settings, "str_mtdbnd_path")
            split.column().operator(SelectCustomMTDBNDFile.bl_idname, text="Browse")

        row = layout.row()
        split = row.split(factor=0.75)
        split.column().prop(settings, "str_png_cache_directory")
        split.column().operator(SelectPNGCacheDirectory.bl_idname, text="Browse")
        layout.row().prop(settings, "read_cached_pngs")
        layout.row().prop(settings, "write_cached_pngs")
        layout.row().prop(settings, "pack_image_data")


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
