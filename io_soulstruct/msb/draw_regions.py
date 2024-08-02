"""Import MSB Regions of any shape as Blender Empty objects, with custom shape properties and a custom draw tool.

Much simpler than MSB Part import, obviously, aside from the custom draw logic.
"""
from __future__ import annotations

__all__ = [
    "RegionDrawSettings",
    "draw_region_volumes",
]

import math
import re

import numpy as np

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix
from io_soulstruct.types import SoulstructType
from soulstruct.base.maps.msb.region_shapes import RegionShapeType


class RegionDrawSettings(bpy.types.PropertyGroup):

    draw_mode: bpy.props.EnumProperty(
        name="Draw Mode",
        description="When to draw MSB regions in the 3D view",
        items=[
            ("ACTIVE_COLLECTION", "Active Collection", "Draw all MSB regions in the active collection"),
            ("SELECTED", "Selected", "Draw only the selected MSB region"),
            ("MAP", "Map", "Draw all MSB regions in collection with name matching '{map} * Volumes *'"),
            ("ALL", "All", "Draw all MSB regions in the scene"),
            ("NONE", "None", "Do not draw any MSB regions"),
        ],
        default="ALL",
    )

    draw_points: bpy.props.BoolProperty(
        name="Draw Points",
        description="Draw MSB Point regions",
        default=True,
    )

    draw_spheres: bpy.props.BoolProperty(
        name="Draw Spheres",
        description="Draw MSB Sphere regions",
        default=False,
    )

    draw_cylinders: bpy.props.BoolProperty(
        name="Draw Cylinders",
        description="Draw MSB Cylinder regions",
        default=False,
    )

    draw_boxes: bpy.props.BoolProperty(
        name="Draw Boxes",
        description="Draw MSB Box regions",
        default=False,
    )

    region_color: bpy.props.FloatVectorProperty(
        name="Region Color",
        description="Color of drawn MSB regions",
        subtype="COLOR",
        default=(1.0, 0.0, 0.0),
        min=0.0,
        max=1.0,
    )

    use_rgb_points: bpy.props.BoolProperty(
        name="Use RGB Points",
        description="Use RGB colors for MSB Point regions",
        default=True,
    )

    point_radius: bpy.props.FloatProperty(
        name="Point Radius",
        description="Radius of circles used to draw MSB Point regions",
        default=3.0,
        min=1.0,
        max=10.0,
    )

    line_width: bpy.props.FloatProperty(
        name="Line Width",
        description="Width of lines used to draw MSB regions",
        default=1.0,
        min=0.1,
        max=10.0,
    )


MAP_VOLUME_COLLECTION_RE = re.compile(r"^(?P<map_stem>.+) (.*)Volumes(.*)$")

UNIT_CIRCLE_32 = [
    [math.cos(angle), math.sin(angle), 0]
    for angle in np.linspace(0, 2 * math.pi, 32)
]
UNIT_CIRCLE_32_TOP = [
    [math.cos(angle), math.sin(angle), 1]
    for angle in np.linspace(0, 2 * math.pi, 32)
]
CIRCLE_Z_MAT = Matrix()
CIRCLE_Y_MAT = Matrix.Rotation(math.radians(90.0), 4, 'X')
CIRCLE_X_MAT = Matrix.Rotation(math.radians(90.0), 4, 'Y')
SHADER = gpu.shader.from_builtin("UNIFORM_COLOR")
CIRCLE_BATCH = batch_for_shader(SHADER, "LINE_LOOP", {'pos': UNIT_CIRCLE_32})
CIRCLE_TOP_BATCH = batch_for_shader(SHADER, "LINE_LOOP", {'pos': UNIT_CIRCLE_32_TOP})

CYLINDER_VERTICES = [
    (1, 0, 0), (1, 0, 1),
    (-1, 0, 0), (-1, 0, 1),
    (0, 1, 0), (0, 1, 1),
    (0, -1, 0), (0, -1, 1),
]
CYLINDER_BATCH = batch_for_shader(SHADER, "LINES", {'pos': CYLINDER_VERTICES})

CUBE_VERTICES = np.array([
    (x, y, z)
    for x in (-1, 1)
    for y in (-1, 1)
    for z in (-1, 1)
])
CUBE_EDGES = [
    (0, 1), (1, 3), (3, 2), (2, 0),
    (4, 5), (5, 7), (7, 6), (6, 4),
    (0, 4), (1, 5), (2, 6), (3, 7),
]
CUBE_BATCH = batch_for_shader(SHADER, "LINES", {'pos': [CUBE_VERTICES[i] for edge in CUBE_EDGES for i in edge]})


