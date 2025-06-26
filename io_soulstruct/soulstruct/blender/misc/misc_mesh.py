"""Miscellaneous Mesh operators."""
from __future__ import annotations

__all__ = [
    "CopyMeshSelectionOperator",
    "CutMeshSelectionOperator",
    "BooleanMeshCut",
    "ApplyLocalMatrixToMesh",
    "ScaleMeshIslands",
    "SelectActiveMeshVerticesNearSelected",
    "ConvexHullOnEachMeshIsland",
    "SetActiveFaceNormalUpward",
    "SpawnObjectIntoMeshAtFaces",
    "WeightVerticesWithFalloff",
    "ApplyModifierNonSingleUser",
]

import math
import random
from collections import deque

import bmesh
import bpy
from mathutils import Matrix, Vector, kdtree

from soulstruct.blender.utilities.operators import LoggingOperator


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
    def poll(cls, context) -> bool:
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
    def poll(cls, context) -> bool:
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
    def poll(cls, context) -> bool:
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


class ApplyLocalMatrixToMesh(LoggingOperator):

    bl_idname = "object.apply_local_matrix_to_mesh"
    bl_label = "Apply Local Matrix to Mesh"
    bl_description = (
        "For each selected object, apply its local (NOT world) transform to its Mesh model data, then reset the "
        "model's transform to identity. Gets around Blender's usual 'no multi user' constraint for applying an object "
        "transform to its Mesh. Useful for applying temporary local transforms on FLVER/Collision/Navmesh models "
        "(which do not affect model/MSB export at all) that you want to now propagate to their MSB Parts"
    )

    @classmethod
    def poll(cls, context) -> bool:
        """Select at least one MSB Part."""
        if not context.selected_objects:
            return False
        if not all(
            obj.type == "MESH"
            for obj in context.selected_objects
        ):
            return False
        return True

    def execute(self, context):
        success_count = 0
        for obj in context.selected_objects:
            obj: bpy.types.MeshObject
            try:
                self._apply_matrix_local_to_mesh(obj)
            except Exception as ex:
                self.error(f"Failed to apply local transform of object '{obj.name}' to its Mesh: {ex}")
            else:
                success_count += 1

        if success_count == 0:
            return self.error("Failed to apply local transform to any models of selected Mesh objects.")

        self.info(
            f"Applied transform to {success_count} / {len(context.selected_objects)} Mesh object"
            f"{'s' if success_count > 1 else ''}."
        )
        return {"FINISHED"}

    @staticmethod
    def _apply_matrix_local_to_mesh(part: bpy.types.MeshObject):
        mesh = part.data
        local_transform = part.matrix_local.copy()
        mesh.transform(local_transform)  # applies to mesh data
        part.matrix_local = Matrix.Identity(4)  # reset to identity


class ScaleMeshIslands(LoggingOperator):

    bl_idname = "mesh.scale_mesh_islands"
    bl_label = "Scale Mesh Islands"
    bl_description = (
        "For each selected face in the edited mesh, select all faces linked to that face (sharing an edge) and scale "
        "the collective island of faces by the given factor relative to their shared centroid"
    )

    scale_factor: bpy.props.FloatProperty(
        name="Scale Factor",
        description="Factor by which to uniformly scale each island of faces",
        default=1.0,
    )

    @classmethod
    def poll(cls, context) -> bool:
        return context.mode == "EDIT_MESH" and context.edit_object.type == "MESH"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):

        # noinspection PyTypeChecker
        obj = context.edit_object  # type: bpy.types.MeshObject

        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()

        # Record the initially selected faces to restore later.
        initially_selected_faces = {face for face in bm.faces if face.select}

        # Use face `tag` to track visited faces.
        for face in bm.faces:
            face.tag = False

        for face in initially_selected_faces:
            if face.tag:
                continue  # part of a previous island

            # Select the connected geometry (island) using 'select linked'
            self.deselect_all()
            face.select_set(True)
            bpy.ops.mesh.select_linked(delimit={"NORMAL"})  # select connected geometry by connectivity

            current_island_faces = {f for f in bm.faces if f.select}
            for island_face in current_island_faces:
                island_face.tag = True  # visited

            # Compute the center of the island.
            island_verts = {v for f in current_island_faces for v in f.verts}
            center = sum((v.co for v in island_verts), Vector()) / len(island_verts)

            # Scale the vertices around the island's center (wrapping with translation to origin).
            scale_matrix = Matrix.Translation(center) @ Matrix.Scale(self.scale_factor, 4) @ Matrix.Translation(-center)
            for vert in island_verts:
                vert.co = scale_matrix @ vert.co

        bmesh.update_edit_mesh(obj.data)
        self.info(f"Scaled each selected island by a factor of {self.scale_factor}.")

        # Restore the initial face selection.
        self.deselect_all()
        for face in initially_selected_faces:
            face.select = True
        return {"FINISHED"}


