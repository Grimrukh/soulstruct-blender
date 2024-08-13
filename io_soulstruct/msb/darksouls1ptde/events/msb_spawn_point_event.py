from __future__ import annotations

__all__ = [
    "BlenderMSBSpawnPointEvent",
]

import typing as tp

import bpy
from io_soulstruct.msb.properties import MSBEventSubtype, MSBSpawnPointEventProps
from io_soulstruct.utilities import LoggingOperator
from io_soulstruct.types import SoulstructType
from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.msb import MSBSpawnPointEvent
from .msb_event import BlenderMSBEvent


class BlenderMSBSpawnPointEvent(BlenderMSBEvent[MSBSpawnPointEvent, MSBSpawnPointEventProps]):

    SOULSTRUCT_CLASS = MSBSpawnPointEvent
    EVENT_SUBTYPE = MSBEventSubtype.SpawnPoint
    PARENT_PROP_NAME = "spawn_point_region"
    __slots__ = []

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
        soulstruct_obj: MSBSpawnPointEvent,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
    ) -> tp.Self:
        bl_event = super().new_from_soulstruct_obj(operator, context, soulstruct_obj, name, collection, map_stem)
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
    ) -> MSBSpawnPointEvent:
        spawn_point_event = super().to_soulstruct_obj(operator, context, map_stem, msb)
        spawn_point_event.spawn_point_region = self.bl_obj_to_entry_ref(
            msb, "spawn_point_region", self.spawn_point_region, spawn_point_event
        )
        return spawn_point_event
