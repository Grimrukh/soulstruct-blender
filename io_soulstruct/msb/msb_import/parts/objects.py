"""Import MSB Object entries."""
from __future__ import annotations

__all__ = [
    "ImportMSBObject",
    "ImportAllMSBObjects",
]

from io_soulstruct.msb.properties import MSBPartSubtype
from .core import *


msb_object_operator_config = MSBPartOperatorConfig(
    PART_SUBTYPE=MSBPartSubtype.OBJECT,
    MSB_LIST_NAME="objects",
    GAME_ENUM_NAME="object_part",
)


class ImportMSBObject(BaseImportSingleMSBPart):
    """Import the model of an enum-selected MSB Object part, and its MSB transform."""
    bl_idname = "import_scene.msb_object_part"
    bl_label = "Import Object Part"
    bl_description = "Import FLVER model and MSB transform of selected MSB Object part"

    config = msb_object_operator_config


class ImportAllMSBObjects(BaseImportAllMSBParts):
    """Import ALL MSB Object parts and their transforms. Will probably take a long time!"""
    bl_idname = "import_scene.all_msb_object_parts"
    bl_label = "Import All Object Parts"
    bl_description = ("Import FLVER model and MSB transform of every MSB Object part. Very slow, especially when "
                      "textures are imported (see console output for progress)")

    config = msb_object_operator_config
