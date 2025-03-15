from __future__ import annotations

__all__ = [
    "BlenderMSBSoundEvent",
]

from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.msb import MSBSoundEvent

from io_soulstruct.msb.properties import MSBEventSubtype, MSBEventProps, MSBSoundEventProps
from io_soulstruct.msb.types.adapters import *
from .base import BaseBlenderMSBEventDS1


@create_msb_entry_field_adapter_properties
class BlenderMSBSoundEvent(BaseBlenderMSBEventDS1[MSBSoundEvent, MSBEventProps, MSBSoundEventProps, MSB]):

    SOULSTRUCT_CLASS = MSBSoundEvent
    MSB_ENTRY_SUBTYPE = MSBEventSubtype.Sound
    PARENT_PROP_NAME = "attached_region"  # attached part is "draw parent" I believe
    __slots__ = []

    SUBTYPE_FIELDS = (
        SoulstructFieldAdapter("sound_type"),
        SoulstructFieldAdapter("sound_id"),
    )

    sound_type: int
    sound_id: int
