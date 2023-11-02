from __future__ import annotations

__all__ = [
    "ImportNVM",
    "ImportNVMWithBinderChoice",
    "QuickImportNVM",
    "ExportLooseNVM",
    "ExportNVMIntoBinder",
    "QuickExportNVM",
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
    "MCGDrawSettings",
    "draw_mcg_nodes",
    "draw_mcg_node_labels",
    "draw_mcg_edges",
    "CreateMCGEdgeOperator",
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


class NavmeshFaceSettings(bpy.types.PropertyGroup):

    flag_type: bpy.props.EnumProperty(
        name="Flag",
        items=_navmesh_type_items,
        default="1",  # Disable
        description="Navmesh type to import.",
    )
    obstacle_count: bpy.props.IntProperty(
        name="Obstacle Count",
        default=0,
        min=0,
        max=255,
        description="Number of obstacles on this navmesh face.",
    )


class RefreshFaceIndices(bpy.types.Operator):
    bl_idname = "object.refresh_face_indices"
    bl_label = "Refresh Selected Face Indices"

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def execute(self, context):
        bpy.context.area.tag_redraw()
        return {'FINISHED'}


class AddNVMFaceFlags(bpy.types.Operator):
    bl_idname = "object.add_nvm_face_flags"
    bl_label = "Add NVM Face Flags"

    @classmethod
    def poll(cls, context):
        return context.edit_object is not None and context.mode == "EDIT_MESH"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.edit_object
        if obj is None or obj.type != "MESH":
            return {"CANCELLED"}

        obj: bpy.types.MeshObject
        bm = bmesh.from_edit_mesh(obj.data)

        props = context.scene.navmesh_face_settings  # type: NavmeshFaceSettings

        flags_layer = bm.faces.layers.int.get("nvm_face_flags")
        if flags_layer:
            selected_faces = [face for face in bm.faces if face.select]
            for face in selected_faces:
                face[flags_layer] |= int(props.flag_type)
                set_face_material(bl_mesh=obj.data, bl_face=face, face_flags=face[flags_layer])

            bmesh.update_edit_mesh(obj.data)

        # TODO: Would be nice to remove now-unused materials from the mesh.

        return {"FINISHED"}


class RemoveNVMFaceFlags(bpy.types.Operator):
    bl_idname = "object.remove_nvm_face_flags"
    bl_label = "Remove NVM Face Flags"

    @classmethod
    def poll(cls, context):
        return context.edit_object is not None and context.mode == "EDIT_MESH"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.edit_object
        if obj is None or obj.type != "MESH":
            return {"CANCELLED"}

        obj: bpy.types.MeshObject
        bm = bmesh.from_edit_mesh(obj.data)

        props = context.scene.navmesh_face_settings  # type: NavmeshFaceSettings

        flags_layer = bm.faces.layers.int.get("nvm_face_flags")
        if flags_layer:
            selected_faces = [face for face in bm.faces if face.select]
            for face in selected_faces:
                face[flags_layer] &= ~int(props.flag_type)
                set_face_material(bl_mesh=obj.data, bl_face=face, face_flags=face[flags_layer])

            bmesh.update_edit_mesh(obj.data)

        # TODO: Would be nice to remove now-unused materials from the mesh.

        return {"FINISHED"}


class SetNVMFaceObstacleCount(bpy.types.Operator):
    bl_idname = "object.set_nvm_face_obstacle_count"
    bl_label = "Set NVM Face Obstacle Count"

    @classmethod
    def poll(cls, context):
        return context.edit_object is not None and context.mode == "EDIT_MESH"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.edit_object
        if obj is None or obj.type != "MESH":
            return {"CANCELLED"}

        obj: bpy.types.MeshObject
        bm = bmesh.from_edit_mesh(obj.data)

        props = context.scene.navmesh_face_settings  # type: NavmeshFaceSettings

        obstacle_count_layer = bm.faces.layers.int.get("nvm_face_obstacle_count")
        if obstacle_count_layer:
            selected_faces = [face for face in bm.faces if face.select]
            for face in selected_faces:
                face[obstacle_count_layer] = props.obstacle_count

            bmesh.update_edit_mesh(obj.data)

        return {"FINISHED"}


class NVM_PT_ds1_navmesh_import(bpy.types.Panel):
    bl_label = "DS1 Navmesh Import"
    bl_idname = "NVM_PT_ds1_navmesh_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct"
    bl_options = {'DEFAULT_CLOSED'}

    # noinspection PyUnusedLocal
    def draw(self, context):
        import_loose_box = self.layout.box()
        import_loose_box.operator(ImportNVM.bl_idname)
        import_loose_box.operator(ImportMCG.bl_idname)
        import_loose_box.operator(ImportMCP.bl_idname)

        quick_box = self.layout.box()
        quick_box.label(text="Quick Game Import")
        quick_box.prop(context.scene.soulstruct_global_settings, "use_bak_file", text="From .BAK File")
        quick_box.prop(context.scene.soulstruct_global_settings, "msb_import_mode", text="MSB Import Mode")
        quick_box.prop(context.scene.game_files, "nvm")
        quick_box.operator(QuickImportNVM.bl_idname)
        quick_box.operator(QuickImportMCG.bl_idname)
        quick_box.operator(QuickImportMCP.bl_idname)


class NVM_PT_ds1_navmesh_export(bpy.types.Panel):
    bl_label = "DS1 Navmesh Export"
    bl_idname = "NVM_PT_ds1_navmesh_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct"
    bl_options = {'DEFAULT_CLOSED'}

    # noinspection PyUnusedLocal
    def draw(self, context):
        export_box = self.layout.box()
        export_box.operator(ExportLooseNVM.bl_idname)
        export_box.operator(ExportNVMIntoBinder.bl_idname)
        export_box.operator(ExportMCG.bl_idname, text="Export MCG + MCP")

        quick_box = export_box.box()
        quick_box.label(text="Quick Game Export")
        quick_box.prop(
            context.scene.soulstruct_global_settings, "detect_map_from_parent", text="Detect Map from Parent"
        )
        quick_box.prop(context.scene.soulstruct_global_settings, "msb_export_mode", text="MSB Export Mode")
        quick_box.operator(QuickExportNVM.bl_idname)
        quick_box.operator(QuickExportMCGMCP.bl_idname)


class NVM_PT_ds1_navmesh_tools(bpy.types.Panel):
    bl_label = "DS1 Navmesh Tools"
    bl_idname = "NVM_PT_ds1_navmesh_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct"
    bl_options = {'DEFAULT_CLOSED'}

    # noinspection PyUnusedLocal
    def draw(self, context):

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
        if obj and obj.type == 'MESH' and bpy.context.mode == 'EDIT_MESH':
            obj: bpy.types.MeshObject
            bm = bmesh.from_edit_mesh(obj.data)
            layout_selected_faces(bm, self.layout, context, selected_faces_box)
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
    else:
        # Prompt user to select some faces.
        selected_faces_box.label(text="Select navmesh faces in Edit Mode")

    del bm
