from __future__ import annotations

__all__ = [
    "FLVERModelToolsPanel",
]

import bpy
from io_soulstruct.exceptions import SoulstructTypeError
from io_soulstruct.misc.misc_mesh import *
from io_soulstruct.flver.models.operators import *
from io_soulstruct.flver.models.types import BlenderFLVER


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
            panel.operator(FastUVUnwrapIslands.bl_idname)
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
