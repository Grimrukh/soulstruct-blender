"""Import MSB Regions of any shape as Blender Empty objects, with custom shape properties and a custom draw tool.

Much simpler than MSB Part import, obviously, aside from the custom draw logic.
"""
from __future__ import annotations

__all__ = [
    "RegionImportError",
    "ImportMSBPoint",
    "ImportMSBVolume",
    "ImportAllMSBPoints",
    "ImportAllMSBVolumes",
]

import time
import traceback
import typing as tp

import bpy

from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.utilities import *
from io_soulstruct.utilities.conversion import Transform
from io_soulstruct.utilities.operators import LoggingOperator

if tp.TYPE_CHECKING:
    from soulstruct.darksouls1r.maps.regions import *  # TODO: use multi-game typing
    from io_soulstruct.type_checking import MSB_TYPING
    from .settings import *


class RegionImportError(Exception):
    pass


def create_region_empty(msb_region: MSBRegion) -> bpy.types.Object:

    # Create an Empty representing the region.
    region = bpy.data.objects.new(msb_region.name, None)

    transform = Transform.from_msb_entry(msb_region)
    region.location = transform.bl_translate
    region.rotation_euler = transform.bl_rotate
    # No scale for regions.
    region["Entity ID"] = msb_region.entity_id

    # Set custom properties. This will depend on the shape type.
    # TODO: I want to overhaul all game `MSBRegion` classes to use `RegionShape` components, which will make this a bit
    #  easier (rather than relying on subclass name).
    # TODO: Obviously, it would be nice/smart to use Blender scale for the radius/size of the region. This is only
    #  complicated for Cylinders, really, which need to enforce equal X and Y (radius) but allow different Z (height).
    #  The draw tool can make it clear that only X *or* Y is used for Cylinders though (e.g. whichever is larger).
    # TODO: Create an EnumProperty for custom Region Type property?
    region_type_name = msb_region.__class__.__name__
    if "Point" in region_type_name:
        msb_region: MSBRegionPoint
        region.region_shape = "Point"
        region.empty_display_type = "SPHERE"  # best for points
        # No scale needed.
    elif "Sphere" in region_type_name:
        msb_region: MSBRegionSphere
        region.region_shape = "Sphere"
        region.scale = (msb_region.radius, msb_region.radius, msb_region.radius)
        region.empty_display_type = "SPHERE"  # makes these regions much easier to click
    elif "Cylinder" in region_type_name:
        msb_region: MSBRegionCylinder
        region.region_shape = "Cylinder"
        region.scale = (msb_region.radius, msb_region.radius, msb_region.height)
        region.empty_display_type = "PLAIN_AXES"  # no great choice for cylinders but this is probably best
    elif "Box" in region_type_name:
        msb_region: MSBRegionBox
        region.region_shape = "Box"
        region.scale = (msb_region.width, msb_region.depth, msb_region.height)
        region.empty_display_type = "CUBE"  # makes these regions much easier to click
    else:
        raise RegionImportError(f"Cannot import MSB region type/shape: {region_type_name}")

    return region


