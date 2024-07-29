from __future__ import annotations

__all__ = [
    "BlenderMSBMapPiece",
]

import re
import traceback
import typing as tp

import bpy
from io_soulstruct.exceptions import FLVERImportError
from io_soulstruct.flver.models import BlenderFLVER
from io_soulstruct.flver.image.image_import_manager import ImageImportManager
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

    __slots__ = []
    obj: bpy.types.MeshObject

    # No additional Map Piece properties.

    @property
    def armature(self) -> bpy.types.ArmatureObject | None:
        """Detect parent Armature of wrapped Mesh object. Rarely present for Parts."""
        if self.obj.parent and self.obj.parent.type == "ARMATURE":
            # noinspection PyTypeChecker
            return self.obj.parent
        return None

    @classmethod
    def find_model_mesh(cls, model_name: str, map_stem: str) -> bpy.types.MeshObject:
        return find_flver_model(model_name).mesh

    @classmethod
    def import_model_mesh(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_name: str,
        map_stem: str,  # required for Map Pieces
    ) -> bpy.types.MeshObject:
        """Import the model of the given name into a collection in the current scene."""
        settings = operator.settings(context)
        flver_import_settings = context.scene.flver_import_settings
        try:
            flver_path = settings.get_import_map_file_path(f"{model_name}.flver")
        except FileNotFoundError:
            raise FLVERImportError(f"Cannot find FLVER model file for Map Piece: {model_name}.")

        operator.info(f"Importing map piece FLVER: {flver_path}")

        flver = FLVER.from_path(flver_path)

        if flver_import_settings.import_textures:
            texture_import_manager = ImageImportManager(operator, context)
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

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBMapPiece,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
    ) -> tp.Self:
        """Map Pieces sometimes use bones to place vertex subsets, which look like nonsense without that positioning.

        So if the Map Piece FLVER model has an Armature, we copy it to this Part, including current pose data. It will
        never be used during Part export. (Cutscenes may also use it, though I don't think Map Pieces are "animated".)
        """
        bl_map_piece = super().new_from_soulstruct_obj(
            operator, context, soulstruct_obj, name, collection, map_stem
        )  # type: BlenderMSBMapPiece

        if bl_map_piece.model:
            bl_flver = BlenderFLVER(bl_map_piece.model)
            if bl_flver.armature:
                # This handles parenting, rigging, etc.
                bl_flver.duplicate_armature(context, bl_map_piece.obj, copy_pose=True)
                # Rename modifier for clarity.
                bl_map_piece.obj.modifiers["FLVER Armature"].name = "Part Armature"

        return bl_map_piece
