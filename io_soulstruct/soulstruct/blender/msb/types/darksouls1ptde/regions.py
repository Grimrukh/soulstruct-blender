from __future__ import annotations

__all__ = [
    "BlenderMSBRegion",
]

from soulstruct.darksouls1ptde.maps.msb import MSB
from soulstruct.darksouls1ptde.maps.regions import *

from soulstruct.blender.msb.types.adapters import *
from soulstruct.blender.msb.types.base.regions import BaseBlenderMSBRegion
from soulstruct.blender.msb.properties import BlenderMSBRegionSubtype
from soulstruct.blender.types import *


@soulstruct_adapter
class BlenderMSBRegion(BaseBlenderMSBRegion[MSBRegion, MSB]):
    """No subclasses in DS1 (just shape types)."""

    TYPE = SoulstructType.MSB_REGION
    BL_OBJ_TYPE = ObjectType.MESH
    SOULSTRUCT_CLASS = MSBRegion
    MSB_ENTRY_SUBTYPE = BlenderMSBRegionSubtype.All  # no subtypes for DS1

    __slots__ = []

    # No subtype fields.
    SUBTYPE_FIELDS = ()
