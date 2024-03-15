from __future__ import annotations

__all__ = [
    "FLVERToolSettings",
    "CopyToNewFLVER",
    "CreateFLVERInstance",
    "RenameFLVER",
    "CreateEmptyMapPieceFLVER",
    "SetSmoothCustomNormals",
    "SetVertexAlpha",
    "InvertVertexAlpha",
    "ActivateUVTexture0",
    "ActivateUVTexture1",
    "ActiveUVLightmap",
    "FindMissingTexturesInPNGCache",
    "SelectMeshChildren",
    "draw_dummy_ids",
]

import typing as tp

import bpy
import blf
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Vector

from io_soulstruct.utilities.operators import LoggingOperator
from io_soulstruct.utilities.bpy_data import *
from io_soulstruct.msb.msb_import.core import create_flver_model_instance
from .utilities import FLVERError, parse_flver_obj, parse_dummy_name, get_selected_flvers


class FLVERToolSettings(bpy.types.PropertyGroup):
    """Holds settings for the various operators below. Drawn manually in operator browser windows."""

    vertex_color_layer_name: bpy.props.StringProperty(
        name="Vertex Color Layer",
        description="Name of the vertex color layer to use for setting vertex alpha",
        default="VertexColors0",
    )
    vertex_alpha: bpy.props.FloatProperty(
        name="Alpha",
        description="Alpha value to set for selected vertices",
        default=1.0,
        min=0.0,
        max=1.0,
    )
    set_selected_face_vertex_alpha_only: bpy.props.BoolProperty(
        name="Set Selected Face Vertex Alpha Only",
        description="Only set alpha values for loops (face corners) that are part of selected faces",
        default=False,
    )
    dummy_id_draw_enabled: bpy.props.BoolProperty(name="Draw Dummy IDs", default=False)
    dummy_id_font_size: bpy.props.IntProperty(name="Dummy ID Font Size", default=16, min=1, max=100)

    new_flver_model_name: bpy.props.StringProperty(
        name="New FLVER Model Name",
        description="Name of the new FLVER model to create",
        default="",  # default is operator-dependent
    )


class CopyToNewFLVER(LoggingOperator):

    bl_idname = "object.copy_to_new_flver"
    bl_label = "Copy to New FLVER"
    bl_description = ("Copy selected vertices, edges, and/or faces, their materials, and all FLVER bones and custom "
                      "properties to a new FLVER model in same collection. Must be in Edit Mode. Will always duplicate "
                      "data, NOT just create new instances")

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH" and context.active_object and context.active_object.type == "MESH"

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select a Mesh in Edit Mode.")

        tool_settings = context.scene.flver_tool_settings  # type: FLVERToolSettings
        # noinspection PyTypeChecker
        mesh = context.active_object  # type: bpy.types.MeshObject
        armature = mesh.parent
        if armature is not None and armature.type != "ARMATURE":
            return self.error("Parent of edited mesh is not an Armature.")
        active_collection = context.collection
        new_name = tool_settings.new_flver_model_name
        if not new_name:
            new_name = f"{mesh.name} (Copy)"

        # Copy mesh data into new object.
        bpy.ops.mesh.duplicate()
        bpy.ops.mesh.separate(type="SELECTED")  # copies custom properties, materials, data layers, etc.
        # Separated object added to selected. We confirm, though.
        # noinspection PyTypeChecker
        new_mesh_obj = context.selected_objects[-1]  # type: bpy.types.MeshObject
        if not new_mesh_obj.name.startswith(mesh.name):
            return self.error(f"Could not duplicate and separate selected part of mesh into new object.")
        new_mesh_obj.name = f"{new_name} Mesh"
        new_mesh_obj.data.name = f"{new_name} Mesh"

        # NOTE: All materials are copied automatically. It's too annoying to remove unused ones and update all the face
        #  indices. However, we do duplicate any materials whose names start with the old mesh name.
        old_mesh_name = mesh.name.split(".")[0].removesuffix(" Mesh")
        for i, mat in enumerate(new_mesh_obj.data.materials):
            if mat.name.startswith(old_mesh_name):
                new_mat = mat.copy()  # copies custom properties
                # Update material name.
                new_mat.name = f"{new_name} {mat.name.removeprefix(old_mesh_name)}"
                new_mesh_obj.data.materials[i] = new_mat

        active_collection.objects.link(new_mesh_obj)

        if armature:
            new_armature_obj = new_armature_object(f"{new_name} Armature", armature.data.copy())
            new_armature_obj.data.name = f"{new_name} Armature"
            # Update bone names.
            bone_indices = {}
            for i, bone in enumerate(new_armature_obj.data.bones):
                bone.name = bone.name.replace(armature.name, new_name)
                bone_indices[bone.name] = i  # for updating dummy bones
            active_collection.objects.link(new_armature_obj)
            new_mesh_obj.parent = new_armature_obj

            # Create Armature modifier on Mesh.
            armature_mod = new_mesh_obj.modifiers.new("Armature", "ARMATURE")
            armature_mod.object = new_armature_obj
            armature_mod.show_in_editmode = True
            armature_mod.show_on_cage = True

            # Copy dummies and rename them and their attach/parent bones.
            for dummy in armature.children:
                if dummy.type == "EMPTY":
                    new_dummy = dummy.copy()  # copies custom properties
                    new_dummy.name = f"{new_name} {dummy.name.removeprefix(armature.name)}"
                    active_collection.objects.link(new_dummy)
                    new_dummy.parent = new_armature_obj
                    bone_index = bone_indices[dummy.parent_bone.name]
                    new_dummy.parent_bone = new_armature_obj.data.bones[bone_index]
                    new_dummy.parent_type = "BONE"
                    if new_dummy["Parent Bone Name"]:
                        parent_bone_index = bone_indices[new_dummy["Parent Bone Name"]]
                        new_dummy["Parent Bone Name"] = new_armature_obj.data.bones[parent_bone_index].name

        return {"FINISHED"}


