from __future__ import annotations

__all__ = [
    "FLVERPropsPanel",
    "FLVERImportPanel",
    "FLVERExportPanel",
]

import bpy
from .import_operators import *
from .export_operators import *
from .types import BlenderFLVER


class FLVERPropsPanel(bpy.types.Panel):
    """Draw a Panel in the Object properties window exposing the appropriate FLVER fields for active object."""
    bl_label = "FLVER Properties"
    bl_idname = "OBJECT_PT_flver"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if not context.active_object:
            return False
        return BlenderFLVER.test_obj(context.active_object)

    def draw(self, context):
        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        props = bl_flver.type_properties
        for prop in props.__annotations__:
            self.layout.prop(props, prop)


class FLVERImportPanel(bpy.types.Panel):
    """Panel for Soulstruct FLVER operators."""
    bl_label = "FLVER Import"
    bl_idname = "SCENE_PT_flver_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        settings = context.scene.soulstruct_settings

        layout.label(text="Import from Game/Project:")
        layout.operator(ImportMapPieceFLVER.bl_idname)
        layout.operator(ImportCharacterFLVER.bl_idname)
        if settings.is_game("ELDEN_RING"):
            layout.operator(ImportAssetFLVER.bl_idname)
        else:
            layout.operator(ImportObjectFLVER.bl_idname)
        layout.operator(ImportEquipmentFLVER.bl_idname)

        layout.label(text="Generic Import:")
        layout.operator(ImportFLVER.bl_idname, text="Import Any FLVER")


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

        header, panel = layout.panel("FLVER Export Settings", default_closed=True)
        header.label(text="FLVER Export Settings")
        if panel:
            panel.prop(context.scene.soulstruct_settings, "detect_map_from_collection")
            panel.prop(context.scene.flver_export_settings, "export_textures")
            panel.prop(context.scene.flver_export_settings, "allow_missing_textures")
            panel.prop(context.scene.flver_export_settings, "allow_unknown_texture_types")
            panel.prop(context.scene.flver_export_settings, "create_lod_face_sets")
            panel.prop(context.scene.flver_export_settings, "base_edit_bone_length")
            panel.prop(context.scene.flver_export_settings, "normal_tangent_dot_max")

        if not context.selected_objects:
            layout.label(text="Select some FLVER models.")
            layout.label(text="MSB Parts cannot be selected.")
            return

        for obj in context.selected_objects:
            if not BlenderFLVER.test_obj(obj):
                layout.label(text="Select some FLVER models.")
                layout.label(text="MSB Parts cannot be selected.")
                return

        layout.label(text="Export to Selected Game/Project/Map:")
        layout.operator(ExportMapPieceFLVERs.bl_idname)
        layout.operator(ExportCharacterFLVER.bl_idname)
        layout.operator(ExportObjectFLVER.bl_idname)
        layout.operator(ExportEquipmentFLVER.bl_idname)

        layout.label(text="Generic Export:")
        layout.operator(ExportStandaloneFLVER.bl_idname, text="Export Loose FLVER")
        layout.operator(ExportFLVERIntoBinder.bl_idname)
