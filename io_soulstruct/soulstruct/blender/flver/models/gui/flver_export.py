from __future__ import annotations

__all__ = [
    "FLVERExportPanel",
]

from soulstruct.blender.bpy_base.panel import SoulstructPanel
from ..operators.export_operators import *
from ..types import BlenderFLVER


class FLVERExportPanel(SoulstructPanel):
    """Panel for Soulstruct FLVER operators."""
    bl_label = "FLVER Export"
    bl_idname = "SCENE_PT_flver_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        settings = context.scene.soulstruct_settings

        header, panel = layout.panel("FLVER Export Settings", default_closed=True)
        header.label(text="FLVER Export Settings")
        if panel:
            export_settings = context.scene.flver_export_settings
            panel.prop(settings, "auto_detect_export_map")
            panel.prop(export_settings, "export_textures")
            panel.prop(export_settings, "allow_missing_textures")
            panel.prop(export_settings, "allow_unknown_texture_types")
            panel.prop(export_settings, "create_lod_face_sets")
            panel.prop(export_settings, "base_edit_bone_length")
            panel.prop(export_settings, "normal_tangent_dot_max")

        if not context.selected_objects:
            layout.label(text="Select some FLVER models.")
            layout.label(text="MSB Parts cannot be selected.")
            return

        for obj in context.selected_objects:
            if not BlenderFLVER.is_obj_type(obj):
                layout.label(text="Select some FLVER models.")
                layout.label(text="MSB Parts cannot be selected.")
                return

        if settings.can_auto_export:
            box = layout.box()
            box.label(text="Game Models:")
            box.operator(ExportCharacterFLVER.bl_idname)
            box.operator(ExportObjectFLVER.bl_idname)
            box.operator(ExportEquipmentFLVER.bl_idname)

            box = layout.box()
            box.label(text="Map Models:")
            box.prop(settings, "auto_detect_export_map")
            if settings.auto_detect_export_map:
                self.draw_detected_map(context, box, use_latest_version=False)
            else:
                self.draw_active_map(context, box)
            box.operator(ExportMapPieceFLVERs.bl_idname)
        else:
            layout.label(text="No export directory set.")

        layout.operator(ExportAnyFLVER.bl_idname)
        layout.operator(ExportFLVERIntoAnyBinder.bl_idname)
