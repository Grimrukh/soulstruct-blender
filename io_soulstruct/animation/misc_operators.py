"""Simple UI panel that allows the user to select an animation from a list of imported animations in the current
Blender file (Action datablocks)."""
from __future__ import annotations

__all__ = ["ArmatureActionChoiceOperator", "SelectArmatureActionOperator"]

import typing as tp

import bpy

from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities.operators import LoggingOperator


class ArmatureActionChoiceOperator(LoggingOperator):
    bl_idname = "wm.armature_action_choice_operator"
    bl_label = "Select Animation Enum"

    bl_armature = None
    bl_mesh = None
    enum_options: list[tuple[tp.Any, str, str]] = []

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
        # full_action_name = f"{self.bl_armature.name}|{self.choices_enum}"
        full_action_name = self.choices_enum
        self.info(f"Setting action for armature {self.bl_armature.name} to: {full_action_name}")
        action = bpy.data.actions[full_action_name]
        self.bl_armature.animation_data.action = action

        if action:
            # Update Blender timeline start/stop times.
            bpy.context.scene.frame_start = int(action.frame_range[0])
            bpy.context.scene.frame_end = int(action.frame_range[1])
            bpy.context.scene.frame_set(bpy.context.scene.frame_start)

        return {"FINISHED"}

    @classmethod
    def run(
        cls,
        bl_armature,
        bl_mesh
    ):
        cls.bl_armature = bl_armature
        cls.bl_mesh = bl_mesh
        cls.enum_options = []
        for action in bpy.data.actions:
            if action.name.startswith(f"{bl_mesh.name}|"):
                action_name = action.name.removeprefix(f"{bl_mesh.name}|")
                cls.enum_options.append((action.name, action_name, ""))
        # noinspection PyUnresolvedReferences
        bpy.ops.wm.armature_action_choice_operator("INVOKE_DEFAULT")


# noinspection PyUnusedLocal
def get_armature_action_choices(self, context):
    return ArmatureActionChoiceOperator.enum_options


class SelectArmatureActionOperator(LoggingOperator):
    bl_idname = "animation.select_action"
    bl_label = "Select Animation"
    bl_description = "Select an animation from the list of imported animations in the current Blender file"

    @classmethod
    def poll(cls, context):
        """Animation's rigged armature must be selected (to extract bone names)."""
        try:
            if context.selected_objects[0] and context.object:
                if context.object.type == 'ARMATURE':
                    sel = context.object
                    for child in sel.children: #! should be O(1) in most cases
                        if child.type == 'MESH':
                            return child.soulstruct_type == SoulstructType.FLVER
                elif context.object.type == 'MESH':
                    return context.object.soulstruct_type == SoulstructType.FLVER
            return False
        except IndexError:
            return False

    def execute(self, context):
        if context.object.type == 'ARMATURE':
            armature = context.object
            for child in armature.children:
                if child.type == 'MESH':
                    mesh = child; break
        elif context.object.type == 'MESH':
            armature = context.object.parent
            mesh = context.object
        ArmatureActionChoiceOperator.run(armature, mesh)
        return {"FINISHED"}
