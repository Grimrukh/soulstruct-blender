from __future__ import annotations

__all__ = [
    "CopyToNewFLVER",
    "DeleteFLVER",
    "DeleteFLVERAndData",
    "RenameFLVER",
    "SelectDisplayMaskID",
    "SetSmoothCustomNormals",
    "SetVertexAlpha",
    "InvertVertexAlpha",
    "BakeBonePoseToVertices",
    "ReboneVertices",
    "ActivateUVTexture0",
    "ActivateUVTexture1",
    "ActiveUVLightmap",
    "FastUVUnwrap",
    "FindMissingTexturesInPNGCache",
    "SelectMeshChildren",
    "draw_dummy_ids",
    "HideAllDummiesOperator",
    "ShowAllDummiesOperator",
    "PrintGameTransform",
]

import typing as tp

import bpy
import bmesh
import blf
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Matrix, Vector, Quaternion

from soulstruct.base.models.flver import Material

from io_soulstruct.exceptions import FLVERError
from io_soulstruct.utilities import *
from .types import *

if tp.TYPE_CHECKING:
    from .properties import FLVERToolSettings


class CopyToNewFLVER(LoggingOperator):

    bl_idname = "object.copy_to_new_flver"
    bl_label = "Copy to New FLVER"
    bl_description = ("Copy selected vertices, edges, and/or faces, their materials, and all FLVER bones and custom "
                      "properties to a new FLVER model in the active collection. Must be in Edit Mode")

    @classmethod
    def poll(cls, context):
        if context.mode != "EDIT_MESH" or not context.active_object or context.active_object.type != "MESH":
            return False
        return BlenderFLVER.test_obj(context.active_object)

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select a Mesh in Edit Mode.")

        settings = self.settings(context)
        bl_flver = BlenderFLVER.from_bl_obj(context.active_object, operator=self)
        new_bl_flver = bl_flver.duplicate_edit_mode(
            context=context,
            make_materials_single_user=True,
            copy_pose=True,
        )
        new_bl_flver.rename(settings.new_model_name or f"{bl_flver.name}_Copy")

        return {"FINISHED"}


class DeleteFLVER(LoggingOperator):

    bl_idname = "object.delete_flver"
    bl_label = "Delete FLVER (Objects)"
    bl_description = "Delete Armature of selected FLVER and all its children"

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" and context.active_object and context.active_object.type in {"ARMATURE", "MESH"}

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select a Mesh or Armature in Object Mode.")

        armature = context.active_object
        if armature.type == "MESH":
            armature = armature.parent
            if armature.type != "ARMATURE":
                return self.error("Selected object is not an Armature or a child of an Armature.")

        for child in armature.children:
            bpy.data.objects.remove(child)
        bpy.data.objects.remove(armature)

        return {"FINISHED"}


class DeleteFLVERAndData(LoggingOperator):

    bl_idname = "object.delete_flver_and_data"
    bl_label = "Delete FLVER (Objects + Data)"
    bl_description = ("Delete Armature/Mesh of selected FLVER and all its children, as well as any Mesh data blocks "
                      "(but not materials or textures)")

    @classmethod
    def poll(cls, context):
        if context.mode != "OBJECT" or not context.active_object:
            return False
        try:
            BlenderFLVER.from_bl_obj(context.active_object)
        except FLVERError:
            return False
        return True

    def execute(self, context):
        bl_flver = BlenderFLVER.from_bl_obj(context.active_object)
        for child in bl_flver.root_obj.children_recursive:
            if child.type == "MESH":
                bpy.data.meshes.remove(child.data)
            bpy.data.objects.remove(child)
        if bl_flver.armature:
            bpy.data.armatures.remove(bl_flver.armature.data)
            bpy.data.objects.remove(bl_flver.armature)
        bpy.data.meshes.remove(bl_flver.mesh.data)
        bpy.data.objects.remove(bl_flver.mesh)

        return {"FINISHED"}