class SelectActiveMeshVerticesNearSelected(LoggingOperator):

    bl_idname = "mesh.select_active_mesh_vertices_near_selected"
    bl_label = "Select Active Mesh Vertices Near Selected"
    bl_description = (
        "Select all vertices of the active/edited mesh that are within the given distance of any vertices in any other "
        "selected mesh, and deselect all other vertices. Works in both Object and Edit Mesh modes"
    )

    max_distance: bpy.props.FloatProperty(
        name="Max Distance",
        description="Maximum distance between vertices to select",
        default=0.1,
        min=0.0,
    )

    @classmethod
    def poll(cls, context):
        return (
            context.mode in {"OBJECT", "EDIT_MESH"}
            and context.active_object and context.active_object.type == "MESH"
            and len(context.selected_objects) > 1
            and all(obj.type == "MESH" for obj in context.selected_objects)
        )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):

        if context.mode == "OBJECT":
            bm = bmesh.new()
            # noinspection PyTypeChecker
            active_obj = context.active_object  # type: bpy.types.MeshObject
            bm.from_mesh(active_obj.data)
            is_edit_mode = False
        elif context.mode == "EDIT_MESH":
            # noinspection PyTypeChecker
            active_obj = context.edit_object  # type: bpy.types.MeshObject
            bm = bmesh.from_edit_mesh(active_obj.data)
            is_edit_mode = True
        else:
            return self.error("Active object must be a mesh in Object or Edit Mesh mode.")

        # noinspection PyTypeChecker
        other_objs = [obj for obj in context.selected_objects if obj != active_obj]  # type: list[bpy.types.MeshObject]

        # Build a KD-tree from the other object's vertices (in global space)
        kd_trees = []
        for other_obj in other_objs:
            other_mesh = other_obj.data
            size = len(other_mesh.vertices)
            kd = kdtree.KDTree(size)
            for i, v in enumerate(other_mesh.vertices):
                # Transform vertex coordinate to global space
                kd.insert(other_obj.matrix_world @ v.co, i)
            kd.balance()
            kd_trees.append(kd)

        # For each vertex in the active mesh, check if it's close to any vertex from the other mesh
        for v in bm.verts:
            global_co = active_obj.matrix_world @ v.co
            for kd in kd_trees:
                # `kd.find_range()` returns a list of (co, index, distance) for points within `max_distance`
                if kd.find_range(global_co, self.max_distance):
                    v.select = True
                    break
            else:
                # Deselect vertex.
                v.select = False

        if is_edit_mode:
            # Update the mesh in Edit Mesh mode to reflect the selection changes.
            bmesh.update_edit_mesh(active_obj.data)
        else:
            # Update the mesh in Object Mode to reflect the selection changes.
            bm.to_mesh(active_obj.data)

        return {"FINISHED"}


