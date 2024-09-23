from __future__ import annotations

__all__ = [
    "BlenderMSBSoundEvent",
]

import typing as tp

import bpy
from io_soulstruct.msb.properties import MSBEventSubtype, MSBSoundEventProps
from io_soulstruct.utilities import LoggingOperator
from soulstruct.demonssouls.maps import MSB
from soulstruct.darksouls1ptde.events.enums import SoundType  # TODO: DeS module
from soulstruct.demonssouls.maps.msb import MSBSoundEvent
from .msb_event import BlenderMSBEvent


class BlenderMSBSoundEvent(BlenderMSBEvent[MSBSoundEvent, MSBSoundEventProps]):

    SOULSTRUCT_CLASS = MSBSoundEvent
    EVENT_SUBTYPE = MSBEventSubtype.Sound
    PARENT_PROP_NAME = "attached_region"  # attached part is "draw parent" I believe
    __slots__ = []

    @property
    def unk_x00(self) -> int:
        return self.subtype_properties.unk_x00

    @unk_x00.setter
    def unk_x00(self, value: int):
        self.subtype_properties.unk_x00 = value

    @property
    def sound_type(self) -> SoundType:
        return SoundType[self.subtype_properties.sound_type]

    @sound_type.setter
    def sound_type(self, value: SoundType):
        self.subtype_properties.sound_type = value.name

    @property
    def sound_id(self) -> int:
        return self.subtype_properties.sound_id

    @sound_id.setter
    def sound_id(self, value: int):
        self.subtype_properties.sound_id = value

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBSoundEvent,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
    ) -> tp.Self:
        bl_event = super().new_from_soulstruct_obj(operator, context, soulstruct_obj, name, collection, map_stem)
        bl_event.unk_x00 = soulstruct_obj.unk_x00
        bl_event.sound_type = SoundType(soulstruct_obj.sound_type)
        bl_event.sound_id = soulstruct_obj.sound_id
        return bl_event

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> MSBSoundEvent:
        sound_event = super().to_soulstruct_obj(operator, context, map_stem, msb)  # type: MSBSoundEvent
        sound_event.unk_x00 = self.unk_x00
        sound_event.sound_type = self.sound_type.value
        sound_event.sound_id = self.sound_id
        return sound_event
