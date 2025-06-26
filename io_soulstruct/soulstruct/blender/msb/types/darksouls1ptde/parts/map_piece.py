from __future__ import annotations

__all__ = [
    "BlenderMSBMapPiece",
]

from soulstruct.darksouls1ptde.maps.models import MSBMapPieceModel
from soulstruct.darksouls1ptde.maps.parts import MSBMapPiece

from soulstruct.blender.msb.types.adapters import *
from soulstruct.blender.msb.properties import BlenderMSBPartSubtype, MSBMapPieceProps
from soulstruct.blender.types import SoulstructType

from .base import BaseBlenderMSBPart_DS1


@soulstruct_adapter
class BlenderMSBMapPiece(BaseBlenderMSBPart_DS1[MSBMapPiece, MSBMapPieceProps]):

    SOULSTRUCT_CLASS = MSBMapPiece
    MSB_ENTRY_SUBTYPE = BlenderMSBPartSubtype.MapPiece
    _MODEL_ADAPTER = MSBPartModelAdapter(SoulstructType.FLVER, MSBMapPieceModel)

    __slots__ = []

    # No fields.
    SUBTYPE_FIELDS = ()
