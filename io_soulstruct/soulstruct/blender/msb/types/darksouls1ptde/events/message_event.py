from __future__ import annotations

__all__ = [
    "BlenderMSBMessageEvent",
]

from soulstruct.darksouls1ptde.maps.msb import MSBMessageEvent

from soulstruct.blender.msb.properties import BlenderMSBEventSubtype, MSBMessageEventProps
from soulstruct.blender.msb.types.adapters import *

from .base import BaseBlenderMSBEvent_DS1


@soulstruct_adapter
class BlenderMSBMessageEvent(BaseBlenderMSBEvent_DS1[MSBMessageEvent, MSBMessageEventProps]):

    SOULSTRUCT_CLASS = MSBMessageEvent
    MSB_ENTRY_SUBTYPE = BlenderMSBEventSubtype.Message
    PARENT_PROP_NAME = "attached_region"
    __slots__ = []

    SUBTYPE_FIELDS = (
        FieldAdapter("text_id"),
        FieldAdapter("unk_x02"),
        FieldAdapter("is_hidden"),
    )

    text_id: int
    unk_x02: int
    is_hidden: bool
