from __future__ import annotations

__all__ = [
    "BlenderMSBPlayerStart",
]

import traceback

import bpy
from io_soulstruct.exceptions import FLVERImportError
from io_soulstruct.flver.model_import.core import FLVERImporter
from io_soulstruct.flver.textures.import_textures import TextureImportManager
from io_soulstruct.flver.utilities import get_flvers_from_binder
from io_soulstruct.general.core import SoulstructSettings
from io_soulstruct.msb.properties import MSBPartSubtype
from io_soulstruct.msb.utilities import find_flver_model
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import LoggingOperator, get_collection, new_empty_object
from soulstruct.containers import Binder
from soulstruct.darksouls1ptde.maps.parts import MSBPlayerStart
from .base import BlenderMSBPart


class BlenderMSBPlayerStart(BlenderMSBPart[MSBPlayerStart]):
    """Should always use model `c0000`, but we remain agnostic and still reference it as normal."""

    SOULSTRUCT_CLASS = MSBPlayerStart
    PART_SUBTYPE = MSBPartSubtype.PLAYER_START
    MODEL_SUBTYPES = ["player_models", "character_models"]

    # No additional Player Start properties.

    @classmethod
    def find_model(cls, model_name: str, map_stem: str):
        return find_flver_model(cls.PART_SUBTYPE, model_name)

    @classmethod
    def import_model(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        model_name: str,
        map_stem: str,
    ):
        flver_import_settings = context.scene.flver_import_settings
        chrbnd_path = settings.get_import_file_path(f"chr/{model_name}.chrbnd")

        operator.info(f"Importing Player Start (character) FLVER from: {chrbnd_path.name}")

        texture_manager = TextureImportManager(settings) if flver_import_settings.import_textures else None

        chrbnd = Binder.from_path(chrbnd_path)
        binder_flvers = get_flvers_from_binder(chrbnd, chrbnd_path, allow_multiple=False)
        if texture_manager:
            texture_manager.find_flver_textures(chrbnd_path, chrbnd)
        flver = binder_flvers[0]

        importer = FLVERImporter(
            operator,
            context,
            settings,
            texture_import_manager=texture_manager,
            collection=get_collection("Character Models", context.scene.collection),
        )

        try:
            return importer.import_flver(flver, name=model_name)
        except Exception as ex:
            # Delete any objects created prior to exception.
            importer.abort_import()
            traceback.print_exc()  # for inspection in Blender console
            raise FLVERImportError(f"Cannot import FLVER from CHRBND: {chrbnd_path.name}. Error: {ex}")

    @classmethod
    def new_from_entry(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        map_stem: str,
        entry: MSBPlayerStart,
        collection: bpy.types.Collection = None,
    ) -> BlenderMSBPlayerStart:
        """Create a new Blender object for the given MSB part."""

        # Always references c0000, so no need to force a FLVER import of it. We just use an Empty.
        part_empty = new_empty_object(entry.name)
        part_empty.empty_display_type = "PLAIN_AXES"
        part_empty.empty_display_size = 2.0
        part_empty.soulstruct_type = SoulstructType.MSB_PART
        (collection or bpy.context.scene.collection).objects.link(part_empty)

        bl_part = cls(part_empty)
        bl_part.set_obj_transform(entry)
        bl_part.set_obj_properties(operator, entry)  # no subtype properties
        return bl_part
