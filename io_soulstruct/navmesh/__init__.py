from __future__ import annotations

__all__ = [
    "ImportNVM",
    "ImportNVMWithBinderChoice",
    "ImportNVMWithMSBChoice",
    "ExportNVM",
    "ExportNVMIntoBinder",
    "ImportMCP",
    "ImportMCG",
    "NVM_PT_navmesh_tools",
    "NavmeshFlagSettings",
    "AddRemoveNVMFaceFlags",
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

from io_soulstruct.navmesh.export_nvm import ExportNVM, ExportNVMIntoBinder
from io_soulstruct.navmesh.import_nvm import ImportNVM, ImportNVMWithBinderChoice, ImportNVMWithMSBChoice
from io_soulstruct.navmesh.import_navinfo import ImportMCP, ImportMCG


_navmesh_type_items = [
    (str(nvmt.value), nvmt.name, "") for nvmt in NavmeshType
    if nvmt != NavmeshType.Default
]


class NavmeshFlagSettings(bpy.types.PropertyGroup):

    action: bpy.props.EnumProperty(
        name="Navmesh Flag Action",
        items=[
            ("ADD", "Add", "Add a navmesh flag."),
            ("REMOVE", "Remove", "Remove a navmesh flag."),
        ],
        default="ADD",
        description="Whether to import or export navmesh flags.",
    )
    flag_type: bpy.props.EnumProperty(
        items=_navmesh_type_items,
        name="Navmesh Type",
        default="1",  # Disable
        description="Navmesh type to import.",
    )


class RefreshFaceIndices(bpy.types.Operator):
    bl_idname = "object.refresh_face_indices"
    bl_label = "Refresh Selected Face Indices"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        bpy.context.area.tag_redraw()
        return {'FINISHED'}


class AddRemoveNVMFaceFlags(bpy.types.Operator):
    bl_idname = "object.add_remove_nvm_face_flags"
    bl_label = "Add/Remove NVM Face Flags"

    @classmethod
    def poll(cls, context):
        return context.edit_object is not None and context.mode == "EDIT_MESH"

    def execute(self, context):
        obj = context.edit_object
        bm = bmesh.from_edit_mesh(obj.data)

        props = context.scene.navmesh_flag_props  # type: NavmeshFlagSettings

        flags_layer = bm.faces.layers.int.get("nvm_face_flags")
        if flags_layer:
            selected_faces = [face for face in bm.faces if face.select]
            for face in selected_faces:
                if props.action == "ADD":
                    face[flags_layer] |= int(props.flag_type)
                elif props.action == "REMOVE":
                    face[flags_layer] &= ~int(props.flag_type)
                else:
                    raise ValueError(f"Invalid action: {props.action}")

                # TODO: set/create face material name to match new flags

            bmesh.update_edit_mesh(obj.data)

        return {"FINISHED"}


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

        # TODO: export NavGraph

        self.layout.label(text="Selected Face Indices:")
        selected_faces_box = self.layout.box()
        obj = bpy.context.edit_object
        if obj and obj.type == 'MESH' and bpy.context.mode == 'EDIT_MESH':
            bm = bmesh.from_edit_mesh(obj.data)
            flags_layer = bm.faces.layers.int.get("nvm_face_flags")
            selected_faces = [f for f in bm.faces if f.select]
            for face in selected_faces:
                face_row = selected_faces_box.row()
                face_flags = face[flags_layer]
                type_name = " | ".join([n.name for n in NavmeshType if n.value & face_flags])
                if type_name:
                    type_name = f" ({type_name})"
                # Show selected face index and flag type names.
                face_row.label(text=f"{face.index}{type_name}")

            if selected_faces:
                # Call refresh operator to tag redraw.
                # refresh_row = selected_faces_box.row()
                # refresh_row.operator(RefreshFaceIndices.bl_idname)

                # Draw operators to add/remove a chosen flag type to/from all selected faces.
                props = context.scene.navmesh_flag_props
                row = self.layout.row()
                row.prop(props, "flag_type")
                row = self.layout.row()
                row.prop(props, "action")
                row = self.layout.row()
                row.operator(AddRemoveNVMFaceFlags.bl_idname)
            else:
                # Prompt user to select some faces.
                selected_faces_box.label(text="Select faces in Edit Mode")

            del bm
        else:
            selected_faces_box.label(text="Select faces in Edit Mode")
