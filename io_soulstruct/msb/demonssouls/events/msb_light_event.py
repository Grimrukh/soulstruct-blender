from __future__ import annotations

__all__ = [
    "BlenderMSBLightEvent",
]

import typing as tp

import bpy
from io_soulstruct.msb.properties import MSBEventSubtype, MSBLightEventProps
from io_soulstruct.utilities import LoggingOperator
from soulstruct.demonssouls.maps import MSB
from soulstruct.demonssouls.maps.msb import MSBLightEvent
from .msb_event import BlenderMSBEvent


class BlenderMSBLightEvent(BlenderMSBEvent[MSBLightEvent, MSBLightEventProps]):

    SOULSTRUCT_CLASS = MSBLightEvent
    EVENT_SUBTYPE = MSBEventSubtype.Light
    PARENT_PROP_NAME = "attached_region"
    __slots__ = []

    @property
    def point_light_id(self) -> int:
        return self.subtype_properties.point_light_id

    @point_light_id.setter
    def point_light_id(self, value: int):
        self.subtype_properties.point_light_id = value

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBLightEvent,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
    ) -> tp.Self:
        bl_event = super().new_from_soulstruct_obj(operator, context, soulstruct_obj, name, collection, map_stem)
        bl_event.point_light_id = soulstruct_obj.point_light_id
        return bl_event

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> MSBLightEvent:
        light_event = super().to_soulstruct_obj(operator, context, map_stem, msb)
        light_event.point_light_id = self.point_light_id
        return light_event
