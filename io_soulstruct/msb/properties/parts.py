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
    "MSBProtobossProps",
    "MSBNavmeshProps",
    "MSBConnectCollisionProps",
]

from enum import StrEnum

from soulstruct.darksouls1ptde.maps.enums import CollisionHitFilter
from soulstruct.games import *

import bpy
from io_soulstruct.types import SoulstructType
from .events import MSBEventSubtype


class MSBPartSubtype(StrEnum):
    """Union of Part subtypes across all games."""
    MapPiece = "MSB_MAP_PIECE"
    Object = "MSB_OBJECT"
    Asset = "MSB_ASSET"
    Character = "MSB_CHARACTER"
    PlayerStart = "MSB_PLAYER_START"
    Collision = "MSB_COLLISION"
    Protoboss = "MSB_PROTOBOSS"
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
def _update_part_model(self: MSBPartProps, context):
    """Set the data-block of this (Mesh) object to `model.data`."""
    if self.model:
        if (
            self.model.type == "MESH"
            and (
                self.model.get("MSB_MODEL_PLACEHOLDER", False)
                or self.model.soulstruct_type in {
                    SoulstructType.FLVER, SoulstructType.COLLISION, SoulstructType.NAVMESH
                }
            )
        ):
            # Valid or placeholder model has been set. Link mesh data.
            self.id_data.data = self.model.data
            # print(f"INFO: Assigned data of model '{self.model.name}' to Part mesh '{self.id_data.name}'.")
        else:
            # Reject model.
            # print(f"INFO: Rejected assignment of model '{self.model.name}' to Part mesh '{self.id_data.name}'.")
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


def _is_environment_event(_, obj: bpy.types.Object):
    return (
        obj.soulstruct_type == SoulstructType.MSB_EVENT
        and obj.MSB_EVENT.event_subtype == MSBEventSubtype.Environment
    )


