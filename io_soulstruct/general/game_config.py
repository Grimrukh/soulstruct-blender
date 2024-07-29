"""Repository for fixed, game-specific configuration data."""
from __future__ import annotations

__all__ = [
    "GameConfig",
    "GAME_CONFIG",
]

from dataclasses import dataclass, field
from pathlib import Path

from soulstruct.base.models.flver import Version
from soulstruct.games import *


@dataclass(slots=True)
class GameConfig:

    uses_matbin: bool
    flver_default_version: Version

    # Redirect files that do and do not use the latest version of map files (e.g. to handle Darkroot Garden in DS1).
    new_to_old_map: dict[str, str] = field(default_factory=dict)
    old_to_new_map: dict[str, str] = field(default_factory=dict)
    # Indicates which file types prefer OLD versions of the map, and which prefer NEW.
    use_new_map: tuple[str, ...] = ()
    use_old_map: tuple[str, ...] = ()

    def process_file_map_stem_version(self, map_stem: str, *parts: str | Path) -> str:
        if not parts:
            return map_stem

        # Check if an older or newer version of the map exists to redirect to, depending on file type.
        last_part = str(parts[-1]).lower().removesuffix(".dcx")
        if self.old_to_new_map and map_stem in self.old_to_new_map and last_part.endswith(self.use_new_map):
            # Redirect to NEW map version.
            return self.old_to_new_map[map_stem]
        elif self.new_to_old_map and map_stem in self.new_to_old_map and last_part.endswith(self.use_old_map):
            # Redirect to OLD map version.
            return self.new_to_old_map[map_stem]
        return map_stem


GAME_CONFIG = {
    DARK_SOULS_PTDE: GameConfig(
        uses_matbin=False,
        flver_default_version=Version.DarkSouls_A,
        new_to_old_map={
            "m12_00_00_01": "m12_00_00_00",
        },
        old_to_new_map={
            "m12_00_00_00": "m12_00_00_01",
        },
        use_new_map=(".msb", ".nvmbnd", ".mcg", ".mcp"),
        use_old_map=(".flver", ".hkxbhd", ".hkxbdt"),
    ),
    DARK_SOULS_DSR: GameConfig(
        uses_matbin=False,
        flver_default_version=Version.DarkSouls_A,
        new_to_old_map={
            "m12_00_00_01": "m12_00_00_00",
        },
        old_to_new_map={
            "m12_00_00_00": "m12_00_00_01",
        },
        use_new_map=(".msb", ".nvmbnd", ".mcg", ".mcp"),
        use_old_map=(".flver", ".hkxbhd", ".hkxbdt"),
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
