"""Import MSB Character entries."""
from __future__ import annotations

__all__ = [
    "ImportMSBCharacter",
    "ImportAllMSBCharacters",
]

import time
import traceback
import typing as tp

import bpy

from soulstruct.containers import Binder

from io_soulstruct.utilities import *
from io_soulstruct.flver.textures.import_textures import TextureImportManager
from io_soulstruct.flver.model_import import FLVERImporter, FLVERImportSettings
from io_soulstruct.flver.utilities import FLVERImportError, get_flvers_from_binder
from .core import *

if tp.TYPE_CHECKING:
    from soulstruct.darksouls1r.maps.parts import MSBCharacter  # TODO: use multi-game typing
    from io_soulstruct.general import SoulstructSettings


def import_character_model(
    operator: LoggingOperator, context, settings: SoulstructSettings, model_name: str
) -> tuple[bpy.types.ArmatureObject | None, bpy.types.MeshObject]:
    """Import the model of the given name into a collection in the current scene."""

    flver_import_settings = context.scene.flver_import_settings  # type: FLVERImportSettings
    chrbnd_path = settings.get_import_file_path(f"chr/{model_name}.chrbnd")

    operator.info(f"Importing character FLVER from: {chrbnd_path.name}")

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


def get_character_model(
    operator: LoggingOperator, context, settings: SoulstructSettings, model_name: str
) -> tuple[bpy.types.ArmatureObject, bpy.types.MeshObject]:
    """Find or create actual Blender model armature/mesh data."""
    try:
        return find_flver_model("Character", model_name)
    except MissingModelError:
        t = time.perf_counter()
        armature, mesh = import_character_model(operator, context, settings, model_name)
        operator.info(f"Imported Character FLVER Model '{model_name}' in {time.perf_counter() - t:.3f} seconds.")
        return armature, mesh


class BaseImportMSBCharacter(BaseImportMSBPart):

    PART_TYPE_NAME = "Character"
    PART_TYPE_NAME_PLURAL = "Characters"
    MSB_LIST_NAME = "characters"

    def _create_part_instance(
        self, context, settings: SoulstructSettings, map_stem: str, part: MSBCharacter, collection: bpy.types.Collection
    ) -> bpy.types.Object:
        armature, mesh = get_character_model(self, context, settings, part.model.name)  # NOT map-specific
        part_armature, part_mesh = create_flver_model_instance(context, armature, mesh, part.name, collection)
        msb_entry_to_obj_transform(part, part_armature)
        part_armature["Draw Parent Name"] = part.draw_parent.name if part.draw_parent else ""
        return part_armature  # only return root object

class ImportMSBCharacter(BaseImportMSBCharacter):
    """Import ALL MSB Character parts and their transforms. Will probably take a long time!"""
    bl_idname = "import_scene.msb_character_part"
    bl_label = "Import Character Part"
    bl_description = "Import FLVER model and MSB transform of selected MSB Character part"

    GAME_ENUM_NAME = "character_part"

    def execute(self, context):
        return self.import_enum_part(context)


class ImportAllMSBCharacters(BaseImportMSBCharacter):
    """Import ALL MSB Character parts and their transforms. Will probably take a long time!"""
    bl_idname = "import_scene.all_msb_character_parts"
    bl_label = "Import All Character Parts"
    bl_description = "Import FLVER model and MSB transform of every MSB Character part (SLOW)"

    GAME_ENUM_NAME = None

    def execute(self, context):
        return self.import_all_parts(context)
