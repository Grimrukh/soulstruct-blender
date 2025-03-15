from __future__ import annotations

__all__ = [
    "BlenderMSBMapOffsetEvent",
]

import math

from mathutils import Vector

from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.msb import MSBMapOffsetEvent

from io_soulstruct.msb.properties import MSBEventSubtype, MSBEventProps, MSBMapOffsetEventProps
from io_soulstruct.msb.types.adapters import *
from io_soulstruct.utilities import BL_TO_GAME_VECTOR3, GAME_TO_BL_VECTOR

from .base import BaseBlenderMSBEventDS1


@create_msb_entry_field_adapter_properties
class BlenderMSBMapOffsetEvent(BaseBlenderMSBEventDS1[MSBMapOffsetEvent, MSBEventProps, MSBMapOffsetEventProps, MSB]):

    SOULSTRUCT_CLASS = MSBMapOffsetEvent
    MSB_ENTRY_SUBTYPE = MSBEventSubtype.MapOffset
    PARENT_PROP_NAME = ""
    __slots__ = []

    SUBTYPE_FIELDS = (
        CustomSoulstructFieldAdapter("translate", read_func=GAME_TO_BL_VECTOR, write_func=BL_TO_GAME_VECTOR3),
        # Z angle is stored in degrees in Blender and requires negation (LHS/RHS).
        CustomSoulstructFieldAdapter(
            "rotate_z", read_func=lambda x: -math.degrees(x), write_func=lambda x: -math.radians(x)
        ),
    )

    translate: Vector
    rotate_z: float
