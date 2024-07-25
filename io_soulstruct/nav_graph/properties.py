from __future__ import annotations

__all__ = [
    "MCGProps",
    "NVMFaceIndex",
    "MCGNodeProps",
    "MCGEdgeProps",
    "NavGraphComputeSettings",
]

import bpy

from io_soulstruct.navmesh.nvm.properties import NVMFaceIndex


class MCGProps(bpy.types.PropertyGroup):

    unknown_0: bpy.props.IntProperty(
        name="Unknown 0",
        default=0,
        description="Unknown value 0 for this MCG object",
    )

    unknown_1: bpy.props.IntProperty(
        name="Unknown 1",
        default=0,
        description="Unknown value 1 for this MCG object",
    )

    unknown_2: bpy.props.IntProperty(
        name="Unknown 2",
        default=0,
        description="Unknown value 2 for this MCG object",
    )


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


class NavGraphComputeSettings(bpy.types.PropertyGroup):

    select_path: bpy.props.BoolProperty(
        name="Select Path",
        default=True,
        description="Select the path of faces found by the pathfinding algorithm"
    )

    wall_multiplier: bpy.props.FloatProperty(
        name="Wall Cost Multiplier",
        default=1.0,
        description="Cost multiplier (of distance) for Wall faces",
    )
    obstacle_multiplier: bpy.props.FloatProperty(
        name="Obstacle Cost Multiplier",
        default=1.0,
        description="Cost multiplier (of distance) for Obstacle faces. Ignores obstacle count",
    )
