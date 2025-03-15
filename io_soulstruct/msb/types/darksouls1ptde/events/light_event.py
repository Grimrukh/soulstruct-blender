from __future__ import annotations

__all__ = [
    "BlenderMSBLightEvent",
]

from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.msb import MSBLightEvent

from io_soulstruct.msb.properties import MSBEventSubtype, MSBEventProps, MSBLightEventProps
from io_soulstruct.msb.types.adapters import *

from .base import BaseBlenderMSBEventDS1


@create_msb_entry_field_adapter_properties
class BlenderMSBLightEvent(BaseBlenderMSBEventDS1[MSBLightEvent, MSBEventProps, MSBLightEventProps, MSB]):

    SOULSTRUCT_CLASS = MSBLightEvent
    MSB_ENTRY_SUBTYPE = MSBEventSubtype.Light
    PARENT_PROP_NAME = "attached_region"
    __slots__ = []

    SUBTYPE_FIELDS = (
        SoulstructFieldAdapter("point_light_id"),
    )

    point_light_id: int
