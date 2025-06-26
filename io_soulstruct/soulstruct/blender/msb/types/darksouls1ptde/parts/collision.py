from __future__ import annotations

__all__ = [
    "BlenderMSBCollision",
]

import bpy

from soulstruct.base.maps.msb.utils import BitSet128
from soulstruct.darksouls1ptde.maps.enums import CollisionHitFilter
from soulstruct.darksouls1ptde.maps.models import MSBCollisionModel
from soulstruct.darksouls1ptde.maps.parts import MSBCollision

from soulstruct.blender.msb.types.adapters import *
from soulstruct.blender.msb.properties.parts import BlenderMSBPartSubtype, MSBCollisionProps
from soulstruct.blender.types import SoulstructType

from .base import BaseBlenderMSBPart_DS1


@soulstruct_adapter
class BlenderMSBCollision(BaseBlenderMSBPart_DS1[MSBCollision, MSBCollisionProps]):
    """Not FLVER-based."""

    SOULSTRUCT_CLASS = MSBCollision
    MSB_ENTRY_SUBTYPE = BlenderMSBPartSubtype.Collision
    _MODEL_ADAPTER = MSBPartModelAdapter(SoulstructType.COLLISION, MSBCollisionModel)

    __slots__ = []

    SUBTYPE_FIELDS = (
        CustomFieldAdapter(
            "hit_filter_id",
            bl_prop_name="hit_filter",
            read_func=lambda i: CollisionHitFilter(i).name,  # integer to enum name
            write_func=lambda s: CollisionHitFilter[s].value,  # enum name to integer
        ),
        FieldAdapter("sound_space_type"),
        FieldAdapter("place_name_banner_id"),
        FieldAdapter("force_place_name_banner"),
        FieldAdapter("reflect_plane_height"),
        MSBPartGroupsAdapter("navmesh_groups", bit_set_type=BitSet128),
        MSBReferenceFieldAdapter("environment_event", ref_type=SoulstructType.MSB_EVENT, ref_subtype="environments"),
        FieldAdapter("play_region_id"),
        FieldAdapter("stable_footing_flag"),
        FieldAdapter("camera_1_id"),
        FieldAdapter("camera_2_id"),
        FieldAdapter("unk_x27_x28"),
        FieldAdapter("attached_bonfire"),
        FieldAdapter("vagrant_entity_ids"),
    )

    hit_filter: int  # TODO: probably better for Blender to use `int` and just a label generated from game-specific enum
    sound_space_type: int
    place_name_banner_id: int
    force_place_name_banner: bool
    reflect_plane_height: float
    navmesh_groups: BitSet128
    environment_event: bpy.types.Object | None
    play_region_id: int
    stable_footing_flag: int
    camera_1_id: int
    camera_2_id: int
    unk_x27_x28: int
    attached_bonfire: int
    vagrant_entity_ids: list[int]  # 3 ints
