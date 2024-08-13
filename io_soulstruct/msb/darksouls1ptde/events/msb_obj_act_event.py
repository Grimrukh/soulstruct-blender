from __future__ import annotations

__all__ = [
    "BlenderMSBObjActEvent",
]

import typing as tp

import bpy
from io_soulstruct.msb.properties import MSBEventSubtype, MSBObjActEventProps
from io_soulstruct.utilities import LoggingOperator
from io_soulstruct.types import SoulstructType
from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.msb import MSBObjActEvent
from .msb_event import BlenderMSBEvent


class BlenderMSBObjActEvent(BlenderMSBEvent[MSBObjActEvent, MSBObjActEventProps]):

    SOULSTRUCT_CLASS = MSBObjActEvent
    EVENT_SUBTYPE = MSBEventSubtype.ObjAct
    PARENT_PROP_NAME = "obj_act_part"
    __slots__ = []

    AUTO_SUBTYPE_PROPS = [
        "obj_act_entity_id",
        "obj_act_param_id",
        "obj_act_state",
        "obj_act_flag",
    ]

    obj_act_entity_id: int
    obj_act_param_id: int
    obj_act_state: int
    obj_act_flag: int

    @property
    def obj_act_part(self) -> bpy.types.Object | None:
        return self.subtype_properties.obj_act_part

    @obj_act_part.setter
    def obj_act_part(self, value: bpy.types.Object | None):
        self.subtype_properties.obj_act_part = value

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBObjActEvent,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
    ) -> tp.Self:
        bl_event = super().new_from_soulstruct_obj(operator, context, soulstruct_obj, name, collection, map_stem)
        bl_event.obj_act_part = cls.entry_ref_to_bl_obj(
            operator,
            soulstruct_obj,
            "obj_act_part",
            soulstruct_obj.obj_act_part,
            SoulstructType.MSB_PART,
            missing_collection_name=f"{map_stem} Missing MSB References".lstrip(),
        )
        for prop_name in cls.AUTO_SUBTYPE_PROPS:
            setattr(bl_event, prop_name, getattr(soulstruct_obj, prop_name))
        return bl_event

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> MSBObjActEvent:
        obj_act_event = super().to_soulstruct_obj(operator, context, map_stem, msb)
        obj_act_event.obj_act_part = self.bl_obj_to_entry_ref(msb, "obj_act_part", self.obj_act_part, obj_act_event)
        for prop_name in self.AUTO_SUBTYPE_PROPS:
            setattr(obj_act_event, prop_name, getattr(self, prop_name))
        return obj_act_event


BlenderMSBObjActEvent.add_auto_subtype_props(*BlenderMSBObjActEvent.AUTO_SUBTYPE_PROPS)
