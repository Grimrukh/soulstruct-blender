"""Adapter functions for converting between Blender object names and game names for MSB parts, events, and regions."""
from __future__ import annotations

__all__ = [
    "get_part_game_name",
    "get_event_game_name",
    "get_region_game_name",
]

import re

from io_soulstruct.utilities.misc import remove_dupe_suffix, get_model_name

_EVENT_PREFIX_RE = re.compile(r"^<(.*)> (.*)$")  # note exactly one space, in case game name starts with spaces


def get_part_game_name(obj_name: str) -> str:
    """Get the game name of an MSB Part Blender object from its Blender name.

    We ignore everything after the first space OR first period for Part names, which are more constrained.
    """
    return get_model_name(obj_name)  # stripped internally


def get_event_game_name(obj_name: str) -> str:
    """Get the game name of an MSB Event Blender object from its Blender name.

    We remove any Event subtype tag '<EvenSubtype>' added by Blender on import. Note that we do NOT strip the name.
    """
    name = remove_dupe_suffix(obj_name)  # no strip!
    if match := _EVENT_PREFIX_RE.match(name):
        return match.group(2)  # no strip!
    return name


def get_region_game_name(obj_name: str) -> str:
    """Get the game name of an MSB Region Blender object from its Blender name. Nothing extra is removed."""
    return remove_dupe_suffix(obj_name)  # no strip!
