from __future__ import annotations

__all__ = [
    "BlenderMSBMapOffsetEvent",
]

import math

from mathutils import Vector

from soulstruct.darksouls1ptde.maps.msb import MSBMapOffsetEvent

from soulstruct.blender.msb.properties import BlenderMSBEventSubtype, MSBMapOffsetEventProps
from soulstruct.blender.msb.types.adapters import *
from soulstruct.blender.utilities import to_game, to_blender

from .base import BaseBlenderMSBEvent_DS1


@soulstruct_adapter
class BlenderMSBMapOffsetEvent(BaseBlenderMSBEvent_DS1[MSBMapOffsetEvent, MSBMapOffsetEventProps]):

    SOULSTRUCT_CLASS = MSBMapOffsetEvent
    MSB_ENTRY_SUBTYPE = BlenderMSBEventSubtype.MapOffset
    PARENT_PROP_NAME = ""
    __slots__ = []

    SUBTYPE_FIELDS = (
        CustomFieldAdapter("translate", read_func=to_blender, write_func=to_game),
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
