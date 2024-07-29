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
    "MSBRegionProps",
]

import bpy
from soulstruct.utilities.future import StrEnum
from io_soulstruct.types import SoulstructType


class MSBPartSubtype(StrEnum):
    NONE = "NONE"
    MAP_PIECE = "MSB_MAP_PIECE"
    OBJECT = "MSB_OBJECT"
    ASSET = "MSB_ASSET"
    CHARACTER = "MSB_CHARACTER"
    PLAYER_START = "MSB_PLAYER_START"
    COLLISION = "MSB_COLLISION"
    NAVMESH = "MSB_NAVMESH"
    CONNECT_COLLISION = "MSB_CONNECT_COLLISION"
    OTHER = "MSB_OTHER"

    def get_nice_name(self) -> str:
        return f"{self.value.replace('MSB_', '').replace('_', ' ').title()}"

    def is_flver(self) -> bool:
        return self in {MSBPartSubtype.MAP_PIECE, MSBPartSubtype.OBJECT, MSBPartSubtype.ASSET, MSBPartSubtype.CHARACTER}

    def is_map_geometry(self) -> bool:
        """TODO: Asset is ambiguous here."""
        return self in {MSBPartSubtype.MAP_PIECE, MSBPartSubtype.COLLISION, MSBPartSubtype.NAVMESH}


# noinspection PyUnusedLocal
def _update_part_model(self, context):
    """Set the data-block of this (Mesh) object to `model.data`."""
    if self.model:
        if self.model.soulstruct_type not in {SoulstructType.FLVER, SoulstructType.COLLISION, SoulstructType.NAVMESH}:
            # Reject model.
            self.model = None  # will not cause this `if` block to recur
        else:
            # Link Part mesh data to model mesh data.
            self.data = self.model.data


