from __future__ import annotations

__all__ = [
    "BlenderMSBEnvironmentEvent",
]

import typing as tp

import bpy
from io_soulstruct.msb.properties import MSBEventSubtype, MSBEnvironmentEventProps
from io_soulstruct.utilities import LoggingOperator
from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.msb import MSBEnvironmentEvent
from .msb_event import BlenderMSBEvent


class BlenderMSBEnvironmentEvent(BlenderMSBEvent[MSBEnvironmentEvent, MSBEnvironmentEventProps]):

    SOULSTRUCT_CLASS = MSBEnvironmentEvent
    EVENT_SUBTYPE = MSBEventSubtype.Environment
    PARENT_PROP_NAME = "attached_region"  # parenting to Collision would be useful but less important
    __slots__ = []

    # NOTE: The `attached_part` is a Collision, which circularly references this same Environment Event with a direct
    # local subtype index (unfortunately). This is the only case of MSB reference circularity in DS1. Fortunately, it's
    # easily handled in the `MSB` class, which has a method to look at all Environment attached parts and set the
    # `environment_event` field of those Collisions to reflect back. In Blender, the reference here is therefore kept
    # and the inverse Collision reference discarded, so Collisions can always be loaded first (in fact, this is the only
    # case of a Part referencing an Event).

    AUTO_SUBTYPE_PROPS = [
        "unk_x00_x04",
        "unk_x04_x08",
        "unk_x08_x0c",
        "unk_x0c_x10",
        "unk_x10_x14",
        "unk_x14_x18",
    ]

    unk_x00_x04: int
    unk_x04_x08: float
    unk_x08_x0c: float
    unk_x0c_x10: float
    unk_x10_x14: float
    unk_x14_x18: float

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBEnvironmentEvent,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
    ) -> tp.Self:
        bl_event = super().new_from_soulstruct_obj(operator, context, soulstruct_obj, name, collection, map_stem)
        for prop_name in cls.AUTO_SUBTYPE_PROPS:
            setattr(bl_event, prop_name, getattr(soulstruct_obj, prop_name))
        return bl_event

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> MSBEnvironmentEvent:
        environment_event = super().to_soulstruct_obj(operator, context, map_stem, msb)
        for prop_name in self.AUTO_SUBTYPE_PROPS:
            setattr(environment_event, prop_name, getattr(self, prop_name))
        return environment_event


BlenderMSBEnvironmentEvent.add_auto_subtype_props(*BlenderMSBEnvironmentEvent.AUTO_SUBTYPE_PROPS)
