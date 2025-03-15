from __future__ import annotations

__all__ = [
    "BlenderMSBWindEvent",
]

from mathutils import Vector

from soulstruct.demonssouls.maps import MSB
from soulstruct.demonssouls.maps.msb import MSBWindEvent
from soulstruct.utilities.maths import Vector3

from io_soulstruct.msb.properties import MSBEventSubtype, MSBEventProps, MSBWindEventProps
from io_soulstruct.msb.types.base.events import BaseBlenderMSBEvent
from io_soulstruct.msb.types.adapters import *


@create_msb_entry_field_adapter_properties
class BlenderMSBWindEvent(BaseBlenderMSBEvent[MSBWindEvent, MSBEventProps, MSBWindEventProps, MSB]):

    SOULSTRUCT_CLASS = MSBWindEvent
    MSB_ENTRY_SUBTYPE = MSBEventSubtype.Wind
    PARENT_PROP_NAME = "attached_region"
    __slots__ = []

    SUBTYPE_FIELDS = (
        CustomSoulstructFieldAdapter("wind_vector_min", read_func=Vector, write_func=Vector3),
        SoulstructFieldAdapter("unk_x0c"),
        CustomSoulstructFieldAdapter("wind_vector_max", read_func=Vector, write_func=Vector3),
        SoulstructFieldAdapter("unk_x1c"),
        CustomSoulstructFieldAdapter("wind_swing_cycles", read_func=Vector, write_func=lambda x: list(x)),
        CustomSoulstructFieldAdapter("wind_swing_powers", read_func=Vector, write_func=lambda x: list(x)),
    )

    wind_vector_min: Vector
    unk_x0c: float
    wind_vector_max: Vector
    unk_x1c: float
    wind_swing_cycles: Vector
    wind_swing_powers: Vector
