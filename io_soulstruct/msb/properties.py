"""Property groups for all MSB subtypes in all games.

These groups are added as extension RNA properties of `bpy.types.Object` upon add-on registration.

Note that all games for all properties are POOLED here. The add-on's panels will selectively display only the properties
that are supported by the current game. The alternative -- a different property group for each game -- would be a mess
and would make it very hard to port entries between games, which is a core goal of Soulstruct for Blender.

In cases where properties conflict between games (e.g. they are extended or the enum changes), then per-game versions of
that property will be defined in the group, and `update` callbacks will be used to synchronize them where possible to
aid porting.
"""
from __future__ import annotations

__all__ = [
    "MSBPartSubtype",
    "MSBPartProps",
    "MSBMapPieceProps",
    "MSBObjectProps",
    "MSBAssetProps",
    "MSBCharacterProps",
    "MSBPlayerStartProps",
    "MSBCollisionProps",
    "MSBNavmeshProps",
    "MSBConnectCollisionProps",

    "MSBRegionSubtype",
    "MSBRegionProps",

    "MSBEventSubtype",
    "MSBEventProps",
    "MSBLightEventProps",
    "MSBSoundEventProps",
    "MSBVFXEventProps",
    "MSBWindEventProps",
    "MSBTreasureEventProps",
    "MSBSpawnerEventProps",
    "MSBMessageEventProps",
    "MSBObjActEventProps",
    "MSBSpawnPointEventProps",
    "MSBMapOffsetEventProps",
    "MSBNavigationEventProps",
    "MSBEnvironmentEventProps",
    "MSBNPCInvasionEventProps",

    "MSBImportSettings",
    "MSBExportSettings",
    "MSBToolSettings",
]

import re
import typing as tp
from enum import StrEnum
from fnmatch import fnmatch

import bpy
from io_soulstruct.types import SoulstructType
from soulstruct.base.maps.msb.region_shapes import RegionShapeType
from soulstruct.darksouls1ptde.maps.enums import CollisionHitFilter
from .utilities import *


class MSBPartSubtype(StrEnum):
    """Union of Part subtypes across all games."""
    MapPiece = "MSB_MAP_PIECE"
    Object = "MSB_OBJECT"
    Asset = "MSB_ASSET"
    Character = "MSB_CHARACTER"
    PlayerStart = "MSB_PLAYER_START"
    Collision = "MSB_COLLISION"
    Navmesh = "MSB_NAVMESH"
    ConnectCollision = "MSB_CONNECT_COLLISION"
    Other = "MSB_OTHER"

    def get_nice_name(self) -> str:
        return f"{self.value.replace('MSB_', '').replace('_', ' ').title()}"

    def is_flver(self) -> bool:
        return self in {MSBPartSubtype.MapPiece, MSBPartSubtype.Object, MSBPartSubtype.Asset, MSBPartSubtype.Character}

    def is_map_geometry(self) -> bool:
        """TODO: Asset is ambiguous here. Probably want more enum options."""
        return self in {MSBPartSubtype.MapPiece, MSBPartSubtype.Collision, MSBPartSubtype.Navmesh}


# noinspection PyUnusedLocal
def _update_part_model(self, context):
    """Set the data-block of this (Mesh) object to `model.data`."""
    if self.model:
        if (
            self.model.type == "MESH"
            and (
                self.model.get("MSB_MODEL_PLACEHOLDER", False)
                or self.model.soulstruct_type in {SoulstructType.FLVER, SoulstructType.COLLISION, SoulstructType.NAVMESH}
            )
        ):
            # Valid or placeholder model has been set. Link mesh data.
            self.data = self.model.data
        else:
            # Reject model.
            self.model = None  # will not cause this `if` block to recur


_DRAW_PARAM_DEFAULTS = dict(
    default=-1,
    min=-1,
    max=255,
)


def _is_part(_, obj: bpy.types.Object):
    return obj.soulstruct_type == SoulstructType.MSB_PART


def _is_collision(_, obj: bpy.types.Object):
    return obj.soulstruct_type == SoulstructType.MSB_PART and obj.MSB_PART.part_subtype_enum == MSBPartSubtype.Collision


def _is_region(_, obj: bpy.types.Object):
    return obj.soulstruct_type == SoulstructType.MSB_REGION


