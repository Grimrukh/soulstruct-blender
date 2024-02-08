from __future__ import annotations

__all__ = [
    "FLVERImportSettings",
    "ImportFLVER",
    "ImportMapPieceFLVER",
    "ImportCharacterFLVER",
    "ImportObjectFLVER",
    "ImportEquipmentFLVER",

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

    "FLVERToolSettings",
    "SetVertexAlpha",
    "ActivateUVMap1",
    "ActivateUVMap2",
    "ActivateUVMap3",
    "FindMissingTexturesInPNGCache",
    "SelectMeshChildren",
    "ImportTextures",
    "BakeLightmapSettings",
    "BakeLightmapTextures",
    "TextureExportSettings",

    "FLVERImportPanel",
    "FLVERExportPanel",
    "TextureExportSettingsPanel",
    "FLVERLightmapsPanel",
    "FLVERToolsPanel",
    "FLVERUVMapsPanel",
]

import bpy

from io_soulstruct.misc_operators import CutMeshSelectionOperator

from .model_import import *
from .model_export import *
from .misc_operators import *
from .textures.import_textures import *
from .textures.export_textures import *
from .textures.lightmaps import *
from .utilities import *


class FLVERImportPanel(bpy.types.Panel):
    """Panel for Soulstruct FLVER operators."""
    bl_label = "FLVER Import"
    bl_idname = "SCENE_PT_flver_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct FLVER"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.operator(ImportFLVER.bl_idname, text="Import Any FLVER")

        game_import_box = layout.box()
        game_import_box.label(text="Import from Game/Project")
        game_import_box.operator(ImportMapPieceFLVER.bl_idname)
        game_import_box.operator(ImportCharacterFLVER.bl_idname)
        game_import_box.operator(ImportObjectFLVER.bl_idname)
        game_import_box.operator(ImportEquipmentFLVER.bl_idname)


class FLVERExportPanel(bpy.types.Panel):
    """Panel for Soulstruct FLVER operators."""
    bl_label = "FLVER Export"
    bl_idname = "SCENE_PT_flver_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct FLVER"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        for prop in ("base_edit_bone_length", "allow_missing_textures", "allow_unknown_texture_types"):
            layout.prop(context.scene.flver_export_settings, prop)
        layout.operator(ExportStandaloneFLVER.bl_idname, text="Export Loose FLVER")
        layout.operator(ExportFLVERIntoBinder.bl_idname)

        game_export_box = layout.box()
        game_export_box.label(text="Export to Project/Game")
        game_export_box.prop(context.scene.soulstruct_settings, "detect_map_from_collection")
        game_export_box.prop(context.scene.flver_export_settings, "export_textures")

        game_export_box.operator(ExportMapPieceFLVERs.bl_idname)
        game_export_box.operator(ExportCharacterFLVER.bl_idname)
        game_export_box.operator(ExportObjectFLVER.bl_idname)
        game_export_box.operator(ExportEquipmentFLVER.bl_idname)


class TextureExportSettingsPanel(bpy.types.Panel):
    """Panel for Soulstruct FLVER texture export settings."""
    bl_label = "Texture Export Settings"
    bl_idname = "SCENE_PT_texture_export_settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct FLVER"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        # TODO: These are DS1 fields. Need other games. (Use their own settings classes.)
        settings = bpy.context.scene.texture_export_settings  # type: TextureExportSettings
        for prop, split in (
            ("overwrite_existing_map_textures", 0),
            ("require_power_of_two", 0),
            ("platform", 0.6),
            ("diffuse_format", 0.6),
            ("diffuse_mipmap_count", 0),
            ("specular_format", 0.6),
            ("specular_mipmap_count", 0),
            ("bumpmap_format", 0.6),
            ("bumpmap_mipmap_count", 0),
            ("height_format", 0.6),
            ("height_mipmap_count", 0),
            ("lightmap_format", 0.6),
            ("lightmap_mipmap_count", 0),
            ("max_chrbnd_tpf_size", 0),
            ("map_tpfbhd_count", 0),
        ):
            if split > 0:
                row = self.layout.row(align=True)
                split = row.split(factor=split)
                split.column().label(text=prop.replace("_", " ").title())
                split.column().prop(settings, prop, text="")
            else:
                self.layout.prop(settings, prop)


class FLVERLightmapsPanel(bpy.types.Panel):
    """Panel for Soulstruct FLVER operators."""
    bl_label = "FLVER Lightmaps"
    bl_idname = "SCENE_PT_flver_lightmaps"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct FLVER"
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
    bl_category = "Soulstruct FLVER"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):

        dummy_box = self.layout.box()
        dummy_box.label(text="Dummy Tools")
        dummy_box.prop(context.scene.flver_tool_settings, "dummy_id_draw_enabled", text="Draw Dummy IDs")
        dummy_box.prop(context.scene.flver_tool_settings, "dummy_id_font_size", text="Dummy ID Font Size")
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
        misc_operators_box.prop(context.scene.flver_tool_settings, "vertex_alpha")
        misc_operators_box.operator(SetVertexAlpha.bl_idname)

        misc_operators_box.label(text="Other Tools:")
        misc_operators_box.operator(FindMissingTexturesInPNGCache.bl_idname)
        misc_operators_box.operator(SelectMeshChildren.bl_idname)
        misc_operators_box.operator(PrintGameTransform.bl_idname)


class FLVERUVMapsPanel(bpy.types.Panel):
    """Panel for Soulstruct FLVER UV map operators."""
    bl_label = "FLVER UV Maps"
    bl_idname = "SCENE_PT_uv_maps"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Soulstruct FLVER"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.operator(ActivateUVMap1.bl_idname)
        layout.operator(ActivateUVMap2.bl_idname)
        layout.operator(ActivateUVMap3.bl_idname)
