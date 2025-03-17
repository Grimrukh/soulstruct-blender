from __future__ import annotations

__all__ = [
    "BlenderMSBSpawnerEvent",
]

import bpy

from soulstruct.darksouls1ptde.maps.msb import MSBSpawnerEvent

from io_soulstruct.msb.properties import BlenderMSBEventSubtype, MSBSpawnerEventProps
from io_soulstruct.msb.types.adapters import *
from io_soulstruct.types import SoulstructType

from .base import BaseBlenderMSBEvent_DS1


@soulstruct_adapter
class BlenderMSBSpawnerEvent(BaseBlenderMSBEvent_DS1[MSBSpawnerEvent, MSBSpawnerEventProps]):

    SOULSTRUCT_CLASS = MSBSpawnerEvent
    MSB_ENTRY_SUBTYPE = BlenderMSBEventSubtype.Spawner
    PARENT_PROP_NAME = ""
    __slots__ = []

    SUBTYPE_FIELDS = (
        MSBReferenceFieldAdapter("spawn_parts", ref_type=SoulstructType.MSB_PART, array_count=32),
        MSBReferenceFieldAdapter("spawn_regions", ref_type=SoulstructType.MSB_REGION, array_count=4),
        FieldAdapter("max_count"),
        FieldAdapter("spawner_type"),
        FieldAdapter("limit_count"),
        FieldAdapter("min_spawner_count"),
        FieldAdapter("max_spawner_count"),
        FieldAdapter("min_interval"),
        FieldAdapter("max_interval"),
        FieldAdapter("initial_spawn_count"),
    )

    spawn_parts: list[bpy.types.MeshObject | None]
    spawn_regions: list[bpy.types.MeshObject | None]
    max_count: int
    spawner_type: int
    limit_count: int
    min_spawner_count: int
    max_spawner_count: int
    min_interval: float
    max_interval: float
    initial_spawn_count: int
