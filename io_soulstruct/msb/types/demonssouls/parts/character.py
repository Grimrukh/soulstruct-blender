from __future__ import annotations

__all__ = [
    "BlenderMSBCharacter",
]

import bpy

from soulstruct.demonssouls.maps.msb import MSB, BitSet128
from soulstruct.demonssouls.maps.models import MSBCharacterModel
from soulstruct.demonssouls.maps.parts import MSBCharacter, MSBDummyCharacter

from io_soulstruct.msb.types.adapters import *
from io_soulstruct.msb.properties.parts import MSBPartSubtype, MSBPartProps, MSBCharacterProps
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import LoggingOperator

from .base import BaseBlenderMSBPart_DES


@create_msb_entry_field_adapter_properties
class BlenderMSBCharacter(BaseBlenderMSBPart_DES[MSBCharacter, MSBPartProps, MSBCharacterProps, MSB, BitSet128]):
    """Concrete wrapper for MSB Characters in Demon's Souls."""

    SOULSTRUCT_CLASS = MSBCharacter
    SOULSTRUCT_DUMMY_CLASS = MSBDummyCharacter
    MSB_ENTRY_SUBTYPE = MSBPartSubtype.Character
    MSB_MODEL_CLASS = MSBCharacterModel
    MODEL_SUBTYPES = ["character_models"]

    _MODEL_ADAPTER = MSBPartModelAdapter(SoulstructType.FLVER, MSBCharacterModel)

    __slots__ = []

    SUBTYPE_FIELDS = (
        MSBReferenceFieldAdapter("draw_parent", ref_type=SoulstructType.MSB_PART),
        MSBReferenceFieldAdapter("patrol_regions", ref_type=SoulstructType.MSB_REGION, array_count=8),
        SoulstructFieldAdapter("unk_x00"),
        SoulstructFieldAdapter("unk_x04"),
        SoulstructFieldAdapter("unk_x08"),
        SoulstructFieldAdapter("character_id"),
        SoulstructFieldAdapter("talk_id"),
        SoulstructFieldAdapter("platoon_id"),
        SoulstructFieldAdapter("patrol_type"),
        SoulstructFieldAdapter("player_id"),
        SoulstructFieldAdapter("default_animation"),
        SoulstructFieldAdapter("damage_animation"),
    )

    draw_parent: bpy.types.Object | None
    patrol_regions: list[bpy.types.Object | None]
    unk_x00: int
    unk_x04: int
    unk_x08: float
    character_id: int
    talk_id: int
    platoon_id: int
    patrol_type: int
    player_id: int
    default_animation: int
    damage_animation: int

    def _post_new_from_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBCharacter,
    ):
        self.subtype_properties.is_dummy = "Dummy" in soulstruct_obj.__class__.__name__

    def _create_soulstruct_obj(self):
        if self.subtype_properties.is_dummy:
            # noinspection PyArgumentList
            return self.SOULSTRUCT_DUMMY_CLASS(name=self.game_name)
        # noinspection PyArgumentList
        return self.SOULSTRUCT_CLASS(name=self.game_name)
