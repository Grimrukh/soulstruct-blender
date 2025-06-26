"""Function to draw the numeric reference IDs of all Dummy children of selected FLVER."""
from __future__ import annotations

__all__ = [
    "draw_dummy_ids",
]

import blf
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d

from soulstruct.blender.exceptions import SoulstructTypeError
from soulstruct.blender.types import SoulstructType

from .types import BlenderFLVER


def draw_dummy_ids():
    """Draw the numeric reference IDs of all Dummy children of selected FLVER.

    Uses each Dummy's `color_rgba` property to determine the color and transparency of the text.
    """
    settings = bpy.context.scene.flver_tool_settings
    if not settings.dummy_id_draw_enabled:
        return

    if not bpy.context.selected_objects:
        return

    obj = bpy.context.selected_objects[0]
    # Check if object is a FLVER mesh, armature, or dummy.
    if obj.soulstruct_type == SoulstructType.FLVER_DUMMY:
        # FLVERs with dummies must have an Armature parent (Mesh is never used as parent).
        try:
            bl_flver = BlenderFLVER.from_armature_or_mesh(obj.parent)
        except SoulstructTypeError:
            return  # ignore, nothing to draw
    else:
        try:
            bl_flver = BlenderFLVER.from_armature_or_mesh(obj)
        except SoulstructTypeError:
            return  # ignore, nothing to draw

    bl_dummies = bl_flver.get_dummies()

    font_id = 0
    try:
        blf.size(font_id, bpy.context.scene.flver_tool_settings.dummy_id_font_size)
    except AttributeError:
        blf.size(font_id, 16)  # default

    for bl_dummy in bl_dummies:
        # Get world location of `dummy` object.
        world_location = bl_dummy.obj.matrix_world.to_translation()
        label_position = location_3d_to_region_2d(bpy.context.region, bpy.context.region_data, world_location)
        if not label_position:
            continue  # dummy is not in view
        blf.position(font_id, label_position.x + 10, label_position.y + 10, 0.0)
        # Set color for this dummy.
        r, g, b, a = bl_dummy.color_rgba
        blf.color(font_id, r / 255, g / 255, b / 255, a / 255)  # TODO: set a minimum alpha of 0.1?
        blf.draw(font_id, str(bl_dummy.reference_id))
