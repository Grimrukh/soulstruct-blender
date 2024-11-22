from __future__ import annotations

__all__ = [
    "BlenderMSBProtoboss",
]

import typing as tp

import bpy
from io_soulstruct.exceptions import FLVERImportError, MissingPartModelError
from io_soulstruct.msb.properties import MSBPartSubtype, MSBProtobossProps
from io_soulstruct.msb.utilities import find_flver_model, batch_import_flver_models
from io_soulstruct.types import *
from io_soulstruct.utilities import LoggingOperator
from soulstruct.containers import Binder
from soulstruct.demonssouls.maps.models import MSBCharacterModel
from soulstruct.demonssouls.maps.parts import MSBProtoboss
from .msb_part import BlenderMSBPart
from .msb_character import BlenderMSBCharacter

if tp.TYPE_CHECKING:
    from soulstruct.demonssouls.maps.msb import MSB


class BlenderMSBProtoboss(BlenderMSBPart[MSBProtoboss, MSBProtobossProps]):

    SOULSTRUCT_CLASS = MSBProtoboss
    SOULSTRUCT_MODEL_CLASS = MSBCharacterModel
    BLENDER_MODEL_TYPE = SoulstructType.FLVER
    PART_SUBTYPE = MSBPartSubtype.Character
    MODEL_SUBTYPES = ["character_models"]

    __slots__ = []

    AUTO_PROTOBOSS_PROPS = [
        "unk_x00",
        "unk_x04",
        "unk_x08",
        "unk_x0c",
        "unk_x10",
        "unk_x14",
        "unk_x18",
        "unk_x1c",
        "unk_x20",
        "unk_x24",
        "unk_x28",
        "unk_x2c",
        "unk_x30",
    ]

    unk_x00: float
    unk_x04: float
    unk_x08: float
    unk_x0c: float
    unk_x10: int
    unk_x14: int
    unk_x18: float
    unk_x1c: float
    unk_x20: int
    unk_x24: int
    unk_x28: float
    unk_x2c: int
    unk_x30: int

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBProtoboss,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
        try_import_model=True,
        model_collection: bpy.types.Collection = None,
    ) -> tp.Self:
        bl_character = super().new_from_soulstruct_obj(
            operator, context, soulstruct_obj, name, collection, map_stem, try_import_model, model_collection
        )

        for name in cls.AUTO_PROTOBOSS_PROPS:
            setattr(bl_character, name, getattr(soulstruct_obj, name))

        return bl_character

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> MSBProtoboss:
        msb_protoboss = super().to_soulstruct_obj(operator, context, map_stem, msb)  # type: MSBProtoboss

        for name in self.AUTO_PROTOBOSS_PROPS:
            setattr(msb_protoboss, name, getattr(self, name))

        return msb_protoboss

    @classmethod
    def find_model_mesh(cls, model_name: str, map_stem="") -> bpy.types.MeshObject:
        return find_flver_model(model_name).mesh

    @classmethod
    def import_model_mesh(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_name: str,
        map_stem="",  # not used
        model_collection: bpy.types.Collection = None,
    ) -> bpy.types.MeshObject:
        """Import the model of the given name into a collection in the current scene."""
        return BlenderMSBCharacter.import_model_mesh(operator, context, model_name, map_stem, model_collection)

    @classmethod
    def batch_import_models(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        parts: list[MSBProtoboss],
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
            operator.info("No Character FLVER models to import.")
            return  # nothing to import

        batch_import_flver_models(
            operator,
            context,
            model_datas,
            map_stem,
            cls.PART_SUBTYPE.get_nice_name(),
            flver_source_binders=model_chrbnds,
        )


BlenderMSBProtoboss.add_auto_subtype_props(*BlenderMSBProtoboss.AUTO_PROTOBOSS_PROPS)
