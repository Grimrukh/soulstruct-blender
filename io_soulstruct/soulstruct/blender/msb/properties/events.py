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
    "BlenderMSBEventSubtype",
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
]

import re
from enum import StrEnum

import bpy

from soulstruct.base.maps.msb.enums import BaseMSBEventSubtype
from soulstruct.darksouls1ptde.events.enums import SoundType
from soulstruct.games import *

from soulstruct.blender.bpy_base.property_group import SoulstructPropertyGroup
from soulstruct.blender.types import SoulstructType


def _is_part(_, obj: bpy.types.Object):
    return obj.soulstruct_type == SoulstructType.MSB_PART


def _is_region(_, obj: bpy.types.Object):
    return obj.soulstruct_type == SoulstructType.MSB_REGION


class BlenderMSBEventSubtype(StrEnum):
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

    @classmethod
    def from_msb_event_subtype(cls, subtype: BaseMSBEventSubtype) -> BaseMSBEventSubtype:
        try:
            # noinspection PyTypeChecker
            return cls[subtype.name]
        except KeyError:
            raise ValueError(f"Unsupported Blender MSB Event subtype: {subtype}")


class MSBEventProps(SoulstructPropertyGroup):

    GAME_PROP_NAMES = {
        DEMONS_SOULS: (
            "entry_subtype",

            "entity_id",
            "attached_part",
            "attached_region",
        ),
        DARK_SOULS_PTDE: (
            "entry_subtype",

            "entity_id",
            "attached_part",
            "attached_region",
            "unknowns",
        ),
    }

    entry_subtype: bpy.props.EnumProperty(
        name="Event Subtype",
        description="MSB subtype of this Event object",
        items=[
            ("NONE", "None", "Not an MSB Event"),
            (BlenderMSBEventSubtype.Light, "Light", "MSB Light Event"),
            (BlenderMSBEventSubtype.Sound, "Sound", "MSB Sound Event"),
            (BlenderMSBEventSubtype.VFX, "VFX", "MSB VFX Event"),
            (BlenderMSBEventSubtype.Wind, "Wind", "MSB Wind Event"),
            (BlenderMSBEventSubtype.Treasure, "Treasure", "MSB Treasure Event"),
            (BlenderMSBEventSubtype.Spawner, "Spawner", "MSB Spawner Event"),
            (BlenderMSBEventSubtype.Message, "Message", "MSB Message Event"),
            (BlenderMSBEventSubtype.ObjAct, "ObjAct", "MSB ObjAct (Object Action) Event"),
            (BlenderMSBEventSubtype.SpawnPoint, "Spawn Point", "MSB Spawn Point Event"),
            (BlenderMSBEventSubtype.MapOffset, "Map Offset", "MSB Map Offset Event"),
            (BlenderMSBEventSubtype.Navigation, "Navigation", "MSB Navigation Event"),
            (BlenderMSBEventSubtype.Environment, "Environment", "MSB Environment Event"),
            (BlenderMSBEventSubtype.NPCInvasion, "NPC Invasion", "MSB NPC Invasion Event"),
        ],
        default="NONE",
        update=lambda self, context: self._update_name_suffix(context),
    )

    @property
    def entry_subtype_enum(self) -> BlenderMSBEventSubtype:
        if self.entry_subtype == "NONE":
            raise ValueError("MSB Event subtype is not set.")
        return BlenderMSBEventSubtype(self.entry_subtype)

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
        description="Four unknown integer values for Events (DS1)",
        size=4,
        default=(0, 0, 0, 0),
    )

    _EVENT_NAME_RE = re.compile(r"^(.*)<(.+)>(\.\d+)?$")

    def _update_name_suffix(self, _):
        """Update suffix is one current exists. Preserves dupe suffix."""
        if match := self._EVENT_NAME_RE.match(self.name):
            old_suffix = match.group(2)
            if old_suffix in BlenderMSBEventSubtype.__members__:
                obj = self.id_data  # type: bpy.types.Object
                name = match.group(1).strip()
                dupe_suffix = match.group(3) or ""
                obj.name = f"{name} <{BlenderMSBEventSubtype.get_enum_name(obj.MSB_EVENT.entry_subtype)}>{dupe_suffix}"


