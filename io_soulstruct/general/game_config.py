"""Repository for fixed, game-specific configuration data."""
from __future__ import annotations

__all__ = [
    "BlenderGameConfig",
    "BLENDER_GAME_CONFIG",
]

from types import ModuleType
from dataclasses import dataclass, field

from soulstruct.base.models.flver import FLVERVersion
from soulstruct.base.models.shaders import MatDef
from soulstruct.base.maps.msb import MSB as BaseMSB
from soulstruct.base.maps.navmesh import BaseNVMBND
from soulstruct.containers.tpf import TPFPlatform
from soulstruct.games import *

from soulstruct import demonssouls, darksouls1ptde, darksouls1r, bloodborne, darksouls3, eldenring

from soulstruct_havok.core import HavokModule
from soulstruct_havok import fromsoft as hk_fromsoft
from soulstruct_havok.fromsoft.base import BaseSkeletonHKX, BaseAnimationHKX


@dataclass(slots=True, kw_only=True)
class BlenderGameConfig:
    """Fixed configuration data and game-specific classes for a specific game."""

    # FLVER/MATERIAL CONFIG
    flver_default_version: FLVERVersion | None = None  # `None` implies no FLVER support
    swizzle_platform: TPFPlatform | None = None  # overrides `TPF.platform` for de/swizzling
    uses_matbin: bool = False
    matdef_class: type[MatDef] | None = None
    _split_mesh_kwargs: dict[str, int | bool] = field(default_factory=lambda: dict(
        use_mesh_bone_indices=False,
        max_mesh_vertex_count=4294967295,  # faces use 32-bit vertex indices
    ))

    # MSB CONFIG
    msb_class: type[BaseMSB] | None = None
    map_constants: ModuleType = None

    # NAVMESH CONFIG
    nvmbnd_class: type[BaseNVMBND] | None = None
    supports_mcg: bool = False

    # HAVOK CONFIG
    havok_module: HavokModule | None = None
    skeleton_hkx_class: type[BaseSkeletonHKX] | None = None
    animation_hkx_class: type[BaseAnimationHKX] | None = None
    supports_collision_model: bool = False  # `MapCollisionModel` support
    uses_loose_collision_files: bool = False
    supports_cutscenes: bool = False  # `RemoBND` support

    # MISC CONFIG
    # Redirect files that do and do not use the latest version of map files (e.g. to handle Darkroot Garden in DS1).
    new_to_old_map: dict[str, str] = field(default_factory=dict)
    old_to_new_map: dict[str, str] = field(default_factory=dict)
    # Indicates which file types prefer OLD versions of the map, and which prefer NEW.
    use_new_map: tuple[str, ...] = ()
    use_old_map: tuple[str, ...] = ()

    def process_file_map_stem_version(self, map_stem: str, file_name: str) -> str:
        """Check if an older or newer version of the map exists to redirect to, depending on file type."""
        last_part = file_name.lower().removesuffix(".dcx")
        if self.old_to_new_map and map_stem in self.old_to_new_map and last_part.endswith(self.use_new_map):
            # Redirect to NEW map version.
            return self.old_to_new_map[map_stem]
        elif self.new_to_old_map and map_stem in self.new_to_old_map and last_part.endswith(self.use_old_map):
            # Redirect to OLD map version.
            return self.new_to_old_map[map_stem]
        return map_stem

    @property
    def supports_flver(self) -> bool:
        return self.flver_default_version is not None

    @property
    def supports_msb(self) -> bool:
        return self.msb_class is not None

    @property
    def supports_nvm(self) -> bool:
        return self.nvmbnd_class is not None

    @property
    def supports_animation(self) -> bool:
        return (
            self.havok_module is not None
            and self.skeleton_hkx_class is not None
            and self.animation_hkx_class is not None
        )

    @property
    def split_mesh_kwargs(self) -> dict[str, int | bool]:
        """Return a copy of game-specific FLVER mesh-splitting kwargs."""
        return self._split_mesh_kwargs.copy()


