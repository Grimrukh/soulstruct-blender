"""Operators for importing entries from MSB files.

These operators will import entries from MSB files into the current scene. The imported objects will link to the
armature and mesh data of FLVER models found in the apppropriate Blender collection, e.g. "Character Models", and import
that model if it doesn't exist.
"""
from __future__ import annotations

__all__ = [
    "ImportMSBMapPiece",
    "ImportAllMSBMapPieces",
]

import fnmatch
import re
import time
import traceback
import typing as tp

import bpy
import bpy.ops

from soulstruct.base.models.flver import FLVER

from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.utilities import *
from io_soulstruct.flver.textures.import_textures import TextureImportManager
from io_soulstruct.flver.flver_import import FLVERImporter, FLVERImportSettings
from io_soulstruct.flver.utilities import FLVERImportError
from .core import *

if tp.TYPE_CHECKING:
    from io_soulstruct.general import SoulstructSettings, SoulstructGameEnums
    from io_soulstruct.type_checking import MSB_TYPING
    from .settings import MSBImportSettings


def import_map_piece_model(
    operator: LoggingOperator, context, settings: SoulstructSettings, model_name: str
) -> tuple[bpy.types.ArmatureObject | None, bpy.types.MeshObject]:
    """Import the model of the given name into a collection in the current scene."""

    flver_import_settings = context.scene.flver_import_settings  # type: FLVERImportSettings
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

    importer = FLVERImporter(
        operator,
        context,
        settings,
        texture_import_manager=texture_manager,
        collection=get_collection("Map Piece Models", context.scene.collection),
    )

    try:
        return importer.import_flver(flver, name=model_name)
    except Exception as ex:
        # Delete any objects created prior to exception.
        importer.abort_import()
        traceback.print_exc()  # for inspection in Blender console
        raise FLVERImportError(f"Cannot import FLVER: {flver_path.name}. Error: {ex}")


def get_map_piece_model(
    operator: LoggingOperator, context, settings: SoulstructSettings, model_name: str
) -> tuple[bpy.types.ArmatureObject | None, bpy.types.MeshObject]:
    """Find or create actual Blender model armature/mesh data."""
    try:
        return find_flver_model("Map Piece", model_name)
    except MissingModelError:
        t = time.perf_counter()
        armature, mesh = import_map_piece_model(operator, context, settings, model_name)
        operator.info(f"Imported Map Piece FLVER Model '{model_name}' in {time.perf_counter() - t:.3f} seconds.")
        return armature, mesh


class ImportMSBMapPiece(LoggingOperator):
    """Import the model of an enum-selected MSB Map Piece part, and its MSB transform."""
    bl_idname = "import_scene.msb_map_piece_part"
    bl_label = "Import Map Piece Part"
    bl_description = "Import FLVER model and MSB transform of selected Map Piece MSB part"

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)
        msb_path = settings.get_import_msb_path()
        if not is_path_and_file(msb_path):
            return False
        game_enums = context.scene.soulstruct_game_enums  # type: SoulstructGameEnums
        if game_enums.map_piece_part in {"", "0"}:
            return False
        return True  # MSB exists and a Map Piece part name is selected from enum

    def execute(self, context):

        settings = self.settings(context)
        settings.save_settings()

        part_name = context.scene.soulstruct_game_enums.map_piece_part
        if part_name in {"", "0"}:
            return self.error(f"Invalid MSB map piece selection: {part_name}")
        msb_path = settings.get_import_msb_path()  # will automatically use latest MSB version if known and enabled
        map_stem = settings.get_oldest_map_stem_version()  # for FLVERs

        # Get MSB part transform.
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING
        map_piece_part = msb.map_pieces.find_entry_name(part_name)

        try:
            armature, mesh = get_map_piece_model(
                self, context, settings, map_piece_part.model.get_model_file_stem(map_stem)
            )
        except Exception as ex:
            return self.error(f"Cannot find or import model for MSB part '{part_name}': {ex}")

        collection = get_collection(f"{settings.map_stem} Map Pieces", context.scene.collection)
        part_armature, part_mesh = create_flver_model_instance(context, armature, mesh, part_name, collection)
        msb_entry_to_obj_transform(map_piece_part, part_armature or part_mesh)

        # Select and frame view on (final) newly imported Mesh.
        self.set_active_obj(mesh)
        bpy.ops.view3d.view_selected(use_all_regions=False)

        return {"FINISHED"}


class ImportAllMSBMapPieces(LoggingOperator):
    """Import ALL MSB map piece parts and their transforms. Will probably take a long time!"""
    bl_idname = "import_scene.all_msb_map_piece_parts"
    bl_label = "Import All Map Piece Parts"
    bl_description = "Import FLVER model and MSB transform of every Map Piece MSB part (SLOW)"

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

        map_stem = settings.get_oldest_map_stem_version()  # for FLVERs
        msb_path = settings.get_import_msb_path()  # will automatically use latest MSB version if known and enabled
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING

        part_count = 0
        part_mesh = None  # for getting final mesh to select

        if msb_import_settings.include_pattern_in_parent_name:
            collection_name = f"{map_stem} Map Pieces ({part_name_match})"
        else:
            collection_name = f"{map_stem} Map Pieces"
        collection = get_collection(collection_name, context.scene.collection)

        for map_piece_part in msb.map_pieces:

            part_name = map_piece_part.name
            if not is_name_match(part_name):
                # MSB map piece name (part, not model) does not match glob/regex.
                continue

            try:
                armature, mesh = get_map_piece_model(self, context, settings, map_piece_part.model.get_model_file_stem(map_stem))
            except Exception as ex:
                self.error(f"Cannot find or import model for MSB part '{map_piece_part.name}': {ex}")
                continue

            part_armature, part_mesh = create_flver_model_instance(context, armature, mesh, part_name, collection)
            msb_entry_to_obj_transform(map_piece_part, part_armature or part_mesh)
            part_count += 1

        if part_count == 0:
            self.warning(
                f"No Map Piece MSB parts found with {msb_import_settings.part_name_match_mode} filter: "
                f"'{part_name_match}'"
            )
            return {"CANCELLED"}

        self.info(
            f"Imported {part_count} / {len(msb.map_pieces)} MSB Map Piece parts in "
            f"{time.perf_counter() - start_time:.3f} seconds (filter: '{part_name_match}')."
        )

        # Select and frame view on (final) newly imported Mesh.
        if part_mesh:
            self.set_active_obj(part_mesh)
            bpy.ops.view3d.view_selected(use_all_regions=False)

        return {"FINISHED"}
