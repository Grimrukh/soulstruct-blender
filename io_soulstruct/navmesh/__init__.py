from __future__ import annotations

__all__ = [
    "ImportNVM",
    "ImportNVMWithBinderChoice",
    "ImportNVMWithMSBChoice",
    "ExportNVM",
    "ExportNVMIntoBinder",
    "NVM_PT_navmesh_tools"
]

import importlib
import sys

import bpy

if "NVM_PT_nvm_tools" in locals():
    importlib.reload(sys.modules["io_soulstruct.navmesh.utilities"])
    importlib.reload(sys.modules["io_soulstruct.navmesh.export_nvm"])
    importlib.reload(sys.modules["io_soulstruct.navmesh.import_nvm"])

from io_soulstruct.navmesh.export_nvm import ExportNVM, ExportNVMIntoBinder
from io_soulstruct.navmesh.import_nvm import ImportNVM, ImportNVMWithBinderChoice, ImportNVMWithMSBChoice


class NVM_PT_navmesh_tools(bpy.types.Panel):
    bl_label = "DS1 Navmesh Tools"
    bl_idname = "NVM_PT_navmesh_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Navmesh"

    # noinspection PyUnusedLocal
    def draw(self, context):
        import_box = self.layout.box()
        import_box.operator(ImportNVM.bl_idname)

        export_box = self.layout.box()
        export_box.operator(ExportNVM.bl_idname)
        export_box.operator(ExportNVMIntoBinder.bl_idname)
