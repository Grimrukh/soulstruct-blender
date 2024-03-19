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

import re
import time
import traceback
import typing as tp

import bpy
import bpy.ops

from soulstruct.base.models.flver import FLVER

from io_soulstruct.utilities import *
from io_soulstruct.flver.textures.import_textures import TextureImportManager
from io_soulstruct.flver.model_import import FLVERImporter, FLVERImportSettings
from io_soulstruct.flver.utilities import FLVERImportError
from .core import *

if tp.TYPE_CHECKING:
    from soulstruct.darksouls1r.maps.parts import MSBMapPiece  # TODO: use multi-game typing
    from soulstruct.base.models.mtd import MTDBND
    from io_soulstruct.general import SoulstructSettings


def import_map_piece_model(
    operator: LoggingOperator,
    context,
    settings: SoulstructSettings,
    map_stem: str,
    model_name: str,
    mtdbnd: MTDBND | None = None,
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
        collection=get_collection(f"{map_stem} Map Piece Models", context.scene.collection, hide_viewport=True),
        mtdbnd=mtdbnd,
    )

    try:
        return importer.import_flver(flver, name=model_name)
    except Exception as ex:
        # Delete any objects created prior to exception.
        importer.abort_import()
        traceback.print_exc()  # for inspection in Blender console
        raise FLVERImportError(f"Cannot import FLVER: {flver_path.name}. Error: {ex}")


def get_map_piece_model(
    operator: LoggingOperator,
    context: bpy.types.Context,
    settings: SoulstructSettings,
    map_stem: str,
    model_name: str,
    mtdbnd: MTDBND | None = None,
) -> tuple[bpy.types.ArmatureObject | None, bpy.types.MeshObject]:
    """Find or create actual Blender model armature/mesh data."""
    try:
        return find_flver_model(f"{map_stem} Map Piece", model_name)
    except MissingModelError:
        t = time.perf_counter()
        armature, mesh = import_map_piece_model(operator, context, settings, map_stem, model_name, mtdbnd)
        operator.info(f"Imported {map_stem} Map Piece model '{model_name}' in {time.perf_counter() - t:.3f} seconds.")
        return armature, mesh


class BaseImportMSBMapPiece(BaseImportMSBPart):

    PART_TYPE_NAME = "Map Piece"
    PART_TYPE_NAME_PLURAL = "Map Pieces"
    MSB_LIST_NAME = "map_pieces"
    USE_MTDBND = True

    def _create_part_instance(
        self,
        context,
        settings: SoulstructSettings,
        map_stem: str,
        part: MSBMapPiece,
        collection: bpy.types.Collection,
        mtdbnd: MTDBND | None = None,
    ) -> bpy.types.Object:
        model_name = part.model.get_model_file_stem(map_stem)
        armature, mesh = get_map_piece_model(self, context, settings, map_stem, model_name, mtdbnd)
        part_armature, part_mesh = create_flver_model_instance(
            context, armature, mesh, part.name, collection, copy_pose=True
        )
        msb_entry_to_obj_transform(part, part_armature)
        return part_mesh  # return mesh to center view on


class ImportMSBMapPiece(BaseImportMSBMapPiece):
    """Import the model of an enum-selected MSB Map Piece part, and its MSB transform."""
    bl_idname = "import_scene.msb_map_piece_part"
    bl_label = "Import Map Piece Part"
    bl_description = "Import FLVER model and MSB transform of selected Map Piece MSB part"

    GAME_ENUM_NAME = "map_piece_part"

    def execute(self, context):
        return self.import_enum_part(context)


class ImportAllMSBMapPieces(BaseImportMSBMapPiece):
    """Import ALL MSB map piece parts and their transforms. Will probably take a long time!"""
    bl_idname = "import_scene.all_msb_map_piece_parts"
    bl_label = "Import All Map Piece Parts"
    bl_description = ("Import FLVER model and MSB transform of every Map Piece MSB part. Very slow, especially when "
                      "importing textures (see console output for progress)")

    GAME_ENUM_NAME = None

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        return self.import_all_parts(context)
