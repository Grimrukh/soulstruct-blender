from __future__ import annotations

__all__ = [
    "BlenderMSBNPCInvasionEvent",
]

from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.msb import MSBNPCInvasionEvent

from io_soulstruct.msb.properties import MSBEventSubtype, MSBEventProps, MSBNPCInvasionEventProps
from io_soulstruct.msb.types.adapters import *

from .base import BaseBlenderMSBEventDS1


@create_msb_entry_field_adapter_properties
class BlenderMSBNPCInvasionEvent(
    BaseBlenderMSBEventDS1[MSBNPCInvasionEvent, MSBEventProps, MSBNPCInvasionEventProps, MSB]
):

    SOULSTRUCT_CLASS = MSBNPCInvasionEvent
    MSB_ENTRY_SUBTYPE = MSBEventSubtype.NPCInvasion
    PARENT_PROP_NAME = "attached_region"  # invasion trigger region (with Black Eye Orb)
    __slots__ = []

    SUBTYPE_FIELDS = (
        SoulstructFieldAdapter("host_entity_id"),
        SoulstructFieldAdapter("invasion_flag_id"),
        SoulstructFieldAdapter("activate_good_id"),
    )

    host_entity_id: int
    invasion_flag_id: int
    activate_good_id: int
