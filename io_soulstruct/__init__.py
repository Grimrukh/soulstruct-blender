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
# Note that Blender 4.1+ finally upgraded to Python 3.11, so we deploy two versions here.
addon_modules_path = str((Path(__file__).parent / "../io_soulstruct_lib").resolve())
if addon_modules_path not in sys.path:
    sys.path.append(addon_modules_path)

addon_modules_path_scipy = str((Path(__file__).parent / "../io_soulstruct_lib_311").resolve())
if addon_modules_path_scipy not in sys.path:
    sys.path.append(addon_modules_path_scipy)


def try_reload(_module_name: str):
    try:
        importlib.reload(sys.modules[_module_name])
    except (KeyError, ImportError):
        pass


# Reload all Soulstruct modules, then all modules in this add-on (except this script).
# NOTE: This is IMPORTANT when using 'Reload Scripts' in Blender, as it is otherwise prone to partial re-imports of
# Soulstruct that duplicate classes and cause wild bugs with `isinstance`, object ID equality, etc.

# TODO: `soulstruct` reload doesn't seem to be complete; `Vector has no attribute 'ndim'` appears.
# for module_name in list(sys.modules.keys()):
#     if "io_soulstruct" not in module_name and "soulstruct" in module_name.split(".")[0]:
#         try_reload(module_name)

for module_name in list(sys.modules.keys()):
    if module_name != "io_soulstruct" and "io_soulstruct" in module_name.split(".")[0]:  # don't reload THIS module
        try_reload(module_name)

import io_soulstruct._logging

from io_soulstruct.general import *
from io_soulstruct.misc_operators import *

from io_soulstruct.animation import *
from io_soulstruct.collision import *
from io_soulstruct.cutscene import *
from io_soulstruct.flver import *
from io_soulstruct.msb import *
from io_soulstruct.nav_graph import *
from io_soulstruct.navmesh import *
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import ViewSelectedAtDistanceZero


bl_info = {
    "name": "Soulstruct",
    "author": "Scott Mooney (Grimrukh)",
    "version": (2, 2, 3),
    "blender": (4, 2, 0),
    "location": "File > Import-Export",
    "description": "Import, manipulate, and export FromSoftware/Havok assets",
    "warning": "",
    "doc_url": "https://github.com/Grimrukh/soulstruct-blender",
    "support": "COMMUNITY",
    "category": "Import-Export",
}


# TODO: Add more operators to menu functions.


# noinspection PyUnusedLocal
def menu_func_import(self, context):
    layout = self.layout
    layout.operator(ImportFLVER.bl_idname, text="FLVER (.flver/.*bnd)")
    layout.operator(ImportNVM.bl_idname, text="NVM (.nvm/.nvmbnd)")
    layout.operator(ImportMCG.bl_idname, text="MCG (.mcg)")


# noinspection PyUnusedLocal
def menu_func_export(self, context):
    layout = self.layout
    layout.operator(ExportLooseFLVER.bl_idname, text="FLVER (.flver)")
    layout.operator(ExportFLVERIntoBinder.bl_idname, text="FLVER to Binder (.*bnd)")
    layout.operator(ExportLooseNVM.bl_idname, text="NVM (.nvm)")
    layout.operator(ExportNVMIntoBinder.bl_idname, text="NVM to Binder (.nvmbnd)")


# noinspection PyUnusedLocal
def menu_func_view3d_mt(self, context):
    layout = self.layout
    layout.operator(CopyMeshSelectionOperator.bl_idname, text="Copy Mesh Selection to Mesh")


