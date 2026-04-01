"""Shared constants/config for the add-on."""
from __future__ import annotations

__all__ = [
    "SUPPORTED_TYPES",
    "DEFAULT_EXPORT",
]

from pathlib import Path

SUPPORTED_TYPES = {"MESH", "CURVE", "SURFACE", "META", "FONT"}
DEFAULT_EXPORT = Path("~/map_progress.csv").expanduser()
