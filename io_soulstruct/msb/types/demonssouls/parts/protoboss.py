from __future__ import annotations

__all__ = [
    "BlenderMSBProtoboss",
]

from soulstruct.demonssouls.maps.msb import MSB, BitSet128
from soulstruct.demonssouls.maps.models import MSBCharacterModel
from soulstruct.demonssouls.maps.parts import MSBProtoboss

from io_soulstruct.msb.types.adapters import *
from io_soulstruct.msb.properties import MSBPartSubtype, MSBPartProps, MSBProtobossProps
from io_soulstruct.types import *

from .base import BaseBlenderMSBPart_DES


@create_msb_entry_field_adapter_properties
class BlenderMSBProtoboss(BaseBlenderMSBPart_DES[MSBProtoboss, MSBPartProps, MSBProtobossProps, MSB, BitSet128]):
    """Ancient Demon's Souls MSB character variant. I don't think it's used in any of the non-cut maps."""

    SOULSTRUCT_CLASS = MSBProtoboss
    MSB_ENTRY_SUBTYPE = MSBPartSubtype.Character
    _MODEL_ADAPTER = MSBPartModelAdapter(SoulstructType.FLVER, MSBCharacterModel)

    __slots__ = []

    SUBTYPE_FIELDS = (
        SoulstructFieldAdapter("unk_x00"),
        SoulstructFieldAdapter("unk_x04"),
        SoulstructFieldAdapter("unk_x08"),
        SoulstructFieldAdapter("unk_x0c"),
        SoulstructFieldAdapter("unk_x10"),
        SoulstructFieldAdapter("unk_x14"),
        SoulstructFieldAdapter("unk_x18"),
        SoulstructFieldAdapter("unk_x1c"),
        SoulstructFieldAdapter("unk_x20"),
        SoulstructFieldAdapter("unk_x24"),
        SoulstructFieldAdapter("unk_x28"),
        SoulstructFieldAdapter("unk_x2c"),
        SoulstructFieldAdapter("unk_x30"),
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
