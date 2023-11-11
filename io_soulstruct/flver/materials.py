from __future__ import annotations

__all__ = [
    "BaseMaterialShaderInfo",
    "DS1MaterialShaderInfo",
    "get_submesh_blender_material",
]

import abc
import re
import typing as tp
from dataclasses import dataclass, field
from pathlib import Path

import bpy

from soulstruct.base.models.flver.material import Material
from soulstruct.base.models.flver.submesh import Submesh
from soulstruct.base.models.flver.vertex_array import *
from soulstruct.base.models.mtd import MTD, MTDShaderCategory
from soulstruct.darksouls1r.models.mtd import MTDBND
from soulstruct.eldenring.models.matbin import MATBIN, MATBINBND

from io_soulstruct.utilities.operators import LoggingOperator


@dataclass(slots=True)
class BaseMaterialShaderInfo(abc.ABC):
    """Various summarized properties that tell Soulstruct how to generate FLVER vertex array layouts and Blender
    shader node trees (for appearance purposes only!)."""

    # List of sampler types that FLVER material is expected to have, in order.
    sampler_types: list[str] = field(default_factory=list)
    # Ordered dict mapping texture type names like 'g_Diffuse' to their FLVER vertex UV index/Blender layer (1-indexed).
    sampler_type_uv_indices: dict[str, int] = field(default_factory=dict)

    # Unknown value to write to generated `VertexArrayLayout` elements.
    type_unk_x00: int = 0

    alpha: bool = False
    edge: bool = False
    spec: bool = False

    # region Abstract Methods/Properties

    @abc.abstractmethod
    def get_uv_layer_names(self) -> list[str]:
        ...

    @property
    @abc.abstractmethod
    def is_water(self) -> bool:
        ...

    @property
    @abc.abstractmethod
    def slot_count(self) -> int:
        ...

    # endregion


