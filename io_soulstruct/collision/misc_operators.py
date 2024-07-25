from __future__ import annotations

__all__ = [
    "SelectHiResFaces",
    "SelectLoResFaces",
]

import bpy

from io_soulstruct.utilities.operators import LoggingOperator


class SelectHiResFaces(LoggingOperator):
    bl_idname = "object.select_hi_res_faces"
    bl_label = "Select Hi-Res Collision Faces"
    bl_description = "Select all hi-res collision faces (materials with '(Hi)') in the edited object"

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH" and context.edit_object is not None

    def execute(self, context):
        bpy.ops.mesh.select_all(action="DESELECT")
        # noinspection PyTypeChecker
        obj = context.edit_object  # type: bpy.types.MeshObject
        bpy.ops.object.mode_set(mode="OBJECT")
        if obj.type != "MESH":
            return self.error("Selected object is not a mesh.")
        for face in obj.data.polygons:
            if "(Hi)" in obj.data.materials[face.material_index].name:
                face.select = True
        bpy.ops.object.mode_set(mode="EDIT")
        return {"FINISHED"}


class SelectLoResFaces(LoggingOperator):
    bl_idname = "object.select_lo_res_faces"
    bl_label = "Select Lo-Res Collision Faces"
    bl_description = "Select all lo-res collision faces (materials with '(Lo)') in the edited object"

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH" and context.edit_object is not None

    def execute(self, context):
        bpy.ops.mesh.select_all(action="DESELECT")
        # noinspection PyTypeChecker
        obj = context.edit_object  # type: bpy.types.MeshObject
        bpy.ops.object.mode_set(mode="OBJECT")
        if obj.type != "MESH":
            return self.error("Selected object is not a mesh.")
        for face in obj.data.polygons:
            if "(Lo)" in obj.data.materials[face.material_index].name:
                face.select = True
        bpy.ops.object.mode_set(mode="EDIT")
        return {"FINISHED"}
