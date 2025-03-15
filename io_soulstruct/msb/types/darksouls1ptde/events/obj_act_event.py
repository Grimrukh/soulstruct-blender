from __future__ import annotations

__all__ = [
    "BlenderMSBObjActEvent",
]

import bpy

from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.msb import MSBObjActEvent

from io_soulstruct.msb.properties import MSBEventSubtype, MSBEventProps, MSBObjActEventProps
from io_soulstruct.msb.types.adapters import *
from io_soulstruct.types import SoulstructType

from .base import BaseBlenderMSBEventDS1


@create_msb_entry_field_adapter_properties
class BlenderMSBObjActEvent(BaseBlenderMSBEventDS1[MSBObjActEvent, MSBEventProps, MSBObjActEventProps, MSB]):

    SOULSTRUCT_CLASS = MSBObjActEvent
    MSB_ENTRY_SUBTYPE = MSBEventSubtype.ObjAct
    PARENT_PROP_NAME = "obj_act_part"
    __slots__ = []

    SUBTYPE_FIELDS = (
        MSBReferenceFieldAdapter("obj_act_part", ref_type=SoulstructType.MSB_PART),
        SoulstructFieldAdapter("obj_act_entity_id"),
        SoulstructFieldAdapter("obj_act_param_id"),
        SoulstructFieldAdapter("obj_act_state"),
        SoulstructFieldAdapter("obj_act_flag"),
    )

    obj_act_part: bpy.types.MeshObject | None
    obj_act_entity_id: int
    obj_act_param_id: int
    obj_act_state: int
    obj_act_flag: int
