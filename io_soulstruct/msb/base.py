from __future__ import annotations

__all__ = [
    "BlenderMSBEntry",
]

import abc
import typing as tp

import bpy

from io_soulstruct.utilities import Transform

if tp.TYPE_CHECKING:
    from soulstruct.base.maps.msb.parts import BaseMSBPart
    from soulstruct.base.maps.msb.regions import BaseMSBRegion


class BlenderMSBEntry(abc.ABC):
    """Base class for Blender objects that represent MSB entries of any supertype/subtype."""

    obj: bpy.types.Object

    def __init__(self, obj: bpy.types.Object):
        """NOTE: We don't check the `soulstruct_type` of `obj`."""
        # noinspection PyTypeChecker
        self.obj = obj

    def set_transform(self, part_or_region: BaseMSBPart | BaseMSBRegion):
        game_transform = Transform.from_msb_entry(part_or_region)
        self.obj.location = game_transform.bl_translate
        self.obj.rotation_euler = game_transform.bl_rotate
        self.obj.scale = game_transform.bl_scale
