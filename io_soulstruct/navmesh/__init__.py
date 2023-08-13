from __future__ import annotations

__all__ = [
    "ImportNVM",
    "ImportNVMWithBinderChoice",
    "ImportNVMWithMSBChoice",
    "ExportNVM",
    "ExportNVMIntoBinder",
    "ImportMCP",
    "ImportMCG",
    "NVM_PT_navmesh_tools"
]

import importlib
import sys

import bmesh
import bpy

if "NVM_PT_nvm_tools" in locals():
    importlib.reload(sys.modules["io_soulstruct.navmesh.utilities"])
    importlib.reload(sys.modules["io_soulstruct.navmesh.export_nvm"])
    importlib.reload(sys.modules["io_soulstruct.navmesh.import_nvm"])

from io_soulstruct.navmesh.export_nvm import ExportNVM, ExportNVMIntoBinder
from io_soulstruct.navmesh.import_nvm import ImportNVM, ImportNVMWithBinderChoice, ImportNVMWithMSBChoice
from io_soulstruct.navmesh.import_navinfo import ImportMCP, ImportMCG


class RefreshFaceIndices(bpy.types.Operator):
    bl_idname = "object.refresh_face_indices"
    bl_label = "Refresh Selected Face Indices"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        bpy.context.area.tag_redraw()
        return {'FINISHED'}


class NVM_PT_navmesh_tools(bpy.types.Panel):
    bl_label = "DS1 Navmesh Tools"
    bl_idname = "NVM_PT_navmesh_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Navmesh"

    # noinspection PyUnusedLocal
    def draw(self, context):
        import_box = self.layout.box()
        import_box.operator(ImportNVM.bl_idname)

        export_box = self.layout.box()
        export_box.operator(ExportNVM.bl_idname)
        export_box.operator(ExportNVMIntoBinder.bl_idname)

        import_navinfo_box = self.layout.box()
        import_navinfo_box.operator(ImportMCP.bl_idname)
        import_navinfo_box.operator(ImportMCG.bl_idname)

        # TODO: export navinfo

        self.layout.label(text="Selected Face Indices:")
        selected_faces_box = self.layout.box()
        obj = bpy.context.edit_object
        if obj and obj.type == 'MESH' and bpy.context.mode == 'EDIT_MESH':
            bm = bmesh.from_edit_mesh(obj.data)

            selected_faces = [f for f in bm.faces if f.select]

            for face in selected_faces:
                row = selected_faces_box.row()
                try:
                    material_name = obj.data.materials[face.material_index].name
                    material_name = material_name.removeprefix("Navmesh Flag ").split(".")[0]
                except IndexError:
                    material_name = "???"
                row.label(text=f"{face.index} ({material_name})")

            if selected_faces:
                row = selected_faces_box.row()
                row.operator("object.refresh_face_indices")
            else:
                selected_faces_box.label(text="Select faces in Edit Mode")

            del bm
        else:
            selected_faces_box.label(text="Select faces in Edit Mode")
