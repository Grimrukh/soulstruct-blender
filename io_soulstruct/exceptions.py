__all__ = [
    "SoulstructBlenderError",
    "UnsupportedGameError",
    "SoulstructTypeError",
    "FLVERError",
    "FLVERImportError",
    "FLVERExportError",
    "NVMImportError",
    "NavGraphImportError",
    "NavGraphExportError",
    "MissingPartModelError",
    "MissingMSBEntryError",
    "MSBPartImportError",
    "MSBPartExportError",
    "MSBRegionImportError",
]

from soulstruct.exceptions import SoulstructError


class SoulstructBlenderError(SoulstructError):
    """Base error for Blender operations."""
    pass


class UnsupportedGameError(SoulstructBlenderError):
    """Raised when trying to do something not supported for the selected game."""
    pass


class SoulstructTypeError(SoulstructBlenderError):
    """Raised when the `soulstruct_type` of a Blender object is not as expected."""
    pass


class FLVERError(SoulstructBlenderError):
    """Exception raised by a FLVER-based operator error."""


class FLVERImportError(FLVERError):
    """Exception raised during FLVER import."""
    pass


class FLVERExportError(FLVERError):
    """Exception raised during FLVER export."""
    pass


class NVMImportError(SoulstructBlenderError):
    """Exception raised during NVM import."""
    pass


class NavGraphImportError(SoulstructBlenderError):
    """Exception raised during NavGraph import."""
    pass


class NavGraphExportError(SoulstructBlenderError):
    """Exception raised during NavGraph export."""
    pass


class MissingPartModelError(SoulstructBlenderError):
    """Raised when the model for an MSB Part is not set (on export) or cannot be found in Blender."""


class MissingMSBEntryError(SoulstructBlenderError):
    """Raised when a reference MSB entry (by name) is missing from the MSB file on entry export."""
    pass


class MSBPartImportError(SoulstructBlenderError):
    """Raised by any problem with importing an MSB Region instance."""


class MSBPartExportError(SoulstructBlenderError):
    """Raised by any problem with importing an MSB Region instance."""


class MSBRegionImportError(SoulstructBlenderError):
    """Raised by any problem with importing an MSB Region instance."""
