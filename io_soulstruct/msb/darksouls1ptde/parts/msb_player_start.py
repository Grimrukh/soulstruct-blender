from __future__ import annotations

__all__ = [
    "BlenderMSBPlayerStart",
]

import traceback

import bpy
from io_soulstruct.exceptions import FLVERImportError, MissingPartModelError
from io_soulstruct.flver.image.image_import_manager import ImageImportManager
from io_soulstruct.flver.models import BlenderFLVER
from io_soulstruct.flver.utilities import get_flvers_from_binder
from io_soulstruct.msb.properties import MSBPartSubtype, MSBPlayerStartProps
from io_soulstruct.msb.utilities import find_flver_model, batch_import_flver_models
from io_soulstruct.types import *
from io_soulstruct.utilities import LoggingOperator, get_or_create_collection
from soulstruct.containers import Binder
from soulstruct.darksouls1ptde.maps.models import MSBCharacterModel
from soulstruct.darksouls1ptde.maps.parts import MSBPlayerStart
from .msb_part import BlenderMSBPart


class BlenderMSBPlayerStart(BlenderMSBPart[MSBPlayerStart, MSBPlayerStartProps]):
    """Always references 'c0000', but we don't assume anything here, and import that FLVER as required."""

    OBJ_DATA_TYPE = SoulstructDataType.MESH
    SOULSTRUCT_CLASS = MSBPlayerStart
    SOULSTRUCT_MODEL_CLASS = MSBCharacterModel  # or `MSBPlayerStartModel` but we don't need that here
    PART_SUBTYPE = MSBPartSubtype.PLAYER_START
    MODEL_SUBTYPES = ["player_models", "character_models"]

    __slots__ = []

    # No additional Player Start properties.

    @property
    def armature(self) -> bpy.types.ArmatureObject | None:
        """Detect parent Armature of wrapped Mesh object. Rarely present for Parts."""
        if self.obj.parent and self.obj.parent.type == "ARMATURE":
            # noinspection PyTypeChecker
            return self.obj.parent
        return None

    @classmethod
    def find_model_mesh(cls, model_name: str, map_stem="") -> bpy.types.MeshObject:
        return find_flver_model(model_name).mesh

    @classmethod
    def import_model_mesh(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_name: str,
        map_stem: str,
    ) -> bpy.types.MeshObject:
        settings = operator.settings(context)
        import_settings = context.scene.flver_import_settings
        chrbnd_path = settings.get_import_file_path(f"chr/{model_name}.chrbnd")

        operator.info(f"Importing Player Start (character) FLVER from: {chrbnd_path.name}")

        image_import_manager = ImageImportManager(operator, context) if import_settings.import_textures else None

        chrbnd = Binder.from_path(chrbnd_path)
        binder_flvers = get_flvers_from_binder(chrbnd, chrbnd_path, allow_multiple=False)
        if image_import_manager:
            image_import_manager.find_flver_textures(chrbnd_path, chrbnd)
        flver = binder_flvers[0]

        try:
            bl_flver = BlenderFLVER.new_from_soulstruct_obj(
                operator,
                context,
                flver,
                model_name,
                image_import_manager,
                collection=get_or_create_collection(context.scene.collection, "Character Models"),
            )
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            raise FLVERImportError(f"Cannot import FLVER from CHRBND: {chrbnd_path.name}. Error: {ex}")

        return bl_flver.mesh

    @classmethod
    def batch_import_models(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        parts: list[MSBPlayerStart],
        map_stem: str,
    ):
        """Import all models for a batch of MSB Parts, as needed, in parallel as much as possible."""
        settings = operator.settings(context)
        model_datas = {}
        model_chrbnds = {}
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
                chrbnd_path = settings.get_import_file_path(f"chr/{model_name}.chrbnd")
                chrbnd = Binder.from_path(chrbnd_path)
                flver_entries = chrbnd.find_entries_matching_name(r".*\.flver(\.dcx)?")
                if not flver_entries:
                    raise FLVERImportError(f"Cannot find a FLVER file in CHRBND {chrbnd_path}.")
                model_datas[model_name] = flver_entries[0]
                model_chrbnds[model_name] = chrbnd

        batch_import_flver_models(
            operator,
            context,
            model_datas,
            map_stem,
            cls.PART_SUBTYPE.get_nice_name(),
            flver_source_binders=model_chrbnds,
        )

    # No other overrides needed.