class MSBPartProps(bpy.types.PropertyGroup):
    part_subtype: bpy.props.EnumProperty(
        name="Part Subtype",
        description="MSB subtype of this Part object",
        items=[
            ("NONE", "None", "Not an MSB Part"),
            (MSBPartSubtype.MapPiece, "Map Piece", "MSB MapPiece object"),
            (MSBPartSubtype.Object, "Object", "MSB Object object"),
            (MSBPartSubtype.Asset, "Asset", "MSB Asset object"),
            (MSBPartSubtype.Character, "Character", "MSB Character object"),
            (MSBPartSubtype.PlayerStart, "Player Start", "MSB PlayerStart object"),
            (MSBPartSubtype.Collision, "Collision", "MSB Collision object"),
            (MSBPartSubtype.Navmesh, "Navmesh", "MSB Navmesh object"),
            (MSBPartSubtype.ConnectCollision, "Connect Collision", "MSB Connect Collision object"),
            (MSBPartSubtype.Other, "Other", "MSB Other object"),
        ],
        default="NONE",
    )

    @property
    def part_subtype_enum(self) -> MSBPartSubtype:
        if self.part_subtype == "NONE":
            raise ValueError("MSB Part subtype is not set.")
        return MSBPartSubtype(self.part_subtype)

    model: bpy.props.PointerProperty(
        name="Model",
        type=bpy.types.Object,  # could be Armature or Mesh
        description="Source model of this MSB Part instance",

        # Only Mesh objects are supported as models.
        poll=lambda self, obj: obj.type == "MESH",

        # On update, validate Soulstruct type and set the data-block of this (Mesh) object to `model.data`.
        update=_update_part_model,
    )

    # Not used by all subtypes, but still a base Part field, and one we want to preserve if subtype ever changes.
    entity_id: bpy.props.IntProperty(name="Entity ID", default=-1, min=-1)

    draw_groups_0: bpy.props.BoolVectorProperty(
        name="Draw Groups [0, 31]",
        description="Draw groups for this MSB Part object. Parts with draw groups that overlap the display groups of "
                    "the player's current Collision will be drawn or active in the map",
        size=32,
        default=[False] * 32,
    )
    draw_groups_1: bpy.props.BoolVectorProperty(
        name="Draw Groups [32, 63]",
        description="Draw groups for this MSB Part object. Parts with draw groups that overlap the display groups of "
                    "the player's current Collision will be drawn or active in the map",
        size=32,
        default=[False] * 32,
    )
    draw_groups_2: bpy.props.BoolVectorProperty(
        name="Draw Groups [64, 95]",
        description="Draw groups for this MSB Part object. Parts with draw groups that overlap the display groups of "
                    "the player's current Collision will be drawn or active in the map",
        size=32,
        default=[False] * 32,
    )
    draw_groups_3: bpy.props.BoolVectorProperty(
        name="Draw Groups [96, 127]",
        description="Draw groups for this MSB Part object. Parts with draw groups that overlap the display groups of "
                    "the player's current Collision will be drawn or active in the map",
        size=32,
        default=[False] * 32,
    )

    def get_draw_groups_props_128(self) -> list[bpy.props.BoolVectorProperty]:
        return [
            self.draw_groups_0,
            self.draw_groups_1,
            self.draw_groups_2,
            self.draw_groups_3,
        ]

    display_groups_0: bpy.props.BoolVectorProperty(
        name="Display Groups [0, 31]",
        description="Display groups for this MSB Part object. Only used by Collisions. Parts with draw groups that "
                    "overlap the display groups of the player's current Collision will be drawn or active in the map",
        size=32,
        default=[False] * 32,
    )
    display_groups_1: bpy.props.BoolVectorProperty(
        name="Display Groups [32, 63]",
        description="Display groups for this MSB Part object. Only used by Collisions. Parts with draw groups that "
                    "overlap the display groups of the player's current Collision will be drawn or active in the map",
        size=32,
        default=[False] * 32,
    )
    display_groups_2: bpy.props.BoolVectorProperty(
        name="Display Groups [64, 95]",
        description="Display groups for this MSB Part object. Only used by Collisions. Parts with draw groups that "
                    "overlap the display groups of the player's current Collision will be drawn or active in the map",
        size=32,
        default=[False] * 32,
    )
    display_groups_3: bpy.props.BoolVectorProperty(
        name="Display Groups [96, 127]",
        description="Display groups for this MSB Part object. Only used by Collisions. Parts with draw groups that "
                    "overlap the display groups of the player's current Collision will be drawn or active in the map",
        size=32,
        default=[False] * 32,
    )

    def get_display_groups_props_128(self) -> list[bpy.props.BoolVectorProperty]:
        return [
            self.display_groups_0,
            self.display_groups_1,
            self.display_groups_2,
            self.display_groups_3,
        ]

    ambient_light_id: bpy.props.IntProperty(
        name="Ambient Light (Light Bank) ID",
        description="Ambient light DrawParam ID for this MSB Part object (baked lighting, i.e. 'Light Bank')",
        **_DRAW_PARAM_DEFAULTS,
    )
    fog_id: bpy.props.IntProperty(
        name="Fog ID",
        description="Fog DrawParam ID for this MSB Part object",
        **_DRAW_PARAM_DEFAULTS,
    )
    scattered_light_id: bpy.props.IntProperty(
        name="Scattered Light ID",
        description="Scattered light DrawParam ID for this MSB Part object",
        **_DRAW_PARAM_DEFAULTS,
    )
    lens_flare_id: bpy.props.IntProperty(
        name="Lens Flare ID",
        description="Lens flare DrawParam ID for this MSB Part object",
        **_DRAW_PARAM_DEFAULTS,
    )
    shadow_id: bpy.props.IntProperty(
        name="Shadow ID",
        description="Shadow DrawParam ID for this MSB Part object",
        **_DRAW_PARAM_DEFAULTS,
    )
    dof_id: bpy.props.IntProperty(
        name="Depth of Field ID",
        description="Depth of field DrawParam ID for this MSB Part object",
        **_DRAW_PARAM_DEFAULTS,
    )
    tone_map_id: bpy.props.IntProperty(
        name="Tone Map ID",
        description="Tone map DrawParam ID for this MSB Part object",
        **_DRAW_PARAM_DEFAULTS,
    )
    point_light_id: bpy.props.IntProperty(
        name="Point Light ID",
        description="Point light DrawParam ID for this MSB Part object (i.e. player 'lantern')",
        **_DRAW_PARAM_DEFAULTS,
    )
    tone_correction_id: bpy.props.IntProperty(
        name="Tone Correction ID",
        description="Tone correction DrawParam ID for this MSB Part object",
        **_DRAW_PARAM_DEFAULTS,
    )

    DRAW_PARAM_PROP_NAMES = (
        "ambient_light_id",
        "fog_id",
        "scattered_light_id",
        "lens_flare_id",
        "shadow_id",
        "dof_id",
        "tone_map_id",
        "point_light_id",
        "tone_correction_id",
    )

    lod_id: bpy.props.IntProperty(
        name="Level of Detail ID",
        description="Level of Detail ID for this MSB Part object",
        **_DRAW_PARAM_DEFAULTS,
    )
    is_shadow_source: bpy.props.BoolProperty(
        name="Casts Shadow",
        default=False,
    )
    is_shadow_destination: bpy.props.BoolProperty(
        name="Receives Shadow",
        default=False,
    )
    is_shadow_only: bpy.props.BoolProperty(
        name="Only Casts Shadow",
        default=False,
    )
    draw_by_reflect_cam: bpy.props.BoolProperty(
        name="Draw Reflection",
        default=False,
    )
    draw_only_reflect_cam: bpy.props.BoolProperty(
        name="Draw Only Reflection",
        default=False,
    )
    use_depth_bias_float: bpy.props.BoolProperty(
        name="Use Depth Bias",
        default=False,
    )
    disable_point_light_effect: bpy.props.BoolProperty(
        name="Disable Point Light Effect",
        default=False,
    )

    OTHER_DRAW_PROP_NAMES = (
        "lod_id",
        "is_shadow_source",
        "is_shadow_destination",
        "is_shadow_only",
        "draw_by_reflect_cam",
        "draw_only_reflect_cam",
        "use_depth_bias_float",
        "disable_point_light_effect",
    )


class MSBMapPieceProps(bpy.types.PropertyGroup):
    """No additional properties."""
    pass


class MSBObjectProps(bpy.types.PropertyGroup):
    is_dummy: bpy.props.BoolProperty(
        name="Is Dummy",
        description="If enabled, this object will be written to MSB as a Dummy object, which is not loaded "
                    "in-game but can still be used by cutscenes",
        default=False,
    )
    draw_parent: bpy.props.PointerProperty(
        name="Draw Parent",
        type=bpy.types.Object,
    )
    break_term: bpy.props.IntProperty(
        name="Break Term",
        default=0,
    )
    net_sync_type: bpy.props.IntProperty(
        name="Net Sync Type",
        default=0,
    )
    default_animation: bpy.props.IntProperty(
        name="Default Animation",
        default=-1,
        min=-1,
    )
    unk_x0e_x10: bpy.props.IntProperty(
        name="Unknown x0E-x10",
        default=0,
    )
    unk_x10_x14: bpy.props.IntProperty(
        name="Unknown x10-x14",
        default=0,
    )


