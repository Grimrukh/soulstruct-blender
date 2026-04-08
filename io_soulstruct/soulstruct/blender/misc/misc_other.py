"""Truly miscellaneous functions for Soulstruct Blender objects."""
from __future__ import annotations

__all__ = [
    "PrintGameTransform",
]


from ..base.operators import *
from ..base.register import io_soulstruct_class
from ..utilities import BLTransform


@io_soulstruct_class
class PrintGameTransform(LoggingOperator):
    bl_idname = "io_scene_soulstruct.print_game_transform"
    bl_label = "Print Game Transform"
    bl_description = "Print the active object's transform in game coordinates to Blender console"

    @classmethod
    def poll(cls, context) -> bool:
        return context.active_object is not None

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        obj = context.active_object
        bl_transform = BLTransform(obj.location, obj.rotation_euler, obj.scale)
        print(
            f"FromSoftware game transform of object '{obj.name}':\n"
            f"    translate = {repr(bl_transform.game_translate)}\n"
            f"    rotate = {repr(bl_transform.game_rotate_deg)}  # degrees\n"
            f"    scale = {repr(bl_transform.game_scale)}"
        )
        return {"FINISHED"}
