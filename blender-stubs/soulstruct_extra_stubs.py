from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from io_soulstruct import *


class Scene:
    soulstruct_settings: SoulstructSettings
    flver_import_settings: FLVERImportSettings
    flver_export_settings: FLVERExportSettings
    texture_export_settings: TextureExportSettings
    bake_lightmap_settings: BakeLightmapSettings
    flver_tool_settings: FLVERToolSettings
    flver_material_settings: FLVERMaterialSettings
    material_tool_settings: MaterialToolSettings
    map_collision_import_settings: MapCollisionImportSettings
    map_collision_tool_settings: MapCollisionToolSettings
    navmesh_face_settings: NavmeshFaceSettings
    nav_graph_compute_settings: NavGraphComputeSettings
    nvmhkt_import_settings: NVMHKTImportSettings
    mcg_draw_settings: MCGDrawSettings
    msb_import_settings: MSBImportSettings
    msb_export_settings: MSBExportSettings
    msb_part_creation_templates: MSBPartCreationTemplates
    find_msb_parts_pointer: FindMSBPartsPointer
    msb_tool_settings: MSBToolSettings
    region_draw_settings: RegionDrawSettings
    animation_import_settings: AnimationImportSettings
    animation_export_settings: AnimationExportSettings
    # TODO: Cutscene disabled.
    # cutscene_import_settings: CutsceneImportSettings
    # cutscene_export_settings: CutsceneExportSettings

    map_progress_settings: MapProgressSettings
    material_debug_settings: MaterialDebugSettings


class Object:
    FLVER: FLVERProps
    FLVER_DUMMY: FLVERDummyProps

    COLLISION: MapCollisionProps  # currently empty

    NVM: NVMProps  # currently empty
    NVM_EVENT_ENTITY: NVMEventEntityProps
    MCG: MCGProps
    MCG_NODE: MCGNodeProps
    MCG_EDGE: MCGEdgeProps

    MSB_PART: MSBPartProps
    MSB_MAP_PIECE: MSBMapPieceProps
    MSB_OBJECT: MSBObjectProps
    MSB_ASSET: MSBAssetProps
    MSB_CHARACTER: MSBCharacterProps
    MSB_PLAYER_START: MSBPlayerStartProps
    MSB_COLLISION: MSBCollisionProps
    MSB_NAVMESH: MSBNavmeshProps
    MSB_CONNECT_COLLISION: MSBConnectCollisionProps

    MSB_REGION: MSBRegionProps
    # No real subtypes yet.

    MSB_EVENT: MSBEventProps
    MSB_LIGHT: MSBLightEventProps
    MSB_SOUND: MSBSoundEventProps
    MSB_VFX: MSBVFXEventProps
    MSB_WIND: MSBWindEventProps
    MSB_TREASURE: MSBTreasureEventProps
    MSB_SPAWNER: MSBSpawnerEventProps
    MSB_MESSAGE: MSBMessageEventProps
    MSB_OBJ_ACT: MSBObjActEventProps
    MSB_SPAWN_POINT: MSBSpawnPointEventProps
    MSB_MAP_OFFSET: MSBMapOffsetEventProps
    MSB_NAVIGATION: MSBNavigationEventProps
    MSB_ENVIRONMENT: MSBEnvironmentEventProps
    MSB_NPC_INVASION: MSBNPCInvasionEventProps

    map_progress: MapProgressProps


class Material:
    FLVER_MATERIAL: FLVERMaterialProps


class Image:
    DDS_TEXTURE: DDSTextureProps


class Bone:
    FLVER_BONE: FLVERBoneProps