class MSBAssetProps(bpy.types.PropertyGroup):
    is_dummy: bpy.props.BoolProperty(
        name="Is Dummy",
        description="If enabled, this Asset will be written to MSB as a Dummy Asset, which is not loaded "
                    "in-game but can still be used by cutscenes (and has a heavily restricted subset of fields)",
        default=False,
    )
    draw_parent: bpy.props.PointerProperty(
        name="Draw Parent",
        type=bpy.types.Object,
    )
    # TODO: Elden Ring Asset properties.


class MSBCharacterProps(bpy.types.PropertyGroup):
    is_dummy: bpy.props.BoolProperty(
        name="Is Dummy",
        description="If enabled, this character will be written to MSB as a Dummy character, which is not loaded "
                    "in-game but can still be used by cutscenes",
        default=False,
    )
    draw_parent: bpy.props.PointerProperty(
        name="Draw Parent",
        type=bpy.types.Object,
    )
    ai_id: bpy.props.IntProperty(
        name="AI (NpcThinkParam) ID",
        default=0,
    )
    character_id: bpy.props.IntProperty(
        name="Character (NpcParam) ID",
        default=0,
    )
    talk_id: bpy.props.IntProperty(
        name="Talk ID",
        description="Talk ID (map TalkESD file) to use for this character",
        default=0,
    )
    platoon_id: bpy.props.IntProperty(
        name="Platoon ID",
        default=0,
    )
    patrol_type: bpy.props.IntProperty(
        name="Patrol Type",
        default=0,
    )
    player_id: bpy.props.IntProperty(
        name="Player (CharaInitParam) ID",
        description="Player ID (CharaInitParam) to use for this character. Only used for player model (c0000)",
        default=0,
    )
    patrol_regions_0: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Patrol Region 0",
        description="Patrol region 0 for character",
    )
    patrol_regions_1: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Patrol Region 1",
        description="Patrol region 1 for character",
    )
    patrol_regions_2: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Patrol Region 2",
        description="Patrol region 2 for character",
    )
    patrol_regions_3: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Patrol Region 3",
        description="Patrol region 3 for character",
    )
    patrol_regions_4: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Patrol Region 4",
        description="Patrol region 4 for character",
    )
    patrol_regions_5: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Patrol Region 5",
        description="Patrol region 5 for character",
    )
    patrol_regions_6: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Patrol Region 6",
        description="Patrol region 6 for character",
    )
    patrol_regions_7: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Patrol Region 7",
        description="Patrol region 7 for character",
    )

    def get_patrol_regions(self) -> list[bpy.types.Object | None]:
        return [
            self.patrol_regions_0, self.patrol_regions_1, self.patrol_regions_2, self.patrol_regions_3,
            self.patrol_regions_4, self.patrol_regions_5, self.patrol_regions_6, self.patrol_regions_7,
        ]

    default_animation: bpy.props.IntProperty(
        name="Default Animation",
        default=0,
    )
    damage_animation: bpy.props.IntProperty(
        name="Damage Animation",
        default=0,
    )

    # Likely to be changed.
    BASIC_SETTINGS = (
        "draw_parent",
        "ai_id",
        "character_id",
        "player_id",
        "talk_id",
        "default_animation",
    )

    PATROL_SETTINGS = (
        "patrol_type",
        "patrol_regions_0",
        "patrol_regions_1",
        "patrol_regions_2",
        "patrol_regions_3",
        "patrol_regions_4",
        "patrol_regions_5",
        "patrol_regions_6",
        "patrol_regions_7",
    )

    # Unlikely to be changed.
    ADVANCED_SETTINGS = (
        "platoon_id",
        "damage_animation",
    )


class MSBPlayerStartProps(bpy.types.PropertyGroup):
    """No additional properties."""
    pass


