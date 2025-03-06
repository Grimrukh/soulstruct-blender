from __future__ import annotations

__all__ = [
    "FLVERExportPanel",
]

import bpy

from io_soulstruct.general.gui import map_stem_box
from ..operators.export_operators import *
from ..types import BlenderFLVER


class FLVERExportPanel(bpy.types.Panel):
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
            panel.prop(settings, "detect_map_from_collection")
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

        map_stem_box(layout, settings)

        if settings.can_auto_export:
            map_stem = settings.get_active_object_detected_map(context)
            if not map_stem:
                layout.label(text="To Map: <NO MAP>")
            else:
                map_stem = settings.get_oldest_map_stem_version(map_stem)
                layout.label(text=f"To Map: {map_stem}")
            layout.operator(ExportMapPieceFLVERs.bl_idname)
            layout.label(text="Game Models:")
            layout.operator(ExportCharacterFLVER.bl_idname)
            layout.operator(ExportObjectFLVER.bl_idname)
            layout.operator(ExportEquipmentFLVER.bl_idname)
        else:
            layout.label(text="No export directory set.")

        layout.label(text="Generic Export:")
        layout.operator(ExportLooseFLVER.bl_idname, text="Export Loose FLVER")
        layout.operator(ExportFLVERIntoBinder.bl_idname)
