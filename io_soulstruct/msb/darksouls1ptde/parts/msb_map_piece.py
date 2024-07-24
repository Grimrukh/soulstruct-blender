from __future__ import annotations

__all__ = [
    "BlenderMSBMapPiece",
]

import re
import traceback

import bpy
from io_soulstruct.exceptions import FLVERImportError
from io_soulstruct.flver.models import BlenderFLVER
from io_soulstruct.flver.textures.import_textures import TextureImportManager
from io_soulstruct.msb.properties import MSBPartSubtype, MSBMapPieceProps
from io_soulstruct.msb.utilities import find_flver_model
from io_soulstruct.types import *
from io_soulstruct.utilities import LoggingOperator, get_collection
from soulstruct.base.models.flver import FLVER
from soulstruct.darksouls1ptde.maps.msb import MSBMapPiece
from .msb_part import BlenderMSBPart


class BlenderMSBMapPiece(BlenderMSBPart[MSBMapPiece, MSBMapPieceProps]):

    OBJ_DATA_TYPE = SoulstructDataType.MESH
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
        map_stem: str,
        model_name: str,
    ) -> bpy.types.MeshObject:
        """Import the model of the given name into a collection in the current scene."""
        settings = operator.settings(context)
        flver_import_settings = context.scene.flver_import_settings
        flver_path = settings.get_import_map_path(f"{model_name}.flver")

        operator.info(f"Importing map piece FLVER: {flver_path}")

        flver = FLVER.from_path(flver_path)

        if flver_import_settings.import_textures:
            texture_import_manager = TextureImportManager(settings)
            texture_import_manager.find_flver_textures(flver_path)
            area_re = re.compile(r"^m\d\d_")
            texture_map_areas = {
                texture_path.stem[:3]
                for texture_path in flver.get_all_texture_paths()
                if re.match(area_re, texture_path.stem)
            }
            for map_area in texture_map_areas:
                map_area_dir = (flver_path.parent / f"../{map_area}").resolve()
                texture_import_manager.find_specific_map_textures(map_area_dir)
        else:
            texture_import_manager = None

        map_piece_model_collection = get_collection(f"{map_stem} Map Piece Models", context.scene.collection)
        try:
            bl_flver = BlenderFLVER.new_from_soulstruct_obj(
                operator,
                context,
                flver,
                model_name,
                texture_import_manager=texture_import_manager,
                collection=map_piece_model_collection,
            )
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            raise FLVERImportError(f"Cannot import FLVER: {flver_path.name}. Error: {ex}")

        # Return only the mesh for MSB Part instances.
        return bl_flver.mesh
