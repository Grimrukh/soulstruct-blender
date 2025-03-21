from __future__ import annotations

__all__ = [
    "AnimationImportExportPanel",
    "AnimationToolsPanel",
]

from io_soulstruct.bpy_base.panel import SoulstructPanel
from .import_operators import *
from .export_operators import *
from .misc_operators import *


class AnimationImportExportPanel(SoulstructPanel):
    bl_label = "Animation Import/Export"
    bl_idname = "HKX_ANIMATION_PT_animation_import_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Animation"
    bl_options = {"DEFAULT_CLOSED"}

    # noinspection PyUnusedLocal
    def draw(self, context):
        settings = context.scene.soulstruct_settings
        if not settings.game_config.supports_animation:
            self.layout.label(text="Not supported for game.")
            return

        header, panel = self.layout.panel("Import", default_closed=False)
        header.label(text="Import")
        if panel:
            if settings.import_roots != (None, None):
                panel.label(text="Import from Game/Project")
                panel.operator(ImportCharacterHKXAnimation.bl_idname)
                if settings.is_game("ELDEN_RING"):
                    panel.operator(ImportAssetHKXAnimation.bl_idname)
                else:
                    panel.operator(ImportObjectHKXAnimation.bl_idname)
            else:
                panel.label(text="No game root path set.")
            panel.label(text="Generic Import:")
            panel.operator(ImportAnyHKXAnimation.bl_idname, text="Import Any Animation")

        header, panel = self.layout.panel("Export", default_closed=False)
        header.label(text="Export")
        if panel:
            panel.label(text="Export to Project/Game")
            panel.operator(ExportCharacterHKXAnimation.bl_idname)
            if settings.is_game("ELDEN_RING"):
                panel.label(text="Asset animation export not ready!")
            else:
                panel.operator(ExportObjectHKXAnimation.bl_idname)
            panel.label(text="Generic Export:")
            panel.operator(ExportAnyHKXAnimation.bl_idname)
            panel.operator(ExportHKXAnimationIntoAnyBinder.bl_idname)


class AnimationToolsPanel(SoulstructPanel):
    bl_label = "Animation Tools"
    bl_idname = "HKX_ANIMATION_PT_animation_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Animation"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        self.layout.operator(SelectArmatureActionOperator.bl_idname)
        # TODO: decimate operator with ratio field