class MSBCollisionProps(bpy.types.PropertyGroup):
    navmesh_groups_0: bpy.props.BoolVectorProperty(
        name="Navmesh Groups [0, 31]",
        description="Navmesh groups for this Collision. These should match the navmesh groups of corresponding Navmesh "
                    "parts and are used to control navmesh-based map backread. They generally match the model ID",
        size=32,
        default=[False] * 32,
    )
    navmesh_groups_1: bpy.props.BoolVectorProperty(
        name="Navmesh Groups [32, 63]",
        description="Navmesh groups for this Collision. These should match the navmesh groups of corresponding Navmesh "
                    "parts and are used to control navmesh-based map backread. They generally match the model ID",
        size=32,
        default=[False] * 32,
    )
    navmesh_groups_2: bpy.props.BoolVectorProperty(
        name="Navmesh Groups [64, 95]",
        description="Navmesh groups for this Collision. These should match the navmesh groups of corresponding Navmesh "
                    "parts and are used to control navmesh-based map backread. They generally match the model ID",
        size=32,
        default=[False] * 32,
    )
    navmesh_groups_3: bpy.props.BoolVectorProperty(
        name="Navmesh Groups [96, 127]",
        description="Navmesh groups for this Collision. These should match the navmesh groups of corresponding Navmesh "
                    "parts and are used to control navmesh-based map backread. They generally match the model ID",
        size=32,
        default=[False] * 32,
    )

    def get_navmesh_groups_props_128(self) -> list[bpy.props.BoolVectorProperty]:
        return [
            self.navmesh_groups_0,
            self.navmesh_groups_1,
            self.navmesh_groups_2,
            self.navmesh_groups_3,
        ]

    hit_filter: bpy.props.EnumProperty(
        name="Hit Filter Name",
        description="Determines effect of collision on characters",
        items=[
            (CollisionHitFilter.NoHiHitNoFeetIK.name, "NoHiHitNoFeetIK", "NoHiHitNoFeetIK"),  # solid
            (CollisionHitFilter.NoHiHit_1.name, "NoHiHit_1", "NoHiHit_1"),  # solid
            (CollisionHitFilter.NoHiHit_2.name, "NoHiHit_2", "NoHiHit_2"),  # solid
            (CollisionHitFilter.NoHiHit_3.name, "NoHiHit_3", "NoHiHit_3"),  # solid
            (CollisionHitFilter.NoHiHit_4.name, "NoHiHit_4", "NoHiHit_4"),  # solid
            (CollisionHitFilter.NoHiHit_5.name, "NoHiHit_5", "NoHiHit_5"),  # solid
            (CollisionHitFilter.NoHiHit_6.name, "NoHiHit_6", "NoHiHit_6"),  # solid
            (CollisionHitFilter.NoHiHit_7.name, "NoHiHit_7", "NoHiHit_7"),  # solid
            (CollisionHitFilter.Normal.name, "Normal", "Normal"),  # solid
            (CollisionHitFilter.Water_A.name, "Water_A", "Water_A"),  # blue
            (CollisionHitFilter.Unknown_10.name, "Unknown_10", "Unknown_10"),
            (CollisionHitFilter.Solid_ForNPCsOnly_A.name, "Solid_ForNPCsOnly_A", "Solid_ForNPCsOnly_A"),  # blue
            (CollisionHitFilter.Unknown_12.name, "Unknown_12", "Unknown_12"),
            (CollisionHitFilter.DeathCam.name, "DeathCam", "DeathCam"),  # white
            (CollisionHitFilter.LethalFall.name, "LethalFall", "LethalFall"),  # red
            (CollisionHitFilter.KillPlane.name, "KillPlane", "KillPlane"),  # black
            (CollisionHitFilter.Water_B.name, "Water_B", "Water_B"),  # dark blue
            (CollisionHitFilter.GroupSwitch.name, "GroupSwitch", "GroupSwitch"),  # turquoise; in elevator shafts
            (CollisionHitFilter.Unknown_18.name, "Unknown_18", "Unknown_18"),
            (CollisionHitFilter.Solid_ForNPCsOnly_B.name, "Solid_ForNPCsOnly_B", "Solid_ForNPCsOnly_B"),  # turquoise
            (CollisionHitFilter.LevelExit_A.name, "LevelExit_A", "LevelExit_A"),  # purple
            (CollisionHitFilter.Slide.name, "Slide", "Slide"),  # yellow
            (CollisionHitFilter.FallProtection.name, "FallProtection", "FallProtection"),  # permeable for projectiles
            (CollisionHitFilter.LevelExit_B.name, "LevelExit_B", "LevelExit_B"),  # glowing turquoise
        ],
        default=CollisionHitFilter.Normal.name,
    )
    sound_space_type: bpy.props.IntProperty(
        name="Sound Space Type",
        description="Sound space (e.g. reverberation) type for this collision",
        default=0,
    )
    place_name_banner_id: bpy.props.IntProperty(
        name="Place Name Banner ID",
        description="ID of the Place Name Banner (in 'PlaceName' FMG) to display when player steps on this collision. "
                    "Set to -1 to use map's default banner (mAA_BB -> AABB), but note that it must always be Forced in "
                    "this case",
        default=-1,
        min=-1,
        update=lambda self, context: setattr(self, "force_place_name_banner", True),
    )
    force_place_name_banner: bpy.props.BoolProperty(
        name="Force Place Name Banner",
        description="If enabled, the Place Name Banner will be displayed as long as it is a new banner ID, rather than "
                    "only showing on game load. Must be enabled if using map's default banner ID (-1)",
        default=True,
    )
    play_region_id: bpy.props.IntProperty(
        name="Play Region ID",
        description="Online/multiplayer play region ID for this collision. Must be set to 0 (NOT -1) if a non-zero "
                    "Stable Footing Flag is set",
        default=0,
        min=0,
        update=lambda self, context: self._update_play_region_id(context),
    )
    stable_footing_flag: bpy.props.IntProperty(
        name="Stable Footing Flag",
        description="If non-zero, this flag must be enabled for this collision to be considered stable ground. Must be "
                    "set to 0 if a non-zero Play Region ID is set",
        default=0,
        min=0,
        update=lambda self, context: self._update_stable_footing_flag(context),
    )
    camera_1_id: bpy.props.IntProperty(
        name="Camera 1 ID",
        description="Primary camera ID (LockCamParam) to switch to when player steps on this collision",
        default=-1,
        min=-1,
    )
    camera_2_id: bpy.props.IntProperty(
        name="Camera 2 ID",
        description="Secondary camera ID (LockCamParam) to switch to when player steps on this collision",
        default=-1,
        min=-1,
    )
    unk_x27_x28: bpy.props.IntProperty(
        name="Unknown x27-x28",
        description="Unknown purpose; rarely non-zero, e.g. for Anor Londo spinning tower collision",
        default=0,
    )
    attached_bonfire: bpy.props.IntProperty(
        name="Attached Bonfire",
        description="Entity ID of optional attached bonfire, which will be unusable if enemies are on this collision",
        default=0,
        min=0,
    )
    # NOTE: `environment_event` is not maintained in Blender. We just find the Environment event that references this.
    reflect_plane_height: bpy.props.FloatProperty(
        name="Reflect Plane Height",
        description="Height of the reflection plane for this collision, used for water reflections",
        default=0.0,
    )
    vagrant_entity_ids_0: bpy.props.IntProperty(
        name="Vagrant Entity ID [0]",
        description="Entity ID of Vagrant that can appear on this collision",
        default=-1,
        min=-1,
    )
    vagrant_entity_ids_1: bpy.props.IntProperty(
        name="Vagrant Entity ID [1]",
        description="Entity ID of Vagrant that can appear on this collision",
        default=-1,
        min=-1,
    )
    vagrant_entity_ids_2: bpy.props.IntProperty(
        name="Vagrant Entity ID [2]",
        description="Entity ID of Vagrant that can appear on this collision",
        default=-1,
        min=-1,
    )

    def get_vagrant_entity_ids(self) -> list[int]:
        return [
            self.vagrant_entity_ids_0, self.vagrant_entity_ids_1, self.vagrant_entity_ids_2
        ]

    starts_disabled: bpy.props.BoolProperty(
        name="Starts Disabled",
        description="If enabled, this collision will be disabled on game load and must be enabled with EMEVD",
        default=False,
    )

    def _update_play_region_id(self, _):
        if self.play_region_id != 0:
            self.stable_footing_flag = 0

    def _update_stable_footing_flag(self, _):
        if self.stable_footing_flag != 0:
            self.play_region_id = 0


class MSBNavmeshProps(bpy.types.PropertyGroup):
    navmesh_groups_0: bpy.props.BoolVectorProperty(
        name="Navmesh Groups [0, 31]",
        description="Navmesh groups for this Navmesh. These should match the navmesh groups of corresponding Collision "
                    "parts and are used to control navmesh-based map backread. They generally match the model ID",
        size=32,
        default=[False] * 32,
    )
    navmesh_groups_1: bpy.props.BoolVectorProperty(
        name="Navmesh Groups [32, 63]",
        description="Navmesh groups for this Navmesh. These should match the navmesh groups of corresponding Collision "
                    "parts and are used to control navmesh-based map backread. They generally match the model ID",
        size=32,
        default=[False] * 32,
    )
    navmesh_groups_2: bpy.props.BoolVectorProperty(
        name="Navmesh Groups [64, 95]",
        description="Navmesh groups for this Navmesh. These should match the navmesh groups of corresponding Collision "
                    "parts and are used to control navmesh-based map backread. They generally match the model ID",
        size=32,
        default=[False] * 32,
    )
    navmesh_groups_3: bpy.props.BoolVectorProperty(
        name="Navmesh Groups [96, 127]",
        description="Navmesh groups for this Navmesh. These should match the navmesh groups of corresponding Collision "
                    "parts and are used to control navmesh-based map backread. They generally match the model ID",
        size=32,
        default=[False] * 32,
    )

    def get_navmesh_groups_props_128(self) -> list[bpy.props.BoolVectorProperty]:
        return [
            self.navmesh_groups_0,
            self.navmesh_groups_1,
            self.navmesh_groups_2,
            self.navmesh_groups_3,
        ]


