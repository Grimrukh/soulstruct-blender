from __future__ import annotations

__all__ = [
    "HKXMapCollisionImportSettings",
]

import bpy


class HKXMapCollisionImportSettings(bpy.types.PropertyGroup):
    """Common HKX map collision import settings. Drawn manually in operator browser windows."""

    # TODO: Currently not exposing this, and forcing it to be True. Split is too painful for MSB Part instances.
    merge_submeshes: bpy.props.BoolProperty(
        name="Merge Submeshes",
        description="Merge all submeshes into a single mesh, using material to define submeshes",
        default=True,
    )
