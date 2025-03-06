"""Miscellaneous Bone operators that only make sense for FLVER models."""
from __future__ import annotations

__all__ = [
    "BakeBonePoseToVertices",
    "ReboneVertices",
]

import bpy
from mathutils import Matrix, Quaternion, Vector

from io_soulstruct.exceptions import SoulstructTypeError
from io_soulstruct.flver.models.types import BlenderFLVER
from io_soulstruct.utilities import LoggingOperator


class BakeBonePoseToVertices(LoggingOperator):

    bl_idname = "mesh.bake_bone_pose_to_vertices"
    bl_label = "Bake Bone Pose to Vertices"
    bl_description = (
        "Bake the pose of each selected bone into all vertices weighted ONLY to that bone into the mesh and set bone "
        "pose to origin. Valid only for Map Piece FLVERs (`Bone Data Type` must be set to 'Pose Bones' in Object FLVER "
        "properties)"
    )

    @classmethod
    def poll(cls, context) -> bool:
        """Must select at least one bone in Armature of active object."""
        if (
            context.mode != "OBJECT"
            or not context.active_object
            or not context.active_object.type == "ARMATURE"
        ):
            return False

        try:
            bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        except SoulstructTypeError:
            return False

        if not bl_flver.armature or bl_flver.bone_data_type != "PoseBone":
            return False

        # At least one bone must be selected.
        return any(bone.select for bone in bl_flver.armature.data.bones)

    def execute(self, context):

        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        armature = bl_flver.armature
        mesh = bl_flver.mesh

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
                    f"{[group.name for group in vertex.groups]}. No bone transforms were baked."
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
    def poll(cls, context) -> bool:
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
