from __future__ import annotations

__all__ = [
    "BlenderMSBWindEvent",
]

from mathutils import Vector

from soulstruct.demonssouls.maps.msb import MSBWindEvent
from soulstruct.utilities.maths import Vector3

from io_soulstruct.msb.properties import BlenderMSBEventSubtype, MSBWindEventProps
from io_soulstruct.msb.types.adapters import *

from .base import BaseBlenderMSBEvent_DES


@soulstruct_adapter
class BlenderMSBWindEvent(BaseBlenderMSBEvent_DES[MSBWindEvent, MSBWindEventProps]):

    SOULSTRUCT_CLASS = MSBWindEvent
    MSB_ENTRY_SUBTYPE = BlenderMSBEventSubtype.Wind
    PARENT_PROP_NAME = "attached_region"
    __slots__ = []

    SUBTYPE_FIELDS = (
        CustomFieldAdapter("wind_vector_min", read_func=Vector, write_func=Vector3),
        FieldAdapter("unk_x0c"),
        CustomFieldAdapter("wind_vector_max", read_func=Vector, write_func=Vector3),
        FieldAdapter("unk_x1c"),
        CustomFieldAdapter("wind_swing_cycles", read_func=Vector, write_func=lambda x: list(x)),
        CustomFieldAdapter("wind_swing_powers", read_func=Vector, write_func=lambda x: list(x)),
    )

    wind_vector_min: Vector
    unk_x0c: float
    wind_vector_max: Vector
    unk_x1c: float
    wind_swing_cycles: Vector
    wind_swing_powers: Vector
