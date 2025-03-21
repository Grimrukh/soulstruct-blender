from __future__ import annotations

__all__ = ["ArmatureActionChoiceOperator", "SelectArmatureActionOperator"]

import typing as tp

import bpy

from io_soulstruct.utilities.operators import LoggingOperator

from .types import SoulstructAnimation
from .utilities import get_active_flver_or_part_armature


class ArmatureActionChoiceOperator(LoggingOperator):
    """Operator called dynamically to let the user choose from a list of available animations for a given armature.

    TODO: Could probably just invoke props dialog on the calling Operator, moving this EnumProperty there.
    """
    bl_idname = "wm.armature_action_choice_operator"
    bl_label = "Select Animation Enum"

    ARMATURE_OBJ: tp.ClassVar[bpy.types.Object | None] = None
    MESH_OBJ: tp.ClassVar[bpy.types.Object | None] = None
    IS_PART: tp.ClassVar[bool] = False
    ENUM_OPTIONS: tp.ClassVar[list[tuple[tp.Any, str, str]]] = []

    choices_enum: bpy.props.EnumProperty(items=get_armature_action_choices)

    # noinspection PyUnusedLocal
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    # noinspection PyUnusedLocal
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "choices_enum", expand=False)

    # noinspection PyUnusedLocal
    def execute(self, context):
        full_action_name = self.choices_enum
        self.info(f"Setting action for armature {self.ARMATURE_OBJ.name} to: {full_action_name}")
        action = bpy.data.actions[full_action_name]
        ss_animation = SoulstructAnimation(action)
        if self.IS_PART and not self.ARMATURE_OBJ.animation_data:
            # Store last Part transform in custom properties.
            self.MESH_OBJ["MSB Translate"] = self.MESH_OBJ.location
            self.MESH_OBJ["MSB Rotate"] = self.MESH_OBJ.rotation_euler
            self.MESH_OBJ["MSB Scale"] = self.MESH_OBJ.scale

        if not self.ARMATURE_OBJ.animation_data:
            self.ARMATURE_OBJ.animation_data_create()
        self.ARMATURE_OBJ.animation_data.action = action

        ss_animation.set_scene_frame_range(context, reset_current_frame=True)

        return {"FINISHED"}

    @classmethod
    def run(
        cls,
        armature_obj: bpy.types.ArmatureObject,
        mesh_obj: bpy.types.MeshObject,
        model_name: str,
    ):
        cls.ARMATURE_OBJ = armature_obj
        cls.MESH_OBJ = mesh_obj
        cls.ENUM_OPTIONS = []
        # Scan all Blender actions for this armature.
        for action in bpy.data.actions:
            ss_animation = SoulstructAnimation(action)
            if ss_animation.model_stem == model_name:
                cls.ENUM_OPTIONS.append((action.name, ss_animation.animation_stem, ""))
        # noinspection PyUnresolvedReferences
        bpy.ops.wm.armature_action_choice_operator("INVOKE_DEFAULT")


# noinspection PyUnusedLocal
def get_armature_action_choices(self, context):
    return ArmatureActionChoiceOperator.ENUM_OPTIONS


class SelectArmatureActionOperator(LoggingOperator):
    # TODO: FLVER and Part actions are not compatible, as they put root motion in different places.
    #

    bl_idname = "animation.select_action"
    bl_label = "Select Animation"
    bl_description = "Select an animation from the list of available animations for this FLVER model"

    @classmethod
    def poll(cls, context) -> bool:
        """Animation's rigged armature must be selected (to extract bone names)."""
        armature_obj, _, _, _ = get_active_flver_or_part_armature(context)
        return armature_obj is not None

    def execute(self, context):
        armature_obj, mesh_obj, model_name, is_part = get_active_flver_or_part_armature(context)
        ArmatureActionChoiceOperator.run(armature_obj, mesh_obj, model_name)
        return {"FINISHED"}
