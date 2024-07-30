"""Import MSB Map Piece entries."""
from __future__ import annotations

__all__ = [
    "ImportMSBMapPiece",
    "ImportAllMSBMapPieces",
    "ExportMSBMapPieces",
]

from pathlib import Path

import bpy
from io_soulstruct import SoulstructSettings
from io_soulstruct.flver.image import DDSTextureCollection, export_map_area_textures
from io_soulstruct.flver.models import BlenderFLVER
from io_soulstruct.msb.operator_config import MSBPartOperatorConfig
from io_soulstruct.msb.properties import MSBPartSubtype
from io_soulstruct.utilities import *
from soulstruct.base.models.flver import FLVER
from .base import *


msb_map_piece_operator_config = MSBPartOperatorConfig(
    PART_SUBTYPE=MSBPartSubtype.MAP_PIECE,
    MSB_LIST_NAME="map_pieces",
    MSB_MODEL_LIST_NAMES=["map_piece_models"],
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


class ExportMSBMapPieces(BaseExportMSBParts):
    bl_idname = "export_scene.msb_map_piece"
    bl_label = "Export Map Piece Parts"
    bl_description = ("Export all selected MSB Map Piece parts to MSB. Existing MSB parts with the same name will be "
                      "replaced. Does not export FLVER models")

    config = msb_map_piece_operator_config

    map_piece_flvers: dict[Path, FLVER]
    map_area_texture_collections: dict[str, DDSTextureCollection]

    def init(self, context, settings):
        self.map_piece_flvers = {}
        self.map_area_texture_collections = {}

    def export_model(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_mesh: bpy.types.MeshObject,
        map_stem: str,
    ):
        """Export FLVER model."""
        settings = operator.settings(context)
        bl_flver = BlenderFLVER.from_armature_or_mesh(model_mesh)
        texture_collection = DDSTextureCollection()
        flver = bl_flver.to_soulstruct_obj(operator, context, texture_collection)
        flver.dcx_type = settings.game.get_dcx_type("flver")

        # TODO: Elden Ring will need to export into MAPBNDs (alongside existing grass files).
        model_stem = bl_flver.tight_name
        flver_path = Path(f"map/{map_stem}/{model_stem}.flver")

        if context.scene.flver_export_settings.export_textures:
            # Collect all Blender images for batched map area export.
            area = settings.map_stem[:3]
            area_textures = self.map_area_texture_collections.setdefault(area, DDSTextureCollection())
            area_textures |= texture_collection

        self.map_piece_flvers[flver_path] = flver

    def finish_model_export(self, context: bpy.types.Context, settings: SoulstructSettings):
        """Export all collected FLVERs to their respective paths."""
        for relative_flver_path, flver in self.map_piece_flvers.items():
            settings.export_file(self, flver, relative_flver_path)

        if self.map_area_texture_collections:
            # Export all Map Piece textures collected during FLVER export to their areas.
            for map_area, dds_textures in self.map_area_texture_collections.items():
                export_map_area_textures(self, context, map_area, dds_textures)

        return {"FINISHED"}
