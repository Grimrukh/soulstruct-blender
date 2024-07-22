from __future__ import annotations

__all__ = [
    "BlenderMSBCharacter",
]

import traceback
import typing as tp

import bpy
from io_soulstruct.exceptions import FLVERImportError
from io_soulstruct.flver.model_import.core import FLVERImporter
from io_soulstruct.flver.model_import.settings import FLVERImportSettings
from io_soulstruct.flver.textures.import_textures import TextureImportManager
from io_soulstruct.flver.types import BlenderFLVER
from io_soulstruct.flver.utilities import get_flvers_from_binder
from io_soulstruct.general.core import SoulstructSettings
from io_soulstruct.msb.properties import MSBPartSubtype, MSBCharacterProps
from io_soulstruct.msb.utilities import find_flver_model
from io_soulstruct.utilities import LoggingOperator, get_collection, find_obj_or_create_empty
from soulstruct.containers import Binder
from soulstruct.darksouls1ptde.maps.parts import MSBCharacter, MSBDummyCharacter
from .base import BlenderMSBPart

if tp.TYPE_CHECKING:
    from io_soulstruct.type_checking import *


class BlenderMSBCharacter(BlenderMSBPart):

    PART_SUBTYPE = MSBPartSubtype.CHARACTER

    @property
    def character_props(self) -> MSBCharacterProps:
        return self.obj.msb_character_props

    @classmethod
    def find_model(cls, model_name: str, map_stem: str):
        return find_flver_model(cls.PART_SUBTYPE, model_name)

    @classmethod
    def import_model(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        model_name: str,
        map_stem="",  # not used
    ) -> BlenderFLVER:
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

    def set_properties(self, operator: LoggingOperator, part: MSB_CHARACTER_TYPING):
        super().set_properties(operator, part)
        if not isinstance(part, MSBCharacter):  # `MSBDummyCharacter` is a subclass of `MSBCharacter` in DS1
            return

        props = self.character_props

        if part.draw_parent:
            was_missing, props.draw_parent = find_obj_or_create_empty(part.draw_parent.name)
            if was_missing:
                operator.warning(
                    f"Draw parent '{part.draw_parent.name}' not found in scene. Creating empty object with that name "
                    f"in Scene Collection to use as draw parent for '{part.name}'."
                )

        for i, region in enumerate(part.patrol_regions):
            if not region:
                continue  # leave slot `i` as `None`
            prop_name = f"patrol_regions_{i}"
            was_missing, region_obj = find_obj_or_create_empty(region.name)
            if was_missing:
                operator.warning(
                    f"Patrol region '{region.name}' not found in scene. Creating empty object with that name "
                    f"in Scene Collection to use as patrol region {i} for '{part.name}'."
                )
            setattr(props, prop_name, region_obj)

        for prop_name in props.__annotations__:
            if prop_name == "is_dummy":
                setattr(props, prop_name, isinstance(part, MSBDummyCharacter))
                continue
            if prop_name == "draw_parent" or prop_name.startswith("patrol_regions_"):
                continue  # handled above
            # Primitive property.
            setattr(props, prop_name, getattr(part, prop_name))