class RenameFLVER(LoggingOperator):

    bl_idname = "object.rename_flver"
    bl_label = "Rename FLVER"
    bl_description = (
        "Rename all occurrences of model name in the selected FLVER model (text before first space and/or dot). "
        "Automatically removes Blender duplicate name suffixes like '.001'. Must be in Object Mode"
    )

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" and context.active_object and context.active_object.type in {"ARMATURE", "MESH"}

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select a Mesh in Object Mode.")

        settings = self.settings(context)
        if not settings.new_model_name:
            return self.error("No new model name specified.")

        bl_flver = BlenderFLVER.from_bl_obj(context.active_object, operator=self)
        bl_flver.rename(settings.new_model_name)

        return {"FINISHED"}


class SelectDisplayMaskID(LoggingOperator):

    bl_idname = "mesh.select_display_mask_id"
    bl_label = "Select Display Mask ID"
    bl_description = "Select all faces with materials labelled with the given display mask ('#XX#')"

    @classmethod
    def poll(cls, context):
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

        tool_settings = context.scene.flver_tool_settings

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

        tool_settings = context.scene.flver_tool_settings

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


class BakeBonePoseToVertices(LoggingOperator):

    bl_idname = "mesh.bake_bone_pose_to_vertices"
    bl_label = "Bake Bone Pose to Vertices"
    bl_description = (
        "Bake the pose of each selected bone into all vertices weighted ONLY to that bone into the mesh and set bone "
        "pose to origin. Valid only for Map Piece FLVERs; for safety, no Mesh material can have 'Is Bind Pose' custom "
        "property set to True"
    )

    @classmethod
    def poll(cls, context):
        """Must select at least one bone in Armature of active object."""
        if context.mode == "OBJECT" and context.active_object:
            arma = context.active_object.find_armature()
            if arma and any(bone.select for bone in arma.data.bones):
                return True
        return False

    def execute(self, context):
        if context.mode != "OBJECT":
            return self.error("Please enter Object Mode to use this operator.")

        # noinspection PyTypeChecker
        mesh = context.active_object  # type: bpy.types.MeshObject
        if mesh is None or mesh.type != "MESH":
            return self.error("Please select a Mesh object.")

        # TODO: Should check that Mesh has an Armature modifier attached to parent?
        # noinspection PyTypeChecker
        armature = mesh.parent  # type: bpy.types.ArmatureObject
        if not armature or armature.type != "ARMATURE":
            return self.error("Mesh is not parented to an Armature.")

        if any(mat.get("Is Bind Pose") for mat in mesh.data.materials):
            return self.error(
                "One or more materials have 'Is Bind Pose' custom property set to True. This operator is only usable "
                "for Map Piece FLVERs, where 'Is Bind Pose' is False and vertices are 'auto-posed' by exactly one "
                "FLVER bone."
            )

        # Get a dictionary mapping bone names to their (location, rotation, scale) tuples for baking into vertices.
        # Ignores bones that are not selected.
        bone_pose_transforms = {}  # type: dict[str, Matrix]
        selected_pose_bones = []
        for pose_bone in armature.pose.bones:
            if not pose_bone.bone.select:
                continue  # bone not selected; do not bake
            bone_pose_transforms[pose_bone.bone.name] = pose_bone.matrix  # no need to copy (not modified)
            selected_pose_bones.append(pose_bone)

        # First, a validation pass.
        affected_vertices = []  # type: list[tuple[bpy.types.MeshVertex, Matrix]]
        for vertex in mesh.data.vertices:
            if len(vertex.groups) != 1:
                return self.error(
                    f"Vertex {vertex.index} is weighted to more than one bone: "
                    f"{[group.name for group in vertex.groups]}. No vertices were baked."
                )
            group_index = vertex.groups[0].group
            bone_name = mesh.vertex_groups[group_index].name
            if bone_name not in bone_pose_transforms:
                continue  # not selected for baking
            affected_vertices.append((vertex, bone_pose_transforms[bone_name]))

        # Bake bone pose into vertices.
        for vertex, transform in affected_vertices:
            vertex.co = transform @ vertex.co

        # Reset bone pose transform to origin.
        for pose_bone in selected_pose_bones:
            pose_bone.location = Vector((0.0, 0.0, 0.0))
            pose_bone.rotation_quaternion = Quaternion((1.0, 0.0, 0.0, 0.0))
            pose_bone.scale = Vector((1.0, 1.0, 1.0))

        self.info(f"Baked pose of {len(affected_vertices)} vertices into mesh and reset bone pose(s) to origin.")

        return {"FINISHED"}


