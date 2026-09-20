from __future__ import annotations

__all__ = [
    "BLENDER_MSB_PART_CLASSES",
    "BLENDER_MSB_REGION_CLASSES",
    "BLENDER_MSB_EVENT_CLASSES",
]

from soulstruct.games import GameType

from ..msb.types import darksouls1ptde, darksouls1r, demonssouls
from .properties import BlenderMSBPartSubtype, BlenderMSBRegionSubtype, BlenderMSBEventSubtype
from .types.base import BaseBlenderMSBPart, BaseBlenderMSBRegion, BaseBlenderMSBEvent


BLENDER_MSB_PART_CLASSES = {
    GameType.DemonsSouls: {
        BlenderMSBPartSubtype.MapPiece: demonssouls.BlenderMSBMapPiece,
        BlenderMSBPartSubtype.Object: demonssouls.BlenderMSBObject,
        BlenderMSBPartSubtype.Character: demonssouls.BlenderMSBCharacter,
        BlenderMSBPartSubtype.PlayerStart: demonssouls.BlenderMSBPlayerStart,
        BlenderMSBPartSubtype.Collision: demonssouls.BlenderMSBCollision,
        BlenderMSBPartSubtype.Protoboss: demonssouls.BlenderMSBProtoboss,
        BlenderMSBPartSubtype.Navmesh: demonssouls.BlenderMSBNavmesh,
        BlenderMSBPartSubtype.ConnectCollision: demonssouls.BlenderMSBConnectCollision,
    },
    GameType.DarkSoulsPTDE: {
        BlenderMSBPartSubtype.MapPiece: darksouls1ptde.BlenderMSBMapPiece,
        BlenderMSBPartSubtype.Object: darksouls1ptde.BlenderMSBObject,
        BlenderMSBPartSubtype.Character: darksouls1ptde.BlenderMSBCharacter,
        BlenderMSBPartSubtype.PlayerStart: darksouls1ptde.BlenderMSBPlayerStart,
        BlenderMSBPartSubtype.Collision: darksouls1ptde.BlenderMSBCollision,
        BlenderMSBPartSubtype.Navmesh: darksouls1ptde.BlenderMSBNavmesh,
        BlenderMSBPartSubtype.ConnectCollision: darksouls1ptde.BlenderMSBConnectCollision,
    },
    GameType.DarkSoulsDSR: {
        BlenderMSBPartSubtype.MapPiece: darksouls1r.BlenderMSBMapPiece,
        BlenderMSBPartSubtype.Object: darksouls1r.BlenderMSBObject,
        BlenderMSBPartSubtype.Character: darksouls1r.BlenderMSBCharacter,
        BlenderMSBPartSubtype.PlayerStart: darksouls1r.BlenderMSBPlayerStart,
        BlenderMSBPartSubtype.Collision: darksouls1r.BlenderMSBCollision,
        BlenderMSBPartSubtype.Navmesh: darksouls1r.BlenderMSBNavmesh,
        BlenderMSBPartSubtype.ConnectCollision: darksouls1r.BlenderMSBConnectCollision,
    },
}  # type: dict[GameType, dict[BlenderMSBPartSubtype, type[BaseBlenderMSBPart]]]


BLENDER_MSB_REGION_CLASSES = {
    GameType.DarkSoulsPTDE: {
        # No subtypes, only shapes.
        BlenderMSBRegionSubtype.All: darksouls1ptde.BlenderMSBRegion,
    },
    GameType.DarkSoulsDSR: {
        # No subtypes, only shapes. (Shares PTDE class.)
        BlenderMSBRegionSubtype.All: darksouls1ptde.BlenderMSBRegion,
    },
    GameType.DemonsSouls: {
        BlenderMSBRegionSubtype.All: demonssouls.BlenderMSBRegion,
    }
}  # type: dict[GameType, dict[BlenderMSBRegionSubtype, type[BaseBlenderMSBRegion]]]


