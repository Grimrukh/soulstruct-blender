from __future__ import annotations

__all__ = [
    "BlenderMSBNPCInvasionEvent",
]

import typing as tp

import bpy
from io_soulstruct.msb.properties import MSBEventSubtype, MSBNPCInvasionEventProps
from io_soulstruct.utilities import LoggingOperator
from io_soulstruct.types import SoulstructType
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
    def spawn_point_region(self) -> bpy.types.Object | None:
        return self.subtype_properties.spawn_point_region

    @spawn_point_region.setter
    def spawn_point_region(self, value: bpy.types.Object | None):
        self.subtype_properties.spawn_point_region = value

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
        bl_event.spawn_point_region = cls.entry_ref_to_bl_obj(
            operator,
            soulstruct_obj,
            "spawn_point_region",
            soulstruct_obj.spawn_point_region,
            SoulstructType.MSB_REGION,
            missing_collection_name=f"{map_stem} Missing MSB References".lstrip(),
        )
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
        npc_invasion_event.spawn_point_region = self.bl_obj_to_entry_ref(
            msb, "spawn_point_region", self.spawn_point_region, npc_invasion_event
        )
        return npc_invasion_event
