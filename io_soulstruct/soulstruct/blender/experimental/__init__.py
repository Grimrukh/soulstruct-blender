"""Soulstruct Experimental

Requires main Soulstruct for Blender add-on.
"""
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
