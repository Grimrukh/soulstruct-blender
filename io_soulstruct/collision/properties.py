from __future__ import annotations

__all__ = [
    "MapCollisionProps",
    "MapCollisionImportSettings",
]

import bpy


class MapCollisionProps(bpy.types.PropertyGroup):
    """Common map collision properties for Blender objects."""

    # Currently none.
    pass


class MapCollisionImportSettings(bpy.types.PropertyGroup):
    """Common HKX map collision import settings. Drawn manually in operator browser windows."""

    # Currently none.
