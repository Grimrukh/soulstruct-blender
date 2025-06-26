from __future__ import annotations

__all__ = [
    "BaseBlenderMSBPart_DS1",
]

import abc

from soulstruct.darksouls1ptde.maps.msb import MSB, BitSet128

from soulstruct.blender.msb.types.adapters import FieldAdapter, MSBPartGroupsAdapter
from soulstruct.blender.msb.types.base.parts import BaseBlenderMSBPart, PART_T, SUBTYPE_PROPS_T


class BaseBlenderMSBPart_DS1(BaseBlenderMSBPart[PART_T, SUBTYPE_PROPS_T, MSB, BitSet128], abc.ABC):

    TYPE_FIELDS = BaseBlenderMSBPart.TYPE_FIELDS + (
        MSBPartGroupsAdapter("draw_groups", bit_set_type=BitSet128),
        MSBPartGroupsAdapter("display_groups", bit_set_type=BitSet128),
        FieldAdapter("ambient_light_id"),
        FieldAdapter("fog_id"),
        FieldAdapter("scattered_light_id"),
        FieldAdapter("lens_flare_id"),
        FieldAdapter("shadow_id"),
        FieldAdapter("dof_id"),
        FieldAdapter("tone_map_id"),
        FieldAdapter("point_light_id"),
        FieldAdapter("tone_correction_id"),
        FieldAdapter("lod_id"),
        FieldAdapter("is_shadow_source"),
        FieldAdapter("is_shadow_destination"),
        FieldAdapter("is_shadow_only"),
        FieldAdapter("draw_by_reflect_cam"),
        FieldAdapter("draw_only_reflect_cam"),
        FieldAdapter("use_depth_bias_float"),
        FieldAdapter("disable_point_light_effect"),
    )

    draw_groups: BitSet128
    display_groups: BitSet128
    ambient_light_id: int
    fog_id: int
    scattered_light_id: int
    lens_flare_id: int
    shadow_id: int
    dof_id: int
    tone_map_id: int
    point_light_id: int
    tone_correction_id: int
    lod_id: int
    is_shadow_source: bool
    is_shadow_destination: bool
    is_shadow_only: bool
    draw_by_reflect_cam: bool
    draw_only_reflect_cam: bool
    use_depth_bias_float: bool
    disable_point_light_effect: bool
