"""Miscellaneous operators for copying/changing FLVER data."""
from __future__ import annotations

__all__ = [
    "CopyToNewFLVER",
    "RenameFLVER",
    "SelectMeshChildren",
    "SyncMSBPartArmatures",
    "ClearFLVERSubmeshProperties",
    "AddFLVERSubmeshProperties",
]

import bpy

from ....base.operators import LoggingOperator
from ....base.register import io_soulstruct_class
from ....types import SoulstructType
from ....utilities import replace_shared_prefix
from ..types import BlenderFLVER


@io_soulstruct_class
class CopyToNewFLVER(LoggingOperator):

    bl_idname = "object.copy_to_new_flver"
    bl_label = "Copy to New FLVER"
    bl_description = ("Copy selected vertices, edges, and/or faces, their materials, and all FLVER bones and custom "
                      "properties to a new FLVER model in the active collection. Must be in Edit Mode")

    new_name: bpy.props.StringProperty(
        name="New Model Name",
        description="Name of the new FLVER model. If empty, will just add '_Copy' suffix to the original name",
        default="",
    )

    @classmethod
    def poll(cls, context) -> bool:
        if context.mode != "EDIT_MESH" or not context.active_object or context.active_object.type != "MESH":
            return False
        return BlenderFLVER.is_obj_type(context.active_object)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select a Mesh in Edit Mode.")

        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        new_bl_flver = bl_flver.duplicate_edit_mode(
            context=context,
            make_materials_single_user=True,
            copy_pose=True,  # copy pose immediately (not batched)
        )
        new_bl_flver.deep_rename(self.new_name or f"{bl_flver.name}_Copy")

        return {"FINISHED"}


@io_soulstruct_class
class RenameFLVER(LoggingOperator):

    bl_idname = "object.rename_flver"
    bl_label = "Rename FLVER"
    bl_description = (
        "Do a 'deep rename' of all occurrences of model name in the selected FLVER model (text before first space "
        "and/or dot). Automatically removes Blender duplicate name suffixes like '.001'. Must be in Object Mode. Can "
        "optionally rename all MSB Map Piece parts that instance this model"
    )

    new_name: bpy.props.StringProperty(
        name="New Name",
        description="New name for the FLVER model",
        default="",
    )
    rename_parts: bpy.props.BoolProperty(
        name="Rename Parts",
        description="Rename MSB Map Piece ('m*' models), Character ('c*' models), or Object ('o*' models) parts that "
                    "instance this FLVER model",
        default=True,
    )

    @classmethod
    def poll(cls, context) -> bool:
        if not context.mode == "OBJECT":
            return False
        return BlenderFLVER.is_obj_type(context.active_object)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        if not self.new_name:
            return self.error("No new model name specified.")

        flver_obj = context.active_object
        bl_flver = BlenderFLVER.from_armature_or_mesh(flver_obj)
        old_model_name = bl_flver.game_name
        new_model_name = self.new_name
        bl_flver.deep_rename(new_model_name)

        if self.rename_parts:
            if self.new_name[0] == "m":
                part_subtype = "MSB_MAP_PIECE"
            elif self.new_name[0] == "c":
                part_subtype = "MSB_CHARACTER"
            elif self.new_name[0] == "o":
                part_subtype = "MSB_OBJECT"
            else:
                self.warning(f"Cannot determine part subtype from model name '{self.new_name}'. No parts were renamed.")
                return {"FINISHED"}

            part_count = 0
            for obj in bpy.data.objects:
                if (
                    obj.soulstruct_type == SoulstructType.MSB_PART
                    and obj.MSB_PART.entry_subtype == part_subtype
                    and obj is not flver_obj
                    and obj.data == flver_obj.data
                ):
                    # Found a part to rename.
                    part_count += 1
                    obj.name = replace_shared_prefix(old_model_name, new_model_name, obj.name)

            self.info(f"Renamed {part_count} parts that instance FLVER model '{old_model_name}' to '{new_model_name}'.")

        return {"FINISHED"}


