from __future__ import annotations

__all__ = [
    "AnimationImportExportPanel",
    "AnimationToolsPanel",
]

import bpy
from .import_operators import *
from .export_operators import *
from .misc_operators import *


class AnimationImportExportPanel(bpy.types.Panel):
    bl_label = "Animation Import/Export"
    bl_idname = "HKX_ANIMATION_PT_animation_import_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Animation"
    bl_options = {"DEFAULT_CLOSED"}

    # noinspection PyUnusedLocal
    def draw(self, context):
        settings = context.scene.soulstruct_settings
        if not settings.is_game("DARK_SOULS_PTDE", "DARK_SOULS_DSR", "ELDEN_RING"):
            self.layout.label(text="Import/Export for DSR and ER only.")
            return

        header, panel = self.layout.panel("Import", default_closed=False)
        header.label(text="Import")
        if panel:
            if settings.import_roots != (None, None):
                panel.label(text="Import from Game/Project")
                panel.operator(ImportCharacterHKXAnimation.bl_idname)
                if settings.game_variable_name == "ELDEN_RING":
                    panel.operator(ImportAssetHKXAnimation.bl_idname)
                else:
                    panel.operator(ImportObjectHKXAnimation.bl_idname)
            else:
                panel.label(text="No game root path set.")
            panel.label(text="Generic Import:")
            panel.operator(ImportHKXAnimation.bl_idname, text="Import Any Animation")

        header, panel = self.layout.panel("Export", default_closed=False)
        header.label(text="Export")
        if panel:
            if settings.game_variable_name not in {"DARK_SOULS_DSR"}:
                panel.label(text="Export for DSR only.")
            else:
                panel.label(text="Export to Project/Game")
                panel.operator(ExportCharacterHKXAnimation.bl_idname)
                panel.operator(ExportObjectHKXAnimation.bl_idname)
                panel.label(text="Generic Export:")
                panel.operator(ExportLooseHKXAnimation.bl_idname)
                panel.operator(ExportHKXAnimationIntoBinder.bl_idname)


class AnimationToolsPanel(bpy.types.Panel):
    bl_label = "Animation Tools"
    bl_idname = "HKX_ANIMATION_PT_animation_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Animation"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        self.layout.operator(SelectArmatureActionOperator.bl_idname)
        # TODO: decimate operator with ratio field
