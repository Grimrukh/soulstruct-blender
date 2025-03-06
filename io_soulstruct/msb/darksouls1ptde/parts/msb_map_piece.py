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
from io_soulstruct.flver.models import BlenderFLVER, FLVERBoneDataType
from io_soulstruct.msb.properties import MSBPartSubtype, MSBMapPieceProps
from io_soulstruct.msb.utilities import find_flver_model, batch_import_flver_models
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import LoggingOperator, get_or_create_collection
from soulstruct.base.models.flver import FLVER
from soulstruct.darksouls1ptde.maps.models import MSBMapPieceModel
from soulstruct.darksouls1ptde.maps.msb import MSBMapPiece
from .msb_part import BlenderMSBPart


class BlenderMSBMapPiece(BlenderMSBPart[MSBMapPiece, MSBMapPieceProps]):

    SOULSTRUCT_CLASS = MSBMapPiece
    SOULSTRUCT_MODEL_CLASS = MSBMapPieceModel
    BLENDER_MODEL_TYPE = SoulstructType.FLVER
    PART_SUBTYPE = MSBPartSubtype.MapPiece
    MODEL_SUBTYPES = ["map_piece_models"]
    MODEL_USES_OLDEST_MAP_VERSION = True

    __slots__ = []

    # No additional Map Piece properties.

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
                force_bone_data_type=FLVERBoneDataType.POSE,
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
        """Create a fully-represented MSB Part linked to a source model in Blender.

        Map Piece creates Armature parent if needed before setting transform, so that it can be redirected to the new
        Armature if present.
        """
        model = cls.model_ref_to_bl_obj(
            operator, context, soulstruct_obj, map_stem, try_import_model, model_collection
        )
        model_mesh = model.data if model else bpy.data.meshes.new(name)
        bl_part = cls.new(name, model_mesh, collection)  # type: tp.Self
        bl_part.model = model
        bl_part.draw_groups = soulstruct_obj.draw_groups
        bl_part.display_groups = soulstruct_obj.display_groups
        for prop_name in cls.AUTO_PART_PROPS:
            setattr(bl_part, prop_name, getattr(soulstruct_obj, prop_name))

        # Create a duplicated parent Armature for the Part if present, so Map Piece static posing is visible.
        if model and not model.get("MSB_MODEL_PLACEHOLDER", False):
            # This will return `None` if the FLVER has no Armature (default, most Map Pieces).
            if armature_obj := bl_part.duplicate_flver_model_armature(context, create_default_armature=False):
                # Rename Armature (obj and data) to match Part name.
                armature_obj.name = armature_obj.data.name = f"{name} Armature"

        # Now we can set the Blender transform, which will go to the Armature if present.
        bl_part.set_bl_obj_transform(soulstruct_obj)

        return bl_part

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
                try:
                    model_path = settings.get_import_map_file_path(f"{model_name}.flver", map_stem=map_stem)
                except FileNotFoundError:
                    pass  # handled later with placeholder model
                else:
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
            part_subtype_title=cls.PART_SUBTYPE.get_nice_name(),
            flver_source_binders=None,
            image_import_callback=image_import_callback,
        )
