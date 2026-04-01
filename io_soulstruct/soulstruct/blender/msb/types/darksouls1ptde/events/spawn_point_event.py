from __future__ import annotations

__all__ = [
    "BlenderMSBSpawnPointEvent",
]

from soulstruct.darksouls1ptde.maps.events import MSBSpawnPointEvent

from ....properties import BlenderMSBEventSubtype, MSBSpawnPointEventProps
from ...adapters import *
from .....types import MeshObject, SoulstructType

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

    spawn_point_region: MeshObject | None
