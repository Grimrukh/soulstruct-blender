"""Soulstruct Experimental

Requires main Soulstruct for Blender add-on.
"""

__all__ = [
    "MapProgressSelectObject",
    "SetMapProgressState",
    "ToggleMapProgressOverlay",
    "ExportMapProgressCSV",
    "MapProgressBulkInit",
    "RefreshMapProgressVisuals",

    "MapProgressPanel",
    "MapProgressSettings",
    "MapProgressProps",

    "MaterialDebugSettings",
    "AddDebugNodeGroupToMaterials",
    "RemoveDebugNodeGroupFromMaterials",
    "MaterialDebugPanel",
]

from .map_progress.operators import (
    MapProgressSelectObject,
    SetMapProgressState,
    ToggleMapProgressOverlay,
    ExportMapProgressCSV,
    MapProgressBulkInit,
    RefreshMapProgressVisuals,
)
from .map_progress.panel import MapProgressPanel
from .map_progress.properties import MapProgressSettings, MapProgressProps

from .material_debug import (
    MaterialDebugSettings,
    AddDebugNodeGroupToMaterials,
    RemoveDebugNodeGroupFromMaterials,
    MaterialDebugPanel,
)
