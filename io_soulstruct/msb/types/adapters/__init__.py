"""Adds a class that can adapt MSB Entry references between MSBs and Blender.

Includes simple name adapter functions for each Entry subtype (used in multiple places for finding referenced Blender
objects and setting `MSBEntry.name` correctly for the supertype).
"""

__all__ = [
    "SoulstructFieldAdapter",
    "CustomSoulstructFieldAdapter",
    "MSBPartGroupsAdapter",
    "MSBPartModelAdapter",
    "MSBReferenceFieldAdapter",
    "create_msb_entry_field_adapter_properties",
    "get_part_game_name",
    "get_event_game_name",
    "get_region_game_name",
]

from io_soulstruct.types.field_adapters import SoulstructFieldAdapter, CustomSoulstructFieldAdapter
from .core import create_msb_entry_field_adapter_properties
from .groups import MSBPartGroupsAdapter
from .model import MSBPartModelAdapter
from .names import *
from .reference import MSBReferenceFieldAdapter
