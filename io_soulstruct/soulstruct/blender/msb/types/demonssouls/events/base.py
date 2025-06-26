from __future__ import annotations

__all__ = [
    "BaseBlenderMSBEvent_DES",
]

import abc

from soulstruct.demonssouls.maps.msb import MSB

from soulstruct.blender.msb.types.base.events import BaseBlenderMSBEvent, EVENT_T, SUBTYPE_PROPS_T


class BaseBlenderMSBEvent_DES(BaseBlenderMSBEvent[EVENT_T, SUBTYPE_PROPS_T, MSB], abc.ABC):
    """Just fixes `MSB_T` generic parameter."""
