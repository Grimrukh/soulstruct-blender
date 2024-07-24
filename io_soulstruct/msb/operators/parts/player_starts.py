"""Operators for importing `MSBPlayerStart` entries, and their HKX models, from MSB files."""
from __future__ import annotations

__all__ = [
    "ImportMSBPlayerStart",
    "ImportAllMSBPlayerStarts",
    "ExportMSBPlayerStarts",
]

import bpy
from io_soulstruct.general import SoulstructSettings
from io_soulstruct.msb.operator_config import MSBPartOperatorConfig
from io_soulstruct.msb.properties import MSBPartSubtype
from io_soulstruct.utilities import LoggingOperator
from .base import *

msb_player_start_operator_config = MSBPartOperatorConfig(
    PART_SUBTYPE=MSBPartSubtype.PLAYER_START,
    MSB_LIST_NAME="player_starts",
    MSB_MODEL_LIST_NAMES=["player_models", "character_models"],
    GAME_ENUM_NAME="player_start_part",
)


class ImportMSBPlayerStart(BaseImportSingleMSBPart):
    bl_idname = "import_scene.msb_player_start"
    bl_label = "Import MSB Player Start Part"
    bl_description = "Import selected MSB Player Start entry from selected game MSB"

    config = msb_player_start_operator_config


class ImportAllMSBPlayerStarts(BaseImportAllMSBParts):
    bl_idname = "import_scene.all_msb_player_starts"
    bl_label = "Import All Player Start Parts"
    bl_description = "Import HKX meshes and MSB transform of every MSB Player Start part. Moderately slow"

    config = msb_player_start_operator_config


class ExportMSBPlayerStarts(BaseExportMSBParts):
    """Export one or more HKX collision files into a FromSoftware DSR map directory BHD."""

    bl_idname = "export_scene_map.msb_player_starts"
    bl_label = "Export Map Player Starts"
    bl_description = "Export MSB Player Start parts to MSB. Never exports models"

    config = msb_player_start_operator_config

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
