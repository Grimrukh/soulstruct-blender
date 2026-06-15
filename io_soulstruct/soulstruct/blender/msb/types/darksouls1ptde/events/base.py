from __future__ import annotations

__all__ = [
    "BaseBlenderMSBEvent_DS1",
]

import abc

from bpy.types import PropertyGroup

from soulstruct.darksouls1ptde.maps.msb import MSB
from soulstruct.darksouls1ptde.maps.events import MSBEvent

from ...adapters import CustomFieldAdapter
from ...base.events import BaseBlenderMSBEvent


class BaseBlenderMSBEvent_DS1[
    EVENT_T: MSBEvent,
    SUBTYPE_PROPS_T: PropertyGroup,
](BaseBlenderMSBEvent[EVENT_T, SUBTYPE_PROPS_T, MSB], abc.ABC):
    """All DS1 MSB Events have an extra field of unknowns."""

    TYPE_FIELDS = BaseBlenderMSBEvent.TYPE_FIELDS + (
        CustomFieldAdapter("unknowns", read_func=lambda x: x, write_func=lambda x: list(x)),  # from `IntVectorProperty`
    )
