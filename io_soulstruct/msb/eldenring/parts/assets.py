from __future__ import annotations

__all__ = [
    "BlenderMSBPart",
    "BlenderMSBAsset",
]

import traceback

import bpy
from io_soulstruct.exceptions import FLVERImportError
from io_soulstruct.flver.model_import.core import FLVERImporter
from io_soulstruct.flver.model_import.settings import FLVERImportSettings
from io_soulstruct.flver.textures.import_textures import TextureImportManager
from io_soulstruct.flver.utilities import get_flvers_from_binder
from io_soulstruct.general.core import SoulstructSettings
from io_soulstruct.msb.properties import MSBPartSubtype
from io_soulstruct.msb.utilities import find_flver_model
from io_soulstruct.utilities import LoggingOperator, get_collection
from soulstruct.base.models.flver import FLVER
from soulstruct.containers import Binder
from soulstruct.eldenring.maps.parts import MSBAsset
from .base import BlenderMSBPart


class BlenderMSBAsset(BlenderMSBPart):

    PART_SUBTYPE = MSBPartSubtype.ASSET

    @property
    def asset_props(self):
        return self.obj.msb_asset_props

    @classmethod
    def find_model(cls, model_name: str, map_stem: str):
        return find_flver_model(cls.PART_SUBTYPE, model_name)

    @classmethod
    def import_model(
        cls,
        operator: LoggingOperator,
        context,
        settings: SoulstructSettings,
        model_name: str,
        map_stem="",  # not used
    ) -> bpy.types.MeshObject:
        """Import the model of the given name into a collection in the current scene."""

        flver_import_settings = context.scene.flver_import_settings  # type: FLVERImportSettings
        chrbnd_path = settings.get_import_file_path(f"obj/{model_name}.objbnd")

        operator.info(f"Importing asset FLVER from: {chrbnd_path.name}")

        texture_manager = TextureImportManager(settings) if flver_import_settings.import_textures else None

        objbnd = Binder.from_path(chrbnd_path)
        binder_flvers = get_flvers_from_binder(objbnd, chrbnd_path, allow_multiple=False)
        if texture_manager:
            texture_manager.find_flver_textures(chrbnd_path, objbnd)
        flver = binder_flvers[0]  # type: FLVER

        importer = FLVERImporter(
            operator,
            context,
            settings,
            texture_import_manager=texture_manager,
            collection=get_collection("Asset Models", context.scene.collection),
        )

        try:
            bl_flver = importer.import_flver(flver, name=model_name)
        except Exception as ex:
            # Delete any assets created prior to exception.
            importer.abort_import()
            traceback.print_exc()  # for inspection in Blender console
            raise FLVERImportError(f"Cannot import FLVER from OBJBND: {chrbnd_path.name}. Error: {ex}")

        return bl_flver.mesh

    def set_properties(self, operator: LoggingOperator, part: MSBAsset):
        super().set_properties(operator, part)
        # TODO: Currently no properties for Assets.
