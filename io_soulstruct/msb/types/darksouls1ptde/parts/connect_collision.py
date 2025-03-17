from __future__ import annotations

__all__ = [
    "BlenderMSBConnectCollision",
]

from soulstruct.darksouls1ptde.maps.models import MSBCollisionModel
from soulstruct.darksouls1ptde.maps.parts import MSBConnectCollision

from io_soulstruct.msb.types.adapters import *
from io_soulstruct.msb.properties import BlenderMSBPartSubtype, MSBConnectCollisionProps
from io_soulstruct.types import SoulstructType

from .base import BaseBlenderMSBPart_DS1


@soulstruct_adapter
class BlenderMSBConnectCollision(BaseBlenderMSBPart_DS1[MSBConnectCollision, MSBConnectCollisionProps]):

    SOULSTRUCT_CLASS = MSBConnectCollision
    MSB_ENTRY_SUBTYPE = BlenderMSBPartSubtype.ConnectCollision
    _MODEL_ADAPTER = MSBPartModelAdapter(SoulstructType.COLLISION, MSBCollisionModel)

    __slots__ = []

    SUBTYPE_FIELDS = (
        MSBReferenceFieldAdapter("collision", ref_type=SoulstructType.MSB_PART, ref_subtype="collisions"),  # subtype
        FieldAdapter("connected_map_id"),  # stored as four ints in Blender properties
    )
