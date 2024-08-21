from __future__ import annotations

__all__ = [
    "BlenderMSBNPCInvasionEvent",
]

import typing as tp

import bpy
from io_soulstruct.msb.properties import MSBEventSubtype, MSBNPCInvasionEventProps
from io_soulstruct.utilities import LoggingOperator
from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.msb import MSBNPCInvasionEvent
from .msb_event import BlenderMSBEvent


class BlenderMSBNPCInvasionEvent(BlenderMSBEvent[MSBNPCInvasionEvent, MSBNPCInvasionEventProps]):

    SOULSTRUCT_CLASS = MSBNPCInvasionEvent
    EVENT_SUBTYPE = MSBEventSubtype.NPCInvasion
    PARENT_PROP_NAME = "attached_region"  # invasion trigger region (with Black Eye Orb)
    __slots__ = []

    @property
    def host_entity_id(self) -> int:
        return self.subtype_properties.host_entity_id

    @host_entity_id.setter
    def host_entity_id(self, value: int):
        self.subtype_properties.host_entity_id = value

    @property
    def invasion_flag_id(self) -> int:
        return self.subtype_properties.invasion_flag_id

    @invasion_flag_id.setter
    def invasion_flag_id(self, value: int):
        self.subtype_properties.invasion_flag_id = value

    @property
    def activate_good_id(self) -> int:
        return self.subtype_properties.activate_good_id

    @activate_good_id.setter
    def activate_good_id(self, value: int):
        self.subtype_properties.activate_good_id = value

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBNPCInvasionEvent,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
    ) -> tp.Self:
        bl_event = super().new_from_soulstruct_obj(operator, context, soulstruct_obj, name, collection, map_stem)
        bl_event.host_entity_id = soulstruct_obj.host_entity_id
        bl_event.invasion_flag_id = soulstruct_obj.invasion_flag_id
        bl_event.activate_good_id = soulstruct_obj.activate_good_id
        return bl_event

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> MSBNPCInvasionEvent:
        npc_invasion_event = super().to_soulstruct_obj(operator, context, map_stem, msb)
        npc_invasion_event.host_entity_id = self.host_entity_id
        npc_invasion_event.invasion_flag_id = self.invasion_flag_id
        npc_invasion_event.activate_good_id = self.activate_good_id
        return npc_invasion_event
