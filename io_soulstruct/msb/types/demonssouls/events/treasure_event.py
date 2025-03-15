from __future__ import annotations

__all__ = [
    "BlenderMSBTreasureEvent",
]

import bpy

from soulstruct.demonssouls.maps import MSB
from soulstruct.demonssouls.maps.msb import MSBTreasureEvent

from io_soulstruct.msb.properties import MSBEventSubtype, MSBEventProps, MSBTreasureEventProps
from io_soulstruct.msb.types.base.events import BaseBlenderMSBEvent
from io_soulstruct.msb.types.adapters import *
from io_soulstruct.types import SoulstructType


@create_msb_entry_field_adapter_properties
class BlenderMSBTreasureEvent(BaseBlenderMSBEvent[MSBTreasureEvent, MSBEventProps, MSBTreasureEventProps, MSB]):

    SOULSTRUCT_CLASS = MSBTreasureEvent
    MSB_ENTRY_SUBTYPE = MSBEventSubtype.Treasure
    PARENT_PROP_NAME = "treasure_part"  # invasion trigger region (with Black Eye Orb)
    __slots__ = []

    SUBTYPE_FIELDS = (
        MSBReferenceFieldAdapter("treasure_part", ref_type=SoulstructType.MSB_PART),
        SoulstructFieldAdapter("item_lot_1"),
        SoulstructFieldAdapter("item_lot_2"),
        SoulstructFieldAdapter("item_lot_3"),
        SoulstructFieldAdapter("item_lot_4"),
        SoulstructFieldAdapter("item_lot_5"),
    )

    treasure_part: bpy.types.MeshObject | None
    item_lot_1: int
    item_lot_2: int
    item_lot_3: int
    item_lot_4: int
    item_lot_5: int
