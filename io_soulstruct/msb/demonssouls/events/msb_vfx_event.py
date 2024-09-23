from __future__ import annotations

__all__ = [
    "BlenderMSBVFXEvent",
]

import typing as tp

import bpy
from io_soulstruct.msb.properties import MSBEventSubtype, MSBVFXEventProps
from io_soulstruct.utilities import LoggingOperator
from soulstruct.demonssouls.maps import MSB
from soulstruct.demonssouls.maps.msb import MSBVFXEvent
from .msb_event import BlenderMSBEvent


class BlenderMSBVFXEvent(BlenderMSBEvent[MSBVFXEvent, MSBVFXEventProps]):

    SOULSTRUCT_CLASS = MSBVFXEvent
    EVENT_SUBTYPE = MSBEventSubtype.VFX
    PARENT_PROP_NAME = "attached_region"  # attached part is used as a 'draw parent'
    __slots__ = []

    @property
    def vfx_id(self) -> int:
        return self.subtype_properties.vfx_id

    @vfx_id.setter
    def vfx_id(self, value: int):
        self.subtype_properties.vfx_id = value

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBVFXEvent,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
    ) -> tp.Self:
        bl_event = super().new_from_soulstruct_obj(operator, context, soulstruct_obj, name, collection, map_stem)
        bl_event.vfx_id = soulstruct_obj.vfx_id
        return bl_event

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> MSBVFXEvent:
        vfx_event = super().to_soulstruct_obj(operator, context, map_stem, msb)
        vfx_event.vfx_id = self.vfx_id
        return vfx_event
