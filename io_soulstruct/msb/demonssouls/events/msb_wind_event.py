from __future__ import annotations

__all__ = [
    "BlenderMSBWindEvent",
]

import typing as tp

import bpy
from mathutils import Vector
from io_soulstruct.msb.properties import MSBEventSubtype, MSBWindEventProps
from io_soulstruct.utilities import LoggingOperator
from soulstruct.demonssouls.maps import MSB
from soulstruct.demonssouls.maps.msb import MSBWindEvent
from .msb_event import BlenderMSBEvent


class BlenderMSBWindEvent(BlenderMSBEvent[MSBWindEvent, MSBWindEventProps]):

    SOULSTRUCT_CLASS = MSBWindEvent
    EVENT_SUBTYPE = MSBEventSubtype.Wind
    PARENT_PROP_NAME = "attached_region"
    __slots__ = []

    @property
    def wind_vector_min(self) -> Vector:
        return self.subtype_properties.wind_vector_min

    @wind_vector_min.setter
    def wind_vector_min(self, value: Vector):
        self.subtype_properties.wind_vector_min = value

    @property
    def unk_x0c(self) -> float:
        return self.subtype_properties.unk_x0c

    @unk_x0c.setter
    def unk_x0c(self, value: float):
        self.subtype_properties.unk_x0c = value

    @property
    def wind_vector_max(self) -> Vector:
        return self.subtype_properties.wind_vector_max

    @wind_vector_max.setter
    def wind_vector_max(self, value: Vector):
        self.subtype_properties.wind_vector_max = value

    @property
    def unk_x1c(self) -> float:
        return self.subtype_properties.unk_x1c

    @unk_x1c.setter
    def unk_x1c(self, value: float):
        self.subtype_properties.unk_x1c = value

    @property
    def wind_swing_cycles(self) -> Vector:
        return self.subtype_properties.wind_swing_cycles

    @wind_swing_cycles.setter
    def wind_swing_cycles(self, value: Vector):
        if len(value) != 4:
            raise ValueError("Wind swing cycles must be a 4D vector.")
        self.subtype_properties.wind_swing_cycles = value

    @property
    def wind_swing_powers(self) -> Vector:
        return self.subtype_properties.wind_swing_powers

    @wind_swing_powers.setter
    def wind_swing_powers(self, value: Vector):
        if len(value) != 4:
            raise ValueError("Wind swing powers must be a 4D vector.")
        self.subtype_properties.wind_swing_powers = value

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBWindEvent,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
    ) -> tp.Self:
        bl_event = super().new_from_soulstruct_obj(
            operator, context, soulstruct_obj, name, collection, map_stem
        )  # type: BlenderMSBWindEvent
        bl_event.wind_vector_min = Vector(soulstruct_obj.wind_vector_min)
        bl_event.unk_x0c = soulstruct_obj.unk_x0c
        bl_event.wind_vector_max = Vector(soulstruct_obj.wind_vector_max)
        bl_event.unk_x1c = soulstruct_obj.unk_x1c
        bl_event.wind_swing_cycles = Vector(soulstruct_obj.wind_swing_cycles)
        bl_event.wind_swing_powers = Vector(soulstruct_obj.wind_swing_powers)
        return bl_event

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> MSBWindEvent:
        wind_event = super().to_soulstruct_obj(operator, context, map_stem, msb)
        wind_event.wind_vector_min = list(self.wind_vector_min)
        wind_event.unk_x0c = self.unk_x0c
        wind_event.wind_vector_max = list(self.wind_vector_max)
        wind_event.unk_x1c = self.unk_x1c
        wind_event.wind_swing_cycles = list(self.wind_swing_cycles)
        wind_event.wind_swing_powers = list(self.wind_swing_powers)
        return wind_event
