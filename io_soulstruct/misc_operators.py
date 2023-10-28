from __future__ import annotations

__all__ = [
    "MeshMoveSettings",
    "CopyMeshSelectionOperator",
    "CutMeshSelectionOperator",
]

import bpy

from io_soulstruct.utilities.operators import LoggingOperator


class MeshMoveSettings(bpy.types.PropertyGroup):
    new_material_index: bpy.props.IntProperty(
        name="New Material Index",
        description="Material index to set for cut or copied mesh selection. Leave as -1 to bring over materials",
        default=-1,
    )


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
        # noinspection PyTypeChecker
        dest_msh_obj = [
            obj for obj in context.selected_objects if obj != edited_mesh_obj
        ][0]  # type: bpy.types.MeshObject

        # Check if both are mesh objects
        if edited_mesh_obj.type != "MESH" or dest_msh_obj.type != "MESH":
            return self.error("Both selected objects must be of type 'MESH'.")

        settings = bpy.context.scene.mesh_move_settings  # type: MeshMoveSettings

        # Duplicate selected vertices, edges, and faces in the edited mesh
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.duplicate()
        bpy.ops.mesh.separate(type="SELECTED")

        # Switch to OBJECT mode and identify the newly created object
        bpy.ops.object.mode_set(mode="OBJECT")
        try:
            # noinspection PyTypeChecker
            temp_obj = [
                obj for obj in context.selected_objects
                if obj != edited_mesh_obj and obj != dest_msh_obj
            ][0]  # type: bpy.types.MeshObject
        except IndexError:
            return self.error("Could not identify temporary mesh object used for copy operation.")

        if settings.new_material_index > -1:
            # Change materials of temp object to materials of destination object, and assign new material index to all.
            temp_obj.data.materials.clear()
            for dest_mat in dest_msh_obj.data.materials:
                temp_obj.data.materials.append(dest_mat)
            for poly in temp_obj.data.polygons:
                poly.material_index = 0

        # Join the newly created mesh to the non-edited mesh.
        self.deselect_all()
        dest_msh_obj.select_set(True)
        temp_obj.select_set(True)
        context.view_layer.objects.active = dest_msh_obj  # copy target
        bpy.ops.object.join()

        return {"FINISHED"}


class CutMeshSelectionOperator(LoggingOperator):
    bl_idname = "object.cut_mesh_selection"
    bl_label = "Cut Edit Mesh Selection to Mesh"
    bl_description = "Move the selected vertices/edges/faces from a mesh being edited to another selected mesh"

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
        dest_msh_obj = [obj for obj in context.selected_objects if obj != edited_mesh_obj][0]
        dest_msh_obj: bpy.types.MeshObject

        # Check if both are mesh objects
        if edited_mesh_obj.type != "MESH" or dest_msh_obj.type != "MESH":
            return self.error("Both selected objects must be of type 'MESH'.")

        settings = bpy.context.scene.mesh_move_settings  # type: MeshMoveSettings

        # Separate selected vertices, edges, and faces in the edited mesh WITHOUT duplicating them
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.separate(type="SELECTED")

        # Switch to OBJECT mode and identify the newly created object
        bpy.ops.object.mode_set(mode="OBJECT")
        try:
            temp_obj = [
                obj for obj in context.selected_objects
                if obj != edited_mesh_obj and obj != dest_msh_obj
            ][0]  # type: bpy.types.MeshObject
        except IndexError:
            return self.error("Could not identify temporary mesh object used for copy operation.")

        if settings.new_material_index > -1:
            # Change materials of temp object to materials of destination object, and assign new material index to all.
            temp_obj.data.materials.clear()
            for dest_mat in dest_msh_obj.data.materials:
                temp_obj.data.materials.append(dest_mat)
            for poly in temp_obj.data.polygons:
                poly.material_index = 0

        # Join the newly created mesh to the non-edited mesh
        bpy.ops.object.select_all(action="DESELECT")
        dest_msh_obj.select_set(True)
        temp_obj.select_set(True)
        context.view_layer.objects.active = dest_msh_obj  # copy target
        bpy.ops.object.join()

        return {"FINISHED"}
