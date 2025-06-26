from __future__ import annotations

__all__ = [
    "NavmeshFaceSettings",
    "RenameNavmesh",
    "RefreshFaceIndices",
    "AddNVMFaceFlags",
    "RemoveNVMFaceFlags",
    "SetNVMFaceFlags",
    "SetNVMFaceObstacleCount",
    "ResetNVMFaceInfo",
    "AddNVMEventEntityTriangleIndex",
    "RemoveNVMEventEntityTriangleIndex",
    "GenerateNavmeshFromCollision",
]

import bmesh
import bpy
from mathutils import Vector

from soulstruct.base.events.enums import NavmeshFlag

from soulstruct.blender.bpy_base.property_group import SoulstructPropertyGroup
from soulstruct.blender.exceptions import SoulstructTypeError
from soulstruct.blender.types import SoulstructType
from soulstruct.blender.utilities import ObjectType, LoggingOperator, replace_shared_prefix
from .types import BlenderNVM
from .utilities import set_face_material, get_navmesh_material

# Get all non-default `NavmeshFlag` values for Blender `EnumProperty`.
_navmesh_flag_items = [
    (str(flag.value), flag.name, "") for flag in NavmeshFlag
    if flag.value > 0
]


class NavmeshFaceSettings(SoulstructPropertyGroup):

    # No game-specific properties.

    navmesh_flag: bpy.props.EnumProperty(
        name="Flag",
        items=_navmesh_flag_items,
        default="1",  # Disable
        description="Navmesh type to add or remove",
    )
    obstacle_count: bpy.props.IntProperty(
        name="Obstacle Count",
        default=0,
        min=0,
        max=255,
        description="Number of obstacles on this navmesh face.",
    )


class RenameNavmesh(LoggingOperator):
    """Simply renames an NVM model and all MSB Navmesh parts that instance it."""
    bl_idname = "object.rename_nvm"
    bl_label = "Rename Navmesh"
    bl_description = (
        "Rename the selected NVM navmesh model and, optionally, the overlapping prefix of any MSB Navmesh part that "
        "instances it"
    )

    new_name: bpy.props.StringProperty(
        name="New Name",
        description="New name for the NVM model",
        default="",
    )
    rename_parts: bpy.props.BoolProperty(
        name="Rename Parts",
        description="Rename MSB Navmesh parts that instance this NVM model",
        default=True,
    )

    @classmethod
    def poll(cls, context) -> bool:
        try:
            BlenderNVM.from_active_object(context)
        except SoulstructTypeError:
            return False
        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, title="Rename Navmesh")

    def execute(self, context):
        if not self.new_name:
            return self.error("New NVM name cannot be empty.")

        bl_nvm = BlenderNVM.from_active_object(context)
        old_model_name = bl_nvm.game_name  # we never rename MORE than this much of the old name
        new_model_name = self.new_name

        bl_nvm.rename(new_model_name)  # will also rename NVM Event Entity children

        if self.rename_parts:
            part_count = 0
            for obj in bpy.data.objects:
                if (
                    obj.soulstruct_type == SoulstructType.MSB_PART
                    and obj.MSB_PART.entry_subtype == "MSB_NAVMESH"
                    and obj is not bl_nvm
                    and obj.data == bl_nvm.data
                ):
                    # Found a part to rename.
                    part_count += 1
                    obj.name = replace_shared_prefix(old_model_name, new_model_name, obj.name)
            self.info(f"Renamed {part_count} MSB Navmeshes that instance '{old_model_name}' to '{new_model_name}'.")

        return {"FINISHED"}


class RefreshFaceIndices(LoggingOperator):
    bl_idname = "mesh.refresh_face_indices"
    bl_label = "Refresh Selected Face Indices"
    bl_description = "Refresh the list of selected face indices"

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def execute(self, context):
        bpy.context.area.tag_redraw()
        return {"FINISHED"}


