from __future__ import annotations

__all__ = [
    "BlenderMSBMessageEvent",
]

import typing as tp

import bpy
from io_soulstruct.msb.properties import MSBEventSubtype, MSBMessageEventProps
from io_soulstruct.utilities import LoggingOperator
from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.msb import MSBMessageEvent
from .msb_event import BlenderMSBEvent


class BlenderMSBMessageEvent(BlenderMSBEvent[MSBMessageEvent, MSBMessageEventProps]):

    SOULSTRUCT_CLASS = MSBMessageEvent
    EVENT_SUBTYPE = MSBEventSubtype.Message
    PARENT_PROP_NAME = "attached_region"
    __slots__ = []

    @property
    def text_id(self) -> int:
        return self.subtype_properties.text_id

    @text_id.setter
    def text_id(self, value: int):
        self.subtype_properties.text_id = value

    @property
    def unk_x02(self) -> int:
        return self.subtype_properties.unk_x02

    @unk_x02.setter
    def unk_x02(self, value: int):
        self.subtype_properties.unk_x02 = value

    @property
    def is_hidden(self) -> bool:
        return self.subtype_properties.is_hidden

    @is_hidden.setter
    def is_hidden(self, value: bool):
        self.subtype_properties.is_hidden = value

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBMessageEvent,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
    ) -> tp.Self:
        bl_event = super().new_from_soulstruct_obj(operator, context, soulstruct_obj, name, collection, map_stem)
        bl_event.text_id = soulstruct_obj.text_id
        bl_event.unk_x02 = soulstruct_obj.unk_x02
        bl_event.is_hidden = soulstruct_obj.is_hidden
        return bl_event

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> MSBMessageEvent:
        message_event = super().to_soulstruct_obj(operator, context, map_stem, msb)
        message_event.text_id = self.text_id
        message_event.unk_x02 = self.unk_x02
        message_event.is_hidden = self.is_hidden
        return message_event
