from __future__ import annotations

__all__ = [
    "DDSTextureProps",
    "TextureExportSettings",
]

import bpy

from soulstruct.containers.tpf import TPFPlatform

from soulstruct.blender.bpy_base.property_group import SoulstructPropertyGroup
from .enums import *


class DDSTextureProps(SoulstructPropertyGroup):
    """Used as `bpy.types.Image.DDS_TEXTURE`."""

    dds_format: bpy.props.EnumProperty(
        name="DDS Format",
        description="DDS compression format for this texture. 'NONE' means DDS cannot export and 'SAME' (default) "
                    "means format will match existing DDS texture that is about to be overwritten",
        items=[
            (BlenderDDSFormat.NONE, "None", "Do not export this texture type"),
            (BlenderDDSFormat.SAME, "Same", "Use same format as overwritten texture (which must exist)"),
            (BlenderDDSFormat.DXT1, "DXT1", "DXT1 (no alpha)"),
            (BlenderDDSFormat.DXT3, "DXT3", "DXT3 (sharp alpha)"),
            (BlenderDDSFormat.DXT5, "DXT5", "DXT5 (smooth alpha)"),
            (BlenderDDSFormat.BC5_UNORM, "BC5", "BC5 (normal map)"),
            (BlenderDDSFormat.BC7_UNORM, "BC7", "BC7 (high quality)"),
        ],
        default=BlenderDDSFormat.SAME,
    )

    tpf_platform: bpy.props.EnumProperty(
        name="Platform",
        description="Platform to export textures for. Currently only PC is supported",
        items=[
            (TPFPlatform.PC.name, "PC", "PC"),
            # ("Xbox360", "Xbox 360", "Xbox 360"),
            # ("PS3", "PS3", "PS3"),
            # ("PS4", "PS4", "PS4"),
            # ("XboxOne", "Xbox One", "Xbox One"),
        ],
        default=TPFPlatform.PC.name,
    )

    mipmap_count: bpy.props.IntProperty(
        name="Mipmap Count",
        description="Number of mipmaps to generate in DDS texture (0 = all mipmaps)",
        default=0,
        min=0,
        max=16,
    )


class TextureExportSettings(SoulstructPropertyGroup):
    """Contains settings and enums that determine DDS compression type for each FLVER texture slot type."""

    overwrite_existing_map_textures: bpy.props.BoolProperty(
        name="Overwrite Existing Map Textures",
        description="Overwrite existing map TPF textures with the same name as exported textures. If False, an error "
                    "will be raised if the texture already exists in the map (to protect you from affecting other Map "
                    "Piece FLVERs). Other FLVER types that bundle their own textures will always be overwritten with "
                    "a complete new texture set. Texture names are not case-sensitive",
        default=True,
    )

    require_power_of_two: bpy.props.BoolProperty(
        name="Require Power of Two Size",
        description="Require that all exported textures have power-of-two dimensions. Even if disabled, this will "
                    "never allow 1-pixel textures to be exported",
        default=True,
    )

    max_chrbnd_tpf_size: bpy.props.IntProperty(
        name="Max CHRBND TPF Size (kB)",
        description="Maximum size (in kB) of TPF bundled inside CHRBND. Characters with total texture size beyond this "
                    "will have their texture data placed in individual TPFs in an adjacent folder (PTDE) or split "
                    "CHRTPFBDT (DSR)",
        default=5000,
    )
