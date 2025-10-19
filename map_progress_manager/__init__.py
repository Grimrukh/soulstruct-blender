# SPDX-License-Identifier: MIT
# flake8: noqa
"""Soulstruct Map Progress Manager (package)

Split version with TODO SCENERY state and material-based viewport tint.
"""

bl_info = {
    "name": "Soulstruct Map Progress Manager",
    "author": "Scott Mooney (Grimrukh)",
    "version": (1, 0, 0),
    "blender": (4, 4, 0),
    "location": "3D View > N-Panel > MapTools > Map Progress",
    "description": "Per-object progress tags with visual overlay, edit lock, queue, CSV export, and injected shader tinting.",
    "category": "Object",
}

import bpy

from .properties import MapProgressManagerSettings, MapProgressProps
from .operators import (
    MapProgressSelectObject,
    SetMapProgressState,
    ToggleMapProgressOverlay,
    ExportMapProgressCSV,
    MapProgressBulkInit,
    RefreshMapProgressVisuals,
)
from .tint import (
    ApplyProgressTintToMaterials,
    RemoveProgressTintFromMaterials,
    on_global_tint_toggle,
    get_or_make_tint_node_group,  # used implicitly by Apply operator
)
from .panel import MapProgressPanel

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
