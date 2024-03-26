__all__ = [
    "MSBExportSettings",

    "ExportMSBMapPieces",
    "ExportMSBCollisions",
    "ExportMSBNavmeshes",
    "ExportCompleteMapNavigation",

    "MSBExportPanel",
]

from .map_pieces import *
from .collisions import *
from .navmeshes import *
from .settings import *

import bpy


class MSBExportPanel(bpy.types.Panel):
    """Panel for Soulstruct MSB export operators."""
    bl_label = "MSB Export"
    bl_idname = "SCENE_PT_msb_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MSB"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        flver_export_settings_box = self.layout.box()
        flver_export_settings_box.label(text="FLVER Export Settings")

        for prop in (
            "export_textures",
            "create_lod_face_sets",
            "base_edit_bone_length",
            "allow_missing_textures",
            "allow_unknown_texture_types",
            "normal_tangent_dot_max",
        ):
            flver_export_settings_box.prop(context.scene.flver_export_settings, prop)

        msb_export_box = self.layout.box()
        msb_export_box.prop(context.scene.soulstruct_settings, "detect_map_from_collection")
        msb_export_box.prop(context.scene.msb_export_settings, "export_model_files")

        map_piece_box = self.layout.box()
        map_piece_box.operator(ExportMSBMapPieces.bl_idname)

        collision_box = self.layout.box()
        collision_box.operator(ExportMSBCollisions.bl_idname)

        navmesh_box = self.layout.box()
        navmesh_box.operator(ExportMSBNavmeshes.bl_idname)
        navmesh_box.label(text="Complete MSB Navmeshes + NVMBND + NVMDUMP Export:")
        navmesh_box.operator(ExportCompleteMapNavigation.bl_idname)
