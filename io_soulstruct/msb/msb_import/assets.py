"""Import MSB Asset entries."""
from __future__ import annotations

__all__ = [
    "ImportMSBAsset",
    "ImportAllMSBAssets",
]

import time
import traceback
import typing as tp

import bpy

from soulstruct.containers import Binder

from io_soulstruct.exceptions import *
from io_soulstruct.utilities import *
from io_soulstruct.flver.textures.import_textures import TextureImportManager
from io_soulstruct.flver.model_import import FLVERImporter, FLVERImportSettings
from io_soulstruct.flver.utilities import get_flvers_from_binder
from .core import *

if tp.TYPE_CHECKING:
    from io_soulstruct.general import SoulstructSettings
    from io_soulstruct.type_checking import MSB_ASSET_TYPING


def import_asset_model(
    operator: LoggingOperator, context, settings: SoulstructSettings, model_name: str
) -> tuple[bpy.types.ArmatureObject | None, bpy.types.MeshObject]:
    """Import the model of the given name into a collection in the current scene."""

    flver_import_settings = context.scene.flver_import_settings  # type: FLVERImportSettings
    chrbnd_path = settings.get_import_file_path(f"obj/{model_name}.objbnd")

    operator.info(f"Importing asset FLVER from: {chrbnd_path.name}")

    texture_manager = TextureImportManager(settings) if flver_import_settings.import_textures else None

    objbnd = Binder.from_path(chrbnd_path)
    binder_flvers = get_flvers_from_binder(objbnd, chrbnd_path, allow_multiple=False)
    if texture_manager:
        texture_manager.find_flver_textures(chrbnd_path, objbnd)
    flver = binder_flvers[0]

    importer = FLVERImporter(
        operator,
        context,
        settings,
        texture_import_manager=texture_manager,
        collection=get_collection("Asset Models", context.scene.collection, hide_viewport=True),
    )

    try:
        return importer.import_flver(flver, name=model_name)
    except Exception as ex:
        # Delete any assets created prior to exception.
        importer.abort_import()
        traceback.print_exc()  # for inspection in Blender console
        raise FLVERImportError(f"Cannot import FLVER from OBJBND: {chrbnd_path.name}. Error: {ex}")


def get_asset_model(
    operator: LoggingOperator, context, settings: SoulstructSettings, model_name: str
) -> tuple[bpy.types.ArmatureObject, bpy.types.MeshObject]:
    """Find or create actual Blender model armature/mesh data."""
    try:
        return find_flver_model("Asset", model_name)
    except MissingModelError:
        t = time.perf_counter()
        armature, mesh = import_asset_model(operator, context, settings, model_name)
        operator.info(f"Imported Asset FLVER Model '{model_name}' in {time.perf_counter() - t:.3f} seconds.")
        return armature, mesh


class BaseImportMSBAsset(BaseImportMSBPart):

    PART_TYPE_NAME = "Asset"
    PART_TYPE_NAME_PLURAL = "Assets"
    MSB_LIST_NAME = "assets"

    def _create_part_instance(
        self,
        context,
        settings: SoulstructSettings,
        map_stem: str,
        part: MSB_ASSET_TYPING,
        collection: bpy.types.Collection,
    ) -> bpy.types.Object:
        armature, mesh = get_asset_model(self, context, settings, part.model.name)  # NOT map-specific
        part_armature, part_mesh = create_flver_model_instance(context, armature, mesh, part.name, collection)
        msb_entry_to_obj_transform(part, part_armature)
        # Currently no custom properties managed.
        return part_armature  # return armature to center view on

class ImportMSBAsset(BaseImportMSBAsset):
    """Import ALL MSB Asset parts and their transforms. Will probably take a long time!"""
    bl_idname = "import_scene.msb_asset_part"
    bl_label = "Import Asset Part"
    bl_description = "Import FLVER model and MSB transform of selected MSB Asset part"

    GAME_ENUM_NAME = "asset_part"

    def execute(self, context):
        return self.import_enum_part(context)


class ImportAllMSBAssets(BaseImportMSBAsset):
    """Import ALL MSB Asset parts and their transforms. Will probably take a long time!"""
    bl_idname = "import_scene.all_msb_asset_parts"
    bl_label = "Import All Asset Parts"
    bl_description = ("Import FLVER model and MSB transform of every MSB Asset part. Very slow, especially when "
                      "textures are imported (see console output for progress)")

    GAME_ENUM_NAME = None

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        return self.import_all_parts(context)
