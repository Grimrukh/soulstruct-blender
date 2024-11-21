from __future__ import annotations

__all__ = [
    "NVMProps",
    "NVMFaceIndex",
    "NVMEventEntityProps",
]

import bpy


class NVMProps(bpy.types.PropertyGroup):
    """No properties currently."""
    pass


class NVMFaceIndex(bpy.types.PropertyGroup):
    """No other way to handle this, unfortunately, since we need to store an arbitrary number of faces."""

    index: bpy.props.IntProperty(
        name="Index",
        default=-1,
        description="Index of the face in the navmesh",
    )


class NVMEventEntityProps(bpy.types.PropertyGroup):

    entity_id: bpy.props.IntProperty(
        name="Entity ID",
        description="ID of the Navmesh event for EMEVD reference. Matches a 'dummy' Navigation event in the MSB",
        default=-1,
    )

    triangle_indices: bpy.props.CollectionProperty(
        name="Triangles",
        type=NVMFaceIndex,
        description="Triangle indices in the Navmesh that this event affects",
    )

    # Internal for GUI only:
    triangle_index: bpy.props.IntProperty(
        name="Triangle Index",
        default=0,
        description="Index of the currently selected triangle",
    )
