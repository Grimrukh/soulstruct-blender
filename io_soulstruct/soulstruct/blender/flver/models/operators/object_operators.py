"""Miscellaneous operators for copying/changing FLVER data."""
from __future__ import annotations

__all__ = [
    "CopyToNewFLVER",
    "RenameFLVER",
    "SelectMeshChildren",
]

import bpy

from soulstruct.blender.flver.models.types import BlenderFLVER
from soulstruct.blender.types import SoulstructType
from soulstruct.blender.utilities import LoggingOperator, replace_shared_prefix


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


class SelectMeshChildren(LoggingOperator):
    """Simple operator that iterates over selected objects, selects all MESH children of any ARMATURES, and deselects
    anything else that isn't a MESH."""
    bl_idname = "object.select_mesh_children"
    bl_label = "Select Mesh Children"
    bl_description = "Select all immediate Mesh children of selected objects and deselect all non-Meshes"

    @classmethod
    def poll(cls, context) -> bool:
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
