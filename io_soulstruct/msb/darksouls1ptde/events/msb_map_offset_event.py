from __future__ import annotations

__all__ = [
    "BlenderMSBMapOffsetEvent",
]

import math
import typing as tp

import bpy
from mathutils import Vector
from io_soulstruct.msb.properties import MSBEventSubtype, MSBMapOffsetEventProps
from io_soulstruct.utilities import LoggingOperator, BL_TO_GAME_VECTOR3, GAME_TO_BL_VECTOR
from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.msb import MSBMapOffsetEvent
from .msb_event import BlenderMSBEvent


class BlenderMSBMapOffsetEvent(BlenderMSBEvent[MSBMapOffsetEvent, MSBMapOffsetEventProps]):

    SOULSTRUCT_CLASS = MSBMapOffsetEvent
    EVENT_SUBTYPE = MSBEventSubtype.MapOffset
    PARENT_PROP_NAME = ""
    __slots__ = []

    @property
    def translate(self) -> Vector:
        """Property is a `FloatVectorArray`."""
        return Vector(self.subtype_properties.translate)

    @translate.setter
    def translate(self, value: Vector):
        self.subtype_properties.translate = value

    @property
    def rotate_z(self) -> float:
        return self.subtype_properties.rotate_z

    @rotate_z.setter
    def rotate_z(self, value):
        self.subtype_properties.rotate_z = value

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBMapOffsetEvent,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
    ) -> tp.Self:
        bl_event = super().new_from_soulstruct_obj(operator, context, soulstruct_obj, name, collection, map_stem)
        bl_event.translate = GAME_TO_BL_VECTOR(soulstruct_obj.translate)
        bl_event.rotate_z = -(180.0 / math.pi) * soulstruct_obj.rotate_y
        return bl_event

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> MSBMapOffsetEvent:
        map_offset_event = super().to_soulstruct_obj(operator, context, map_stem, msb)
        map_offset_event.translate = BL_TO_GAME_VECTOR3(self.translate)
        map_offset_event.rotate_y = -(math.pi / 180.0) * self.rotate_z
        return map_offset_event
