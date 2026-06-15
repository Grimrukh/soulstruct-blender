"""Import MSB Regions of any shape as Blender Empty objects, with custom shape properties and a custom draw tool.

Much simpler than MSB Part import, obviously, aside from the custom draw logic.
"""
from __future__ import annotations

__all__ = [
    "RegionDrawSettings",
    "draw_msb_regions",
]

import math
import typing as tp

import numpy as np

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix

from soulstruct.base.maps.msb.region_shapes import RegionShapeType

from ..base.register import *
from ..types import SoulstructType

if tp.TYPE_CHECKING:
    from gpu.types import GPUShader, GPUBatch


@io_soulstruct_properties
@io_soulstruct_pointer_property(bpy.types.Scene, "region_draw_settings")
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

_CACHED_SHADER = None  # type: GPUShader | None
_CACHED_CIRCLE_BATCH = None  # type: GPUBatch | None
_CACHED_X_LINE_BATCH = None  # type: GPUBatch | None
_CACHED_Y_LINE_BATCH = None  # type: GPUBatch | None
_CACHED_Z_LINE_BATCH = None  # type: GPUBatch | None

XYZ_COLORS = [
    (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)  # matches Blender convention
]
X_OFFSET = Matrix.Translation((1, 0, 0))
Y_OFFSET = Matrix.Translation((0, 1, 0))
Z_OFFSET = Matrix.Translation((0, 0, 1))


@io_soulstruct_space_view_3d_draw_handler("WINDOW", "POST_VIEW")
def draw_msb_regions():
    if bpy.app.background:
        return

    global _CACHED_SHADER, _CACHED_CIRCLE_BATCH, _CACHED_X_LINE_BATCH, _CACHED_Y_LINE_BATCH, _CACHED_Z_LINE_BATCH
    if not _CACHED_SHADER:
        _CACHED_SHADER = gpu.shader.from_builtin("UNIFORM_COLOR")  # type: GPUShader
        _CACHED_CIRCLE_BATCH = batch_for_shader(_CACHED_SHADER, "LINE_LOOP", {'pos': UNIT_CIRCLE_32})
        _CACHED_X_LINE_BATCH = batch_for_shader(_CACHED_SHADER, "LINES", {'pos': [(0, 0, 0), (1, 0, 0)]})
        _CACHED_Y_LINE_BATCH = batch_for_shader(_CACHED_SHADER, "LINES", {'pos': [(0, 0, 0), (0, 1, 0)]})
        _CACHED_Z_LINE_BATCH = batch_for_shader(_CACHED_SHADER, "LINES", {'pos': [(0, 0, 0), (0, 0, 1)]})

    draw_settings = bpy.context.scene.region_draw_settings
    if not draw_settings.draw_point_axes:
        # Nothing to draw.
        return

    # Find all MSB Point regions to draw.
    points = [
        obj for obj in bpy.context.scene.collection.all_objects
        if obj.soulstruct_type == SoulstructType.MSB_REGION
        and obj.MSB_REGION.shape_type_enum == RegionShapeType.Point
        and obj.visible_get()
    ]

    _CACHED_SHADER.bind()
    gpu.state.line_width_set(draw_settings.line_width)

    for point in points:

        point_loc = Matrix.Translation(point.location)
        point_rot = point.rotation_euler.to_matrix().to_4x4()
        circle_rad = Matrix.Scale(draw_settings.point_radius, 4)

        for i, (line_batch, circle_offset_mat) in enumerate(zip(
            (_CACHED_X_LINE_BATCH, _CACHED_Y_LINE_BATCH, _CACHED_Z_LINE_BATCH),
            (X_OFFSET, Y_OFFSET, Z_OFFSET)
        )):

            _CACHED_SHADER.uniform_float("color", (*XYZ_COLORS[i], 1.0))

            gpu.matrix.push()
            gpu.matrix.multiply_matrix(point_loc @ point_rot)
            line_batch.draw(_CACHED_SHADER)
            gpu.matrix.pop()

            for circle_rot in (CIRCLE_Z_MAT, CIRCLE_Y_MAT, CIRCLE_X_MAT):
                gpu.matrix.push()
                gpu.matrix.multiply_matrix(point_loc @ point_rot @ circle_offset_mat @ circle_rot @ circle_rad)
                _CACHED_CIRCLE_BATCH.draw(_CACHED_SHADER)
                gpu.matrix.pop()