class MSBLightEventProps(SoulstructPropertyGroup):

    GAME_PROP_NAMES = {
        DEMONS_SOULS: (
            "point_light_id",
            "unk_x04",
        ),
        DARK_SOULS_PTDE: (
            "point_light_id",
        ),
    }

    point_light_id: bpy.props.IntProperty(
        name="Point Light ID",
        description="DrawParam ID of the point light to attach to this MSB Light Event",
        default=-1,
        min=-1,
        max=255,
    )

    unk_x04: bpy.props.IntProperty(
        name="Unknown x04 (DeS)",
        description="Unknown integer value in DeS Light event",
        default=0,
    )


class MSBSoundEventProps(SoulstructPropertyGroup):

    GAME_PROP_NAMES = {
        DEMONS_SOULS: (
            "sound_type",
            "sound_id",
            "unk_x00",
        ),
        DARK_SOULS_PTDE: (
            "sound_type",
            "sound_id",
        ),
    }

    sound_type: bpy.props.EnumProperty(
        name="Sound Type",
        description="Type of sound to play. Determines sound file prefix letter",
        # TODO: Using DS1 `SoundType` enum for now.
        items=[
            (sound_type.name, sound_type.name, sound_type.name.split("_", 1)[1].title())
            for sound_type in SoundType
        ],
        default="s_SFX",
    )

    sound_id: bpy.props.IntProperty(
        name="Sound ID",
        description="ID of the sound to play",
        default=0,
        min=0,
    )

    unk_x00: bpy.props.IntProperty(
        name="Unknown x00 (DeS)",
        description="Unknown integer value in DeS Sound event",
        default=0,
    )


class MSBVFXEventProps(SoulstructPropertyGroup):

    GAME_PROP_NAMES = {
        DEMONS_SOULS: (
            "vfx_id",
            "unk_x00",
        ),
        DARK_SOULS_PTDE: (
            "vfx_id",
        ),
    }

    vfx_id: bpy.props.IntProperty(
        name="VFX ID",
        description="ID of the VFX to play",
        default=0,
        min=0,
    )

    unk_x00: bpy.props.IntProperty(
        name="Unknown x00 (DeS)",
        description="Unknown integer value in DeS VFX event",
        default=0,
    )