@dataclass(slots=True)
class DS1MaterialShaderInfo(BaseMaterialShaderInfo):

    MTD_DSBH_RE: tp.ClassVar[re.Pattern] = re.compile(r".*\[(D)?(S)?(B)?(H)?\].*")  # TODO: support 'T' (translucency)
    MTD_M_RE: tp.ClassVar[re.Pattern] = re.compile(r".*\[(M|ML|LM)\].*")  # two texture slots (Multiple)
    MTD_L_RE: tp.ClassVar[re.Pattern] = re.compile(r".*\[(L|ML|LM)\].*")  # lightmap texture slot
    MTD_N_RE: tp.ClassVar[re.Pattern] = re.compile(r".*\[(N|NL|LN)\].*")  # unshaded
    MTD_Dn_RE: tp.ClassVar[re.Pattern] = re.compile(r".*\[Dn\].*")  # unshaded
    # Checked separately: [Dn] (g_Diffuse only), [We] (g_Bumpmap only)

    # TODO: Hardcoding a set of 'foliage' shader prefixes I've encountered in DSR.
    MTD_FOLIAGE_PREFIXES: tp.ClassVar[set[str]] = {
        "M_2Foliage",
    }
    MTD_IVY_PREFIXES: tp.ClassVar[set[str]] = {
        "M_3Ivy",
    }

    # All MTD stems in DSR that use a 'FRPG_Water*' SPX shader but don't have [We] in their name.
    WATER_STEMS: tp.ClassVar[set[str]] = {
        "M_5Water[B]",  # FRPG_Water_Reflect
        "A10_00_Water_drainage",  # FRPG_Water_Reflect
        "A10_01_Water[B]",  # FRPG_Water_Reflect
        "A11_Water[W]",  # FRPG_Water_Reflect
        "A12_Little River",  # FRPG_Water_Reflect
        "A12_River",  # FRPG_Water_Reflect
        "A12_River_No reflect",  # FRPG_Water_Reflect
        "A12_Water",  # FRPG_Water_Reflect
        "A12_Water_lake",  # FRPG_Water_Reflect
        "A14Water[B]",  # FRPG_Water_Reflect
        "S[DB]_Alp_water",  # FRPG_WaterWaveSfx
        "A12_DarkRiver",  # FRPG_Water_Reflect
        "A12_DarkWater",  # FRPG_Water_Reflect
        "A12_NewWater",  # FRPG_Water_Reflect
        "A12_Water_boss",  # FRPG_Water_Reflect
    }

    SNOW_STEMS: tp.ClassVar[set[str]] = {
        "M_8Snow",  # FRPG_Snow
        "A10_slime[D][L]",  # FRPG_Snow_Lit
        "A11_Snow",  # FRPG_Snow
        "A11_Snow[L]",  # FRPG_Snow_Lit
        "A11_Snow_stair",  # FRPG_Snow
        "A11_Snow_stair[L]",  # FRPG_Snow_Lit
        "A14_numa",  # FRPG_Snow (Blighttown swamp)
        "A14_numa2",  # FRPG_Snow (Blighttown swamp)
        "A15_Tar",  # FRPG_Snow
        "A18_ash",  # FRPG_Snow
        "A19_Snow",  # FRPG_Snow
        "A19_Snow[L]",  # FRPG_Snow_Lit
    }

    # Subset of `SNOW_STEMS` that use a 'FRPG_Snow*' SPX shader and also have a 'g_SnowMetalMask' param and an extra
    # 'g_Bumpmap_3' texture type.
    SNOW_METAL_MASK_STEMS: tp.ClassVar[set[str]] = {
        "A10_slime[D][L]",  # FRPG_Snow_Lit
        "A11_Snow",  # FRPG_Snow
        "A11_Snow[L]",  # FRPG_Snow_Lit
        "A11_Snow_stair",  # FRPG_Snow
        "A11_Snow_stair[L]",  # FRPG_Snow_Lit
        "A14_numa",  # FRPG_Snow (Blighttown swamp)
        "A14_numa2",  # FRPG_Snow (Blighttown swamp)
        "A15_Tar",  # FRPG_Snow
        "A19_Snow",  # FRPG_Snow
        "A19_Snow[L]",  # FRPG_Snow_Lit
    }

    # Non-[Dn] MTD names that use `FRPG_NormalToAlpha` shader. Only one case in DS1R.
    NORMAL_TO_ALPHA_STEMS: tp.ClassVar[set[str]] = {
        "M_Tree[D]_Edge",
    }

    # TODO: Some shaders simply don't use the always-empty 'g_DetailBumpmap', but I can find no reliable way to detect
    #  this from their MTD names alone. I may have to guess that they do unless the MTD file is provided.

    detb: bool = False  # I don't think these shaders are used in DS1. Also `g_EnvSpcSlotNo = 2`...
    shader_category: MTDShaderCategory = MTDShaderCategory.PHN

    # Has one or two extra 'g_Bumpmap' textures and 'g_Snow[Roughness/MetalMask/DiffuseF0]' params.
    # Differs in PTDE vs. DS1R.
    has_snow_roughness: bool = False

    @classmethod
    def from_mtd(cls, mtd: MTD):
        """Extract critical MTD information (mainly for generating FLVER vertex array layouts) directly from MTD.

        NOTES:
            - There are only a couple dozen different shaders (SPX) used by all MTDs.
            - All FLVER vertex arrays have normals, at least one vertex color.
        """

        info = cls()

        info.shader_category = mtd.shader_category

        for sampler in mtd.samplers:
            # NOTE: Each MTD may not use certain UV indices -- e.g. 'g_Lightmap' always uses UV index 3, even if there
            # is no second texture slot to use UV index 2. This is obviously desirable to keep the same UV layouts
            # together, and we do the same in Blender.
            info.sampler_types.append(sampler.sampler_type)
            if info.shader_category == MTDShaderCategory.SNOW and sampler.sampler_type == "g_Bumpmap_2":
                # Unfortunate known case of LIES in DS1. This texture says it uses UV index 2 (1-indexed) but actually
                # uses the first UV index, even if you add a second UV array manually.
                info.sampler_type_uv_indices[sampler.sampler_type] = 1  # 1-indexed!
            else:
                info.sampler_type_uv_indices[sampler.sampler_type] = sampler.uv_index  # 1-indexed!

        blend_mode = mtd.get_param("g_BlendMode", default=0)
        if blend_mode == 1:
            info.edge = True
        elif blend_mode == 2:
            info.alpha = True

        env_spc_slot_no = mtd.get_param("g_EnvSpcSlotNo", default=0)
        if env_spc_slot_no == 1:
            info.spec = True

        detail_bump_power = mtd.get_param("g_DetailBump_BumpPower", default=0.0)
        if detail_bump_power > 0.0:
            info.detb = True

        # TODO: PTDE and DS1R differ here. Only the latter uses 'g_Bumpmap_3'.
        info.has_snow_roughness = mtd.has_param("g_SnowRoughness")  # only present in some Snow shaders

        return info

    @classmethod
    def from_mtd_name(cls, mtd_name, operator: LoggingOperator):
        """Guess as much information about the shader as possible purely from its name.

        Obviously, getting the texture names right is the most important part, but we can also guess whether the shader
        uses a lightmap (L), two texture slots (M), or has extra features like alpha (Alp/Edge).
        """
        info = cls()
        mtd_stem = Path(mtd_name).stem

        if dsbh_match := cls.MTD_DSBH_RE.match(mtd_stem):
            if dsbh_match.group(1):
                info.sampler_types.append("g_Diffuse")
                info.sampler_type_uv_indices["g_Diffuse"] = 1
            if dsbh_match.group(2):
                info.sampler_types.append("g_Specular")
                info.sampler_type_uv_indices["g_Specular"] = 1
            if dsbh_match.group(3):
                info.sampler_types.append("g_Bumpmap")
                info.sampler_type_uv_indices["g_Bumpmap"] = 1
            if dsbh_match.group(4):
                info.sampler_types.append("g_Height")
                info.sampler_type_uv_indices["g_Height"] = 1
        elif "[Dn]" in mtd_stem or cls.MTD_N_RE.match(mtd_stem) or mtd_stem in cls.NORMAL_TO_ALPHA_STEMS:
            # Unshaded skyboxes, mist, some trees, etc.
            info.sampler_types.append("g_Diffuse")
            info.sampler_type_uv_indices["g_Diffuse"] = 1
        elif "[We]" in mtd_stem or mtd_stem in cls.WATER_STEMS:
            # Water has a Bumpmap only.
            info.sampler_types.append("g_Bumpmap")
            info.sampler_type_uv_indices["g_Bumpmap"] = 1
        else:
            operator.warning(
                f"Unusual MTD name '{mtd_name}' could not be parsed for its textures. You may need to define it in "
                f"your own custom MTD/MTDBND."
            )

        if cls.MTD_M_RE.match(mtd_stem):
            for sampler_type, _ in info.sampler_type_uv_indices:
                # Second slot for each texture type.
                info.sampler_types.append(sampler_type + "_2")
                info.sampler_type_uv_indices[sampler_type + "_2"] = 2

        if cls.MTD_L_RE.match(mtd_stem):
            # Lightmap is present. Slot is 3 even if there's no second texture slot.
            info.sampler_types.append("g_Lightmap")
            info.sampler_type_uv_indices["g_Lightmap"] = 3

        if "[We]" in mtd_stem or mtd_stem in cls.WATER_STEMS:
            info.shader_category = MTDShaderCategory.WATER
        elif any(mtd_name.startswith(prefix) for prefix in cls.MTD_FOLIAGE_PREFIXES):
            # Has two extra UV slots.
            info.shader_category = MTDShaderCategory.FOLIAGE
        elif any(mtd_name.startswith(prefix) for prefix in cls.MTD_IVY_PREFIXES):
            # Has two extra UV slots.
            info.shader_category = MTDShaderCategory.IVY
        elif mtd_stem in cls.SNOW_STEMS:
            info.shader_category = MTDShaderCategory.SNOW
            # Could have an extra 'g_Bumpmap_3' texture type.
            info.has_snow_roughness = mtd_stem in cls.SNOW_METAL_MASK_STEMS
        else:
            # TODO: Can't distinguish between `Phn` and `Sfx` based on name?
            info.shader_category = MTDShaderCategory.PHN

        info.alpha = "_Alp" in mtd_name
        info.edge = "_Edge" in mtd_name
        info.spec = "_Spec" in mtd_name
        info.detb = "_DetB" in mtd_name

        if "g_Bumpmap" in info.sampler_type_uv_indices:
            # Add useless 'g_DetailBumpmap' for completion.
            # TODO: Some shaders, even with 'g_Bumpmap', do not have this. I have no way to detect from the name.
            #  Currently assuming that it doesn't matter at all if FLVERs have an (empty) texture definition for it.
            info.sampler_types.append("g_DetailBumpmap")
            info.sampler_type_uv_indices["g_DetailBumpmap"] = 1  # always

        return info

    @classmethod
    def from_mtdbnd_or_name(cls, operator: LoggingOperator, mtd_name, mtdbnd: MTDBND = None):
        """Get DS1 material info for a FLVER material, which is needed to determine which material uses which UV
                layers from Blender, and for layout generation.
                """
        if not mtdbnd:
            return DS1MaterialShaderInfo.from_mtd_name(mtd_name, operator)

        # Use real MTD file (much less guesswork).
        try:
            mtd = mtdbnd.mtds[mtd_name]
        except KeyError:
            operator.warning(
                f"Could not find MTD '{mtd_name}' in MTD dict. Guessing info from name."
            )
            return DS1MaterialShaderInfo.from_mtd_name(mtd_name, operator)
        return DS1MaterialShaderInfo.from_mtd(mtd)

    def get_uv_layer_names(self) -> list[str]:
        """Determine Blender UV layer names, which should correspond with the length of each vertex UV list."""
        uv_layer_names = []
        sorted_uv_indices = sorted(self.sampler_type_uv_indices.values())
        for uv_index in sorted_uv_indices:
            name = f"UVMap{uv_index}"
            if name not in uv_layer_names:
                uv_layer_names.append(name)

        if self.shader_category in {MTDShaderCategory.FOLIAGE, MTDShaderCategory.IVY}:
            # Add extra UV layers for plant wind animation control.
            uv_layer_names.extend(["UVMapWindA", "UVMapWindB"])

        return uv_layer_names

    @property
    def slot_count(self) -> int:
        return sum([sampler_type.startswith("g_Diffuse") for sampler_type in self.sampler_types])

    @property
    def is_water(self):
        return self.shader_category == MTDShaderCategory.WATER

    @property
    def has_tangent(self):
        """Present IFF bumpmaps are present."""
        return any(sampler.startswith("g_Bumpmap") for sampler in self.sampler_type_uv_indices)

    @property
    def has_bitangent(self):
        """Present IFF multiple bumpmaps are present (excluding extra bumpmaps for Snow shader roughness)."""
        return self.has_tangent and self.slot_count == 2

    @property
    def has_lightmap(self):
        return "g_Lightmap" in self.sampler_type_uv_indices

    @property
    def has_detail_bumpmap(self):
        return "g_DetailBumpmap" in self.sampler_type_uv_indices

    def get_map_piece_layout(self) -> VertexArrayLayout:
        """Get a standard DS1 map piece layout."""

        data_types = [  # always present
            VertexPosition(VertexDataFormatEnum.Float3, 0),
            VertexBoneIndices(VertexDataFormatEnum.FourBytesB, 0),
            VertexNormal(VertexDataFormatEnum.FourBytesC, 0),
            # Tangent/Bitangent will be inserted here if needed.
            VertexColor(VertexDataFormatEnum.FourBytesC, 0),
            # UV/UVPair will be inserted here if needed.
        ]

        if self.has_tangent:
            data_types.insert(3, VertexTangent(VertexDataFormatEnum.FourBytesC, 0))
            if self.slot_count > 1:  # still has Bitangent
                # TODO: Why is Bitangent needed for double slots? Does it actually hold a second tangent or something?
                data_types.insert(4, VertexBitangent(VertexDataFormatEnum.FourBytesC, 0))
        elif self.slot_count > 1:  # has Bitangent but not Tangent (probably never happens)
            data_types.insert(3, VertexBitangent(VertexDataFormatEnum.FourBytesC, 0))

        # Calculate total UV map count and use a combination of UVPair and UV format members below.
        uv_count = len(self.get_uv_layer_names())

        if self.shader_category in {MTDShaderCategory.FOLIAGE, MTDShaderCategory.IVY}:
            # Foliage shaders have two extra UV slots for wind animation control.
            uv_count += 2

        if uv_count > 4:
            # TODO: Might be an unnecessary assertion. True for DS1, for sure.
            raise ValueError(f"Cannot have more than 4 UV maps in a vertex array (got {uv_count}).")

        uv_member_index = 0
        while uv_count > 0:  # extra UVs
            # For odd counts, single UV member is added first.
            if uv_count % 2:
                data_types.append(VertexUV(VertexDataFormatEnum.UV, uv_member_index))
                uv_count -= 1
                uv_member_index += 1
            else:  # must be a non-zero even number remaining
                # Use a UVPair member.
                data_types.append(VertexUV(VertexDataFormatEnum.UVPair, uv_member_index))
                uv_count -= 2
                uv_member_index += 1

        for data_type in data_types:
            data_type.unk_x00 = self.type_unk_x00

        return VertexArrayLayout(data_types)

    def get_chr_array_layout(self) -> VertexArrayLayout:
        """Get a standard vertex array layout for character (and probably object) materials in DS1."""
        data_types = [
            VertexPosition(VertexDataFormatEnum.Float3, 0),
            VertexBoneIndices(VertexDataFormatEnum.FourBytesB, 0),
            VertexBoneWeights(VertexDataFormatEnum.FourShortsToFloats, 0),
            VertexNormal(VertexDataFormatEnum.FourBytesC, 0),
            VertexTangent(VertexDataFormatEnum.FourBytesC, 0),
            VertexColor(VertexDataFormatEnum.FourBytesC, 0),
        ]
        # TODO: Assuming no DS1 character material (or any material) has more than two slots.
        if self.slot_count > 1:  # has Bitangent and UVPair
            data_types.insert(5, VertexBitangent(VertexDataFormatEnum.FourBytesC, 0))
            data_types.append(VertexUV(VertexDataFormatEnum.UVPair, 0))
        else:  # one UV
            data_types.append(VertexUV(VertexDataFormatEnum.UV, 0))

        for data_type in data_types:
            data_type.unk_x00 = 0  # DS1

        return VertexArrayLayout(data_types)


