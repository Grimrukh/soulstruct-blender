from __future__ import annotations

__all__ = [
    "BaseBlenderMSBEvent_DES",
]

import abc

from bpy.types import PropertyGroup

from soulstruct.demonssouls.maps.msb import MSB
from soulstruct.demonssouls.maps.events import MSBEvent

from ...base.events import BaseBlenderMSBEvent


class BaseBlenderMSBEvent_DES[
    EVENT_T: MSBEvent,
    SUBTYPE_PROPS_T: PropertyGroup,
](BaseBlenderMSBEvent[EVENT_T, SUBTYPE_PROPS_T, MSB], abc.ABC):
    """Narrows `EVENT_T` and fixes `MSB_T` to Demon's Souls."""
