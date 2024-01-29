from __future__ import annotations

__all__ = [
    "NVMImportSettings",
    "ImportNVM",
    "ImportNVMWithBinderChoice",
    "ImportNVMFromNVMBND",
    "ImportNVMMSBPart",
    "ImportAllNVMMSBParts",
    "ExportLooseNVM",
    "ExportNVMIntoBinder",
    "ExportNVMIntoNVMBND",
    "ExportNVMMSBPart",
    "ExportAllNVMMSBParts",

    "ImportMCP",
    "QuickImportMCP",
    "ImportMCG",
    "QuickImportMCG",
    "ExportMCG",
    "QuickExportMCGMCP",

    "NVM_PT_ds1_navmesh_import",
    "NVM_PT_ds1_navmesh_export",
    "NVM_PT_ds1_navmesh_tools",

    "NavmeshFaceSettings",
    "AddNVMFaceFlags",
    "RemoveNVMFaceFlags",
    "SetNVMFaceObstacleCount",
    "ResetNVMFaceInfo",

    "MCGDrawSettings",
    "draw_mcg_nodes",
    "draw_mcg_node_labels",
    "draw_mcg_edges",
    "CreateMCGEdgeOperator",
    "SetNodeNavmeshATriangles",
    "SetNodeNavmeshBTriangles",
]

import importlib
import sys

import bmesh
import bpy

from soulstruct.darksouls1r.events.emevd.enums import NavmeshType

if "NVM_PT_nvm_tools" in locals():
    importlib.reload(sys.modules["io_soulstruct.navmesh.utilities"])
    importlib.reload(sys.modules["io_soulstruct.navmesh.export_nvm"])
    importlib.reload(sys.modules["io_soulstruct.navmesh.import_nvm"])

from .nvm import *
from .nvm.utilities import set_face_material
from .nav_graph import *


_navmesh_type_items = [
    (str(nvmt.value), nvmt.name, "") for nvmt in NavmeshType
    if nvmt.value > 0
]


class NVM_PT_ds1_navmesh_import(bpy.types.Panel):
    bl_label = "Navmesh Import"
    bl_idname = "NVM_PT_ds1_navmesh_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct Navmesh"
    bl_options = {'DEFAULT_CLOSED'}

    # noinspection PyUnusedLocal
    def draw(self, context):
        settings = context.scene.soulstruct_settings
        if settings.game_variable_name != "DARK_SOULS_DSR":
            self.layout.label(text="Dark Souls: Remastered only.")
            return

        import_loose_box = self.layout.box()
        import_loose_box.operator(ImportNVM.bl_idname)
        import_loose_box.operator(ImportMCG.bl_idname)
        import_loose_box.operator(ImportMCP.bl_idname)

        quick_box = self.layout.box()
        quick_box.label(text="Game Navmesh Import")
        quick_box.prop(context.scene.soulstruct_settings, "import_bak_file", text="From .BAK File")
        quick_box.prop(context.scene.soulstruct_game_enums, "nvm")
        quick_box.operator(ImportNVMFromNVMBND.bl_idname)
        quick_box.operator(QuickImportMCG.bl_idname)
        quick_box.operator(QuickImportMCP.bl_idname)

        msb_box = self.layout.box()
        msb_box.label(text="Game MSB Part Import")
        msb_box.prop(context.scene.soulstruct_game_enums, "nvm_parts")
        msb_box.operator(ImportNVMMSBPart.bl_idname)
        msb_box.prop(context.scene.nvm_import_settings, "msb_part_name_match")
        msb_box.prop(context.scene.nvm_import_settings, "msb_part_name_match_mode")
        msb_box.prop(context.scene.nvm_import_settings, "include_pattern_in_parent_name")
        msb_box.operator(ImportAllNVMMSBParts.bl_idname, text="Import ALL Matching Parts")


class NVM_PT_ds1_navmesh_export(bpy.types.Panel):
    bl_label = "Navmesh Export"
    bl_idname = "NVM_PT_ds1_navmesh_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct Navmesh"
    bl_options = {'DEFAULT_CLOSED'}

    # noinspection PyUnusedLocal
    def draw(self, context):
        settings = context.scene.soulstruct_settings
        if settings.game_variable_name != "DARK_SOULS_DSR":
            self.layout.label(text="Dark Souls: Remastered only.")
            return

        export_box = self.layout.box()
        export_box.operator(ExportLooseNVM.bl_idname)
        export_box.operator(ExportNVMIntoBinder.bl_idname)
        export_box.operator(ExportMCG.bl_idname, text="Export MCG + MCP")

        quick_box = self.layout.box()
        quick_box.label(text="Game Navmesh Export")
        quick_box.prop(
            context.scene.soulstruct_settings, "detect_map_from_parent", text="Detect Map from Parent"
        )
        quick_box.operator(ExportNVMIntoNVMBND.bl_idname)
        quick_box.operator(QuickExportMCGMCP.bl_idname)

        msb_box = self.layout.box()
        msb_box.label(text="Game MSB Part Export")
        msb_box.prop(
            context.scene.soulstruct_settings, "detect_map_from_parent", text="Detect Map from Parent"
        )
        msb_box.operator(ExportNVMMSBPart.bl_idname)
        msb_box.label(text="Game MSB and NVMBND Complete Export")
        msb_box.operator(ExportAllNVMMSBParts.bl_idname)


