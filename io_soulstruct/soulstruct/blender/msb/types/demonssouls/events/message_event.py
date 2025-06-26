from __future__ import annotations

__all__ = [
    "BlenderMSBMessageEvent",
]

from soulstruct.demonssouls.maps.msb import MSBMessageEvent

from soulstruct.blender.msb.properties import BlenderMSBEventSubtype, MSBMessageEventProps
from soulstruct.blender.msb.types.adapters import *

from .base import BaseBlenderMSBEvent_DES


@soulstruct_adapter
class BlenderMSBMessageEvent(BaseBlenderMSBEvent_DES[MSBMessageEvent, MSBMessageEventProps]):

    SOULSTRUCT_CLASS = MSBMessageEvent
    MSB_ENTRY_SUBTYPE = BlenderMSBEventSubtype.Message
    PARENT_PROP_NAME = "attached_region"
    __slots__ = []

    SUBTYPE_FIELDS = (
        FieldAdapter("unk_x00"),
        FieldAdapter("text_id"),
        FieldAdapter("text_param"),
    )

    unk_x00: int
    text_id: int
    text_param: int
