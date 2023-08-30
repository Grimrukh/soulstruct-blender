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
from io_soulstruct.navmesh.nav_graph import CreateMCGEdgeOperator

modules_path = str(Path(__file__).parent / "modules")
if modules_path not in sys.path:
    sys.path.append(modules_path)

# Reload all Soulstruct modules, then all modules in this add-on (except this script).
for module_name in list(sys.modules.keys()):
    if "io_soulstruct" not in module_name and "soulstruct" in module_name.split(".")[0]:
        importlib.reload(sys.modules[module_name])
for module_name in list(sys.modules.keys()):
    if module_name != "io_soulstruct" and "io_soulstruct" in module_name.split(".")[0]:  # don't reload THIS module
        importlib.reload(sys.modules[module_name])

from io_soulstruct.flver import *
from io_soulstruct.navmesh import *
from io_soulstruct.misc_operators import *

# TODO: Currently asserting that `soulstruct_havok` is installed, but this is not necessary for all add-ons.
import soulstruct_havok

# try:
#     import soulstruct_havok
# except ModuleNotFoundError:
#     # `soulstruct_havok` not installed. HKX add-ons not enabled.
#     soulstruct_havok = None


bl_info = {
    "name": "Soulstruct (FromSoftware Formats)",
    "author": "Scott Mooney (Grimrukh)",
    "version": (1, 0, 0),
    "blender": (3, 5, 0),
    "location": "File > Import-Export",
    "description": "Import/export FromSoftware game files: FLVER models, NVM navmeshes, HKX collisions, HKX animations",
    "warning": "",
    "doc_url": "https://github.com/Grimrukh/soulstruct-blender",
    "support": "COMMUNITY",
    "category": "Import-Export",
}


# noinspection PyUnusedLocal
def menu_func_import(self, context):
    self.layout.operator(ImportFLVER.bl_idname, text="FLVER (.flver/.*bnd)")
    self.layout.operator(ImportNVM.bl_idname, text="NVM (.nvm/.nvmbnd)")
    self.layout.operator(ImportMCG.bl_idname, text="MCG (.mcg)")


# noinspection PyUnusedLocal
def menu_func_export(self, context):
    self.layout.operator(ExportFLVER.bl_idname, text="FLVER (.flver)")
    self.layout.operator(ExportFLVERIntoBinder.bl_idname, text="FLVER to Binder (.*bnd)")
    self.layout.operator(ExportNVM.bl_idname, text="NVM (.nvm)")
    self.layout.operator(ExportNVMIntoBinder.bl_idname, text="NVM to Binder (.nvmbnd)")


# noinspection PyUnusedLocal
def menu_func_view3d_mt(self, context):
    self.layout.operator(CopyMeshSelectionOperator.bl_idname, text="Copy Mesh Selection to Mesh")


# Classes to register.
CLASSES = (
    CopyMeshSelectionOperator,

    ImportFLVER,
    ImportFLVERWithMSBChoice,
    ImportEquipmentFLVER,

    HideAllDummiesOperator,
    ShowAllDummiesOperator,
    PrintGameTransform,

    ExportFLVER,
    ExportFLVERIntoBinder,
    ExportFLVERToMapDirectory,
    ExportMapDirectorySettings,

    ImportDDS,
    ExportTexturesIntoBinder,
    LightmapBakeProperties,
    BakeLightmapTextures,
    ExportLightmapTextures,

    FLVER_PT_flver_tools,
    FLVER_PT_bake_subpanel,

    ImportNVM,
    ImportNVMWithBinderChoice,
    ImportNVMWithMSBChoice,
    ExportNVM,
    ExportNVMIntoBinder,
    ImportMCP,
    ImportMCG,
    ExportMCG,
    CreateMCGEdgeOperator,
    NVM_PT_navmesh_tools,
    NavmeshFaceSettings,
    AddNVMFaceFlags,
    RemoveNVMFaceFlags,
    SetNVMFaceObstacleCount,
    MCGDrawSettings,
)

