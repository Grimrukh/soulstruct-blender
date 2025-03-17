from __future__ import annotations

__all__ = [
    "BlenderMSBVFXEvent",
]

from soulstruct.darksouls1ptde.maps.msb import MSBVFXEvent

from io_soulstruct.msb.properties import BlenderMSBEventSubtype, MSBVFXEventProps
from io_soulstruct.msb.types.adapters import *

from .base import BaseBlenderMSBEvent_DS1


@soulstruct_adapter
class BlenderMSBVFXEvent(BaseBlenderMSBEvent_DS1[MSBVFXEvent, MSBVFXEventProps]):

    SOULSTRUCT_CLASS = MSBVFXEvent
    MSB_ENTRY_SUBTYPE = BlenderMSBEventSubtype.VFX
    PARENT_PROP_NAME = "attached_region"  # attached part is used as a 'draw parent'
    __slots__ = []

    SUBTYPE_FIELDS = (
        FieldAdapter("vfx_id"),
    )

    vfx_id: int