class BaseImportMSBRegion(LoggingOperator):

    REGION_TYPE_NAME: str  # e.g. 'Volume'
    REGION_TYPE_NAME_PLURAL: str  # e.g. 'Volumes'
    MSB_LIST_NAMES: list[str]  # e.g. ['spheres', 'cylinders', 'boxes']
    GAME_ENUM_NAME: str | None  # e.g. 'point_region' or 'volume_region' or `None` for all-region importers

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)
        msb_path = settings.get_import_msb_path()
        if not is_path_and_file(msb_path):
            return False
        if cls.GAME_ENUM_NAME is not None:
            region = getattr(context.scene.soulstruct_game_enums, cls.GAME_ENUM_NAME)
            if region in {"", "0"}:
                return False  # no enum option selected
        return True  # MSB exists and a region name is selected from enum

    def import_enum_region(self, context):

        region_name = getattr(context.scene.soulstruct_game_enums, self.GAME_ENUM_NAME)
        if region_name in {"", "0"}:
            return self.error(f"Invalid MSB {self.REGION_TYPE_NAME} selection: {region_name}")

        settings = self.settings(context)
        settings.save_settings()
        msb_import_settings = context.scene.msb_import_settings  # type: MSBImportSettings

        if not settings.get_import_map_path():  # validation
            return self.error("Game directory and map stem must be set in Blender's Soulstruct global settings.")

        # We always use the latest MSB, if the setting is enabled.
        msb_stem = settings.get_latest_map_stem_version()
        msb_path = settings.get_import_msb_path()  # will automatically use latest MSB version if known and enabled
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING
        collection_name = msb_import_settings.get_collection_name(msb_stem, self.REGION_TYPE_NAME_PLURAL)
        region_collection = get_collection(collection_name, context.scene.collection)  # does NOT hide in viewport

        # Get MSB region.
        region_list = getattr(msb, self.MSB_LIST_NAMES[0])
        try:
            region = region_list.find_entry_name(region_name)
        except KeyError:
            return self.error(f"MSB {self.REGION_TYPE_NAME} '{region_name}' not found in MSB.")

        try:
            # NOTE: Instance creator may not always use `map_stem` (e.g. characters).
            region_empty = create_region_empty(region)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Failed to import MSB {self.REGION_TYPE_NAME} region '{region.name}': {ex}")
        region_collection.objects.link(region_empty)

        # Select and frame view on new instance.
        self.set_active_obj(region_empty)
        bpy.ops.view3d.view_selected(use_all_regions=False)

        return {"FINISHED"}

    def import_all_regions(self, context):

        start_time = time.perf_counter()

        settings = self.settings(context)
        settings.save_settings()

        if not settings.get_import_map_path():  # validation
            return self.error("Game directory and map stem must be set in Blender's Soulstruct global settings.")

        msb_import_settings = context.scene.msb_import_settings  # type: MSBImportSettings
        is_name_match = msb_import_settings.get_name_match_filter()
        msb_stem = settings.get_latest_map_stem_version()
        msb_path = settings.get_import_msb_path()  # will automatically use latest MSB version if known and enabled
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING
        collection_name = msb_import_settings.get_collection_name(msb_stem, self.REGION_TYPE_NAME_PLURAL)
        region_collection = get_collection(collection_name, context.scene.collection)

        combined_region_list = []
        for region_list in [getattr(msb, name) for name in self.MSB_LIST_NAMES]:
            combined_region_list.extend(region_list)
        region_count = 0

        for region in [region for region in combined_region_list if is_name_match(region.name)]:
            try:
                region_empty = create_region_empty(region)
            except Exception as ex:
                traceback.print_exc()
                self.error(f"Failed to import MSB {self.REGION_TYPE_NAME} region '{region.name}': {ex}")
                continue
            region_collection.objects.link(region_empty)
            region_count += 1

        if region_count == 0:
            self.warning(
                f"No MSB {self.REGION_TYPE_NAME} regions found with {msb_import_settings.entry_name_match_mode} filter: "
                f"'{msb_import_settings.entry_name_match}'"
            )
            return {"CANCELLED"}

        self.info(
            f"Imported {region_count} / {len(combined_region_list)} MSB {self.REGION_TYPE_NAME} regions in "
            f"{time.perf_counter() - start_time:.3f} seconds (filter: '{msb_import_settings.entry_name_match}')."
        )

        # No change in view after importing all regions.

        return {"FINISHED"}


class ImportMSBPoint(BaseImportMSBRegion):
    bl_idname = "import_scene.msb_point_region"
    bl_label = "Import Point Region"
    bl_description = "Import MSB transform of selected MSB Point region"

    REGION_TYPE_NAME = "Point"
    REGION_TYPE_NAME_PLURAL = "Points"
    MSB_LIST_NAMES = ["points"]
    GAME_ENUM_NAME = "point_region"

    def execute(self, context):
        return self.import_enum_region(context)


class ImportMSBVolume(BaseImportMSBRegion):
    bl_idname = "import_scene.msb_volume_region"
    bl_label = "Import Volume Region"
    bl_description = "Import MSB transform and shape of selected MSB Volume region"

    REGION_TYPE_NAME = "Volume"
    REGION_TYPE_NAME_PLURAL = "Volumes"
    MSB_LIST_NAMES = ["spheres", "cylinders", "boxes"]
    GAME_ENUM_NAME = "volume_region"

    def execute(self, context):
        return self.import_enum_region(context)


class ImportAllMSBPoints(BaseImportMSBRegion):
    bl_idname = "import_scene.all_msb_point_regions"
    bl_label = "Import All Point Regions"
    bl_description = "Import MSB transform of every MSB Point region"

    REGION_TYPE_NAME = "Point"
    REGION_TYPE_NAME_PLURAL = "Points"
    MSB_LIST_NAMES = ["points"]
    GAME_ENUM_NAME = None

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        return self.import_all_regions(context)


class ImportAllMSBVolumes(BaseImportMSBRegion):
    bl_idname = "import_scene.all_msb_volume_regions"
    bl_label = "Import All Volume Regions"
    bl_description = "Import MSB transform and shape of every MSB Volume region"

    REGION_TYPE_NAME = "Volume"
    REGION_TYPE_NAME_PLURAL = "Volumes"
    MSB_LIST_NAMES = ["spheres", "cylinders", "boxes"]
    GAME_ENUM_NAME = None

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        return self.import_all_regions(context)
