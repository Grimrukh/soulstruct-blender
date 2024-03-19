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

# TODO: I suspect that 'Reload Scripts' in Blender eventually breaks the `colorama` module, causing a recursion limit.

# Reload all Soulstruct modules, then all modules in this add-on (except this script).
# NOTE: This is IMPORTANT when using 'Reload Scripts' in Blender, as it is otherwise prone to partial re-imports of
# Soulstruct that duplicate classes and cause wild bugs with `isinstance`, etc.
for module_name in list(sys.modules.keys()):
    if "io_soulstruct" not in module_name and "soulstruct" in module_name.split(".")[0]:
        importlib.reload(sys.modules[module_name])
for module_name in list(sys.modules.keys()):
    if module_name != "io_soulstruct" and "io_soulstruct" in module_name.split(".")[0]:  # don't reload THIS module
        importlib.reload(sys.modules[module_name])

from io_soulstruct.flver import *
from io_soulstruct.msb import *
from io_soulstruct.navmesh import *
from io_soulstruct.misc_operators import *
from io_soulstruct.general import *

# TODO: Currently asserting that `soulstruct_havok` is installed, but this is not necessary for all add-ons.
from io_soulstruct.havok.hkx_map_collision import *
from io_soulstruct.havok.hkx_animation import *
from io_soulstruct.havok.hkx_cutscene import *

