from __future__ import annotations

__all__ = [
    "BlenderMSBSoundEvent",
]

from soulstruct.demonssouls.maps import MSB
from soulstruct.demonssouls.maps.msb import MSBSoundEvent

from io_soulstruct.msb.properties import MSBEventSubtype, MSBEventProps, MSBSoundEventProps
from io_soulstruct.msb.types.base.events import BaseBlenderMSBEvent
from io_soulstruct.msb.types.adapters import *


@create_msb_entry_field_adapter_properties
class BlenderMSBSoundEvent(BaseBlenderMSBEvent[MSBSoundEvent, MSBEventProps, MSBSoundEventProps, MSB]):

    SOULSTRUCT_CLASS = MSBSoundEvent
    MSB_ENTRY_SUBTYPE = MSBEventSubtype.Sound
    PARENT_PROP_NAME = "attached_region"  # attached part is "draw parent" (hear parent?) I believe
    __slots__ = []

    SUBTYPE_FIELDS = (
        SoulstructFieldAdapter("unk_x00"),
        SoulstructFieldAdapter("sound_type"),
        SoulstructFieldAdapter("sound_id"),
    )

    unk_x00: int
    sound_type: int
    sound_id: int
