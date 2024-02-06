from __future__ import annotations

__all__ = [
    "obj_to_msb_entry_transform",
]

import typing as tp

import bpy

from io_soulstruct.utilities import BlenderTransform

if tp.TYPE_CHECKING:
    from soulstruct.base.maps.msb.parts import BaseMSBPart
    from soulstruct.base.maps.msb.regions import BaseMSBRegion


def obj_to_msb_entry_transform(obj: bpy.types.Object, msb_entry: BaseMSBPart | BaseMSBRegion):
    bl_transform = BlenderTransform.from_bl_obj(obj)
    msb_entry.translate = bl_transform.game_translate
    msb_entry.rotate = bl_transform.game_rotate_deg
    try:
        # Parts only.
        msb_entry.scale = bl_transform.game_scale
    except AttributeError:
        pass
