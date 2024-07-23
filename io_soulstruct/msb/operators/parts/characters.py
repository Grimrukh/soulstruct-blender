"""Import MSB Character entries."""
from __future__ import annotations

__all__ = [
    "ImportMSBCharacter",
    "ImportAllMSBCharacters",
    "ExportMSBCharacters",
]

import typing as tp

import bpy
from io_soulstruct.flver.model_export import FLVERExporter
from io_soulstruct.general import SoulstructSettings
from io_soulstruct.msb.core import MSBPartOperatorConfig
from io_soulstruct.msb.properties import MSBPartSubtype
from .base import *

if tp.TYPE_CHECKING:
    from soulstruct.containers import Binder


msb_character_operator_config = MSBPartOperatorConfig(
    PART_SUBTYPE=MSBPartSubtype.CHARACTER,
    MSB_LIST_NAME="characters",
    MSB_MODEL_LIST_NAME="character_models",
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

    chrbnds: dict[str, Binder]  # keys are stems

    def init(self, context: bpy.types.Context, settings: SoulstructSettings):
        self.chrbnds = {}

    def export_model(
        self,
        bl_model_obj: bpy.types.MeshObject,
        settings: SoulstructSettings,
        map_stem: str,
        flver_exporter: FLVERExporter | None,
        export_textures=False,
    ):
        pass

    def finish_model_export(self, context: bpy.types.Context, settings: SoulstructSettings):
        pass
