from __future__ import annotations

__all__ = [
    "SoulstructType",
]

from soulstruct.utilities.future import StrEnum


class SoulstructType(StrEnum):
    NONE = "None"
    FLVER = "FLVER"
    DUMMY = "DUMMY"
    COLLISION = "COLLISION"
    NAVMESH = "NAVMESH"
    MCG_NODE = "MCG_NODE"
    MCG_EDGE = "MCG_EDGE"
    MSB_PART = "MSB_PART"
    MSB_REGION = "MSB_REGION"
    MSB_EVENT = "MSB_EVENT"
