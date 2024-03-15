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


def move_mesh_selection(
    operator: LoggingOperator,
    context: bpy.types.Context,
    duplicate: bool,
) -> set[str]:
    """Either cut (`duplicate = False`) or copy selected faces of edited mesh to another Mesh."""

    # Identify edited and non-edited meshes
    # noinspection PyTypeChecker
    source_mesh = context.edit_object  # type: bpy.types.MeshObject
    # noinspection PyTypeChecker
    dest_mesh = [
        obj for obj in context.selected_objects if obj != source_mesh
    ][0]  # type: bpy.types.MeshObject

    mesh_move_settings = bpy.context.scene.mesh_move_settings  # type: MeshMoveSettings

    # Duplicate selected vertices, edges, and faces in the edited mesh
    bpy.ops.object.mode_set(mode="EDIT")
    if duplicate:
        bpy.ops.mesh.duplicate()
    bpy.ops.mesh.separate(type="SELECTED")

    # Switch to OBJECT mode and identify the newly created object
    bpy.ops.object.mode_set(mode="OBJECT")
    try:
        # noinspection PyTypeChecker
        temp_obj = [
            obj for obj in context.selected_objects
            if obj != source_mesh and obj != dest_mesh
        ][0]  # type: bpy.types.MeshObject
    except IndexError:
        return operator.error("Could not identify temporary mesh object used for copy operation.")

    if mesh_move_settings.new_material_index > -1:
        # Change materials of temp object to materials of destination object, and assign new material index to all.
        temp_obj.data.materials.clear()
        for dest_mat in dest_mesh.data.materials:
            temp_obj.data.materials.append(dest_mat)
        for poly in temp_obj.data.polygons:
            poly.material_index = mesh_move_settings.new_material_index

    # Join the newly created mesh to the dest mesh.
    operator.deselect_all()
    dest_mesh.select_set(True)
    temp_obj.select_set(True)
    context.view_layer.objects.active = dest_mesh
    bpy.ops.object.join()

    return {"FINISHED"}

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
        if not self.poll(context):
            return self.error("Please select exactly two Mesh objects, one in Edit Mode.")

        return move_mesh_selection(self, context, duplicate=True)


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
        if not self.poll(context):
            return self.error("Please select exactly two Mesh objects, one in Edit Mode.")

        return move_mesh_selection(self, context, duplicate=False)
