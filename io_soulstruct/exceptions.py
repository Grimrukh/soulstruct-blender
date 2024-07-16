__all__ = [
    "SoulstructBlenderError",
    "UnsupportedGameError",
    "FLVERError",
    "FLVERImportError",
    "FLVERExportError",
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