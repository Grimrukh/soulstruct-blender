from __future__ import annotations

__all__ = [
    "BLENDER_MSB_PART_TYPES",
    "BLENDER_MSB_REGION_TYPES",
    "BLENDER_MSB_EVENT_TYPES",
]

from io_soulstruct.msb import darksouls1ptde, darksouls1r
from soulstruct.games import *
from .properties import MSBPartSubtype, MSBRegionSubtype, MSBEventSubtype


BLENDER_MSB_PART_TYPES = {
    DARK_SOULS_PTDE: {
        MSBPartSubtype.MapPiece: darksouls1ptde.BlenderMSBMapPiece,
        MSBPartSubtype.Object: darksouls1ptde.BlenderMSBObject,
        MSBPartSubtype.Character: darksouls1ptde.BlenderMSBCharacter,
        MSBPartSubtype.PlayerStart: darksouls1ptde.BlenderMSBPlayerStart,
        MSBPartSubtype.Collision: darksouls1ptde.BlenderMSBCollision,
        MSBPartSubtype.Navmesh: darksouls1ptde.BlenderMSBNavmesh,
        MSBPartSubtype.ConnectCollision: darksouls1ptde.BlenderMSBConnectCollision,
    },
    DARK_SOULS_DSR: {
        MSBPartSubtype.MapPiece: darksouls1r.BlenderMSBMapPiece,
        MSBPartSubtype.Object: darksouls1r.BlenderMSBObject,
        MSBPartSubtype.Character: darksouls1r.BlenderMSBCharacter,
        MSBPartSubtype.PlayerStart: darksouls1r.BlenderMSBPlayerStart,
        MSBPartSubtype.Collision: darksouls1r.BlenderMSBCollision,
        MSBPartSubtype.Navmesh: darksouls1r.BlenderMSBNavmesh,
        MSBPartSubtype.ConnectCollision: darksouls1r.BlenderMSBConnectCollision,
    },
}


BLENDER_MSB_REGION_TYPES = {
    DARK_SOULS_PTDE: {
        # No subtypes, only shapes.
        MSBRegionSubtype.All: darksouls1ptde.BlenderMSBRegion,
    },
    DARK_SOULS_DSR: {
        # No subtypes, only shapes.
        MSBRegionSubtype.All: darksouls1ptde.BlenderMSBRegion,
    },
}


BLENDER_MSB_EVENT_TYPES = {
    DARK_SOULS_PTDE: {
        MSBEventSubtype.Light: darksouls1ptde.BlenderMSBLightEvent,
        MSBEventSubtype.Sound: darksouls1ptde.BlenderMSBSoundEvent,
        MSBEventSubtype.VFX: darksouls1ptde.BlenderMSBVFXEvent,
        MSBEventSubtype.Wind: darksouls1ptde.BlenderMSBWindEvent,
        MSBEventSubtype.Treasure: darksouls1ptde.BlenderMSBTreasureEvent,
        MSBEventSubtype.Spawner: darksouls1ptde.BlenderMSBSpawnerEvent,
        MSBEventSubtype.Message: darksouls1ptde.BlenderMSBMessageEvent,
        MSBEventSubtype.ObjAct: darksouls1ptde.BlenderMSBObjActEvent,
        MSBEventSubtype.SpawnPoint: darksouls1ptde.BlenderMSBSpawnPointEvent,
        MSBEventSubtype.MapOffset: darksouls1ptde.BlenderMSBMapOffsetEvent,
        MSBEventSubtype.Navigation: darksouls1ptde.BlenderMSBNavigationEvent,
        MSBEventSubtype.Environment: darksouls1ptde.BlenderMSBEnvironmentEvent,
        MSBEventSubtype.NPCInvasion: darksouls1ptde.BlenderMSBNPCInvasionEvent,
    },
    DARK_SOULS_DSR: {
        MSBEventSubtype.Light: darksouls1r.BlenderMSBLightEvent,
        MSBEventSubtype.Sound: darksouls1r.BlenderMSBSoundEvent,
        MSBEventSubtype.VFX: darksouls1r.BlenderMSBVFXEvent,
        MSBEventSubtype.Wind: darksouls1r.BlenderMSBWindEvent,
        MSBEventSubtype.Treasure: darksouls1r.BlenderMSBTreasureEvent,
        MSBEventSubtype.Spawner: darksouls1r.BlenderMSBSpawnerEvent,
        MSBEventSubtype.Message: darksouls1r.BlenderMSBMessageEvent,
        MSBEventSubtype.ObjAct: darksouls1r.BlenderMSBObjActEvent,
        MSBEventSubtype.SpawnPoint: darksouls1r.BlenderMSBSpawnPointEvent,
        MSBEventSubtype.MapOffset: darksouls1r.BlenderMSBMapOffsetEvent,
        MSBEventSubtype.Navigation: darksouls1r.BlenderMSBNavigationEvent,
        MSBEventSubtype.Environment: darksouls1r.BlenderMSBEnvironmentEvent,
        MSBEventSubtype.NPCInvasion: darksouls1r.BlenderMSBNPCInvasionEvent,
    },
}
