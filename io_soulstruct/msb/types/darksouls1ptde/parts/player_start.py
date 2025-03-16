from __future__ import annotations

__all__ = [
    "BlenderMSBPlayerStart",
]

from soulstruct.darksouls1ptde.maps.msb import MSB, MSBPlayerStart, BitSet128
from soulstruct.darksouls1ptde.maps.models import MSBCharacterModel

from io_soulstruct.msb.types.adapters import *
from io_soulstruct.msb.properties import MSBPartSubtype, MSBPartProps, MSBPlayerStartProps
from io_soulstruct.types import SoulstructType

from .base import BaseBlenderMSBPart_DS1


@create_msb_entry_field_adapter_properties
class BlenderMSBPlayerStart(BaseBlenderMSBPart_DS1[MSBPlayerStart, MSBPartProps, MSBPlayerStartProps, MSB, BitSet128]):

    SOULSTRUCT_CLASS = MSBPlayerStart
    MSB_ENTRY_SUBTYPE = MSBPartSubtype.PlayerStart
    # NOTE: We only use the `MSBModel` subclass here to get the file name, which is the same for `MSBPlayerModel`.
    _MODEL_ADAPTER = MSBPartModelAdapter(SoulstructType.FLVER, MSBCharacterModel)

    __slots__ = []

    # No fields.
    SUBTYPE_FIELDS = ()
