from __future__ import annotations

__all__ = [
    "NavmeshFaceSettings",
    "RefreshFaceIndices",
    "AddNVMFaceFlags",
    "RemoveNVMFaceFlags",
    "SetNVMFaceObstacleCount",
    "ResetNVMFaceInfo",
    "AddNVMEventEntityTriangleIndex",
    "RemoveNVMEventEntityTriangleIndex",
]

import bmesh
import bpy

from soulstruct.base.events.enums import NavmeshFlag

from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import LoggingOperator
from .utilities import set_face_material

# Get all non-default `NavmeshFlag` values for Blender `EnumProperty`.
_navmesh_flag_items = [
    (str(flag.value), flag.name, "") for flag in NavmeshFlag
    if flag.value > 0
]


class NavmeshFaceSettings(bpy.types.PropertyGroup):

    navmesh_flag: bpy.props.EnumProperty(
        name="Flag",
        items=_navmesh_flag_items,
        default="1",  # Disable
        description="Navmesh type to add or remove",
    )
    obstacle_count: bpy.props.IntProperty(
        name="Obstacle Count",
        default=0,
        min=0,
        max=255,
        description="Number of obstacles on this navmesh face.",
    )


class RefreshFaceIndices(LoggingOperator):
    bl_idname = "mesh.refresh_face_indices"
    bl_label = "Refresh Selected Face Indices"
    bl_description = "Refresh the list of selected face indices"

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def execute(self, context):
        bpy.context.area.tag_redraw()
        return {"FINISHED"}


class AddNVMFaceFlags(LoggingOperator):
    bl_idname = "mesh.add_nvm_face_flags"
    bl_label = "Add NVM Face Flags"
    bl_description = "Add the selected NavmeshFlag bit flag to all selected faces"

    @classmethod
    def poll(cls, context):
        return context.edit_object is not None and context.mode == "EDIT_MESH"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.edit_object
        if obj is None or obj.type != "MESH":
            return self.error("No Mesh selected.")

        obj: bpy.types.MeshObject
        bm = bmesh.from_edit_mesh(obj.data)

        props = context.scene.navmesh_face_settings
        navmesh_flag = int(props.navmesh_flag)

        flags_layer = bm.faces.layers.int.get("nvm_face_flags")
        if flags_layer:
            selected_faces = [face for face in bm.faces if face.select]
            for face in selected_faces:
                face[flags_layer] |= navmesh_flag
                set_face_material(bl_mesh=obj.data, bl_face=face, face_flags=face[flags_layer])

            bmesh.update_edit_mesh(obj.data)

        # TODO: Would be nice to remove now-unused materials from the mesh.

        return {"FINISHED"}


class RemoveNVMFaceFlags(LoggingOperator):
    bl_idname = "mesh.remove_nvm_face_flags"
    bl_label = "Remove NVM Face Flags"
    bl_description = "Remove the selected NavmeshFlag bit flag from all selected faces"

    @classmethod
    def poll(cls, context):
        return context.edit_object is not None and context.mode == "EDIT_MESH"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.edit_object
        if obj is None or obj.type != "MESH":
            return self.error("No Mesh selected.")

        obj: bpy.types.MeshObject
        bm = bmesh.from_edit_mesh(obj.data)

        props = context.scene.navmesh_face_settings
        navmesh_flag = int(props.navmesh_flag)

        flags_layer = bm.faces.layers.int.get("nvm_face_flags")
        if flags_layer:
            selected_faces = [face for face in bm.faces if face.select]
            for face in selected_faces:
                face[flags_layer] &= ~navmesh_flag
                set_face_material(bl_mesh=obj.data, bl_face=face, face_flags=face[flags_layer])

            bmesh.update_edit_mesh(obj.data)

        # TODO: Would be nice to remove now-unused materials from the mesh.

        return {"FINISHED"}


class SetNVMFaceObstacleCount(LoggingOperator):
    bl_idname = "mesh.set_nvm_face_obstacle_count"
    bl_label = "Set NVM Face Obstacle Count"
    bl_description = "Set the obstacle count for all selected faces"

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

        props = context.scene.navmesh_face_settings

        obstacle_count_layer = bm.faces.layers.int.get("nvm_face_obstacle_count")
        if obstacle_count_layer:
            selected_faces = [face for face in bm.faces if face.select]
            for face in selected_faces:
                face[obstacle_count_layer] = props.obstacle_count

            bmesh.update_edit_mesh(obj.data)

        return {"FINISHED"}


class ResetNVMFaceInfo(LoggingOperator):
    """Reset all NVM face flags and obstacle counts to default, and create face layers if missing.

    Useful for turning a newly created Blender mesh into a Navmesh.
    """
    bl_idname = "mesh.reset_nvm_face_info"
    bl_label = "Reset NVM Face Info"
    bl_description = "Reset NVM face flags and obstacle counts of selected faces to default (both zero)"
    
    DEFAULT_FLAGS = 0
    DEFAULT_OBSTACLE_COUNT = 0

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

        # TODO: Can probably use `verify()`.
        flags_layer = bm.faces.layers.int.get("nvm_face_flags")
        if flags_layer is None:
            flags_layer = bm.faces.layers.int.new("nvm_face_flags")
        obstacle_count_layer = bm.faces.layers.int.get("nvm_face_obstacle_count")
        if obstacle_count_layer is None:
            obstacle_count_layer = bm.faces.layers.int.new("nvm_face_obstacle_count")

        for f_i, face in enumerate(bm.faces):
            face[flags_layer] = self.DEFAULT_FLAGS
            face[obstacle_count_layer] = self.DEFAULT_OBSTACLE_COUNT

        bmesh.update_edit_mesh(obj.data)

        return {"FINISHED"}


class AddNVMEventEntityTriangleIndex(bpy.types.Operator):
    bl_idname = "nvm_event_entity.add_triangle_index"
    bl_label = "Add Triangle"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object and context.active_object.soulstruct_type == SoulstructType.NVM_EVENT_ENTITY

    def execute(self, context):
        nvm_event_entity = context.active_object
        nvm_event_entity.NVM_EVENT_ENTITY.triangle_indices.add()
        return {'FINISHED'}


class RemoveNVMEventEntityTriangleIndex(bpy.types.Operator):
    bl_idname = "nvm_event_entity.remove_triangle_index"
    bl_label = "Remove Triangle"

    @classmethod
    def poll(cls, context):
        return (
            context.active_object
            and context.active_object.soulstruct_type == SoulstructType.NVM_EVENT_ENTITY
            and len(context.active_object.NVM_EVENT_ENTITY.triangle_indices) > 0
        )

    def execute(self, context):
        obj = context.active_object
        index = obj.NVM_EVENT_ENTITY.triangle_index
        obj.NVM_EVENT_ENTITY.triangle_indices.remove(index)
        obj.NVM_EVENT_ENTITY.triangle_index = max(0, index - 1)
        return {'FINISHED'}
