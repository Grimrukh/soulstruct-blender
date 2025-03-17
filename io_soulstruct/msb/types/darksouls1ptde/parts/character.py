from __future__ import annotations

__all__ = [
    "BlenderMSBCharacter",
]

import bpy

from soulstruct.darksouls1ptde.maps.models import MSBCharacterModel
from soulstruct.darksouls1ptde.maps.parts import MSBCharacter, MSBDummyCharacter

from io_soulstruct.msb.types.adapters import *
from io_soulstruct.msb.properties.parts import BlenderMSBPartSubtype, MSBCharacterProps
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import LoggingOperator

from .base import BaseBlenderMSBPart_DS1


@soulstruct_adapter
class BlenderMSBCharacter(BaseBlenderMSBPart_DS1[MSBCharacter, MSBCharacterProps]):
    """Concrete wrapper for MSB Characters in Dark Souls 1."""

    SOULSTRUCT_CLASS = MSBCharacter
    SOULSTRUCT_DUMMY_CLASS = MSBDummyCharacter
    MSB_ENTRY_SUBTYPE = BlenderMSBPartSubtype.Character
    MODEL_SUBTYPES = ["character_models"]

    _MODEL_ADAPTER = MSBPartModelAdapter(SoulstructType.FLVER, MSBCharacterModel)

    __slots__ = []

    SUBTYPE_FIELDS = (
        MSBReferenceFieldAdapter("draw_parent", ref_type=SoulstructType.MSB_PART),
        MSBReferenceFieldAdapter("patrol_regions", ref_type=SoulstructType.MSB_REGION, array_count=8),
        FieldAdapter("ai_id"),
        FieldAdapter("character_id"),
        FieldAdapter("talk_id"),
        FieldAdapter("platoon_id"),
        FieldAdapter("patrol_type"),
        FieldAdapter("player_id"),
        FieldAdapter("default_animation"),
        FieldAdapter("damage_animation"),
    )

    # Properties common to all supported games' MSB Characters.
    draw_parent: bpy.types.Object | None
    patrol_regions: list[bpy.types.Object | None]
    ai_id: int
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
