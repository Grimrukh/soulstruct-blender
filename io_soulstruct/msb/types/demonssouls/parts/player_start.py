from __future__ import annotations

__all__ = [
    "BlenderMSBPlayerStart",
]

from soulstruct.demonssouls.maps.msb import MSB, MSBPlayerStart, BitSet128
from soulstruct.demonssouls.maps.models import MSBCharacterModel

from io_soulstruct.msb.types.adapters import *
from io_soulstruct.msb.properties import MSBPartSubtype, MSBPartProps, MSBPlayerStartProps
from io_soulstruct.types import SoulstructType

from .base import BaseBlenderMSBPart_DES


@create_msb_entry_field_adapter_properties
class BlenderMSBPlayerStart(BaseBlenderMSBPart_DES[MSBPlayerStart, MSBPartProps, MSBPlayerStartProps, MSB, BitSet128]):

    SOULSTRUCT_CLASS = MSBPlayerStart
    MSB_ENTRY_SUBTYPE = MSBPartSubtype.PlayerStart
    # NOTE: We only use the `MSBModel` subclass here to get the file name, which is the same for `MSBPlayerModel`.
    _MODEL_ADAPTER = MSBPartModelAdapter(SoulstructType.FLVER, MSBCharacterModel)

    __slots__ = []

    SUBTYPE_FIELDS = (
        SoulstructFieldAdapter("unk_x00_x04"),
    )

    unk_x00_x04: int
