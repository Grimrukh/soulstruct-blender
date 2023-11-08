from __future__ import annotations

__all__ = [
    "FLVERImportSettings",
    "ImportFLVER",
    "ImportMapPieceFLVER",
    "ImportCharacterFLVER",
    "ImportObjectFLVER",
    "ImportEquipmentFLVER",
    "ImportMapPieceMSBPart",

    "HideAllDummiesOperator",
    "ShowAllDummiesOperator",
    "PrintGameTransform",
    "draw_dummy_ids",

    "FLVERExportSettings",
    "ExportStandaloneFLVER",
    "ExportFLVERIntoBinder",
    "ExportMapPieceFLVERs",
    "ExportCharacterFLVER",
    "ExportObjectFLVER",
    "ExportEquipmentFLVER",
    "ExportMapPieceMSBParts",

    "FLVERToolSettings",
    "SetVertexAlpha",
    "ActivateUVMap1",
    "ActivateUVMap2",
    "ActivateUVMap3",
    "ImportTextures",
    "BakeLightmapSettings",
    "BakeLightmapTextures",
    "TextureExportSettings",

    "FLVERImportPanel",
    "FLVERExportPanel",
    "FLVERLightmapsPanel",
    "FLVERToolsPanel",
    "FLVERUVMapsPanel",
]

import bpy

from io_soulstruct.misc_operators import CutMeshSelectionOperator

from .import_flver import *
from .export_flver import *
from .misc_operators import *
from .textures.import_textures import *
from .textures.export_textures import *
from .textures.lightmaps import *
from .utilities import *


def CUSTOM_ENUM(choices):
    CUSTOM_ENUM.choices = choices


CUSTOM_ENUM.choices = []


class FLVERImportPanel(bpy.types.Panel):
    """Panel for Soulstruct FLVER operators."""
    bl_label = "FLVER Import"
    bl_idname = "SCENE_PT_flver_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.operator(ImportFLVER.bl_idname)

        game_import_box = layout.box()
        game_import_box.label(text="Game Model Import")
        game_import_box.operator(ImportMapPieceFLVER.bl_idname)
        game_import_box.operator(ImportCharacterFLVER.bl_idname)
        game_import_box.operator(ImportObjectFLVER.bl_idname)
        game_import_box.operator(ImportEquipmentFLVER.bl_idname)

        msb_import_box = layout.box()
        msb_import_box.label(text="Game MSB Part Import")
        for prop in (
            "import_textures",
            "material_blend_mode",
            "base_edit_bone_length",
        ):
            msb_import_box.prop(context.scene.flver_import_settings, prop)
        msb_import_box.prop(context.scene.soulstruct_game_enums, "map_piece_parts")
        msb_import_box.operator(ImportMapPieceMSBPart.bl_idname, text="Import Map Piece Part")


class FLVERExportPanel(bpy.types.Panel):
    """Panel for Soulstruct FLVER operators."""
    bl_label = "FLVER Export"
    bl_idname = "SCENE_PT_flver_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        for prop in ("base_edit_bone_length", "allow_missing_textures", "allow_unknown_texture_types"):
            layout.prop(context.scene.flver_export_settings, prop)
        layout.operator(ExportStandaloneFLVER.bl_idname)
        layout.operator(ExportFLVERIntoBinder.bl_idname)

        game_export_box = layout.box()
        game_export_box.label(text="Game Model Export")
        game_export_box.prop(context.scene.soulstruct_settings, "detect_map_from_parent")
        game_export_box.prop(context.scene.flver_export_settings, "export_textures")

        if context.scene.flver_export_settings.export_textures:
            self._draw_texture_export_settings(context.scene.texture_export_settings, game_export_box.box())

        game_export_box.operator(ExportMapPieceFLVERs.bl_idname)
        game_export_box.operator(ExportCharacterFLVER.bl_idname)
        game_export_box.operator(ExportEquipmentFLVER.bl_idname)

        msb_export_box = layout.box()
        msb_export_box.label(text="Game MSB Part Export")
        msb_export_box.operator(ExportMapPieceMSBParts.bl_idname)

    @staticmethod
    def _draw_texture_export_settings(settings: TextureExportSettings, layout):
        layout.label(text="Texture Export Settings")
        for prop in (
            "overwrite_existing",
            "require_power_of_two",
            "platform",
            "diffuse_format",
            "diffuse_mipmap_count",
            "specular_format",
            "specular_mipmap_count",
            "bumpmap_format",
            "bumpmap_mipmap_count",
            "height_format",
            "height_mipmap_count",
            "lightmap_format",
            "lightmap_mipmap_count",
            "chrbnd_tpf_max_size",
            "max_tpfs_per_map_tpfbhd",
        ):
            layout.prop(settings, prop)


class FLVERLightmapsPanel(bpy.types.Panel):
    """Panel for Soulstruct FLVER operators."""
    bl_label = "FLVER Lightmaps"
    bl_idname = "SCENE_PT_flver_lightmaps"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        for prop in (
            "uv_layer_name",
            "texture_node_name",
            "bake_image_size",
            "bake_device",
            "bake_samples",
            "bake_margin",
            "bake_edge_shaders",
            "bake_rendered_only",
        ):
            layout.prop(context.scene.bake_lightmap_settings, prop)
        layout.operator(BakeLightmapTextures.bl_idname)


class FLVERToolsPanel(bpy.types.Panel):
    bl_label = "FLVER Tools"
    bl_idname = "SCENE_PT_flver_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):

        dummy_box = self.layout.box()
        dummy_box.label(text="Dummy Tools")
        dummy_box.prop(context.scene.flver_settings, "dummy_id_draw_enabled", text="Draw Dummy IDs")
        dummy_box.prop(context.scene.flver_settings, "dummy_id_font_size", text="Dummy ID Font Size")
        dummy_box.operator(HideAllDummiesOperator.bl_idname)
        dummy_box.operator(ShowAllDummiesOperator.bl_idname)

        textures_box = self.layout.box()
        textures_box.operator(ImportTextures.bl_idname)
        # textures_box.operator(ExportTexturesIntoBinder.bl_idname)

        misc_operators_box = self.layout.box()
        misc_operators_box.label(text="Move Mesh Selection:")
        misc_operators_box.prop(context.scene.mesh_move_settings, "new_material_index")
        misc_operators_box.operator(CutMeshSelectionOperator.bl_idname)
        misc_operators_box.label(text="Set Vertex Alpha:")
        misc_operators_box.prop(context.scene.flver_settings, "vertex_alpha")
        misc_operators_box.operator(SetVertexAlpha.bl_idname)

        misc_box = self.layout.box()
        misc_box.operator(PrintGameTransform.bl_idname)


class FLVERUVMapsPanel(bpy.types.Panel):
    """Panel for Soulstruct FLVER UV map operators."""
    bl_label = "FLVER UV Maps"
    bl_idname = "SCENE_PT_uv_maps"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Soulstruct"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.operator(ActivateUVMap1.bl_idname)
        layout.operator(ActivateUVMap2.bl_idname)
        layout.operator(ActivateUVMap3.bl_idname)