@dataclass(slots=True)
class ERMaterialShaderInfo(BaseMaterialShaderInfo):

    shader_stem: str = ""  # e.g. 'M[AMSN_V][Ov_N]'

    # Basic shader stem segments, each in square brackets.
    AMSN_RE: tp.ClassVar[re.Pattern] = re.compile(r".*\[(?P<A>A)?(?P<M>M)?(?P<S>S)?(?P<N>N)?(?P<V>_V)?\].*")
    MULTI_RE: tp.ClassVar[re.Pattern] = re.compile(r".*\[Mb(?P<count>\d)(?P<suffix>_[_\w]+)?\].*")  # 2 to 5 observed
    OV_RE: tp.ClassVar[re.Pattern] = re.compile(r".*\[Ov_(?P<suffix>[_\w]+)\].*")  # e.g. '[Ov_N]'
    FAR_RE: tp.ClassVar[re.Pattern] = re.compile(r".*\[Far_(?P<suffix>[_\w]+)\].*")  # e.g. '[Far_AN]'

    # Special shader types.
    SPIDERWEB_RE: tp.ClassVar[re.Pattern] = re.compile(r".*\[Spiderweb\].*")
    TRANSLUCENCY_RE: tp.ClassVar[re.Pattern] = re.compile(r".*\[Translucency].*")
    WAX_RE: tp.ClassVar[re.Pattern] = re.compile(r".*\[Wax\].*")
    SWAY_RE: tp.ClassVar[re.Pattern] = re.compile(r".*\[Sway\].*")
    MASK_RE: tp.ClassVar[re.Pattern] = re.compile(r".*\[(?P<mask>\d)Mask(?P<suffix>_[_\w]+)?\].*")  # e.g. 'ch18'
    # TODO: A bunch more: Birds, Birds_liner, Flag, Flag2, Flag3, Flower_m10, Interior, PlacidLake, Rainbow, Sky...
    #  Probably easiest to have a simple list of these 'one-word' bracketed labels.

    # Shader suffix patterns.
    # TODO: These never seem to be combined, but potentially could be. Maybe safest to split name by final square
    #  bracket and run a check for '_{suffix}[_$]' for each suffix.
    Alpha_RE: tp.ClassVar[re.Pattern] = re.compile(r".*_Alpha$")
    Edge_RE: tp.ClassVar[re.Pattern] = re.compile(r".*_Edge$")
    Emissive_Glow_RE: tp.ClassVar[re.Pattern] = re.compile(r".*_Emissive_Glow$")
    Grass_RE: tp.ClassVar[re.Pattern] = re.compile(r".*_Grass$")
    Grass2_RE: tp.ClassVar[re.Pattern] = re.compile(r".*_Grass2$")
    Grass2_LOD1_RE: tp.ClassVar[re.Pattern] = re.compile(r".*_Grass2_LOD1$")
    MeshDecalBlend_RE: tp.ClassVar[re.Pattern] = re.compile(r".*_MeshDecalBlend$")
    Skin_PaintDecal_RE: tp.ClassVar[re.Pattern] = re.compile(r".*_Skin_PaintDecal$")
    Vesitation_RE: tp.ClassVar[re.Pattern] = re.compile(r".*_Vesitation$")
    NoLight_RE: tp.ClassVar[re.Pattern] = re.compile(r".*_NoLight.*")  # TODO: seen with '_Alpha' after it

    @classmethod
    def from_matbin(cls, matbin: MATBIN):
        """Extract critical material information directly from MATBIN."""

        info = cls()

        for sampler in matbin.samplers:
            info.sampler_types.append(sampler.sampler_type)
            # TODO: How to detect UV index in ER?

        # Still here, like in MTD.
        blend_mode = matbin.get_param("g_BlendMode", default=0)
        if blend_mode == 1:
            info.edge = True
        elif blend_mode == 2:
            info.alpha = True

        # TODO: Not sure how to detect.
        info.spec = False

        info.shader_stem = matbin.shader_name
        # TODO: Notes.
        #  - The sampler types have prefixes from the shader stem, with square brackets replaced by underscores,
        #  followed by '_snp_', then a meaningful suffix like 'Texture2D_2_AlbedoMap_0'.
        #  - Not sure what 'snp' means, but it could just be 'specular, normal, physical' or something.
        #   - Could also be a mistranslated abbreviation of 'sampler'?
        #  - 'Texture2D' obviously fairly standard.
        #  - The index after that varies. Some kind of slot. Seems always unique, but not always contiguous, and also
        #    kind of random in order (e.g. normal 1, normal 2, albedo 1, albedo 2, mask1map, normal 0).
        #  - Then map type, then 'group' of that map type (but only in the same slot?).
        #   - I know it's 'group' because it corresponds to present 'group_#_CommonUV-UVParam' params.
        #   - Although the numbering doesn't always line up. [Mb2][Ov_N] has three UV 'group' params but has two real
        #     albedo/normal groups plus the extra normal map.
        #  - 'Multi-group' materials appear to have [Mb#] in the shader stem. Have seen 2 and 3 so far.
        #   - They also have 'GSBlendMap' between the index and map type in the sampler type.
        #   - They also have an extra sampler slot with type '_BlendEdge' (extra underscore) or 'Mask1Map'.
        #  - '[Ov_N]' shader suffix seems to be just albedo and normal. No metallic. Has two normals in same group;
        #    possibly 'standard' (7) and 'detailed' (2).
        #  - Shaders with no suffix, like just 'M[AMSN_V], have one albedo and one bumpmap.
        #  - Suffixes can stack: [Mb2][Ov_N] has two albedo/normal groups AND one extra normal (plus 'Mask1Map').
        #  - '[Ov_AN]' suffix has an extra albedo AND normal map (though I've seen the normal map path empty).
        #  - '[Sway]' suffix probably for... swaying stuff like trees. Has a few 'Sway' param floats defined.
        #  - g_BlendMode == 2 for alpha, 0 otherwise. Have seen no other values.
        #  - 'M[A]' has albedo only. Have only seen this used for low-ID materials using dummy SYSTEX textures.
        #  - The V in M[AMSN_V] seems to indicate the ABSENCE of metallic textures.

        # TODO: Action items.
        #  - First order, to get import working, is just to detect basic shader setups in the same way as DS1.
        #   - Need to handle multi-groups, name textures appropriately, and find DDS textures in AET binders.
        #   - Node tree builder below

        return info

    @classmethod
    def from_matbin_name(cls, matbin_name, operator: LoggingOperator):
        """Guess as much information about the shader as possible purely from its name.

        Obviously, getting the texture names right is the most important part, but we can also guess whether the shader
        uses a lightmap (L), two texture slots (M), or has extra features like alpha (Alp/Edge).
        """
        # TODO: Make regex for this.
        info = cls()
        mtd_stem = Path(matbin_name).stem

        if dsbh_match := cls.MTD_DSBH_RE.match(mtd_stem):
            if dsbh_match.group(1):
                info.sampler_types.append("g_Diffuse")
                info.sampler_type_uv_indices["g_Diffuse"] = 1
            if dsbh_match.group(2):
                info.sampler_types.append("g_Specular")
                info.sampler_type_uv_indices["g_Specular"] = 1
            if dsbh_match.group(3):
                info.sampler_types.append("g_Bumpmap")
                info.sampler_type_uv_indices["g_Bumpmap"] = 1
            if dsbh_match.group(4):
                info.sampler_types.append("g_Height")
                info.sampler_type_uv_indices["g_Height"] = 1
        elif "[Dn]" in mtd_stem or cls.MTD_N_RE.match(mtd_stem) or mtd_stem in cls.NORMAL_TO_ALPHA_STEMS:
            # Unshaded skyboxes, mist, some trees, etc.
            info.sampler_types.append("g_Diffuse")
            info.sampler_type_uv_indices["g_Diffuse"] = 1
        elif "[We]" in mtd_stem or mtd_stem in cls.WATER_STEMS:
            # Water has a Bumpmap only.
            info.sampler_types.append("g_Bumpmap")
            info.sampler_type_uv_indices["g_Bumpmap"] = 1
        else:
            operator.warning(
                f"Unusual MTD name '{matbin_name}' could not be parsed for its textures. You may need to define it in "
                f"your own custom MTD/MTDBND."
            )

        if cls.MTD_M_RE.match(mtd_stem):
            for sampler_type in info.sampler_types:
                # Second slot for each texture type.
                info.sampler_types.append(sampler_type + "_2")
                info.sampler_type_uv_indices[sampler_type + "_2"] = 2

        if cls.MTD_L_RE.match(mtd_stem):
            # Lightmap is present. Slot is 3 even if there's no second texture slot.
            info.sampler_types.append("g_Lightmap")
            info.sampler_type_uv_indices["g_Lightmap"] = 3

        if "[We]" in mtd_stem or mtd_stem in cls.WATER_STEMS:
            info.shader_category = MTDShaderCategory.WATER
        elif any(matbin_name.startswith(prefix) for prefix in cls.MTD_FOLIAGE_PREFIXES):
            # Has two extra UV slots.
            info.shader_category = MTDShaderCategory.FOLIAGE
        elif any(matbin_name.startswith(prefix) for prefix in cls.MTD_IVY_PREFIXES):
            # Has two extra UV slots.
            info.shader_category = MTDShaderCategory.IVY
        elif mtd_stem in cls.SNOW_STEMS:
            info.shader_category = MTDShaderCategory.SNOW
            # Could have an extra 'g_Bumpmap_3' texture type.
            info.has_snow_roughness = mtd_stem in cls.SNOW_METAL_MASK_STEMS
        else:
            # TODO: Can't distinguish between `Phn` and `Sfx` based on name?
            info.shader_category = MTDShaderCategory.PHN

        info.alpha = "_Alp" in matbin_name
        info.edge = "_Edge" in matbin_name
        info.spec = "_Spec" in matbin_name
        info.detb = "_DetB" in matbin_name

        if "g_Bumpmap" in info.sampler_types:
            # Add useless 'g_DetailBumpmap' for completion.
            # TODO: Some shaders, even with 'g_Bumpmap', do not have this. I have no way to detect from the name.
            #  Currently assuming that it doesn't matter at all if FLVERs have an (empty) texture definition for it.
            info.sampler_types.append("g_DetailBumpmap")
            info.sampler_type_uv_indices["g_DetailBumpmap"] = 1  # always

        return info

    @classmethod
    def from_matbin_name_or_matbinbnd(cls, operator: LoggingOperator, matbin_name: str, matbinbnd: MATBINBND = None):
        """Get info for a FLVER material, which is needed for both material creation and assignment of vertex UV
        data to the correct Blender UV data layer during mesh creation.
        """
        if not matbinbnd:
            raise NotImplementedError("Cannot yet guess MATBIN info from name. MATBINBND must be given.")

        # Use real MATBIN file (much less guesswork -- currently required).
        try:
            matbin = matbinbnd.get_matbin(matbin_name)
        except KeyError:
            raise NotImplementedError(f"Could not find MATBIN '{matbin_name}' in MATBINBND and cannot yet guess info.")
        return cls.from_matbin(matbin)

    def get_uv_layer_names(self) -> list[str]:
        """Determine Blender UV layer names, which should correspond with the length of each vertex UV list."""
        # TODO

    @property
    def slot_count(self) -> int:
        # TODO: Not sure if can be detected from sampler types alone (generically).
        return 1

    @property
    def is_water(self):
        return self.shader_category == MTDShaderCategory.WATER

    @property
    def has_tangent(self):
        """Present IFF bumpmaps are present."""
        return any(texture_type.startswith("g_Bumpmap") for texture_type in self.sampler_types)

    @property
    def has_bitangent(self):
        """Present IFF multiple bumpmaps are present (excluding extra bumpmaps for Snow shader roughness)."""
        return self.has_tangent and self.slot_count > 1

    @property
    def has_lightmap(self):
        return "g_Lightmap" in self.sampler_types

    @property
    def has_detail_bumpmap(self):
        return "g_DetailBumpmap" in self.sampler_types

    def get_map_piece_layout(self) -> VertexArrayLayout:
        """Get a standard DS1 map piece layout."""

        data_types = [  # always present
            VertexPosition(VertexDataFormatEnum.Float3, 0),
            VertexBoneIndices(VertexDataFormatEnum.FourBytesB, 0),
            VertexNormal(VertexDataFormatEnum.FourBytesC, 0),
            # Tangent/Bitangent will be inserted here if needed.
            VertexColor(VertexDataFormatEnum.FourBytesC, 0),
            # UV/UVPair will be inserted here if needed.
        ]

        if self.has_tangent:
            data_types.insert(3, VertexTangent(VertexDataFormatEnum.FourBytesC, 0))
            if self.slot_count > 1:  # still has Bitangent
                # TODO: Why is Bitangent needed for double slots? Does it actually hold a second tangent or something?
                data_types.insert(4, VertexBitangent(VertexDataFormatEnum.FourBytesC, 0))
        elif self.slot_count > 1:  # has Bitangent but not Tangent (probably never happens)
            data_types.insert(3, VertexBitangent(VertexDataFormatEnum.FourBytesC, 0))

        # Calculate total UV map count and use a combination of UVPair and UV format members below.
        uv_count = self.slot_count + int(self.has_lightmap)

        if self.shader_category in {MTDShaderCategory.FOLIAGE, MTDShaderCategory.IVY}:
            # Foliage shaders have two extra UV slots for wind animation control.
            uv_count += 2

        if uv_count > 4:
            # TODO: Might be an unnecessary assertion. True for DS1, for sure.
            raise ValueError(f"Cannot have more than 4 UV maps in a vertex array (got {uv_count}).")

        uv_member_index = 0
        while uv_count > 0:  # extra UVs
            # For odd counts, single UV member is added first.
            if uv_count % 2:
                data_types.append(VertexUV(VertexDataFormatEnum.UV, uv_member_index))
                uv_count -= 1
                uv_member_index += 1
            else:  # must be a non-zero even number remaining
                # Use a UVPair member.
                data_types.append(VertexUV(VertexDataFormatEnum.UVPair, uv_member_index))
                uv_count -= 2
                uv_member_index += 1

        for data_type in data_types:
            data_type.unk_x00 = self.type_unk_x00

        return VertexArrayLayout(data_types)

    def get_character_layout(self) -> VertexArrayLayout:
        """Get a standard vertex array layout for character (and probably object) materials in DS1."""
        data_types = [
            VertexPosition(VertexDataFormatEnum.Float3, 0),
            VertexBoneIndices(VertexDataFormatEnum.FourBytesB, 0),
            VertexBoneWeights(VertexDataFormatEnum.FourShortsToFloats, 0),
            VertexNormal(VertexDataFormatEnum.FourBytesC, 0),
            VertexTangent(VertexDataFormatEnum.FourBytesC, 0),
            VertexColor(VertexDataFormatEnum.FourBytesC, 0),
        ]
        if self.slot_count > 1:  # has Bitangent and UVPair
            data_types.insert(5, VertexBitangent(VertexDataFormatEnum.FourBytesC, 0))
            data_types.append(VertexUV(VertexDataFormatEnum.UVPair, 0))
        else:  # one UV
            data_types.append(VertexUV(VertexDataFormatEnum.UV, 0))

        for data_type in data_types:
            data_type.unk_x00 = self.type_unk_x00

        return VertexArrayLayout(data_types)


