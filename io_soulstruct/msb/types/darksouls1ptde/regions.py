from __future__ import annotations

__all__ = [
    "BlenderMSBRegion",
]

from soulstruct.darksouls1ptde.maps.msb import MSB
from soulstruct.darksouls1ptde.maps.regions import *

from io_soulstruct.msb.types.adapters import *
from io_soulstruct.msb.types.base.regions import BaseBlenderMSBRegion
from io_soulstruct.msb.properties import MSBRegionProps, MSBRegionSubtype
from io_soulstruct.types import *


@create_msb_entry_field_adapter_properties
class BlenderMSBRegion(BaseBlenderMSBRegion[MSBRegion, MSBRegionProps, None, MSB]):
    """No subclasses in DS1 (just shape types)."""

    TYPE = SoulstructType.MSB_REGION
    BL_OBJ_TYPE = ObjectType.MESH
    SOULSTRUCT_CLASS = MSBRegion
    MSB_ENTRY_SUBTYPE = MSBRegionSubtype.All  # no subtypes for DS1

    __slots__ = []

    # No subtype fields.
    SUBTYPE_FIELDS = ()