def _is_model(_, obj: bpy.types.Object):
    """Only allow models that are FLVER, COLLISION, or NAVMESH Mesh objects."""
    return obj.type == "MESH" and obj.soulstruct_type in {
        SoulstructType.FLVER, SoulstructType.COLLISION, SoulstructType.NAVMESH
    }


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
            (MSBPartSubtype.Protoboss, "Protoboss", "MSB Protoboss object (DeS only)"),
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
        poll=_is_model,
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

    unk_x0e: bpy.props.IntProperty(
        name="Unknown x0E (DeS)",
        description="Unknown DeS-specific Part field",
        default=0,
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

    def get_game_props(self, game: Game) -> list[str]:
        if game is DARK_SOULS_DSR or game is DARK_SOULS_PTDE:
            return [
                p for p in self.__annotations__
                if p != "unk_x0e"
            ]
        return list(self.__annotations__)


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
        poll=_is_part,
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
    unk_x0e: bpy.props.IntProperty(
        name="Unknown x0E",
        default=0,
    )
    unk_x10: bpy.props.IntProperty(
        name="Unknown x10",
        default=0,
    )

    def get_game_props(self, game: Game) -> list[str]:
        if game is DEMONS_SOULS:
            return [
                p for p in self.__annotations__
                if p != "draw_parent"
            ]
        return list(self.__annotations__)


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
        poll=_is_part,
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
        poll=_is_part,
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
        poll=_is_region,
    )
    patrol_regions_1: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Patrol Region 1",
        description="Patrol region 1 for character",
        poll=_is_region,
    )
    patrol_regions_2: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Patrol Region 2",
        description="Patrol region 2 for character",
        poll=_is_region,
    )
    patrol_regions_3: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Patrol Region 3",
        description="Patrol region 3 for character",
        poll=_is_region,
    )
    patrol_regions_4: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Patrol Region 4",
        description="Patrol region 4 for character",
        poll=_is_region,
    )
    patrol_regions_5: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Patrol Region 5",
        description="Patrol region 5 for character",
        poll=_is_region,
    )
    patrol_regions_6: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Patrol Region 6",
        description="Patrol region 6 for character",
        poll=_is_region,
    )
    patrol_regions_7: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Patrol Region 7",
        description="Patrol region 7 for character",
        poll=_is_region,
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

    # DeS only:
    unk_x00: bpy.props.IntProperty(
        name="Unknown x00 (DeS)",
        description="Unknown DeS-specific Character field",
        default=0,
    )
    unk_x04: bpy.props.IntProperty(
        name="Unknown x04 (DeS)",
        description="Unknown DeS-specific Character field",
        default=0,
    )
    unk_x08: bpy.props.FloatProperty(
        name="Unknown x08 (DeS)",
        description="Unknown DeS-specific Character field",
        default=0.0,
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

    def get_game_props(self, game: Game) -> list[str]:
        if game is DEMONS_SOULS:
            return [
                p for p in self.__annotations__
                if p != "ai_id"
            ]
        return list(self.__annotations__)


class MSBPlayerStartProps(bpy.types.PropertyGroup):

    unk_x00: bpy.props.IntProperty(
        name="Unknown x00 (DeS)",
        description="Unknown DeS-specific PlayerStart field",
        default=0,
    )

    def get_game_props(self, game: Game) -> list[str]:
        if game is not DEMONS_SOULS:
            return []

        return list(self.__annotations__)


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
    # NOTE: This property is set AFTER full MSB import out of necessity.
    environment_event: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Environment Event",
        description="Environment ('GI') event that describes the lighting cubemaps used on this collision. That "
                    "same event will almost always be attached to this collision",
        poll=_is_environment_event,
    )
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

    # DeS only:

    cubemap_index: bpy.props.IntProperty(
        name="Cubemap Index (DeS)",
        description="Index of cubemap to use for this collision (DeS only)",
        default=0,
    )

    ref_tex_ids_0: bpy.props.IntProperty(
        name="Ref Tex IDs [0] (DeS)",
        description="Reference texture IDs for this collision (DeS only)",
        default=0,
    )
    ref_tex_ids_1: bpy.props.IntProperty(
        name="Ref Tex IDs [1] (DeS)",
        description="Reference texture IDs for this collision (DeS only)",
        default=0,
    )
    ref_tex_ids_2: bpy.props.IntProperty(
        name="Ref Tex IDs [2] (DeS)",
        description="Reference texture IDs for this collision (DeS only)",
        default=0,
    )
    ref_tex_ids_3: bpy.props.IntProperty(
        name="Ref Tex IDs [3] (DeS)",
        description="Reference texture IDs for this collision (DeS only)",
        default=0,
    )
    ref_tex_ids_4: bpy.props.IntProperty(
        name="Ref Tex IDs [4] (DeS)",
        description="Reference texture IDs for this collision (DeS only)",
        default=0,
    )
    ref_tex_ids_5: bpy.props.IntProperty(
        name="Ref Tex IDs [5] (DeS)",
        description="Reference texture IDs for this collision (DeS only)",
        default=0,
    )
    ref_tex_ids_6: bpy.props.IntProperty(
        name="Ref Tex IDs [6] (DeS)",
        description="Reference texture IDs for this collision (DeS only)",
        default=0,
    )
    ref_tex_ids_7: bpy.props.IntProperty(
        name="Ref Tex IDs [7] (DeS)",
        description="Reference texture IDs for this collision (DeS only)",
        default=0,
    )
    ref_tex_ids_8: bpy.props.IntProperty(
        name="Ref Tex IDs [8] (DeS)",
        description="Reference texture IDs for this collision (DeS only)",
        default=0,
    )
    ref_tex_ids_9: bpy.props.IntProperty(
        name="Ref Tex IDs [9] (DeS)",
        description="Reference texture IDs for this collision (DeS only)",
        default=0,
    )
    ref_tex_ids_10: bpy.props.IntProperty(
        name="Ref Tex IDs [10] (DeS)",
        description="Reference texture IDs for this collision (DeS only)",
        default=0,
    )
    ref_tex_ids_11: bpy.props.IntProperty(
        name="Ref Tex IDs [11] (DeS)",
        description="Reference texture IDs for this collision (DeS only)",
        default=0,
    )
    ref_tex_ids_12: bpy.props.IntProperty(
        name="Ref Tex IDs [12] (DeS)",
        description="Reference texture IDs for this collision (DeS only)",
        default=0,
    )
    ref_tex_ids_13: bpy.props.IntProperty(
        name="Ref Tex IDs [13] (DeS)",
        description="Reference texture IDs for this collision (DeS only)",
        default=0,
    )
    ref_tex_ids_14: bpy.props.IntProperty(
        name="Ref Tex IDs [14] (DeS)",
        description="Reference texture IDs for this collision (DeS only)",
        default=0,
    )
    ref_tex_ids_15: bpy.props.IntProperty(
        name="Ref Tex IDs [15] (DeS)",
        description="Reference texture IDs for this collision (DeS only)",
        default=0,
    )

    def get_ref_tex_ids(self) -> list[int]:
        return [getattr(self, f"ref_tex_ids_{i}") for i in range(16)]

    unk_x38: bpy.props.IntProperty(
        name="Unknown x38 (DeS)",
        description="Unknown DeS-specific Collision field",
        default=0,
    )

    def get_game_props(self, game: Game) -> list[str]:
        if game is DEMONS_SOULS:
            exclude = {
                "play_region_id",
                "stable_footing_flag",
                "camera_1_id",
                "camera_2_id",
                "unk_x27_x28",
                "attached_bonfire",
                "vagrant_entity_ids_0",
                "vagrant_entity_ids_1",
                "vagrant_entity_ids_2",
                "starts_disabled",
            }
            return [
                p for p in self.__annotations__
                if p not in exclude
            ]
        elif game is DARK_SOULS_PTDE or game is DARK_SOULS_DSR:
            exclude = {
                "unk_x38",
                "cubemap_index",
            }
            return [
                p for p in self.__annotations__
                if not p.startswith("ref_tex_ids")
                if p not in exclude
            ]

        return list(self.__annotations__)


