from __future__ import annotations

__all__ = [
    "FLVERLightmapsPanel",
    "FLVERModelToolsPanel",
    "FLVERMaterialToolsPanel",
    "FLVERUVMapsPanel",
]

import bpy
from io_soulstruct.exceptions import SoulstructTypeError
from io_soulstruct.misc_operators import *
from .image import *
from .lightmaps import *
from .material import *
from .misc_operators import *
from .models.types import BlenderFLVER


class FLVERLightmapsPanel(bpy.types.Panel):
    """Panel for Soulstruct FLVER operators."""
    bl_label = "FLVER Lightmaps"
    bl_idname = "SCENE_PT_flver_lightmaps"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        bake_lightmap_settings = context.scene.bake_lightmap_settings
        header, panel = layout.panel("Settings", default_closed=False)
        header.label(text="Settings")
        if panel:
            for prop_name in bake_lightmap_settings.__annotations__:
                panel.prop(bake_lightmap_settings, prop_name)
        layout.operator(BakeLightmapTextures.bl_idname)


class FLVERModelToolsPanel(bpy.types.Panel):
    bl_label = "FLVER Model Tools"
    bl_idname = "SCENE_PT_flver_model_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):

        flver_tool_settings = context.scene.flver_tool_settings
        layout = self.layout

        header, panel = layout.panel("Mesh Tools", default_closed=True)
        header.label(text="Mesh Tools")
        if panel:
            mask_box = panel.box()
            mask_box.label(text="Display Mask ID:")
            mask_box.prop(flver_tool_settings, "display_mask_id", text="")
            mask_box.operator(SelectDisplayMaskID.bl_idname)

            modify_box = panel.box()
            modify_box.label(text="Modify Mesh:")
            modify_box.operator(BooleanMeshCut.bl_idname)

            polish_box = panel.box()
            polish_box.label(text="Select/Polish Mesh:")
            polish_box.operator(SelectUnweightedVertices.bl_idname)
            polish_box.operator(SelectMeshChildren.bl_idname)
            polish_box.operator(SetSmoothCustomNormals.bl_idname)

            move_box = panel.box()
            move_box.label(text="Move Mesh:")
            move_box.prop(context.scene.mesh_move_settings, "new_material_index")
            move_box.operator(CopyMeshSelectionOperator.bl_idname)
            move_box.operator(CutMeshSelectionOperator.bl_idname)
            move_box.operator(ApplyLocalMatrixToMesh.bl_idname)
            move_box.operator(CopyToNewFLVER.bl_idname)

        header, panel = layout.panel("Bone Tools", default_closed=True)
        header.label(text="Bone Tools")
        if panel:
            try:
                bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
            except SoulstructTypeError:
                bl_flver = None
            # Get armature or armature of mesh.
            if bl_flver and bl_flver.armature:
                panel.operator(BakeBonePoseToVertices.bl_idname)
                # noinspection PyTypeChecker
                panel.prop_search(flver_tool_settings, "rebone_target_bone", bl_flver.armature.data, "bones")
                panel.operator(ReboneVertices.bl_idname)
            elif bl_flver:
                panel.label(text="Active FLVER model does not have an Armature parent.")
            else:
                panel.label(text="No active FLVER model.")

        header, panel = layout.panel("UV Tools", default_closed=True)
        header.label(text="UV Tools")
        if panel:
            panel.prop(context.scene.flver_tool_settings, "uv_scale")
            panel.operator(FastUVUnwrap.bl_idname)
            panel.operator(RotateUVMapClockwise90.bl_idname)
            panel.operator(RotateUVMapCounterClockwise90.bl_idname)

        header, panel = layout.panel("Vertex Color Tools", default_closed=True)
        header.label(text="Vertex Color Tools")
        if panel:
            panel.label(text="Vertex Color Layer Name:")
            panel.prop(flver_tool_settings, "vertex_color_layer_name", text="")
            panel.prop(flver_tool_settings, "set_selected_face_vertex_alpha_only")
            panel.operator(InvertVertexAlpha.bl_idname)
            panel.prop(flver_tool_settings, "vertex_alpha")
            panel.operator(SetVertexAlpha.bl_idname)

        header, panel = layout.panel("Dummy Tools", default_closed=True)
        header.label(text="Dummy Tools")
        if panel:
            panel.prop(context.scene.flver_tool_settings, "dummy_id_draw_enabled", text="Draw Dummy IDs")
            panel.prop(context.scene.flver_tool_settings, "dummy_id_font_size", text="Dummy ID Font Size")
            panel.operator(HideAllDummiesOperator.bl_idname)
            panel.operator(ShowAllDummiesOperator.bl_idname)

        header, panel = layout.panel("Other Tools", default_closed=True)
        header.label(text="Other Tools")
        if panel:
            panel.operator(RenameFLVER.bl_idname)
            panel.operator(PrintGameTransform.bl_idname)


class FLVERMaterialToolsPanel(bpy.types.Panel):
    bl_label = "FLVER Material Tools"
    bl_idname = "SCENE_PT_flver_material_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        header, panel = layout.panel("Material Tools", default_closed=True)
        header.label(text="Material Tools")
        if panel:
            material_tool_settings = context.scene.material_tool_settings
            panel.prop(material_tool_settings, "use_model_stem_in_material_name")
            panel.prop(material_tool_settings, "clean_up_identical")
            panel.prop(material_tool_settings, "clean_up_ignores_face_set_count")
            panel.operator(AutoRenameMaterials.bl_idname)
            panel.operator(MergeFLVERMaterials.bl_idname)
            active_object = context.active_object
            if active_object and active_object.active_material:
                panel.label(text=active_object.active_material.name)
                panel.prop(material_tool_settings, "albedo_image")
                panel.operator(SetMaterialTexture0.bl_idname)
                panel.operator(SetMaterialTexture1.bl_idname)
            else:
                panel.label(text="No Material Selected.")

        header, panel = layout.panel("Texture Export Settings", default_closed=True)
        header.label(text="Texture Export Settings")
        if panel:
            texture_export_settings = context.scene.texture_export_settings
            for prop_name in texture_export_settings.__annotations__:
                panel.prop(texture_export_settings, prop_name)

        header, panel = layout.panel("Texture Tools", default_closed=True)
        header.label(text="Texture Tools")
        if panel:
            panel.label(text="Textures:")
            panel.operator(ImportTextures.bl_idname)
            panel.operator(FindMissingTexturesInImageCache.bl_idname)
            # panel.operator(ExportTexturesIntoBinder.bl_idname)  # TODO: not yet functional


class FLVERUVMapsPanel(bpy.types.Panel):
    """Panel for Soulstruct FLVER UV map operators. Appears in IMAGE_EDITOR space."""
    bl_label = "FLVER UV Maps"
    bl_idname = "SCENE_PT_uv_maps"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.operator(ActivateUVTexture0.bl_idname)
        layout.operator(ActivateUVTexture1.bl_idname)
        layout.operator(ActiveUVLightmap.bl_idname)
