from __future__ import annotations

import importlib
import sys
from pathlib import Path

import bpy

# Force reload of Soulstruct module (for easier updating).
modules_path = str(Path(__file__).parent / "modules")
if modules_path not in sys.path:
    sys.path.append(modules_path)
try:
    import soulstruct_havok
except ImportError:
    soulstruct_havok = None
else:
    importlib.reload(soulstruct_havok)
import soulstruct
importlib.reload(soulstruct)


if "HKX_PT_hkx_tools" in locals():
    importlib.reload(sys.modules["io_hkx.core"])
    importlib.reload(sys.modules["io_hkx.export_hkx"])
    importlib.reload(sys.modules["io_hkx.import_hkx"])

from io_hkx.export_hkx import ExportHKX, ExportHKXIntoBinder
from io_hkx.import_hkx import ImportHKX, ImportHKXWithBinderChoice, ImportHKXWithMSBChoice


bl_info = {
    "name": "HKX format",
    "author": "Scott Mooney (Grimrukh)",
    "version": (1, 0, 0),
    "blender": (3, 3, 0),
    "location": "File > Import-Export",
    "description": "HKX IO collision meshes",
    "warning": "",
    "doc_url": "https://github.com/Grimrukh/soulstruct-blender",
    "support": "COMMUNITY",
    "category": "Import-Export",
}


class HKX_PT_hkx_tools(bpy.types.Panel):
    bl_label = "HKX Tools"
    bl_idname = "HKX_PT_hkx_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "HKX"

    def draw(self, context):
        import_box = self.layout.box()
        import_box.operator("import_scene.hkx")

        export_box = self.layout.box()
        export_box.operator("export_scene.hkx")
        export_box.operator("export_scene.hkx_binder")


def menu_func_import(self, context):
    self.layout.operator(ImportHKX.bl_idname, text="HKX (.hkx/.hkxbhd)")


def menu_func_export(self, context):
    self.layout.operator(ExportHKX.bl_idname, text="HKX (.hkx)")
    self.layout.operator(ExportHKXIntoBinder.bl_idname, text="HKX to Binder (.hkxbhd)")


classes = (
    ImportHKX,
    ImportHKXWithBinderChoice,
    ImportHKXWithMSBChoice,
    ExportHKX,
    ExportHKXIntoBinder,
    HKX_PT_hkx_tools,
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
