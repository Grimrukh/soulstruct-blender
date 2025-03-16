from __future__ import annotations

__all__ = [
    "BlenderMSBObject",
]

import bpy

from soulstruct.demonssouls.maps.msb import MSB, BitSet128
from soulstruct.demonssouls.maps.models import MSBObjectModel
from soulstruct.demonssouls.maps.parts import MSBObject, MSBDummyObject

from io_soulstruct.msb.types.adapters import *
from io_soulstruct.msb.properties.parts import MSBPartSubtype, MSBPartProps, MSBObjectProps
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import LoggingOperator

from .base import BaseBlenderMSBPart_DES


@create_msb_entry_field_adapter_properties
class BlenderMSBObject(BaseBlenderMSBPart_DES[MSBObject, MSBPartProps, MSBObjectProps, MSB, BitSet128]):
    """Concrete wrapper for MSB Objects in Demon's Souls."""

    SOULSTRUCT_CLASS = MSBObject
    SOULSTRUCT_DUMMY_CLASS = MSBDummyObject
    MSB_ENTRY_SUBTYPE = MSBPartSubtype.Object
    MODEL_SUBTYPES = ["object_models"]

    _MODEL_ADAPTER = MSBPartModelAdapter(SoulstructType.FLVER, MSBObjectModel)

    __slots__ = []

    SUBTYPE_FIELDS = (
        SoulstructFieldAdapter("break_term"),
        SoulstructFieldAdapter("net_sync_type"),
        SoulstructFieldAdapter("default_animation"),
        SoulstructFieldAdapter("unk_x0e"),
        SoulstructFieldAdapter("unk_x10"),
    )

    break_term: int
    net_sync_type: int
    default_animation: int
    unk_x0e: int
    unk_x10: int

    def _post_new_from_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBObject,
    ):
        self.subtype_properties.is_dummy = "Dummy" in soulstruct_obj.__class__.__name__

    def _create_soulstruct_obj(self):
        if self.subtype_properties.is_dummy:
            # noinspection PyArgumentList
            return self.SOULSTRUCT_DUMMY_CLASS(name=self.game_name)
        # noinspection PyArgumentList
        return self.SOULSTRUCT_CLASS(name=self.game_name)