# Classes to register.
CLASSES = (
    # region Basic
    SoulstructSettings,
    GlobalSettingsPanel,
    GlobalSettingsPanel_FLVERView,
    SelectGameMapDirectory,
    SelectProjectMapDirectory,
    SelectImageCacheDirectory,
    SelectCustomMTDBNDFile,
    SelectCustomMATBINBNDFile,
    LoadCollectionsFromBlend,
    # endregion

    # region Misc. Operators
    MeshMoveSettings,
    CopyMeshSelectionOperator,
    CutMeshSelectionOperator,
    BooleanMeshCut,
    ViewSelectedAtDistanceZero,
    # endregion

    # region FLVER / Materials / Textures
    ImportFLVER,
    ImportMapPieceFLVER,
    ImportCharacterFLVER,
    ImportObjectFLVER,
    ImportAssetFLVER,
    ImportEquipmentFLVER,
    FLVERImportSettings,

    HideAllDummiesOperator,
    ShowAllDummiesOperator,
    PrintGameTransform,

    FLVERExportSettings,
    ExportLooseFLVER,
    ExportFLVERIntoBinder,
    ExportMapPieceFLVERs,
    ExportCharacterFLVER,
    ExportObjectFLVER,
    ExportEquipmentFLVER,

    FLVERProps,
    FLVERDummyProps,
    FLVERGXItemProps,  # must be registered before `FLVERMaterialProps`
    FLVERMaterialProps,
    FLVERBoneProps,

    FLVERToolSettings,
    CopyToNewFLVER,
    RenameFLVER,
    SelectDisplayMaskID,
    SelectUnweightedVertices,
    SetSmoothCustomNormals,
    SetVertexAlpha,
    InvertVertexAlpha,
    BakeBonePoseToVertices,
    ReboneVertices,
    ActivateUVTexture0,
    ActivateUVTexture1,
    ActiveUVLightmap,
    FastUVUnwrap,
    RotateUVMapClockwise90,
    RotateUVMapCounterClockwise90,
    FindMissingTexturesInImageCache,
    SelectMeshChildren,

    MaterialToolSettings,
    SetMaterialTexture0,
    SetMaterialTexture1,
    AutoRenameMaterials,
    MergeFLVERMaterials,
    AddMaterialGXItem,
    RemoveMaterialGXItem,

    DDSTextureProps,
    ImportTextures,
    BakeLightmapSettings,
    BakeLightmapTextures,
    TextureExportSettings,
    DDSTexturePanel,

    FLVERPropsPanel,
    FLVERDummyPropsPanel,
    FLVERImportPanel,
    FLVERExportPanel,
    FLVERModelToolsPanel,
    FLVERMaterialToolsPanel,
    # FLVERLightmapsPanel,  # TODO: not quite ready
    FLVERUVMapsPanel,

    OBJECT_UL_flver_gx_item,
    FLVERMaterialPropsPanel,
    # endregion

    # region Havok Animation
    GlobalSettingsPanel_AnimationView,

    ImportHKXAnimation,
    ImportHKXAnimationWithBinderChoice,
    ImportCharacterHKXAnimation,
    ImportObjectHKXAnimation,
    ImportAssetHKXAnimation,
    ExportLooseHKXAnimation,
    ExportHKXAnimationIntoBinder,
    ExportCharacterHKXAnimation,
    ExportObjectHKXAnimation,

    AnimationImportSettings,
    AnimationExportSettings,

    ArmatureActionChoiceOperator,
    SelectArmatureActionOperator,
    AnimationImportExportPanel,
    AnimationToolsPanel,
    # endregion

    # region Havok Collision
    GlobalSettingsPanel_CollisionView,

    ImportHKXMapCollision,
    ImportHKXMapCollisionWithBinderChoice,
    ImportSelectedMapHKXMapCollision,

    ExportLooseHKXMapCollision,
    ExportHKXMapCollisionIntoBinder,
    ExportHKXMapCollisionToMap,
    MapCollisionImportExportPanel,
    MapCollisionToolsPanel,

    RenameCollision,
    GenerateCollisionFromMesh,
    SelectHiResFaces,
    SelectLoResFaces,

    MapCollisionProps,
    MapCollisionImportSettings,
    MapCollisionToolSettings,
    # endregion

    # region Cutscenes
    # TODO: Not quite ready.
    # GlobalSettingsPanel_CutsceneView,
    # ImportHKXCutscene,
    # ExportHKXCutscene,
    # CutsceneImportSettings,
    # CutsceneExportSettings,
    # CutsceneImportExportPanel,
    # endregion

    # region Navmesh
    GlobalSettingsPanel_NavmeshView,

    NVMProps,
    NVMFaceIndex,  # also used by `MCGNodeProps`
    NVMEventEntityProps,

    ImportNVM,
    ImportNVMWithBinderChoice,
    ImportSelectedMapNVM,
    ExportLooseNVM,
    ExportNVMIntoBinder,
    ExportNVMIntoSelectedMap,

    ImportNVMHKT,
    ImportNVMHKTWithBinderChoice,
    ImportNVMHKTFromNVMHKTBND,
    ImportAllNVMHKTsFromNVMHKTBND,
    ImportAllOverworldNVMHKTs,
    ImportAllDLCOverworldNVMHKTs,
    NVMHKTImportSettings,

    NVMNavmeshImportPanel,
    NVMNavmeshExportPanel,
    NVMNavmeshToolsPanel,
    NVMHKTImportPanel,
    NVMEventEntityPanel,
    OBJECT_UL_nvm_event_entity_triangle,
    NavmeshFaceSettings,
    RenameNavmesh,
    AddNVMFaceFlags,
    RemoveNVMFaceFlags,
    SetNVMFaceObstacleCount,
    ResetNVMFaceInfo,
    AddNVMEventEntityTriangleIndex,
    RemoveNVMEventEntityTriangleIndex,
    GenerateNavmeshFromCollision,
    # endregion

    # region Nav Graph (MCG)
    GlobalSettingsPanel_NavGraphView,

    ImportMCG,
    ImportSelectedMapMCG,
    ImportMCP,
    ImportSelectedMapMCP,
    ExportMCG,
    ExportMCGMCPToMap,
    MCGDrawSettings,

    AddMCGNodeNavmeshATriangleIndex,
    RemoveMCGNodeNavmeshATriangleIndex,
    AddMCGNodeNavmeshBTriangleIndex,
    RemoveMCGNodeNavmeshBTriangleIndex,
    JoinMCGNodesThroughNavmesh,
    SetNodeNavmeshTriangles,
    RefreshMCGNames,
    RecomputeEdgeCost,
    FindCheapestPath,
    AutoCreateMCG,

    MCGProps,
    MCGNodeProps,
    MCGEdgeProps,
    NavGraphComputeSettings,

    MCGPropsPanel,
    OBJECT_UL_nav_triangle,
    MCGNodePropsPanel,
    MCGEdgePropsPanel,
    MCGImportExportPanel,
    MCGDrawPanel,
    MCGToolsPanel,
    MCGGeneratorPanel,
    # endregion

    # region MSB
    GlobalSettingsPanel_MSBView,
    ImportMapMSB,
    ImportAnyMSB,
    ExportMapMSB,

    RegionDrawSettings,

    EnableAllImportModels,
    DisableAllImportModels,
    EnableSelectedNames,
    DisableSelectedNames,
    MSBPartCreationTemplates,
    CreateMSBPart,
    CreateMSBRegion,
    DuplicateMSBPartModel,
    BatchSetPartGroups,
    ApplyPartTransformToModel,
    CreateConnectCollision,
    MSBFindPartsPointer,
    FindMSBParts,
    FindEntityID,
    ColorMSBEvents,

    MSBPartProps,
    MSBMapPieceProps,
    MSBObjectProps,
    MSBAssetProps,
    MSBCharacterProps,
    MSBPlayerStartProps,
    MSBCollisionProps,
    MSBNavmeshProps,
    MSBConnectCollisionProps,
    MSBRegionProps,
    MSBImportSettings,
    MSBExportSettings,
    MSBToolSettings,

    MSBImportPanel,
    MSBExportPanel,
    MSBToolsPanel,
    MSBPartPanel,

    MSBMapPiecePartPanel,
    MSBObjectPartPanel,
    MSBCharacterPartPanel,
    MSBPlayerStartPartPanel,
    MSBCollisionPartPanel,
    MSBNavmeshPartPanel,
    MSBConnectCollisionPartPanel,
    MSBRegionPanel,
    MSBEventPanel,
    MSBLightEventPanel,
    MSBSoundEventPanel,
    MSBVFXEventPanel,
    MSBWindEventPanel,
    MSBTreasureEventPanel,
    MSBSpawnerEventPanel,
    MSBMessageEventPanel,
    MSBObjActEventPanel,
    MSBSpawnPointEventPanel,
    MSBMapOffsetEventPanel,
    MSBNavigationEventPanel,
    MSBEnvironmentEventPanel,
    MSBNPCInvasionEventPanel,

    MSBEventProps,
    MSBLightEventProps,
    MSBSoundEventProps,
    MSBVFXEventProps,
    MSBWindEventProps,
    MSBTreasureEventProps,
    MSBSpawnerEventProps,
    MSBMessageEventProps,
    MSBObjActEventProps,
    MSBSpawnPointEventProps,
    MSBMapOffsetEventProps,
    MSBNavigationEventProps,
    MSBEnvironmentEventProps,
    MSBNPCInvasionEventProps,
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
    flver_import_settings=FLVERImportSettings,
    flver_export_settings=FLVERExportSettings,
    texture_export_settings=TextureExportSettings,
    bake_lightmap_settings=BakeLightmapSettings,
    flver_tool_settings=FLVERToolSettings,
    material_tool_settings=MaterialToolSettings,
    mesh_move_settings=MeshMoveSettings,
    map_collision_import_settings=MapCollisionImportSettings,
    map_collision_tool_settings=MapCollisionToolSettings,
    navmesh_face_settings=NavmeshFaceSettings,
    nav_graph_compute_settings=NavGraphComputeSettings,
    nvmhkt_import_settings=NVMHKTImportSettings,
    mcg_draw_settings=MCGDrawSettings,
    msb_import_settings=MSBImportSettings,
    msb_export_settings=MSBExportSettings,
    msb_part_creation_templates=MSBPartCreationTemplates,
    find_msb_parts_pointer=MSBFindPartsPointer,
    msb_tool_settings=MSBToolSettings,
    region_draw_settings=RegionDrawSettings,
    animation_import_settings=AnimationImportSettings,
    animation_export_settings=AnimationExportSettings,
    # TODO: Cutscene disabled.
    # cutscene_import_settings=CutsceneImportSettings,
    # cutscene_export_settings=CutsceneExportSettings,
)


