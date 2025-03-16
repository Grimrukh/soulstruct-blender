from __future__ import annotations

__all__ = [
    "BlenderMSBMapPiece",
]

from soulstruct.demonssouls.maps.msb import MSB, MSBMapPiece, BitSet128
from soulstruct.demonssouls.maps.models import MSBMapPieceModel

from io_soulstruct.msb.types.adapters import *
from io_soulstruct.msb.properties import MSBPartSubtype, MSBPartProps, MSBMapPieceProps
from io_soulstruct.types import SoulstructType

from .base import BaseBlenderMSBPart_DES


@create_msb_entry_field_adapter_properties
class BlenderMSBMapPiece(BaseBlenderMSBPart_DES[MSBMapPiece, MSBPartProps, MSBMapPieceProps, MSB, BitSet128]):

    SOULSTRUCT_CLASS = MSBMapPiece
    MSB_ENTRY_SUBTYPE = MSBPartSubtype.MapPiece
    _MODEL_ADAPTER = MSBPartModelAdapter(SoulstructType.FLVER, MSBMapPieceModel)

    __slots__ = []

    # No fields.
    SUBTYPE_FIELDS = ()
