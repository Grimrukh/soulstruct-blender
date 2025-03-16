from __future__ import annotations

__all__ = [
    "BaseBlenderMSBPart_DS1",
]

import abc

from soulstruct.darksouls1ptde.maps.msb import MSB, BitSet128

from io_soulstruct.msb.types.adapters import SoulstructFieldAdapter, MSBPartGroupsAdapter
from io_soulstruct.msb.types.base.parts import BaseBlenderMSBPart, PART_T, SUBTYPE_PROPS_T
from io_soulstruct.msb.properties.parts import MSBPartProps


class BaseBlenderMSBPart_DS1(BaseBlenderMSBPart[PART_T, MSBPartProps, SUBTYPE_PROPS_T, MSB], abc.ABC):

    TYPE_FIELDS = BaseBlenderMSBPart.TYPE_FIELDS + (
        MSBPartGroupsAdapter("draw_groups", bit_set_type=BitSet128),
        MSBPartGroupsAdapter("display_groups", bit_set_type=BitSet128),
        SoulstructFieldAdapter("ambient_light_id"),
        SoulstructFieldAdapter("fog_id"),
        SoulstructFieldAdapter("scattered_light_id"),
        SoulstructFieldAdapter("lens_flare_id"),
        SoulstructFieldAdapter("shadow_id"),
        SoulstructFieldAdapter("dof_id"),
        SoulstructFieldAdapter("tone_map_id"),
        SoulstructFieldAdapter("point_light_id"),
        SoulstructFieldAdapter("tone_correction_id"),
        SoulstructFieldAdapter("lod_id"),
        SoulstructFieldAdapter("is_shadow_source"),
        SoulstructFieldAdapter("is_shadow_destination"),
        SoulstructFieldAdapter("is_shadow_only"),
        SoulstructFieldAdapter("draw_by_reflect_cam"),
        SoulstructFieldAdapter("draw_only_reflect_cam"),
        SoulstructFieldAdapter("use_depth_bias_float"),
        SoulstructFieldAdapter("disable_point_light_effect"),
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
