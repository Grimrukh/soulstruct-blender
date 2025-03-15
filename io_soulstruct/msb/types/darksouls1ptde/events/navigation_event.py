from __future__ import annotations

__all__ = [
    "BlenderMSBNavigationEvent",
]

import bpy

from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.msb import MSBNavigationEvent

from io_soulstruct.msb.properties import MSBEventSubtype, MSBEventProps, MSBNavigationEventProps
from io_soulstruct.msb.types.adapters import *
from io_soulstruct.types import SoulstructType

from .base import BaseBlenderMSBEventDS1


@create_msb_entry_field_adapter_properties
class BlenderMSBNavigationEvent(
    BaseBlenderMSBEventDS1[MSBNavigationEvent, MSBEventProps, MSBNavigationEventProps, MSB]
):

    SOULSTRUCT_CLASS = MSBNavigationEvent
    MSB_ENTRY_SUBTYPE = MSBEventSubtype.Navigation
    PARENT_PROP_NAME = "navigation_region"
    __slots__ = []

    SUBTYPE_FIELDS = (
        MSBReferenceFieldAdapter("navigation_region", ref_type=SoulstructType.MSB_REGION),
    )

    navigation_region: bpy.types.MeshObject | None
