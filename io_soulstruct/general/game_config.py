"""Repository for fixed, game-specific configuration data."""
from __future__ import annotations

__all__ = [
    "GameConfig",
    "GAME_CONFIG",
]

from types import ModuleType
from dataclasses import dataclass, field
from pathlib import Path

from soulstruct.base.models.flver import Version
from soulstruct.base.maps.msb import MSB as BaseMSB
from soulstruct.games import *
from soulstruct.bloodborne.maps import constants as bb_constants
from soulstruct.bloodborne.maps import MSB as bb_MSB
from soulstruct.darksouls1ptde.maps import constants as ds1ptde_constants
from soulstruct.darksouls1ptde.maps import MSB as ds1ptde_MSB
from soulstruct.darksouls1r.maps import constants as ds1r_constants
from soulstruct.darksouls1r.maps import MSB as ds1r_MSB
from soulstruct.darksouls3.maps import constants as ds3_constants
# from soulstruct.darksouls3.maps import MSB as ds3_MSB
from soulstruct.eldenring.maps import constants as er_constants
from soulstruct.eldenring.maps import MSB as er_MSB


@dataclass(slots=True)
class GameConfig:

    uses_matbin: bool
    flver_default_version: Version

    msb_class: type[BaseMSB] | None = None

    # Redirect files that do and do not use the latest version of map files (e.g. to handle Darkroot Garden in DS1).
    new_to_old_map: dict[str, str] = field(default_factory=dict)
    old_to_new_map: dict[str, str] = field(default_factory=dict)
    # Indicates which file types prefer OLD versions of the map, and which prefer NEW.
    use_new_map: tuple[str, ...] = ()
    use_old_map: tuple[str, ...] = ()

    map_constants: ModuleType = None

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
        msb_class=ds1ptde_MSB,
        new_to_old_map={
            "m12_00_00_01": "m12_00_00_00",
        },
        old_to_new_map={
            "m12_00_00_00": "m12_00_00_01",
        },
        use_new_map=(".msb", ".nvmbnd", ".mcg", ".mcp"),
        use_old_map=(".flver", ".hkxbhd", ".hkxbdt"),
        map_constants=ds1ptde_constants,
    ),
    DARK_SOULS_DSR: GameConfig(
        uses_matbin=False,
        flver_default_version=Version.DarkSouls_A,
        msb_class=ds1r_MSB,
        new_to_old_map={
            "m12_00_00_01": "m12_00_00_00",
        },
        old_to_new_map={
            "m12_00_00_00": "m12_00_00_01",
        },
        use_new_map=(".msb", ".nvmbnd", ".mcg", ".mcp"),
        use_old_map=(".flver", ".hkxbhd", ".hkxbdt"),
        map_constants=ds1r_constants,
    ),
    BLOODBORNE: GameConfig(
        uses_matbin=False,
        flver_default_version=Version.Bloodborne_DS3_A,
        msb_class=bb_MSB,
        map_constants=bb_constants,
    ),
    DARK_SOULS_3: GameConfig(
        uses_matbin=False,
        flver_default_version=Version.Bloodborne_DS3_A,
        map_constants=ds3_constants,
    ),
    SEKIRO: GameConfig(
        uses_matbin=False,
        flver_default_version=Version.Sekiro_EldenRing,
    ),
    ELDEN_RING: GameConfig(
        uses_matbin=True,
        flver_default_version=Version.Sekiro_EldenRing,
        msb_class=er_MSB,
        map_constants=er_constants,
    ),
}
