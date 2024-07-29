"""Import MSB Regions of any shape as Blender Empty objects, with custom shape properties and a custom draw tool.

Much simpler than MSB Part import, obviously, aside from the custom draw logic.
"""
from __future__ import annotations

__all__ = [
    "BaseImportSingleMSBRegion",
    "BaseImportAllMSBRegions",
]

import time
import traceback
import typing as tp

import bpy
from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.msb.operator_config import MSBRegionOperatorConfig
from io_soulstruct.msb.utilities import BaseMSBEntrySelectOperator
from io_soulstruct.utilities import *
from io_soulstruct.utilities.operators import LoggingOperator

if tp.TYPE_CHECKING:
    from io_soulstruct.type_checking import MSB_TYPING
    from soulstruct.darksouls1ptde.maps.regions import MSBRegion


class BaseImportSingleMSBRegion(BaseMSBEntrySelectOperator):

    config: tp.ClassVar[MSBRegionOperatorConfig]

    @classmethod
    def get_msb_list_names(cls, context) -> list[str]:
        return cls.config.MSB_LIST_NAMES

    @classmethod
    def poll(cls, context):
        if not super().poll(context):
            return False

        settings = cls.settings(context)
        try:
            cls.config.get_bl_region_type(settings.game)
        except KeyError:
            return False
        return True

    def _import_entry(self, context, entry: MSBRegion):

        settings = self.settings(context)
        msb_import_settings = context.scene.msb_import_settings

        try:
            bl_region_type = self.config.get_bl_region_type(settings.game)
        except KeyError:
            return self.error(
                f"Cannot import MSB Region subtype `{self.config.REGION_SUBTYPE}` for game {settings.game.name}."
            )

        # We always use the latest MSB, if the setting is enabled.
        msb_stem = settings.get_latest_map_stem_version()
        collection_name = msb_import_settings.get_collection_name(msb_stem, self.config.COLLECTION_NAME)
        region_collection = get_collection(collection_name, context.scene.collection)  # does NOT hide in viewport

        try:
            bl_region = bl_region_type.new_from_soulstruct_obj(
                self, context, entry, entry.name, region_collection
            )
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Failed to import MSB {self.config.REGION_SUBTYPE} region '{entry.name}': {ex}")

        # Select and frame view on new instance.
        self.set_active_obj(bl_region.obj)
        bpy.ops.view3d.view_selected(use_all_regions=False)

        return {"FINISHED"}


class BaseImportAllMSBRegions(LoggingOperator):

    config: tp.ClassVar[MSBRegionOperatorConfig]

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)
        try:
            settings.get_import_msb_path()
        except FileNotFoundError:
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

        msb_import_settings = context.scene.msb_import_settings
        is_name_match = msb_import_settings.get_name_match_filter()
        msb_stem = settings.get_latest_map_stem_version()
        msb_path = settings.get_import_msb_path()  # will automatically use latest MSB version if known and enabled
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING
        collection_name = msb_import_settings.get_collection_name(msb_stem, self.config.COLLECTION_NAME)
        region_collection = get_collection(collection_name, context.scene.collection)

        combined_region_list = []
        for region_list in [getattr(msb, name) for name in self.config.MSB_LIST_NAMES]:
            combined_region_list.extend(region_list)
        region_count = 0

        for region in [region for region in combined_region_list if is_name_match(region.name)]:
            try:
                # Don't need to get created object.
                bl_region_type.new_from_soulstruct_obj(
                    self, context, region, region.name, region_collection)
            except Exception as ex:
                traceback.print_exc()
                self.error(f"Failed to import MSB {self.config.REGION_SUBTYPE} region '{region.name}': {ex}")
                continue
            region_count += 1

        if region_count == 0:
            self.warning(
                f"No MSB {self.config.REGION_SUBTYPE} regions found with {msb_import_settings.entry_name_match_mode} "
                f"filter: '{msb_import_settings.entry_name_match}'"
            )
            return {"CANCELLED"}

        self.info(
            f"Imported {region_count} / {len(combined_region_list)} MSB {self.config.REGION_SUBTYPE} regions in "
            f"{time.perf_counter() - start_time:.3f} seconds (filter: '{msb_import_settings.entry_name_match}')."
        )

        # No change in view after importing all regions.

        return {"FINISHED"}


# TODO: Exporter. Can be shared by Point/Volume region shapes.