class ConvexHullOnEachMeshIsland(LoggingOperator):

    bl_idname = "mesh.convex_hull_on_each_mesh_island"
    bl_label = "Convex Hull on Each Mesh Island"
    bl_description = (
        "For each selected face in the edited mesh, select all faces linked to that face (sharing an edge) and run the "
        "Convex Hull operator with the given settings. Useful for quickly creating simplified collision meshes. See "
        "the underlying 'Convex Hull' and 'Tris to Quads' operators for parameter descriptions"
    )

    delete_unused: bpy.props.BoolProperty(name="Deleted Unused", default=True)
    use_existing_faces: bpy.props.BoolProperty(name="Use Existing Faces", default=True)
    make_holes: bpy.props.BoolProperty(name="Make Holes", default=False)
    join_triangles: bpy.props.BoolProperty(name="Join Triangles", default=True)
    face_threshold: bpy.props.FloatProperty(name="Max Face Angle (Rad)", default=0.698132)
    shape_threshold: bpy.props.FloatProperty(name="Max Shape Angle (Rad)", default=0.698132)
    uvs: bpy.props.BoolProperty(name="Compare UVs", default=False)
    vcols: bpy.props.BoolProperty(name="Compare Vertex Colors", default=False)
    seam: bpy.props.BoolProperty(name="Compare Seam", default=False)
    sharp: bpy.props.BoolProperty(name="Compare Sharp", default=False)
    materials: bpy.props.BoolProperty(name="Compare Materials", default=False)

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "EDIT_MESH"
            and context.edit_object and context.edit_object.type == "MESH"
        )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Convex Hull:")
        layout.prop(self, "delete_unused")
        layout.prop(self, "use_existing_faces")
        layout.prop(self, "make_holes")
        layout.prop(self, "join_triangles")
        # Only show Tris to Quads options if `join_triangles` is enabled.
        if self.join_triangles:
            layout.label(text="Tris to Quads:")
            layout.prop(self, "face_threshold")
            layout.prop(self, "shape_threshold")
            layout.prop(self, "uvs")
            layout.prop(self, "vcols")
            layout.prop(self, "seam")
            layout.prop(self, "sharp")
            layout.prop(self, "materials")

    def execute(self, context):

        # noinspection PyTypeChecker
        obj = context.edit_object  # type: bpy.types.MeshObject
        if not obj or obj.type != "MESH":
            raise Exception("Active object must be a mesh in Edit Mode.")

        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)
        bm.faces.ensure_lookup_table()

        # Use the built-in `tag` attribute to mark faces as visited.
        for face in bm.faces:
            face.tag = False

        islands = []  # each island is a list of edge-linked `BMFace`s

        # Flood-fill: for each selected, unvisited face, collect all linked selected faces.
        for face in bm.faces:
            if not face.select or face.tag:
                continue  # ignore unselected or already tagged face

            # This face will be part of a new island.
            island = []
            queue = deque([face])
            while queue:
                current = queue.popleft()
                if current.tag:
                    continue
                current.tag = True
                island.append(current)
                # Check all faces sharing an edge with the current face.
                for edge in current.edges:
                    for linked in edge.link_faces:
                        if linked.select and not linked.tag:
                            queue.append(linked)
            islands.append(island)

        self.info(f"Found {len(islands)} connected islands of mesh faces.")

        # Process each group: select only that group and run convex hull operator.
        # (We’ll use the built-in operator bpy.ops.mesh.convex_hull.)
        for island in islands:
            self.deselect_all()

            # Select faces in this group.
            for face in island:
                face.select = True
            bmesh.update_edit_mesh(mesh)  # make sure the selection is updated

            # Run convex hull operator on the current selection.
            # This replaces the selected faces with a convex hull.
            bpy.ops.mesh.convex_hull(
                delete_unused=self.delete_unused,
                use_existing_faces=self.use_existing_faces,
                make_holes=self.make_holes,
                join_triangles=self.join_triangles,
                face_threshold=self.face_threshold,
                shape_threshold=self.shape_threshold,
                uvs=self.uvs,
                vcols=self.vcols,
                seam=self.seam,
                sharp=self.sharp,
                materials=self.materials,
            )

        self.deselect_all()
        bmesh.update_edit_mesh(mesh)
        self.info(f"Convex hulls generated for each of {islands} connected islands.")
        return {"FINISHED"}