OBJECT_POINTERS = dict(
    FLVER=FLVERProps,
    FLVER_DUMMY=FLVERDummyProps,

    COLLISION=MapCollisionProps,  # currently empty

    NVM=NVMProps,  # currently empty
    NVM_EVENT_ENTITY=NVMEventEntityProps,
    MCG=MCGProps,
    MCG_NODE=MCGNodeProps,
    MCG_EDGE=MCGEdgeProps,

    MSB_PART=MSBPartProps,
    MSB_MAP_PIECE=MSBMapPieceProps,
    MSB_OBJECT=MSBObjectProps,
    MSB_ASSET=MSBAssetProps,
    MSB_CHARACTER=MSBCharacterProps,
    MSB_PLAYER_START=MSBPlayerStartProps,
    MSB_COLLISION=MSBCollisionProps,
    MSB_NAVMESH=MSBNavmeshProps,
    MSB_CONNECT_COLLISION=MSBConnectCollisionProps,

    MSB_REGION=MSBRegionProps,
    # No real subtypes yet.

    MSB_EVENT=MSBEventProps,
    MSB_LIGHT=MSBLightEventProps,
    MSB_SOUND=MSBSoundEventProps,
    MSB_VFX=MSBVFXEventProps,
    MSB_WIND=MSBWindEventProps,
    MSB_TREASURE=MSBTreasureEventProps,
    MSB_SPAWNER=MSBSpawnerEventProps,
    MSB_MESSAGE=MSBMessageEventProps,
    MSB_OBJ_ACT=MSBObjActEventProps,
    MSB_SPAWN_POINT=MSBSpawnPointEventProps,
    MSB_MAP_OFFSET=MSBMapOffsetEventProps,
    MSB_NAVIGATION=MSBNavigationEventProps,
    MSB_ENVIRONMENT=MSBEnvironmentEventProps,
    MSB_NPC_INVASION=MSBNPCInvasionEventProps,
)


