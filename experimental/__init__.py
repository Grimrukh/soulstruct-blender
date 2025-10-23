"""Soulstruct Experimental

Requires main Soulstruct for Blender add-on.
"""

bl_info = {
    "name": "Soulstruct Experimental",
    "author": "Scott Mooney (Grimrukh)",
    "version": (1, 0, 1),
    "blender": (4, 4, 0),
    "location": "3D View > N-Panel > Experimental",
    "description": "Experimental features for Soulstruct: map progress, material debugging tools, ...",
    "category": "Object",
}

import bpy

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

CLASSES = (
    MapProgressSettings,
    MapProgressProps,
    MapProgressSelectObject,
    SetMapProgressState,
    ToggleMapProgressOverlay,
    ExportMapProgressCSV,
    MapProgressBulkInit,
    RefreshMapProgressVisuals,
    MapProgressPanel,

    MaterialDebugSettings,
    AddDebugNodeGroupToMaterials,
    RemoveDebugNodeGroupFromMaterials,
    MaterialDebugPanel,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

    # Global add-on settings stored in Scene
    bpy.types.Scene.map_progress_settings = bpy.props.PointerProperty(type=MapProgressSettings)
    bpy.types.Scene.material_debug_settings = bpy.props.PointerProperty(type=MaterialDebugSettings)

    # Per-object progress properties
    bpy.types.Object.map_progress = bpy.props.PointerProperty(type=MapProgressProps)


def unregister():
    # Remove scene/wm scratch props
    if hasattr(bpy.types.Object, "map_progress"):
        del bpy.types.Object.map_progress
    if hasattr(bpy.types.Scene, "material_debug_settings"):
        del bpy.types.Scene.material_debug_settings
    if hasattr(bpy.types.Scene, "map_progress_settings"):
        del bpy.types.Scene.map_progress_settings

    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
