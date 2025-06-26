from __future__ import annotations

__all__ = [
    "BlenderMSBPlayerStart",
]

from soulstruct.demonssouls.maps.models import MSBCharacterModel
from soulstruct.demonssouls.maps.parts import MSBPlayerStart

from soulstruct.blender.msb.types.adapters import *
from soulstruct.blender.msb.properties import BlenderMSBPartSubtype, MSBPlayerStartProps
from soulstruct.blender.types import SoulstructType

from .base import BaseBlenderMSBPart_DES


@soulstruct_adapter
class BlenderMSBPlayerStart(BaseBlenderMSBPart_DES[MSBPlayerStart, MSBPlayerStartProps]):

    SOULSTRUCT_CLASS = MSBPlayerStart
    MSB_ENTRY_SUBTYPE = BlenderMSBPartSubtype.PlayerStart
    # NOTE: We only use the `MSBModel` subclass here to get the file name, which is the same for `MSBPlayerModel`.
    _MODEL_ADAPTER = MSBPartModelAdapter(SoulstructType.FLVER, MSBCharacterModel)

    __slots__ = []

    SUBTYPE_FIELDS = (
        FieldAdapter("unk_x00_x04"),
    )

    unk_x00_x04: int
