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
    "GlobalSettingsPanel_MiscView",
]

import bpy
from soulstruct.games import DEMONS_SOULS

from io_soulstruct.bpy_base.panel import SoulstructPanel
from io_soulstruct.types import SoulstructType
from .properties import SoulstructSettings


class _BaseGlobalSettingsPanel(SoulstructPanel):
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

        self.draw_map_stem_choice(context, layout)

        header, panel = layout.panel("Import/Export Settings", default_closed=True)
        header.label(text="Import/Export Settings")
        if panel:
            panel.prop(settings, "import_bak_file")
            panel.prop(settings, "prefer_import_from_project")
            panel.prop(settings, "also_export_to_game")
            panel.prop(settings, "smart_map_version_handling")
            if settings.is_game(DEMONS_SOULS):
                panel.prop(settings, "des_export_debug_files")
            panel.label(text="Soulstruct GUI Project Path:")
            panel.prop(settings, "soulstruct_project_root_str", text="")

        # TODO: Not that useful anymore. Removing to keep GUI minimal.
        # layout.operator(LoadCollectionsFromBlend.bl_idname, text="Load BLEND Collections")

        # Convenience: expose Soulstruct Type of active object, for manual editing.
        if context.active_object:
            box = layout.box()
            box.label(text="Active Object:")
            box.label(text=f"Name: {context.active_object.name}")
            box.prop(context.active_object, "soulstruct_type", text="Type")

            if context.active_object.soulstruct_type in {
                SoulstructType.MSB_PART, SoulstructType.MSB_REGION, SoulstructType.MSB_EVENT
            }:
                type_properties = getattr(context.active_object, context.active_object.soulstruct_type)
                box.prop(type_properties, "entry_subtype", text="Subtype")

        # TODO: Not useful at the moment, since the only Collection type is "MSB" and it's not checked.
        # if context.collection:
        #     box = layout.box()
        #     box.label(text="Active Collection:")
        #     box.label(text=f"Name: {context.collection.name}")
        #     box.prop(context.collection, "soulstruct_type", text="Type")

        layout.prop(settings, "enable_debug_logging")


class GlobalSettingsPanel(_BaseGlobalSettingsPanel):
    """SCENE properties panel for Soulstruct global settings."""
    bl_label = "Soulstruct Settings"
    bl_idname = "SCENE_PT_soulstruct_settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"


class GlobalSettingsPanel_FLVERView(_BaseGlobalSettingsPanel):
    """VIEW properties panel for Soulstruct global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_flver"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_options = {"DEFAULT_CLOSED"}


class GlobalSettingsPanel_MSBView(_BaseGlobalSettingsPanel):
    """VIEW properties panel for Soulstruct global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_msb"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MSB"
    bl_options = {"DEFAULT_CLOSED"}


class GlobalSettingsPanel_NavmeshView(_BaseGlobalSettingsPanel):
    """VIEW properties panel for Soulstruct global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_navmesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Navmesh"
    bl_options = {"DEFAULT_CLOSED"}


class GlobalSettingsPanel_NavGraphView(_BaseGlobalSettingsPanel):
    """VIEW properties panel for Soulstruct global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_navgraph"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NavGraph (MCG)"
    bl_options = {"DEFAULT_CLOSED"}


class GlobalSettingsPanel_AnimationView(_BaseGlobalSettingsPanel):
    """VIEW properties panel for Soulstruct Animation global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_animation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Animation"
    bl_options = {"DEFAULT_CLOSED"}


class GlobalSettingsPanel_CollisionView(_BaseGlobalSettingsPanel):
    """VIEW properties panel for Soulstruct Collision global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_collision"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Collision"
    bl_options = {"DEFAULT_CLOSED"}


class GlobalSettingsPanel_CutsceneView(_BaseGlobalSettingsPanel):
    """VIEW properties panel for Soulstruct global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_cutscene"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cutscene"
    bl_options = {"DEFAULT_CLOSED"}


class GlobalSettingsPanel_MiscView(_BaseGlobalSettingsPanel):
    """VIEW properties panel for Soulstruct global settings."""
    bl_label = "General Settings"
    bl_idname = "VIEW_PT_soulstruct_settings_misc"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Misc. Soulstruct"
    bl_options = {"DEFAULT_CLOSED"}
