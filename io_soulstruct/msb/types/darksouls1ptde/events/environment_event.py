from __future__ import annotations

__all__ = [
    "BlenderMSBEnvironmentEvent",
]

from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.msb import MSBEnvironmentEvent

from io_soulstruct.msb.properties import MSBEventSubtype, MSBEventProps, MSBEnvironmentEventProps
from io_soulstruct.msb.types.adapters import *

from .base import BaseBlenderMSBEventDS1


@create_msb_entry_field_adapter_properties
class BlenderMSBEnvironmentEvent(
    BaseBlenderMSBEventDS1[MSBEnvironmentEvent, MSBEventProps, MSBEnvironmentEventProps, MSB]
):

    SOULSTRUCT_CLASS = MSBEnvironmentEvent
    MSB_ENTRY_SUBTYPE = MSBEventSubtype.Environment
    PARENT_PROP_NAME = "attached_region"  # parenting to Collision would be useful but less important

    __slots__ = []

    # NOTE: This is the only class with a circular MSB Entry type reference (to/from `MSBCollision` Parts).
    # However, the same instances do NOT always point at each other (though they often do).

    SUBTYPE_FIELDS = (
        SoulstructFieldAdapter("unk_x00_x04"),
        SoulstructFieldAdapter("unk_x04_x08"),
        SoulstructFieldAdapter("unk_x08_x0c"),
        SoulstructFieldAdapter("unk_x0c_x10"),
        SoulstructFieldAdapter("unk_x10_x14"),
        SoulstructFieldAdapter("unk_x14_x18"),
    )

    unk_x00_x04: int
    unk_x04_x08: float
    unk_x08_x0c: float
    unk_x0c_x10: float
    unk_x10_x14: float
    unk_x14_x18: float