class MSBConnectCollisionProps(bpy.types.PropertyGroup):
    collision: bpy.props.PointerProperty(
        name="Collision Part",
        description="Collision part to which this Connect Collision is attached",
        type=bpy.types.Object,
        poll=_is_collision,
    )
    map_area: bpy.props.IntProperty(
        name="Connected Map Area",
        description="Area ID of the connected map ('AA' from mAA_BB_CC_DD)",
        default=0,
        min=0,
        max=99,
    )
    map_block: bpy.props.IntProperty(
        name="Connected Map Block",
        description="Block ID of the connected map ('BB' from mAA_BB_CC_DD). Can be -1",
        default=-1,
        min=-1,
        max=99,
    )
    map_cc: bpy.props.IntProperty(
        name="Connected Map CC",
        description="CC ID of the connected map (from mAA_BB_CC_DD). Can be -1",
        default=-1,
        min=-1,
        max=99,
    )
    map_dd: bpy.props.IntProperty(
        name="Connected Map DD",
        description="DD ID of the connected map (from mAA_BB_CC_DD). Can be -1",
        default=-1,
        min=-1,
        max=99,
    )


class MSBRegionSubtype(StrEnum):
    """Union of Region subtypes across all games."""
    All = "ALL"  # for games with no real subtypes (DS1, BB, ...)


class MSBRegionProps(bpy.types.PropertyGroup):
    entity_id: bpy.props.IntProperty(
        name="Entity ID",
        default=-1
    )

    region_subtype: bpy.props.EnumProperty(
        name="Region Subtype",
        description="MSB subtype (shape) of this Region object",
        items=[
            ("NONE", "None", "Not an MSB Region"),
            (MSBRegionSubtype.All, "All", "Older game with no region subtypes (only shapes)"),
            # TODO: ER subtypes...
        ],
        default="NONE",
    )

    @property
    def region_subtype_enum(self):
        if self.region_subtype == "NONE":
            raise ValueError("MSB Region subtype is not set.")
        return MSBRegionSubtype(self.region_subtype)

    shape_type: bpy.props.EnumProperty(
        name="Shape",
        description="Shape of this Region object. Object's mesh will update automatically when changed and shape "
                    "dimension properties will be applied to object scale",
        items=[
            (RegionShapeType.Point.name, "Point", "Point with location and rotation only"),
            (RegionShapeType.Circle.name, "Circle", "2D circle with radius (-> X/Y scale). Unused"),
            (RegionShapeType.Sphere.name, "Sphere", "Volume with radius only (-> X/Y/Z scale)"),
            (RegionShapeType.Cylinder.name, "Cylinder", "Volume with radius (-> X/Y scale) and height (-> Z scale)"),
            (RegionShapeType.Rect.name, "Rect", "2D rectangle with width (X) and depth (Y). Unused"),
            (RegionShapeType.Box.name, "Box", "Volume with width (X), depth (Y), and height (Z)"),
        ],
        default=RegionShapeType.Point.name,
        update=lambda self, context: self._auto_shape_mesh(context),
    )

    @property
    def shape_type_enum(self) -> RegionShapeType:
        return RegionShapeType[self.shape_type]

    # Three shape fields that are exposed differently depending on `shape` type. These are used to drive object scale.
    # Note that these are in Blender coordinates, so Z is height here, rather than Y (as in MSB).
    shape_x: bpy.props.FloatProperty(
        name="Shape X",
        description="X dimension of region shape (sphere/cylinder/circle radius or box/rect width)",
        default=1.0,
    )
    shape_y: bpy.props.FloatProperty(
        name="Shape Y",
        description="Y dimension of region shape (box/rect depth)",
        default=1.0,
    )
    shape_z: bpy.props.FloatProperty(
        name="Shape Z",
        description="Z dimension of region shape (cylinder/box height)",
        default=1.0,
    )

    def _auto_shape_mesh(self, _):
        """Fully replace mesh when a new shape is selected."""
        shape = RegionShapeType[self.shape_type]
        obj = self.id_data  # type: bpy.types.MeshObject
        if obj.type != "MESH":
            return  # unsupported region object
        mesh = obj.data  # type: bpy.types.Mesh
        # Clear scale drivers. New ones will be created as appropriate.
        for i in range(3):
            obj.driver_remove("scale", i)

        # NOTE: We don't change `obj.show_axis` here. It's enabled by default for Points on import, but is up to
        # the player to enable/disable after that.

        if shape == RegionShapeType.Point:
            primitive_three_axes(mesh)
            # No drivers.
        elif shape == RegionShapeType.Circle:
            primitive_circle(mesh)
            create_region_scale_driver(obj, "xx")
        elif shape == RegionShapeType.Sphere:
            primitive_sphere(mesh)
            create_region_scale_driver(obj, "xxx")
        elif shape == RegionShapeType.Cylinder:
            primitive_cylinder(mesh)
            create_region_scale_driver(obj, "xxz")
        elif shape == RegionShapeType.Rect:
            primitive_rect(mesh)
            create_region_scale_driver(obj, "xy")
        elif shape == RegionShapeType.Box:
            primitive_cube(mesh)
            create_region_scale_driver(obj, "xyz")
        else:
            # TODO: Handle Composite.
            pass


class MSBEventSubtype(StrEnum):
    """Union of Event subtypes across all games."""
    Light = "MSB_LIGHT"
    Sound = "MSB_SOUND"
    VFX = "MSB_VFX"
    Wind = "MSB_WIND"
    Treasure = "MSB_TREASURE"
    Spawner = "MSB_SPAWNER"
    Message = "MSB_MESSAGE"
    ObjAct = "MSB_OBJ_ACT"
    SpawnPoint = "MSB_SPAWN_POINT"
    MapOffset = "MSB_MAP_OFFSET"
    Navigation = "MSB_NAVIGATION"
    Environment = "MSB_ENVIRONMENT"
    NPCInvasion = "MSB_NPC_INVASION"

    def get_nice_name(self) -> str:
        return f"{self.value.replace('MSB_', '').replace('_', ' ').title()}"

    @classmethod
    def get_enum_name(cls, enum_value: str):
        return cls(enum_value).name


