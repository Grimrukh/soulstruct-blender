from __future__ import annotations

__all__ = [
    "FLVERToolSettings",
    "CopyToNewFLVER",
    "DeleteFLVER",
    "DeleteFLVERAndData",
    "CreateFLVERInstance",
    "DuplicateFLVERModel",
    "RenameFLVER",
    "CreateEmptyMapPieceFLVER",
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
]

import typing as tp

import bpy
import bmesh
import blf
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Matrix, Vector, Quaternion

from soulstruct.base.models.flver import Material

from io_soulstruct.exceptions import FLVERError
from io_soulstruct.utilities.operators import LoggingOperator
from io_soulstruct.utilities.bpy_data import *
from io_soulstruct.msb.msb_import.core import create_flver_model_instance
from .utilities import *


_MASK_ID_STRINGS = []


# noinspection PyUnusedLocal
def _get_display_mask_id_items(self, context) -> list[tuple[str, str, str]]:
    """Dynamic `EnumProperty` that iterates over all materials of selected meshes to find all unique Model Mask IDs."""
    _MASK_ID_STRINGS.clear()
    _MASK_ID_STRINGS.append("No Mask")
    items = [
        ("-1", "No Mask", "Select all materials that do not have a display mask"),
    ]  # type: list[tuple[str, str, str]]

    mask_id_set = set()  # type: set[str]
    for obj in context.selected_objects:
        if obj.type != "MESH":
            continue
        for mat in obj.data.materials:
            if match := Material.DISPLAY_MASK_RE.match(mat.name):
                mask_id = match.group(1)
                mask_id_set.add(mask_id)
    for mask_id in sorted(mask_id_set):
        _MASK_ID_STRINGS.append(mask_id)
        items.append(
            (mask_id, f"Mask {mask_id}", f"Select all materials with display mask {mask_id}")
        )
    return items


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

    uv_scale: bpy.props.FloatProperty(
        name="UV Scale",
        description="Scale to apply to UVs after unwrapping",
        default=1.0,
        min=0.0,
    )

    rebone_target_bone: bpy.props.StringProperty(
        name="Rebone Target Bone",
        description="New bone (vertex group) to assign to vertices with 'Rebone Vertices' operator",
    )

    display_mask_id: bpy.props.EnumProperty(
        name="Display Mask",
        items=_get_display_mask_id_items,
    )


class CopyToNewFLVER(LoggingOperator):

    bl_idname = "object.copy_to_new_flver"
    bl_label = "Copy to New FLVER"
    bl_description = ("Copy selected vertices, edges, and/or faces, their materials, and all FLVER bones and custom "
                      "properties to a new FLVER model in the active collection. Must be in Edit Mode. Will always "
                      "duplicate data, NOT just create new instances")

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH" and context.active_object and context.active_object.type == "MESH"

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select a Mesh in Edit Mode.")

        tool_settings = context.scene.flver_tool_settings  # type: FLVERToolSettings
        # noinspection PyTypeChecker
        mesh = context.edit_object  # type: bpy.types.MeshObject
        armature = mesh.parent
        if armature is not None and armature.type != "ARMATURE":
            return self.error("Parent of edited mesh is not an Armature.")
        new_name = tool_settings.new_flver_model_name
        if not new_name:
            new_name = f"{mesh.name} (Copy)"

        # Copy mesh data into new object. Note that the `separate` operator will add the new mesh to the same
        # collection(s) automatically.
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
        #  indices. However, we do duplicate any materials whose names contain the old mesh name.
        old_mesh_name = mesh.name.split(".")[0].removesuffix(" Mesh")
        for i, mat in enumerate(new_mesh_obj.data.materials):
            if old_mesh_name in mat.name:
                new_mat = mat.copy()  # copies custom properties
                # Update material name.
                new_mat.name = mat.name.replace(old_mesh_name, new_name)
                new_mesh_obj.data.materials[i] = new_mat

        if armature:
            # We need to copy custom properties manually here. TODO: Why not just `armature.copy()`?
            new_armature_obj = new_armature_object(new_name, armature.data.copy(), props=armature)
            new_armature_obj.data.name = f"{new_name} Armature"
            # Add Armature object to same collection(s) as `new_mesh_obj`.
            for collection in new_mesh_obj.users_collection:
                collection.objects.link(new_armature_obj)
            # Update bone names.
            bone_indices = {}
            for i, bone in enumerate(new_armature_obj.data.bones):
                bone.name = bone.name.replace(armature.name, new_name)
                bone_indices[bone.name] = i  # for updating dummy bones
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
                    new_dummy.parent = new_armature_obj
                    # Add Dummy object to same collection(s) as `new_mesh_obj`.
                    for collection in new_mesh_obj.users_collection:
                        collection.objects.link(new_dummy)
                    bone_index = bone_indices[dummy.parent_bone.name]
                    new_dummy.parent_bone = new_armature_obj.data.bones[bone_index]
                    new_dummy.parent_type = "BONE"
                    if new_dummy["Parent Bone Name"]:
                        parent_bone_index = bone_indices[new_dummy["Parent Bone Name"]]
                        new_dummy["Parent Bone Name"] = new_armature_obj.data.bones[parent_bone_index].name

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
    bl_description = "Delete Armature of selected FLVER and all its children, as well as their data blocks"

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" and context.active_object and context.active_object.type in {"ARMATURE", "MESH"}

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select a Mesh or Armature in Object Mode.")

        # noinspection PyTypeChecker
        armature = context.active_object
        if armature.type in {"EMPTY", "MESH"}:
            # noinspection PyTypeChecker
            armature = armature.parent
        if armature.type != "ARMATURE":
            return self.error("Selected object is not an Armature or a child Mesh/Empty of an Armature.")
        armature: bpy.types.ArmatureObject

        for child in armature.children:
            if child.type == "MESH":
                bpy.data.meshes.remove(child.data)
            bpy.data.objects.remove(child)
        bpy.data.armatures.remove(armature.data)
        bpy.data.objects.remove(armature)

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


