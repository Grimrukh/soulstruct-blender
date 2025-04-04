from __future__ import annotations

__all__ = [
    "BlenderMSBNavigationEvent",
]

import bpy

from soulstruct.darksouls1ptde.maps.msb import MSBNavigationEvent

from io_soulstruct.msb.properties import BlenderMSBEventSubtype, MSBNavigationEventProps
from io_soulstruct.msb.types.adapters import *
from io_soulstruct.types import SoulstructType

from .base import BaseBlenderMSBEvent_DS1


@soulstruct_adapter
class BlenderMSBNavigationEvent(BaseBlenderMSBEvent_DS1[MSBNavigationEvent, MSBNavigationEventProps]):

    SOULSTRUCT_CLASS = MSBNavigationEvent
    MSB_ENTRY_SUBTYPE = BlenderMSBEventSubtype.Navigation
    PARENT_PROP_NAME = "navigation_region"
    __slots__ = []

    SUBTYPE_FIELDS = (
        MSBReferenceFieldAdapter("navigation_region", ref_type=SoulstructType.MSB_REGION),
    )

    navigation_region: bpy.types.MeshObject | None
