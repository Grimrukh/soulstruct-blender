"""Import MSB Regions of any shape as Blender Empty objects, with custom shape properties and a custom draw tool.

Much simpler than MSB Part import, obviously, aside from the custom draw logic.
"""
from __future__ import annotations

__all__ = [
    "RegionDrawSettings",
    "draw_msb_regions",
]

import math

import numpy as np

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix
from soulstruct.blender.types import SoulstructType
from soulstruct.base.maps.msb.region_shapes import RegionShapeType


class RegionDrawSettings(bpy.types.PropertyGroup):

    draw_point_axes: bpy.props.BoolProperty(
        name="Draw Point Axes",
        description="Draw MSB Point axis RGB extensions",
        default=True,
    )

    point_radius: bpy.props.FloatProperty(
        name="Point Radius",
        description="Radius of circles used to draw MSB Point axis spheres",
        default=0.05,
        min=0.01,
        max=3.0,
    )

    line_width: bpy.props.FloatProperty(
        name="Line Width",
        description="Width of lines used to draw MSB regions",
        default=3.0,
        min=0.1,
        max=5.0,
    )


UNIT_CIRCLE_32 = [
    [math.cos(angle), math.sin(angle), 0]
    for angle in np.linspace(0, 2 * math.pi, 32)
]
CIRCLE_Z_MAT = Matrix()
CIRCLE_Y_MAT = Matrix.Rotation(math.radians(90.0), 4, 'X')
CIRCLE_X_MAT = Matrix.Rotation(math.radians(90.0), 4, 'Y')
SHADER = gpu.shader.from_builtin("UNIFORM_COLOR")
CIRCLE_BATCH = batch_for_shader(SHADER, "LINE_LOOP", {'pos': UNIT_CIRCLE_32})
X_LINE_BATCH = batch_for_shader(SHADER, "LINES", {'pos': [(0, 0, 0), (1, 0, 0)]})
Y_LINE_BATCH = batch_for_shader(SHADER, "LINES", {'pos': [(0, 0, 0), (0, 1, 0)]})
Z_LINE_BATCH = batch_for_shader(SHADER, "LINES", {'pos': [(0, 0, 0), (0, 0, 1)]})

XYZ_COLORS = [
    (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)  # matches Blender convention
]
X_OFFSET = Matrix.Translation((1, 0, 0))
Y_OFFSET = Matrix.Translation((0, 1, 0))
Z_OFFSET = Matrix.Translation((0, 0, 1))


def draw_msb_regions():
    draw_settings = bpy.context.scene.region_draw_settings
    if not draw_settings.draw_point_axes:
        # Nothing to draw.
        return

    # Find all MSB Point regions to draw.
    points = [
        obj for obj in bpy.context.scene.collection.all_objects
        if obj.soulstruct_type == SoulstructType.MSB_REGION
        and obj.MSB_REGION.shape_type_enum == RegionShapeType.Point
    ]

    SHADER.bind()
    gpu.state.line_width_set(draw_settings.line_width)

    for point in points:

        point_loc = Matrix.Translation(point.location)
        point_rot = point.rotation_euler.to_matrix().to_4x4()
        circle_rad = Matrix.Scale(draw_settings.point_radius, 4)

        for i, (line_batch, circle_offset_mat) in enumerate(zip(
            (X_LINE_BATCH, Y_LINE_BATCH, Z_LINE_BATCH),
            (X_OFFSET, Y_OFFSET, Z_OFFSET)
        )):

            SHADER.uniform_float("color", (*XYZ_COLORS[i], 1.0))

            gpu.matrix.push()
            gpu.matrix.multiply_matrix(point_loc @ point_rot)
            line_batch.draw(SHADER)
            gpu.matrix.pop()

            for circle_rot in (CIRCLE_Z_MAT, CIRCLE_Y_MAT, CIRCLE_X_MAT):
                gpu.matrix.push()
                gpu.matrix.multiply_matrix(point_loc @ point_rot @ circle_offset_mat @ circle_rot @ circle_rad)
                CIRCLE_BATCH.draw(SHADER)
                gpu.matrix.pop()
