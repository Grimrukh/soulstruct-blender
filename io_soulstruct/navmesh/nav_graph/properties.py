from __future__ import annotations

__all__ = [
    "NVMFaceIndex",
    "MCGNodeProps",
    "MCGEdgeProps",
]

import bpy

from io_soulstruct.navmesh.nvm.properties import NVMFaceIndex


class MCGNodeProps(bpy.types.PropertyGroup):

    unknown_offset: bpy.props.IntProperty(
        name="Unknown Offset",
        default=0,
        description="Unknown offset value for this node, probably a useless artifact of its original generation",
    )

    navmesh_a: bpy.props.PointerProperty(
        name="Navmesh A",
        type=bpy.types.Object,
        description="Navmesh A that this node sits between",
    )

    navmesh_a_triangles: bpy.props.CollectionProperty(
        name="Navmesh A Triangles",
        type=NVMFaceIndex,
        description="Triangle indices in Navmesh A directly in contact with this node",
    )

    navmesh_b: bpy.props.PointerProperty(
        name="Navmesh B",
        type=bpy.types.Object,
        description="Navmesh B that this node sits between",
    )

    navmesh_b_triangles: bpy.props.CollectionProperty(
        name="Navmesh B Triangles",
        type=NVMFaceIndex,
        description="Triangle indices in Navmesh B directly in contact with this node",
    )

class MCGEdgeProps(bpy.types.PropertyGroup):

    navmesh_part: bpy.props.PointerProperty(
        name="Navmesh Part",
        type=bpy.types.Object,
        description="Navmesh part that this edge passes through",
    )

    node_a: bpy.props.PointerProperty(
        name="Node A",
        type=bpy.types.Object,
        description="Node A of this edge",
    )

    node_b: bpy.props.PointerProperty(
        name="Node B",
        type=bpy.types.Object,
        description="Node B of this edge",
    )

    cost: bpy.props.FloatProperty(
        name="Cost",
        default=1.0,
        min=0.0,
        description="Cost of traversing this edge",
    )
