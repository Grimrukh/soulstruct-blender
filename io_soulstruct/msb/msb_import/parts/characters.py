"""Import MSB Character entries."""
from __future__ import annotations

__all__ = [
    "ImportMSBCharacter",
    "ImportAllMSBCharacters",
]

from io_soulstruct.msb.properties import MSBPartSubtype
from .core import *


msb_character_operator_config = MSBPartOperatorConfig(
    PART_SUBTYPE=MSBPartSubtype.CHARACTER,
    MSB_LIST_NAME="characters",
    GAME_ENUM_NAME="character_part",
)


class ImportMSBCharacter(BaseImportSingleMSBPart):
    """Import the model of an enum-selected MSB Character part, and its MSB transform."""
    bl_idname = "import_scene.msb_character_part"
    bl_label = "Import Character Part"
    bl_description = "Import FLVER model and MSB transform of selected MSB Character part"

    config = msb_character_operator_config


class ImportAllMSBCharacters(BaseImportAllMSBParts):
    """Import ALL MSB Character parts and their transforms. Will probably take a long time!"""
    bl_idname = "import_scene.all_msb_character_parts"
    bl_label = "Import All Character Parts"
    bl_description = ("Import FLVER model and MSB transform of every MSB Character part. Very slow, especially when "
                      "textures are imported (see console output for progress)")

    config = msb_character_operator_config
