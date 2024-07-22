"""Import MSB Regions of any shape as Blender Empty objects, with custom shape properties and a custom draw tool.

Much simpler than MSB Part import, obviously, aside from the custom draw logic.
"""
from __future__ import annotations

__all__ = [
    "MSBRegionOperatorConfig",
    "BaseImportSingleMSBRegion",
    "BaseImportAllMSBRegions",
]

import time
import traceback
import typing as tp
from dataclasses import dataclass

import bpy
from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.msb import darksouls1ptde
from io_soulstruct.msb.properties import MSBRegionSubtype
from io_soulstruct.utilities import *
from io_soulstruct.utilities.operators import LoggingOperator
from soulstruct.games import *

if tp.TYPE_CHECKING:
    from io_soulstruct.type_checking import MSB_TYPING
    from ..settings import *


BLENDER_MSB_REGION_TYPES = {
    DARK_SOULS_PTDE: {
        # No subtypes, only shapes.
        MSBRegionSubtype.NA: darksouls1ptde.BlenderMSBRegion,
    },
    DARK_SOULS_DSR: {
        # No subtypes, only shapes.
        MSBRegionSubtype.NA: darksouls1ptde.BlenderMSBRegion,
    },
}


@dataclass(slots=True)
class MSBRegionOperatorConfig:
    """Configuration for MSB Region import operators."""

    REGION_SUBTYPE: MSBRegionSubtype
    MSB_LIST_NAMES: list[str]  # e.g. ['spheres', 'cylinders', 'boxes']
    GAME_ENUM_NAME: str | None  # e.g. 'point_region' or 'volume_region'

    def get_bl_region_type(self, game: Game) -> tp.Type[darksouls1ptde.BlenderMSBRegion]:
        return BLENDER_MSB_REGION_TYPES[game][self.REGION_SUBTYPE]


class BaseImportSingleMSBRegion(LoggingOperator):

    config: tp.ClassVar[MSBRegionOperatorConfig]

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)

        try:
            cls.config.get_bl_region_type(settings.game)
        except KeyError:
            return False

        msb_path = settings.get_import_msb_path()
        if not is_path_and_file(msb_path):
            return False
        region = getattr(context.scene.soulstruct_game_enums, cls.config.GAME_ENUM_NAME)
        if region in {"", "0"}:
            return False  # no enum option selected
        return True  # MSB exists and a region name is selected from enum

    def execute(self, context):

        settings = self.settings(context)

        try:
            bl_region_type = self.config.get_bl_region_type(settings.game)
        except KeyError:
            return self.error(
                f"Cannot import MSB Region subtype `{self.config.REGION_SUBTYPE}` for game {settings.game.name}."
            )

        msb_import_settings = context.scene.msb_import_settings  # type: MSBImportSettings

        if not settings.get_import_map_path():  # validation
            return self.error("Game directory and map stem must be set in Blender's Soulstruct global settings.")

        region_name = getattr(context.scene.soulstruct_game_enums, self.config.GAME_ENUM_NAME)
        if region_name in {"", "0"}:
            return self.error(f"Invalid MSB {self.config.REGION_SUBTYPE} selection: {region_name}")

        # We always use the latest MSB, if the setting is enabled.
        msb_stem = settings.get_latest_map_stem_version()
        msb_path = settings.get_import_msb_path()  # will automatically use latest MSB version if known and enabled
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING
        collection_name = msb_import_settings.get_collection_name(msb_stem, self.config.REGION_SUBTYPE)
        region_collection = get_collection(collection_name, context.scene.collection)  # does NOT hide in viewport

        # Get MSB region.
        region_lists = [getattr(msb, msb_list_name) for msb_list_name in self.config.MSB_LIST_NAMES]
        for region_list in region_lists:
            try:
                region = region_list.find_entry_name(region_name)
                break  # found
            except KeyError:
                continue
        else:
            return self.error(f"MSB {self.config.REGION_SUBTYPE} '{region_name}' not found in MSB.")

        try:
            bl_region = bl_region_type.new_from_region(self, region, region_collection)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Failed to import MSB {self.config.REGION_SUBTYPE} region '{region.name}': {ex}")

        # Select and frame view on new instance.
        self.set_active_obj(bl_region.obj)
        bpy.ops.view3d.view_selected(use_all_regions=False)

        return {"FINISHED"}


class BaseImportAllMSBRegions(LoggingOperator):

    config: tp.ClassVar[MSBRegionOperatorConfig]

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)
        msb_path = settings.get_import_msb_path()
        if not is_path_and_file(msb_path):
            return False
        return True  # MSB exists and a region name is selected from enum

    def execute(self, context):

        start_time = time.perf_counter()

        settings = self.settings(context)

        try:
            bl_region_type = self.config.get_bl_region_type(settings.game)
        except KeyError:
            return self.error(
                f"Cannot import MSB Region subtype `{self.config.REGION_SUBTYPE}` for game {settings.game.name}."
            )

        if not settings.get_import_map_path():  # validation
            return self.error("Game directory and map stem must be set in Blender's Soulstruct global settings.")

        msb_import_settings = context.scene.msb_import_settings  # type: MSBImportSettings
        is_name_match = msb_import_settings.get_name_match_filter()
        msb_stem = settings.get_latest_map_stem_version()
        msb_path = settings.get_import_msb_path()  # will automatically use latest MSB version if known and enabled
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING
        collection_name = msb_import_settings.get_collection_name(msb_stem, self.config.REGION_SUBTYPE)
        region_collection = get_collection(collection_name, context.scene.collection)

        combined_region_list = []
        for region_list in [getattr(msb, name) for name in self.config.MSB_LIST_NAMES]:
            combined_region_list.extend(region_list)
        region_count = 0

        for region in [region for region in combined_region_list if is_name_match(region.name)]:
            try:
                # Don't need to get created object.
                bl_region_type.new_from_region(self, region, region_collection)
            except Exception as ex:
                traceback.print_exc()
                self.error(f"Failed to import MSB {self.config.REGION_SUBTYPE} region '{region.name}': {ex}")
                continue
            region_count += 1

        if region_count == 0:
            self.warning(
                f"No MSB {self.config.REGION_SUBTYPE} regions found with {msb_import_settings.entry_name_match_mode} filter: "
                f"'{msb_import_settings.entry_name_match}'"
            )
            return {"CANCELLED"}

        self.info(
            f"Imported {region_count} / {len(combined_region_list)} MSB {self.config.REGION_SUBTYPE} regions in "
            f"{time.perf_counter() - start_time:.3f} seconds (filter: '{msb_import_settings.entry_name_match}')."
        )

        # No change in view after importing all regions.

        return {"FINISHED"}