class AddNVMFaceFlags(LoggingOperator):
    bl_idname = "mesh.add_nvm_face_flags"
    bl_label = "Add NVM Face Flags"
    bl_description = "Add the selected NavmeshFlag bit flag to all selected faces"

    @classmethod
    def poll(cls, context) -> bool:
        return context.edit_object is not None and context.mode == "EDIT_MESH"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.edit_object
        if obj is None or obj.type != ObjectType.MESH:
            return self.error("No Mesh selected.")

        obj: bpy.types.MeshObject
        bm = bmesh.from_edit_mesh(obj.data)

        props = context.scene.navmesh_face_settings
        navmesh_flag = int(props.navmesh_flag)

        flags_layer = bm.faces.layers.int.get("nvm_face_flags")
        if flags_layer:
            selected_faces = [face for face in bm.faces if face.select]
            for face in selected_faces:
                face[flags_layer] |= navmesh_flag
                set_face_material(bl_mesh=obj.data, bl_face=face, face_flags=face[flags_layer])

            bmesh.update_edit_mesh(obj.data)

        # TODO: Would be nice to remove now-unused materials from the mesh.

        return {"FINISHED"}


class RemoveNVMFaceFlags(LoggingOperator):
    bl_idname = "mesh.remove_nvm_face_flags"
    bl_label = "Remove NVM Face Flags"
    bl_description = "Remove the selected NavmeshFlag bit flag from all selected faces"

    @classmethod
    def poll(cls, context) -> bool:
        return context.edit_object is not None and context.mode == "EDIT_MESH"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.edit_object
        if obj is None or obj.type != ObjectType.MESH:
            return self.error("No Mesh selected.")

        obj: bpy.types.MeshObject
        bm = bmesh.from_edit_mesh(obj.data)

        props = context.scene.navmesh_face_settings
        navmesh_flag = int(props.navmesh_flag)

        flags_layer = bm.faces.layers.int.get("nvm_face_flags")
        if flags_layer:
            selected_faces = [face for face in bm.faces if face.select]
            for face in selected_faces:
                face[flags_layer] &= ~navmesh_flag
                set_face_material(bl_mesh=obj.data, bl_face=face, face_flags=face[flags_layer])

            bmesh.update_edit_mesh(obj.data)

        # TODO: Would be nice to remove now-unused materials from the mesh.

        return {"FINISHED"}


class SetNVMFaceFlags(LoggingOperator):
    bl_idname = "mesh.set_nvm_face_flags"
    bl_label = "Set NVM Face Flags"
    bl_description = "Set the selected NavmeshFlag bit flag (and no others) to all selected faces"

    @classmethod
    def poll(cls, context) -> bool:
        return context.edit_object is not None and context.mode == "EDIT_MESH"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.edit_object
        if obj is None or obj.type != ObjectType.MESH:
            return self.error("No Mesh selected.")

        obj: bpy.types.MeshObject
        bm = bmesh.from_edit_mesh(obj.data)

        props = context.scene.navmesh_face_settings
        navmesh_flag = int(props.navmesh_flag)

        flags_layer = bm.faces.layers.int.get("nvm_face_flags")
        if flags_layer:
            selected_faces = [face for face in bm.faces if face.select]
            for face in selected_faces:
                face[flags_layer] = navmesh_flag
                set_face_material(bl_mesh=obj.data, bl_face=face, face_flags=face[flags_layer])

            bmesh.update_edit_mesh(obj.data)

        # TODO: Would be nice to remove now-unused materials from the mesh.

        return {"FINISHED"}


class SetNVMFaceObstacleCount(LoggingOperator):
    bl_idname = "mesh.set_nvm_face_obstacle_count"
    bl_label = "Set NVM Face Obstacle Count"
    bl_description = "Set the obstacle count for all selected faces"

    @classmethod
    def poll(cls, context) -> bool:
        return context.edit_object is not None and context.mode == "EDIT_MESH"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.edit_object
        if obj is None or obj.type != ObjectType.MESH:
            return {"CANCELLED"}

        obj: bpy.types.MeshObject
        bm = bmesh.from_edit_mesh(obj.data)

        props = context.scene.navmesh_face_settings

        obstacle_count_layer = bm.faces.layers.int.get("nvm_face_obstacle_count")
        if obstacle_count_layer:
            selected_faces = [face for face in bm.faces if face.select]
            for face in selected_faces:
                face[obstacle_count_layer] = props.obstacle_count

            bmesh.update_edit_mesh(obj.data)

        return {"FINISHED"}