def get_submesh_blender_material(
    operator: LoggingOperator,
    material: Material,
    material_name: str,
    material_info: BaseMaterialShaderInfo,
    submesh: Submesh,
    blend_mode="HASHED",
) -> bpy.types.Material:
    """Create a new material in the current Blender scene from a FLVER material.

    Will use material texture stems to search for PNG or DDS images in the Blender image data. If no image is found,
    the texture will be left unassigned in the material.
    """

    bl_material = bpy.data.materials.new(name=material_name)
    bl_material.use_nodes = True
    if blend_mode:
        bl_material.blend_method = blend_mode

    # Critical `Material` information stored in custom properties.
    bl_material["Flags"] = material.flags  # int
    bl_material["MTD Path"] = material.mtd_path  # str
    bl_material["Unk x18"] = material.unk_x18  # int
    # NOTE: Texture path prefixes not stored, as they aren't actually needed in the TPFBHDs.

    # Store GX items as custom properties 'array', except the final dummy array.
    for i, gx_item in enumerate(material.gx_items):
        if gx_item.is_dummy:
            continue  # ignore dummy items
        try:
            bl_material[f"GXItem[{i}] Category"] = gx_item.category.decode()
        except UnicodeDecodeError:
            operator.warning(f"Could not decode GXItem {i} category: {gx_item.category}. Storing empty string.")
            bl_material[f"GXItem[{i}] Category"] = ""
        bl_material[f"GXItem[{i}] Index"] = gx_item.index
        bl_material[f"GXItem[{i}] Data"] = repr(gx_item.data)

    node_tree = bl_material.node_tree
    node_tree.nodes.remove(node_tree.nodes["Principled BSDF"])
    node_tree.links.clear()
    output_node = node_tree.nodes["Material Output"]
    builder = NodeTreeBuilder(node_tree)

    vertex_colors_node = builder.add_vertex_colors_node()
    uv_nodes = {}
    tex_image_nodes = {}  # type: dict[str, bpy.types.Node]
    bsdf_nodes = [None, None]  # type: list[bpy.types.Node | None]

    missing_textures = list(material_info.sampler_types)
    for texture_type, texture in material.get_texture_dict().items():
        if texture_type not in material_info.sampler_types:
            operator.warning(
                f"Texture type '{texture_type}' does not seem to be supported by shader '{material.mtd_name}'. "
                f"Creating FLVER material texture node anyway (with no UV input).",
            )
            uv_index = None
        elif texture_type not in missing_textures:
            operator.warning(
                f"Texture type '{texture_type}' occurred multiple times in FLVER material, which is invalid. Please "
                f"repair this corrupt FLVER file. Ignoring this texture.",
            )
            continue
        else:
            missing_textures.remove(texture_type)
            uv_index = material_info.sampler_type_uv_indices[texture_type]

        if not texture.path:
            # Empty texture in FLVER (e.g. 'g_DetailBumpmap' in every single DS1 FLVER).
            tex_image_node = builder.add_tex_image_node(texture_type, None)
            tex_image_nodes[texture_type] = tex_image_node
            continue

        # Try to find texture in Blender image data as a PNG (preferred) or DDS.
        # TODO: 'DetailBump_01_n' texture seems to always be missing from characters' `g_DetailBumpmap` slot. Handle?
        #  I think it's in some common texture bunch, potentially?

        for image_name in (f"{texture.stem}", f"{texture.stem}.png", f"{texture.stem}.dds"):
            if image_name in bpy.data.images:
                bl_image = bpy.data.images[image_name]
                break
        else:
            # Create empty Blender image.
            bl_image = bpy.data.images.new(name=texture.stem, width=1, height=1, alpha=True)
            bl_image.pixels = [1.0, 0.0, 1.0, 1.0]  # magenta
            operator.warning(
                f"Could not find texture '{texture.stem}' in Blender image data. Created 1x1 magenta texture for node."
            )

        tex_image_node = builder.add_tex_image_node(texture_type, bl_image)
        tex_image_nodes[texture_type] = tex_image_node

        if uv_index is not None:
            # Connect to appropriate UV node, creating it if necessary.
            uv_map_name = f"UVMap{uv_index}"
            if uv_map_name in uv_nodes:
                uv_node = uv_nodes[uv_map_name]
            else:
                uv_node = uv_nodes[uv_map_name] = builder.add_uv_node(uv_map_name)
            builder.link(uv_node.outputs["Vector"], tex_image_node.inputs["Vector"])

    if material_info.is_water:
        # Special simplified shader. Uses 'g_Bumpmap' only.
        water_mix = builder.new("ShaderNodeMixShader", (builder.MIX_X, builder.MIX_Y))
        transparent = builder.new("ShaderNodeBsdfTransparent", (builder.BSDF_X, builder.MIX_Y))
        glass = builder.new("ShaderNodeBsdfGlass", (builder.BSDF_X, 1000), input_defaults={"IOR": 1.333})
        builder.link(transparent.outputs[0], water_mix.inputs[1])
        builder.link(glass.outputs[0], water_mix.inputs[2])

        bumpmap_node = tex_image_nodes["g_Bumpmap"]
        normal_map_node = builder.add_normal_map_node("UVMap1", bumpmap_node.location[1])

        builder.link(bumpmap_node.outputs["Color"], normal_map_node.inputs["Color"])
        builder.link(normal_map_node.outputs["Normal"], glass.inputs["Normal"])
        builder.link(vertex_colors_node.outputs["Alpha"], water_mix.inputs["Fac"])
        return bl_material

    # TODO: Sketch for snow shader:
    #  - Create a Diffuse BSDF shader with HSV (0.75, 0.3, 1.0) (blue tint).
    #  - Mix g_Bumpmap_2 and (if present) g_Bumpmap_3 with Mix RGB.
    #  - Plug that into Normal Map using UVMap1 (always UVMap1, regardless of what MTD says - though this is handled).
    #  - Create a Mix Shader for the standard textures and new Diffuse snow BSDF. Plug into material output.
    #  - Use Math node to raise VertexColors alpha to exponent 10 and use that as Fac of the Mix Shader.
    #     - This shows roughly where the snow will be created without completely obscuring the underlying texture.
    #  - If a lightmap is present, instead mix that mix shader with it!

    # Standard shader: one or two Principled BSDFs mixed 50/50, or one Principled BSDF mixed with a Transparent BSDF
    # for alpha-supporting shaders (includes edge shaders currently).
    bsdf_nodes[0] = builder.add_principled_bsdf_node("Texture Slot 1")
    if material_info.slot_count > 1:
        if material_info.slot_count > 2:
            operator.warning("Cannot yet set up Blender shader for more than two texture groups.")
        bsdf_nodes[1] = builder.add_principled_bsdf_node("Texture Slot 1")
        mix_node = builder.new("ShaderNodeMixShader", location=(builder.MIX_X, builder.MIX_Y))
        builder.link(bsdf_nodes[0].outputs["BSDF"], mix_node.inputs[1])
        builder.link(bsdf_nodes[1].outputs["BSDF"], mix_node.inputs[2])
        builder.link(vertex_colors_node.outputs["Alpha"], mix_node.inputs["Fac"])
        builder.link(mix_node.outputs["Shader"], output_node.inputs["Surface"])
    elif material_info.alpha or material_info.edge:
        # Mix main Principled BSDF with a Transparent BSDF using vertex alpha.
        # TODO: Assumes single BSDF; will not render with second texture slot at all. Confirm 'M' shaders never use Alp.
        transparent_node = builder.new("ShaderNodeBsdfTransparent", location=(builder.BSDF_X, builder.bsdf_y))
        mix_node = builder.new("ShaderNodeMixShader", location=(builder.MIX_X, builder.MIX_Y))
        builder.link(transparent_node.outputs["BSDF"], mix_node.inputs[1])
        builder.link(bsdf_nodes[0].outputs["BSDF"], mix_node.inputs[2])  # more vertex alpha -> more opacity
        builder.link(vertex_colors_node.outputs["Alpha"], mix_node.inputs["Fac"])
        builder.link(mix_node.outputs["Shader"], output_node.inputs["Surface"])
    else:
        builder.link(bsdf_nodes[0].outputs["BSDF"], output_node.inputs["Surface"])

    if "g_Lightmap" in tex_image_nodes:
        lightmap_node = tex_image_nodes["g_Lightmap"]
        for texture_type in ("g_Diffuse", "g_Specular", "g_Diffuse_2", "g_Specular_2"):
            if texture_type not in tex_image_nodes:
                continue
            bsdf_node = bsdf_nodes[1] if texture_type.endswith("_2") else bsdf_nodes[0]
            if bsdf_node is None:
                continue  # TODO: bad state
            tex_image_node = tex_image_nodes[texture_type]
            overlay_node_y = tex_image_node.location[1]
            overlay_node = builder.new(
                "ShaderNodeMixRGB", location=(builder.OVERLAY_X, overlay_node_y), blend_type="OVERLAY"
            )
            builder.link(tex_image_node.outputs["Color"], overlay_node.inputs["Color1"])
            builder.link(lightmap_node.outputs["Color"], overlay_node.inputs["Color2"])  # order is important!

            bsdf_input = "Base Color" if texture_type.startswith("g_Diffuse") else "Specular"
            builder.link(overlay_node.outputs["Color"], bsdf_node.inputs[bsdf_input])
            if texture_type.startswith("g_Diffuse"):
                # Plug diffuse alpha into BSDF alpha.
                builder.link(tex_image_node.outputs["Alpha"], bsdf_node.inputs["Alpha"])
    else:
        # Plug diffuse and specular textures directly into Principled BSDF.
        for texture_type in ("g_Diffuse", "g_Specular", "g_Diffuse_2", "g_Specular_2"):
            if texture_type not in tex_image_nodes:
                continue
            bsdf_node = bsdf_nodes[1] if texture_type.endswith("_2") else bsdf_nodes[0]
            if bsdf_node is None:
                continue  # TODO: bad state
            tex_image_node = tex_image_nodes[texture_type]
            if texture_type.startswith("g_Diffuse"):
                builder.link(tex_image_node.outputs["Color"], bsdf_node.inputs["Base Color"])
                builder.link(tex_image_node.outputs["Alpha"], bsdf_node.inputs["Alpha"])
            else:  # g_Specular[_2]
                builder.link(tex_image_node.outputs["Color"], bsdf_node.inputs["Specular"])

    if "g_Height" in tex_image_nodes:
        # 'g_Height' is an actual height map (not normals, like 'g_Bumpmap').
        height_node = tex_image_nodes["g_Height"]
        # NOTE: In my observation so far, this always uses UVMap1 (i.e. never the second texture in a two-slot mat).
        builder.link(uv_nodes["UVMap1"].outputs["Vector"], height_node.inputs["Vector"])
        builder.link(height_node.outputs["Color"], output_node.inputs["Displacement"])

    for texture_type, bsdf_node in zip(("g_Bumpmap", "g_Bumpmap_2"), bsdf_nodes):
        if texture_type not in tex_image_nodes or texture_type not in material_info.sampler_types:
            continue
        if bsdf_node is None:
            continue  # TODO: bad state
        # Create normal map node.
        bumpmap_node = tex_image_nodes[texture_type]
        uv_index = material_info.sampler_type_uv_indices[texture_type]
        uv_map_name = f"UVMap{uv_index}"
        normal_map_node = builder.add_normal_map_node(uv_map_name, bumpmap_node.location[1])
        builder.link(bumpmap_node.outputs["Color"], normal_map_node.inputs["Color"])
        builder.link(normal_map_node.outputs["Normal"], bsdf_node.inputs["Normal"])

    # Set additional real and custom properties from FLVER submesh.
    bl_material["Is Bind Pose"] = submesh.is_bind_pose
    # NOTE: This index is sometimes invalid for vanilla map FLVERs (e.g., 1 when there is only one bone).
    bl_material["Default Bone Index"] = submesh.default_bone_index
    # Currently, main face set is simply copied to all additional face sets on export.
    bl_material["Face Set Count"] = len(submesh.face_sets)
    bl_material.use_backface_culling = submesh.use_backface_culling

    return bl_material


