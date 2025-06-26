from __future__ import annotations

__all__ = [
    "BlenderImageFormat",
    "BlenderDDSFormat",
]

from enum import StrEnum


class BlenderImageFormat(StrEnum):
    """Supported Blender image formats (for assignment to `Image.file_format`)."""

    TARGA = "TARGA"
    PNG = "PNG"

    def get_suffix(self) -> str:
        if self.value == "TARGA":
            return ".tga"
        # Other formats just need lower case.
        return f".{self.value.lower()}"


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
