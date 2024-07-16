"""Repository for fixed, game-specific configuration data."""
from __future__ import annotations

__all__ = [
    "GameConfig",
    "GAME_CONFIG",
]

from dataclasses import dataclass

from soulstruct.base.models.flver import Version
from soulstruct.games import *


@dataclass(slots=True)
class GameConfig:

    uses_matbin: bool
    flver_default_version: Version


GAME_CONFIG = {
    DARK_SOULS_PTDE: GameConfig(
        uses_matbin=False,
        flver_default_version=Version.DarkSouls_A,
    ),
    DARK_SOULS_DSR: GameConfig(
        uses_matbin=False,
        flver_default_version=Version.DarkSouls_A,
    ),
    BLOODBORNE: GameConfig(
        uses_matbin=False,
        flver_default_version=Version.Bloodborne_DS3_A,
    ),
    DARK_SOULS_3: GameConfig(
        uses_matbin=False,
        flver_default_version=Version.Bloodborne_DS3_A,
    ),
    SEKIRO: GameConfig(
        uses_matbin=False,
        flver_default_version=Version.Sekiro_EldenRing,
    ),
    ELDEN_RING: GameConfig(
        uses_matbin=True,
        flver_default_version=Version.Sekiro_EldenRing,
    ),
}
