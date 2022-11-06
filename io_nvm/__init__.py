from __future__ import annotations

import importlib
import sys
from pathlib import Path

import bpy

# Force reload of Soulstruct module (for easier updating).
modules_path = str(Path(__file__).parent / "modules")
if modules_path not in sys.path:
    sys.path.append(modules_path)
import soulstruct
importlib.reload(soulstruct)


if "NVM_PT_nvm_tools" in locals():
    importlib.reload(sys.modules["io_nvm.core"])
    importlib.reload(sys.modules["io_nvm.export_nvm"])
    importlib.reload(sys.modules["io_nvm.import_nvm"])

from io_nvm.export_nvm import ExportNVM, ExportNVMIntoBinder
from io_nvm.import_nvm import ImportNVM, ImportNVMWithBinderChoice, ImportNVMWithMSBChoice


bl_info = {
    "name": "NVM format",
    "author": "Scott Mooney (Grimrukh)",
    "version": (1, 0, 0),
    "blender": (3, 3, 0),
    "location": "File > Import-Export",
    "description": "NVM IO collision meshes",
    "warning": "",
    "doc_url": "https://github.com/Grimrukh/soulstruct-blender",
    "support": "COMMUNITY",
    "category": "Import-Export",
}


class NVM_PT_nvm_tools(bpy.types.Panel):
    bl_label = "NVM Tools"
    bl_idname = "NVM_PT_nvm_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NVM"

    def draw(self, context):
        import_box = self.layout.box()
        import_box.operator("import_scene.nvm")

        export_box = self.layout.box()
        export_box.operator("export_scene.nvm")
        export_box.operator("export_scene.nvm_binder")


def menu_func_import(self, context):
    self.layout.operator(ImportNVM.bl_idname, text="NVM (.nvm/.nvmbnd)")


def menu_func_export(self, context):
    self.layout.operator(ExportNVM.bl_idname, text="NVM (.nvm)")
    self.layout.operator(ExportNVMIntoBinder.bl_idname, text="NVM to Binder (.nvmbnd)")


classes = (
    ImportNVM,
    ImportNVMWithBinderChoice,
    ImportNVMWithMSBChoice,
    ExportNVM,
    ExportNVMIntoBinder,
    NVM_PT_nvm_tools,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
