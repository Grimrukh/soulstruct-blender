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

from .operators import (
    MapProgressSelectObject,
    SetMapProgressState,
    ToggleMapProgressOverlay,
    ExportMapProgressCSV,
    MapProgressBulkInit,
    RefreshMapProgressVisuals,
)
from .panel import MapProgressPanel
from .properties import MapProgressManagerSettings, MapProgressProps
from .tint import (
    ApplyProgressTintToMaterials,
    RemoveProgressTintFromMaterials,
)

CLASSES = (
    MapProgressManagerSettings,
    MapProgressProps,
    MapProgressSelectObject,
    SetMapProgressState,
    ToggleMapProgressOverlay,
    ExportMapProgressCSV,
    MapProgressBulkInit,
    RefreshMapProgressVisuals,
    ApplyProgressTintToMaterials,
    RemoveProgressTintFromMaterials,
    MapProgressPanel,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

    # Global add-on settings stored in Scene
    bpy.types.Scene.map_progress_manager_settings = bpy.props.PointerProperty(
        type=MapProgressManagerSettings,
    )

    # Per-object progress properties
    bpy.types.Object.map_progress = bpy.props.PointerProperty(type=MapProgressProps)


def unregister():
    # Remove scene/wm scratch props
    if hasattr(bpy.types.Object, "map_progress"):
        del bpy.types.Object.map_progress
    if hasattr(bpy.types.Scene, "map_progress_manager_settings"):
        del bpy.types.Scene.map_progress_manager_settings

    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
