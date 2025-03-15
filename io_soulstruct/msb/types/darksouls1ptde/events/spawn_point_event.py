from __future__ import annotations

__all__ = [
    "BlenderMSBSpawnPointEvent",
]

import bpy

from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.msb import MSBSpawnPointEvent

from io_soulstruct.msb.properties import MSBEventSubtype, MSBEventProps, MSBSpawnPointEventProps
from io_soulstruct.msb.types.adapters import *
from io_soulstruct.types import SoulstructType

from .base import BaseBlenderMSBEventDS1


@create_msb_entry_field_adapter_properties
class BlenderMSBSpawnPointEvent(
    BaseBlenderMSBEventDS1[MSBSpawnPointEvent, MSBEventProps, MSBSpawnPointEventProps, MSB]
):

    SOULSTRUCT_CLASS = MSBSpawnPointEvent
    MSB_ENTRY_SUBTYPE = MSBEventSubtype.SpawnPoint
    PARENT_PROP_NAME = "spawn_point_region"
    __slots__ = []

    SUBTYPE_FIELDS = (
        MSBReferenceFieldAdapter("spawn_point_region", ref_type=SoulstructType.MSB_REGION),
    )

    spawn_point_region: bpy.types.MeshObject | None