BLENDER_GAME_CONFIG = {
    DEMONS_SOULS: BlenderGameConfig(
        flver_default_version=FLVERVersion.DemonsSouls,
        swizzle_platform=TPFPlatform.PC,  # no swizzling despite being a PS3 exclusive
        matdef_class=demonssouls.models.MatDef,
        _split_mesh_kwargs=dict(
            use_mesh_bone_indices=True,
            max_bones_per_mesh=38,
            max_mesh_vertex_count=65535,  # faces MUST use 16-bit vertex indices
        ),

        msb_class=demonssouls.maps.MSB,
        map_constants=demonssouls.maps.constants,

        # TODO: No idea why PyCharm is complaining about type here. Can't seem to detect 'type[BaseNVMBND] hint above.
        nvmbnd_class=demonssouls.maps.navmesh.NVMBND,
        supports_mcg=True,

        havok_module=HavokModule.hk550,
        skeleton_hkx_class=hk_fromsoft.demonssouls.SkeletonHKX,
        animation_hkx_class=hk_fromsoft.demonssouls.AnimationHKX,
        supports_collision_model=True,
        uses_loose_collision_files=True,
    ),
    DARK_SOULS_PTDE: BlenderGameConfig(
        flver_default_version=FLVERVersion.DarkSouls_A,
        matdef_class=darksouls1ptde.models.MatDef,
        _split_mesh_kwargs=dict(
            use_mesh_bone_indices=True,
            max_bones_per_mesh=38,
            max_mesh_vertex_count=65535,  # TODO: can DS1 use 32-bit vertices?
        ),

        msb_class=darksouls1ptde.maps.MSB,
        map_constants=darksouls1ptde.constants,

        nvmbnd_class=darksouls1ptde.maps.navmesh.NVMBND,
        supports_mcg=True,

        havok_module=HavokModule.hk2010,
        skeleton_hkx_class=hk_fromsoft.darksouls1ptde.SkeletonHKX,
        animation_hkx_class=hk_fromsoft.darksouls1ptde.AnimationHKX,
        supports_collision_model=True,
        uses_loose_collision_files=True,

        new_to_old_map={
            "m12_00_00_01": "m12_00_00_00",
        },
        old_to_new_map={
            "m12_00_00_00": "m12_00_00_01",
        },
        use_new_map=(".msb", ".nvmbnd", ".mcg", ".mcp"),
        use_old_map=(".flver", ".hkx"),
    ),
    DARK_SOULS_DSR: BlenderGameConfig(
        flver_default_version=FLVERVersion.DarkSouls_A,
        matdef_class=darksouls1r.models.MatDef,
        _split_mesh_kwargs=dict(
            use_mesh_bone_indices=True,
            max_bones_per_mesh=38,
            max_mesh_vertex_count=65535,  # TODO: can DS1 use 32-bit vertices?
        ),

        msb_class=darksouls1r.maps.MSB,
        map_constants=darksouls1r.maps.constants,

        nvmbnd_class=darksouls1r.maps.navmesh.NVMBND,
        supports_mcg=True,

        havok_module=HavokModule.hk2015,
        skeleton_hkx_class=hk_fromsoft.darksouls1r.SkeletonHKX,
        animation_hkx_class=hk_fromsoft.darksouls1r.AnimationHKX,
        supports_collision_model=True,

        new_to_old_map={
            "m12_00_00_01": "m12_00_00_00",
        },
        old_to_new_map={
            "m12_00_00_00": "m12_00_00_01",
        },
        use_new_map=(".msb", ".nvmbnd", ".mcg", ".mcp"),
        use_old_map=(".flver", ".hkxbhd", ".hkxbdt"),
    ),
    BLOODBORNE: BlenderGameConfig(
        flver_default_version=FLVERVersion.Bloodborne_DS3_A,
        matdef_class=bloodborne.models.MatDef,

        msb_class=None,  # TODO: need Blender wrappers
        map_constants=bloodborne.maps.constants,

        # NOTE: Bloodborne and onwards use Havok `NVMHKT` for navmeshes, not `NVM`.

        havok_module=HavokModule.hk2014,
        skeleton_hkx_class=hk_fromsoft.bloodborne.SkeletonHKX,
        animation_hkx_class=hk_fromsoft.bloodborne.AnimationHKX,
        supports_collision_model=False,  # TODO: could at least read hknp meshes
    ),
    DARK_SOULS_3: BlenderGameConfig(
        flver_default_version=FLVERVersion.Bloodborne_DS3_A,
        matdef_class=None,  # TODO: not in Soulstruct yet

        msb_class=None,  # TODO: not in Soulstruct yet
        map_constants=darksouls3.maps.constants,

        havok_module=HavokModule.hk2014,
        # TODO: Not yet supported, but doable.
        skeleton_hkx_class=None,
        animation_hkx_class=None,
        supports_collision_model=False,  # TODO: could at least read hknp meshes
    ),
    SEKIRO: BlenderGameConfig(
        flver_default_version=FLVERVersion.Sekiro_EldenRing,
        matdef_class=None,  # TODO: not in Soulstruct yet

        msb_class=None,  # TODO: not in Soulstruct yet

        havok_module=HavokModule.hk2016,
        skeleton_hkx_class=hk_fromsoft.sekiro.SkeletonHKX,
        animation_hkx_class=hk_fromsoft.sekiro.AnimationHKX,
        supports_collision_model=False,
    ),
    ELDEN_RING: BlenderGameConfig(
        flver_default_version=FLVERVersion.Sekiro_EldenRing,
        uses_matbin=True,  # first game to use MATBIN rather than MTD
        matdef_class=eldenring.models.MatDef,

        msb_class=eldenring.maps.MSB,
        map_constants=eldenring.maps.constants,

        havok_module=HavokModule.hk2018,
        skeleton_hkx_class=hk_fromsoft.eldenring.SkeletonHKX,
        animation_hkx_class=hk_fromsoft.eldenring.AnimationHKX,
        supports_collision_model=False,
    ),
}