class MSBEventProps(bpy.types.PropertyGroup):

    event_subtype: bpy.props.EnumProperty(
        name="Event Subtype",
        description="MSB subtype of this Event object",
        items=[
            ("NONE", "None", "Not an MSB Event"),
            (MSBEventSubtype.Light, "Light", "MSB Light Event"),
            (MSBEventSubtype.Sound, "Sound", "MSB Sound Event"),
            (MSBEventSubtype.VFX, "VFX", "MSB VFX Event"),
            (MSBEventSubtype.Wind, "Wind", "MSB Wind Event"),
            (MSBEventSubtype.Treasure, "Treasure", "MSB Treasure Event"),
            (MSBEventSubtype.Spawner, "Spawner", "MSB Spawner Event"),
            (MSBEventSubtype.Message, "Message", "MSB Message Event"),
            (MSBEventSubtype.ObjAct, "ObjAct", "MSB ObjAct (Object Action) Event"),
            (MSBEventSubtype.SpawnPoint, "Spawn Point", "MSB Spawn Point Event"),
            (MSBEventSubtype.MapOffset, "Map Offset", "MSB Map Offset Event"),
            (MSBEventSubtype.Navigation, "Navigation", "MSB Navigation Event"),
            (MSBEventSubtype.Environment, "Environment", "MSB Environment Event"),
            (MSBEventSubtype.NPCInvasion, "NPC Invasion", "MSB NPC Invasion Event"),
        ],
        default="NONE",
        update=lambda self, context: self._update_name_suffix(context),
    )

    @property
    def event_subtype_enum(self) -> MSBEventSubtype:
        if self.event_subtype == "NONE":
            raise ValueError("MSB Event subtype is not set.")
        return MSBEventSubtype(self.event_subtype)

    entity_id: bpy.props.IntProperty(
        name="Entity ID",
        description="Entity ID of MSB Event. Not used by all subtypes",
        default=-1,
        min=-1,
    )

    attached_part: bpy.props.PointerProperty(
        name="Attached Part",
        description="MSB Part object to which this MSB Event is attached. Not used by all subtypes; some subtypes "
                    "even define and use their own additional Part field, for some reason",
        type=bpy.types.Object,
        poll=_is_part,
    )

    attached_region: bpy.props.PointerProperty(
        name="Attached Region",
        description="MSB Region object to which this MSB Event is attached. Not used by all subtypes",
        type=bpy.types.Object,
        poll=_is_region,
    )

    unknowns: bpy.props.IntVectorProperty(
        name="Unknowns",
        description="Four unknown integer values for DS1 MSB Events",
        size=4,
        default=(0, 0, 0, 0),
    )

    _EVENT_NAME_RE = re.compile(r"^(.*)<(.+)>(\.\d+)?$")

    def _update_name_suffix(self, _):
        """Update suffix is one current exists. Preserves dupe suffix."""
        if match := self._EVENT_NAME_RE.match(self.name):
            old_suffix = match.group(2)
            if old_suffix in MSBEventSubtype.__members__:
                obj = self.id_data  # type: bpy.types.Object
                name = match.group(1).strip()
                dupe_suffix = match.group(3) or ""
                obj.name = f"{name} <{MSBEventSubtype.get_enum_name(obj.MSB_EVENT.event_subtype)}>{dupe_suffix}"


class MSBLightEventProps(bpy.types.PropertyGroup):

    point_light_id: bpy.props.IntProperty(
        name="Point Light ID",
        description="DrawParam ID of the point light to attach to this MSB Light Event",
        **_DRAW_PARAM_DEFAULTS,
    )


class MSBSoundEventProps(bpy.types.PropertyGroup):

    sound_type: bpy.props.EnumProperty(
        name="Sound Type",
        description="Type of sound to play. Determines sound file prefix letter",
        items=[
            ("a_Ambient", "a_Ambient", "Ambient"),
            ("c_CharacterMotion", "c_CharacterMotion", "Character Motion"),
            ("f_MenuEffect", "f_MenuEffect", "Menu Effect"),
            ("o_Object", "o_Object", "Object"),
            ("p_Cutscene", "p_Cutscene", "Cutscene"),
            ("s_SFX", "s_SFX", "SFX"),
            ("m_Music", "m_Music", "Music"),
            ("v_Voice", "v_Voice", "Voice"),
            ("x_FloorMaterialDependent", "x_FloorMaterialDependent", "Floor Material Dependent"),
            ("b_ArmorMaterialDependent", "b_ArmorMaterialDependent", "Armor Material Dependent"),
            ("g_Ghost", "g_Ghost", "Ghost"),
        ],
        default="s_SFX",
    )

    sound_id: bpy.props.IntProperty(
        name="Sound ID",
        description="ID of the sound to play",
        default=0,
        min=0,
    )


class MSBVFXEventProps(bpy.types.PropertyGroup):

    vfx_id: bpy.props.IntProperty(
        name="VFX ID",
        description="ID of the VFX to play",
        default=0,
        min=0,
    )


class MSBWindEventProps(bpy.types.PropertyGroup):

    wind_vector_min: bpy.props.FloatVectorProperty(
        name="Wind Vector (Min)",
        description="Wind vector minimum",
        default=(0.0, 0.0, 0.0),
    )
    unk_x04_x08: bpy.props.FloatProperty(
        name="Unk x04",
        description="Unknown scalar related to wind vector minimum",
        default=0.0,
    )
    wind_vector_max: bpy.props.FloatVectorProperty(
        name="Wind Vector (Max)",
        description="Wind vector maximum",
        default=(0.0, 0.0, 0.0),
    )
    unk_x0c_x10: bpy.props.FloatProperty(
        name="Unk x0c",
        description="Unknown scalar related to wind vector maximum",
        default=0.0,
    )
    wind_swing_cycles: bpy.props.FloatVectorProperty(
        name="Wind Swing Cycles",
        description="Likely periods of wind min/max oscillations",
        size=4,
        default=(0.0, 0.0, 0.0, 0.0),
    )
    wind_swing_powers: bpy.props.FloatVectorProperty(
        name="Wind Swing Powers",
        description="Likely amplitudes of wind min/max oscillations",
        size=4,
        default=(0.0, 0.0, 0.0, 0.0),
    )


class MSBTreasureEventProps(bpy.types.PropertyGroup):

    treasure_part: bpy.props.PointerProperty(
        name="Treasure Part",
        description="MSB Part object to which treasure is attached (corpse/chest/empty). Replaces default event "
                    "Attached Part",
        type=bpy.types.Object,
        poll=_is_part,
    )
    item_lot_1: bpy.props.IntProperty(
        name="Item Lot 1",
        description="ItemLotParam ID 1 for treasure",
        default=-1,
    )
    item_lot_2: bpy.props.IntProperty(
        name="Item Lot 2",
        description="ItemLotParam ID 2 for treasure",
        default=-1,
    )
    item_lot_3: bpy.props.IntProperty(
        name="Item Lot 3",
        description="ItemLotParam ID 3 for treasure",
        default=-1,
    )
    item_lot_4: bpy.props.IntProperty(
        name="Item Lot 4",
        description="ItemLotParam ID 4 for treasure",
        default=-1,
    )
    item_lot_5: bpy.props.IntProperty(
        name="Item Lot 5",
        description="ItemLotParam ID 5 for treasure",
        default=-1,
    )
    is_in_chest: bpy.props.BoolProperty(
        name="Is In Chest",
        description="If enabled, treasure is in a chest",
        default=False,
    )
    is_hidden: bpy.props.BoolProperty(
        name="Is Hidden",
        description="If enabled, treasure is disabled on load and must be enabled with EMEVD",
        default=False,
    )


