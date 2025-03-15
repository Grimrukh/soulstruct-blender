from __future__ import annotations

__all__ = [
    "BlenderMSBNavmesh",
]

from soulstruct.demonssouls.maps.msb import MSB, MSBNavmesh, BitSet128
from soulstruct.demonssouls.maps.models import MSBNavmeshModel

from io_soulstruct.msb.types.base.parts import BaseBlenderMSBPart
from io_soulstruct.msb.types.adapters import *
from io_soulstruct.msb.properties import MSBPartSubtype, MSBPartProps, MSBNavmeshProps
from io_soulstruct.types import SoulstructType


@create_msb_entry_field_adapter_properties
class BlenderMSBNavmesh(BaseBlenderMSBPart[MSBNavmesh, MSBPartProps, MSBNavmeshProps, MSB, BitSet128]):

    SOULSTRUCT_CLASS = MSBNavmesh
    MSB_ENTRY_SUBTYPE = MSBPartSubtype.Navmesh
    _MODEL_ADAPTER = MSBPartModelAdapter(SoulstructType.NAVMESH, MSBNavmeshModel)

    __slots__ = []

    # No fields.
    SUBTYPE_FIELDS = ()