class CreateFLVERInstance(LoggingOperator):

    bl_idname = "object.create_flver_instance"
    bl_label = "Create FLVER Instance"
    bl_description = "Create an instance of the selected FLVER model. Must be in Object Mode"

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" and context.active_object and context.active_object.type in {"ARMATURE", "MESH"}

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select a Mesh in Object Mode.")

        mesh, armature = parse_flver_obj(context.active_object)
        name = armature.name if armature else mesh.name

        try:
            create_flver_model_instance(context, armature, mesh, f"{name} Instance", context.collection, copy_pose=True)
        except Exception as ex:
            return self.error(f"Could not create FLVER instance: {ex}")

        return {"FINISHED"}


class RenameFLVER(LoggingOperator):

    bl_idname = "object.rename_flver"
    bl_label = "Rename FLVER"
    bl_description = "Rename all occurrences of model name in the selected FLVER model. Must be in Object Mode"

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" and context.active_object and context.active_object.type in {"ARMATURE", "MESH"}

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select a Mesh in Object Mode.")

        tool_settings = context.scene.flver_tool_settings  # type: FLVERToolSettings
        if not tool_settings.new_flver_model_name:
            return self.error("No new name specified.")

        mesh, armature = parse_flver_obj(context.active_object)
        old_name = armature.name if armature else mesh.name
        new_name = tool_settings.new_flver_model_name

        def rename(name: str):
            if name.startswith(old_name):
                return f"{new_name}{name.removeprefix(old_name)}"
            return name

        mesh.name = rename(mesh.name)
        mesh.data.name = rename(mesh.data.name)
        for mat in mesh.data.materials:
            mat.name = rename(mat.name)
        if armature:
            armature.name = rename(armature.name)
            armature.data.name = rename(armature.data.name)
            for bone in armature.data.bones:
                bone.name = rename(bone.name)
            dummy_prefix = f"{old_name} Dummy"
            for child in armature.children:
                if child.type == "EMPTY" and child.name.startswith(dummy_prefix):
                    child.name = rename(child.name)
                    child["Parent Bone Name"] = rename(child["Parent Bone Name"])


