from __future__ import annotations

__all__ = [
    "FLVERPropsPanel",
    "FLVERDummyPropsPanel",
    "FLVERImportPanel",
    "FLVERExportPanel",
]

import bpy
from io_soulstruct.general.gui import map_stem_box
from io_soulstruct.types import SoulstructType
from .import_operators import *
from .export_operators import *
from .types import BlenderFLVER, BlenderFLVERDummy


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
        uses_flver0 = context.scene.soulstruct_settings.game_config.uses_flver0
        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        props = bl_flver.type_properties
        for prop in props.__annotations__:
            if uses_flver0 and prop.startswith("f2_"):
                continue  # do not show `FLVER` property for this game
            elif not uses_flver0 and prop.startswith("f0_"):
                continue  # do not show `FLVER0` property for this game
            self.layout.prop(props, prop)


class FLVERDummyPropsPanel(bpy.types.Panel):
    """Draw a Panel in the Object properties window exposing the appropriate FLVER Dummy fields for active object."""
    bl_label = "FLVER Dummy Properties"
    bl_idname = "OBJECT_PT_flver_dummy"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if not context.active_object:
            return False
        return context.active_object.soulstruct_type == SoulstructType.FLVER_DUMMY

    def draw(self, context):
        bl_dummy = BlenderFLVERDummy.from_active_object(context)
        props = bl_dummy.type_properties
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

        map_stem_box(layout, settings)

        # NOTE: FLVER import settings are exposed within each individual operator (all use browser pop-ups).

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
            if not BlenderFLVER.test_obj(obj):
                layout.label(text="Select some FLVER models.")
                layout.label(text="MSB Parts cannot be selected.")
                return

        map_stem_box(layout, settings)

        layout.label(text="To Game/Project Map:")
        if settings.can_auto_export:
            if settings.map_stem:
                layout.operator(ExportMapPieceFLVERs.bl_idname)
            else:
                layout.label(text="No game map selected.")
                layout.label(text="Cannot export Map Pieces.")
            layout.operator(ExportCharacterFLVER.bl_idname)
            layout.operator(ExportObjectFLVER.bl_idname)
            layout.operator(ExportEquipmentFLVER.bl_idname)
        else:
            layout.label(text="No export directory set.")

        layout.label(text="Generic Export:")
        layout.operator(ExportLooseFLVER.bl_idname, text="Export Loose FLVER")
        layout.operator(ExportFLVERIntoBinder.bl_idname)
