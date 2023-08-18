from __future__ import annotations

__all__ = [
    "MCGImportError",
    "MCGExportError",
]


class MCGImportError(Exception):
    """Exception raised during NVM import."""
    pass


class MCGExportError(Exception):
    """Exception raised during NVM export."""
    pass
