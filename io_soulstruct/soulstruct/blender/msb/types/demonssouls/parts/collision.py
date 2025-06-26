from __future__ import annotations

__all__ = [
    "BlenderMSBCollision",
]

from soulstruct.demonssouls.maps.msb import BitSet128
from soulstruct.demonssouls.maps.enums import CollisionHitFilter
from soulstruct.demonssouls.maps.models import MSBCollisionModel
from soulstruct.demonssouls.maps.parts import MSBCollision

from soulstruct.blender.msb.types.adapters import *
from soulstruct.blender.msb.properties.parts import BlenderMSBPartSubtype, MSBCollisionProps
from soulstruct.blender.types import SoulstructType

from .base import BaseBlenderMSBPart_DES


@soulstruct_adapter
class BlenderMSBCollision(BaseBlenderMSBPart_DES[MSBCollision, MSBCollisionProps]):
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
        FieldAdapter("cubemap_index"),
        FieldAdapter("ref_tex_ids"),
        FieldAdapter("unk_x38"),
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
