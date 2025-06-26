from __future__ import annotations

__all__ = [
    "BlenderMSBProtoboss",
]

from soulstruct.demonssouls.maps.models import MSBCharacterModel
from soulstruct.demonssouls.maps.parts import MSBProtoboss

from soulstruct.blender.msb.types.adapters import *
from soulstruct.blender.msb.properties import BlenderMSBPartSubtype, MSBProtobossProps
from soulstruct.blender.types import *

from .base import BaseBlenderMSBPart_DES


@soulstruct_adapter
class BlenderMSBProtoboss(BaseBlenderMSBPart_DES[MSBProtoboss, MSBProtobossProps]):
    """Ancient Demon's Souls MSB character variant. I don't think it's used in any of the non-cut maps."""

    SOULSTRUCT_CLASS = MSBProtoboss
    MSB_ENTRY_SUBTYPE = BlenderMSBPartSubtype.Character
    _MODEL_ADAPTER = MSBPartModelAdapter(SoulstructType.FLVER, MSBCharacterModel)

    __slots__ = []

    SUBTYPE_FIELDS = (
        FieldAdapter("unk_x00"),
        FieldAdapter("unk_x04"),
        FieldAdapter("unk_x08"),
        FieldAdapter("unk_x0c"),
        FieldAdapter("unk_x10"),
        FieldAdapter("unk_x14"),
        FieldAdapter("unk_x18"),
        FieldAdapter("unk_x1c"),
        FieldAdapter("unk_x20"),
        FieldAdapter("unk_x24"),
        FieldAdapter("unk_x28"),
        FieldAdapter("unk_x2c"),
        FieldAdapter("unk_x30"),
    )

    unk_x00: float
    unk_x04: float
    unk_x08: float
    unk_x0c: float
    unk_x10: int
    unk_x14: int
    unk_x18: float
    unk_x1c: float
    unk_x20: int
    unk_x24: int
    unk_x28: float
    unk_x2c: int
    unk_x30: int