class MSBProtobossProps(bpy.types.PropertyGroup):
    """Only used in Demon's Souls, but doesn't appear in any final MSB files. TODO."""

    unk_x00: bpy.props.FloatProperty(
        name="Unk x00",
        description="Unknown Protoboss field",
        default=0.0,
    )
    unk_x04: bpy.props.FloatProperty(
        name="Unk x04",
        description="Unknown Protoboss field",
        default=0.0,
    )
    unk_x08: bpy.props.FloatProperty(
        name="Unk x08",
        description="Unknown Protoboss field",
        default=0.0,
    )
    unk_x0c: bpy.props.FloatProperty(
        name="Unk x0c",
        description="Unknown Protoboss field",
        default=0.0,
    )
    unk_x10: bpy.props.IntProperty(
        name="Unk x10",
        description="Unknown Protoboss field",
        default=0,
    )
    unk_x14: bpy.props.IntProperty(
        name="Unk x14",
        description="Unknown Protoboss field",
        default=0,
    )
    unk_x18: bpy.props.FloatProperty(
        name="Unk x18",
        description="Unknown Protoboss field",
        default=0.0,
    )
    unk_x1c: bpy.props.FloatProperty(
        name="Unk x1c",
        description="Unknown Protoboss field",
        default=0.0,
    )
    unk_x20: bpy.props.IntProperty(
        name="Unk x20",
        description="Unknown Protoboss field",
        default=0,
    )
    unk_x24: bpy.props.IntProperty(
        name="Unk x24",
        description="Unknown Protoboss field",
        default=0,
    )
    unk_x28: bpy.props.FloatProperty(
        name="Unk x28",
        description="Unknown Protoboss field",
        default=0.0,
    )
    unk_x2c: bpy.props.IntProperty(
        name="Unk x2c",
        description="Unknown Protoboss field",
        default=0,
    )
    unk_x30: bpy.props.IntProperty(
        name="Unk x30",
        description="Unknown Protoboss field",
        default=0,
    )


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

    # noinspection PyUnusedLocal
    def get_game_props(self, game: Game) -> list[str]:
        return list(self.__annotations__)


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

    # noinspection PyUnusedLocal
    def get_game_props(self, game: Game) -> list[str]:
        return list(self.__annotations__)
