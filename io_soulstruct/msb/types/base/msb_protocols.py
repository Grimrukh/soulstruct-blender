# TODO: Pretty sure I can delete all this. No more intermediate classes trying to present shared stuff.
"""Typing Protocols for `MSBEntry` and its subclasses.

Much easier to use Protocols for MSB entry types/subtypes, as games use very similar subclasses of MSBPart that do not
share a parent.
"""
from __future__ import annotations

__all__ = [
    "MSBEntryProtocol",

    "MSBModelProtocol",

    "MSBRegionProtocol",

    "MSBEventProtocol",

    "MSBPartProtocol",
    "MSBMapPieceProtocol",
    "MSBCollisionProtocol",
    "MSBNavmeshProtocol",
    "MSBCharacterProtocol",
    "MSBObjectProtocol",
    "MSBPlayerStartProtocol",
    "MSBConnectCollisionProtocol",
]

import typing as tp

from soulstruct.base.maps.msb.enums import *
from soulstruct.base.maps.msb.region_shapes import RegionShape
from soulstruct.base.maps.msb.utils import *
from soulstruct.utilities.maths import Vector3


class MSBEntryProtocol(tp.Protocol):

    NAME_ENCODING: tp.ClassVar[str]
    SUPERTYPE_ENUM: tp.ClassVar[MSBSupertype]
    SUBTYPE_ENUM: tp.ClassVar[BaseMSBSubtype]
    MSB_ENTRY_REFERENCES: tp.ClassVar[list[str]]

    name: str
    description: str  # not exported for early games


class MSBModelProtocol(tp.Protocol):
    sib_path: str

    def set_auto_sib_path(self, **format_kwargs):
        ...

    def get_model_file_stem(self, map_stem: str):
        ...

    @classmethod
    def model_file_stem_to_model_name(cls, model_stem: str) -> str:
        ...

    def set_name_from_model_file_stem(self, model_stem: str):
        ...


class MSBRegionProtocol(MSBEntryProtocol, tp.Protocol):
    translate: Vector3
    rotate: Vector3
    entity_id: int
    shape: RegionShape


from soulstruct.darksouls1ptde.maps.regions import MSBRegion


def use_region(r: MSBRegionProtocol):
    pass


use_region(MSBRegion(name="test"))


class MSBEventProtocol(MSBEntryProtocol, tp.Protocol):
    entity_id: int
    attached_part: MSBPartProtocol
    attached_region: MSBRegionProtocol


class MSBPartProtocol(MSBEntryProtocol, tp.Protocol):
    BIT_SET_TYPE: tp.ClassVar[type[BitSet]]

    model: MSBModelProtocol
    translate: Vector3
    rotate: Vector3
    scale: Vector3
    draw_groups: BitSet128 | BitSet256
    display_groups: BitSet128 | BitSet256
    entity_id: int
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


class MSBMapPieceProtocol(MSBPartProtocol, tp.Protocol):
    """No additional fields, but here for clarity."""


class MSBCollisionProtocol(MSBPartProtocol, tp.Protocol):
    """Not many fields common to all games."""
    sound_space_type: int
    place_name_banner_id: int
    force_place_name_banner: bool
    reflect_plane_height: float
    hit_filter_id: int


class MSBNavmeshProtocol(MSBPartProtocol, tp.Protocol):
    navmesh_groups: BitSet128 | BitSet256


@tp.runtime_checkable
class MSBCharacterProtocol(MSBPartProtocol, tp.Protocol):
    draw_parent: MSBPartProtocol
    character_id: int
    talk_id: int
    platoon_id: int
    patrol_type: int
    player_id: int
    default_animation: int
    damage_animation: int
    patrol_regions: list[MSBRegionProtocol | None]


@tp.runtime_checkable
class MSBObjectProtocol(MSBPartProtocol, tp.Protocol):
    break_term: int
    net_sync_type: int
    default_animation: int
    unk_x0e: int
    unk_x10: int


class MSBPlayerStartProtocol(MSBPartProtocol, tp.Protocol):
    """No additional (common) fields, but here for clarity."""


class MSBConnectCollisionProtocol(MSBPartProtocol, tp.Protocol):
    collision: MSBCollisionProtocol
    connected_map_id: list[int]


# Single-game subtypes like `MSBProtoboss` in Demon's Souls don't need protocols, as they don't need base wrappers.
