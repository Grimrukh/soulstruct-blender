from __future__ import annotations

__all__ = [
    "NVMProps",
    "NVMFaceIndex",
    "NVMEventEntityProps",
]

import bpy

from ...base.register import io_soulstruct_class, io_soulstruct_pointer_property
from ...bpy_base.property_group import SoulstructPropertyGroup


@io_soulstruct_class
@io_soulstruct_pointer_property(bpy.types.Object, "NVM")
class NVMProps(SoulstructPropertyGroup):
    """No properties currently."""
    pass


@io_soulstruct_class
class NVMFaceIndex(bpy.types.PropertyGroup):
    """No other way to handle this, unfortunately, since we need to store an arbitrary number of faces.

    NOTE: Only used nested inside other property groups.
    """

    index: bpy.props.IntProperty(
        name="Index",
        default=-1,
        description="Index of the face in the navmesh",
    )


@io_soulstruct_class
@io_soulstruct_pointer_property(bpy.types.Object, "NVM_EVENT_ENTITY")
class NVMEventEntityProps(SoulstructPropertyGroup):

    # No game-specific properties.

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
