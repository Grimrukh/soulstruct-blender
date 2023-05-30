from __future__ import annotations

__all__ = [
    "ImportHKXAnimation",
    "ImportHKXAnimationWithBinderChoice",
    "ArmatureActionChoiceOperator",
    "SelectArmatureActionOperator",
    "HKX_ANIMATION_PT_hkx_animation_tools",
]

import importlib
import sys

import bpy

if "HKX_ANIMATION_PT_hkx_tools" in locals():
    importlib.reload(sys.modules["io_soulstruct.hkx_animation.utilities"])
    importlib.reload(sys.modules["io_soulstruct.hkx_animation.import_hkx_animation"])
    importlib.reload(sys.modules["io_soulstruct.hkx_animation.select_hkx_animation"])
    # importlib.reload(sys.modules["io_soulstruct.hkx_animation.export_hkx_animation"])  # TODO

# from io_hkx.export_hkx import ExportHKXAnim, ExportHKXAnimIntoBinder
from .import_hkx_animation import ImportHKXAnimation, ImportHKXAnimationWithBinderChoice
from .select_hkx_animation import ArmatureActionChoiceOperator, SelectArmatureActionOperator


class HKX_ANIMATION_PT_hkx_animation_tools(bpy.types.Panel):
    bl_label = "HKX Animation Tools"
    bl_idname = "HKX_ANIMATION_PT_hkx_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "HKX Animation"

    # noinspection PyUnusedLocal
    def draw(self, context):
        import_box = self.layout.box()
        import_box.operator(ImportHKXAnimation.bl_idname)
        import_box.operator(SelectArmatureActionOperator.bl_idname)

        # TODO: export
        # export_box = self.layout.box()
        # export_box.operator("export_scene.hkxanim")
        # export_box.operator("export_scene.hkxanim_binder")
