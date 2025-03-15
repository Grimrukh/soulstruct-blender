from __future__ import annotations

__all__ = [
    "BaseBlenderMSBEventDS1",
]

import abc

from soulstruct.darksouls1ptde.maps.msb import MSB

from io_soulstruct.msb.types.base.events import BaseBlenderMSBEvent, EVENT_T, SUBTYPE_PROPS_T
from io_soulstruct.msb.types.adapters import SoulstructFieldAdapter
from io_soulstruct.msb.properties.events import MSBEventProps


class BaseBlenderMSBEventDS1(BaseBlenderMSBEvent[EVENT_T, MSBEventProps, SUBTYPE_PROPS_T, MSB], abc.ABC):
    """All DS1 MSB Events have an extra field of unknowns."""

    TYPE_FIELDS = BaseBlenderMSBEvent.TYPE_FIELDS + (
        SoulstructFieldAdapter("unknowns"),
    )
