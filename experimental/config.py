"""Shared constants/config for the add-on."""
from __future__ import annotations

__all__ = [
    "SUPPORTED_TYPES",
    "DEFAULT_EXPORT",
    "PROGRESS_COLORS",
    "PROGRESS_PASS_INDICES",
    "TINT_GROUP_NAME",
    "TINT_WRAP_LABEL",
]

from pathlib import Path

SUPPORTED_TYPES = {"MESH", "CURVE", "SURFACE", "META", "FONT"}
DEFAULT_EXPORT = Path("~/map_progress.csv").expanduser()

# Viewport object-color overlay tints (solid mode)
PROGRESS_COLORS = {
    "NONE":            (1.0, 1.0, 1.0, 0.0),        # white/transparent
    "TODO":            (1.0, 0.15, 0.15, 0.35),     # red
    "TODO_SCENERY":    (0.75, 0.4, 1.0, 0.35),      # purple
    "WIP":             (1.0, 1.0, 0.15, 0.35),      # yellow
    "DONE":            (0.20, 1.0, 0.20, 0.25),     # green
}

# Pass indices for tint masks (Object.pass_index)
PROGRESS_PASS_INDICES = {
    "NONE": 0,
    "TODO": 1,
    "TODO_SCENERY": 2,
    "WIP": 3,
    "DONE": 4,
}

# Node group & wrapper labels
TINT_GROUP_NAME = "MPM_TintGroup"
TINT_WRAP_LABEL = "MPM_TintWrap"
