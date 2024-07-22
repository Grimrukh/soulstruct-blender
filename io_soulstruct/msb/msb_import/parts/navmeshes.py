"""Operators for importing `MSBNavmesh` entries, and their NVM models, from MSB files."""
from __future__ import annotations

__all__ = [
    "ImportMSBNavmesh",
    "ImportAllMSBNavmeshes",
]

from io_soulstruct.msb.properties import MSBPartSubtype
from .core import *


msb_navmesh_operator_config = MSBPartOperatorConfig(
    PART_SUBTYPE=MSBPartSubtype.NAVMESH,
    MSB_LIST_NAME="navmeshes",
    GAME_ENUM_NAME="navmesh_part",
    USE_LATEST_MAP_FOLDER=True,
)


class ImportMSBNavmesh(BaseImportSingleMSBPart):
    """Import a NVM from the current selected value of listed game MSB navmesh entries."""
    bl_idname = "import_scene.msb_navmesh_part"
    bl_label = "Import Navmesh Part"
    bl_description = "Import transform and model of selected Navmesh MSB part from selected game map"

    config = msb_navmesh_operator_config


class ImportAllMSBNavmeshes(BaseImportAllMSBParts):
    """Import a NVM from the current selected value of listed game MSB navmesh entries."""
    bl_idname = "import_scene.all_msb_navmesh_parts"
    bl_label = "Import All Navmesh Parts"
    bl_description = "Import NVM mesh and MSB transform of every MSB Navmesh part. Still quite fast"

    config = msb_navmesh_operator_config
