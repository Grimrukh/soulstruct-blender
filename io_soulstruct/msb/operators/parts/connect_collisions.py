"""Operators for importing `MSBConnectCollision` entries from MSB files."""
from __future__ import annotations

__all__ = [
    "ImportMSBConnectCollision",
    "ImportAllMSBConnectCollisions",
    "ExportMSBConnectCollisions",
]

import bpy
from io_soulstruct.general import SoulstructSettings
from io_soulstruct.msb.operator_config import MSBPartOperatorConfig
from io_soulstruct.msb.properties import MSBPartSubtype
from io_soulstruct.utilities import LoggingOperator
from .base import *


msb_connect_collision_operator_config = MSBPartOperatorConfig(
    PART_SUBTYPE=MSBPartSubtype.CONNECT_COLLISION,
    MSB_LIST_NAME="connect_collisions",
    MSB_MODEL_LIST_NAMES=["collision_models"],
)


class ImportMSBConnectCollision(BaseImportSingleMSBPart):
    bl_idname = "import_scene.msb_connect_collision"
    bl_label = "Import MSB Connect Collision Part"
    bl_description = "Import selected MSB Connect Collision entry from selected game MSB"

    config = msb_connect_collision_operator_config


class ImportAllMSBConnectCollisions(BaseImportAllMSBParts):
    bl_idname = "import_scene.all_msb_connect_collisions"
    bl_label = "Import All Connect Collision Parts"
    bl_description = "Import HKX meshes and MSB transform of every MSB Connect Collision part. Moderately slow"

    config = msb_connect_collision_operator_config


class ExportMSBConnectCollisions(BaseExportMSBParts):
    """Export one or more HKX collision files into a FromSoftware DSR map directory BHD."""

    bl_idname = "export_scene_map.msb_connect_collisions"
    bl_label = "Export Map Connect Collisions"
    bl_description = "Export MSB Connect Collision parts to MSB. Never exports models"

    config = msb_connect_collision_operator_config

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
