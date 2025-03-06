"""Miscellaneous Mesh operators that only make sense for FLVER models."""
from __future__ import annotations

__all__ = [
    "SelectDisplayMaskID",
    "SelectUnweightedVertices",
    "SetSmoothCustomNormals",
    "SetVertexAlpha",
    "InvertVertexAlpha",
]

import bpy
import bmesh

from soulstruct.base.models.flver import Material

from io_soulstruct.utilities import LoggingOperator


class SelectDisplayMaskID(LoggingOperator):

    bl_idname = "mesh.select_display_mask_id"
    bl_label = "Select Display Mask ID"
    bl_description = "Select all faces with materials labelled with the given display mask ('#XX#')"

    @classmethod
    def poll(cls, context) -> bool:
        return context.mode == "EDIT_MESH"

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must be in Edit Mode.")

        # Get edit mesh.
        # noinspection PyTypeChecker
        mesh = context.edit_object.data  # type: bpy.types.Mesh

        bm = bmesh.from_edit_mesh(mesh)

        # Select faces with material mask ID.
        display_mask_id = context.scene.flver_tool_settings.display_mask_id

        count = 0
        if display_mask_id == "-1":
            # Select all faces with a material that has NO mask.
            for face in bm.faces:
                material = mesh.materials[face.material_index]
                face.select = Material.DISPLAY_MASK_RE.match(material.name) is None
                count += face.select
            self.info(f"Selected {count} faces with no material display mask.")
        else:
            # Select all faces with a material that has the given mask.
            for face in bm.faces:
                material = mesh.materials[face.material_index]
                if match := Material.DISPLAY_MASK_RE.match(material.name):
                    if match.group(1) == display_mask_id:
                        face.select = True
                        count += 1
                    else:
                        face.select = False
                else:
                    face.select = False
            self.info(f"Selected {count} faces with material display mask {display_mask_id}.")

        bmesh.update_edit_mesh(mesh)

        return {"FINISHED"}


class SelectUnweightedVertices(LoggingOperator):

    bl_idname = "mesh.select_unweighted_vertices"
    bl_label = "Select Unweighted Vertices"
    bl_description = "Enter Edit Mode on active mesh and select all vertices that are not weighted to any bones"

    @classmethod
    def poll(cls, context) -> bool:
        return context.active_object and context.active_object.type == "MESH"

    def execute(self, context):

        if context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return self.error("Please select a Mesh object.")
        # noinspection PyTypeChecker
        mesh = obj.data  # type: bpy.types.Mesh

        count = 0
        for vert in mesh.vertices:
            vert.select = not vert.groups
            count += vert.select

        # Enter Edit mode.
        bpy.ops.object.mode_set(mode="EDIT")

        self.info(f"Selected {count} unweighted vertices on mesh '{obj.name}'.")
        return {"FINISHED"}


class SetSmoothCustomNormals(LoggingOperator):

    bl_idname = "mesh.set_smooth_custom_normals"
    bl_label = "Set Smooth Custom Normals"
    bl_description = (
        "Set all vertex normals from faces for all mesh faces (if in Object Mode) or selected faces "
        "(if in Edit Mode), then set custom normals from averages of faces. Suitable for most models"
    )

    @classmethod
    def poll(cls, context) -> bool:
        if context.mode == "OBJECT":
            return context.active_object is not None and context.active_object.type == "MESH"
        return context.mode == "EDIT_MESH"

    def execute(self, context):
        is_object = context.mode == "OBJECT"
        if is_object:
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.set_normals_from_faces()
        bpy.ops.mesh.average_normals(average_type="CUSTOM_NORMAL")
        if is_object:
            # Return to Object Mode.
            bpy.ops.object.mode_set(mode="OBJECT")

        return {"FINISHED"}


class SetVertexAlpha(LoggingOperator):

    bl_idname = "mesh.set_selected_vertex_alpha"
    bl_label = "Set Vertex Alpha"
    bl_description = "Set the alpha value of all selected vertices to a value"

    @classmethod
    def poll(cls, context) -> bool:
        return context.mode == "EDIT_MESH" and context.active_object and context.active_object.type == "MESH"

    def execute(self, context):
        if context.mode != "EDIT_MESH":
            return self.error("Please enter Edit Mode to use this operator.")

        tool_settings = context.scene.flver_tool_settings

        # noinspection PyTypeChecker
        mesh = context.active_object.data  # type: bpy.types.Mesh

        bm = bmesh.from_edit_mesh(mesh)

        vertex_colors = bm.loops.layers.color.get(tool_settings.vertex_color_layer_name)
        if not vertex_colors:
            bm.free()
            return self.error(f"Mesh does not have a '{tool_settings.vertex_color_layer_name}' vertex color layer.")

        alpha = tool_settings.vertex_alpha
        count = 0
        for face in bm.faces:
            if tool_settings.set_selected_face_vertex_alpha_only and not face.select:
                continue
            for loop in face.loops:
                if loop.vert.select:
                    loop[vertex_colors][3] = alpha
                    count += 1

        self.info(f"Set vertex alpha {alpha:.03f} for {count} selected vertices/loops.")
        bmesh.update_edit_mesh(mesh)
        return {"FINISHED"}


class InvertVertexAlpha(LoggingOperator):

    bl_idname = "mesh.invert_selected_vertex_alpha"
    bl_label = "Invert Vertex Alpha"
    bl_description = "Invert (subtract from 1) the alpha value of selected vertex color layer for all selected vertices"

    @classmethod
    def poll(cls, context) -> bool:
        return context.mode == "EDIT_MESH"

    def execute(self, context):
        if context.mode != "EDIT_MESH":
            return self.error("Please enter Edit Mode to use this operator.")

        tool_settings = context.scene.flver_tool_settings

        # noinspection PyTypeChecker
        mesh = context.active_object.data  # type: bpy.types.Mesh

        bm = bmesh.from_edit_mesh(mesh)

        vertex_colors = bm.loops.layers.color.get(tool_settings.vertex_color_layer_name)
        if not vertex_colors:
            bm.free()
            return self.error(f"Mesh does not have a '{tool_settings.vertex_color_layer_name}' vertex color layer.")

        count = 0
        for face in bm.faces:
            if tool_settings.set_selected_face_vertex_alpha_only and not face.select:
                continue
            for loop in face.loops:
                if loop.vert.select:
                    # Invert alpha (subtract from 1).
                    loop[vertex_colors][3] = 1.0 - loop[vertex_colors][3]
                    count += 1

        self.info(f"Inverted vertex alpha for {count} selected vertices/loops.")
        bmesh.update_edit_mesh(mesh)
        return {"FINISHED"}
