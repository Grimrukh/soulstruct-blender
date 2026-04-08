from __future__ import annotations

__all__ = [
    "ViewSelectedAtDistanceZero",
]

import bpy
from mathutils import Vector

from ..base.register import io_soulstruct_class


@io_soulstruct_class
class ViewSelectedAtDistanceZero(bpy.types.Operator):
    """Replacement for Blender's default 'View Selected' operator that sets the view distance to zero.

    I use Fly mode religiously to navigate scenes (maps), but Blender does not properly handle the view distance when
    entering and exiting Fly mode, which causes a noticeable JUMP in the camera position that gets worse the greater
    the view distance. This operator calls `view_selected()`, but then converts the view distance to a genuine shift
    in view location, and sets the view distance to zero.

    I bind this to 'Numpad .' instead of the default `view_selected()` ('Frame Selected'). If you use Fly mode more
    than an orbit-style view, I recommend you do the same.
    """
    bl_idname = "view3d.view_selected_distance_zero"
    bl_label = "View Selected at Distance Zero"

    def execute(self, context):
        # Run the default frame selected operator.
        bpy.ops.view3d.view_selected(use_all_regions=False)

        region = context.region_data
        if region is None:
            self.report({"WARNING"}, "Not in a 3D view!")
            return {"CANCELLED"}

        # Store the current view distance and rotation.
        old_distance = region.view_distance
        rot = region.view_rotation

        # Compute the camera position from the view parameters.
        camera_pos = region.view_location + rot @ Vector((0.0, 0.0, old_distance))

        # Now shift the view center to the camera position, then set view_distance to zero.
        region.view_location = camera_pos
        region.view_distance = 0.0

        return {"FINISHED"}
