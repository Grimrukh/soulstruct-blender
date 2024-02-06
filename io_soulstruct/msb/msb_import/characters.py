"""Operators for importing entries from MSB files.

These operators will import entries from MSB files into the current scene. The imported objects will link to the
armature and mesh data of FLVER models found in the apppropriate Blender collection, e.g. "Character Models", and import
that model if it doesn't exist.
"""
from __future__ import annotations

__all__ = [
    "ImportAllMSBCharacters",
]

import fnmatch
import re
import time
import traceback
import typing as tp

import bpy

from soulstruct.containers import Binder

from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.utilities import *
from io_soulstruct.flver.textures.import_textures import TextureImportManager
from io_soulstruct.flver.flver_import import FLVERImporter, FLVERImportSettings
from io_soulstruct.flver.utilities import FLVERImportError, get_flvers_from_binder
from .core import *

if tp.TYPE_CHECKING:
    from io_soulstruct.general import SoulstructSettings
    from io_soulstruct.type_checking import MSB_TYPING
    from .settings import MSBImportSettings


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


class ImportAllMSBCharacters(LoggingOperator):
    """Import ALL MSB Character parts and their transforms. Will probably take a long time!"""
    bl_idname = "import_scene.all_msb_character_parts"
    bl_label = "Import All Character Parts"
    bl_description = "Import FLVER model and MSB transform of every MSB Character part (SLOW)"

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)
        msb_path = settings.get_import_msb_path()
        if not is_path_and_file(msb_path):
            return False
        return True  # MSB exists

    def execute(self, context):

        start_time = time.perf_counter()

        settings = self.settings(context)
        settings.save_settings()

        msb_import_settings = context.scene.msb_import_settings  # type: MSBImportSettings

        part_name_match = msb_import_settings.part_name_match
        match msb_import_settings.part_name_match_mode:
            case "GLOB":
                def is_name_match(name: str):
                    return part_name_match in {"", "*"} or fnmatch.fnmatch(name, part_name_match)
            case "REGEX":
                pattern = re.compile(part_name_match)

                def is_name_match(name: str):
                    return part_name_match == "" or re.match(pattern, name)
            case _:  # should never happen
                return self.error(f"Invalid MSB part name match mode: {msb_import_settings.part_name_match_mode}")

        if not settings.get_import_map_path():  # validation
            return self.error("Game directory and map stem must be set in Blender's Soulstruct global settings.")

        map_stem = settings.get_latest_map_stem_version()
        msb_path = settings.get_import_msb_path()  # will automatically use latest MSB version if known and enabled
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING

        part_count = 0

        if msb_import_settings.include_pattern_in_parent_name:
            collection_name = f"{map_stem} Characters ({part_name_match})"
        else:
            collection_name = f"{map_stem} Characters"
        collection = get_collection(collection_name, context.scene.collection)

        for character in msb.characters:

            part_name = character.name
            if not is_name_match(part_name):
                # MSB part name (part, not model) does not match glob/regex.
                continue

            try:
                # NOTE: Returned armature CANNOT be `None` here.
                armature, mesh = get_character_model(self, context, settings, character.model.name)
            except Exception as ex:
                self.error(f"Cannot find or import model for MSB part '{character.name}': {ex}")
                continue

            part_armature, part_mesh = create_flver_model_instance(context, armature, mesh, part_name, collection)
            msb_entry_to_obj_transform(character, part_armature)
            part_count += 1

        if part_count == 0:
            self.warning(
                f"No MSB Character parts found with {msb_import_settings.part_name_match_mode} filter: "
                f"'{part_name_match}'"
            )
            return {"CANCELLED"}

        self.info(
            f"Imported {part_count} / {len(msb.map_pieces)} MSB Character parts in "
            f"{time.perf_counter() - start_time:.3f} seconds (filter: '{part_name_match}')."
        )

        # No change in view after importing all characters.

        return {"FINISHED"}
