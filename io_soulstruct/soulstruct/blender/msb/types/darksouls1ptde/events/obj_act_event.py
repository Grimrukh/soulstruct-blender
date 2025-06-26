from __future__ import annotations

__all__ = [
    "BlenderMSBObjActEvent",
]

import bpy

from soulstruct.darksouls1ptde.maps.msb import MSBObjActEvent

from soulstruct.blender.msb.properties import BlenderMSBEventSubtype, MSBObjActEventProps
from soulstruct.blender.msb.types.adapters import *
from soulstruct.blender.types import SoulstructType

from .base import BaseBlenderMSBEvent_DS1


@soulstruct_adapter
class BlenderMSBObjActEvent(BaseBlenderMSBEvent_DS1[MSBObjActEvent, MSBObjActEventProps]):

    SOULSTRUCT_CLASS = MSBObjActEvent
    MSB_ENTRY_SUBTYPE = BlenderMSBEventSubtype.ObjAct
    PARENT_PROP_NAME = "obj_act_part"
    __slots__ = []

    SUBTYPE_FIELDS = (
        MSBReferenceFieldAdapter("obj_act_part", ref_type=SoulstructType.MSB_PART),
        FieldAdapter("obj_act_entity_id"),
        FieldAdapter("obj_act_param_id"),
        FieldAdapter("obj_act_state"),
        FieldAdapter("obj_act_flag"),
    )

    obj_act_part: bpy.types.MeshObject | None
    obj_act_entity_id: int
    obj_act_param_id: int
    obj_act_state: int
    obj_act_flag: int
