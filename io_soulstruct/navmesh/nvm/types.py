from __future__ import annotations

__all__ = [
    "BlenderNavmeshEvent",
]

import bpy
from mathutils import Vector

from soulstruct.darksouls1r.maps.navmesh.nvm import NVMEventEntity
from io_soulstruct.types import *
from .properties import *


class BlenderNavmeshEvent(SoulstructObject[NavmeshEventProps]):

    TYPE = SoulstructType.NAVMESH_EVENT
    OBJ_DATA_TYPE = SoulstructDataType.EMPTY

    entity_id: int

    @property
    def triangle_indices(self) -> list[int]:
        return [face.index for face in self.props.triangle_indices]

    @triangle_indices.setter
    def triangle_indices(self, indices: list[int]):
        self.props.triangle_indices.clear()
        for index in indices:
            self.props.triangle_indices.add().index = index

    @classmethod
    def new_from_nvm_event_entity(
        cls,
        context: bpy.types.Context,
        nvm_event_entity: NVMEventEntity,
        nvm_name: str,
        location: Vector,
        collection: bpy.types.Collection = None,
    ):
        bl_event = bpy.data.objects.new(f"{nvm_name} Event {nvm_event_entity.entity_id}", None)
        bl_event.empty_display_type = "CUBE"  # to distinguish it from node spheres
        bl_event.soulstruct_type = SoulstructType.NAVMESH_EVENT
        (collection or context.scene.collection).objects.link(bl_event)

        bl_event.location = location
        bl_event.NAVMESH_EVENT.entity_id = nvm_event_entity.entity_id
        for i in nvm_event_entity.triangle_indices:
            bl_event.NAVMESH_EVENT.triangle_indices.add().index = i
        return cls(bl_event)
