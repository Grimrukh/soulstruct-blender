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

# Add 'modules' subdirectory to Python path. We simply bundle them with the addon.
addon_modules_path = str((Path(__file__).parent / "../io_soulstruct_lib").resolve())
if addon_modules_path not in sys.path:
    sys.path.append(addon_modules_path)

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
from io_soulstruct.general import *

# TODO: Currently asserting that `soulstruct_havok` is installed, but this is not necessary for all add-ons.
import soulstruct_havok


bl_info = {
    "name": "Soulstruct",
    "author": "Scott Mooney (Grimrukh)",
    "version": (1, 0, 0),
    "blender": (3, 5, 0),
    "location": "File > Import-Export",
    "description": "Import, manipulate, and export FromSoftware/Havok assets",
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
    self.layout.operator(ExportStandaloneFLVER.bl_idname, text="FLVER (.flver)")
    self.layout.operator(ExportFLVERIntoBinder.bl_idname, text="FLVER to Binder (.*bnd)")
    self.layout.operator(ExportLooseNVM.bl_idname, text="NVM (.nvm)")
    self.layout.operator(ExportNVMIntoBinder.bl_idname, text="NVM to Binder (.nvmbnd)")


# noinspection PyUnusedLocal
def menu_func_view3d_mt(self, context):
    self.layout.operator(CopyMeshSelectionOperator.bl_idname, text="Copy Mesh Selection to Mesh")


# Classes to register.
CLASSES = (
    SoulstructSettings,
    SoulstructGameEnums,
    GlobalSettingsPanel,
    GlobalSettingsPanel_FLVERView,
    SelectGameDirectory,
    SelectGameExportDirectory,
    SelectMapDirectory,
    SelectPNGCacheDirectory,
    SelectCustomMTDBNDFile,
    SelectCustomMATBINBNDFile,

    MeshMoveSettings,
    CopyMeshSelectionOperator,
    CutMeshSelectionOperator,

    ImportFLVER,
    ImportMapPieceFLVER,
    ImportCharacterFLVER,
    ImportObjectFLVER,
    ImportEquipmentFLVER,
    FLVERImportSettings,
    ImportMapPieceMSBPart,
    ImportAllMapPieceMSBParts,

    HideAllDummiesOperator,
    ShowAllDummiesOperator,
    PrintGameTransform,

    FLVERExportSettings,
    ExportStandaloneFLVER,
    ExportFLVERIntoBinder,
    ExportMapPieceFLVERs,
    ExportCharacterFLVER,
    ExportObjectFLVER,
    ExportEquipmentFLVER,
    ExportMapPieceMSBParts,

    FLVERToolSettings,
    SetVertexAlpha,
    ActivateUVMap1,
    ActivateUVMap2,
    ActivateUVMap3,

    ImportTextures,
    BakeLightmapSettings,
    BakeLightmapTextures,
    TextureExportSettings,

    FLVERImportPanel,
    FLVERExportPanel,
    TextureExportSettingsPanel,
    # FLVERLightmapsPanel,  # TODO: not quite ready
    FLVERToolsPanel,
    FLVERUVMapsPanel,

    GlobalSettingsPanel_NavmeshView,
    ImportNVM,
    ImportNVMWithBinderChoice,
    ImportNVMFromNVMBND,
    ImportNVMMSBPart,
    ExportLooseNVM,
    ExportNVMIntoBinder,
    ExportNVMIntoNVMBND,
    ExportNVMMSBPart,
    ImportMCP,
    QuickImportMCP,
    ImportMCG,
    QuickImportMCG,
    ExportMCG,
    QuickExportMCGMCP,
    CreateMCGEdgeOperator,
    SetNodeNavmeshATriangles,
    SetNodeNavmeshBTriangles,
    NVM_PT_ds1_navmesh_import,
    NVM_PT_ds1_navmesh_export,
    NVM_PT_ds1_navmesh_tools,
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
        GlobalSettingsPanel_HavokView,

        ImportHKXMapCollision,
        ImportHKXMapCollisionWithBinderChoice,
        ImportHKXMapCollisionFromHKXBHD,
        ImportMSBMapCollision,

        ImportHKXAnimation,
        ImportHKXAnimationWithBinderChoice,
        ImportCharacterHKXAnimation,
        ImportObjectHKXAnimation,
        ExportLooseHKXAnimation,
        ExportHKXAnimationIntoBinder,
        QuickExportCharacterHKXAnimation,
        QuickExportObjectHKXAnimation,

        ArmatureActionChoiceOperator,
        SelectArmatureActionOperator,
        HKX_ANIMATION_PT_hkx_animations,

        ExportLooseHKXMapCollision,
        ExportHKXMapCollisionIntoBinder,
        ExportHKXMapCollisionIntoHKXBHD,
        ExportMSBMapCollision,
        HKX_COLLISION_PT_hkx_map_collisions,

        # TODO: Cutscene operators need a bit more work.
        # ImportHKXCutscene,
        # ExportHKXCutscene,
        # HKX_CUTSCENE_PT_hkx_cutscene_tools,
    )

    # noinspection PyUnusedLocal
    def havok_menu_func_import(self, context):
        self.layout.operator(ImportHKXMapCollision.bl_idname, text="HKX Collision (.hkx/.hkxbhd)")
        self.layout.operator(ImportHKXAnimation.bl_idname, text="HKX Animation (.hkx/.hkxbhd)")
        # self.layout.operator(ImportHKXCutscene.bl_idname, text="HKX Cutscene (.remobnd)")

    # noinspection PyUnusedLocal
    def havok_menu_func_export(self, context):
        self.layout.operator(ExportLooseHKXMapCollision.bl_idname, text="HKX Collision (.hkx)")
        self.layout.operator(ExportHKXMapCollisionIntoBinder.bl_idname, text="HKX Collision to Binder (.hkxbhd)")
        self.layout.operator(ExportLooseHKXAnimation.bl_idname, text="HKX Animation (.hkx)")
        self.layout.operator(ExportHKXAnimationIntoBinder.bl_idname, text="HKX Animation to Binder (.hkxbhd)")
        # self.layout.operator(ExportHKXCutscene.bl_idname, text="HKX Cutscene (.remobnd)")

else:
    HAVOK_CLASSES = ()
    havok_menu_func_import = None
    havok_menu_func_export = None


LOAD_POST_HANDLERS = []
SPACE_VIEW_3D_HANDLERS = []


@bpy.app.handlers.persistent
def load_handler(_):
    SoulstructSettings.from_context().load_settings()


def register():
    for cls in CLASSES:
        try:
            bpy.utils.register_class(cls)
        except Exception as ex:
            print(f"Failed to register class {cls.__name__}: {ex}")
            raise

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.VIEW3D_MT_object.append(menu_func_view3d_mt)

    bpy.types.Scene.soulstruct_settings = bpy.props.PointerProperty(type=SoulstructSettings)
    bpy.types.Scene.soulstruct_game_enums = bpy.props.PointerProperty(type=SoulstructGameEnums)
    bpy.types.Scene.flver_import_settings = bpy.props.PointerProperty(type=FLVERImportSettings)
    bpy.types.Scene.flver_export_settings = bpy.props.PointerProperty(type=FLVERExportSettings)
    bpy.types.Scene.texture_export_settings = bpy.props.PointerProperty(type=TextureExportSettings)
    bpy.types.Scene.bake_lightmap_settings = bpy.props.PointerProperty(type=BakeLightmapSettings)
    bpy.types.Scene.navmesh_face_settings = bpy.props.PointerProperty(type=NavmeshFaceSettings)
    bpy.types.Scene.mcg_draw_settings = bpy.props.PointerProperty(type=MCGDrawSettings)
    bpy.types.Scene.mesh_move_settings = bpy.props.PointerProperty(type=MeshMoveSettings)
    bpy.types.Scene.flver_settings = bpy.props.PointerProperty(type=FLVERToolSettings)

    bpy.app.handlers.load_post.append(load_handler)
    LOAD_POST_HANDLERS.append(load_handler)

    SPACE_VIEW_3D_HANDLERS.append(
        bpy.types.SpaceView3D.draw_handler_add(draw_dummy_ids, (), "WINDOW", "POST_PIXEL")
    )

    SPACE_VIEW_3D_HANDLERS.append(
        bpy.types.SpaceView3D.draw_handler_add(draw_mcg_nodes, (), "WINDOW", "POST_VIEW")
    )
    SPACE_VIEW_3D_HANDLERS.append(
        bpy.types.SpaceView3D.draw_handler_add(draw_mcg_node_labels, (), "WINDOW", "POST_PIXEL")
    )
    SPACE_VIEW_3D_HANDLERS.append(
        bpy.types.SpaceView3D.draw_handler_add(draw_mcg_edges, (), "WINDOW", "POST_VIEW")
    )

    if HAVOK_CLASSES:
        for cls in HAVOK_CLASSES:
            bpy.utils.register_class(cls)
        bpy.types.TOPBAR_MT_file_import.append(havok_menu_func_import)
        bpy.types.TOPBAR_MT_file_export.append(havok_menu_func_export)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.VIEW3D_MT_object.remove(menu_func_view3d_mt)

    if HAVOK_CLASSES:
        for cls in reversed(HAVOK_CLASSES):
            bpy.utils.unregister_class(cls)
        bpy.types.TOPBAR_MT_file_import.remove(havok_menu_func_import)
        bpy.types.TOPBAR_MT_file_export.remove(havok_menu_func_export)

    del bpy.types.Scene.soulstruct_settings
    del bpy.types.Scene.soulstruct_game_enums
    del bpy.types.Scene.flver_import_settings
    del bpy.types.Scene.flver_export_settings
    del bpy.types.Scene.texture_export_settings
    del bpy.types.Scene.bake_lightmap_settings
    del bpy.types.Scene.navmesh_face_settings
    del bpy.types.Scene.mcg_draw_settings
    del bpy.types.Scene.mesh_move_settings
    del bpy.types.Scene.flver_settings

    for handler in LOAD_POST_HANDLERS:
        bpy.app.handlers.load_post.remove(handler)
    LOAD_POST_HANDLERS.clear()

    for handler in SPACE_VIEW_3D_HANDLERS:
        bpy.types.SpaceView3D.draw_handler_remove(handler, "WINDOW")
    SPACE_VIEW_3D_HANDLERS.clear()


if __name__ == "__main__":
    register()
