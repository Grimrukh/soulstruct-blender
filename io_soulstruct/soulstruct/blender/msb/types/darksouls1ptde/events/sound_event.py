from __future__ import annotations

__all__ = [
    "BlenderMSBSoundEvent",
]

from soulstruct.darksouls1ptde.events.enums import SoundType
from soulstruct.darksouls1ptde.maps.msb import MSBSoundEvent

from soulstruct.blender.msb.properties import BlenderMSBEventSubtype, MSBSoundEventProps
from soulstruct.blender.msb.types.adapters import *
from .base import BaseBlenderMSBEvent_DS1


@soulstruct_adapter
class BlenderMSBSoundEvent(BaseBlenderMSBEvent_DS1[MSBSoundEvent, MSBSoundEventProps]):

    SOULSTRUCT_CLASS = MSBSoundEvent
    MSB_ENTRY_SUBTYPE = BlenderMSBEventSubtype.Sound
    PARENT_PROP_NAME = "attached_region"  # attached part is "draw parent" I believe
    __slots__ = []

    SUBTYPE_FIELDS = (
        CustomFieldAdapter(
            "sound_type",
            read_func=lambda x: SoundType(x).name,
            write_func=lambda x: SoundType[x].value,
        ),
        FieldAdapter("sound_id"),
    )

    sound_type: int
    sound_id: int
