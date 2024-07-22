"""Import MSB Asset entries."""
from __future__ import annotations

__all__ = [
    "ImportMSBAsset",
    "ImportAllMSBAssets",
]

from io_soulstruct.msb.properties import MSBPartSubtype
from .core import *


msb_asset_operator_config = MSBPartOperatorConfig(
    PART_SUBTYPE=MSBPartSubtype.ASSET,
    MSB_LIST_NAME="assets",
    GAME_ENUM_NAME="asset_part",
)


class ImportMSBAsset(BaseImportSingleMSBPart):
    """Import ALL MSB Asset parts and their transforms. Will probably take a long time!"""
    bl_idname = "import_scene.msb_asset_part"
    bl_label = "Import Asset Part"
    bl_description = "Import FLVER model and MSB transform of selected MSB Asset part"

    config = msb_asset_operator_config


class ImportAllMSBAssets(BaseImportAllMSBParts):
    """Import ALL MSB Asset parts and their transforms. Will probably take a long time!"""
    bl_idname = "import_scene.all_msb_asset_parts"
    bl_label = "Import All Asset Parts"
    bl_description = ("Import FLVER model and MSB transform of every MSB Asset part. Very slow, especially when "
                      "textures are imported (see console output for progress)")

    config = msb_asset_operator_config
