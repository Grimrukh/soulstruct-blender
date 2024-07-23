"""Import MSB Map Piece entries."""
from __future__ import annotations

__all__ = [
    "ImportMSBMapPiece",
    "ImportAllMSBMapPieces",
    "ExportMSBMapPieces",
]

import typing as tp
from pathlib import Path

import bpy
from io_soulstruct import SoulstructSettings
from io_soulstruct.flver.model_export import FLVERExporter
from io_soulstruct.flver.textures.export_textures import export_map_area_textures
from io_soulstruct.flver.types import BlenderFLVER
from io_soulstruct.msb.core import MSBPartOperatorConfig
from io_soulstruct.msb.properties import MSBPartSubtype
from io_soulstruct.utilities import *
from .base import *

if tp.TYPE_CHECKING:
    from soulstruct.base.models.flver import FLVER


msb_map_piece_operator_config = MSBPartOperatorConfig(
    PART_SUBTYPE=MSBPartSubtype.MAP_PIECE,
    MSB_LIST_NAME="map_pieces",
    MSB_MODEL_LIST_NAME="map_piece_models",
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


class ExportMSBMapPieces(BaseExportMSBParts):
    bl_idname = "export_scene.msb_map_piece"
    bl_label = "Export Map Piece Parts"
    bl_description = ("Export all selected MSB Map Piece parts to MSB. Existing MSB parts with the same name will be "
                      "replaced. Does not export FLVER models")

    config = msb_map_piece_operator_config

    map_piece_flvers: dict[Path, FLVER]
    map_area_textures: dict[str, dict[str, bpy.types.Image]]

    def init(self, context, settings):
        self.map_piece_flvers = {}
        self.map_area_textures = {}

    def export_model(
        self,
        bl_model_obj: bpy.types.MeshObject,
        settings: SoulstructSettings,
        map_stem: str,
        flver_exporter: FLVERExporter | None,
        export_textures=False,
    ):
        # Export FLVER model.
        bl_flver = BlenderFLVER.from_bl_obj(bl_model_obj, self)
        flver = flver_exporter.export_flver(bl_flver)
        flver.dcx_type = settings.game.get_dcx_type("flver")
        # TODO: Elden Ring will need to export into MAPBNDs (alongside existing grass files).
        model_stem = get_bl_obj_tight_name(bl_model_obj)
        flver_path = Path(f"map/{map_stem}/{model_stem}.flver")

        if export_textures:
            # Collect all Blender images for batched map area export.
            area = settings.map_stem[:3]
            area_textures = self.map_area_textures.setdefault(area, {})
            area_textures |= flver_exporter.collected_texture_images
            flver_exporter.collected_texture_images.clear()

        self.map_piece_flvers[flver_path] = flver

    def finish_model_export(self, context: bpy.types.Context, settings: SoulstructSettings):
        """Export all collected FLVERs to their respective paths."""
        for relative_flver_path, flver in self.map_piece_flvers.items():
            settings.export_file(self, flver, relative_flver_path)

        if self.map_area_textures:
            # Export all Map Piece textures collected during FLVER export to their areas.
            export_map_area_textures(
                self,
                context,
                self.settings(context),
                self.map_area_textures,
            )
