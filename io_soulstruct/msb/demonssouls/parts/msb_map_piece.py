from __future__ import annotations

__all__ = [
    "BlenderMSBMapPiece",
]

import re
import traceback
import typing as tp
from pathlib import Path

import bpy
from io_soulstruct.exceptions import FLVERImportError, MissingPartModelError
from io_soulstruct.flver.image.image_import_manager import ImageImportManager
from io_soulstruct.flver.models import BlenderFLVER
from io_soulstruct.msb.properties import MSBPartSubtype, MSBMapPieceProps
from io_soulstruct.msb.utilities import find_flver_model, batch_import_flver_models
from io_soulstruct.types import *
from io_soulstruct.utilities import LoggingOperator, get_or_create_collection
from soulstruct.base.models.flver import FLVER
from soulstruct.demonssouls.maps.models import MSBMapPieceModel
from soulstruct.demonssouls.maps.msb import MSBMapPiece
from .msb_part import BlenderMSBPart


class BlenderMSBMapPiece(BlenderMSBPart[MSBMapPiece, MSBMapPieceProps]):

    OBJ_DATA_TYPE = SoulstructDataType.MESH
    SOULSTRUCT_CLASS = MSBMapPiece
    SOULSTRUCT_MODEL_CLASS = MSBMapPieceModel
    PART_SUBTYPE = MSBPartSubtype.MapPiece
    MODEL_SUBTYPES = ["map_piece_models"]

    __slots__ = []

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
        model_collection: bpy.types.Collection = None,
    ) -> bpy.types.MeshObject:
        """Import the model of the given name into a collection in the current scene."""
        settings = operator.settings(context)
        flver_import_settings = context.scene.flver_import_settings
        try:
            flver_path = settings.get_import_map_file_path(f"{model_name}.flver", map_stem=map_stem)
        except FileNotFoundError:
            raise FLVERImportError(f"Cannot find FLVER model file for Map Piece: {model_name}.")

        operator.info(f"Importing map piece FLVER: {flver_path}")

        flver = FLVER.from_path(flver_path)

        if flver_import_settings.import_textures:
            image_import_manager = ImageImportManager(operator, context)
            image_import_manager.find_flver_textures(flver_path)
            area_re = re.compile(r"^m\d\d_")
            texture_map_areas = {
                texture_path.stem[:3]
                for texture_path in flver.get_all_texture_paths()
                if re.match(area_re, texture_path.stem)
            }
            for map_area in texture_map_areas:
                map_area_dir = (flver_path.parent / f"../{map_area}").resolve()
                image_import_manager.find_specific_map_textures(map_area_dir)
        else:
            image_import_manager = None

        if not model_collection:
            model_collection = get_or_create_collection(
                context.scene.collection,
                f"{map_stem} Models",
                f"{map_stem} Map Piece Models",
                hide_viewport=context.scene.msb_import_settings.hide_model_collections,
            )
        try:
            bl_flver = BlenderFLVER.new_from_soulstruct_obj(
                operator,
                context,
                flver,
                model_name,
                image_import_manager=image_import_manager,
                collection=model_collection,
                force_bone_data_type=BlenderFLVER.BoneDataType.POSE,
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
        try_import_model=True,
        model_collection: bpy.types.Collection = None,
    ) -> tp.Self:
        """Map Pieces sometimes use bones to place vertex subsets, which look like nonsense without that positioning.

        So if the Map Piece FLVER model has an Armature, we copy it to this Part, including current pose data. It will
        never be used during Part export. (Cutscenes may also use it, though I don't think Map Pieces are "animated".)
        """
        bl_map_piece = super().new_from_soulstruct_obj(
            operator, context, soulstruct_obj, name, collection, map_stem, try_import_model, model_collection
        )  # type: BlenderMSBMapPiece

        if bl_map_piece.model and not bl_map_piece.model.get("MSB_MODEL_PLACEHOLDER", False):
            bl_flver = BlenderFLVER(bl_map_piece.model)
            if bl_flver.armature:
                # This handles parenting, rigging, etc.
                bl_flver.duplicate_armature(context, bl_map_piece.obj, copy_pose=True)
                # Rename Part Armature object.
                bl_map_piece.armature.name = f"{name} Armature"
                # Rename modifier for clarity.
                bl_map_piece.obj.modifiers["FLVER Armature"].name = "Part Armature"

        return bl_map_piece

    @classmethod
    def batch_import_models(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        parts: list[MSBMapPiece],
        map_stem: str,
    ):
        """Import all models for a batch of MSB Parts, as needed, in parallel as much as possible."""
        settings = operator.settings(context)

        model_datas = {}  # type: dict[str, Path]
        for part in parts:
            if not part.model:
                continue  # ignore (warning will appear when `bl_part.model` assignes None)
            model_name = part.model.get_model_file_stem(map_stem)
            if model_name in model_datas:
                continue  # already queued for import
            try:
                cls.find_model_mesh(model_name, map_stem)
            except MissingPartModelError:
                # Queue up path for batch import.
                model_path = settings.get_import_map_file_path(f"{model_name}.flver", map_stem=map_stem)
                if model_path.is_file():  # otherwise, we'll get a handled error later
                    model_datas[model_name] = model_path

        def image_import_callback(image_import_manager: ImageImportManager, flver: FLVER):
            area_re = re.compile(r"^m\d\d_")
            texture_map_areas = {
                texture_path.stem[:3]
                for texture_path in flver.get_all_texture_paths()
                if re.match(area_re, texture_path.stem)
            }
            for map_area in texture_map_areas:
                map_area_dir = (flver.path.parent / f"../{map_area}").resolve()
                image_import_manager.find_specific_map_textures(map_area_dir)

        if not model_datas:
            operator.info("No Map Piece FLVER models to import.")
            return  # nothing to import

        batch_import_flver_models(
            operator,
            context,
            model_datas,
            map_stem,
            cls.PART_SUBTYPE.get_nice_name(),
            flver_source_binders=None,
            image_import_callback=image_import_callback,
        )
