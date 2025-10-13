from __future__ import annotations

__all__ = [
    "MSBTransformFieldAdapter",
]

import math
import typing as tp
from dataclasses import dataclass

import bpy

from soulstruct.blender.types.field_adapters import FieldAdapter
from soulstruct.blender.utilities.operators import LoggingOperator
from soulstruct.blender.utilities.conversion import *

if tp.TYPE_CHECKING:
    from soulstruct.blender.msb.types.base import BaseBlenderMSBEntry, ENTRY_T, TYPE_PROPS_T, SUBTYPE_PROPS_T, MSB_T


@dataclass(slots=True, frozen=True)
class MSBTransformFieldAdapter(FieldAdapter):
    """Converts between up to three MSB Entry field/Blender property pairs:
        `translate` <> `location`
           `rotate` <> `rotation_euler`
            `scale` <> `scale`

    Uses Blender MSB Entry's `transform_obj` property to access the Blender object that the transform is stored on,
    which may be an Armature parent. May also write the WORLD transform to an exported MSB Entry rather than the Blender
    object's local transform.

    NOTE: Slight abuse of notation with `soulstruct_field_name`, which is used to indicate which MSB Entry fields are
    handled, e.g. "translate|rotate|scale", "translate|rotate", etc. (in practice, likely just those two).
    """
    auto_prop: bool = False  # overridden default

    def __post_init__(self):
        super(MSBTransformFieldAdapter, self).__post_init__()
        field_names = set(self._get_field_names())
        if field_names - {"translate", "rotate", "scale"}:
            raise ValueError("MSB transform field adapter can only handle 'translate', 'rotate', and 'scale' fields.")
        if self.auto_prop:
            raise ValueError("MSB transform field adapter does not support auto-prop.")

    def _get_field_names(self) -> set[str]:
        return set(self.soulstruct_field_name.split("|"))

    def soulstruct_to_blender(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: ENTRY_T,
        bl_obj: BaseBlenderMSBEntry[ENTRY_T, TYPE_PROPS_T, SUBTYPE_PROPS_T, MSB_T],
    ):
        field_names = self._get_field_names()
        if "translate" in field_names:
            bl_translate = to_blender(getattr(soulstruct_obj, "translate"))
            bl_obj.transform_obj.location = bl_translate  # local
        if "rotate" in field_names:
            bl_rotate = to_blender(math.pi / 180.0 * getattr(soulstruct_obj, "rotate"))  # degrees to radians
            bl_obj.transform_obj.rotation_euler = bl_rotate  # local
        if "scale" in field_names:
            bl_scale = to_blender(getattr(soulstruct_obj, "scale"))
            bl_obj.transform_obj.scale = bl_scale  # local

    def blender_to_soulstruct(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        bl_obj: BaseBlenderMSBEntry[ENTRY_T, TYPE_PROPS_T, SUBTYPE_PROPS_T, MSB_T],
        soulstruct_obj: ENTRY_T,
    ):
        field_names = self._get_field_names()
        if context.scene.msb_export_settings.use_world_transforms:
            bl_translate, bl_quaternion, bl_scale = bl_obj.transform_obj.matrix_world.decompose()
            bl_rotate = bl_quaternion.to_euler()
        else:
            bl_translate = bl_obj.transform_obj.location
            bl_rotate = bl_obj.transform_obj.rotation_euler
            bl_scale = bl_obj.transform_obj.scale

        if "translate" in field_names:
            soulstruct_value = to_game(bl_translate)
            setattr(soulstruct_obj, "translate", soulstruct_value)
        if "rotate" in field_names:
            soulstruct_value = to_game(bl_rotate).to_deg()  # Blender radians -> MSB degrees
            setattr(soulstruct_obj, "rotate", soulstruct_value)
        if "scale" in field_names:
            soulstruct_value = to_game(bl_scale)
            setattr(soulstruct_obj, "scale", soulstruct_value)