class ReboneVertices(LoggingOperator):

    bl_idname = "mesh.rebone_vertices"
    bl_label = "Rebone Vertices"
    bl_description = (
        "Change selected vertices' single weighted bone (vertex group) while preserving their posed position through "
        "a vertex data transformation. Useful for 'deboning' Map Pieces by changing to the default origin bone "
        "(usually named after the model)"
    )

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH"

    def execute(self, context):
        if context.mode != "EDIT_MESH":
            return self.error("Please enter Edit Mode to use this operator.")

        tool_settings = context.scene.flver_tool_settings
        if not tool_settings.rebone_target_bone:
            return self.error("No target bone selected for reboning.")

        bpy.ops.object.mode_set(mode="OBJECT")

        # noinspection PyTypeChecker
        mesh = context.active_object  # type: bpy.types.MeshObject
        if mesh is None or mesh.type != "MESH":
            return self.error("Please select a Mesh object.")

        # TODO: Should check that Mesh has an Armature modifier attached to parent?
        # noinspection PyTypeChecker
        armature = mesh.parent  # type: bpy.types.ArmatureObject
        if not armature or armature.type != "ARMATURE":
            return self.error("Mesh is not parented to an Armature.")

        # Get a dictionary mapping bone names to their (location, rotation, scale) tuples for baking into vertices.
        bone_pose_transforms = {}  # type: dict[str, Matrix]
        for pose_bone in armature.pose.bones:
            bone_pose_transforms[pose_bone.bone.name] = pose_bone.matrix  # no need to copy (not modified)

        try:
            target_bone_pose = armature.pose.bones[tool_settings.rebone_target_bone]
        except KeyError:
            return self.error(f"Target bone '{tool_settings.rebone_target_bone}' not found in Armature.")
        target_matrix_inv = target_bone_pose.matrix.inverted()

        try:
            target_group = mesh.vertex_groups[tool_settings.rebone_target_bone]
        except KeyError:
            return self.error(
                f"Target bone '{tool_settings.rebone_target_bone}' not found (by name) in Mesh vertex groups."
            )

        # Iterate over selected mesh vertices. Check that each vertex is weighted to only one bone that is not the
        # target bone. Clear all weights for that vertex and collect it. Finally, make a single `add()` call to add
        # all vertices to the target bone with weight 1.0.
        vertices_to_rebone = []
        for vertex in mesh.data.vertices:
            if not vertex.select:
                continue
            if len(vertex.groups) != 1:
                return self.error(
                    f"Vertex {vertex.index} is weighted to more than one bone: "
                    f"{[group.name for group in vertex.groups]}. No vertices were deboned."
                )
            group_index = vertex.groups[0].group
            if group_index == target_group.index:
                continue  # already weighted to target bone

            old_bone_name = mesh.vertex_groups[group_index].name

            try:
                old_bone_transform = bone_pose_transforms[old_bone_name]
            except KeyError:
                return self.error(f"No bone matches name of vertex group '{old_bone_name}' for vertex {vertex.index}.")
            vertices_to_rebone.append((vertex, (group_index, old_bone_transform)))

        if not vertices_to_rebone:
            return self.error("No vertices (not already weighted to target bone) were selected for reboning.")

        old_vertex_group_indices = {}  # type: dict[int, list[int]]
        vertex_indices = []
        for vertex, (group_index, old_bone_transform) in vertices_to_rebone:
            # Transform vertex data so that new pose will preserve the same posed vertex position.
            # We do this by applying the old bone's transform (to get desired object-space transform), then
            # un-applying the target bone's transform.
            vertex.co = target_matrix_inv @ old_bone_transform @ vertex.co
            # Queue vertex index for old group removal and new group addition below.
            old_vertex_group_indices.setdefault(group_index, []).append(vertex.index)
            vertex_indices.append(vertex.index)

        for group_index, old_group_vertex_indices in old_vertex_group_indices.items():
            mesh.vertex_groups[group_index].remove(old_group_vertex_indices)
        target_group.add(vertex_indices, 1.0, "REPLACE")

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

                            return {"FINISHED"}

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


