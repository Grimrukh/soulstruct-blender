from __future__ import annotations

__all__ = [
    "BlenderMSBPlayerStart",
]

from soulstruct.darksouls1ptde.maps.msb import MSBPlayerStart
from soulstruct.darksouls1ptde.maps.models import MSBCharacterModel

from soulstruct.blender.msb.types.adapters import *
from soulstruct.blender.msb.properties import BlenderMSBPartSubtype, MSBPlayerStartProps
from soulstruct.blender.types import SoulstructType

from .base import BaseBlenderMSBPart_DS1


@soulstruct_adapter
class BlenderMSBPlayerStart(BaseBlenderMSBPart_DS1[MSBPlayerStart, MSBPlayerStartProps]):

    SOULSTRUCT_CLASS = MSBPlayerStart
    MSB_ENTRY_SUBTYPE = BlenderMSBPartSubtype.PlayerStart
    # NOTE: We only use the `MSBModel` subclass here to get the file name, which is the same for `MSBPlayerModel`.
    _MODEL_ADAPTER = MSBPartModelAdapter(SoulstructType.FLVER, MSBCharacterModel)

    __slots__ = []

    # No fields.
    SUBTYPE_FIELDS = ()
