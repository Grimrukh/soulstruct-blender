"""Miscellaneous Dummy operators for FLVER models."""
from __future__ import annotations

__all__ = [
    "HideAllDummiesOperator",
    "ShowAllDummiesOperator",
]

from io_soulstruct.flver.models.types import BlenderFLVER
from io_soulstruct.utilities import LoggingOperator


class HideAllDummiesOperator(LoggingOperator):
    """Simple operator to hide all dummy children of a selected FLVER armature."""
    bl_idname = "object.hide_all_flver_dummies"
    bl_label = "Hide All Dummies"
    bl_description = "Hide all dummy point children in the selected Armature (Empties with 'Dummy' in name)"

    @classmethod
    def poll(cls, context) -> bool:
        if not context.active_object:
            return False
        return BlenderFLVER.is_obj_type(context.active_object)

    def execute(self, context):
        bl_dummies = BlenderFLVER.from_armature_or_mesh(context.active_object).get_dummies(self)
        for bl_dummy in bl_dummies:
            bl_dummy.obj.hide_viewport = True

        return {"FINISHED"}


class ShowAllDummiesOperator(LoggingOperator):
    """Simple operator to show all dummy children of a selected FLVER armature."""
    bl_idname = "object.show_all_flver_dummies"
    bl_label = "Show All Dummies"
    bl_description = "Show all dummy point children in the selected Armature (Empties with 'Dummy' in name)"

    @classmethod
    def poll(cls, context) -> bool:
        if not context.active_object:
            return False
        return BlenderFLVER.is_obj_type(context.active_object)

    def execute(self, context):
        bl_dummies = BlenderFLVER.from_armature_or_mesh(context.active_object).get_dummies(self)
        for bl_dummy in bl_dummies:
            bl_dummy.obj.hide_viewport = False

        return {"FINISHED"}