MATERIAL_POINTERS = dict(
    FLVER_MATERIAL=FLVERMaterialProps,
)


IMAGE_POINTERS = dict(
    DDS_TEXTURE=DDSTextureProps,
)


EDIT_BONE_POINTERS = dict(
    FLVER_BONE=FLVERBoneProps,
)


SCENE_ATTRIBUTES = []
OBJECT_ATTRIBUTES = []
MATERIAL_ATTRIBUTES = []
IMAGE_ATTRIBUTES = []
EDIT_BONE_ATTRIBUTES = []

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

    # region Soulstruct Type Extension

    bpy.types.Object.soulstruct_type = bpy.props.EnumProperty(
        name="Soulstruct Object Type",
        description="Type of Soulstruct object that this Blender Object represents (INTERNAL)",
        items=[
            (SoulstructType.NONE, "None", "Not a Soulstruct typed object"),

            (SoulstructType.FLVER, "FLVER", "FLVER mesh model"),  # data-block 'owner'; NOT an MSB Part instance object
            (SoulstructType.FLVER_DUMMY, "FLVER Dummy", "FLVER dummy object"),
            # All Materials and Bones have FLVER properties exposed.

            (SoulstructType.COLLISION, "Collision", "Map collision mesh model"),

            (SoulstructType.NAVMESH.name, "Navmesh", "Navmesh mesh model"),
            (SoulstructType.NVM_EVENT_ENTITY.name, "NVM Event Entity", ""),
            (SoulstructType.MCG.name, "MCG", "MCG navigation graph (DS1)"),
            (SoulstructType.MCG_NODE.name, "MCG Node", "MCG navigation graph node (DS1)"),
            (SoulstructType.MCG_EDGE.name, "MCG Edge", "MCG navigation graph edge (DS1)"),

            (SoulstructType.MSB_PART, "MSB Part", "MSB part object"),  # NOT a FLVER data-block owner
            (SoulstructType.MSB_REGION, "MSB Region", "MSB region object"),
            (SoulstructType.MSB_EVENT, "MSB Event", "MSB event object"),
        ]
    )
    OBJECT_ATTRIBUTES.append("soulstruct_type")

    for prop_name, prop_type in OBJECT_POINTERS.items():
        setattr(bpy.types.Object, prop_name, bpy.props.PointerProperty(type=prop_type))
        OBJECT_ATTRIBUTES.append(prop_name)

    for prop_name, prop_type in MATERIAL_POINTERS.items():
        setattr(bpy.types.Material, prop_name, bpy.props.PointerProperty(type=prop_type))
        MATERIAL_ATTRIBUTES.append(prop_name)

    for prop_name, prop_type in IMAGE_POINTERS.items():
        setattr(bpy.types.Image, prop_name, bpy.props.PointerProperty(type=prop_type))
        IMAGE_ATTRIBUTES.append(prop_name)

    for prop_name, prop_type in EDIT_BONE_POINTERS.items():
        setattr(bpy.types.EditBone, prop_name, bpy.props.PointerProperty(type=prop_type))
        EDIT_BONE_ATTRIBUTES.append(prop_name)

    bpy.app.handlers.load_post.append(load_handler)
    LOAD_POST_HANDLERS.append(load_handler)

    SPACE_VIEW_3D_HANDLERS.append(
        bpy.types.SpaceView3D.draw_handler_add(draw_dummy_ids, (), "WINDOW", "POST_PIXEL")
    )

    SPACE_VIEW_3D_HANDLERS.append(
        bpy.types.SpaceView3D.draw_handler_add(update_mcg_draw_caches, (), "WINDOW", "POST_VIEW")
    )
    SPACE_VIEW_3D_HANDLERS.append(
        bpy.types.SpaceView3D.draw_handler_add(draw_mcg_nodes, (), "WINDOW", "POST_VIEW")
    )
    SPACE_VIEW_3D_HANDLERS.append(
        bpy.types.SpaceView3D.draw_handler_add(draw_mcg_edges, (), "WINDOW", "POST_VIEW")
    )
    SPACE_VIEW_3D_HANDLERS.append(
        bpy.types.SpaceView3D.draw_handler_add(draw_mcg_edge_cost_labels, (), "WINDOW", "POST_PIXEL")
    )

    SPACE_VIEW_3D_HANDLERS.append(
        bpy.types.SpaceView3D.draw_handler_add(draw_msb_regions, (), "WINDOW", "POST_VIEW")
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

    for prop_name in OBJECT_ATTRIBUTES:
        delattr(bpy.types.Object, prop_name)
    OBJECT_ATTRIBUTES.clear()

    for prop_name in MATERIAL_ATTRIBUTES:
        delattr(bpy.types.Material, prop_name)
    MATERIAL_ATTRIBUTES.clear()

    for prop_name in IMAGE_ATTRIBUTES:
        delattr(bpy.types.Image, prop_name)
    IMAGE_ATTRIBUTES.clear()

    for prop_name in EDIT_BONE_ATTRIBUTES:
        delattr(bpy.types.EditBone, prop_name)
    EDIT_BONE_ATTRIBUTES.clear()

    for handler in LOAD_POST_HANDLERS:
        bpy.app.handlers.load_post.remove(handler)
    LOAD_POST_HANDLERS.clear()

    for handler in SPACE_VIEW_3D_HANDLERS:
        bpy.types.SpaceView3D.draw_handler_remove(handler, "WINDOW")
    SPACE_VIEW_3D_HANDLERS.clear()


if __name__ == "__main__":
    register()
