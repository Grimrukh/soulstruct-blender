"""Blender add-ons for importing/export formats from FromSoftware games.

Primarily tested and maintained for Dark Souls Remastered. Other games and file versions may gradually be supported.

NOTE: some of the tools in this add-on require my additional `soulstruct_havok` Python package, which is provided
separately.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import bpy


modules_path = str(Path(__file__).parent / "modules")
if modules_path not in sys.path:
    sys.path.append(modules_path)

# Reload all Soulstruct and add-on modules (except this one).
for module_name in list(sys.modules.keys()):
    if module_name != "io_soulstruct" and "soulstruct" in module_name.split(".")[0]:  # don't reload THIS module
        importlib.reload(sys.modules[module_name])

from io_soulstruct.flver import *
from io_soulstruct.navmesh import *

try:
    import soulstruct_havok
except ModuleNotFoundError:
    # `soulstruct_havok` not installed. HKX add-ons not enabled.
    soulstruct_havok = None


bl_info = {
    "name": "Soulstruct (FromSoftware Formats)",
    "author": "Scott Mooney (Grimrukh)",
    "version": (1, 0, 0),
    "blender": (3, 3, 0),
    "location": "File > Import-Export",
    "description": "Import/export FromSoftware game files: FLVER, NVM navmesh, HKX collisions, HKX animations",
    "warning": "",
    "doc_url": "https://github.com/Grimrukh/soulstruct-blender",
    "support": "COMMUNITY",
    "category": "Import-Export",
}


def menu_func_import(self, context):
    self.layout.operator(ImportFLVER.bl_idname, text="FLVER (.flver/.*bnd)")
    self.layout.operator(ImportNVM.bl_idname, text="NVM (.nvm/.nvmbnd)")


def menu_func_export(self, context):
    self.layout.operator(ExportFLVER.bl_idname, text="FLVER (.flver)")
    self.layout.operator(ExportFLVERIntoBinder.bl_idname, text="FLVER to Binder (.*bnd)")
    self.layout.operator(ExportNVM.bl_idname, text="NVM (.nvm)")
    self.layout.operator(ExportNVMIntoBinder.bl_idname, text="NVM to Binder (.nvmbnd)")


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

    ImportNVM,
    ImportNVMWithMSBChoice,
    ExportNVM,
    ExportNVMIntoBinder,
    NVM_PT_navmesh_tools,
)


if soulstruct_havok:
    from io_soulstruct.hkx_collision import *
    from io_soulstruct.hkx_animation import *

    havok_classes = (
        ImportHKXCollision,
        ImportHKXCollisionWithBinderChoice,
        ImportHKXCollisionWithMSBChoice,
        ExportHKXCollision,
        ExportHKXCollisionIntoBinder,
        HKX_COLLISION_PT_hkx_collision_tools,

        ImportHKXAnimation,
        ImportHKXAnimationWithBinderChoice,
        # ExportHKXAnimation,
        # ExportHKXAnimationIntoBinder,
        HKX_ANIMATION_PT_hkx_animation_tools,
    )

    def havok_menu_func_import(self, context):
        self.layout.operator(ImportHKXCollision.bl_idname, text="HKX Collision (.hkx/.hkxbhd)")
        self.layout.operator(ImportHKXAnimation.bl_idname, text="HKX Animation (.hkx/.hkxbhd)")

    def havok_menu_func_export(self, context):
        self.layout.operator(ExportHKXCollision.bl_idname, text="HKX Collision (.hkx)")
        self.layout.operator(ExportHKXCollisionIntoBinder.bl_idname, text="HKX Collision to Binder (.hkxbhd)")
        # TODO: HKX animation export (and 'to binder' variant)
        #  Will need an existing ANIBND with existing compatible Skeleton.HKX, most likely.

else:
    havok_classes = ()
    havok_menu_func_import = None
    havok_menu_func_export = None


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

    bpy.types.Scene.lightmap_bake_props = bpy.props.PointerProperty(type=LightmapBakeProperties)

    if havok_classes:
        for cls in havok_classes:
            bpy.utils.register_class(cls)
        bpy.types.TOPBAR_MT_file_import.append(havok_menu_func_import)
        bpy.types.TOPBAR_MT_file_export.append(havok_menu_func_export)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    if havok_classes:
        for cls in havok_classes:
            bpy.utils.unregister_class(cls)
        bpy.types.TOPBAR_MT_file_import.remove(havok_menu_func_import)
        bpy.types.TOPBAR_MT_file_export.remove(havok_menu_func_export)

    del bpy.types.Scene.lightmap_bake_props


if __name__ == "__main__":
    register()
