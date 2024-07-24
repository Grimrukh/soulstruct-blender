from __future__ import annotations

__all__ = [
    "ImportMSBPoint",
    "ImportAllMSBPoints",
]

from io_soulstruct.msb.operator_config import MSBRegionOperatorConfig
from io_soulstruct.msb.properties import MSBRegionSubtype
from .base import *


msb_point_operator_config = MSBRegionOperatorConfig(
    REGION_SUBTYPE=MSBRegionSubtype.NA,
    MSB_LIST_NAMES=["points"],
    GAME_ENUM_NAME="point_region",
)


class ImportMSBPoint(BaseImportSingleMSBRegion):
    bl_idname = "import_scene.msb_point_region"
    bl_label = "Import Point Region"
    bl_description = "Import MSB transform of selected MSB Point region"

    config = msb_point_operator_config


class ImportAllMSBPoints(BaseImportAllMSBRegions):
    bl_idname = "import_scene.all_msb_point_regions"
    bl_label = "Import All Point Regions"
    bl_description = "Import MSB transform of every MSB Point region"

    config = msb_point_operator_config
