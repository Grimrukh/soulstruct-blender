from __future__ import annotations

__all__ = [
    "BlenderMSBMessageEvent",
]

from soulstruct.demonssouls.maps import MSB
from soulstruct.demonssouls.maps.msb import MSBMessageEvent

from io_soulstruct.msb.properties import MSBEventSubtype, MSBEventProps, MSBMessageEventProps
from io_soulstruct.msb.types.base.events import BaseBlenderMSBEvent
from io_soulstruct.msb.types.adapters import *


@create_msb_entry_field_adapter_properties
class BlenderMSBMessageEvent(BaseBlenderMSBEvent[MSBMessageEvent, MSBEventProps, MSBMessageEventProps, MSB]):

    SOULSTRUCT_CLASS = MSBMessageEvent
    MSB_ENTRY_SUBTYPE = MSBEventSubtype.Message
    PARENT_PROP_NAME = "attached_region"
    __slots__ = []

    SUBTYPE_FIELDS = (
        SoulstructFieldAdapter("unk_x00"),
        SoulstructFieldAdapter("text_id"),
        SoulstructFieldAdapter("text_param"),
    )

    unk_x00: int
    text_id: int
    text_param: int
