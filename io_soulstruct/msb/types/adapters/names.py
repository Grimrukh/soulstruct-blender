"""Adapter functions for converting between Blender object names and game names for MSB parts, events, and regions."""
from __future__ import annotations

__all__ = [
    "get_part_game_name",
    "get_event_game_name",
    "get_region_game_name",
]

from io_soulstruct.utilities.misc import remove_dupe_suffix, get_model_name


def get_part_game_name(obj_name: str) -> str:
    """Get the game name of an MSB Part Blender object from its Blender name.

    We ignore everything after the first space OR first period for Part names, which are more constrained.
    """
    return get_model_name(obj_name)  # stripped internally


def get_event_game_name(obj_name: str) -> str:
    """Get the game name of an MSB Event Blender object from its Blender name.

    We also remove the ' <E>' suffix (note exactly one space removed) if it exists. This suffix is added by us when
    importing an MSB, as many Events have the same name as their parent Regions.
    """
    return remove_dupe_suffix(obj_name).removesuffix(" <E>")


def get_region_game_name(obj_name: str) -> str:
    """Get the game name of an MSB Region Blender object from its Blender name. Nothing extra is removed."""
    return remove_dupe_suffix(obj_name)  # no strip!