# noinspection PyUnresolvedReferences
def draw_region_volumes():
    draw_settings = bpy.context.scene.region_draw_settings
    if draw_settings.draw_mode == "NONE":
        return  # don't draw any regions

    # Find all regions to draw.
    regions = {
        RegionShapeType.Point: [],
        RegionShapeType.Sphere: [],
        RegionShapeType.Cylinder: [],
        RegionShapeType.Box: [],
    }

    def register_obj(obj_: bpy.types.Object):
        if obj_.soulstruct_type != SoulstructType.MSB_REGION:
            return
        try:
            shape_type = RegionShapeType[obj_.MSB_REGION.shape_type]
        except KeyError:
            return
        if shape_type in regions:
            regions[shape_type].append(obj_)

    match draw_settings.draw_mode:
        case "ACTIVE_COLLECTION":
            region_collection = bpy.context.collection
            for obj in region_collection.objects:
                register_obj(obj)
        case "SELECTED":
            for obj in bpy.context.selected_objects:
                register_obj(obj)
        case "MAP":
            map_stem = bpy.context.scene.soulstruct_settings.get_oldest_map_stem_version()  # for MSB
            region_collections = [
                collection for collection in bpy.data.collections
                if MAP_VOLUME_COLLECTION_RE.match(collection.name) and collection.name.startswith(map_stem)
            ]
            for collection in region_collections:
                for obj in collection.objects:
                    register_obj(obj)
        case "ALL":
            for obj in bpy.context.scene.collection.all_objects:
                register_obj(obj)

    SHADER.bind()
    gpu.state.line_width_set(draw_settings.line_width)
    # gpu.state.blend_set("ALPHA")

    SHADER.uniform_float("color", (*draw_settings.region_color, 1.0))

    if draw_settings.draw_cylinders:
        for cylinder in regions[RegionShapeType.Cylinder]:
            cylinder_loc = Matrix.Translation(cylinder.location)
            cylinder_rot = cylinder.rotation_euler.to_matrix().to_4x4()
            cylinder_radius = max(cylinder.scale[0], cylinder.scale[1])
            cylinder_height = cylinder.scale[2]
            cylinder_scale = Matrix.Diagonal((cylinder_radius, cylinder_radius, cylinder_height, 1.0))

            gpu.matrix.push()
            gpu.matrix.multiply_matrix(cylinder_loc @ cylinder_rot @ cylinder_scale)
            CIRCLE_BATCH.draw(SHADER)
            CYLINDER_BATCH.draw(SHADER)
            CIRCLE_TOP_BATCH.draw(SHADER)
            gpu.matrix.pop()

    if draw_settings.draw_boxes:
        for box in regions[RegionShapeType.Box]:
            box_transform = Matrix.LocRotScale(box.location, box.rotation_euler, box.scale)
            gpu.matrix.push()
            gpu.matrix.multiply_matrix(box_transform)
            CUBE_BATCH.draw(SHADER)
            gpu.matrix.pop()

    if draw_settings.draw_spheres:
        for sphere in regions[RegionShapeType.Sphere]:

            sphere_loc = Matrix.Translation(sphere.location)
            sphere_rot = sphere.rotation_euler.to_matrix().to_4x4()
            sphere_scale = Matrix.Scale(max(sphere.scale), 4)

            for i, circle_rot in enumerate((CIRCLE_Z_MAT, CIRCLE_Y_MAT, CIRCLE_X_MAT)):
                gpu.matrix.push()
                gpu.matrix.multiply_matrix(sphere_loc @ sphere_rot @ circle_rot @ sphere_scale)
                CIRCLE_BATCH.draw(SHADER)
                gpu.matrix.pop()

    # We draw points last so we can use the RGB color option.
    if draw_settings.draw_points:
        if draw_settings.use_rgb_points:
            point_colors = [
                (0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)
            ]
        else:
            point_colors = None

        for point in regions[RegionShapeType.Point]:

            point_loc = Matrix.Translation(point.location)
            point_rot = point.rotation_euler.to_matrix().to_4x4()
            point_scale = Matrix.Scale(draw_settings.point_radius, 4)

            for i, circle_rot in enumerate((CIRCLE_Z_MAT, CIRCLE_Y_MAT, CIRCLE_X_MAT)):
                if point_colors:
                    SHADER.uniform_float("color", (*point_colors[i], 1.0))
                gpu.matrix.push()
                gpu.matrix.multiply_matrix(point_loc @ point_rot @ circle_rot @ point_scale)
                CIRCLE_BATCH.draw(SHADER)
                gpu.matrix.pop()

    # gpu.state.blend_set("NONE")
