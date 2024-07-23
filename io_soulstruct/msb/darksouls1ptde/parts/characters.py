from __future__ import annotations

__all__ = [
    "BlenderMSBCharacter",
]

import traceback
import typing as tp

import bpy
from io_soulstruct.exceptions import MSBPartExportError, MissingMSBEntryError, FLVERImportError
from io_soulstruct.flver.model_import.core import FLVERImporter
from io_soulstruct.flver.textures.import_textures import TextureImportManager
from io_soulstruct.flver.types import BlenderFLVER
from io_soulstruct.flver.utilities import get_flvers_from_binder
from io_soulstruct.general.core import SoulstructSettings
from io_soulstruct.msb.properties import MSBPartSubtype, MSBCharacterProps
from io_soulstruct.msb.utilities import find_flver_model
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import LoggingOperator, get_collection, find_obj_or_create_empty
from soulstruct.containers import Binder
from soulstruct.darksouls1ptde.maps.parts import MSBCharacter, MSBDummyCharacter
from .base import BlenderMSBPart

if tp.TYPE_CHECKING:
    from soulstruct.darksouls1ptde.maps.msb import MSB, MSBRegion


class BlenderMSBCharacter(BlenderMSBPart[MSBCharacter]):

    SOULSTRUCT_CLASS = MSBCharacter
    PART_SUBTYPE = MSBPartSubtype.CHARACTER
    MODEL_SUBTYPES = ["character_models"]

    @property
    def character_props(self) -> MSBCharacterProps:
        return self.obj.msb_character_props

    def set_obj_properties(self, operator: LoggingOperator, entry: MSBCharacter | MSBDummyCharacter):
        super().set_obj_properties(operator, entry)
        props = self.character_props

        self.set_obj_entry_reference(operator, props, "draw_parent", entry, SoulstructType.MSB_PART)

        for i, region in enumerate(entry.patrol_regions):
            if not region:
                continue  # leave slot `i` as `None`
            prop_name = f"patrol_regions_{i}"
            was_missing, region_obj = find_obj_or_create_empty(
                region.name,
                find_stem=True,
                soulstruct_type=SoulstructType.MSB_REGION,
            )
            if was_missing:
                operator.warning(
                    f"Patrol region '{region.name}' not found in scene. Creating empty object with that name "
                    f"in Scene Collection to use as patrol region {i} for '{entry.name}'."
                )
            setattr(props, prop_name, region_obj)

        if isinstance(entry, MSBDummyCharacter):
            props.is_dummy = True

        self.set_obj_generic_props(
            entry, props, skip_prefixes=("patrol_regions_",), skip_names={"draw_parent", "is_dummy"}
        )

    def set_entry_properties(self, operator: LoggingOperator, entry: MSBCharacter | MSBDummyCharacter, msb: MSB):
        super().set_entry_properties(operator, entry, msb)
        props = self.character_props

        if props.is_dummy and not isinstance(entry, MSBDummyCharacter):
            raise MSBPartExportError(
                f"Character '{entry.name}' is marked as a dummy, but is being exported as a non-dummy MSB Character."
            )
        elif not props.is_dummy and isinstance(entry, MSBDummyCharacter):
            raise MSBPartExportError(
                f"Character '{entry.name}' is not marked as a dummy, but is being exported as an MSB Dummy Character."
            )

        self.set_part_entry_reference(props.draw_parent, entry, "draw_parent", msb)

        for i in range(len(entry.patrol_regions)):
            prop_name = f"patrol_regions_{i}"
            region_obj = getattr(props, prop_name)
            if not region_obj:
                # Empty patrol region slot (fine).
                entry.patrol_regions[i] = None
            else:
                try:
                    # noinspection PyTypeChecker
                    region = msb.find_region_name(region_obj.name)  # type: MSBRegion
                except KeyError:
                    raise MissingMSBEntryError(f"Patrol region '{region_obj.name}' not found in MSB.")
                entry.patrol_regions[i] = region

        self.set_entry_generic_props(
            props, entry, skip_prefixes=("patrol_regions_",), skip_names={"draw_parent", "is_dummy"}
        )

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

        flver_import_settings = context.scene.flver_import_settings
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
