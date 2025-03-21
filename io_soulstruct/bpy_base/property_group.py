from __future__ import annotations

__all__ = ["SoulstructPropertyGroup"]

import typing as tp

import bpy

from soulstruct.games import *

from io_soulstruct.exceptions import InternalSoulstructBlenderError


_ALL_ABBREV_NAMES = {game.abbreviated_name for game in GAMES}


class SoulstructPropertyGroup(bpy.types.PropertyGroup):

    # Maps `Game` instances to tuples of property names they support within this group.
    # If completely empty, then all properties are supported for all games.
    # If not empty and a `Game` key is absent, that game is not supported.
    # If a `Game` key is present but maps to an empty tuple, all properties are supported for that game.
    GAME_PROP_NAMES: tp.ClassVar[dict[Game, tuple[str, ...]]] = {}

    @classmethod
    def is_prop_active(cls, context: bpy.types.Context, prop_name: str) -> bool:
        """Check if given property name is valid for the active game (or based on any other context)."""
        if not cls.GAME_PROP_NAMES:
            return True  # only global properties
        game = context.scene.soulstruct_settings.game
        if game not in cls.GAME_PROP_NAMES:
            return False
        return not cls.GAME_PROP_NAMES[game] or prop_name in cls.GAME_PROP_NAMES[game]

    @classmethod
    def is_bool_prop_active_and_true(cls, context: bpy.types.Context, prop_name: str) -> bool:
        return cls.is_prop_active(context, prop_name) and getattr(cls, prop_name)

    @classmethod
    def get_all_prop_names(cls) -> list[str]:
        return list(cls.__annotations__.keys())

    @classmethod
    def get_game_prop_names(cls, context: bpy.types.Context) -> list[str]:
        """Only get cross-game properties or properties for the active game."""
        if not cls.GAME_PROP_NAMES:
            return cls.get_all_prop_names()
        game = context.scene.soulstruct_settings.game
        if game is DARK_SOULS_DSR and game not in cls.GAME_PROP_NAMES:
            # DSR defaults to matching PTDE (e.g. for MSBs).
            game = DARK_SOULS_PTDE
        if game not in cls.GAME_PROP_NAMES:
            raise InternalSoulstructBlenderError(f"Game {game} not supported by this property group ({cls.__name__}).")
        prop_names = cls.GAME_PROP_NAMES[game]
        if not prop_names:
            # Empty tuple value implies all properties are supported. (Absent key implies unsupported.)
            return cls.get_all_prop_names()
        return list(prop_names)
