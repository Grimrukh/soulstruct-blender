from __future__ import annotations

__all__ = [
    "BlenderMSBNavmesh",
]

from soulstruct.darksouls1ptde.maps.msb import MSB, MSBNavmesh, BitSet128
from soulstruct.darksouls1ptde.maps.models import MSBNavmeshModel

from io_soulstruct.msb.types.adapters import *
from io_soulstruct.msb.properties import MSBPartSubtype, MSBPartProps, MSBNavmeshProps
from io_soulstruct.types import SoulstructType

from .base import BaseBlenderMSBPart_DS1


@create_msb_entry_field_adapter_properties
class BlenderMSBNavmesh(BaseBlenderMSBPart_DS1[MSBNavmesh, MSBPartProps, MSBNavmeshProps, MSB, BitSet128]):

    SOULSTRUCT_CLASS = MSBNavmesh
    MSB_ENTRY_SUBTYPE = MSBPartSubtype.Navmesh
    _MODEL_ADAPTER = MSBPartModelAdapter(SoulstructType.NAVMESH, MSBNavmeshModel)

    __slots__ = []

    SUBTYPE_FIELDS = (
        MSBPartGroupsAdapter("navmesh_groups", bit_set_type=BitSet128),
    )