class ResetNVMFaceInfo(LoggingOperator):
    """Reset all NVM face flags and obstacle counts to default, and create face layers if missing.

    Useful for turning a newly created Blender mesh into a Navmesh.
    """
    bl_idname = "mesh.reset_nvm_face_info"
    bl_label = "Reset NVM Face Info"
    bl_description = "Reset NVM face flags and obstacle counts of selected faces to default (both zero)"
    
    DEFAULT_FLAGS = 0
    DEFAULT_OBSTACLE_COUNT = 0

    @classmethod
    def poll(cls, context) -> bool:
        return context.edit_object is not None and context.mode == "EDIT_MESH"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.edit_object
        if obj is None or obj.type != ObjectType.MESH:
            return {"CANCELLED"}

        obj: bpy.types.MeshObject
        bm = bmesh.from_edit_mesh(obj.data)

        # TODO: Can probably use `verify()`.
        flags_layer = bm.faces.layers.int.get("nvm_face_flags")
        if flags_layer is None:
            flags_layer = bm.faces.layers.int.new("nvm_face_flags")
        obstacle_count_layer = bm.faces.layers.int.get("nvm_face_obstacle_count")
        if obstacle_count_layer is None:
            obstacle_count_layer = bm.faces.layers.int.new("nvm_face_obstacle_count")

        for face in bm.faces:
            if not face.select:
                continue
            face[flags_layer] = self.DEFAULT_FLAGS
            face[obstacle_count_layer] = self.DEFAULT_OBSTACLE_COUNT
            set_face_material(bl_mesh=obj.data, bl_face=face, face_flags=face[flags_layer])

        # TODO: Would be nice to remove unused materials from the mesh.

        bmesh.update_edit_mesh(obj.data)

        return {"FINISHED"}


class AddNVMEventEntityTriangleIndex(bpy.types.Operator):
    bl_idname = "nvm_event_entity.add_triangle_index"
    bl_label = "Add Triangle"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object and context.active_object.soulstruct_type == SoulstructType.NVM_EVENT_ENTITY

    def execute(self, context):
        nvm_event_entity = context.active_object
        nvm_event_entity.NVM_EVENT_ENTITY.triangle_indices.add()
        return {'FINISHED'}


class RemoveNVMEventEntityTriangleIndex(bpy.types.Operator):
    bl_idname = "nvm_event_entity.remove_triangle_index"
    bl_label = "Remove Triangle"

    @classmethod
    def poll(cls, context) -> bool:
        return (
            context.active_object
            and context.active_object.soulstruct_type == SoulstructType.NVM_EVENT_ENTITY
            and len(context.active_object.NVM_EVENT_ENTITY.triangle_indices) > 0
        )

    def execute(self, context):
        obj = context.active_object
        index = obj.NVM_EVENT_ENTITY.triangle_index
        obj.NVM_EVENT_ENTITY.triangle_indices.remove(index)
        obj.NVM_EVENT_ENTITY.triangle_index = max(0, index - 1)
        return {'FINISHED'}


def get_connected_component(face, visited):
    """Flood-fill connected selected faces starting from `face`."""
    island = set()
    stack = [face]
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        island.add(current)
        # Look at all faces sharing an edge with the current face.
        for edge in current.edges:
            for linked_face in edge.link_faces:
                if linked_face.select and linked_face not in visited:
                    stack.append(linked_face)
    return island


