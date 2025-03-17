from __future__ import annotations

__all__ = [
    "BlenderMSBNavmesh",
]

from soulstruct.demonssouls.maps.models import MSBNavmeshModel
from soulstruct.demonssouls.maps.parts import MSBNavmesh

from io_soulstruct.msb.types.adapters import *
from io_soulstruct.msb.properties import BlenderMSBPartSubtype, MSBNavmeshProps
from io_soulstruct.types import SoulstructType

from .base import BaseBlenderMSBPart_DES


@soulstruct_adapter
class BlenderMSBNavmesh(BaseBlenderMSBPart_DES[MSBNavmesh, MSBNavmeshProps]):

    SOULSTRUCT_CLASS = MSBNavmesh
    MSB_ENTRY_SUBTYPE = BlenderMSBPartSubtype.Navmesh
    _MODEL_ADAPTER = MSBPartModelAdapter(SoulstructType.NAVMESH, MSBNavmeshModel)

    __slots__ = []

    # No fields.
    SUBTYPE_FIELDS = ()
