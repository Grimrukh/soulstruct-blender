from __future__ import annotations

__all__ = [
    "ImportHKXAnimation",
    "ImportHKXAnimationWithBinderChoice",
    "ImportCharacterHKXAnimation",
    "ImportObjectHKXAnimation",

    "ExportLooseHKXAnimation",
    "ExportHKXAnimationIntoBinder",
    "QuickExportCharacterHKXAnimation",
    "QuickExportObjectHKXAnimation",

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
    importlib.reload(sys.modules["io_soulstruct.hkx_animation.export_hkx_animation"])

from .import_hkx_animation import *
from .export_hkx_animation import *
from .select_hkx_animation import *


class HKX_ANIMATION_PT_hkx_animation_tools(bpy.types.Panel):
    bl_label = "HKX Animations"
    bl_idname = "HKX_ANIMATION_PT_hkx_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct Havok"
    bl_options = {'DEFAULT_CLOSED'}

    # noinspection PyUnusedLocal
    def draw(self, context):
        import_box = self.layout.box()
        import_box.operator(ImportHKXAnimation.bl_idname)

        quick_import_box = import_box.box()
        quick_import_box.label(text="Quick Game Import")
        quick_import_box.prop(context.scene.soulstruct_settings, "use_bak_file", text="From .BAK File")
        quick_import_box.operator(ImportCharacterHKXAnimation.bl_idname)
        quick_import_box.operator(ImportObjectHKXAnimation.bl_idname)

        export_box = self.layout.box()
        export_box.operator(ExportLooseHKXAnimation.bl_idname)
        export_box.operator(ExportHKXAnimationIntoBinder.bl_idname)

        quick_export_box = export_box.box()
        quick_export_box.label(text="Quick Game Export")
        quick_export_box.operator(QuickExportCharacterHKXAnimation.bl_idname)
        quick_export_box.operator(QuickExportObjectHKXAnimation.bl_idname)

        select_box = self.layout.box()
        select_box.operator(SelectArmatureActionOperator.bl_idname)
        # TODO: decimate operator with ratio field
