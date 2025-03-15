from __future__ import annotations

__all__ = [
    "BlenderMSBVFXEvent",
]

from soulstruct.demonssouls.maps import MSB
from soulstruct.demonssouls.maps.msb import MSBVFXEvent

from io_soulstruct.msb.properties import MSBEventSubtype, MSBEventProps, MSBVFXEventProps
from io_soulstruct.msb.types.base.events import BaseBlenderMSBEvent
from io_soulstruct.msb.types.adapters import *


@create_msb_entry_field_adapter_properties
class BlenderMSBVFXEvent(BaseBlenderMSBEvent[MSBVFXEvent, MSBEventProps, MSBVFXEventProps, MSB]):

    SOULSTRUCT_CLASS = MSBVFXEvent
    MSB_ENTRY_SUBTYPE = MSBEventSubtype.VFX
    PARENT_PROP_NAME = "attached_region"  # attached part is used as a 'draw parent'
    __slots__ = []

    SUBTYPE_FIELDS = (
        SoulstructFieldAdapter("vfx_id"),
    )

    vfx_id: int