class MSBPartProps(bpy.types.PropertyGroup):
    part_subtype: bpy.props.EnumProperty(
        name="MSB Part Subtype",
        description="MSB subtype of this Part object",
        items=[
            (MSBPartSubtype.NONE, "None", "Not an MSB Part"),
            (MSBPartSubtype.MAP_PIECE, "Map Piece", "MSB MapPiece object"),
            (MSBPartSubtype.OBJECT, "Object", "MSB Object object"),
            (MSBPartSubtype.ASSET, "Asset", "MSB Asset object"),
            (MSBPartSubtype.CHARACTER, "Character", "MSB Character object"),
            (MSBPartSubtype.PLAYER_START, "Player Start", "MSB PlayerStart object"),
            (MSBPartSubtype.COLLISION, "Collision", "MSB Collision object"),
            (MSBPartSubtype.NAVMESH, "Navmesh", "MSB Navmesh object"),
            (MSBPartSubtype.CONNECT_COLLISION, "Connect Collision", "MSB Connect Collision object"),
            (MSBPartSubtype.OTHER, "Other", "MSB Other object"),
        ],
        default=MSBPartSubtype.NONE,
    )

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
    entity_id: bpy.props.IntProperty(name="Entity ID", default=-1)

    draw_groups_0: bpy.props.BoolVectorProperty(
        name="Draw Groups [0, 31]",
        description="Draw groups 0 to 31 for this MSB Part object",
        size=32,
        default=[False] * 32,
    )
    draw_groups_1: bpy.props.BoolVectorProperty(
        name="Draw Groups [32, 63]",
        description="Draw groups 32 to 63 for this MSB Part object",
        size=32,
        default=[False] * 32,
    )
    draw_groups_2: bpy.props.BoolVectorProperty(
        name="Draw Groups [64, 95]",
        description="Draw groups 64 to 95 for this MSB Part object",
        size=32,
        default=[False] * 32,
    )
    draw_groups_3: bpy.props.BoolVectorProperty(
        name="Draw Groups [96, 127]",
        description="Draw groups 96 to 127 for this MSB Part object",
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
        description="Display groups 0 to 31 for this MSB Part object",
        size=32,
        default=[False] * 32,
    )
    display_groups_1: bpy.props.BoolVectorProperty(
        name="Display Groups [32, 63]",
        description="Display groups 32 to 63 for this MSB Part object",
        size=32,
        default=[False] * 32,
    )
    display_groups_2: bpy.props.BoolVectorProperty(
        name="Display Groups [64, 95]",
        description="Display groups 64 to 95 for this MSB Part object",
        size=32,
        default=[False] * 32,
    )
    display_groups_3: bpy.props.BoolVectorProperty(
        name="Display Groups [96, 127]",
        description="Display groups 96 to 127 for this MSB Part object",
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
        name="Ambient Light DrawParam ID",
        description="Draw parameter ID for this MSB Part object",
        default=-1,
    )
    fog_id: bpy.props.IntProperty(
        name="Fog DrawParam ID",
        description="Draw parameter ID for this MSB Part object",
        default=-1,
    )
    scattered_light_id: bpy.props.IntProperty(
        name="Scattered Light DrawParam ID",
        description="Draw parameter ID for this MSB Part object",
        default=-1,
    )
    lens_flare_id: bpy.props.IntProperty(
        name="Lens Flare DrawParam ID",
        description="Draw parameter ID for this MSB Part object",
        default=-1,
    )
    shadow_id: bpy.props.IntProperty(
        name="Shadow DrawParam ID",
        description="Draw parameter ID for this MSB Part object",
        default=-1,
    )
    dof_id: bpy.props.IntProperty(
        name="Depth of Field DrawParam ID",
        description="Draw parameter ID for this MSB Part object",
        default=-1,
    )
    tone_map_id: bpy.props.IntProperty(
        name="Tone Map DrawParam ID",
        description="Draw parameter ID for this MSB Part object",
        default=-1,
    )
    point_light_id: bpy.props.IntProperty(
        name="Point Light DrawParam ID",
        description="Draw parameter ID for this MSB Part object",
        default=-1,
    )
    tone_correction_id: bpy.props.IntProperty(
        name="Tone Correction DrawParam ID",
        description="Draw parameter ID for this MSB Part object",
        default=-1,
    )
    lod_id: bpy.props.IntProperty(
        name="Level of Detail ID",
        description="Level of Detail ID for this MSB Part object",
        default=-1,
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
        name="Player ID",
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


class MSBPlayerStartProps(bpy.types.PropertyGroup):
    """No additional properties."""
    pass


class MSBCollisionProps(bpy.types.PropertyGroup):
    navmesh_groups_0: bpy.props.BoolVectorProperty(
        name="Navmesh Groups [0, 31]",
        description="Navmesh groups 0 to 31 for this collision",
        size=32,
        default=[False] * 32,
    )
    navmesh_groups_1: bpy.props.BoolVectorProperty(
        name="Navmesh Groups [32, 63]",
        description="Navmesh groups 32 to 63 for this collision",
        size=32,
        default=[False] * 32,
    )
    navmesh_groups_2: bpy.props.BoolVectorProperty(
        name="Navmesh Groups [64, 95]",
        description="Navmesh groups 64 to 95 for this collision",
        size=32,
        default=[False] * 32,
    )
    navmesh_groups_3: bpy.props.BoolVectorProperty(
        name="Navmesh Groups [96, 127]",
        description="Navmesh groups 96 to 127 for this collision",
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
            ("NoHiHitNoFeetIK", "NoHiHitNoFeetIK", "NoHiHitNoFeetIK"),  # solid
            ("NoHiHit_1", "NoHiHit_1", "NoHiHit_1"),  # solid
            ("NoHiHit_2", "NoHiHit_2", "NoHiHit_2"),  # solid
            ("NoHiHit_3", "NoHiHit_3", "NoHiHit_3"),  # solid
            ("NoHiHit_4", "NoHiHit_4", "NoHiHit_4"),  # solid
            ("NoHiHit_5", "NoHiHit_5", "NoHiHit_5"),  # solid
            ("NoHiHit_6", "NoHiHit_6", "NoHiHit_6"),  # solid
            ("NoHiHit_7", "NoHiHit_7", "NoHiHit_7"),  # solid
            ("Normal", "Normal", "Normal"),  # solid
            ("Water_A", "Water_A", "Water_A"),  # blue
            ("Unknown_10", "Unknown_10", "Unknown_10"),
            ("Solid_ForNPCsOnly_A", "Solid_ForNPCsOnly_A", "Solid_ForNPCsOnly_A"),  # blue
            ("Unknown_12", "Unknown_12", "Unknown_12"),
            ("DeathCam", "DeathCam", "DeathCam"),  # white
            ("LethalFall", "LethalFall", "LethalFall"),  # red
            ("KillPlane", "KillPlane", "KillPlane"),  # black
            ("Water_B", "Water_B", "Water_B"),  # dark blue
            ("GroupSwitch", "GroupSwitch", "GroupSwitch"),  # turquoise; in elevator shafts
            ("Unknown_18", "Unknown_18", "Unknown_18"),
            ("Solid_ForNPCsOnly_B", "Solid_ForNPCsOnly_B", "Solid_ForNPCsOnly_B"),  # turquoise
            ("LevelExit_A", "LevelExit_A", "LevelExit_A"),  # purple
            ("Slide", "Slide", "Slide"),  # yellow
            ("FallProtection", "FallProtection", "FallProtection"),  # permeable for projectiles
            ("LevelExit_B", "LevelExit_B", "LevelExit_B"),  # glowing turquoise
        ],
        default="Normal",
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
    )
    force_place_name_banner: bpy.props.BoolProperty(
        name="Force Place Name Banner",
        description="If enabled, the Place Name Banner will be displayed as long as it is a new banner ID, rather than "
                    "only showing on game load. Must be enabled if using map's default banner ID (-1)",
        default=True,
    )
    play_region_id: bpy.props.IntProperty(
        name="Play Region ID",
        description="Online/multiplayer play region ID for this collision. Must be set to 0 if a non-zero Stable "
                    "Footing Flag is set",
        default=0,
    )
    stable_footing_flag: bpy.props.IntProperty(
        name="Stable Footing Flag",
        description="If non-zero, this flag must be enabled for this collision to be considered stable ground. Must be "
                    "set to 0 if a non-zero Play Region ID is set",
        default=0,
    )
    camera_1_id: bpy.props.IntProperty(
        name="Camera 1 ID",
        description="Primary camera ID (LockCamParam) to switch to when player steps on this collision",
        default=-1,
    )
    camera_2_id: bpy.props.IntProperty(
        name="Camera 1 ID",
        description="Secondary camera ID (LockCamParam) to switch to when player steps on this collision",
        default=-1,
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
    )
    environment_event: bpy.props.PointerProperty(
        name="Environment Event (Cubemap)",
        description="MSB Environment Event (cubemap) to use for specular reflection on this collision",
        type=bpy.types.Object,
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
    )
    vagrant_entity_ids_1: bpy.props.IntProperty(
        name="Vagrant Entity ID [1]",
        description="Entity ID of Vagrant that can appear on this collision",
        default=-1,
    )
    vagrant_entity_ids_2: bpy.props.IntProperty(
        name="Vagrant Entity ID [2]",
        description="Entity ID of Vagrant that can appear on this collision",
        default=-1,
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


class MSBNavmeshProps(bpy.types.PropertyGroup):
    navmesh_groups_0: bpy.props.BoolVectorProperty(
        name="Navmesh Groups [0, 31]",
        description="Navmesh groups 0 to 31 for this navmesh",
        size=32,
        default=[False] * 32,
    )
    navmesh_groups_1: bpy.props.BoolVectorProperty(
        name="Navmesh Groups [32, 63]",
        description="Navmesh groups 32 to 63 for this navmesh",
        size=32,
        default=[False] * 32,
    )
    navmesh_groups_2: bpy.props.BoolVectorProperty(
        name="Navmesh Groups [64, 95]",
        description="Navmesh groups 64 to 95 for this navmesh",
        size=32,
        default=[False] * 32,
    )
    navmesh_groups_3: bpy.props.BoolVectorProperty(
        name="Navmesh Groups [96, 127]",
        description="Navmesh groups 96 to 127 for this navmesh",
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
        poll=lambda self, obj: obj.soulstruct_type == SoulstructType.COLLISION,
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


class MSBRegionShape(StrEnum):
    NONE = "None"
    POINT = "Point"
    SPHERE = "Sphere"
    CYLINDER = "Cylinder"
    BOX = "Box"


class MSBRegionSubtype(StrEnum):
    NONE = "None"
    NA = "N/A"


class MSBRegionProps(bpy.types.PropertyGroup):
    entity_id: bpy.props.IntProperty(
        name="Entity ID",
        default=-1
    )

    region_subtype: bpy.props.EnumProperty(
        name="MSB Region Subtype",
        description="MSB subtype (shape) of this Region object",
        items=[
            (MSBRegionSubtype.NONE, "None", "Not an MSB Region"),
            (MSBRegionSubtype.NA, "N/A", "Older game with no region subtypes (only shapes)"),
            # TODO: ER subtypes...
        ],
        default=MSBRegionSubtype.NONE,
    )

    # TODO: Not a real `MSBRegion` field (sub-struct) yet, but WILL BE.
    shape: bpy.props.EnumProperty(
        name="MSB Region Subtype",
        description="MSB subtype (shape) of this Region object",
        items=[
            (MSBRegionShape.NONE, "None", "Not an MSB Region"),
            (MSBRegionShape.POINT, "Point", "Point with location and rotation only"),
            # NOTE: 2D region shapes not supported (never used in game AFAIK).
            (MSBRegionShape.SPHERE, "Sphere", "Volume region defined by radius (max of X/Y/Z scale)"),
            (MSBRegionShape.CYLINDER, "Cylinder", "Volume region with radius (X/Y scale max) and height (Z scale)"),
            (MSBRegionShape.BOX, "Box", "Volume region defined by X/Y/Z scale"),
        ],
        default=MSBRegionShape.NONE,
    )


# TODO: MSB Event subtype/property support.
#   - Most should just attach to Regions and basically be treated as such.
#       - Complication is separate, usable entity IDs for events and regions.
#   - Can color-code their regions where present.
