"""Miscellaneous UV operators that only make sense for FLVER models.

Unlike most Soulstruct operators (which appear in the View 3D window), some of these appear in the UV Editor window.
"""
from __future__ import annotations

__all__ = [
    "ActivateUVMap",
    "FastUVUnwrap",
    "FastUVUnwrapIslands",
    "RotateUVMapClockwise90",
    "RotateUVMapCounterClockwise90",
    "AddRandomUVTileOffsets",
]

import math
import random
import typing as tp

import bpy
import bmesh
from mathutils import Matrix, Vector

from io_soulstruct.utilities import LoggingOperator


# noinspection PyUnusedLocal
def _get_uv_layer_items(self, context) -> list[tuple[str, str, str]]:
    if context.active_object and context.active_object.type == "MESH":
        ActivateUVMap.UV_LAYER_NAMES = [
            (uv.name, uv.name, uv.name)
            for uv in context.active_object.data.uv_layers
        ]
    else:
        ActivateUVMap.UV_LAYER_NAMES = [("NONE", "None", "No UV map")]
    return ActivateUVMap.UV_LAYER_NAMES


class ActivateUVMap(LoggingOperator):

    bl_idname = "object.activate_uv_map"
    bl_label = "Activate UV Map"
    bl_description = "Set the UV Editor texture to the given UV map for the active Mesh object"

    # Persistent storage for dynamic enum.
    UV_LAYER_NAMES: tp.ClassVar[list[tuple[str, str, str]]] = [("NONE", "None", "No UV map")]

    uv_layer_name: bpy.props.EnumProperty(
        name="UV Layer Name",
        description="Name of the UV layer to activate in the UV Editor",
        items=_get_uv_layer_items,
    )

    @classmethod
    def poll(cls, context) -> bool:
        """Checks for an active Mesh object."""
        return context.active_object and context.active_object.type == "MESH"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context) -> set[str]:
        if self.uv_layer_name == "NONE":
            return self.error("No UV layer selected.")

        uv_layer_name = self.uv_layer_name
        # noinspection PyTypeChecker
        obj = context.active_object  # type: bpy.types.MeshObject

        # Check if the active object and material are valid
        if not obj or obj.type != 'MESH' or not obj.active_material:
            return self.error("No active Mesh object or material found.")

        mat = obj.active_material
        nodes = mat.node_tree.nodes

        # Search for an 'Attribute' node with the given UV layer name
        attr_node = next(
            (node for node in nodes if node.type == 'ATTRIBUTE' and node.attribute_name == uv_layer_name), None
        )

        if not attr_node:
            return self.error(f"Could not find UV attribute node for '{uv_layer_name}'.")

        # Find the first 'Image Texture' node linked to this 'Attribute' node
        for link in mat.node_tree.links:
            if link.from_node == attr_node and link.to_node.type == 'TEX_IMAGE':
                # noinspection PyTypeChecker
                image_node = link.to_node  # type: bpy.types.ShaderNodeTexImage
                image = image_node.image

                # Set the UV Editor texture
                for area in context.screen.areas:
                    if area.type == 'IMAGE_EDITOR':
                        area.spaces.active.image = image

                        # Set the active object UV layer (determines what the Image Editor says!)
                        if uv_layer_name in obj.data.uv_layers:
                            obj.data.uv_layers.active = obj.data.uv_layers[uv_layer_name]

                        return {"FINISHED"}

        return self.error(f"No textures found that were linked to by the '{uv_layer_name}' attribute node.")


class FastUVUnwrap(LoggingOperator):

    bl_idname = "uv.fast_uv_unwrap"
    bl_label = "Fast UV Unwrap"
    bl_description = "Unwrap selected faces using the 'UV Unwrap' operator, then scale their UVs using given value"

    @classmethod
    def poll(cls, context) -> bool:
        return context.mode == "EDIT_MESH"

    def execute(self, context):

        # Get all selected face loops (of edit object).
        # noinspection PyTypeChecker
        edit_mesh = context.edit_object.data  # type: bpy.types.Mesh
        bm = bmesh.from_edit_mesh(edit_mesh)
        uv_layer = bm.loops.layers.uv.active
        if not uv_layer:
            return self.error("No active UV layer to scale.")

        tool_settings = context.scene.flver_tool_settings
        bpy.ops.uv.unwrap()  # default arguments

        # TODO: Could probably be more efficient outside `bmesh`.
        for face in [face for face in bm.faces if face.select]:
            for loop in face.loops:
                loop[uv_layer].uv *= tool_settings.uv_scale

        bmesh.update_edit_mesh(edit_mesh)
        del bm

        return {"FINISHED"}


