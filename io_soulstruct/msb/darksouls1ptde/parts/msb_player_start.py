from __future__ import annotations

__all__ = [
    "BlenderMSBPlayerStart",
]

import bpy
from io_soulstruct.exceptions import FLVERImportError, MissingPartModelError
from io_soulstruct.msb.properties import MSBPartSubtype, MSBPlayerStartProps
from io_soulstruct.msb.utilities import find_flver_model, batch_import_flver_models
from io_soulstruct.types import *
from io_soulstruct.utilities import LoggingOperator
from soulstruct.containers import Binder
from soulstruct.darksouls1ptde.maps.models import MSBCharacterModel
from soulstruct.darksouls1ptde.maps.parts import MSBPlayerStart
from .msb_part import BlenderMSBPart
from .msb_character import BlenderMSBCharacter


class BlenderMSBPlayerStart(BlenderMSBPart[MSBPlayerStart, MSBPlayerStartProps]):
    """Always references model 'c0000', but we don't assume anything here, and import that FLVER as required."""

    SOULSTRUCT_CLASS = MSBPlayerStart
    SOULSTRUCT_MODEL_CLASS = MSBCharacterModel  # or `MSBPlayerStartModel` but we don't need that here
    BLENDER_MODEL_TYPE = SoulstructType.FLVER
    PART_SUBTYPE = MSBPartSubtype.PlayerStart
    MODEL_SUBTYPES = ["player_models", "character_models"]

    __slots__ = []

    # No additional Player Start properties.

    @classmethod
    def find_model_mesh(cls, model_name: str, map_stem="") -> bpy.types.MeshObject:
        return find_flver_model(model_name).mesh

    @classmethod
    def import_model_mesh(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_name: str,
        map_stem: str = "",  # not used
        model_collection: bpy.types.Collection = None,
    ) -> bpy.types.MeshObject:
        return BlenderMSBCharacter.import_model_mesh(operator, context, model_name, map_stem, model_collection)

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

        if not model_datas:
            operator.info("No Player Start (Character) FLVER models to import.")
            return  # nothing to import

        batch_import_flver_models(
            operator,
            context,
            model_datas,
            map_stem,
            cls.PART_SUBTYPE.get_nice_name(),
            flver_source_binders=model_chrbnds,
        )

    # No other overrides needed.
