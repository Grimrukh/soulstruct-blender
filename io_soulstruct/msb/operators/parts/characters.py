"""Import MSB Character entries."""
from __future__ import annotations

__all__ = [
    "ImportMSBCharacter",
    "ImportAllMSBCharacters",
    "ExportMSBCharacters",
]

import typing as tp

import bpy
from io_soulstruct.flver.models import BlenderFLVER
from io_soulstruct.general import SoulstructSettings
from io_soulstruct.msb.operator_config import MSBPartOperatorConfig
from io_soulstruct.msb.properties import MSBPartSubtype
from io_soulstruct.utilities import LoggingOperator
from .base import *

if tp.TYPE_CHECKING:
    from soulstruct.containers import Binder


msb_character_operator_config = MSBPartOperatorConfig(
    PART_SUBTYPE=MSBPartSubtype.CHARACTER,
    MSB_LIST_NAME="characters",
    MSB_MODEL_LIST_NAMES=["character_models"],
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


class ExportMSBCharacters(BaseExportMSBParts):

    bl_idname = "export_scene.msb_character_part"
    bl_label = "Export Character Parts"
    bl_description = "Export selected MSB Character parts to selected map MSB"

    config = msb_character_operator_config

    def init(self, context: bpy.types.Context, settings: SoulstructSettings):
        pass

    def export_model(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_mesh: bpy.types.MeshObject,
        map_stem="",
    ):
        pass

    def finish_model_export(self, context: bpy.types.Context, settings: SoulstructSettings):
        pass
