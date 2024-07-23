from __future__ import annotations

__all__ = [
    "BLENDER_MSB_PART_TYPES",
    "MSBPartOperatorConfig",
]

import typing as tp
from dataclasses import dataclass

from io_soulstruct.msb import darksouls1ptde, darksouls1r
from soulstruct.games import *
from .properties import MSBPartSubtype, MSBRegionSubtype


BLENDER_MSB_PART_TYPES = {
    DARK_SOULS_PTDE: {
        MSBPartSubtype.MAP_PIECE: darksouls1ptde.BlenderMSBMapPiece,
        MSBPartSubtype.OBJECT: darksouls1ptde.BlenderMSBObject,
        MSBPartSubtype.CHARACTER: darksouls1ptde.BlenderMSBCharacter,
        MSBPartSubtype.PLAYER_START: darksouls1ptde.BlenderMSBPlayerStart,
        MSBPartSubtype.COLLISION: darksouls1ptde.BlenderMSBCollision,
        MSBPartSubtype.NAVMESH: darksouls1ptde.BlenderMSBNavmesh,
        MSBPartSubtype.CONNECT_COLLISION: darksouls1ptde.BlenderMSBConnectCollision,
    },
    DARK_SOULS_DSR: {
        MSBPartSubtype.MAP_PIECE: darksouls1r.BlenderMSBMapPiece,
        MSBPartSubtype.OBJECT: darksouls1r.BlenderMSBObject,
        MSBPartSubtype.CHARACTER: darksouls1r.BlenderMSBCharacter,
        MSBPartSubtype.PLAYER_START: darksouls1r.BlenderMSBPlayerStart,
        MSBPartSubtype.COLLISION: darksouls1r.BlenderMSBCollision,
        MSBPartSubtype.NAVMESH: darksouls1r.BlenderMSBNavmesh,
        MSBPartSubtype.CONNECT_COLLISION: darksouls1r.BlenderMSBConnectCollision,
    },
}


@dataclass(slots=True)
class MSBPartOperatorConfig:
    """Configuration for MSB Part import operators."""

    PART_SUBTYPE: MSBPartSubtype
    MSB_LIST_NAME: str
    MSB_MODEL_LIST_NAME: str
    GAME_ENUM_NAME: str | None
    USE_LATEST_MAP_FOLDER: bool = False

    def get_bl_part_type(self, game: Game) -> tp.Type[darksouls1ptde.BlenderMSBPart]:
        return BLENDER_MSB_PART_TYPES[game][self.PART_SUBTYPE]


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
