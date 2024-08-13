from __future__ import annotations

__all__ = [
    "BlenderMSBTreasureEvent",
]

import typing as tp

import bpy
from io_soulstruct.msb.properties import MSBEventSubtype, MSBTreasureEventProps
from io_soulstruct.utilities import LoggingOperator
from io_soulstruct.types import SoulstructType
from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.msb import MSBTreasureEvent
from .msb_event import BlenderMSBEvent


class BlenderMSBTreasureEvent(BlenderMSBEvent[MSBTreasureEvent, MSBTreasureEventProps]):

    SOULSTRUCT_CLASS = MSBTreasureEvent
    EVENT_SUBTYPE = MSBEventSubtype.Treasure
    PARENT_PROP_NAME = "treasure_part"  # invasion trigger region (with Black Eye Orb)
    __slots__ = []

    AUTO_SUBTYPE_PROPS = [
        "item_lot_1",
        "item_lot_2",
        "item_lot_3",
        "item_lot_4",
        "item_lot_5",
        "is_in_chest",
        "is_hidden",
    ]

    item_lot_1: int
    item_lot_2: int
    item_lot_3: int
    item_lot_4: int
    item_lot_5: int
    is_in_chest: bool
    is_hidden: bool

    @property
    def treasure_part(self) -> bpy.types.Object | None:
        return self.subtype_properties.treasure_part

    @treasure_part.setter
    def treasure_part(self, value: bpy.types.Object | None):
        self.subtype_properties.treasure_part = value

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBTreasureEvent,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
    ) -> tp.Self:
        bl_event = super().new_from_soulstruct_obj(operator, context, soulstruct_obj, name, collection, map_stem)
        bl_event.treasure_part = cls.entry_ref_to_bl_obj(
            operator,
            soulstruct_obj,
            "treasure_part",
            soulstruct_obj.treasure_part,
            SoulstructType.MSB_PART,
            missing_collection_name=f"{map_stem} Missing MSB References".lstrip(),
        )
        for prop_name in cls.AUTO_SUBTYPE_PROPS:
            setattr(bl_event, prop_name, getattr(soulstruct_obj, prop_name))
        return bl_event

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> MSBTreasureEvent:
        treasure_event = super().to_soulstruct_obj(operator, context, map_stem, msb)
        treasure_event.treasure_part = self.bl_obj_to_entry_ref(
            msb, "treasure_part", self.treasure_part, treasure_event
        )
        for prop_name in self.AUTO_SUBTYPE_PROPS:
            setattr(treasure_event, prop_name, getattr(self, prop_name))
        return treasure_event


BlenderMSBTreasureEvent.add_auto_subtype_props(*BlenderMSBTreasureEvent.AUTO_SUBTYPE_PROPS)
