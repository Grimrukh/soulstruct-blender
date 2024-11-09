"""Repository for fixed, game-specific configuration data."""
from __future__ import annotations

__all__ = [
    "GameConfig",
    "GAME_CONFIG",
]

from types import ModuleType
from dataclasses import dataclass, field
from pathlib import Path

from soulstruct.base.models.flver import FLVERVersion
from soulstruct.base.maps.msb import MSB as BaseMSB
from soulstruct.containers.tpf import TPFPlatform
from soulstruct.games import *

from soulstruct.demonssouls.maps import constants as des_constants
from soulstruct.demonssouls.maps import MSB as des_MSB

from soulstruct.darksouls1ptde.maps import constants as ds1ptde_constants
from soulstruct.darksouls1ptde.maps import MSB as ds1ptde_MSB

from soulstruct.darksouls1r.maps import constants as ds1r_constants
from soulstruct.darksouls1r.maps import MSB as ds1r_MSB

from soulstruct.bloodborne.maps import constants as bb_constants
from soulstruct.bloodborne.maps import MSB as bb_MSB

from soulstruct.darksouls3.maps import constants as ds3_constants
# from soulstruct.darksouls3.maps import MSB as ds3_MSB

from soulstruct.eldenring.maps import constants as er_constants
from soulstruct.eldenring.maps import MSB as er_MSB

from soulstruct_havok.core import PyHavokModule
from soulstruct_havok.fromsoft import darksouls1ptde, darksouls1r, bloodborne, sekiro, eldenring
from soulstruct_havok.fromsoft.base import BaseSkeletonHKX, BaseAnimationHKX


@dataclass(slots=True)
class GameConfig:

    # File format support.
    supports_flver: bool = False
    supports_nvm: bool = False
    supports_collision_model: bool = False
    supports_animation: bool = False
    supports_msb: bool = False
    supports_cutscenes: bool = False

    uses_matbin: bool = False
    flver_default_version: FLVERVersion = FLVERVersion.DarkSouls_A
    # True from Bloodborne (DS2?) onwards, where Map Piece FLVER vertices store their singular bone indices in the
    # fourth 8-bit component of the 'normal_w' vertex array, rather than having a full useless four-bone `bone_indices`
    # field like real rigged FLVERs.
    map_pieces_use_normal_w_bones: bool = False

    swizzle_platform: TPFPlatform | None = None  # overrides `TPF.platform` for de/swizzling
    msb_class: type[BaseMSB] | None = None

    # HAVOK
    py_havok_module: PyHavokModule | None = None
    skeleton_hkx: type[BaseSkeletonHKX] | None = None
    animation_hkx: type[BaseAnimationHKX] | None = None

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
    DEMONS_SOULS: GameConfig(
        supports_flver=True,
        supports_nvm=True,
        supports_collision_model=True,
        supports_animation=False,  # TODO: wavelet compression support?
        supports_msb=True,
        uses_matbin=False,
        flver_default_version=FLVERVersion.DemonsSouls,
        swizzle_platform=TPFPlatform.PC,  # no swizzling despite being a PS3 exclusive
        map_pieces_use_normal_w_bones=False,
        msb_class=des_MSB,
        map_constants=des_constants,

        py_havok_module=PyHavokModule.hk550,
        # Animation not yet supported (uses wavelet compression).
        skeleton_hkx=None,
        animation_hkx=None,
    ),
    DARK_SOULS_PTDE: GameConfig(
        supports_flver=True,
        supports_nvm=True,
        supports_collision_model=True,
        supports_animation=True,
        supports_msb=True,
        uses_matbin=False,
        flver_default_version=FLVERVersion.DarkSouls_A,
        map_pieces_use_normal_w_bones=False,
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

        py_havok_module=PyHavokModule.hk2010,
        skeleton_hkx=darksouls1ptde.SkeletonHKX,
        animation_hkx=darksouls1ptde.AnimationHKX,
    ),
    DARK_SOULS_DSR: GameConfig(
        supports_flver=True,
        supports_nvm=True,
        supports_collision_model=True,
        supports_animation=True,
        supports_msb=True,
        uses_matbin=False,
        flver_default_version=FLVERVersion.DarkSouls_A,
        map_pieces_use_normal_w_bones=False,
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

        py_havok_module=PyHavokModule.hk2015,
        skeleton_hkx=darksouls1r.SkeletonHKX,
        animation_hkx=darksouls1r.AnimationHKX,
    ),
    BLOODBORNE: GameConfig(
        supports_flver=True,
        supports_nvm=False,  # TODO: used?
        supports_collision_model=False,  # TODO: could at least read hknp meshes
        supports_animation=True,
        supports_msb=False,  # TODO
        uses_matbin=False,
        flver_default_version=FLVERVersion.Bloodborne_DS3_A,
        map_pieces_use_normal_w_bones=True,
        msb_class=bb_MSB,
        map_constants=bb_constants,

        py_havok_module=PyHavokModule.hk2014,
        skeleton_hkx=bloodborne.SkeletonHKX,
        animation_hkx=bloodborne.AnimationHKX,
    ),
    DARK_SOULS_3: GameConfig(
        supports_flver=True,
        supports_nvm=False,  # not used
        supports_collision_model=False,  # TODO: could at least read hknp meshes
        supports_animation=True,
        supports_msb=False,  # TODO: not supported by Soulstruct
        uses_matbin=False,
        flver_default_version=FLVERVersion.Bloodborne_DS3_A,
        map_pieces_use_normal_w_bones=True,
        map_constants=ds3_constants,

        py_havok_module=PyHavokModule.hk2014,
        # TODO: Not yet supported, but doable.
        skeleton_hkx=None,
        animation_hkx=None,
    ),
    SEKIRO: GameConfig(
        supports_flver=True,
        supports_nvm=False,
        supports_collision_model=False,
        supports_animation=False,  # TODO: probably easy
        supports_msb=False,
        uses_matbin=False,
        flver_default_version=FLVERVersion.Sekiro_EldenRing,
        map_pieces_use_normal_w_bones=True,

        py_havok_module=PyHavokModule.hk2016,
        skeleton_hkx=sekiro.SkeletonHKX,
        animation_hkx=sekiro.AnimationHKX,
    ),
    ELDEN_RING: GameConfig(
        supports_flver=True,
        supports_nvm=False,
        supports_collision_model=False,
        supports_animation=True,
        supports_msb=False,
        uses_matbin=True,
        flver_default_version=FLVERVersion.Sekiro_EldenRing,
        map_pieces_use_normal_w_bones=True,
        msb_class=er_MSB,
        map_constants=er_constants,

        py_havok_module=PyHavokModule.hk2018,
        skeleton_hkx=eldenring.SkeletonHKX,
        animation_hkx=eldenring.AnimationHKX,
    ),
}
