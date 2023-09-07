from __future__ import annotations

__all__ = [
    "ImportFLVER",
    "ImportFLVERWithMSBChoice",
    "ImportEquipmentFLVER",
    "HideAllDummiesOperator",
    "ShowAllDummiesOperator",
    "PrintGameTransform",
    "ExportFLVER",
    "ExportFLVERIntoBinder",
    "ExportFLVERToMapDirectory",
    "ExportMapDirectorySettings",
    "FLVERSettings",
    "SetVertexAlpha",
    "ActivateUVMap1",
    "ActivateUVMap2",
    "ActivateUVMap3",
    "ImportDDS",
    "ExportTexturesIntoBinder",
    "LightmapBakeProperties",
    "BakeLightmapTextures",
    "ExportLightmapTextures",
    "FLVER_PT_flver_tools",
    "FLVER_PT_bake_subpanel",
    "FLVER_PT_uv_maps",
]

import bpy

from io_soulstruct.misc_operators import CutMeshSelectionOperator

from .import_flver import ImportFLVER, ImportFLVERWithMSBChoice, ImportEquipmentFLVER
from .export_flver import (
    ExportFLVER, ExportFLVERIntoBinder, ExportFLVERToMapDirectory, ExportMapDirectorySettings
)
from .misc_operators import *
from .textures import *
from .utilities import HideAllDummiesOperator, ShowAllDummiesOperator, PrintGameTransform


def CUSTOM_ENUM(choices):
    CUSTOM_ENUM.choices = choices


CUSTOM_ENUM.choices = []


class FLVER_PT_flver_tools(bpy.types.Panel):
    """Panel for Soulstruct FLVER operators."""
    bl_label = "FLVER"
    bl_idname = "FLVER_PT_flver_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct"

    def draw(self, context):
        import_box = self.layout.box()
        import_box.operator(ImportFLVER.bl_idname)

        equipment_import_box = self.layout.box()
        equipment_import_box.operator(ImportEquipmentFLVER.bl_idname)

        export_box = self.layout.box()
        export_box.operator(ExportFLVER.bl_idname)
        export_box.operator(ExportFLVERIntoBinder.bl_idname)

        misc_box = self.layout.box()
        misc_box.operator(HideAllDummiesOperator.bl_idname)
        misc_box.operator(ShowAllDummiesOperator.bl_idname)
        misc_box.operator(PrintGameTransform.bl_idname)

        export_map_settings = context.scene.export_map_directory_settings
        export_to_map_box = self.layout.box()
        export_to_map_box.prop(export_map_settings, "game_directory")
        export_to_map_box.prop(export_map_settings, "map_stem")
        export_to_map_box.prop(export_map_settings, "dcx_type")
        export_to_map_box.operator(ExportFLVERToMapDirectory.bl_idname)

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


class FLVER_PT_bake_subpanel(bpy.types.Panel):
    """Panel for Soulstruct FLVER lightmap texture baking."""
    bl_label = "FLVER Lightmaps"
    bl_idname = "FLVER_PT_bake_subpanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct"
    bl_parent_id = "FLVER_PT_flver_tools"

    def draw(self, context):
        self.layout.row().prop(context.scene.lightmap_bake_props, "bake_margin")
        self.layout.row().prop(context.scene.lightmap_bake_props, "bake_edge_shaders")
        self.layout.row().prop(context.scene.lightmap_bake_props, "bake_rendered_only")
        self.layout.row().operator(BakeLightmapTextures.bl_idname)

        self.layout.box().operator(ExportLightmapTextures.bl_idname)


class FLVER_PT_uv_maps(bpy.types.Panel):
    """Panel for Soulstruct FLVER UV map operators."""
    bl_label = "FLVER UV Maps"
    bl_idname = "FLVER_PT_uv_maps"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Soulstruct"

    def draw(self, context):
        self.layout.row().operator(ActivateUVMap1.bl_idname)
        self.layout.row().operator(ActivateUVMap2.bl_idname)
        self.layout.row().operator(ActivateUVMap3.bl_idname)
