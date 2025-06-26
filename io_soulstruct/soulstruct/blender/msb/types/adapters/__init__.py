"""Adds a class that can adapt MSB Entry references between MSBs and Blender.

Includes simple name adapter functions for each Entry subtype (used in multiple places for finding referenced Blender
objects and setting `MSBEntry.name` correctly for the supertype).
"""

__all__ = [
    "FieldAdapter",
    "CustomFieldAdapter",
    "soulstruct_adapter",
    "MSBPartGroupsAdapter",
    "MSBPartModelAdapter",
    "MSBReferenceFieldAdapter",
    "MSBTransformFieldAdapter",

    "get_part_game_name",
    "get_event_game_name",
    "get_region_game_name",
]

from soulstruct.blender.types.field_adapters import FieldAdapter, CustomFieldAdapter, soulstruct_adapter
from .groups import MSBPartGroupsAdapter
from .model import MSBPartModelAdapter
from .reference import MSBReferenceFieldAdapter
from .transform import MSBTransformFieldAdapter
from .names import *
