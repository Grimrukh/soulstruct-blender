"""Import MSB Object entries."""
from __future__ import annotations

__all__ = [
    "ImportMSBObject",
    "ImportAllMSBObjects",
    "ExportMSBObjects",
]

import typing as tp

import bpy
from io_soulstruct.flver import FLVERExporter
from io_soulstruct.general import SoulstructSettings
from io_soulstruct.msb.core import MSBPartOperatorConfig
from io_soulstruct.msb.properties import MSBPartSubtype
from .base import *

if tp.TYPE_CHECKING:
    from soulstruct.containers import Binder


msb_object_operator_config = MSBPartOperatorConfig(
    PART_SUBTYPE=MSBPartSubtype.OBJECT,
    MSB_LIST_NAME="objects",
    MSB_MODEL_LIST_NAME="object_models",
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


class ExportMSBObjects(BaseExportMSBParts):

    bl_idname = "export_scene.msb_object_part"
    bl_label = "Export Object Parts"
    bl_description = "Export selected MSB Object parts to FLVER models"

    config = msb_object_operator_config

    objbnds: dict[str, Binder]  # keys are stems

    def init(self, context: bpy.types.Context, settings: SoulstructSettings):
        self.objbnds = {}

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