class MSBSpawnerEventProps(bpy.types.PropertyGroup):

    max_count: bpy.props.IntProperty(
        name="Max Count",
        description="Maximum number of characters that can be spawned per game load",
        default=255,
        min=0,
        max=255,
    )

    spawner_type: bpy.props.IntProperty(
        name="Spawner Type",
        description="Spawner type",
        default=0,
        min=0,
    )

    limit_count: bpy.props.IntProperty(
        name="Limit Count",
        description="Limit count (-1 means no limit)",
        default=-1,
        min=-1,
    )

    min_spawner_count: bpy.props.IntProperty(
        name="Minimum Spawner Count",
        description="Ensure number of spawned living characters stays at or above this minimum",
        default=1,
        min=0,
    )

    max_spawner_count: bpy.props.IntProperty(
        name="Maximum Spawner Count",
        description="Ensure number of spawned living characters stays at or below this maximum",
        default=1,
        min=0,
    )

    min_interval: bpy.props.FloatProperty(
        name="Minimum Interval",
        description="Minimum time between spawns",
        default=1.0,
        min=0.0,
    )

    max_interval = bpy.props.FloatProperty(
        name="Maximum Interval",
        description="Maximum time between spawns",
        default=1.0,
        min=0.0,
    )

    initial_spawn_count: bpy.props.IntProperty(
        name="Initial Spawn Count",
        description="Number of characters to spawn on game load",
        default=1,
        min=0,
    )

    # region Spawn Parts

    spawn_parts_0: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 0",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_1: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 1",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_2: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 2",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_3: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 3",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_4: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 4",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_5: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 5",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_6: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 6",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_7: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 7",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_8: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 8",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_9: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 9",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_10: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 10",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_11: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 11",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_12: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 12",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_13: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 13",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_14: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 14",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_15: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 15",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_16: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 16",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_17: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 17",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_18: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 18",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_19: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 19",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_20: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 20",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_21: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 21",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_22: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 22",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_23: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 23",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_24: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 24",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_25: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 25",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_26: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 26",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_27: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 27",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_28: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 28",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_29: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 29",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_30: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 30",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    spawn_parts_31: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Character 31",
        description="MSB Character part to spawn at this step in the sequence",
        poll=_is_part,
    )

    # endregion

    def get_spawn_parts(self) -> list[bpy.types.Object | None]:
        return [getattr(self, f"spawn_parts_{i}") for i in range(32)]

    spawn_regions_0: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Region 0",
        description="MSB Region object to spawn characters at this step in the sequence",
        poll=_is_region,
    )

    spawn_regions_1: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Region 1",
        description="MSB Region object to spawn characters at this step in the sequence",
        poll=_is_region,
    )

    spawn_regions_2: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Region 2",
        description="MSB Region object to spawn characters at this step in the sequence",
        poll=_is_region,
    )

    spawn_regions_3: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Spawn Region 3",
        description="MSB Region object to spawn characters at this step in the sequence",
        poll=_is_region,
    )

    def get_spawn_regions(self) -> list[bpy.types.Object | None]:
        return [getattr(self, f"spawn_regions_{i}") for i in range(4)]


class MSBMessageEventProps(bpy.types.PropertyGroup):

    text_id: bpy.props.IntProperty(
        name="Text ID",
        description="Soapstone message ID to display",
        default=-1,
    )
    unk_x02_x04: bpy.props.IntProperty(
        name="Unk x02",
        description="Unknown integer value",
        default=2,
    )
    is_hidden: bpy.props.BoolProperty(
        name="Is Hidden",
        description="If enabled, message is disabled on load and must be enabled with EMEVD",
        default=False,
    )


class MSBObjActEventProps(bpy.types.PropertyGroup):

    obj_act_entity_id: bpy.props.IntProperty(
        name="ObjAct Entity ID",
        description="ID of ObjAct trigger to check for in EMEVD. Replaces base MSB Event Entity ID",
        default=-1,
    )

    obj_act_part: bpy.props.PointerProperty(
        name="ObjAct Part",
        description="MSB Part (likely Object) that ObjAct event is attached to. Replaces base MSB Event Attached Part",
        type=bpy.types.Object,
        poll=_is_part,
    )

    obj_act_param_id: bpy.props.IntProperty(
        name="ObjAct Param ID",
        description="ObjAct Param ID to use for this event. -1 means ID will match ObjAct Part model ID",
        default=-1,
    )

    obj_act_state: bpy.props.IntProperty(
        name="ObjAct State",
        description="Initial state of ObjAct Part controlled by this event",
        default=0,
    )

    obj_act_flag: bpy.props.IntProperty(
        name="ObjAct Flag",
        description="Persistent flag used to record state of ObjAct Part controlled by this event (e.g. open/closed)",
        default=0,
    )


class MSBSpawnPointEventProps(bpy.types.PropertyGroup):

    spawn_point_region: bpy.props.PointerProperty(
        name="Spawn Point Region",
        description="MSB Region object defining the spawn point location. Replaces base MSB Event Attached Region",
        type=bpy.types.Object,
        poll=_is_region,
    )


class MSBMapOffsetEventProps(bpy.types.PropertyGroup):

    # TODO: Standard game coordinate conversion.
    translate: bpy.props.FloatVectorProperty(
        name="Translate",
        description="Translation offset for the map (in Blender coordinates)",
        default=(0.0, 0.0, 0.0),
    )

    # TODO: Make sure to convert to radians and negate.
    rotate_z: bpy.props.FloatProperty(
        name="Rotate Z",
        description="Z-axis rotation offset for the map (in degrees around Blender's vertical Z axis)",
        default=0.0,
    )


class MSBNavigationEventProps(bpy.types.PropertyGroup):

    navigation_region: bpy.props.PointerProperty(
        name="Navigation Region",
        description="MSB Region object defining the area of the navigation mesh corresponding to this Entity ID. NOTE: "
                    "these events are dummy representations of events and IDs hard-coded into the NVM Navmesh model",
        type=bpy.types.Object,
        poll=_is_region,
    )


class MSBEnvironmentEventProps(bpy.types.PropertyGroup):

    unk_x00_x04: bpy.props.IntProperty(
        name="Unk x00",
        description="Unknown integer value",
        default=0,
    )

    unk_x04_x08: bpy.props.FloatProperty(
        name="Unk x04",
        description="Unknown float value",
        default=1.0,
    )

    unk_x08_x0c: bpy.props.FloatProperty(
        name="Unk x08",
        description="Unknown float value",
        default=1.0,
    )

    unk_x0c_x10: bpy.props.FloatProperty(
        name="Unk x0c",
        description="Unknown float value",
        default=1.0,
    )

    unk_x10_x14: bpy.props.FloatProperty(
        name="Unk x10",
        description="Unknown float value",
        default=1.0,
    )

    unk_x14_x18: bpy.props.FloatProperty(
        name="Unk x14",
        description="Unknown float value",
        default=1.0,
    )


