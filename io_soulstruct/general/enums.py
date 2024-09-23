from __future__ import annotations

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
