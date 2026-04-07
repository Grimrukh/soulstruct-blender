"""Blender add-ons for importing/export formats from FromSoftware games.

Primarily tested and maintained for Dark Souls Remastered. Other games and file versions may gradually be supported.

Requires:
    soulstruct (most `soulstruct.*` packages)
    soulstruct-havok (`soulstruct.havok` package)

On startup this script verifies that the exact required versions of `soulstruct` and `soulstruct-havok` are
installed (via `importlib.metadata`).  If they are missing or at the wrong version it will pip-install them:
  1. From the bundled `io_soulstruct_lib/` directory (present in release zip builds).
  2. From PyPI, as a fallback (for users who installed the add-on without the bundled libraries).

Editable (development) installs are fully supported — as long as the installed version string matches the required
version declared below, no reinstall is triggered.

Any stale `sys.path` entries pointing to a different Blender version's `addons/modules` are cleaned up before
the version check to prevent shadowing by older installs.
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


from .soulstruct.blender.general import *
from .soulstruct.blender.misc import *

from .soulstruct.blender.animation import *
from .soulstruct.blender.collision import *
from .soulstruct.blender.cutscene import *
from .soulstruct.blender.flver import *
from .soulstruct.blender.msb import *
from .soulstruct.blender.nav_graph import *
from .soulstruct.blender.navmesh import *
from .soulstruct.blender.types import SoulstructType, SoulstructCollectionType
from .soulstruct.blender.utilities import ViewSelectedAtDistanceZero

from .soulstruct.blender.experimental import *


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

    FLVERExportSettings,
    ExportAnyFLVER,
    ExportFLVERIntoAnyBinder,
    ExportMapPieceFLVERs,
    ExportCharacterFLVER,
    ExportObjectFLVER,
    ExportEquipmentFLVER,

    FLVERSubmeshProps,
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
    ActivateUVMap,
    FastUVUnwrap,
    FastUVUnwrapIslands,
    RotateUVMapClockwise90,
    RotateUVMapCounterClockwise90,
    FindMissingTexturesInImageCache,
    SelectMeshChildren,
    SyncMSBPartArmatures,
    ClearFLVERSubmeshProperties,
    AddFLVERSubmeshProperties,

    FLVERMaterialSettings,
    MaterialToolSettings,
    SetMaterialTexture0,
    SetMaterialTexture1,
    AutoRenameMaterials,
    MergeFLVERMaterials,
    AddMaterialGXItem,
    RemoveMaterialGXItem,
    RegenerateFLVERMaterialShaders,

    DDSTextureProps,
    ImportTextures,
    BakeLightmapSettings,
    BakeLightmapTextures,
    TextureExportSettings,
    DDSTexturePanel,

    FLVERPropsPanel,
    FLVERDummyPropsPanel,
    FLVERBonePropsPanel,
    FLVERImportPanel,
    FLVERExportPanel,
    FLVERMaterialSettingsPanel,
    FLVERModelToolsPanel,
    FLVERMaterialToolsPanel,
    # FLVERLightmapsPanel,  # TODO: not quite ready
    FLVERUVMapsPanel,

    FLVERGXItemUIList,
    FLVERMaterialPropsPanel,
    # endregion

    # region Havok Animation
    GlobalSettingsPanel_AnimationView,

    ImportAnyHKXAnimation,
    ImportHKXAnimationWithBinderChoice,
    ImportCharacterHKXAnimation,
    ImportObjectHKXAnimation,
    ImportAssetHKXAnimation,
    ExportAnyHKXAnimation,
    ExportHKXAnimationIntoAnyBinder,
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

    ImportAnyHKXMapCollision,
    ImportHKXMapCollisionWithBinderChoice,
    ImportMapHKXMapCollision,

    ExportAnyHKXMapCollision,
    ExportHKXMapCollisionIntoAnyBinder,
    ExportMapHKXMapCollision,
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
    GlobalSettingsPanel_CutsceneView,
    ImportHKXCutscene,
    ExportHKXCutscene,
    CutsceneImportSettings,
    CutsceneExportSettings,
    CutsceneImportExportPanel,
    # endregion

    # region Navmesh
    GlobalSettingsPanel_NavmeshView,

    NVMProps,
    NVMFaceIndex,  # also used by `MCGNodeProps`
    NVMEventEntityProps,

    ImportAnyNVM,
    ImportNVMWithBinderChoice,
    ImportMapNVM,
    ExportAnyNVM,
    ExportNVMIntoAnyBinder,
    ExportMapNVM,

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
    NVMEventEntityTriangleUIList,
    NavmeshFaceSettings,
    RenameNavmesh,
    AddNVMFaceFlags,
    RemoveNVMFaceFlags,
    SetNVMFaceFlags,
    SetNVMFaceObstacleCount,
    ResetNVMFaceInfo,
    AddNVMEventEntityTriangleIndex,
    RemoveNVMEventEntityTriangleIndex,
    GenerateNavmeshFromCollision,
    # endregion

    # region Nav Graph (MCG)
    GlobalSettingsPanel_NavGraphView,

    ImportAnyMCG,
    ImportMapMCG,
    ImportAnyMCP,
    ImportMapMCP,
    ExportAnyMCGMCP,
    ExportMapMCGMCP,
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
    NavTriangleUIList,
    MCGNodePropsPanel,
    MCGEdgePropsPanel,
    NavGraphImportExportPanel,
    NavGraphDrawPanel,
    NavGraphToolsPanel,
    MCGGeneratorPanel,
    # endregion

    # region MSB
    GlobalSettingsPanel_MSBView,
    ImportMapMSB,
    ImportAnyMSB,
    ExportMapMSB,
    ExportAnyMSB,

    RegionDrawSettings,

    EnableAllImportModels,
    DisableAllImportModels,
    EnableSelectedNames,
    DisableSelectedNames,
    MSBPartCreationTemplates,
    CreateMSBPart,
    CreateMSBRegion,
    CreateMSBEnvironmentEvent,
    DuplicateMSBPartModel,
    BatchSetPartGroups,
    CopyDrawGroups,
    ApplyPartTransformToModel,
    CreateConnectCollision,
    MSBFindPartsPointer,
    FindMSBParts,
    FindEntityID,
    ColorMSBEvents,
    RestoreActivePartInitialTransform,
    RestoreSelectedPartsInitialTransforms,
    UpdateActiveMSBPartInitialTransform,
    UpdateSelectedPartsInitialTransforms,

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

    # region Misc. Operators
    CopyMeshSelectionOperator,
    CutMeshSelectionOperator,
    BooleanMeshCut,
    ApplyLocalMatrixToMesh,
    ScaleMeshIslands,
    SelectActiveMeshVerticesNearSelected,
    ConvexHullOnEachMeshIsland,
    SetActiveFaceNormalUpward,
    SpawnObjectIntoMeshAtFaces,
    WeightVerticesWithFalloff,
    ApplyModifierNonSingleUser,
    PrintGameTransform,

    ShowCollectionOperator,
    HideCollectionOperator,

    GlobalSettingsPanel_MiscView,
    MiscSoulstructMeshOperatorsPanel,
    MiscSoulstructCollectionOperatorsPanel,
    MiscSoulstructOtherOperatorsPanel,
    # endregion

    # region Utility Operators
    ViewSelectedAtDistanceZero,
    # endregion

    # region Experimental
    MapProgressSettings,
    MapProgressProps,
    MapProgressSelectObject,
    SetMapProgressState,
    ToggleMapProgressOverlay,
    ExportMapProgressCSV,
    MapProgressBulkInit,
    RefreshMapProgressVisuals,
    MapProgressPanel,

    MaterialDebugSettings,
    AddDebugNodeGroupToMaterials,
    RemoveDebugNodeGroupFromMaterials,
    MaterialDebugPanel,
    # endregion
)


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


# TODO: Put all of these pointers under a common group like `context.scene.soulstruct` for the add-on.
SCENE_POINTERS = dict(
    soulstruct_settings=SoulstructSettings,  # TODO: -> `context.scene.soulstruct.general_settings`
    flver_import_settings=FLVERImportSettings,
    flver_export_settings=FLVERExportSettings,
    texture_export_settings=TextureExportSettings,
    bake_lightmap_settings=BakeLightmapSettings,
    flver_tool_settings=FLVERToolSettings,
    flver_material_settings=FLVERMaterialSettings,
    material_tool_settings=MaterialToolSettings,
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
    cutscene_import_settings=CutsceneImportSettings,
    cutscene_export_settings=CutsceneExportSettings,

    # EXPERIMENTAL
    map_progress_settings=MapProgressSettings,
    material_debug_settings=MaterialDebugSettings,
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

    map_progress=MapProgressProps,
)


MATERIAL_POINTERS = dict(
    FLVER_MATERIAL=FLVERMaterialProps,
)


IMAGE_POINTERS = dict(
    DDS_TEXTURE=DDSTextureProps,
)


BONE_POINTERS = dict(
    FLVER_BONE=FLVERBoneProps,
)


SCENE_ATTRIBUTES = []
OBJECT_ATTRIBUTES = []
COLLECTION_ATTRIBUTES = []
MATERIAL_ATTRIBUTES = []
IMAGE_ATTRIBUTES = []
BONE_ATTRIBUTES = []

LOAD_POST_HANDLERS = []
SPACE_VIEW_3D_HANDLERS = []
DEPSGRAPH_UPDATE_POST_HANDLERS = []


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
            (SoulstructType.MSB_MODEL_PLACEHOLDER, "MSB Model (Placeholder)", "MSB model placeholder object"),
        ]
    )
    OBJECT_ATTRIBUTES.append("soulstruct_type")

    bpy.types.Collection.soulstruct_type = bpy.props.EnumProperty(
        name="Soulstruct Collection Type",
        description="Type of Soulstruct collection that this Blender Collection represents (INTERNAL)",
        items=[
            (SoulstructCollectionType.NONE, "None", "Not a Soulstruct typed collection"),

            (SoulstructCollectionType.MSB, "MSB", "MSB collection"),
        ]
    )
    COLLECTION_ATTRIBUTES.append("soulstruct_type")

    for prop_name, prop_type in OBJECT_POINTERS.items():
        setattr(bpy.types.Object, prop_name, bpy.props.PointerProperty(type=prop_type))
        OBJECT_ATTRIBUTES.append(prop_name)

    for prop_name, prop_type in MATERIAL_POINTERS.items():
        setattr(bpy.types.Material, prop_name, bpy.props.PointerProperty(type=prop_type))
        MATERIAL_ATTRIBUTES.append(prop_name)

    for prop_name, prop_type in IMAGE_POINTERS.items():
        setattr(bpy.types.Image, prop_name, bpy.props.PointerProperty(type=prop_type))
        IMAGE_ATTRIBUTES.append(prop_name)

    for prop_name, prop_type in BONE_POINTERS.items():
        setattr(bpy.types.Bone, prop_name, bpy.props.PointerProperty(type=prop_type))
        BONE_ATTRIBUTES.append(prop_name)

    # FLVER dummy draw handler
    SPACE_VIEW_3D_HANDLERS.append(
        bpy.types.SpaceView3D.draw_handler_add(draw_dummy_ids, (), "WINDOW", "POST_PIXEL")
    )

    # MCG draw handlers
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

    # MSB region draw handler
    SPACE_VIEW_3D_HANDLERS.append(
        bpy.types.SpaceView3D.draw_handler_add(draw_msb_regions, (), "WINDOW", "POST_VIEW")
    )

    # FLVER submesh sync handler
    bpy.app.handlers.depsgraph_update_post.append(flver_submesh_sync_handler)
    DEPSGRAPH_UPDATE_POST_HANDLERS.append(flver_submesh_sync_handler)

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

    for prop_name in COLLECTION_ATTRIBUTES:
        delattr(bpy.types.Collection, prop_name)
    COLLECTION_ATTRIBUTES.clear()

    for prop_name in MATERIAL_ATTRIBUTES:
        delattr(bpy.types.Material, prop_name)
    MATERIAL_ATTRIBUTES.clear()

    for prop_name in IMAGE_ATTRIBUTES:
        delattr(bpy.types.Image, prop_name)
    IMAGE_ATTRIBUTES.clear()

    for prop_name in BONE_ATTRIBUTES:
        delattr(bpy.types.Bone, prop_name)
    BONE_ATTRIBUTES.clear()

    for handler in LOAD_POST_HANDLERS:
        bpy.app.handlers.load_post.remove(handler)
    LOAD_POST_HANDLERS.clear()

    for handler in SPACE_VIEW_3D_HANDLERS:
        # All added to WINDOW region.
        bpy.types.SpaceView3D.draw_handler_remove(handler, "WINDOW")
    SPACE_VIEW_3D_HANDLERS.clear()

    for handler in DEPSGRAPH_UPDATE_POST_HANDLERS:
        bpy.app.handlers.depsgraph_update_post.remove(handler)
    DEPSGRAPH_UPDATE_POST_HANDLERS.clear()


if __name__ == "__main__":
    register()
