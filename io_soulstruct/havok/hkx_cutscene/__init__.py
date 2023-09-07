from __future__ import annotations

__all__ = [
    "ImportHKXCutscene",
    "ExportHKXCutscene",
    "HKX_CUTSCENE_PT_hkx_cutscene_tools",
]

import importlib
import sys

import bpy

if "HKX_CUTSCENE_PT_hkx_tools" in locals():
    importlib.reload(sys.modules["io_soulstruct.hkx_cutscene.utilities"])
    importlib.reload(sys.modules["io_soulstruct.hkx_cutscene.import_hkx_cutscene"])
    importlib.reload(sys.modules["io_soulstruct.hkx_cutscene.export_hkx_cutscene"])

from .import_hkx_cutscene import ImportHKXCutscene
from .export_hkx_cutscene import ExportHKXCutscene


class HKX_CUTSCENE_PT_hkx_cutscene_tools(bpy.types.Panel):
    bl_label = "Cutscenes"
    bl_idname = "HKX_CUTSCENE_PT_hkx_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct Havok"

    # noinspection PyUnusedLocal
    def draw(self, context):
        import_box = self.layout.box()
        import_box.operator(ImportHKXCutscene.bl_idname)

        export_box = self.layout.box()
        export_box.operator(ExportHKXCutscene.bl_idname)