class SetActiveFaceNormalUpward(LoggingOperator):

    bl_idname = "mesh.set_active_face_normal_upward"
    bl_label = "Set Active Face Normal Upward"
    bl_description = "Transform all selected vertices such that the active face's normal points upward (+Z)"

    @classmethod
    def poll(cls, context) -> bool:
        return context.mode == "EDIT_MESH" and context.edit_object.type == "MESH"

    def execute(self, context):

        # noinspection PyTypeChecker
        mesh = context.edit_object.data  # type: bpy.types.Mesh

        # We have to toggle out of Edit Mode to save the active face, then back in.
        bpy.ops.object.mode_set(mode="OBJECT")
        active_index = mesh.polygons.active
        if active_index < 0:
            return self.error("No active face detected. Please set an active face.")

        # Now go back to Edit Mode and create Bmesh.
        bpy.ops.object.mode_set(mode="EDIT")
        bm = bmesh.from_edit_mesh(mesh)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        active_face = bm.faces[active_index]

        # Compute the active face's centroid and normal (in local space).
        pivot = active_face.calc_center_median()
        face_normal = active_face.normal.copy()

        # Compute the rotation that aligns face_normal to +Z.
        target_normal = Vector((0, 0, 1))
        rotation_quat = face_normal.rotation_difference(target_normal)
        rotation_mat = rotation_quat.to_matrix()

        # Apply the rotation to all selected vertices, pivoting on the active face's centroid.
        for v in bm.verts:
            if v.select:
                v.co = pivot + rotation_mat @ (v.co - pivot)

        bmesh.update_edit_mesh(mesh)
        return {"FINISHED"}