class FastUVUnwrap(LoggingOperator):
    bl_idname = "mesh.fast_uv_unwrap"
    bl_label = "Fast UV Unwrap"
    bl_description = "Unwrap selected faces using the 'UV Unwrap' operator, then scale their UVs using given value"

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH"

    def execute(self, context):
        if context.mode != "EDIT_MESH":
            return self.error("Please enter Edit Mode to use this operator.")

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
            bl_flvers = BlenderFLVER.get_selected_flvers(context)
        except FLVERError as ex:
            return self.error(str(ex))

        meshes_data = [bl_flver.mesh.data for bl_flver in bl_flvers]
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
    settings = bpy.context.scene.flver_tool_settings
    if not settings.dummy_id_draw_enabled:
        return

    if not bpy.context.selected_objects:
        return

    obj = bpy.context.selected_objects[0]
    try:
        bl_flver = BlenderFLVER.from_bl_obj(obj)
    except FLVERError:
        return

    bl_dummies = bl_flver.get_dummies()

    font_id = 0
    try:
        blf.size(font_id, bpy.context.scene.flver_tool_settings.dummy_id_font_size)
    except AttributeError:
        blf.size(font_id, 16)  # default
    blf.color(font_id, 1, 1, 1, 1)  # white

    for bl_dummy in bl_dummies:
        # Get world location of `dummy` object.
        world_location = bl_dummy.obj.matrix_world.to_translation()
        label_position = location_3d_to_region_2d(bpy.context.region, bpy.context.region_data, world_location)
        if not label_position:
            continue  # dummy is not in view
        blf.position(font_id, label_position.x + 10, label_position.y + 10, 0.0)
        blf.draw(font_id, str(bl_dummy.reference_id))


class HideAllDummiesOperator(LoggingOperator):
    """Simple operator to hide all dummy children of a selected FLVER armature."""
    bl_idname = "io_scene_soulstruct.hide_all_dummies"
    bl_label = "Hide All Dummies"
    bl_description = "Hide all dummy point children in the selected armature (Empties with 'Dummy' in name)"

    @classmethod
    def poll(cls, context):
        if not context.active_object:
            return False
        try:
            BlenderFLVER.from_bl_obj(context.active_object)
        except IndexError:
            return False
        return True

    def execute(self, context):
        bl_dummies = BlenderFLVER.from_bl_obj(context.active_object).get_dummies(self)
        for bl_dummy in bl_dummies:
            bl_dummy.obj.hide_viewport = True

        return {"FINISHED"}


class ShowAllDummiesOperator(LoggingOperator):
    """Simple operator to show all dummy children of a selected FLVER armature."""
    bl_idname = "io_scene_soulstruct.show_all_dummies"
    bl_label = "Show All Dummies"
    bl_description = "Show all dummy point children in the selected armature (Empties with 'Dummy' in name)"

    @classmethod
    def poll(cls, context):
        if not context.active_object:
            return False
        try:
            BlenderFLVER.from_bl_obj(context.active_object)
        except IndexError:
            return False
        return True

    def execute(self, context):
        bl_dummies = BlenderFLVER.from_bl_obj(context.active_object).get_dummies(self)
        for bl_dummy in bl_dummies:
            bl_dummy.obj.hide_viewport = False

        return {"FINISHED"}


class PrintGameTransform(LoggingOperator):
    bl_idname = "io_scene_soulstruct.print_game_transform"
    bl_label = "Print Game Transform"
    bl_description = "Print the selected object's transform in game coordinates to Blender console"

    @classmethod
    def poll(cls, context):
        return context.object is not None

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        obj = context.object
        if obj:
            bl_transform = BlenderTransform(obj.location, obj.rotation_euler, obj.scale)
            print(
                f"FromSoftware game transform of object '{obj.name}':\n"
                f"    translate = {repr(bl_transform.game_translate)}\n"
                f"    rotate = {repr(bl_transform.game_rotate_deg)}  # degrees\n"
                f"    scale = {repr(bl_transform.game_scale)}"
            )
        return {"FINISHED"}
