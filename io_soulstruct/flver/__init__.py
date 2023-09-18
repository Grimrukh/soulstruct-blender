from __future__ import annotations

__all__ = [
    "ImportFLVER",
    "ImportFLVERWithMSBChoice",
    "ImportMapPieceFLVER",
    "ImportCharacterFLVER",
    "ImportObjectFLVER",
    "ImportEquipmentFLVER",

    "HideAllDummiesOperator",
    "ShowAllDummiesOperator",
    "PrintGameTransform",

    "ExportFLVER",
    "ExportFLVERIntoBinder",
    "ExportFLVERToMapDirectory",

    "FLVERSettings",
    "SetVertexAlpha",
    "ActivateUVMap1",
    "ActivateUVMap2",
    "ActivateUVMap3",
    "ImportDDS",
    "ExportTexturesIntoBinder",
    "BakeLightmapSettings",
    "BakeLightmapTextures",
    "ExportLightmapTextures",

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
from .textures import *
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
        layout.operator(ImportEquipmentFLVER.bl_idname)

        layout.separator()
        layout.label(text="From Game Directory:")

        map_piece_import_box = layout.box()
        map_piece_import_box.prop(context.scene.game_files, "map_piece_flver")
        map_piece_import_box.operator(ImportMapPieceFLVER.bl_idname)

        chrbnd_import_box = layout.box()
        chrbnd_import_box.prop(context.scene.game_files, "chrbnd")
        chrbnd_import_box.operator(ImportCharacterFLVER.bl_idname)

        objbnd_import_box = layout.box()
        objbnd_import_box.prop(context.scene.game_files, "objbnd_name")
        objbnd_import_box.operator(ImportObjectFLVER.bl_idname)


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
        layout.operator(ExportFLVER.bl_idname)
        layout.operator(ExportFLVERIntoBinder.bl_idname)

        layout.label(text="To Game Directory:")
        layout.operator(ExportFLVERToMapDirectory.bl_idname)


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
        layout.prop(context.scene.bake_lightmap_settings, "bake_margin")
        layout.prop(context.scene.bake_lightmap_settings, "bake_edge_shaders")
        layout.prop(context.scene.bake_lightmap_settings, "bake_rendered_only")
        layout.operator(BakeLightmapTextures.bl_idname)
        layout.operator(ExportLightmapTextures.bl_idname)


class FLVERToolsPanel(bpy.types.Panel):
    bl_label = "FLVER Tools"
    bl_idname = "SCENE_PT_flver_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):

        misc_box = self.layout.box()
        misc_box.operator(HideAllDummiesOperator.bl_idname)
        misc_box.operator(ShowAllDummiesOperator.bl_idname)
        misc_box.operator(PrintGameTransform.bl_idname)

        textures_box = self.layout.box()
        textures_box.operator(ImportDDS.bl_idname)
        textures_box.operator(ExportTexturesIntoBinder.bl_idname)

        misc_operators_box = self.layout.box()
        misc_operators_box.label(text="Move Mesh Selection:")
        misc_operators_box.prop(context.scene.mesh_move_settings, "new_material_index")
        misc_operators_box.operator(CutMeshSelectionOperator.bl_idname)
        misc_operators_box.label(text="Set Vertex Alpha:")
        misc_operators_box.prop(context.scene.flver_settings, "vertex_alpha")
        misc_operators_box.operator(SetVertexAlpha.bl_idname)

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