if soulstruct_havok:
    from io_soulstruct.havok.hkx_map_collision import *
    from io_soulstruct.havok.hkx_animation import *
    from io_soulstruct.havok.hkx_cutscene import *

    # Extra Havok classes to register.
    HAVOK_CLASSES = (
        ImportHKXMapCollision,
        ImportHKXMapCollisionWithBinderChoice,
        ImportHKXMapCollisionWithMSBChoice,
        ExportHKXMapCollision,
        ExportHKXMapCollisionIntoBinder,
        ExportHKXMapCollisionToMapDirectoryBHD,
        HKX_COLLISION_PT_hkx_map_collision_tools,

        ImportHKXAnimation,
        ImportHKXAnimationWithBinderChoice,
        ExportHKXAnimation,
        ExportHKXAnimationIntoBinder,
        ArmatureActionChoiceOperator,
        SelectArmatureActionOperator,
        HKX_ANIMATION_PT_hkx_animation_tools,

        ImportHKXCutscene,
        ExportHKXCutscene,
        HKX_CUTSCENE_PT_hkx_cutscene_tools,
    )

    # noinspection PyUnusedLocal
    def havok_menu_func_import(self, context):
        self.layout.operator(ImportHKXMapCollision.bl_idname, text="HKX Collision (.hkx/.hkxbhd)")
        self.layout.operator(ImportHKXAnimation.bl_idname, text="HKX Animation (.hkx/.hkxbhd)")
        self.layout.operator(ImportHKXCutscene.bl_idname, text="HKX Cutscene (.remobnd)")

    # noinspection PyUnusedLocal
    def havok_menu_func_export(self, context):
        self.layout.operator(ExportHKXMapCollision.bl_idname, text="HKX Collision (.hkx)")
        self.layout.operator(ExportHKXMapCollisionIntoBinder.bl_idname, text="HKX Collision to Binder (.hkxbhd)")
        self.layout.operator(ExportHKXAnimation.bl_idname, text="HKX Animation (.hkx)")
        self.layout.operator(ExportHKXAnimationIntoBinder.bl_idname, text="HKX Animation to Binder (.hkxbhd)")
        self.layout.operator(ExportHKXCutscene.bl_idname, text="HKX Cutscene (.remobnd)")

else:
    HAVOK_CLASSES = ()
    havok_menu_func_import = None
    havok_menu_func_export = None


HANDLERS = []


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.VIEW3D_MT_object.append(menu_func_view3d_mt)

    bpy.types.Scene.lightmap_bake_props = bpy.props.PointerProperty(type=LightmapBakeProperties)
    bpy.types.Scene.export_map_directory_settings = bpy.props.PointerProperty(type=ExportMapDirectorySettings)
    bpy.types.Scene.navmesh_face_settings = bpy.props.PointerProperty(type=NavmeshFaceSettings)
    bpy.types.Scene.mcg_draw_settings = bpy.props.PointerProperty(type=MCGDrawSettings)

    HANDLERS.append(bpy.types.SpaceView3D.draw_handler_add(draw_mcg_nodes, (), "WINDOW", "POST_VIEW"))
    HANDLERS.append(bpy.types.SpaceView3D.draw_handler_add(draw_mcg_node_labels, (), "WINDOW", "POST_PIXEL"))
    HANDLERS.append(bpy.types.SpaceView3D.draw_handler_add(draw_mcg_edges, (), "WINDOW", "POST_VIEW"))

    if HAVOK_CLASSES:
        for cls in HAVOK_CLASSES:
            bpy.utils.register_class(cls)
        bpy.types.TOPBAR_MT_file_import.append(havok_menu_func_import)
        bpy.types.TOPBAR_MT_file_export.append(havok_menu_func_export)


def unregister():
    for cls in CLASSES:
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.VIEW3D_MT_object.remove(menu_func_view3d_mt)

    if HAVOK_CLASSES:
        for cls in HAVOK_CLASSES:
            bpy.utils.unregister_class(cls)
        bpy.types.TOPBAR_MT_file_import.remove(havok_menu_func_import)
        bpy.types.TOPBAR_MT_file_export.remove(havok_menu_func_export)

    del bpy.types.Scene.lightmap_bake_props
    del bpy.types.Scene.export_map_directory_settings
    del bpy.types.Scene.navmesh_face_settings
    del bpy.types.Scene.mcg_draw_settings

    for handler in HANDLERS:
        bpy.types.SpaceView3D.draw_handler_remove(handler, "WINDOW")
    HANDLERS.clear()


if __name__ == "__main__":
    register()
