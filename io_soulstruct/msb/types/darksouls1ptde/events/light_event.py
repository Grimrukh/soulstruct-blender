from __future__ import annotations

__all__ = [
    "BlenderMSBLightEvent",
]

from soulstruct.darksouls1ptde.maps.msb import MSBLightEvent

from io_soulstruct.msb.properties import BlenderMSBEventSubtype, MSBLightEventProps
from io_soulstruct.msb.types.adapters import *

from .base import BaseBlenderMSBEvent_DS1


@soulstruct_adapter
class BlenderMSBLightEvent(BaseBlenderMSBEvent_DS1[MSBLightEvent, MSBLightEventProps]):

    SOULSTRUCT_CLASS = MSBLightEvent
    MSB_ENTRY_SUBTYPE = BlenderMSBEventSubtype.Light
    PARENT_PROP_NAME = "attached_region"
    __slots__ = []

    SUBTYPE_FIELDS = (
        FieldAdapter("point_light_id"),
    )

    point_light_id: int
