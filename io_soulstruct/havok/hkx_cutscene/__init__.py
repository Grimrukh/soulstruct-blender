from __future__ import annotations

__all__ = [
    "ImportHKXCutscene",
    "ExportHKXCutscene",
    "HKX_CUTSCENE_PT_hkx_cutscene_tools",
]

import bpy

from .import_hkx_cutscene import ImportHKXCutscene
from .export_hkx_cutscene import ExportHKXCutscene


class HKX_CUTSCENE_PT_hkx_cutscene_tools(bpy.types.Panel):
    bl_label = "HKX Cutscenes"
    bl_idname = "HKX_CUTSCENE_PT_hkx_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cutscene"
    bl_options = {'DEFAULT_CLOSED'}

    # noinspection PyUnusedLocal
    def draw(self, context):
        import_box = self.layout.box()
        import_box.operator(ImportHKXCutscene.bl_idname)

        export_box = self.layout.box()
        export_box.operator(ExportHKXCutscene.bl_idname)
