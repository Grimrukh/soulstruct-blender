from __future__ import annotations

__all__ = [
    "HKXCutsceneImportError",
    "HKXCutsceneExportError",
]


class HKXCutsceneImportError(Exception):
    """Exception raised during HKX cutscene import."""
    pass


class HKXCutsceneExportError(Exception):
    """Exception raised during HKX cutscene export."""
    pass
