from __future__ import annotations

__all__ = [
    "FLVERImportSettings",
    "ImportFLVER",
    "ImportMapPieceFLVER",
    "ImportCharacterFLVER",
    "ImportObjectFLVER",
    "ImportAssetFLVER",
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
    "CopyToNewFLVER",
    "DeleteFLVER",
    "DeleteFLVERAndData",
    "CreateFLVERInstance",
    "RenameFLVER",
    "CreateEmptyMapPieceFLVER",
    "SelectDisplayMaskID",
    "SetSmoothCustomNormals",
    "SetVertexAlpha",
    "InvertVertexAlpha",
    "ReboneVertices",
    "BakeBonePoseToVertices",

    "MaterialToolSettings",
    "SetMaterialTexture0",
    "SetMaterialTexture1",
    "ActivateUVTexture0",
    "ActivateUVTexture1",
    "ActiveUVLightmap",
    "FastUVUnwrap",
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
    "FLVERMeshToolsPanel",
    "FLVERMaterialToolsPanel",
    "FLVERDummyToolsPanel",
    "FLVEROtherToolsPanel",
    "FLVERUVMapsPanel",
]

import bpy

from io_soulstruct.misc_operators import CopyMeshSelectionOperator, CutMeshSelectionOperator

from .materials.misc_operators import *
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
    bl_category = "FLVER"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.operator(ImportFLVER.bl_idname, text="Import Any FLVER")

        settings = context.scene.soulstruct_settings

        game_import_box = layout.box()
        game_import_box.label(text="Import from Game/Project")
        game_import_box.operator(ImportMapPieceFLVER.bl_idname)
        game_import_box.operator(ImportCharacterFLVER.bl_idname)
        if settings.game_variable_name == "ELDEN_RING":
            game_import_box.operator(ImportAssetFLVER.bl_idname)
        else:
            game_import_box.operator(ImportObjectFLVER.bl_idname)
        game_import_box.operator(ImportEquipmentFLVER.bl_idname)


class FLVERExportPanel(bpy.types.Panel):
    """Panel for Soulstruct FLVER operators."""
    bl_label = "FLVER Export"
    bl_idname = "SCENE_PT_flver_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"
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
        game_export_box.prop(context.scene.flver_export_settings, "create_lod_face_sets")
        game_export_box.prop(context.scene.flver_export_settings, "normal_tangent_dot_max")

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
    bl_category = "FLVER"
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
    bl_category = "FLVER"
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


class FLVERMeshToolsPanel(bpy.types.Panel):
    bl_label = "FLVER Mesh Tools"
    bl_idname = "SCENE_PT_flver_mesh_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):

        flver_tool_settings = context.scene.flver_tool_settings  # type: FLVERToolSettings

        mask_box = self.layout.box()
        mask_box.label(text="Mask:")
        mask_box.prop(flver_tool_settings, "display_mask_id")
        mask_box.operator(SelectDisplayMaskID.bl_idname)

        polish_box = self.layout.box()
        polish_box.label(text="Select/Polish Mesh:")
        polish_box.operator(SelectMeshChildren.bl_idname)
        polish_box.operator(SetSmoothCustomNormals.bl_idname)

        move_box = self.layout.box()
        move_box.label(text="Move Mesh:")
        move_box.prop(context.scene.mesh_move_settings, "new_material_index")
        move_box.operator(CopyMeshSelectionOperator.bl_idname)
        move_box.operator(CutMeshSelectionOperator.bl_idname)
        move_box.prop(flver_tool_settings, "new_flver_model_name")
        move_box.operator(CopyToNewFLVER.bl_idname)

        bone_box = self.layout.box()
        bone_box.label(text="Bones:")
        # Get armature or armature of mesh.
        if (arma := context.object) and (
            context.object.type == "ARMATURE"
            or (context.object.type == "MESH" and (arma := context.object.find_armature()))
        ):
            bone_box.operator(BakeBonePoseToVertices.bl_idname)
            bone_box.prop_search(flver_tool_settings, "rebone_target_bone", arma.data, "bones")
            bone_box.operator(ReboneVertices.bl_idname)
        else:
            bone_box.label(text="No Armature found for selected object.")

        uv_box = self.layout.box()
        uv_box.label(text="UV Maps:")
        uv_box.prop(context.scene.flver_tool_settings, "uv_scale")
        uv_box.operator(FastUVUnwrap.bl_idname)

        vertex_color_box = self.layout.box()
        vertex_color_box.label(text="Vertex Colors:")
        vertex_color_box.prop(flver_tool_settings, "vertex_color_layer_name")
        vertex_color_box.prop(flver_tool_settings, "set_selected_face_vertex_alpha_only")
        vertex_color_box.operator(InvertVertexAlpha.bl_idname)
        vertex_color_box.prop(flver_tool_settings, "vertex_alpha")
        vertex_color_box.operator(SetVertexAlpha.bl_idname)


class FLVERMaterialToolsPanel(bpy.types.Panel):
    bl_label = "FLVER Material Tools"
    bl_idname = "SCENE_PT_flver_material_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):

        material_box = self.layout.box()
        material_box.label(text="Material Tools")
        selected_object = context.object
        if selected_object and selected_object.active_material:
            material_box.label(text=selected_object.active_material.name)
        else:
            material_box.label(text="No Material Selected.")
        material_box.prop(context.scene.material_tool_settings, "albedo_image")
        material_box.operator(SetMaterialTexture0.bl_idname)
        material_box.operator(SetMaterialTexture1.bl_idname)

        textures_box = self.layout.box()
        textures_box.operator(ImportTextures.bl_idname)
        textures_box.operator(FindMissingTexturesInPNGCache.bl_idname)
        # textures_box.operator(ExportTexturesIntoBinder.bl_idname)


class FLVERDummyToolsPanel(bpy.types.Panel):
    bl_label = "FLVER Dummy Tools"
    bl_idname = "SCENE_PT_flver_dummy_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.flver_tool_settings, "dummy_id_draw_enabled", text="Draw Dummy IDs")
        layout.prop(context.scene.flver_tool_settings, "dummy_id_font_size", text="Dummy ID Font Size")
        layout.operator(HideAllDummiesOperator.bl_idname)
        layout.operator(ShowAllDummiesOperator.bl_idname)


class FLVEROtherToolsPanel(bpy.types.Panel):
    bl_label = "FLVER Other Tools"
    bl_idname = "SCENE_PT_flver_other_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.operator(DeleteFLVER.bl_idname)
        layout.operator(DeleteFLVERAndData.bl_idname)
        layout.operator(CreateFLVERInstance.bl_idname)
        layout.prop(context.scene.flver_tool_settings, "new_flver_model_name")
        layout.operator(RenameFLVER.bl_idname)
        layout.operator(CreateEmptyMapPieceFLVER.bl_idname)
        layout.operator(PrintGameTransform.bl_idname)


class FLVERUVMapsPanel(bpy.types.Panel):
    """Panel for Soulstruct FLVER UV map operators."""
    bl_label = "FLVER UV Maps"
    bl_idname = "SCENE_PT_uv_maps"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.operator(ActivateUVTexture0.bl_idname)
        layout.operator(ActivateUVTexture1.bl_idname)
        layout.operator(ActiveUVLightmap.bl_idname)
