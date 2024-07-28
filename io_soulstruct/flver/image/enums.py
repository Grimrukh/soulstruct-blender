from __future__ import annotations

__all__ = [
    "BlenderDDSFormat",
]

from enum import StrEnum


class BlenderDDSFormat(StrEnum):
    """Options for DDS format choice, including 'NONE' for not exporting a texture type and 'SAME' for trying to match
    the format of an existing DDS that is about to be overwritten."""
    NONE = "NONE"
    SAME = "SAME"
    DXT1 = "DXT1"
    DXT3 = "DXT3"
    DXT5 = "DXT5"
    BC5_UNORM = "BC5_UNORM"
    BC7_UNORM = "BC7_UNORM"