class MSBWindEventProps(SoulstructPropertyGroup):

    GAME_PROP_NAMES = {
        DEMONS_SOULS: (
            "wind_vector_min",
            "unk_x0c",
            "wind_vector_max",
            "unk_x1c",
            "wind_swing_cycles",
            "wind_swing_powers",
        ),
        DARK_SOULS_PTDE: (
            "wind_vector_min",
            "unk_x0c",
            "wind_vector_max",
            "unk_x1c",
            "wind_swing_cycles",
            "wind_swing_powers",
        ),
    }

    wind_vector_min: bpy.props.FloatVectorProperty(
        name="Wind Vector (Min)",
        description="Wind vector minimum",
        default=(0.0, 0.0, 0.0),
    )
    unk_x0c: bpy.props.FloatProperty(
        name="Unk x0c",
        description="Unknown scalar related to wind vector minimum",
        default=0.0,
    )
    wind_vector_max: bpy.props.FloatVectorProperty(
        name="Wind Vector (Max)",
        description="Wind vector maximum",
        default=(0.0, 0.0, 0.0),
    )
    unk_x1c: bpy.props.FloatProperty(
        name="Unk x1c",
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


class MSBTreasureEventProps(SoulstructPropertyGroup):

    GAME_PROP_NAMES = {
        DEMONS_SOULS: (
            "treasure_part",
            "item_lot_1",
            "item_lot_2",
            "item_lot_3",
            "item_lot_4",
            "item_lot_5",
        ),
        DARK_SOULS_PTDE: (
            "treasure_part",
            "item_lot_1",
            "item_lot_2",
            "item_lot_3",
            "item_lot_4",
            "item_lot_5",
            "is_in_chest",
            "is_hidden",
        ),
    }

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


class MSBSpawnerEventProps(SoulstructPropertyGroup):

    GAME_PROP_NAMES = {
        DEMONS_SOULS: (
            "max_count",
            "spawner_type",
            "limit_count",
            "min_spawner_count",
            "max_spawner_count",
            "min_interval",
            "max_interval",
            "initial_spawn_count",
        ) + tuple(f"spawn_parts_{i}" for i in range(32)) + tuple(f"spawn_regions_{i}" for i in range(4)),
        DARK_SOULS_PTDE: (
            "max_count",
            "spawner_type",
            "limit_count",
            "min_spawner_count",
            "max_spawner_count",
            "min_interval",
            "max_interval",
            "initial_spawn_count",
        ) + tuple(f"spawn_parts_{i}" for i in range(32)) + tuple(f"spawn_regions_{i}" for i in range(4)),
    }

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

    max_interval: bpy.props.FloatProperty(
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


class MSBMessageEventProps(SoulstructPropertyGroup):

    GAME_PROP_NAMES = {
        DEMONS_SOULS: (
            "unk_x00",
            "text_id",
            "text_param",
        ),
        DARK_SOULS_PTDE: (
            "text_id",
            "unk_x02",
            "is_hidden",
        ),
    }

    text_id: bpy.props.IntProperty(
        name="Text ID",
        description="Soapstone message ID to display",
        default=-1,
    )
    unk_x02: bpy.props.IntProperty(
        name="Unk x02 (DS1)",
        description="Unknown integer value in DS1 Messages",
        default=2,
    )
    is_hidden: bpy.props.BoolProperty(
        name="Is Hidden",
        description="If enabled, message is disabled on load and must be enabled with EMEVD",
        default=False,
    )

    unk_x00: bpy.props.IntProperty(
        name="Unk x00 (DeS)",
        description="Unknown integer value in DeS Messages",
        default=0,
    )
    text_param: bpy.props.IntProperty(
        name="Text Param ID (DeS)",
        description="TextParam ID to use for this message (DeS)",
        default=-1,
    )


class MSBObjActEventProps(SoulstructPropertyGroup):

    GAME_PROP_NAMES = {
        DARK_SOULS_PTDE: (
            "obj_act_entity_id",
            "obj_act_part",
            "obj_act_param_id",
            "obj_act_state",
            "obj_act_flag",
        ),
    }

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


class MSBSpawnPointEventProps(SoulstructPropertyGroup):

    GAME_PROP_NAMES = {
        DARK_SOULS_PTDE: (
            "spawn_point_region",
        ),
    }

    spawn_point_region: bpy.props.PointerProperty(
        name="Spawn Point Region",
        description="MSB Region object defining the spawn point location. Replaces base MSB Event Attached Region",
        type=bpy.types.Object,
        poll=_is_region,
    )


class MSBMapOffsetEventProps(SoulstructPropertyGroup):

    GAME_PROP_NAMES = {
        DARK_SOULS_PTDE: (
            "translate",
            "rotate_z",
        ),
    }

    translate: bpy.props.FloatVectorProperty(
        name="Translate",
        description="Translation offset for the map (in Blender coordinates)",
        default=(0.0, 0.0, 0.0),
    )

    rotate_z: bpy.props.FloatProperty(
        name="Rotate Z",
        description="Z-axis rotation offset for the map (in degrees around Blender's vertical Z axis)",
        default=0.0,
    )


class MSBNavigationEventProps(SoulstructPropertyGroup):

    GAME_PROP_NAMES = {
        DARK_SOULS_PTDE: (
            "navigation_region",
        ),
    }

    navigation_region: bpy.props.PointerProperty(
        name="Navigation Region",
        description="MSB Region object defining the area of the navigation mesh corresponding to this Entity ID. NOTE: "
                    "these events are dummy representations of events and IDs hard-coded into the NVM Navmesh model",
        type=bpy.types.Object,
        poll=_is_region,
    )


class MSBEnvironmentEventProps(SoulstructPropertyGroup):

    GAME_PROP_NAMES = {
        DARK_SOULS_PTDE: (
            "unk_x00_x04",
            "unk_x04_x08",
            "unk_x08_x0c",
            "unk_x0c_x10",
            "unk_x10_x14",
            "unk_x14_x18",
        ),
    }

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


class MSBNPCInvasionEventProps(SoulstructPropertyGroup):

    GAME_PROP_NAMES = {
        DARK_SOULS_PTDE: (
            "host_entity_id",
            "invasion_flag_id",
            "activate_good_id",
        ),
    }

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
