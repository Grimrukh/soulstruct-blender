from __future__ import annotations

__all__ = [
    "NavmeshFaceSettings",
    "RefreshFaceIndices",
    "AddNVMFaceFlags",
    "RemoveNVMFaceFlags",
    "SetNVMFaceObstacleCount",
    "ResetNVMFaceInfo",
]

import bmesh
import bpy

from soulstruct.darksouls1r.events.enums import NavmeshType

from .utilities import set_face_material

# Get all non-default Navmesh Types for Blender `EnumProperty`.
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


class ResetNVMFaceInfo(bpy.types.Operator):
    """Reset all NVM face flags and obstacle counts to default, and create face layers if missing.

    Useful for turning a newly created Blender mesh into a Navmesh.
    """
    bl_idname = "object.reset_nvm_face_info"
    bl_label = "Reset NVM Face Info"
    
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
