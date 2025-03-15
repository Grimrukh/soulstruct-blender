from __future__ import annotations

__all__ = [
    "BlenderMSBMapPiece",
]

from soulstruct.darksouls1ptde.maps.msb import MSB, MSBMapPiece, BitSet128
from soulstruct.darksouls1ptde.maps.models import MSBMapPieceModel

from io_soulstruct.msb.types.base.parts import BaseBlenderMSBPart
from io_soulstruct.msb.types.adapters import *
from io_soulstruct.msb.properties import MSBPartSubtype, MSBPartProps, MSBMapPieceProps
from io_soulstruct.types import SoulstructType


@create_msb_entry_field_adapter_properties
class BlenderMSBMapPiece(BaseBlenderMSBPart[MSBMapPiece, MSBPartProps, MSBMapPieceProps, MSB, BitSet128]):

    SOULSTRUCT_CLASS = MSBMapPiece
    MSB_ENTRY_SUBTYPE = MSBPartSubtype.MapPiece
    _MODEL_ADAPTER = MSBPartModelAdapter(SoulstructType.FLVER, MSBMapPieceModel)

    __slots__ = []

    # No fields.
    SUBTYPE_FIELDS = ()
