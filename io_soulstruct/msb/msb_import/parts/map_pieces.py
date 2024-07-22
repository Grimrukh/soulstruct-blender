"""Import MSB Map Piece entries."""
from __future__ import annotations

__all__ = [
    "ImportMSBMapPiece",
    "ImportAllMSBMapPieces",
]

from io_soulstruct.msb.properties import MSBPartSubtype
from .core import *


msb_map_piece_operator_config = MSBPartOperatorConfig(
    PART_SUBTYPE=MSBPartSubtype.MAP_PIECE,
    MSB_LIST_NAME="map_pieces",
    GAME_ENUM_NAME="map_piece_part",
)


class ImportMSBMapPiece(BaseImportSingleMSBPart):
    """Import the model of an enum-selected MSB Map Piece part, and its MSB transform."""
    bl_idname = "import_scene.msb_map_piece_part"
    bl_label = "Import Map Piece Part"
    bl_description = "Import FLVER model and MSB transform of selected Map Piece MSB part"

    config = msb_map_piece_operator_config


class ImportAllMSBMapPieces(BaseImportAllMSBParts):
    """Import ALL MSB map piece parts and their transforms. Will probably take a long time!"""
    bl_idname = "import_scene.all_msb_map_piece_parts"
    bl_label = "Import All Map Piece Parts"
    bl_description = ("Import FLVER model and MSB transform of every Map Piece MSB part. Very slow, especially when "
                      "importing textures (see console output for progress)")

    config = msb_map_piece_operator_config
