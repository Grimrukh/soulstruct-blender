"""Base class for MSB events in Blender.

NOTE: Unlike Models, Parts, and Regions, Events don't have enough in common across games for shared subtype base
classes to be worth the hassle. It would just obfuscate the actual fields of each concrete class.
"""
from __future__ import annotations

__all__ = [
    "BaseBlenderMSBEvent",
]

import abc
import typing as tp

import bpy

from soulstruct.base.maps.msb.events import BaseMSBEvent

from io_soulstruct.msb.properties import BlenderMSBEventSubtype, MSBEventProps
from io_soulstruct.msb.types.adapters import *
from io_soulstruct.types import ObjectType, SoulstructType
from io_soulstruct.utilities.bpy_data import get_or_create_collection

from .entry import BaseBlenderMSBEntry, SUBTYPE_PROPS_T, MSB_T


EVENT_T = tp.TypeVar("EVENT_T", bound=BaseMSBEvent)
SELF_T = tp.TypeVar("SELF_T", bound="BaseBlenderMSBEvent")


class BaseBlenderMSBEvent(BaseBlenderMSBEntry[EVENT_T, MSBEventProps, SUBTYPE_PROPS_T, MSB_T], abc.ABC):
    """MSB Event instance.

    Always represented by an Empty object, parented to either the attached region or part, depending on the subtype.
    """

    TYPE: tp.ClassVar[SoulstructType] = SoulstructType.MSB_EVENT
    BL_OBJ_TYPE: tp.ClassVar[ObjectType] = ObjectType.EMPTY
    SOULSTRUCT_CLASS: tp.ClassVar[type[BaseMSBEvent]]
    MSB_ENTRY_SUBTYPE: tp.ClassVar[BlenderMSBEventSubtype]  # narrows type

    PARENT_PROP_NAME: tp.ClassVar[str] = ""  # name of property to use as Blender parent, if any ('attached_part', etc.)

    __slots__ = []
    obj: bpy.types.EmptyObject
    data: None

    TYPE_FIELDS = (
        FieldAdapter("entity_id"),
        MSBReferenceFieldAdapter("attached_part", ref_type=SoulstructType.MSB_PART),
        MSBReferenceFieldAdapter("attached_region", ref_type=SoulstructType.MSB_REGION),
    )

    entity_id: int
    attached_part: bpy.types.MeshObject | None
    attached_region: bpy.types.MeshObject | None

    @classmethod
    def get_msb_subcollection(cls, msb_collection: bpy.types.Collection, msb_stem: str) -> bpy.types.Collection:
        return get_or_create_collection(msb_collection, f"{msb_stem} Regions/Events")

    @classmethod
    def new(
        cls: type[SELF_T],
        name: str,
        data: bpy.types.Mesh | None,
        collection: bpy.types.Collection = None,
    ) -> SELF_T:
        """MSB Event has its '<EventSubtype>' prepended as a tag (removed for export/ref finding)."""
        event_name = f"<{cls.SOULSTRUCT_CLASS.__name__.removeprefix('MSB')}> {name}"
        return super().new(event_name, data, collection)  # type: SELF_T

    @property
    def game_name(self) -> str:
        """Any name is permitted for events, including Unicode (Japanese) characters, and they do not have to be
        unique in the MSB (though this makes Soulstruct EMEVD event scripting harder). We just remove any Blender
        duplicate suffixes and the convenient '<SUBTYPE>' suffix added on import."""
        return get_event_game_name(self.name)