bl_info = {
    "name": "Soulstruct",
    "author": "Scott Mooney (Grimrukh)",
    "version": (1, 5, 0),
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
    # region Basic
    SoulstructSettings,
    SoulstructGameEnums,
    GlobalSettingsPanel,
    GlobalSettingsPanel_FLVERView,
    SelectGameDirectory,
    SelectProjectDirectory,
    SelectMapDirectory,
    SelectPNGCacheDirectory,
    SelectCustomMTDBNDFile,
    SelectCustomMATBINBNDFile,
    ClearCachedLists,
    # endregion

    # region Misc. Operators
    MeshMoveSettings,
    CopyMeshSelectionOperator,
    CutMeshSelectionOperator,
    # endregion

    # region FLVER / Materials / Textures
    ImportFLVER,
    ImportMapPieceFLVER,
    ImportCharacterFLVER,
    ImportObjectFLVER,
    ImportEquipmentFLVER,
    FLVERImportSettings,

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

    FLVERToolSettings,
    CopyToNewFLVER,
    DeleteFLVER,
    DeleteFLVERAndData,
    CreateFLVERInstance,
    RenameFLVER,
    CreateEmptyMapPieceFLVER,
    SetSmoothCustomNormals,
    SetVertexAlpha,
    InvertVertexAlpha,
    MaterialToolSettings,
    SetMaterialTexture0,
    SetMaterialTexture1,
    ActivateUVTexture0,
    ActivateUVTexture1,
    ActiveUVLightmap,
    FindMissingTexturesInPNGCache,
    SelectMeshChildren,

    ImportTextures,
    BakeLightmapSettings,
    BakeLightmapTextures,
    TextureExportSettings,

    FLVERImportPanel,
    FLVERExportPanel,
    TextureExportSettingsPanel,
    # FLVERLightmapsPanel,  # TODO: not quite ready
    FLVERMeshToolsPanel,
    FLVERMaterialToolsPanel,
    FLVERDummyToolsPanel,
    FLVEROtherToolsPanel,
    FLVERUVMapsPanel,
    # endregion

    # region Havok
    GlobalSettingsPanel_HavokView,

    ImportHKXMapCollision,
    ImportHKXMapCollisionWithBinderChoice,
    ImportHKXMapCollisionFromHKXBHD,
    HKXMapCollisionImportSettings,

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
    HKX_COLLISION_PT_hkx_map_collisions,

    SelectHiResFaces,
    SelectLoResFaces,

    # TODO: Cutscene operators need a bit more work.
    # ImportHKXCutscene,
    # ExportHKXCutscene,
    # HKX_CUTSCENE_PT_hkx_cutscene_tools,
    # endregion

    # region Navmesh
    GlobalSettingsPanel_NavmeshView,
    ImportNVM,
    ImportNVMWithBinderChoice,
    ImportNVMFromNVMBND,
    ExportLooseNVM,
    ExportNVMIntoBinder,
    ExportNVMIntoNVMBND,

    ImportMCP,
    QuickImportMCP,
    ImportMCG,
    QuickImportMCG,
    ExportMCG,
    ExportMCGMCPToMap,
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
    ResetNVMFaceInfo,
    MCGDrawSettings,
    # endregion

    # region MSB
    GlobalSettingsPanel_MSBView,
    MSBImportSettings,
    ImportMSBMapPiece,
    ImportAllMSBMapPieces,
    ImportMSBMapCollision,
    ImportAllMSBMapCollisions,
    ImportMSBNavmesh,
    ImportAllMSBNavmeshes,
    ImportMSBCharacter,
    ImportAllMSBCharacters,
    ImportMSBPoint,
    ImportMSBVolume,
    ImportAllMSBPoints,
    ImportAllMSBVolumes,
    RegionDrawSettings,

    MSBExportSettings,
    ExportMSBMapPieces,
    ExportMSBCollisions,
    ExportMSBNavmeshes,
    ExportCompleteMapNavigation,

    MSBImportPanel,
    MSBExportPanel,
    MSBToolsPanel,
    MSBRegionPanel,
    # endregion
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


SCENE_POINTERS = dict(
    soulstruct_settings=SoulstructSettings,
    soulstruct_game_enums=SoulstructGameEnums,
    flver_import_settings=FLVERImportSettings,
    flver_export_settings=FLVERExportSettings,
    texture_export_settings=TextureExportSettings,
    bake_lightmap_settings=BakeLightmapSettings,
    flver_tool_settings=FLVERToolSettings,
    material_tool_settings=MaterialToolSettings,
    mesh_move_settings=MeshMoveSettings,
    hkx_map_collision_import_settings=HKXMapCollisionImportSettings,
    navmesh_face_settings=NavmeshFaceSettings,
    mcg_draw_settings=MCGDrawSettings,
    msb_import_settings=MSBImportSettings,
    msb_export_settings=MSBExportSettings,
    region_draw_settings=RegionDrawSettings,
)


SCENE_ATTRIBUTES = []
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

    for prop_name, prop_type in SCENE_POINTERS.items():
        setattr(bpy.types.Scene, prop_name, bpy.props.PointerProperty(type=prop_type))
        SCENE_ATTRIBUTES.append(prop_name)

    # region Other Type Extensions
    bpy.types.Object.region_shape = bpy.props.EnumProperty(
        items=[
            ("None", "None", "Not a region object"),
            ("Point", "Point", "Point with location and rotation only"),
            # NOTE: 2D region shapes not supported (never used in game AFAIK).
            ("Sphere", "Sphere", "Volume region defined by radius (max of X/Y/Z scale)"),
            ("Cylinder", "Cylinder", "Volume region defined by radius (max of X/Y scale) and height (Z scale)"),
            ("Box", "Box", "Volume region defined by X/Y/Z scale"),
        ],
        name="Region Shape",
        default="None",
    )
    # endregion

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

    SPACE_VIEW_3D_HANDLERS.append(
        bpy.types.SpaceView3D.draw_handler_add(draw_region_volumes, (), "WINDOW", "POST_VIEW")
    )

    bpy.types.TOPBAR_MT_file_import.append(havok_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(havok_menu_func_export)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.VIEW3D_MT_object.remove(menu_func_view3d_mt)
    bpy.types.TOPBAR_MT_file_import.remove(havok_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(havok_menu_func_export)

    for prop_name in SCENE_ATTRIBUTES:
        delattr(bpy.types.Scene, prop_name)
    SCENE_ATTRIBUTES.clear()

    # noinspection PyUnresolvedReferences
    del bpy.types.Object.region_shape

    for handler in LOAD_POST_HANDLERS:
        bpy.app.handlers.load_post.remove(handler)
    LOAD_POST_HANDLERS.clear()

    for handler in SPACE_VIEW_3D_HANDLERS:
        bpy.types.SpaceView3D.draw_handler_remove(handler, "WINDOW")
    SPACE_VIEW_3D_HANDLERS.clear()


if __name__ == "__main__":
    register()