class DuplicateFLVERModel(LoggingOperator):

    bl_idname = "object.duplicate_flver_model"
    bl_label = "Duplicate to New FLVER Model"
    bl_description = (
        "Duplicate model of selected FLVER to a new model with given name (or text before first underscore in FLVER "
        "instance name). Selected FLVER must be an 'instance' FLVER with a custom 'Model Name' property pointing to "
        "its source model object. Bone poses will also be copied if new model name starts with 'm' (Map Piece). Must "
        "be in Object Mode"
    )

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" and context.active_object and context.active_object.type in {"ARMATURE", "MESH"}

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select a Mesh in Object Mode.")

        instance_mesh, instance_armature = parse_flver_obj(context.active_object)
        instance_name = instance_armature.name if instance_armature else instance_mesh.name

        tool_settings = context.scene.flver_tool_settings  # type: FLVERToolSettings
        if not tool_settings.new_flver_model_name:
            new_model_name = instance_name.split("_")[0]
            self.info(f"No name for new model specified. Using prefix of FLVER instance name: '{new_model_name}'")
        else:
            new_model_name = tool_settings.new_flver_model_name

        # Check that name is available.
        if new_model_name in bpy.data.objects:
            if instance_armature is None:
                return self.error(
                    f"Object with name '{new_model_name}' already exists. Please choose a unique name for new FLVER "
                    f"model's Mesh."
                )
            else:
                return self.error(
                    f"Object with name '{new_model_name}' already exists. Please choose a unique name for new FLVER "
                    f"model's Armature."
                )
        if instance_armature is not None and f"{new_model_name} Mesh" in bpy.data.objects:
            return self.error(
                f"Object with name '{new_model_name} Mesh' already exists. Please choose a unique name for new FLVER "
                f"model's Mesh."
            )

        try:
            source_model_name = (instance_armature or instance_mesh)["Model Name"]
        except KeyError:
            return self.error(
                f"Selected FLVER '{instance_name}' does not have a 'Model Name' custom property, suggesting it is "
                f"not a model instance. Please select a FLVER instance with this property rather than the base model."
            )

        # Find model.
        try:
            source_flver_model = bpy.data.objects[source_model_name]
        except KeyError:
            return self.error(
                f"FLVER mesh '{instance_name}' has 'Model Name' property set to non-existent object "
                f"{source_model_name}'. Cannot find FLVER model to duplicate."
            )
        # Find all collections containing source model.
        source_collections = source_flver_model.users_collection

        model_mesh, model_armature = parse_flver_obj(source_flver_model)

        self.info(f"Creating new FLVER model '{new_model_name}' from '{source_model_name}'.")

        new_mesh_obj = new_mesh_object(
            f"{new_model_name} Mesh" if model_armature else new_model_name,
            model_mesh.data.copy(),
            props=model_mesh,
        )
        new_mesh_obj.data.name = f"{new_model_name} Mesh"  # suffix handled automatically by Blender
        for collection in source_collections:
            collection.objects.link(new_mesh_obj)

        # Duplicate and rename mesh materials.
        for i, mat in enumerate(tuple(new_mesh_obj.data.materials)):
            new_mat = mat.copy()
            new_mat.name = replace_name_model(mat.name, source_model_name, new_model_name)
            new_mesh_obj.data.materials[i] = new_mat

        new_armature_obj = None
        if model_armature:
            new_armature_obj = new_armature_object(
                new_model_name,
                data=model_armature.data.copy(),
                props=model_armature,
            )
            for collection in source_collections:
                collection.objects.link(new_armature_obj)
            new_armature_obj.data.name = f"{new_model_name} Armature"  # suffix handled automatically by Blender
            # Other properties already copied over above.
            context.view_layer.objects.active = new_armature_obj

            if new_model_name.startswith("m"):
                # Copy pose bone transforms for auto-detected Map Piece.
                context.view_layer.update()  # need Blender to create `linked_armature_obj.pose` now
                for pose_bone in model_armature.pose.bones:
                    source_bone = model_armature.pose.bones[pose_bone.name]
                    pose_bone.rotation_mode = "QUATERNION"  # should be default but being explicit
                    pose_bone.location = source_bone.location
                    pose_bone.rotation_quaternion = source_bone.rotation_quaternion
                    pose_bone.scale = source_bone.scale

            # Now rename bones and vertex groups.
            bone_renaming = {}
            for bone in new_armature_obj.data.bones:
                old_bone_name = bone.name
                # If there is only one bone, we set its name to the model name manually, as they can be outdated.
                if len(new_armature_obj.pose.bones) == 1:
                    new_bone_name = new_model_name
                else:
                    new_bone_name = replace_name_model(bone.name, source_model_name, new_model_name)
                bone_renaming[old_bone_name] = bone.name = new_bone_name
            for vertex_group in new_mesh_obj.vertex_groups:
                if vertex_group.name in bone_renaming:
                    vertex_group.name = bone_renaming[vertex_group.name]

            new_mesh_obj.parent = new_armature_obj
            if bpy.ops.object.select_all.poll():
                bpy.ops.object.select_all(action="DESELECT")
            new_mesh_obj.select_set(True)
            context.view_layer.objects.active = new_mesh_obj
            bpy.ops.object.modifier_add(type="ARMATURE")
            armature_mod = new_mesh_obj.modifiers["Armature"]
            armature_mod.object = new_armature_obj
            armature_mod.show_in_editmode = True
            armature_mod.show_on_cage = True

        # New model created successfully. Now we update the instance to refer to it, and use its name.
        # The instance name may just be part of the full model name, so we find the overlap and update from that.
        # Get prefix that overlaps with old model name (e.g. 'm2000B0_0000_SUFFIX' * 'm2000B0A10' = 'm2000B0').
        old_instance_prefix = new_instance_prefix = ""
        for i, (a, b) in enumerate(zip(instance_name, source_model_name)):
            if a != b:
                old_instance_prefix = instance_name[:i]
                new_instance_prefix = new_model_name[:i]  # take same length prefix from new model name
                break

        instance_mesh.data = new_mesh_obj.data
        if old_instance_prefix:
            instance_mesh.name = replace_name_model(instance_mesh.name, old_instance_prefix, new_instance_prefix)
        if instance_armature:
            # Model reference stored on instance Armature.
            if new_armature_obj:
                instance_armature.data = new_armature_obj.data
                instance_armature["Model Name"] = new_model_name  # name of model Armature or Mesh
                if old_instance_prefix:
                    instance_armature.name = replace_name_model(
                        instance_armature.name, old_instance_prefix, new_instance_prefix
                    )
            else:
                self.warning(
                    f"FLVER instance '{instance_armature.name}' has an Armature, but model does not. Keeping Model "
                    f"Name reference on instance Mesh."
                )
                instance_mesh["Model Name"] = new_model_name  # name of model Armature or Mesh
        else:
            # Model reference stored on instance Mesh (no Armature).
            instance_mesh["Model Name"] = new_model_name  # name of model Armature or Mesh

        return {"FINISHED"}


class RenameFLVER(LoggingOperator):

    bl_idname = "object.rename_flver"
    bl_label = "Rename FLVER"
    bl_description = (
        "Rename all occurrences of model name in the selected FLVER model. Automatically removes Blender duplicate "
        "name suffixes like '.001'. Must be in Object Mode"
    )

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

        rename_flver(armature, mesh, old_name, new_name, strip_dupe_suffix=True)

        return {"FINISHED"}


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
            props={
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

        tool_settings = context.scene.flver_tool_settings  # type: FLVERToolSettings
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