class FastUVUnwrapIslands(LoggingOperator):

    bl_idname = "uv.fast_uv_unwrap_islands"
    bl_label = "Fast UV Unwrap Islands"
    bl_description = (
        "Independently unwrap and scale all islands (delimited by seams) that contain at least one selected face"
    )

    @classmethod
    def poll(cls, context) -> bool:
        return context.mode == "EDIT_MESH"

    def execute(self, context):

        # Get all selected face loops (of edit object).
        # noinspection PyTypeChecker
        edit_mesh = context.edit_object.data  # type: bpy.types.Mesh
        bm = bmesh.from_edit_mesh(edit_mesh)
        uv_layer = bm.loops.layers.uv.active
        if not uv_layer:
            return self.error("No active UV layer to scale.")

        tool_settings = context.scene.flver_tool_settings

        for face in bm.faces:
            face.tag = False  # tracks visited below

        initial_selected_faces = [face for face in bm.faces if face.select]  # for restoring

        for face in initial_selected_faces:
            if face.tag:
                continue  # island already visited

            self.deselect_all()
            face.select = True
            bpy.ops.mesh.select_linked(delimit={'SEAM'})

            bpy.ops.uv.unwrap()  # default arguments

            # Record face island and scale UV loops.
            for f in bm.faces:
                if not f.select:
                    continue
                f.tag = True
                for loop in face.loops:
                    loop[uv_layer].uv *= tool_settings.uv_scale

        bmesh.update_edit_mesh(edit_mesh)
        del bm

        return {"FINISHED"}


def _rotate_uv_map(operator: LoggingOperator, context, angle_rad: float) -> set[str]:

    # Get all selected face loops (of edit object).
    # noinspection PyTypeChecker
    edit_mesh = context.edit_object.data  # type: bpy.types.Mesh
    bm = bmesh.from_edit_mesh(edit_mesh)
    uv_layer = bm.loops.layers.uv.active
    if not uv_layer:
        return operator.error("No active UV layer to rotate.")

    # Collect all selected UV coordinates (all loops of all selected faces).
    selected_uvs = []
    for face in bm.faces:
        if face.select:
            for loop in face.loops:
                uv = loop[uv_layer].uv
                selected_uvs.append(uv)

    if not selected_uvs:
        print("No UVs selected.")
        return operator.error("No UVs selected.")

    uv_center = sum(selected_uvs, Vector((0.0, 0.0))) / len(selected_uvs)
    rotation_matrix = Matrix.Rotation(angle_rad, 2)  # 2D rotation matrix
    for uv in selected_uvs:
        uv.xy = uv_center + rotation_matrix @ (uv.xy - uv_center)

    bmesh.update_edit_mesh(edit_mesh)
    del bm

    return {"FINISHED"}


class RotateUVMapClockwise90(LoggingOperator):

    bl_idname = "uv.rotate_uv_map_clockwise_90"
    bl_label = "Rotate UVs CW 90°"
    bl_description = "Rotate the UV map of selected faces clockwise by 90°"

    @classmethod
    def poll(cls, context) -> bool:
        return context.mode == "EDIT_MESH"

    def execute(self, context):
        return _rotate_uv_map(self, context, -math.pi / 2.0)


class RotateUVMapCounterClockwise90(LoggingOperator):

    bl_idname = "uv.rotate_uv_map_counter_clockwise_90"
    bl_label = "Rotate UVs CCW 90°"
    bl_description = "Rotate the UV map of selected faces counter-clockwise by 90°"

    @classmethod
    def poll(cls, context) -> bool:
        return context.mode == "EDIT_MESH"

    def execute(self, context):
        return _rotate_uv_map(self, context, math.pi / 2.0)


class AddRandomUVTileOffsets(LoggingOperator):

    bl_idname = "uv.add_random_uv_tile_offsets"
    bl_label = "Add Random UV Tile Offsets"
    bl_description = "Add random offsets to UV coordinates to 'randomly choose' one of the texture's tiles"

    u_tile_count: bpy.props.FloatProperty(
        name="U Tile Count",
        description="Number of texture tiles in U dimension",
        min=2,
        default=4,
    )

    v_tile_count: bpy.props.FloatProperty(
        name="V Tile Count",
        description="Number of texture tiles in V dimension",
        min=2,
        default=4,
    )

    @classmethod
    def poll(cls, context) -> bool:
        return context.mode == "EDIT_MESH"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):

        # noinspection PyTypeChecker
        mesh = context.edit_object.data  # type: bpy.types.Mesh

        bm = bmesh.from_edit_mesh(mesh)

        uv_layer = bm.loops.layers.uv.active
        if not uv_layer:
            return self.error("No active UV map found.")

        # Process each selected face
        for face in bm.faces:
            if face.select:  # Only process selected faces

                # Randomly choose an integer tile offset for each dimension.
                u_tile_offset = random.randint(0, self.u_tile_count)
                v_tile_offset = random.randint(0, self.v_tile_count)

                # Compute shift in UV coordinates [0, 1].
                offset_u = 1 / self.u_tile_count * u_tile_offset
                offset_v = 1 / self.v_tile_count * v_tile_offset

                # Apply the offset to all loops' UVs for this face.
                for loop in face.loops:
                    uv = loop[uv_layer]
                    uv.uv.x += offset_u
                    uv.uv.y += offset_v

        bmesh.update_edit_mesh(mesh)
        return {"FINISHED"}