class NVM_PT_ds1_navmesh_tools(bpy.types.Panel):
    bl_label = "Navmesh Tools"
    bl_idname = "NVM_PT_ds1_navmesh_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct Navmesh"
    bl_options = {'DEFAULT_CLOSED'}

    # noinspection PyUnusedLocal
    def draw(self, context):
        """Still shown if game is not DSR."""

        self.layout.label(text="MCG Draw Settings:")
        mcg_draw_settings_box = self.layout.box()
        mcg_draw_settings = context.scene.mcg_draw_settings
        mcg_draw_settings_box.prop(mcg_draw_settings, "mcg_parent_name")
        mcg_draw_settings_box.prop(mcg_draw_settings, "mcg_graph_draw_enabled")
        mcg_draw_settings_box.prop(mcg_draw_settings, "mcg_graph_draw_selected_nodes_only")
        mcg_draw_settings_box.prop(mcg_draw_settings, "mcg_graph_color")
        mcg_draw_settings_box.prop(mcg_draw_settings, "mcg_node_label_draw_enabled")
        mcg_draw_settings_box.prop(mcg_draw_settings, "mcg_node_label_font_size")
        mcg_draw_settings_box.prop(mcg_draw_settings, "mcg_node_label_font_color")
        mcg_draw_settings_box.prop(mcg_draw_settings, "mcg_edge_triangles_highlight_enabled")

        mcg_edit_box = self.layout.box()
        mcg_edit_box.operator(CreateMCGEdgeOperator.bl_idname, text="Create MCG Edge")

        self.layout.label(text="Selected Face Indices:")
        selected_faces_box = self.layout.box()
        # noinspection PyTypeChecker
        obj = context.edit_object
        if obj and obj.name.startswith("n") and obj.type == 'MESH' and bpy.context.mode == 'EDIT_MESH':
            self.layout.operator(ResetNVMFaceInfo.bl_idname)
            obj: bpy.types.MeshObject
            bm = bmesh.from_edit_mesh(obj.data)
            try:
                layout_selected_faces(bm, self.layout, context, selected_faces_box)
            finally:
                del bm
        else:
            selected_faces_box.label(text="Select navmesh faces in Edit Mode")


def layout_selected_faces(bm: bmesh.types.BMesh, layout, context, selected_faces_box):
    flags_layer = bm.faces.layers.int.get("nvm_face_flags")
    obstacle_count_layer = bm.faces.layers.int.get("nvm_face_obstacle_count")

    if flags_layer is None or obstacle_count_layer is None:
        # Prompt user to select some faces.
        selected_faces_box.label(text="Select navmesh faces in Edit Mode")
        return

    selected_faces = [f for f in bm.faces if f.select]
    for face in selected_faces:
        face_row = selected_faces_box.row()
        face_flags = face[flags_layer]
        face_obstacle_count = face[obstacle_count_layer]
        suffix = " | ".join([n.name for n in NavmeshType if n.value & face_flags])
        if suffix:
            suffix = f" ({suffix})"
        if face_obstacle_count > 0:
            suffix += f" <{face_obstacle_count} obstacles>"
        # Show selected face index, flag type names, and obstacle count.
        face_row.label(text=f"{face.index}{suffix}")

    if selected_faces:
        # Call refresh operator to tag redraw.
        # refresh_row = selected_faces_box.row()
        # refresh_row.operator(RefreshFaceIndices.bl_idname)

        # Draw operators to add/remove a chosen flag type to/from all selected faces.
        props = context.scene.navmesh_face_settings
        flag_box = layout.box()
        row = flag_box.row()
        row.prop(props, "flag_type")
        row = flag_box.row()
        row.operator(AddNVMFaceFlags.bl_idname, text="Add Flag")
        row.operator(RemoveNVMFaceFlags.bl_idname, text="Remove Flag")

        # Box and button to set obstacle count for selected faces.
        obstacle_box = layout.box()
        row = obstacle_box.row()
        row.prop(props, "obstacle_count")
        row = obstacle_box.row()
        row.operator(SetNVMFaceObstacleCount.bl_idname, text="Set Obstacle Count")

        # Buttons to set navmesh A and B triangles for selected MCG node.
        set_node_box = layout.box()
        set_node_box.operator(SetNodeNavmeshATriangles.bl_idname)
        set_node_box.operator(SetNodeNavmeshBTriangles.bl_idname)

    else:
        # Prompt user to select some faces.
        selected_faces_box.label(text="Select navmesh faces in Edit Mode")

    del bm