class NodeTreeBuilder:
    """Wraps a Blender `NodeTree` and adds utility methods for creating/linking nodes for FLVER materials."""

    tree: bpy.types.NodeTree

    # X coordinates of node type columns.
    VERTEX_COLORS_X = -950
    UV_X = -750
    TEX_X = -550
    OVERLAY_X = -250  # includes Normal Map node for 'g_Bumpmap'
    BSDF_X = -50
    MIX_X, MIX_Y = 100, 300  # only one (max)

    def __init__(self, node_tree: bpy.types.NodeTree):
        self.tree = node_tree

        # Auto-decremented Y coordinates for each node type (so newer nodes are further down).
        self.uv_y = 1000
        self.tex_y = 1000
        self.bsdf_y = 1000

    def new(
        self, node_type: str, location: tuple[int, int] = None, /, input_defaults: dict[str, tp.Any] = None, **kwargs
    ) -> bpy.types.Node:
        node = self.tree.nodes.new(node_type)
        if location is not None:
            node.location = location
        for k, v in kwargs.items():
            setattr(node, k, v)
        if input_defaults:
            for k, v in input_defaults.items():
                node.inputs[k].default_value = v
        return node

    def link(self, node_output, node_input) -> bpy.types.NodeLink:
        return self.tree.links.new(node_output, node_input)

    def add_vertex_colors_node(self) -> bpy.types.Node:
        return self.new(
            "ShaderNodeAttribute",
            location=(self.OVERLAY_X, 1200),
            name="VertexColors",
            attribute_name="VertexColors",
        )

    def add_uv_node(self, uv_map_name: str):
        """Create an attribute node for the given UV layer name."""
        node = self.new(
            "ShaderNodeAttribute",
            location=(self.UV_X, self.uv_y),
            name=uv_map_name,
            attribute_name=uv_map_name,
            label=uv_map_name,
        )
        self.uv_y -= 1000
        return node

    def add_tex_image_node(self, texture_type: str, image: bpy.types.Image | None):
        node = self.new(
            "ShaderNodeTexImage",
            location=(self.TEX_X, self.tex_y),
            image=image,
            name=texture_type,
            label=texture_type,
        )
        self.tex_y -= 330
        return node

    def add_principled_bsdf_node(self, bsdf_name: str):
        node = self.new(
            "ShaderNodeBsdfPrincipled",
            location=(self.BSDF_X, self.bsdf_y),
            name=bsdf_name,
            input_defaults={"Roughness": 0.75},
        )
        self.bsdf_y -= 1000
        return node

    def add_normal_map_node(self, uv_map_name: str, location_y: float):
        return self.new(
            "ShaderNodeNormalMap",
            location=(self.OVERLAY_X, location_y),
            space="TANGENT",
            uv_map=uv_map_name,
            input_defaults={"Strength": 0.4},
        )
