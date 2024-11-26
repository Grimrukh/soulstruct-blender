from __future__ import annotations

__all__ = [
    "MeshMoveSettings",
    "CopyMeshSelectionOperator",
    "CutMeshSelectionOperator",
    "BooleanMeshCut",
]

import bmesh
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

    mesh_move_settings = bpy.context.scene.mesh_move_settings

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
    else:
        # Remove all unused materials from temp object so they don't get needlessly copied to dest object.
        used_material_indices = set(poly.material_index for poly in temp_obj.data.polygons)
        unused_material_indices = set(range(len(temp_obj.data.materials))) - used_material_indices
        for i in sorted(unused_material_indices, reverse=True):  # avoid index shifting
            temp_obj.data.materials.pop(index=i)

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
            and len(context.selected_objects) == 1
            and context.selected_objects[0].type == "MESH"
            and context.selected_objects[0] is not context.edit_object
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
            and len(context.selected_objects) == 1
            and context.selected_objects[0].type == "MESH"
            and context.selected_objects[0] is not context.edit_object
        )

    def execute(self, context):
        if not self.poll(context):
            return self.error("Please select exactly two Mesh objects, one in Edit Mode.")

        return move_mesh_selection(self, context, duplicate=False)


class BooleanMeshCut(LoggingOperator):
    bl_idname = "mesh.boolean_mesh_cut"
    bl_label = "Boolean Mesh Cut"
    bl_description = (
        "Use selected faces of active edit mesh to bake a boolean difference cut into another selected mesh object. "
        "Useful to, e.g., use a room to cut a hole in a wall that it is embedded in"
    )

    @classmethod
    def poll(cls, context):
        """Check that the active object is a mesh in Edit Mode and that exactly one other object is selected."""
        if (
            context.mode != "EDIT_MESH"
            or not context.object
            or context.object.type != "MESH"
        ):
            return False
        selected_objects = [obj for obj in context.selected_objects if obj != context.object]
        return len(selected_objects) == 1 and selected_objects[0].type == "MESH"

    def execute(self, context):

        # Get the active object (in Edit Mode).
        # noinspection PyTypeChecker
        cut_source_obj = bpy.context.object  # type: bpy.types.MeshObject

        if not cut_source_obj or cut_source_obj.type != 'MESH':
            return self.error("The active object must be a mesh.")

        if cut_source_obj.mode != 'EDIT':
            return self.error("The active object (cut source) must be in Edit Mode.")

        # Get the other selected object (wall object).
        selected_objects = [obj for obj in bpy.context.selected_objects if obj != cut_source_obj]
        if len(selected_objects) != 1:
            return self.error("You must have exactly one additional Mesh object selected as the cut target.")
        cut_target_obj = selected_objects[0]
        if cut_target_obj.type != 'MESH':
            return self.error("The selected second object (cut target) must be a mesh.")

        # Access the BMesh of the active object.
        bm = bmesh.from_edit_mesh(cut_source_obj.data)
        bm.faces.ensure_lookup_table()

        # Get the selected faces.
        selected_faces = [face for face in bm.faces if face.select]
        if not selected_faces:
            return self.error("No faces selected in the active edit mesh.")

        # Create a temporary mesh for the selected faces.
        temp_mesh = bpy.data.meshes.new(name="TempMesh")
        temp_obj = bpy.data.objects.new(name="TempObject", object_data=temp_mesh)
        temp_obj.matrix_local = cut_source_obj.matrix_world  # important!
        context.scene.collection.objects.link(temp_obj)

        # Extract the selected faces into the temporary mesh.
        selected_verts = set(vert for face in selected_faces for vert in face.verts)
        temp_bm = bmesh.new()
        temp_bm_verts = {v: temp_bm.verts.new(v.co) for v in selected_verts}
        for face in selected_faces:
            temp_bm.faces.new([temp_bm_verts[v] for v in face.verts])
        temp_bm.to_mesh(temp_mesh)
        temp_bm.free()

        # Get all objects using the same mesh data as wall_obj.
        cut_target_mesh = cut_target_obj.data
        linked_objects = [
            obj for obj in bpy.data.objects
            if obj.data == cut_target_mesh and obj != cut_target_obj
        ]

        # Temporarily assign the temp_mesh to all linked objects (since we already have it).
        # This is necessary to get around the 'can't apply modifiers to multi-user data' restriction.
        for obj in linked_objects:
            obj.data = temp_mesh

        # Apply the Boolean Modifier to the shared mesh
        boolean_modifier = cut_target_obj.modifiers.new(name="CutHole", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = temp_obj

        context.view_layer.objects.active = cut_target_obj

        try:
            bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        finally:
            # Restore the modified mesh back to all linked objects
            for obj in linked_objects:
                obj.data = cut_target_mesh
            # Delete the temporary object and its mesh
            bpy.data.objects.remove(temp_obj, do_unlink=True)
            bpy.data.meshes.remove(temp_mesh, do_unlink=True)
            # Restore active object to edit mesh (or we get brief weird behavior)
            bpy.context.view_layer.objects.active = cut_source_obj

        self.info(f"Cut operation completed on shared mesh data of {cut_target_obj.name}.")
        return {"FINISHED"}