class CreateEmptyMapPieceFLVER(LoggingOperator):

    # TODO: Need to add loop data layers like vertex colors, UVs, etc.

    bl_idname = "object.create_empty_map_piece_flver"
    bl_label = "Create Empty Map Piece FLVER"
    bl_description = "Create a new empty FLVER model. Must be in Object Mode"

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context):

        tool_settings = context.scene.flver_tool_settings  # type: FLVERToolSettings
        new_name = tool_settings.new_flver_model_name
        if not new_name:
            new_name = "New Map Piece"

        new_armature_obj = new_armature_object(
            f"{new_name} Armature",
            data=bpy.data.armatures.new(f"{new_name} Armature"),
            **{
                "Is Big Endian": False,
                "Version": "DarkSouls_A",
                "Unicode": True,
                "Unk x4a": False,
                "Unk x4c": 0,
                "Unk x5c": 0,
                "Unk x5d": 0,
                "Unk x68": 0,
            }
        )
        context.collection.objects.link(new_armature_obj)

        context.view_layer.objects.active = new_armature_obj
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        edit_bone = new_armature_obj.data.edit_bones.new(new_name)
        edit_bone["Is Unused"] = False
        edit_bone.use_local_location = True
        edit_bone.inherit_scale = "NONE"
        # Leave Head as zero.
        bone_length = context.scene.flver_import_settings.base_edit_bone_length
        edit_bone.tail = Vector((0.0, bone_length, 0.0))  # default tail position
        del edit_bone
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        new_mesh_obj = new_mesh_object(f"{new_name} Mesh", bpy.data.meshes.new(f"{new_name} Mesh"))
        context.collection.objects.link(new_mesh_obj)
        new_mesh_obj.parent = new_armature_obj
        armature_mod = new_mesh_obj.modifiers.new("Armature", "ARMATURE")
        armature_mod.object = new_armature_obj
        armature_mod.show_in_editmode = True
        armature_mod.show_on_cage = True

        return {"FINISHED"}


class SetSmoothCustomNormals(LoggingOperator):

    bl_idname = "mesh.set_smooth_custom_normals"
    bl_label = "Set Smooth Custom Normals"
    bl_description = (
        "Set all vertex normals from faces for all mesh faces (if in Object Mode) or selected faces "
        "(if in Edit Mode), then set custom normals from averages of faces. Suitable for most models"
    )

    @classmethod
    def poll(cls, context):
        return context.mode in {"OBJECT", "EDIT_MESH"}

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

            if tool_settings.set_selected_face_vertex_alpha_only:
                face_loops = {i for face in mesh.data.polygons if face.select for i in face.loop_indices}
            else:
                face_loops = set()

            alpha = tool_settings.vertex_alpha
            for i, loop in enumerate(mesh.data.loops):
                if tool_settings.set_selected_face_vertex_alpha_only and i not in face_loops:
                    continue
                if loop.vertex_index in vertex_indices:
                    vertex_colors.data[i].color[3] = alpha
        finally:
            bpy.ops.object.mode_set(mode="EDIT")

        return {"FINISHED"}


class InvertVertexAlpha(LoggingOperator):

    bl_idname = "mesh.invert_selected_vertex_alpha"
    bl_label = "Invert Vertex Alpha"
    bl_description = "Invert (subtract from 1) the alpha value of selected vertex color layer for all selected vertices"

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

            if tool_settings.set_selected_face_vertex_alpha_only:
                face_loops = {i for face in mesh.data.polygons if face.select for i in face.loop_indices}
            else:
                face_loops = set()

            for i, loop in enumerate(mesh.data.loops):
                if tool_settings.set_selected_face_vertex_alpha_only and i not in face_loops:
                    continue
                if loop.vertex_index in vertex_indices:
                    vertex_colors.data[i].color[3] = 1.0 - vertex_colors.data[i].color[3]
        finally:
            bpy.ops.object.mode_set(mode="EDIT")

        return {"FINISHED"}


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
        return self.set_uv_editor_texture(context, self.UV_LAYER_NAME)

    def set_uv_editor_texture(self, context, uv_layer_name: str) -> set[str]:
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
                return self.error(f"Could not find UV attribute node for '{uv_layer_name}'.")

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

        return self.error(f"No textures found that were linked to by the '{uv_layer_name}' attribute node.")


class ActivateUVTexture0(ActivateUVMap):
    bl_idname = "object.activate_uv_texture_0"
    bl_label = "Activate UV Texture 0"
    bl_description = "Set the UV Editor texture to 'UVTexture0', usually the first standard texture"

    UV_LAYER_NAME = "UVTexture0"


class ActivateUVTexture1(ActivateUVMap):
    bl_idname = "object.activate_uv_texture_1"
    bl_label = "Activate UV Texture 1"
    bl_description = "Set the UV Editor texture to 'UVTexture1', usually the second standard texture"

    UV_LAYER_NAME = "UVTexture1"


class ActiveUVLightmap(ActivateUVMap):
    bl_idname = "object.activate_uv_lightmap"
    bl_label = "Activate UV Lightmap"
    bl_description = "Set the UV Editor texture to 'UVLightmap'"

    UV_LAYER_NAME = "UVLightmap"


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
