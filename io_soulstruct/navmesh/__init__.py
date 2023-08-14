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
    "NavmeshFaceSettings",
    "AddRemoveNVMFaceFlags",
    "SetNVMFaceObstacleCount",
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

from .nvm import ImportNVM, ImportNVMWithBinderChoice, ImportNVMWithMSBChoice, ExportNVM, ExportNVMIntoBinder
from .nvm.utilities import set_face_material
from .nav_graph import ImportMCP, ImportMCG


_navmesh_type_items = [
    (str(nvmt.value), nvmt.name, "") for nvmt in NavmeshType
    if nvmt.value > 0
]


class NavmeshFaceSettings(bpy.types.PropertyGroup):

    flag_action: bpy.props.EnumProperty(
        name="Action",
        items=[
            ("ADD", "Add", "Add a navmesh flag."),
            ("REMOVE", "Remove", "Remove a navmesh flag."),
        ],
        default="ADD",
        description="Whether to add or remove a navmesh flag type.",
    )
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


class AddRemoveNVMFaceFlags(bpy.types.Operator):
    bl_idname = "object.add_remove_nvm_face_flags"
    bl_label = "Add/Remove NVM Face Flags"

    @classmethod
    def poll(cls, context):
        return context.edit_object is not None and context.mode == "EDIT_MESH"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        obj = context.edit_object
        bm = bmesh.from_edit_mesh(obj.data)

        props = context.scene.navmesh_face_settings  # type: NavmeshFaceSettings

        flags_layer = bm.faces.layers.int.get("nvm_face_flags")
        if flags_layer:
            selected_faces = [face for face in bm.faces if face.select]
            for face in selected_faces:
                if props.flag_action == "ADD":
                    face[flags_layer] |= int(props.flag_type)
                elif props.flag_action == "REMOVE":
                    face[flags_layer] &= ~int(props.flag_type)
                else:
                    raise ValueError(f"Invalid action: {props.flag_action}")

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
        obj = context.edit_object
        bm = bmesh.from_edit_mesh(obj.data)

        props = context.scene.navmesh_face_settings  # type: NavmeshFaceSettings

        obstacle_count_layer = bm.faces.layers.int.get("nvm_face_obstacle_count")
        if obstacle_count_layer:
            selected_faces = [face for face in bm.faces if face.select]
            for face in selected_faces:
                face[obstacle_count_layer] = props.obstacle_count

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

        import_navgraph_box = self.layout.box()
        import_navgraph_box.operator(ImportMCP.bl_idname)
        import_navgraph_box.operator(ImportMCG.bl_idname)

        # NOTE: No plans for MCP/MCG export yet. Preferring to edit manually and use Blender just to inspect.

        self.layout.label(text="Selected Face Indices:")
        selected_faces_box = self.layout.box()
        obj = bpy.context.edit_object
        if obj and obj.type == 'MESH' and bpy.context.mode == 'EDIT_MESH':
            bm = bmesh.from_edit_mesh(obj.data)
            flags_layer = bm.faces.layers.int.get("nvm_face_flags")
            obstacle_count_layer = bm.faces.layers.int.get("nvm_face_obstacle_count")
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
                flag_box = self.layout.box()
                row = flag_box.row()
                row.prop(props, "flag_type")
                row = flag_box.row()
                row.prop(props, "flag_action")
                row = flag_box.row()
                row.operator(AddRemoveNVMFaceFlags.bl_idname, text="Add/Remove Flag")

                # Box and button to set obstacle count for selected faces.
                obstacle_box = self.layout.box()
                row = obstacle_box.row()
                row.prop(props, "obstacle_count")
                row = obstacle_box.row()
                row.operator(SetNVMFaceObstacleCount.bl_idname, text="Set Obstacle Count")
            else:
                # Prompt user to select some faces.
                selected_faces_box.label(text="Select faces in Edit Mode")

            del bm
        else:
            selected_faces_box.label(text="Select faces in Edit Mode")
