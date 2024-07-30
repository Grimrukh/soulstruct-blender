from __future__ import annotations

__all__ = [
    "CutsceneImportExportPanel",
]

import bpy
from .import_operators import *


class CutsceneImportExportPanel(bpy.types.Panel):
    bl_label = "Cutscenes"
    bl_idname = "CUTSCENE_PT_hkx_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cutscene"
    bl_options = {"DEFAULT_CLOSED"}

    # noinspection PyUnusedLocal
    def draw(self, context):
        layout = self.layout
        settings = context.scene.soulstruct_settings

        header, panel = layout.panel("Import", default_closed=False)
        header.label(text="Import")
        if panel:
            if not settings.is_game("DARK_SOULS_DSR"):
                panel.label(text="Import for DSR only.")
            else:
                panel.operator(ImportHKXCutscene.bl_idname)

        header, panel = layout.panel("Export", default_closed=False)
        header.label(text="Export")
        if panel:
            if not settings.is_game("DARK_SOULS_DSR"):
                panel.label(text="Export for DSR only.")
            else:
                # TODO: Not up yet.
                panel.label(text="Not yet implemented.")
                # panel.operator(ExportHKXCutscene.bl_idname)
