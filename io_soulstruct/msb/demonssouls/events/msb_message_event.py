from __future__ import annotations

__all__ = [
    "BlenderMSBMessageEvent",
]

import typing as tp

import bpy
from io_soulstruct.msb.properties import MSBEventSubtype, MSBMessageEventProps
from io_soulstruct.utilities import LoggingOperator
from soulstruct.demonssouls.maps import MSB
from soulstruct.demonssouls.maps.msb import MSBMessageEvent
from .msb_event import BlenderMSBEvent


class BlenderMSBMessageEvent(BlenderMSBEvent[MSBMessageEvent, MSBMessageEventProps]):

    SOULSTRUCT_CLASS = MSBMessageEvent
    EVENT_SUBTYPE = MSBEventSubtype.Message
    PARENT_PROP_NAME = "attached_region"
    __slots__ = []

    @property
    def unk_x00(self) -> int:
        return self.subtype_properties.unk_x00

    @unk_x00.setter
    def unk_x00(self, value: int):
        self.subtype_properties.unk_x00 = value

    @property
    def text_id(self) -> int:
        return self.subtype_properties.text_id

    @text_id.setter
    def text_id(self, value: int):
        self.subtype_properties.text_id = value

    @property
    def text_param(self) -> bool:
        return self.subtype_properties.text_param

    @text_param.setter
    def text_param(self, value: bool):
        self.subtype_properties.text_param = value

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
        bl_event.unk_x00 = soulstruct_obj.unk_x00
        bl_event.text_id = soulstruct_obj.text_id
        bl_event.text_param = soulstruct_obj.text_param
        return bl_event

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> MSBMessageEvent:
        message_event = super().to_soulstruct_obj(operator, context, map_stem, msb)
        message_event.unk_x00 = self.unk_x00
        message_event.text_id = self.text_id
        message_event.text_param = self.text_param
        return message_event