class GenerateNavmeshFromCollision(LoggingOperator):
    bl_idname = "object.generate_navmesh_from_collision"
    bl_label = "Generate Navmesh from Collision"
    bl_description = (
        "Generate a simplified navmesh from a collision mesh. "
        "Walkable faces (those with normals nearly vertical) are duplicated into a new object, "
        "triangulated, and then simplified via Limited Dissolve"
    )

    walkable_threshold: bpy.props.FloatProperty(
        name="Walkable Threshold",
        description="Minimum dot product of face normal with global up (0,0,1) for a face to be considered walkable",
        default=0.95,
        min=0.0, max=1.0
    )
    island_area_threshold: bpy.props.FloatProperty(
        name="Island Area Threshold",
        description="Minimum area (in Blender units²) of a connected group of walkable faces to keep",
        default=0.1,
        min=0.0
    )
    dissolve_angle_limit: bpy.props.FloatProperty(
        name="Dissolve Angle Limit",
        description="Angle limit (in degrees) for Limited Dissolve operator",
        default=5.0,
        min=0.0, max=180.0
    )
    min_walkable_faces: bpy.props.IntProperty(
        name="Minimum Walkable Faces",
        description="Minimum number of walkable faces required to generate a navmesh (or operator will abort)",
        default=1,
        min=1,
    )
    vertical_bump: bpy.props.FloatProperty(
        name="Vertical Bump",
        description="Amount to bump the navmesh up vertically after triangulation",
        default=0.1,
        min=0.0,
    )

    @classmethod
    def poll(cls, context):
        """Must select exactly one active Mesh object in OBJECT mode."""
        if not context.mode == "OBJECT":
            return False
        if not len(context.selected_objects) == 1:
            return False
        obj = context.active_object
        return obj is not None and obj.type == 'MESH'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        # Assume the active object is the collision mesh.
        # noinspection PyTypeChecker
        collision_obj = context.active_object  # type: bpy.types.MeshObject

        # Ensure we are in Edit mode so we can use bmesh.
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(collision_obj.data)

        # Deselect all faces first.
        for face in bm.faces:
            face.select = False

        # Global up vector (world space).
        up = Vector((0, 0, 1))
        # For each face, transform its normal to world space and select if walkable.
        # Note: if the collision object has a non-identity transform, we must transform the face normals.
        # TODO: Can ignore world matrix, I think.
        matrix = collision_obj.matrix_world.to_3x3()
        for face in bm.faces:
            # For Collisions, we only use 'Lo' faces.
            if collision_obj.soulstruct_type == SoulstructType.COLLISION:
                material = collision_obj.data.materials[face.material_index]
                if "(Lo)" not in material.name:
                    continue
            world_normal = matrix @ face.normal
            # If the face normal is close enough to up, mark it as selected.
            if world_normal.dot(up) >= self.walkable_threshold:
                face.select = True

        bmesh.update_edit_mesh(collision_obj.data)

        # Now deselect small islands of selected faces.
        visited = set()
        for face in list(bm.faces):
            if face.select and face not in visited:
                island = get_connected_component(face, visited)
                # Compute total area of the island.
                total_area = sum(f.calc_area() for f in island)
                if total_area < self.island_area_threshold:
                    for f in island:
                        f.select = False
        bmesh.update_edit_mesh(collision_obj.data)

        # Make sure we selected enough walkable faces.
        select_count = sum(1 for face in bm.faces if face.select)
        bm.free()  # done with this BMesh

        if select_count < self.min_walkable_faces:
            return self.error(
                f"Not enough walkable faces found ({select_count} < {self.min_walkable_faces}) with current settings."
            )

        # Duplicate and separate the selected faces into a new object.
        bpy.ops.mesh.duplicate()
        bpy.ops.mesh.separate(type='SELECTED')

        # Switch back to Object mode.
        bpy.ops.object.mode_set(mode='OBJECT')

        # Identify the new navmesh object: it should be the one selected that is not our original collision object.
        for obj in context.selected_objects:
            if obj != collision_obj and obj.type == 'MESH':
                # noinspection PyTypeChecker
                navmesh_obj = obj  # type: bpy.types.MeshObject
                break
        else:
            return self.error("Failed to separate walkable faces into a new object.")

        # Rename the navmesh object.
        navmesh_obj.name = f"{collision_obj.name} Navmesh"
        navmesh_obj.soulstruct_type = SoulstructType.NAVMESH
        navmesh_obj.show_wire = True

        # Now we simplify the navmesh geometry.
        
        self.edit_object(context, navmesh_obj)

        # Just 'Default' navmesh material on new object.
        bl_material = get_navmesh_material(0)  # Default
        navmesh_obj.data.materials.clear()
        navmesh_obj.data.materials.append(bl_material)

        # Use BMesh to triangulate the mesh, set its material, and bump it up vertically.
        bm_nav = bmesh.from_edit_mesh(navmesh_obj.data)
        bmesh.ops.triangulate(bm_nav, faces=bm_nav.faces, quad_method="BEAUTY", ngon_method="BEAUTY")
        for face in bm_nav.faces:
            face.material_index = 0
        if self.vertical_bump > 0.0:
            for vertex in bm_nav.verts:
                vertex.co.z += self.vertical_bump
        bmesh.update_edit_mesh(navmesh_obj.data)
        bm_nav.free()
        del bm_nav

        # Select all geometry and Merge by Distance (remove doubles).
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()
        # TODO: Limit dissolve is too aggressive.
        # bpy.ops.mesh.dissolve_limited(angle_limit=self.dissolve_angle_limit)

        # Switch back to Object mode.
        bpy.ops.object.mode_set(mode='OBJECT')

        self.info(f"Navmesh generated: '{navmesh_obj.name}'")
        bm.free()
        return {'FINISHED'}
