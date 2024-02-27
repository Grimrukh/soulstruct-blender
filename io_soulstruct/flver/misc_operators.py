from __future__ import annotations

__all__ = [
    "FLVERToolSettings",
    "SetVertexAlpha",
    "ActivateUVMap1",
    "ActivateUVMap2",
    "ActivateUVMap3",
    "FindMissingTexturesInPNGCache",
    "SelectMeshChildren",
    "draw_dummy_ids",
]

import typing as tp

import bpy
import blf
from bpy_extras.view3d_utils import location_3d_to_region_2d

from io_soulstruct.utilities.operators import LoggingOperator
from .utilities import FLVERError, parse_dummy_name, get_selected_flvers


class FLVERToolSettings(bpy.types.PropertyGroup):
    vertex_color_layer_name: bpy.props.StringProperty(
        name="Vertex Color Layer",
        description="Name of the vertex color layer to use for setting vertex alpha",
        default="VertexColors1",
    )
    vertex_alpha: bpy.props.FloatProperty(
        name="Alpha",
        description="Alpha value to set for selected vertices",
        default=1.0,
        min=0.0,
        max=1.0,
    )
    dummy_id_draw_enabled: bpy.props.BoolProperty(name="Draw Dummy IDs", default=False)
    dummy_id_font_size: bpy.props.IntProperty(name="Dummy ID Font Size", default=16, min=1, max=100)


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

        tool_settings = context.scene.flver_tool_settings  # type: FLVERToolSettings

        bpy.ops.object.mode_set(mode="OBJECT")
        try:
            # noinspection PyTypeChecker
            mesh = context.active_object  # type: bpy.types.MeshObject
            if mesh is None or mesh.type != "MESH":
                return self.error("Please select a Mesh object.")

            vertex_indices = [v.index for v in mesh.data.vertices if v.select]
            vertex_colors = mesh.data.vertex_colors[tool_settings.vertex_color_layer_name]
            if not vertex_colors:
                return self.error(f"Mesh does not have a '{tool_settings.vertex_color_layer_name}' vertex color layer.")

            alpha = tool_settings.vertex_alpha
            for i, loop in enumerate(mesh.data.loops):
                if loop.vertex_index in vertex_indices:
                    vertex_colors.data[i].color[3] = alpha
        finally:
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
    bl_description = "Set the UV Editor texture to 'UVMap2', usually the second texture"

    UV_LAYER_NAME = "UVMap2"


class ActivateUVMap3(ActivateUVMap):
    bl_idname = "object.activate_uv_map_3"
    bl_label = "Activate UV Map 3"
    bl_description = "Set the UV Editor texture to 'UVMap3', usually the light map"

    UV_LAYER_NAME = "UVMap3"


class FindMissingTexturesInPNGCache(LoggingOperator):
    """Iterate over all texture nodes used by all materials of one or more selected FLVER meshes and (if currently a 1x1
    dummy texture) find that PNG file in the PNG cache directory.

    This modified the Blender Image data, so obviously, it will affect all models/materials that use this texture.

    Note that this will link the texture to the cached PNG file, rather than packing the image data into the Blend file.
    """
    bl_idname = "mesh.find_missing_textures_in_png_cache"
    bl_label = "Find Missing Textures in PNG Cache"
    bl_description = "Find missing texture names used by materials of selected FLVERs in PNG cache"

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type in {"ARMATURE", "MESH"}

    def execute(self, context):

        settings = self.settings(context)

        try:
            meshes_armatures = get_selected_flvers(context)
        except FLVERError as ex:
            return self.error(str(ex))

        meshes_data = [mesh.data for mesh, _ in meshes_armatures]
        checked_image_names = set()  # to avoid looking for the same PNG twice

        for mesh_data in meshes_data:
            for bl_material in mesh_data.materials:
                texture_nodes = [
                    node for node in bl_material.node_tree.nodes
                    if node.type == "TEX_IMAGE" and node.image is not None
                ]
                for node in texture_nodes:
                    image = node.image  # type: bpy.types.Image
                    if image.size[0] != 1 or image.size[1] != 1:
                        continue
                    # This is a dummy texture. Try to find it in the PNG cache.
                    image_name = image.name
                    if image_name.endswith(".dds"):
                        image_name = image_name[:-4] + ".png"
                    elif not image_name.endswith(".png"):
                        image_name += ".png"
                    if image_name in checked_image_names:
                        continue
                    checked_image_names.add(image_name)
                    png_path = settings.png_cache_directory / image_name
                    if png_path.is_file():
                        image.filepath = str(png_path)
                        image.source = "FILE"
                        image.reload()
                        self.info(f"Found and linked texture file '{image_name}' in PNG cache.")
                    else:
                        self.warning(f"Could not find texture file '{image_name}' in PNG cache.")

        return {"FINISHED"}


class SelectMeshChildren(LoggingOperator):
    """Simple operator that iterates over selected objects, selects all MESH children of any ARMATURES, and deselects
    anything else that isn't a MESH."""
    bl_idname = "object.select_mesh_children"
    bl_label = "Select Mesh Children"
    bl_description = "Select all immediate Mesh children of selected objects and deselect all non-Meshes"

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type in {"ARMATURE", "MESH"}

    def execute(self, context):
        for obj in context.selected_objects:
            for child in obj.children:
                if child.type == "MESH":
                    child.select_set(True)
            if obj.type != "MESH":
                obj.select_set(False)

        if context.selected_objects[0]:
            # Set active object to first selected object.
            bpy.context.view_layer.objects.active = context.selected_objects[0]

        return {"FINISHED"}


def draw_dummy_ids():
    """Draw the numeric reference IDs of all Dummy children of selected FLVER."""
    settings = bpy.context.scene.flver_tool_settings  # type: FLVERToolSettings
    if not settings.dummy_id_draw_enabled:
        return

    if not bpy.context.selected_objects:
        return

    obj = bpy.context.selected_objects[0]

    empties = [child for child in obj.children if child.type == "EMPTY"]
    if obj.type == "MESH" and obj.parent and obj.parent.type == "ARMATURE":
        empties.extend([child for child in obj.parent.children if child.type == "EMPTY"])  # siblings

    dummy_children = []
    for child in empties:
        if dummy_info := parse_dummy_name(child.name):
            dummy_children.append((child, dummy_info))

    font_id = 0
    try:
        blf.size(font_id, bpy.context.scene.flver_tool_settings.dummy_id_font_size)
    except AttributeError:
        blf.size(font_id, 16)  # default
    blf.color(font_id, 1, 1, 1, 1)  # white

    for dummy, dummy_info in dummy_children:
        # Get world location of `dummy` object.
        world_location = dummy.matrix_world.to_translation()
        label_position = location_3d_to_region_2d(bpy.context.region, bpy.context.region_data, world_location)
        if not label_position:
            continue  # dummy is not in view
        blf.position(font_id, label_position.x + 10, label_position.y + 10, 0.0)
        blf.draw(font_id, str(dummy_info.reference_id))
