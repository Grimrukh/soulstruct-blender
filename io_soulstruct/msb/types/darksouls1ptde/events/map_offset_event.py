from __future__ import annotations

__all__ = [
    "BlenderMSBMapOffsetEvent",
]

import math

from mathutils import Vector

from soulstruct.darksouls1ptde.maps.msb import MSBMapOffsetEvent

from io_soulstruct.msb.properties import BlenderMSBEventSubtype, MSBMapOffsetEventProps
from io_soulstruct.msb.types.adapters import *
from io_soulstruct.utilities import BL_TO_GAME_VECTOR3, GAME_TO_BL_VECTOR

from .base import BaseBlenderMSBEvent_DS1


@soulstruct_adapter
class BlenderMSBMapOffsetEvent(BaseBlenderMSBEvent_DS1[MSBMapOffsetEvent, MSBMapOffsetEventProps]):

    SOULSTRUCT_CLASS = MSBMapOffsetEvent
    MSB_ENTRY_SUBTYPE = BlenderMSBEventSubtype.MapOffset
    PARENT_PROP_NAME = ""
    __slots__ = []

    SUBTYPE_FIELDS = (
        CustomFieldAdapter("translate", read_func=GAME_TO_BL_VECTOR, write_func=BL_TO_GAME_VECTOR3),
        # Y angle is stored in degrees in Blender (as Z) and requires negation (LHS/RHS).
        CustomFieldAdapter(
            "rotate_y",
            bl_prop_name="rotate_z",
            read_func=lambda x: -math.degrees(x),
            write_func=lambda x: -math.radians(x),
        ),
    )

    translate: Vector
    rotate_z: float
