"""Blender add-ons for importing/export formats from FromSoftware games and manipulating their data.

Primarily tested and maintained for Dark Souls Remastered. See README.md for table of supported games and file types.

This Blender Extension uses the apparatus created in Blender 4.2 -- all Python dependencies are included as wheels
for all supported platforms (currently only Windows AMD64).

If you would like to use this extension in development mode, you can use the `install_extension.py` and/or
`prepare_extension.py` scripts in the root of the extension's GitHub repo:
    https://github.com/Grimrukh/soulstruct-blender.git

The `install_extension.py` script will attempt to directly. update the local 'user_default' Python site-packages for
your chosen version of Blender.
"""
from __future__ import annotations

import importlib
import importlib.util
import sys

try:
    import bpy
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        "This module requires Blender (`bpy`, etc.) to be run in order to import it. "
        "Please ensure you are running this code inside Blender's Python environment."
    )

try:
    import soulstruct.version
    import soulstruct.havok.version
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        "This Soulstruct add-on requires `soulstruct` and `soulstruct-havok` Python packages to be installed. "
        "This should have been done automatically by the extension. Try restarting Blender or "
        "uninstalling and reinstalling the add-on."
    )


# Reload all Soulstruct modules, then all modules in this add-on (except this script).
# NOTE: This is IMPORTANT when using 'Reload Scripts' in Blender, as it is otherwise prone to partial re-imports of
# Soulstruct that duplicate classes and cause wild bugs with `isinstance`, object ID equality, etc.

def _try_reload(_module_name: str):
    try:
        importlib.reload(sys.modules[_module_name])
    except (KeyError, ImportError):
        pass


for module_name in list(sys.modules.keys()):
    if "soulstruct.blender" in module_name:
        _try_reload(module_name)


from .soulstruct.blender.base.register import register_io_soulstruct, unregister_io_soulstruct

from .soulstruct.blender.misc import *

from .soulstruct.blender.animation import *
from .soulstruct.blender.collision import *
from .soulstruct.blender.cutscene import *
from .soulstruct.blender.flver import *
from .soulstruct.blender.nav_graph import *
from .soulstruct.blender.navmesh import *


# TODO: Add more operators to menu functions.


# noinspection PyUnusedLocal
def menu_func_import(self, context):
    layout = self.layout
    layout.operator(ImportFLVER.bl_idname, text="FLVER (.flver/.*bnd)")
    layout.operator(ImportAnyNVM.bl_idname, text="NVM (.nvm/.nvmbnd)")
    layout.operator(ImportAnyMCG.bl_idname, text="MCG (.mcg)")


# noinspection PyUnusedLocal
def menu_func_export(self, context):
    layout = self.layout
    layout.operator(ExportAnyFLVER.bl_idname, text="FLVER (.flver)")
    layout.operator(ExportFLVERIntoAnyBinder.bl_idname, text="FLVER to Binder (.*bnd)")
    layout.operator(ExportAnyNVM.bl_idname, text="NVM (.nvm)")
    layout.operator(ExportNVMIntoAnyBinder.bl_idname, text="NVM to Binder (.nvmbnd)")


# noinspection PyUnusedLocal
def menu_func_view3d_mt(self, context):
    layout = self.layout
    layout.operator(CopyMeshSelectionOperator.bl_idname, text="Copy Mesh Selection to Mesh")


# noinspection PyUnusedLocal
def havok_menu_func_import(self, context):
    self.layout.operator(ImportAnyHKXMapCollision.bl_idname, text="HKX Collision (.hkx/.hkxbhd)")
    self.layout.operator(ImportAnyHKXAnimation.bl_idname, text="HKX Animation (.hkx/.hkxbhd)")
    self.layout.operator(ImportHKXCutscene.bl_idname, text="HKX Cutscene (.remobnd)")


# noinspection PyUnusedLocal
def havok_menu_func_export(self, context):
    self.layout.operator(ExportAnyHKXMapCollision.bl_idname, text="HKX Collision (.hkx)")
    self.layout.operator(ExportHKXMapCollisionIntoAnyBinder.bl_idname, text="HKX Collision to Binder (.hkxbhd)")
    self.layout.operator(ExportAnyHKXAnimation.bl_idname, text="HKX Animation (.hkx)")
    self.layout.operator(ExportHKXAnimationIntoAnyBinder.bl_idname, text="HKX Animation to Binder (.hkxbhd)")
    self.layout.operator(ExportHKXCutscene.bl_idname, text="HKX Cutscene (.remobnd)")


# TODO: Put all Scene pointer props under a common group like `Scene.soulstruct`.


def register():

    register_io_soulstruct()

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.VIEW3D_MT_object.append(menu_func_view3d_mt)

    bpy.types.TOPBAR_MT_file_import.append(havok_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(havok_menu_func_export)


def unregister():

    unregister_io_soulstruct()

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.VIEW3D_MT_object.remove(menu_func_view3d_mt)
    bpy.types.TOPBAR_MT_file_import.remove(havok_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(havok_menu_func_export)


if __name__ == "__main__":
    register()
