from __future__ import annotations

__all__ = [
    "BlenderMSBNPCInvasionEvent",
]

from soulstruct.darksouls1ptde.maps.msb import MSBNPCInvasionEvent

from soulstruct.blender.msb.properties import BlenderMSBEventSubtype, MSBNPCInvasionEventProps
from soulstruct.blender.msb.types.adapters import *

from .base import BaseBlenderMSBEvent_DS1


@soulstruct_adapter
class BlenderMSBNPCInvasionEvent(BaseBlenderMSBEvent_DS1[MSBNPCInvasionEvent, MSBNPCInvasionEventProps]):

    SOULSTRUCT_CLASS = MSBNPCInvasionEvent
    MSB_ENTRY_SUBTYPE = BlenderMSBEventSubtype.NPCInvasion
    PARENT_PROP_NAME = "attached_region"  # invasion trigger region (with Black Eye Orb)
    __slots__ = []

    SUBTYPE_FIELDS = (
        FieldAdapter("host_entity_id"),
        FieldAdapter("invasion_flag_id"),
        FieldAdapter("activate_good_id"),
    )

    host_entity_id: int
    invasion_flag_id: int
    activate_good_id: int
