from __future__ import annotations

__all__ = ["CopyMeshSelectionOperator"]

import bpy

from io_soulstruct.utilities import LoggingOperator


class CopyMeshSelectionOperator(LoggingOperator):
    bl_idname = "object.copy_mesh_selection"
    bl_label = "Copy Edit Mesh Selection to Mesh"
    bl_description = "Copy the selected vertices, edges, and faces from the edited mesh to the other selected mesh"

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "EDIT_MESH"
            and len(context.selected_objects) == 2
            and all(obj.type == "MESH" for obj in context.selected_objects)
        )

    def execute(self, context):
        # Check if two objects are selected
        if len(context.selected_objects) != 2:
            return self.error("Please select exactly two mesh objects.")

        # Identify edited and non-edited meshes
        edited_mesh_obj = context.edit_object
        non_edited_mesh_obj = [obj for obj in context.selected_objects if obj != edited_mesh_obj][0]

        # Check if both are mesh objects
        if edited_mesh_obj.type != "MESH" or non_edited_mesh_obj.type != "MESH":
            return self.error("Both selected objects must be of type 'MESH'.")

        # Duplicate selected vertices, edges, and faces in the edited mesh
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.duplicate()
        bpy.ops.mesh.separate(type="SELECTED")

        # Switch to OBJECT mode and identify the newly created object
        bpy.ops.object.mode_set(mode="OBJECT")
        try:
            temp_obj = [
                obj for obj in context.selected_objects
                if obj != edited_mesh_obj and obj != non_edited_mesh_obj
            ][0]
        except IndexError:
            return self.error("Could not identify temporary mesh object used for copy operation.")

        # Join the newly created mesh to the non-edited mesh
        bpy.ops.object.select_all(action="DESELECT")
        non_edited_mesh_obj.select_set(True)
        temp_obj.select_set(True)
        context.view_layer.objects.active = non_edited_mesh_obj  # copy target
        bpy.ops.object.join()

        return {"FINISHED"}
