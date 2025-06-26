from __future__ import annotations

__all__ = [
    "BlenderMSBSoundEvent",
]

from soulstruct.demonssouls.events.enums import SoundType
from soulstruct.demonssouls.maps.msb import MSBSoundEvent

from soulstruct.blender.msb.properties import BlenderMSBEventSubtype, MSBSoundEventProps
from soulstruct.blender.msb.types.adapters import *

from .base import BaseBlenderMSBEvent_DES


@soulstruct_adapter
class BlenderMSBSoundEvent(BaseBlenderMSBEvent_DES[MSBSoundEvent, MSBSoundEventProps]):

    SOULSTRUCT_CLASS = MSBSoundEvent
    MSB_ENTRY_SUBTYPE = BlenderMSBEventSubtype.Sound
    PARENT_PROP_NAME = "attached_region"  # attached part is "draw parent" (hear parent?) I believe
    __slots__ = []

    SUBTYPE_FIELDS = (
        FieldAdapter("unk_x00"),
        CustomFieldAdapter(
            "sound_type",
            read_func=lambda x: SoundType(x).name,
            write_func=lambda x: SoundType[x].value,
        ),
        FieldAdapter("sound_id"),
    )

    unk_x00: int
    sound_type: int
    sound_id: int
