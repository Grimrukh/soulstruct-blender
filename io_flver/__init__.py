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

if "FLVER_PT_flver_tools" in locals():
    print("Reloading add-on module...")
    importlib.reload(sys.modules["io_flver.core"])
    importlib.reload(sys.modules["io_flver.export_flver"])
    importlib.reload(sys.modules["io_flver.import_flver"])
    importlib.reload(sys.modules["io_flver.textures"])
    importlib.reload(sys.modules["io_flver.textures_utils"])

from io_flver.core import LoggingOperator, Transform
from io_flver.export_flver import ExportFLVER, ExportFLVERIntoBinder
from io_flver.import_flver import ImportFLVER, ImportFLVERWithMSBChoice
from io_flver.textures import *


bl_info = {
    "name": "FLVER format",
    "author": "Scott Mooney (Grimrukh)",
    "version": (1, 0, 0),
    "blender": (3, 3, 0),
    "location": "File > Import-Export",
    "description": "FLVER IO meshes, materials, textures, and bones",
    "warning": "",
    "doc_url": "https://github.com/Grimrukh/soulstruct-blender",
    "support": "COMMUNITY",
    "category": "Import-Export",
}


def CUSTOM_ENUM(choices):
    CUSTOM_ENUM.choices = choices


CUSTOM_ENUM.choices = []


class FLVER_PT_flver_tools(bpy.types.Panel):
    bl_label = "FLVER Tools"
    bl_idname = "FLVER_PT_flver_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"

    def draw(self, context):
        import_box = self.layout.box()
        import_box.operator("import_scene.flver")

        export_box = self.layout.box()
        export_box.operator("export_scene.flver")
        export_box.operator("export_scene.flver_binder")

        textures_box = self.layout.box()
        textures_box.operator("import_image.dds")
        textures_box.operator("export_image.texture_binder")


class FLVER_PT_bake_subpanel(bpy.types.Panel):
    bl_label = "Lightmaps"
    bl_idname = "FLVER_PT_bake_subpanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_parent_id = "FLVER_PT_flver_tools"

    def draw(self, context):
        self.layout.row().prop(context.scene.lightmap_bake_props, "bake_margin")
        self.layout.row().prop(context.scene.lightmap_bake_props, "bake_edge_shaders")
        self.layout.row().prop(context.scene.lightmap_bake_props, "bake_rendered_only")
        self.layout.row().operator("bake.lightmaps")

        self.layout.box().operator("export_image.lightmaps")


def menu_func_import(self, context):
    self.layout.operator(ImportFLVER.bl_idname, text="FLVER (.flver/.*bnd)")


def menu_func_export(self, context):
    self.layout.operator(ExportFLVER.bl_idname, text="FLVER (.flver)")


classes = (
    ImportFLVER,
    ImportFLVERWithMSBChoice,
    ExportFLVER,
    ExportFLVERIntoBinder,
    ImportDDS,
    ExportTexturesIntoBinder,
    LightmapBakeProperties,
    BakeLightmapTextures,
    ExportLightmapTextures,
    FLVER_PT_flver_tools,
    FLVER_PT_bake_subpanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

    bpy.types.Scene.lightmap_bake_props = bpy.props.PointerProperty(type=LightmapBakeProperties)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    del bpy.types.Scene.lightmap_bake_props


if __name__ == "__main__":
    register()
