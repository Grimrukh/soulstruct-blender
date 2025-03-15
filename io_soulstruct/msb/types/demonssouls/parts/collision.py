from __future__ import annotations

__all__ = [
    "BlenderMSBCollision",
]

import bpy

from soulstruct.base.maps.msb.utils import BitSet128
from soulstruct.darksouls1ptde.maps.msb import MSB
from soulstruct.darksouls1ptde.maps.models import MSBCollisionModel
from soulstruct.darksouls1ptde.maps.parts import MSBCollision

from io_soulstruct.msb.types.base.parts import BaseBlenderMSBPart
from io_soulstruct.msb.types.adapters import *
from io_soulstruct.msb.properties.parts import MSBPartSubtype, MSBPartProps, MSBCollisionProps
from io_soulstruct.types import SoulstructType


@create_msb_entry_field_adapter_properties
class BlenderMSBCollision(BaseBlenderMSBPart[MSBCollision, MSBPartProps, MSBCollisionProps, MSB, BitSet128]):
    """Not FLVER-based."""

    SOULSTRUCT_CLASS = MSBCollision
    MSB_ENTRY_SUBTYPE = MSBPartSubtype.Collision
    _MODEL_ADAPTER = MSBPartModelAdapter(SoulstructType.COLLISION, MSBCollisionModel)

    __slots__ = []

    SUBTYPE_FIELDS = (
        SoulstructFieldAdapter("hit_filter_id", bl_prop_name="hit_filter"),
        SoulstructFieldAdapter("sound_space_type"),
        SoulstructFieldAdapter("place_name_banner_id"),
        SoulstructFieldAdapter("force_place_name_banner"),
        SoulstructFieldAdapter("reflect_plane_height"),
        MSBPartGroupsAdapter("navmesh_groups", bit_set_type=BitSet128),
        SoulstructFieldAdapter("cubemap_index"),
        SoulstructFieldAdapter("ref_tex_ids"),
        SoulstructFieldAdapter("unk_x38"),
    )

    hit_filter: int  # TODO: probably better for Blender to use `int` and just a label generated from game-specific enum
    sound_space_type: int
    place_name_banner_id: int
    force_place_name_banner: bool
    reflect_plane_height: float
    navmesh_groups: BitSet128
    cubemap_index: int
    ref_tex_ids: list[int]  # 16 ints
    unk_x38: int
