"""Import MSB Object entries."""
from __future__ import annotations

__all__ = [
    "ImportMSBObject",
    "ImportAllMSBObjects",
    "ExportMSBObjects",
]

import bpy
from io_soulstruct.general import SoulstructSettings
from io_soulstruct.msb.operator_config import MSBPartOperatorConfig
from io_soulstruct.msb.properties import MSBPartSubtype
from io_soulstruct.utilities import LoggingOperator
from .base import *


msb_object_operator_config = MSBPartOperatorConfig(
    PART_SUBTYPE=MSBPartSubtype.OBJECT,
    MSB_LIST_NAME="objects",
    MSB_MODEL_LIST_NAMES=["object_models"],
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


class ExportMSBObjects(BaseExportMSBParts):

    bl_idname = "export_scene.msb_object_part"
    bl_label = "Export Object Parts"
    bl_description = "Export selected MSB Object parts to MSB"

    config = msb_object_operator_config

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