BLENDER_MSB_EVENT_CLASSES = {
    GameType.DemonsSouls: {
        BlenderMSBEventSubtype.Light: demonssouls.BlenderMSBLightEvent,
        BlenderMSBEventSubtype.Sound: demonssouls.BlenderMSBSoundEvent,
        BlenderMSBEventSubtype.VFX: demonssouls.BlenderMSBVFXEvent,
        BlenderMSBEventSubtype.Wind: demonssouls.BlenderMSBWindEvent,
        BlenderMSBEventSubtype.Treasure: demonssouls.BlenderMSBTreasureEvent,
        BlenderMSBEventSubtype.Spawner: demonssouls.BlenderMSBSpawnerEvent,
        BlenderMSBEventSubtype.Message: demonssouls.BlenderMSBMessageEvent,
    },
    GameType.DarkSoulsPTDE: {
        BlenderMSBEventSubtype.Light: darksouls1ptde.BlenderMSBLightEvent,
        BlenderMSBEventSubtype.Sound: darksouls1ptde.BlenderMSBSoundEvent,
        BlenderMSBEventSubtype.VFX: darksouls1ptde.BlenderMSBVFXEvent,
        BlenderMSBEventSubtype.Wind: darksouls1ptde.BlenderMSBWindEvent,
        BlenderMSBEventSubtype.Treasure: darksouls1ptde.BlenderMSBTreasureEvent,
        BlenderMSBEventSubtype.Spawner: darksouls1ptde.BlenderMSBSpawnerEvent,
        BlenderMSBEventSubtype.Message: darksouls1ptde.BlenderMSBMessageEvent,
        BlenderMSBEventSubtype.ObjAct: darksouls1ptde.BlenderMSBObjActEvent,
        BlenderMSBEventSubtype.SpawnPoint: darksouls1ptde.BlenderMSBSpawnPointEvent,
        BlenderMSBEventSubtype.MapOffset: darksouls1ptde.BlenderMSBMapOffsetEvent,
        BlenderMSBEventSubtype.Navigation: darksouls1ptde.BlenderMSBNavigationEvent,
        BlenderMSBEventSubtype.Environment: darksouls1ptde.BlenderMSBEnvironmentEvent,
        BlenderMSBEventSubtype.NPCInvasion: darksouls1ptde.BlenderMSBNPCInvasionEvent,
    },
    GameType.DarkSoulsDSR: {
        BlenderMSBEventSubtype.Light: darksouls1r.BlenderMSBLightEvent,
        BlenderMSBEventSubtype.Sound: darksouls1r.BlenderMSBSoundEvent,
        BlenderMSBEventSubtype.VFX: darksouls1r.BlenderMSBVFXEvent,
        BlenderMSBEventSubtype.Wind: darksouls1r.BlenderMSBWindEvent,
        BlenderMSBEventSubtype.Treasure: darksouls1r.BlenderMSBTreasureEvent,
        BlenderMSBEventSubtype.Spawner: darksouls1r.BlenderMSBSpawnerEvent,
        BlenderMSBEventSubtype.Message: darksouls1r.BlenderMSBMessageEvent,
        BlenderMSBEventSubtype.ObjAct: darksouls1r.BlenderMSBObjActEvent,
        BlenderMSBEventSubtype.SpawnPoint: darksouls1r.BlenderMSBSpawnPointEvent,
        BlenderMSBEventSubtype.MapOffset: darksouls1r.BlenderMSBMapOffsetEvent,
        BlenderMSBEventSubtype.Navigation: darksouls1r.BlenderMSBNavigationEvent,
        BlenderMSBEventSubtype.Environment: darksouls1r.BlenderMSBEnvironmentEvent,
        BlenderMSBEventSubtype.NPCInvasion: darksouls1r.BlenderMSBNPCInvasionEvent,
    },
}  # type: dict[GameType, dict[BlenderMSBEventSubtype, type[BaseBlenderMSBEvent]]]