class SpawnObjectIntoMeshAtFaces(LoggingOperator):

    bl_idname = "mesh.spawn_object_into_mesh_at_faces"
    bl_label = "Spawn Object Into Mesh at Faces"
    bl_description = (
        "Copies the active object's mesh into the edited mesh at each selected face, rotating its normal from +Z "
        "(assumed starting orientation) to the face's normal, with optional translation, rotation, and scaling "
        "relative to the face normal"
    )

    object_name: bpy.props.StringProperty(
        name="Object Name",
        description="Name of the object to spawn into the mesh. Must exist in Blender data",
        default="",
    )

    rotate_to_face_normal: bpy.props.BoolProperty(
        name="Rotate to Face Normal",
        description="Rotate the spawned object to align with the face normal (assuming it started pointing upward)",
        default=True,
    )

    translation_min: bpy.props.FloatProperty(
        name="Translation Min",
        description="Minimum translation distance along face normal (positive is away from face). Affected by scale",
        default=0.0,
    )
    translation_max: bpy.props.FloatProperty(
        name="Translation Max",
        description="Maximum translation distance along face normal (positive is away from face). Affected by scale",
        default=0.0,
    )

    rotation_min: bpy.props.FloatProperty(
        name="Rotation Min",
        description="Minimum rotation angle (in degrees) around face normal",
        default=0.0,
    )
    rotation_max: bpy.props.FloatProperty(
        name="Rotation Max",
        description="Maximum rotation angle (in degrees) around face normal",
        default=0.0,
    )

    scale_min: bpy.props.FloatProperty(
        name="Scale Min",
        description="Minimum scale factor (1.0 is no scaling)",
        default=1.0,
    )
    scale_max: bpy.props.FloatProperty(
        name="Scale Max",
        description="Maximum scale factor (1.0 is no scaling)",
        default=1.0,
    )

    @classmethod
    def poll(cls, context) -> bool:
        return context.mode == "EDIT_MESH" and context.edit_object.type == "MESH"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):

        source_obj = bpy.data.objects.get(self.object_name)  # type: bpy.types.MeshObject
        if source_obj is None:
            return self.error(f"Source object '{self.object_name}' not found.")
        if source_obj.type != 'MESH':
            return self.error(f"Source object '{self.object_name}' is not a Mesh.")

        # noinspection PyTypeChecker
        dest_obj = bpy.context.edit_object  # type: bpy.types.MeshObject
        if dest_obj is None or dest_obj.type != 'MESH':
            return self.error("Active object must be a mesh in Edit Mode.")

        dest_mesh = dest_obj.data
        bm = bmesh.from_edit_mesh(dest_mesh)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        # Store spawn data: for each selected face, record its centroid and normal.
        spawn_data = []
        for face in bm.faces:
            if face.select:
                spawn_data.append((face.calc_center_median(), face.normal.copy()))
        if not spawn_data:
            return self.error("No selected faces to spawn onto.")

        # Store original face count.
        orig_face_count = len(bm.faces)

        # Merge in the source mesh.
        bm.from_mesh(source_obj.data)  # merges into `bm`
        bm.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()

        # The newly merged source geometry is now appended.
        # noinspection PyTypeChecker
        source_faces = bm.faces[orig_face_count:]  # type: list[bmesh.types.BMFace]
        if not source_faces:
            raise Exception("No new faces were merged from the source.")

        # Compute the centroid of the merged source geometry once.
        temp_center = Vector((0, 0, 0))
        for f in source_faces:
            temp_center += f.calc_center_median()
        temp_center /= len(source_faces)

        # For each spawn location, duplicate the merged source geometry and transform it.
        for centroid, normal in spawn_data:
            dup_result = bmesh.ops.duplicate(bm, geom=source_faces)
            new_geom = dup_result["geom"]
            new_verts = [elem for elem in new_geom if isinstance(elem, bmesh.types.BMVert)]

            # Compute random rotation (in radians) and random scale factor.
            rand_slide = random.uniform(self.translation_min, self.translation_max)
            rand_angle = math.radians(random.uniform(self.rotation_min, self.rotation_max))
            rand_scale = random.uniform(self.scale_min, self.scale_max)
            rand_slide *= rand_scale  # scale affects translation

            # Build transformation matrices.
            # 1. T1: Translate source so that its center is at the origin.
            t_to_origin = Matrix.Translation(-temp_center)  # move source center to origin

            if self.rotate_to_face_normal:
                r_to_face = Vector((0, 0, 1)).rotation_difference(normal).to_matrix().to_4x4()  # align to face normal
            else:
                r_to_face = Matrix.Identity(4)  # don't align

            # Random rotation around face normal.
            r_random = Matrix.Rotation(rand_angle, 4, normal)
            # Random uniform scaling.
            s_random = Matrix.Scale(rand_scale, 4)
            # Translate source to face centroid.
            t_to_face = Matrix.Translation(centroid)
            # Random translation along face normal.
            t_random = Matrix.Translation(normal * rand_slide)

            # Compose the final transformation.
            transform = t_random @ t_to_face @ s_random @ r_random @ r_to_face @ t_to_origin

            for v in new_verts:
                v.co = transform @ v.co

        # Delete the original merged source geometry, which has now been duplicated to each face.
        bmesh.ops.delete(bm, geom=source_faces, context="VERTS")

        bmesh.update_edit_mesh(dest_mesh)
        self.info(f"Spawned {len(spawn_data)} copies of the source mesh.")
        return {"FINISHED"}


