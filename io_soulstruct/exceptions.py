__all__ = [
    "SoulstructBlenderError",
    "UnsupportedGameError",
    "FLVERError",
    "FLVERImportError",
    "FLVERExportError",
    "NVMImportError",
    "NavGraphImportError",
    "NavGraphExportError",
    "MissingPartModelError",
    "MSBRegionImportError",
]

from soulstruct.exceptions import SoulstructError


class SoulstructBlenderError(SoulstructError):
    """Base error for Blender operations."""
    pass


class UnsupportedGameError(SoulstructBlenderError):
    """Raised when trying to do something not supported for the selected game."""
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
    """Raised when the model for an MSB Part cannot be found in a Blender collection."""


class MSBRegionImportError(SoulstructBlenderError):
    """Raised by any problem with importing an MSB Region instance."""
