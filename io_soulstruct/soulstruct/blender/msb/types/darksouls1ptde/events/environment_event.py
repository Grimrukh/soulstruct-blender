from __future__ import annotations

__all__ = [
    "BlenderMSBEnvironmentEvent",
]

from soulstruct.darksouls1ptde.maps.msb import MSBEnvironmentEvent

from soulstruct.blender.msb.properties import BlenderMSBEventSubtype, MSBEnvironmentEventProps
from soulstruct.blender.msb.types.adapters import *

from .base import BaseBlenderMSBEvent_DS1


@soulstruct_adapter
class BlenderMSBEnvironmentEvent(BaseBlenderMSBEvent_DS1[MSBEnvironmentEvent, MSBEnvironmentEventProps]):

    SOULSTRUCT_CLASS = MSBEnvironmentEvent
    MSB_ENTRY_SUBTYPE = BlenderMSBEventSubtype.Environment
    PARENT_PROP_NAME = "attached_region"  # parenting to Collision would be useful but less important

    __slots__ = []

    # NOTE: This is the only class with a circular MSB Entry type reference (to/from `MSBCollision` Parts).
    # However, the same instances do NOT always point at each other (though they often do).

    SUBTYPE_FIELDS = (
        FieldAdapter("unk_x00_x04"),
        FieldAdapter("unk_x04_x08"),
        FieldAdapter("unk_x08_x0c"),
        FieldAdapter("unk_x0c_x10"),
        FieldAdapter("unk_x10_x14"),
        FieldAdapter("unk_x14_x18"),
    )

    unk_x00_x04: int
    unk_x04_x08: float
    unk_x08_x0c: float
    unk_x0c_x10: float
    unk_x10_x14: float
    unk_x14_x18: float
