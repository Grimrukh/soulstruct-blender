"""Operators for importing `MSBCollision` entries, and their HKX models, from MSB files."""
from __future__ import annotations

__all__ = [
    "ImportMSBMapCollision",
    "ImportAllMSBMapCollisions",
]

from io_soulstruct.msb.properties import MSBPartSubtype
from .core import *


msb_collision_operator_config = MSBPartOperatorConfig(
    PART_SUBTYPE=MSBPartSubtype.COLLISION,
    MSB_LIST_NAME="collisions",
    GAME_ENUM_NAME="collision_part",
)


class ImportMSBMapCollision(BaseImportSingleMSBPart):
    bl_idname = "import_scene.msb_map_collision_part"
    bl_label = "Import MSB Collision Part"
    bl_description = "Import selected MSB Collision entry from selected game MSB"

    config = msb_collision_operator_config


class ImportAllMSBMapCollisions(BaseImportAllMSBParts):
    bl_idname = "import_scene.all_msb_map_collision_parts"
    bl_label = "Import All Collision Parts"
    bl_description = "Import HKX meshes and MSB transform of every MSB Collision part. Moderately slow"

    config = msb_collision_operator_config
