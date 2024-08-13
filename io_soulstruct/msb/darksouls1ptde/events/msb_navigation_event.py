from __future__ import annotations

__all__ = [
    "BlenderMSBNavigationEvent",
]

import typing as tp

import bpy
from io_soulstruct.msb.properties import MSBEventSubtype, MSBNavigationEventProps
from io_soulstruct.utilities import LoggingOperator
from io_soulstruct.types import SoulstructType
from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.msb import MSBNavigationEvent
from .msb_event import BlenderMSBEvent


class BlenderMSBNavigationEvent(BlenderMSBEvent[MSBNavigationEvent, MSBNavigationEventProps]):

    SOULSTRUCT_CLASS = MSBNavigationEvent
    EVENT_SUBTYPE = MSBEventSubtype.Navigation
    PARENT_PROP_NAME = "navigation_region"
    __slots__ = []

    @property
    def navigation_region(self) -> bpy.types.Object | None:
        return self.subtype_properties.navigation_region

    @navigation_region.setter
    def navigation_region(self, value: bpy.types.Object | None):
        self.subtype_properties.navigation_region = value

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBNavigationEvent,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
    ) -> tp.Self:
        bl_event = super().new_from_soulstruct_obj(operator, context, soulstruct_obj, name, collection, map_stem)
        bl_event.navigation_region = cls.entry_ref_to_bl_obj(
            operator,
            soulstruct_obj,
            "navigation_region",
            soulstruct_obj.navigation_region,
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
    ) -> MSBNavigationEvent:
        navigation_event = super().to_soulstruct_obj(operator, context, map_stem, msb)
        navigation_event.navigation_region = self.bl_obj_to_entry_ref(
            msb, "navigation_region", self.navigation_region, navigation_event
        )
        return navigation_event
