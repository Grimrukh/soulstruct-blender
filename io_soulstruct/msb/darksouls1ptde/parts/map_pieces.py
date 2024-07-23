from __future__ import annotations

__all__ = [
    "BlenderMSBMapPiece",
]

import re
import traceback

import bpy
from io_soulstruct.exceptions import FLVERImportError
from io_soulstruct.flver.model_import import FLVERImporter
from io_soulstruct.flver.textures.import_textures import TextureImportManager
from io_soulstruct.general.core import SoulstructSettings
from io_soulstruct.msb.properties import MSBPartSubtype
from io_soulstruct.msb.utilities import find_flver_model
from io_soulstruct.utilities import LoggingOperator, get_collection
from soulstruct.base.models.flver import FLVER
from soulstruct.darksouls1ptde.maps.msb import MSBMapPiece
from .base import BlenderMSBPart


class BlenderMSBMapPiece(BlenderMSBPart):

    SOULSTRUCT_CLASS = MSBMapPiece
    PART_SUBTYPE = MSBPartSubtype.MAP_PIECE
    MODEL_SUBTYPES = ["map_piece_models"]

    # No additional Map Piece properties.

    @classmethod
    def find_model(cls, model_name: str, map_stem: str):
        return find_flver_model(cls.PART_SUBTYPE, model_name)

    @classmethod
    def import_model(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        map_stem: str,
        model_name: str,
    ) -> bpy.types.MeshObject:
        """Import the model of the given name into a collection in the current scene."""
        flver_import_settings = context.scene.flver_import_settings
        flver_path = settings.get_import_map_path(f"{model_name}.flver")

        operator.info(f"Importing map piece FLVER: {flver_path}")

        flver = FLVER.from_path(flver_path)

        if flver_import_settings.import_textures:
            texture_manager = TextureImportManager(settings)
            texture_manager.find_flver_textures(flver_path)
            area_re = re.compile(r"^m\d\d_")
            texture_map_areas = {
                texture_path.stem[:3]
                for texture_path in flver.get_all_texture_paths()
                if re.match(area_re, texture_path.stem)
            }
            for map_area in texture_map_areas:
                map_area_dir = (flver_path.parent / f"../{map_area}").resolve()
                texture_manager.find_specific_map_textures(map_area_dir)
        else:
            texture_manager = None

        map_piece_model_collection = get_collection(f"{map_stem} Map Piece Models", context.scene.collection)
        importer = FLVERImporter(
            operator,
            context,
            settings,
            texture_import_manager=texture_manager,
            collection=map_piece_model_collection,
        )

        try:
            bl_flver = importer.import_flver(flver, name=model_name)
        except Exception as ex:
            # Delete any objects created prior to exception.
            importer.abort_import()
            traceback.print_exc()  # for inspection in Blender console
            raise FLVERImportError(f"Cannot import FLVER: {flver_path.name}. Error: {ex}")

        # Return only the mesh for MSB Part instances.
        return bl_flver.mesh
