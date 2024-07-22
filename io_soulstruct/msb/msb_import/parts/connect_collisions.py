"""Operators for importing `MSBCollision` entries, and their HKX models, from MSB files."""
from __future__ import annotations

__all__ = [
    "ImportMSBConnectCollision",
    "ImportAllMSBConnectCollisions",
]

from io_soulstruct.msb.properties import MSBPartSubtype
from .core import *


msb_connect_collision_operator_config = MSBPartOperatorConfig(
    PART_SUBTYPE=MSBPartSubtype.CONNECT_COLLISION,
    MSB_LIST_NAME="collisions",
    GAME_ENUM_NAME="collision_part",
)


class ImportMSBConnectCollision(BaseImportSingleMSBPart):
    bl_idname = "import_scene.msb_connect_collision"
    bl_label = "Import MSB Connect Collision Part"
    bl_description = "Import selected MSB Connect Collision entry from selected game MSB"

    config = msb_connect_collision_operator_config


class ImportAllMSBConnectCollisions(BaseImportAllMSBParts):
    bl_idname = "import_scene.all_msb_connect_collisions"
    bl_label = "Import All Connect Collision Parts"
    bl_description = "Import HKX meshes and MSB transform of every MSB Connect Collision part. Moderately slow"

    config = msb_connect_collision_operator_config
