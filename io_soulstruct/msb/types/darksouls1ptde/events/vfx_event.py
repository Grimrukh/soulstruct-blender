from __future__ import annotations

__all__ = [
    "BlenderMSBVFXEvent",
]

from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.msb import MSBVFXEvent

from io_soulstruct.msb.properties import MSBEventSubtype, MSBEventProps, MSBVFXEventProps
from io_soulstruct.msb.types.adapters import *

from .base import BaseBlenderMSBEventDS1


@create_msb_entry_field_adapter_properties
class BlenderMSBVFXEvent(BaseBlenderMSBEventDS1[MSBVFXEvent, MSBEventProps, MSBVFXEventProps, MSB]):

    SOULSTRUCT_CLASS = MSBVFXEvent
    MSB_ENTRY_SUBTYPE = MSBEventSubtype.VFX
    PARENT_PROP_NAME = "attached_region"  # attached part is used as a 'draw parent'
    __slots__ = []

    SUBTYPE_FIELDS = (
        SoulstructFieldAdapter("vfx_id"),
    )

    vfx_id: int
