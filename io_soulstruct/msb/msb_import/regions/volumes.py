from __future__ import annotations

__all__ = [
    "ImportMSBVolume",
    "ImportAllMSBVolumes",
]

from io_soulstruct.msb.properties import MSBRegionSubtype
from .core import *


msb_volume_operator_config = MSBRegionOperatorConfig(
    REGION_SUBTYPE=MSBRegionSubtype.NA,
    MSB_LIST_NAMES=["spheres", "cylinders", "boxes"],
    GAME_ENUM_NAME="volume_region",
)


class ImportMSBVolume(BaseImportSingleMSBRegion):
    bl_idname = "import_scene.msb_volume_region"
    bl_label = "Import Volume Region"
    bl_description = "Import MSB transform and shape of selected MSB Volume region"

    config = msb_volume_operator_config


class ImportAllMSBVolumes(BaseImportAllMSBRegions):
    bl_idname = "import_scene.all_msb_volume_regions"
    bl_label = "Import All Volume Regions"
    bl_description = "Import MSB transform and shape of every MSB Volume region"

    config = msb_volume_operator_config
