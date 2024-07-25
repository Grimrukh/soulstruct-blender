from __future__ import annotations

__all__ = [
    "BlenderMSBPlayerStart",
]

import traceback

import bpy
from io_soulstruct.exceptions import FLVERImportError
from io_soulstruct.flver.textures.import_textures import TextureImportManager
from io_soulstruct.flver.models import BlenderFLVER
from io_soulstruct.flver.utilities import get_flvers_from_binder
from io_soulstruct.msb.properties import MSBPartSubtype, MSBPlayerStartProps
from io_soulstruct.msb.utilities import find_flver_model
from io_soulstruct.types import *
from io_soulstruct.utilities import LoggingOperator, get_collection
from soulstruct.containers import Binder
from soulstruct.darksouls1ptde.maps.parts import MSBPlayerStart
from .msb_part import BlenderMSBPart


class BlenderMSBPlayerStart(BlenderMSBPart[MSBPlayerStart, MSBPlayerStartProps]):
    """Always references 'c0000', but we don't assume anything here, and import that FLVER as required."""

    OBJ_DATA_TYPE = SoulstructDataType.MESH
    SOULSTRUCT_CLASS = MSBPlayerStart
    PART_SUBTYPE = MSBPartSubtype.PLAYER_START
    MODEL_SUBTYPES = ["player_models", "character_models"]

    data: bpy.types.Mesh  # type override (NOTE: c0000 Mesh will be empty)

    # No additional Player Start properties.

    @classmethod
    def find_model(cls, model_name: str, map_stem: str):
        return find_flver_model(cls.PART_SUBTYPE, model_name)

    @classmethod
    def import_model(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_name: str,
        map_stem: str,
    ):
        settings = operator.settings(context)
        flver_import_settings = context.scene.flver_import_settings
        chrbnd_path = settings.get_import_file_path(f"chr/{model_name}.chrbnd")

        operator.info(f"Importing character FLVER from: {chrbnd_path.name}")

        texture_import_manager = TextureImportManager(settings) if flver_import_settings.import_textures else None

        chrbnd = Binder.from_path(chrbnd_path)
        binder_flvers = get_flvers_from_binder(chrbnd, chrbnd_path, allow_multiple=False)
        if texture_import_manager:
            texture_import_manager.find_flver_textures(chrbnd_path, chrbnd)
        flver = binder_flvers[0]

        try:
            return BlenderFLVER.new_from_soulstruct_obj(
                operator,
                context,
                flver,
                model_name,
                texture_import_manager,
                collection=get_collection("Character Models", context.scene.collection),
            )
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            raise FLVERImportError(f"Cannot import FLVER from CHRBND: {chrbnd_path.name}. Error: {ex}")

    # No other overrides needed.
