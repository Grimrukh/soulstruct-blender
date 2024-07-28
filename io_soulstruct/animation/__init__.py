from __future__ import annotations

__all__ = [
    "ImportHKXAnimation",
    "ImportHKXAnimationWithBinderChoice",
    "ImportCharacterHKXAnimation",
    "ImportObjectHKXAnimation",
    "ImportAssetHKXAnimation",

    "ExportLooseHKXAnimation",
    "ExportHKXAnimationIntoBinder",
    "ExportCharacterHKXAnimation",
    "ExportObjectHKXAnimation",

    "ArmatureActionChoiceOperator",
    "SelectArmatureActionOperator",
    "HKX_ANIMATION_PT_hkx_animations",

    "AnimationImportSettings",
    "AnimationExportSettings",
]

import bpy

from .import_operators import *
from .export_operators import *
from .misc_operators import *
from .properties import *


class HKX_ANIMATION_PT_hkx_animations(bpy.types.Panel):
    bl_label = "HKX Animations"
    bl_idname = "HKX_ANIMATION_PT_hkx_animations"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Animation"
    bl_options = {'DEFAULT_CLOSED'}

    # noinspection PyUnusedLocal
    def draw(self, context):
        settings = context.scene.soulstruct_settings
        if settings.game_variable_name not in {"DARK_SOULS_DSR", "ELDEN_RING"}:
            self.layout.label(text="Import/Export for DSR and ER only.")
            return

        import_box = self.layout.box()
        import_box.operator(ImportHKXAnimation.bl_idname)

        quick_import_box = import_box.box()
        quick_import_box.label(text="Import from Game/Project")
        quick_import_box.prop(context.scene.soulstruct_settings, "import_bak_file", text="From .BAK File")
        quick_import_box.operator(ImportCharacterHKXAnimation.bl_idname)
        if settings.game_variable_name == "ELDEN_RING":
            quick_import_box.operator(ImportAssetHKXAnimation.bl_idname)
        else:
            quick_import_box.operator(ImportObjectHKXAnimation.bl_idname)

        if settings.game_variable_name not in {"DARK_SOULS_DSR"}:
            self.layout.label(text="Export for DSR only.")
            return

        export_box = self.layout.box()
        export_box.operator(ExportLooseHKXAnimation.bl_idname)
        export_box.operator(ExportHKXAnimationIntoBinder.bl_idname)

        quick_export_box = export_box.box()
        quick_export_box.label(text="Export to Project/Game")
        quick_export_box.operator(ExportCharacterHKXAnimation.bl_idname)
        quick_export_box.operator(ExportObjectHKXAnimation.bl_idname)

        select_box = self.layout.box()
        select_box.operator(SelectArmatureActionOperator.bl_idname)
        # TODO: decimate operator with ratio field