class WeightVerticesWithFalloff(LoggingOperator):

    bl_idname = "mesh.weight_vertices_with_falloff"
    bl_label = "Weight Vertices with Falloff"
    bl_description = (
        "Add all selected vertices in the active mesh to the given vertex group with weight 1, then progressively "
        "expand the selection by the given number of steps and add those vertices with linearly decreasing weight, "
        "down to zero. Useful for Displace modifiers with gradual falloff"
    )

    vertex_group: bpy.props.StringProperty(
        name="Vertex Group",
        description="Name of the vertex group to add vertices to. Must already exist in Mesh",
        default="",
    )

    steps: bpy.props.IntProperty(
        name="Steps",
        description="Number of selection expansion steps to linearly decrease weight. A value of 1, for example, "
                    "means that one expanded ring of vertices will be weighted at 0.5",
        default=5,
        min=1,
    )

    @classmethod
    def poll(cls, context) -> bool:
        return context.mode == "EDIT_MESH" and context.edit_object.type == "MESH"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):

        # noinspection PyTypeChecker
        obj = context.edit_object  # type: bpy.types.MeshObject

        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)
        bm.verts.ensure_lookup_table()

        # Get the vertex group (must already exist).
        vg = obj.vertex_groups.get(self.vertex_group)
        if vg is None:
            return self.error(f"Vertex group '{self.vertex_group}' not found in Mesh '{obj.name}'.")

        # Start with the currently selected vertices.
        initial_verts = set(v.index for v in bm.verts if v.select)
        if not initial_verts:
            return self.error("No vertices are selected.")

        # Mark visited vertices using a set of vertex indices.
        visited = set(initial_verts)

        # Assign weight 1.0 to the initial (selected) vertices.
        for idx in initial_verts:
            vg.add([idx], 1.0, 'REPLACE')

        # The current "ring" is the set of vertices we just processed.
        current_ring = initial_verts

        # For each step, find neighbors not yet visited. The weight for the final step is `1 / num_steps`.
        falloff = 1.0 / (self.steps + 1)
        for step in range(1, self.steps + 1):
            new_ring = set()
            for vertex_idx in current_ring:
                v = bm.verts[vertex_idx]
                # For each edge connected to v, check the other vertex.
                for edge in v.link_edges:
                    for other in edge.verts:
                        if other.index not in visited:
                            new_ring.add(other.index)
            weight = 1.0 - step * falloff
            # Assign that weight to all vertices in this new ring.
            for idx in new_ring:
                vg.add([idx], weight, 'REPLACE')
            # Update visited and current_ring for the next iteration.
            visited.update(new_ring)
            current_ring = new_ring

        # Update the mesh.
        bmesh.update_edit_mesh(mesh)
        self.info(f"Vertex group '{self.vertex_group}' updated with falloff weights over {self.steps} steps.")
        return {"FINISHED"}


class ApplyModifierNonSingleUser(LoggingOperator):

    bl_idname = "mesh.apply_modifier_non_single_user"
    bl_label = "Apply Modifier (To All Users)"
    bl_description = ("Apply the active modifier to the active mesh, even if it is used by multiple objects, without "
                      "forcing the Mesh data to become single-user as Blender normally does")

    @classmethod
    def poll(cls, context) -> bool:
        return (
            context.mode == "OBJECT"
            and context.active_object
            and context.active_object.type == "MESH"
            and len(context.active_object.modifiers) >= 1
            and context.active_object.modifiers.active
        )

    def invoke(self, context, event):
        """Confirm type and name of active modifier to be applied."""
        modifier = context.active_object.modifiers.active
        return context.window_manager.invoke_confirm(
            self, event,
            title="Confirm Modifier",
            message=f"Apply {modifier.type} modifier '{modifier.name}' to active mesh?",
        )

    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.active_object  # type: bpy.types.MeshObject
        modifier_name = obj.modifiers.active.name

        original_data = obj.data
        try:
            bpy.ops.object.modifier_apply(modifier=modifier_name, single_user=True)
        except Exception as ex:
            return self.error(f"Failed to apply modifier '{modifier_name}': {ex}")

        new_data = obj.data

        bm = bmesh.new()
        try:
            bm.from_mesh(new_data)
            bm.to_mesh(original_data)
        except Exception as ex:
            return self.error(f"Failed to copy new data to original data: {ex}")
        finally:
            bm.free()

        obj.data = original_data
        bpy.data.meshes.remove(new_data, do_unlink=True)

        self.info(f"Applied modifier '{modifier_name}' to mesh '{obj.name}' without forcing single user.")

        return {"FINISHED"}
