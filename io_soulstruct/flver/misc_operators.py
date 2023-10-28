from __future__ import annotations

__all__ = [
    "FLVERSettings",
    "SetVertexAlpha",
    "ActivateUVMap1",
    "ActivateUVMap2",
    "ActivateUVMap3",
]

import typing as tp

import bpy

from io_soulstruct.utilities.operators import LoggingOperator


class FLVERSettings(bpy.types.PropertyGroup):
    vertex_alpha: bpy.props.FloatProperty(
        name="Alpha",
        description="Alpha value to set for selected vertices",
        default=1.0,
        min=0.0,
        max=1.0,
    )


class SetVertexAlpha(LoggingOperator):

    bl_idname = "mesh.set_selected_vertex_alpha"
    bl_label = "Set Vertex Alpha"
    bl_description = "Set the alpha value of all selected vertices to a value"

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH"

    def execute(self, context):
        if context.mode != "EDIT_MESH":
            return self.error("Please enter Edit Mode to use this operator.")

        # Go to OBJECT mode
        bpy.ops.object.mode_set(mode="OBJECT")

        # noinspection PyTypeChecker
        mesh = context.active_object  # type: bpy.types.MeshObject
        if mesh is None or mesh.type != "MESH":
            return self.error("Please select a Mesh object.")

        # Get selected vertices
        vertex_indices = [v.index for v in mesh.data.vertices if v.select]

        vertex_colors = mesh.data.vertex_colors["VertexColors"]
        if not vertex_colors:
            return self.error("Mesh does not have a 'VertexColors' layer (which is the name used by FLVERs).")

        for i, loop in enumerate(mesh.data.loops):
            if loop.vertex_index in vertex_indices:
                vertex_colors.data[i].color[3] = context.scene.flver_settings.vertex_alpha

        # Go back to EDIT mode
        bpy.ops.object.mode_set(mode="EDIT")

        return {"FINISHED"}


def set_uv_editor_texture(context, uv_layer_name: str):
    obj = context.active_object

    # Check if the active object and material are valid
    if obj and obj.type == 'MESH' and obj.active_material:
        mat = obj.active_material
        nodes = mat.node_tree.nodes

        # Search for an 'Attribute' node with the given UV layer name
        attr_node = next(
            (node for node in nodes if node.type == 'ATTRIBUTE' and node.attribute_name == uv_layer_name), None
        )

        if not attr_node:
            return

        # Find the first 'Image Texture' node linked to this 'Attribute' node
        for link in mat.node_tree.links:
            if link.from_node == attr_node and link.to_node.type == 'TEX_IMAGE':
                image_node = link.to_node
                image = image_node.image

                # Set the UV Editor texture
                for area in context.screen.areas:
                    if area.type == 'IMAGE_EDITOR':
                        area.spaces.active.image = image

                        # Set the active object UV layer (determines what the Image Editor says!)
                        if uv_layer_name in obj.data.uv_layers:
                            obj.data.uv_layers.active = obj.data.uv_layers[uv_layer_name]

                        return {'FINISHED'}


class ActivateUVMap(LoggingOperator):

    UV_LAYER_NAME: tp.ClassVar[str]

    @classmethod
    def poll(cls, context):
        """Checks if the given `UV_LAYER_NAME` exists in material shader nodes."""
        obj = context.active_object
        if obj and obj.type == 'MESH' and obj.active_material:
            mat = obj.active_material
            nodes = mat.node_tree.nodes
            attr_node = next(
                (node for node in nodes if node.type == 'ATTRIBUTE' and node.attribute_name == cls.UV_LAYER_NAME), None
            )
            return attr_node is not None
        return False

    def execute(self, context):
        return set_uv_editor_texture(context, self.UV_LAYER_NAME)


class ActivateUVMap1(ActivateUVMap):
    bl_idname = "object.activate_uv_map_1"
    bl_label = "Activate UV Map 1"
    bl_description = "Set the UV Editor texture to 'UVMap1', usually the first texture"

    UV_LAYER_NAME = "UVMap1"


class ActivateUVMap2(ActivateUVMap):
    bl_idname = "object.activate_uv_map_2"
    bl_label = "Activate UV Map 2"
    bl_description = "Set the UV Editor texture to 'UVMap1', usually the second texture or light map"

    UV_LAYER_NAME = "UVMap2"


class ActivateUVMap3(ActivateUVMap):
    bl_idname = "object.activate_uv_map_3"
    bl_label = "Activate UV Map 3"
    bl_description = "Set the UV Editor texture to 'UVMap1', usually the light map"

    UV_LAYER_NAME = "UVMap3"
