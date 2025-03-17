from __future__ import annotations

__all__ = [
    "MSBPartGroupsAdapter",
]

import typing as tp
from dataclasses import dataclass

import bpy

from soulstruct.base.maps.msb.utils import BitSet

from io_soulstruct.types.field_adapters import FieldAdapter

BIT_SET_T = tp.TypeVar("BIT_SET_T", bound=BitSet)

if tp.TYPE_CHECKING:
    from ..base.parts import BaseBlenderMSBPart


@dataclass(slots=True, frozen=True)
class MSBPartGroupsAdapter(FieldAdapter, tp.Generic[BIT_SET_T]):
    """Adapter for any `MSBPart` field using a `BitSet` (e.g. draw/display/navmesh groups).

    Only 128-bit and 256-bit `BitSet` types are supported. (1024-bit is only used for `collision_mask` in Elden Ring.)
    """

    bit_set_type: type[BIT_SET_T] = None

    def __post_init__(self):
        super(MSBPartGroupsAdapter, self).__post_init__()
        if self.bit_set_type is None:
            raise ValueError("Must provide a `BitSet` type for MSBPartGroupsAdapter.")

    def getter(self, bl_obj: BaseBlenderMSBPart, is_subtype=False) -> BIT_SET_T:
        props = bl_obj.subtype_properties if is_subtype else bl_obj.type_properties
        bit_vector_32s = self._get_groups_props(props, self.soulstruct_field_name, self.bit_set_type.BIT_COUNT)
        groups = set()
        for i, bit_vector_32 in enumerate(bit_vector_32s):
            for j in range(32):
                if bit_vector_32[i]:
                    groups.add(i * 32 + j)
        return self.bit_set_type(groups)

    def setter(self, bl_obj: BaseBlenderMSBPart, value: BIT_SET_T, is_subtype=False) -> None:
        if not isinstance(value, self.bit_set_type):
            raise TypeError(
                f"Groups must be set with a `{self.bit_set_type.__class__.__name__}` instance, "
                f"not: {value.__class__.__name__}.",
            )
        props = bl_obj.subtype_properties if is_subtype else bl_obj.type_properties
        bit_vector_32s = self._get_groups_props(props, self.soulstruct_field_name, self.bit_set_type.BIT_COUNT)
        bits = value.enabled_bits
        for i, bit_vector_32 in enumerate(bit_vector_32s):
            for j in range(32):
                bit_vector_32[j] = (i * 32 + j) in bits

    @staticmethod
    def _get_groups_props(
        props: bpy.types.PropertyGroup,
        field_name: str,
        bit_count: int,
    ) -> list[bpy.types.CollectionProperty]:
        """Get the appropriate number of draw group properties for the given bit count (128 or 256)."""
        if bit_count == 128:
            return [getattr(props, f"{field_name}_{i}") for i in range(4)]
        elif bit_count == 256:
            return [getattr(props, f"{field_name}_{i}") for i in range(8)]
        raise ValueError(f"Invalid MSB Part `{field_name}` bit count: {bit_count}. Must be 128 or 256.")
