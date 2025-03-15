from __future__ import annotations

__all__ = [
    "BlenderMSBMessageEvent",
]

from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.msb import MSBMessageEvent

from io_soulstruct.msb.properties import MSBEventSubtype, MSBEventProps, MSBMessageEventProps
from io_soulstruct.msb.types.adapters import *

from .base import BaseBlenderMSBEventDS1


@create_msb_entry_field_adapter_properties
class BlenderMSBMessageEvent(BaseBlenderMSBEventDS1[MSBMessageEvent, MSBEventProps, MSBMessageEventProps, MSB]):

    SOULSTRUCT_CLASS = MSBMessageEvent
    MSB_ENTRY_SUBTYPE = MSBEventSubtype.Message
    PARENT_PROP_NAME = "attached_region"
    __slots__ = []

    SUBTYPE_FIELDS = (
        SoulstructFieldAdapter("text_id"),
        SoulstructFieldAdapter("unk_x02"),
        SoulstructFieldAdapter("is_hidden"),
    )

    text_id: int
    unk_x02: int
    is_hidden: bool
