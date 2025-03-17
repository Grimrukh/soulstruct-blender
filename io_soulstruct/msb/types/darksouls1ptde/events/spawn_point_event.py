from __future__ import annotations

__all__ = [
    "BlenderMSBSpawnPointEvent",
]

import bpy

from soulstruct.darksouls1ptde.maps.msb import MSBSpawnPointEvent

from io_soulstruct.msb.properties import BlenderMSBEventSubtype, MSBSpawnPointEventProps
from io_soulstruct.msb.types.adapters import *
from io_soulstruct.types import SoulstructType

from .base import BaseBlenderMSBEvent_DS1


@soulstruct_adapter
class BlenderMSBSpawnPointEvent(BaseBlenderMSBEvent_DS1[MSBSpawnPointEvent, MSBSpawnPointEventProps]):

    SOULSTRUCT_CLASS = MSBSpawnPointEvent
    MSB_ENTRY_SUBTYPE = BlenderMSBEventSubtype.SpawnPoint
    PARENT_PROP_NAME = "spawn_point_region"
    __slots__ = []

    SUBTYPE_FIELDS = (
        MSBReferenceFieldAdapter("spawn_point_region", ref_type=SoulstructType.MSB_REGION),
    )

    spawn_point_region: bpy.types.MeshObject | None