@io_soulstruct_class
class SelectMeshChildren(LoggingOperator):
    """Simple operator that iterates over selected objects, selects all MESH children of any ARMATURES, and deselects
    anything else that isn't a MESH."""
    bl_idname = "object.select_mesh_children"
    bl_label = "Select Mesh Children"
    bl_description = "Select all immediate Mesh children of selected objects and deselect all non-Meshes"

    @classmethod
    def poll(cls, context) -> bool:
        """Requires at least one object selected."""
        return context.selected_objects and all(obj.type in {"ARMATURE", "MESH"} for obj in context.selected_objects)

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


@io_soulstruct_class
class SyncMSBPartArmatures(LoggingOperator):
    """Sync the Armature of all FLVER models that are instanced by MSB Parts. Only works for MSB Map Piece ('m*') parts
    currently."""
    bl_idname = "object.sync_msb_part_armatures"
    bl_label = "Sync MSB Part Armatures"
    bl_description = (
        "For all MSB Parts that instance the selected FLVER model's mesh, set the Part's Armature to the same "
        "as the FLVER and copy over any pose set in the FLVER. This may create a new Armature"
    )

    @classmethod
    def poll(cls, context) -> bool:
        if not context.mode == "OBJECT":
            return False
        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        if not bl_flver:
            return False
        if not bl_flver.armature:
            return False  # no Armature to sync with
        return True

    def execute(self, context):
        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        if not bl_flver.armature:
            return self.error("Active FLVER model has no Armature to sync.")

        msb_parts = bl_flver.sync_msb_part_armatures(context)

        self.info(f"Synchronized Armatures of {len(msb_parts)} MSB Parts to FLVER model '{bl_flver.name}'.")

        return {"FINISHED"}


@io_soulstruct_class
class ClearFLVERSubmeshProperties(LoggingOperator):
    """Clear all submesh properties on the active FLVER model, so that it will use global properties instead."""
    bl_idname = "flver.clear_submesh_props"
    bl_label = "Clear Submesh Properties"
    bl_description = "Clear all submesh properties on the active FLVER model, so that it will use global properties instead"

    @classmethod
    def poll(cls, context) -> bool:
        if not context.active_object or context.active_object.type != "MESH":
            return False
        return BlenderFLVER.is_obj_type(context.active_object)

    def execute(self, context):
        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        bl_flver.type_properties.submesh_props.clear()
        self.info(f"Cleared per-submesh properties on FLVER model '{bl_flver.name}'.")
        return {"FINISHED"}


@io_soulstruct_class
class AddFLVERSubmeshProperties(LoggingOperator):
    """Add per-submesh properties on the active FLVER model, to use instead of global properties."""
    bl_idname = "flver.add_submesh_props"
    bl_label = "Add Submesh Properties"
    bl_description = "Add per-submesh properties on the active FLVER model, to use instead of global properties"

    @classmethod
    def poll(cls, context) -> bool:
        if not context.active_object or context.active_object.type != "MESH":
            return False
        return BlenderFLVER.is_obj_type(context.active_object)

    def execute(self, context):
        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        for material_slot in bl_flver.obj.material_slots:
            material = material_slot.material
            if not material:
                continue  # empty slot, skip
            submesh_props = bl_flver.type_properties.submesh_props.add()
            submesh_props.material = material
            submesh_props.is_dynamic = bl_flver.type_properties.global_is_dynamic
            submesh_props.default_bone_index = bl_flver.type_properties.global_default_bone_index
            submesh_props.face_set_count = bl_flver.type_properties.global_face_set_count
            submesh_props.use_backface_culling = "MATERIAL"  # default
        self.info(
            f"Added per-submesh properties for {len(bl_flver.type_properties.submesh_props)} materials on "
            f"FLVER model '{bl_flver.name}'."
        )
        return {"FINISHED"}
