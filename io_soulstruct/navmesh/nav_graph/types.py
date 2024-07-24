from __future__ import annotations

import bpy
from io_soulstruct.types import *
from .properties import *


class BlenderMCGNode(SoulstructObject[MCGNodeProps]):

    TYPE = SoulstructType.MCG_NODE
    OBJ_DATA_TYPE = SoulstructDataType.EMPTY

    unknown_offset: int
    navmesh_a: bpy.types.Object | None
    navmesh_b: bpy.types.Object | None

    @property
    def navmesh_a_triangles(self) -> list[int]:
        return [t.index for t in self.type_properties.navmesh_a_triangles]

    @navmesh_a_triangles.setter
    def navmesh_a_triangles(self, value: list[int]):
        self.type_properties.navmesh_a_triangles.clear()
        for index in value:
            self.type_properties.navmesh_a_triangles.add().index = index

    @property
    def navmesh_b_triangles(self) -> list[int]:
        return [t.index for t in self.type_properties.navmesh_b_triangles]

    @navmesh_b_triangles.setter
    def navmesh_b_triangles(self, value: list[int]):
        self.type_properties.navmesh_b_triangles.clear()
        for index in value:
            self.type_properties.navmesh_b_triangles.add().index = index


class BlenderMCGEdge(SoulstructObject[MCGEdgeProps]):

    TYPE = SoulstructType.MCG_EDGE
    OBJ_DATA_TYPE = SoulstructDataType.EMPTY

    navmesh_part: bpy.types.Object | None
    node_a: bpy.types.Object | None
    node_b: bpy.types.Object | None
    cost: float