class MSBNPCInvasionEventProps(bpy.types.PropertyGroup):

    host_entity_id: bpy.props.IntProperty(
        name="Host Entity ID",
        description="Entity ID of the host NPC for this invasion",
        default=-1,
    )

    invasion_flag_id: bpy.props.IntProperty(
        name="Invasion Flag ID",
        description="Flag ID to set when this invasion is triggered",
        default=-1,
    )

    activate_good_id: bpy.props.IntProperty(
        name="Activate Good ID",
        description="GoodParam ID that must be used inside attached region to trigger NPC invasion",
        default=-1,
    )


class MSBImportSettings(bpy.types.PropertyGroup):
    """Common MSB import settings. Drawn manually in operator browser windows."""

    import_map_piece_models: bpy.props.BoolProperty(
        name="Import Map Piece Models",
        description="Import models for MSB Map Piece parts, rather than using placeholder meshes",
        default=True,
    )
    import_collision_models: bpy.props.BoolProperty(
        name="Import Collision Models",
        description="Import models for MSB Collision/Connect Collision parts, rather than using placeholder meshes",
        default=True,
    )
    import_navmesh_models: bpy.props.BoolProperty(
        name="Import Navmesh Models",
        description="Import models for MSB Navmesh parts, rather than using placeholder meshes",
        default=True,
    )
    import_object_models: bpy.props.BoolProperty(
        name="Import Object Models",
        description="Import models for MSB Object/Asset parts, rather than using placeholder meshes",
        default=True,
    )
    import_character_models: bpy.props.BoolProperty(
        name="Import Character Models",
        description="Import models for MSB Character and MSB Player Start parts, rather than using placeholder meshes",
        default=True,
    )

    part_name_model_filter: bpy.props.StringProperty(
        name="Part Name Model Import Filter",
        description="Glob/Regex for filtering which MSB Parts should have their models loaded (if their type is "
                    "also enabled for import above), rather than using placeholder meshes",
        default="*",
    )

    part_name_filter_match_mode: bpy.props.EnumProperty(
        name="Part Name Filter Match Mode",
        description="Whether to use glob or regex for MSB Part name matching for model import",
        items=[
            ("GLOB", "Glob", "Use glob (*, ?, etc.) for MSB Part name matching"),
            ("REGEX", "Regex", "Use Python regular expressions for MSB Part name matching"),
        ],
        default="GLOB",
    )

    def get_name_match_filter(self) -> tp.Callable[[str], bool]:
        match self.part_name_filter_match_mode:
            case "GLOB":
                def is_name_match(name: str):
                    return self.part_name_model_filter in {"", "*"} or fnmatch(name, self.part_name_model_filter)
            case "REGEX":
                pattern = re.compile(self.part_name_model_filter)

                def is_name_match(name: str):
                    return self.part_name_model_filter == "" or re.match(pattern, name)
            case _:  # should never happen
                raise ValueError(f"Invalid MSB Part name match mode: {self.part_name_filter_match_mode}")
        return is_name_match

    hide_model_collections: bpy.props.BoolProperty(
        name="Hide Model Collections",
        description="Hide any new Model collections (in viewport) created for the first time on MSB import",
        default=True,
    )

    hide_dummy_entries: bpy.props.BoolProperty(
        name="Hide Dummy Characters/Objects",
        description="Hide dummy MSB Characters, Objects, and Assets (disabled, cutscene only, etc.) in the viewport",
        default=True,
    )


class MSBExportSettings(bpy.types.PropertyGroup):

    use_world_transforms: bpy.props.BoolProperty(
        name="Use World Transforms",
        description="Use world transforms when exporting MSB entries, rather than local transforms. Recommended so "
                    "that you can use Blender parenting to place groups of MSB entries and still see exactly what you "
                    "see in Blender in-game",
        default=True,
    )

    export_collision_models: bpy.props.BoolProperty(
        name="Export Collision Models",
        description="Export models for MSB Collision parts to new hi/lo-res HKXBHD Binders in map. Convenient way to "
                    "ensure that collision models are synchronized with the MSB (Collision HKX export is quite fast)",
        default=False,
    )

    export_navmesh_models: bpy.props.BoolProperty(
        name="Export Navmesh Models",
        description="Export models for MSB Navmesh parts to a new NVMBND Binder in map. Convenient way to ensure that "
                    "navmesh models are synchronized with the MSB (NVM export is quite fast)",
        default=False,
    )

    export_nvmdump: bpy.props.BoolProperty(
        name="Export NVMDUMP",
        description="Export NVMDUMP text file to map",
        default=True,
    )

    export_soulstruct_jsons: bpy.props.BoolProperty(
        name="Export Soulstruct JSONs",
        description="Export MSB JSON files to 'maps' directory in Soulstruct GUI Project Directory, if given",
        default=False,
    )


class MSBToolSettings(bpy.types.PropertyGroup):

    event_color: bpy.props.FloatVectorProperty(
        name="Event Color",
        description="Color for setting MSB Event objects in the viewport",
        subtype="COLOR",
        size=4,
        default=(0.0, 0.0, 0.0, 1.0),
    )

    event_color_type: bpy.props.EnumProperty(
        name="Event Subtype to Color",
        items=[
            ("ALL", "All", "Color all MSB Events"),
            (MSBEventSubtype.Light, "Light", "MSB Light Events"),
            (MSBEventSubtype.Sound, "Sound", "MSB Sound Events"),
            (MSBEventSubtype.VFX, "VFX", "MSB VFX Events"),
            (MSBEventSubtype.Wind, "Wind", "MSB Wind Events"),
            (MSBEventSubtype.Treasure, "Treasure", "MSB Treasure Events"),
            (MSBEventSubtype.Spawner, "Spawner", "MSB Spawner Events"),
            (MSBEventSubtype.Message, "Message", "MSB Message Events"),
            (MSBEventSubtype.ObjAct, "ObjAct", "MSB ObjAct (Object Action) Events"),
            (MSBEventSubtype.SpawnPoint, "Spawn Point", "MSB Spawn Point Events"),
            (MSBEventSubtype.MapOffset, "Map Offset", "MSB Map Offset Events"),
            (MSBEventSubtype.Navigation, "Navigation", "MSB Navigation Events"),
            (MSBEventSubtype.Environment, "Environment", "MSB Environment Events"),
            (MSBEventSubtype.NPCInvasion, "NPC Invasion", "MSB NPC Invasion Events"),
        ],
        default="ALL",
    )

    event_color_active_collection_only: bpy.props.BoolProperty(
        name="Active Collection Only",
        description="Only color MSB Events in the active collection or a child of it",
        default=True,
    )
