from __future__ import annotations

__all__ = [
    "BlenderMSBConnectCollision",
]

from soulstruct.darksouls1ptde.maps.msb import MSB, MSBConnectCollision, BitSet128
from soulstruct.darksouls1ptde.maps.models import MSBCollisionModel

from io_soulstruct.msb.types.adapters import *
from io_soulstruct.msb.properties import MSBPartSubtype, MSBPartProps, MSBConnectCollisionProps
from io_soulstruct.types import SoulstructType

from .base import BaseBlenderMSBPart_DS1


@create_msb_entry_field_adapter_properties
class BlenderMSBConnectCollision(
    BaseBlenderMSBPart_DS1[MSBConnectCollision, MSBPartProps, MSBConnectCollisionProps, MSB, BitSet128]
):

    SOULSTRUCT_CLASS = MSBConnectCollision
    MSB_ENTRY_SUBTYPE = MSBPartSubtype.ConnectCollision
    _MODEL_ADAPTER = MSBPartModelAdapter(SoulstructType.COLLISION, MSBCollisionModel)

    __slots__ = []

    SUBTYPE_FIELDS = (
        MSBReferenceFieldAdapter("collision", ref_type=SoulstructType.COLLISION),
        SoulstructFieldAdapter("connected_map_id"),  # stored as four ints in Blender properties
    )
