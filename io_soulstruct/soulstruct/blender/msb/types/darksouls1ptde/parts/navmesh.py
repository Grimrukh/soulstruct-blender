from __future__ import annotations

__all__ = [
    "BlenderMSBNavmesh",
]

from soulstruct.darksouls1ptde.maps.msb import BitSet128
from soulstruct.darksouls1ptde.maps.models import MSBNavmeshModel
from soulstruct.darksouls1ptde.maps.parts import MSBNavmesh

from soulstruct.blender.msb.types.adapters import *
from soulstruct.blender.msb.properties import BlenderMSBPartSubtype, MSBNavmeshProps
from soulstruct.blender.types import SoulstructType

from .base import BaseBlenderMSBPart_DS1


@soulstruct_adapter
class BlenderMSBNavmesh(BaseBlenderMSBPart_DS1[MSBNavmesh, MSBNavmeshProps]):

    SOULSTRUCT_CLASS = MSBNavmesh
    MSB_ENTRY_SUBTYPE = BlenderMSBPartSubtype.Navmesh
    _MODEL_ADAPTER = MSBPartModelAdapter(SoulstructType.NAVMESH, MSBNavmeshModel)

    __slots__ = []

    SUBTYPE_FIELDS = (
        MSBPartGroupsAdapter("navmesh_groups", bit_set_type=BitSet128),
    )
