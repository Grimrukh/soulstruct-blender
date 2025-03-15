from __future__ import annotations

__all__ = [
    "BlenderMSBSpawnerEvent",
]

import bpy

from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.msb import MSBSpawnerEvent

from io_soulstruct.msb.properties import MSBEventSubtype, MSBEventProps, MSBSpawnerEventProps
from io_soulstruct.msb.types.adapters import *
from io_soulstruct.types import SoulstructType

from .base import BaseBlenderMSBEventDS1


@create_msb_entry_field_adapter_properties
class BlenderMSBSpawnerEvent(BaseBlenderMSBEventDS1[MSBSpawnerEvent, MSBEventProps, MSBSpawnerEventProps, MSB]):

    SOULSTRUCT_CLASS = MSBSpawnerEvent
    MSB_ENTRY_SUBTYPE = MSBEventSubtype.Spawner
    PARENT_PROP_NAME = ""
    __slots__ = []

    SUBTYPE_FIELDS = (
        MSBReferenceFieldAdapter("spawn_parts", ref_type=SoulstructType.MSB_PART, array_count=32),
        MSBReferenceFieldAdapter("spawn_regions", ref_type=SoulstructType.MSB_REGION, array_count=4),
        SoulstructFieldAdapter("max_count"),
        SoulstructFieldAdapter("spawner_type"),
        SoulstructFieldAdapter("limit_count"),
        SoulstructFieldAdapter("min_spawner_count"),
        SoulstructFieldAdapter("max_spawner_count"),
        SoulstructFieldAdapter("min_interval"),
        SoulstructFieldAdapter("max_interval"),
        SoulstructFieldAdapter("initial_spawn_count"),
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
