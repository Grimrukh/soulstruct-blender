from __future__ import annotations

__all__ = [
    "NavmeshFaceSettings",
    "RefreshFaceIndices",
    "AddNVMFaceFlags",
    "RemoveNVMFaceFlags",
    "SetNVMFaceObstacleCount",
    "ResetNVMFaceInfo",
    "NavmeshComputeSettings",
    "FindCheapestPath",
    "RecomputeEdgeCost",
    "AutoCreateMCG",
]

import bmesh
import bpy
from mathutils import Vector

from soulstruct.darksouls1r.events.enums import NavmeshFlag

from io_soulstruct.utilities import LoggingOperator
from .utilities import set_face_material, a_star

# Get all non-default `NavmeshFlag` values for Blender `EnumProperty`.
_navmesh_flag_items = [
    (str(flag.value), flag.name, "") for flag in NavmeshFlag
    if flag.value > 0
]


class NavmeshFaceSettings(bpy.types.PropertyGroup):

    flag_type: bpy.props.EnumProperty(
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
    def poll(cls, context):
        return context.edit_object is not None and context.mode == "EDIT_MESH"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.edit_object
        if obj is None or obj.type != "MESH":
            return {"CANCELLED"}

        obj: bpy.types.MeshObject
        bm = bmesh.from_edit_mesh(obj.data)

        props = context.scene.navmesh_face_settings  # type: NavmeshFaceSettings

        flags_layer = bm.faces.layers.int.get("nvm_face_flags")
        if flags_layer:
            selected_faces = [face for face in bm.faces if face.select]
            for face in selected_faces:
                face[flags_layer] |= int(props.flag_type)
                set_face_material(bl_mesh=obj.data, bl_face=face, face_flags=face[flags_layer])

            bmesh.update_edit_mesh(obj.data)

        # TODO: Would be nice to remove now-unused materials from the mesh.

        return {"FINISHED"}


class RemoveNVMFaceFlags(LoggingOperator):
    bl_idname = "mesh.remove_nvm_face_flags"
    bl_label = "Remove NVM Face Flags"
    bl_description = "Remove the selected NavmeshFlag bit flag from all selected faces"

    @classmethod
    def poll(cls, context):
        return context.edit_object is not None and context.mode == "EDIT_MESH"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.edit_object
        if obj is None or obj.type != "MESH":
            return {"CANCELLED"}

        obj: bpy.types.MeshObject
        bm = bmesh.from_edit_mesh(obj.data)

        props = context.scene.navmesh_face_settings  # type: NavmeshFaceSettings

        flags_layer = bm.faces.layers.int.get("nvm_face_flags")
        if flags_layer:
            selected_faces = [face for face in bm.faces if face.select]
            for face in selected_faces:
                face[flags_layer] &= ~int(props.flag_type)
                set_face_material(bl_mesh=obj.data, bl_face=face, face_flags=face[flags_layer])

            bmesh.update_edit_mesh(obj.data)

        # TODO: Would be nice to remove now-unused materials from the mesh.

        return {"FINISHED"}


class SetNVMFaceObstacleCount(LoggingOperator):
    bl_idname = "mesh.set_nvm_face_obstacle_count"
    bl_label = "Set NVM Face Obstacle Count"
    bl_description = "Set the obstacle count for all selected faces"

    @classmethod
    def poll(cls, context):
        return context.edit_object is not None and context.mode == "EDIT_MESH"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.edit_object
        if obj is None or obj.type != "MESH":
            return {"CANCELLED"}

        obj: bpy.types.MeshObject
        bm = bmesh.from_edit_mesh(obj.data)

        props = context.scene.navmesh_face_settings  # type: NavmeshFaceSettings

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
    def poll(cls, context):
        return context.edit_object is not None and context.mode == "EDIT_MESH"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.edit_object
        if obj is None or obj.type != "MESH":
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

        for f_i, face in enumerate(bm.faces):
            face[flags_layer] = self.DEFAULT_FLAGS
            face[obstacle_count_layer] = self.DEFAULT_OBSTACLE_COUNT

        bmesh.update_edit_mesh(obj.data)

        return {"FINISHED"}


class NavmeshComputeSettings(bpy.types.PropertyGroup):

    select_path: bpy.props.BoolProperty(
        name="Select Path",
        default=True,
        description="Select the path of faces found by the pathfinding algorithm"
    )

    wall_multiplier: bpy.props.FloatProperty(
        name="Wall Cost Multiplier",
        default=1.0,
        description="Cost multiplier (of distance) for Wall faces",
    )
    obstacle_multiplier: bpy.props.FloatProperty(
        name="Obstacle Cost Multiplier",
        default=1.0,
        description="Cost multiplier (of distance) for Obstacle faces. Ignores obstacle count",
    )


class FindCheapestPath(LoggingOperator):
    """Uses A* to find the cheapest path between two selected faces on a navmesh.

    Can be used on arbitrary meshes, in which case the cost of moving between faces is the distance between their
    centroids. This is also generally the case for navmeshes, but some flags modify cost.
    """
    bl_idname = "mesh.find_cheapest_path"
    bl_label = "Find Cheapest Path"
    bl_description = ("Find and select the cheapest path between two selected faces on a navmesh. Total cost of path "
                      "will be logged to the console")

    @classmethod
    def poll(cls, context):
        """NOTE: Two faces must be selected, but would need to create a BMesh to check this."""
        return (
            context.edit_object is not None
            and context.mode == "EDIT_MESH"
        )

    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            return self.error("No active edit mesh object.")
        obj: bpy.types.MeshObject

        bm = bmesh.from_edit_mesh(obj.data)

        selected_faces = [f for f in bm.faces if f.select]
        if len(selected_faces) != 2:
            return self.error("Select exactly two faces on edit mesh.")
        active_face = bm.faces.active
        if active_face not in selected_faces:
            return self.error("Active face must be one of the selected faces.")
        start_face, end_face = selected_faces
        if start_face == active_face:
            start_face, end_face = end_face, start_face

        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)

        path, total_cost, all_passable_fallback = a_star(start_face, end_face, bm)

        if path:
            if all_passable_fallback:
                self.info(
                    f"No path found with face flags, but when allowed to traverse all faces, shortest path traverses "
                    f"{len(path)} faces with cost: {total_cost}"
                )
            else:
                self.info(
                    f"Shortest path through passable face flags traverses {len(path)} faces with cost: {total_cost}"
                )
            if context.scene.navmesh_compute_settings.select_path:
                for face in path:
                    face.select_set(True)
        else:
            self.info("No path found between selected faces, even when all faces are passable.")

        bmesh.update_edit_mesh(obj.data)

        return {"FINISHED"}


class RecomputeEdgeCost(LoggingOperator):
    """Compute the expected cost of moving from the given edge's start node (lowest face index) to its end node (also
    lowest face index).

    Result is stored in "Blender Cost" custom property on edge, which the cost label draw hook will check and display
    alongside the true loaded MCG costs. The `UpdateEdgeCost` operator can be used to override "Cost" with "Blender
    Cost" and delete the latter property, causing the new cost to be exported to MCG edges (rather than just being for
    comparison).
    """
    bl_idname = "mesh.recompute_mcg_edge_cost"
    bl_label = "Recompute Edge Costs"
    bl_description = "Recompute costs of selected MCG edges and store in \"Blender Cost\" custom property"

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "OBJECT"
            and len(context.selected_objects) >= 1
            and (
                (len(context.selected_objects) == 1 and context.selected_objects[0].name.endswith(" Edges"))
                or all(obj.type == "EMPTY" and " Edge " in obj.name for obj in context.selected_objects)
            )
        )

    def execute(self, context):

        if len(context.selected_objects) == 1 and context.selected_objects[0].name.endswith(" Edges"):
            edges = context.selected_objects[0].children
            map_stem = context.selected_objects[0].name.split(" ")[0]
        else:
            edges = context.selected_objects
            map_stem = context.selected_objects[0].name.split(" ")[0]

        try:
            node_parent = bpy.data.objects[f"{map_stem} Nodes"]
        except KeyError:
            return self.error(f"No node parent found for map stem '{map_stem}'.")

        nodes = {
            obj.name.split("<")[0].strip(): obj
            for obj in node_parent.children
        }

        for edge in edges:

            edge_stem = edge.name.split(" ")[0]
            if edge_stem != map_stem:
                self.warning(
                    f"Selected edges must belong to a single map stem (first stem: {map_stem}). "
                    f"Ignoring '{edge.name}'.")
                continue

            try:
                navmesh = bpy.data.objects[edge["Navmesh Name"]]
            except KeyError:
                continue  # can't draw

            try:
                node_a = nodes[edge["Node A"]]
                node_b = nodes[edge["Node B"]]
            except KeyError:
                self.warning(f"Node(s) not found for edge '{edge.name}'. Ignoring.")
                continue

            if node_a["Navmesh A Name"] == navmesh.name:
                node_a_triangles = node_a["Navmesh A Triangles"]
            elif node_a["Navmesh B Name"] == navmesh.name:
                node_a_triangles = node_a["Navmesh B Triangles"]
            else:
                self.warning(
                    f"Node A '{node_a.name}' does not reference navmesh '{navmesh.name}'. Ignoring edge '{edge.name}'."
                )
                continue

            if node_b["Navmesh A Name"] == navmesh.name:
                node_b_triangles = node_b["Navmesh A Triangles"]
            elif node_b["Navmesh B Name"] == navmesh.name:
                node_b_triangles = node_b["Navmesh B Triangles"]
            else:
                self.warning(
                    f"Node B '{node_b.name}' does not reference navmesh '{navmesh.name}'. Ignoring edge '{edge.name}'."
                )
                continue

            start_face_i = min(node_a_triangles)
            end_face_i = min(node_b_triangles)

            total_cost = self.get_best_cost(navmesh, start_face_i, end_face_i)
            if total_cost == 0.0:
                self.warning(f"No path found in either direction between nodes for edge '{edge.name}'.")
                continue

            edge["Blender Cost"] = total_cost

        return {"FINISHED"}

    @staticmethod
    def get_best_cost(navmesh: bpy.types.MeshObject, start_face_i: int, end_face_i: int):

        # We calculate cost in both directions and use the cheaper one.
        forward_path, forward_cost, forward_all_passable = RecomputeEdgeCost.get_edge_cost(
            navmesh, start_face_i, end_face_i
        )
        backward_path, backward_cost, backward_all_passable = RecomputeEdgeCost.get_edge_cost(
            navmesh, end_face_i, start_face_i
        )

        if not forward_path and not backward_path:
            return 0.0

        if forward_all_passable == backward_all_passable:
            return min(forward_cost, backward_cost)
        elif not forward_all_passable:
            # Use forward cost, as it didn't fall back to distance as cost.
            return forward_cost
        else:  # not backward_is_distance
            return backward_cost

    @staticmethod
    def get_edge_cost(navmesh: bpy.types.MeshObject, start_face_i: int, end_face_i: int) -> tuple[list, float, bool]:
        bm = bmesh.new()
        bm.from_mesh(navmesh.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
        bm.faces.ensure_lookup_table()
        start_face = bm.faces[start_face_i]
        end_face = bm.faces[end_face_i]
        try:
            return a_star(start_face, end_face, bm)
        finally:
            bm.free()
            del bm


class AutoCreateMCG(LoggingOperator):
    """Create a full MCG structure from scratch but detecting node placements (adjoining 'Exit' faces) and computing
    edge costs between all pairs of nodes in each navmesh.

    EXPERIMENTAL! Edge cost algorithm is not yet perfect, especially when Wall drops are involved. Some connections in
    vanilla MCG edges also seem to be manually inflated, presumably to avoid certain paths. However, I doubt this will
    matter in-game.
    """
    bl_idname = "mesh.auto_create_mcg"
    bl_label = "Auto Create Full MCG"
    bl_description = "Create an entire MCG hierarchy of nodes/edges using all navmesh 'Exit' faces"

    navmesh_bmeshes: list[bmesh.types.BMesh]

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "OBJECT"
            and context.collection is not None
            and context.collection.name.endswith(" MSB Navmeshes (*)")
        )

    def execute(self, context):

        self.navmesh_bmeshes = []
        try:
            return self._execute(context)
        except Exception as ex:
            return self.error(f"An error occurred during MCG creation: {ex}")
        finally:
            for bm in self.navmesh_bmeshes:
                bm.free()
                del bm

    def _execute(self, context):

        map_stem = context.collection.name.split(" ")[0]

        navmesh_parts = [
            obj for obj in context.collection.objects if obj.name.startswith("n")
        ]  # type: list[bpy.types.MeshObject]

        # Storing navmesh BMeshes.

        navmesh_exit_clusters = []

        for navmesh in navmesh_parts:
            bm = bmesh.new()
            bm.from_mesh(navmesh.data)
            # We do NOT remove doubles here, as it could modify face indices.
            bm.faces.ensure_lookup_table()  # face indices won't change again
            self.navmesh_bmeshes.append(bm)
            flags_layer = bm.faces.layers.int.get("nvm_face_flags")
            if flags_layer is None:
                self.warning(f"Navmesh '{navmesh.name}' has no 'nvm_face_flags' layer. Ignoring it for MCG creation.")
                continue

            # First, find all clusters of connected 'Exit' faces in each navmesh.
            exit_clusters = []
            checked = []

            for face in bm.faces:

                if face in checked:
                    continue
                checked.append(face)

                if face[flags_layer] & NavmeshFlag.Exit:
                    # Find all connected 'Exit' faces.
                    cluster = []  # type: list[tuple[bmesh.types.BMFace, frozenset[tuple[float, ...]]]]
                    stack = [face]
                    while stack:
                        f = stack.pop()
                        if f in cluster:
                            continue

                        verts = frozenset(tuple(v.co + navmesh.location) for v in f.verts)
                        cluster.append((f, verts))
                        for edge in f.edges:
                            for other_face in edge.link_faces:
                                if other_face in checked:
                                    continue
                                checked.append(other_face)  # cannot possibly already be checked
                                if other_face not in cluster and other_face[flags_layer] & NavmeshFlag.Exit:
                                    stack.append(other_face)
                    exit_clusters.append(tuple(cluster))

            navmesh_exit_clusters.append(tuple(exit_clusters))
            self.info(f"Found {len(exit_clusters)} exit clusters for navmesh {navmesh.name}.")

        self.info("Found all exit clusters.")

        # Now find connected exit clusters across navmeshes.
        all_nodes = {}  # type: dict[tuple[tuple[int, ...], tuple[int, ...]], bpy.types.Object]
        # List of node objects stored for each navmesh part, along with ordered navmesh model IDs.
        navmesh_nodes = [[] for _ in navmesh_parts]  # type: list[list[tuple[bpy.types.Object, tuple[int, int]]]]

        navmesh_pair_node_counts = {}

        def sq_dist(v1, v2):
            return sum((v1[_i] - v2[_i]) ** 2 for _i in range(3))
        sq_dist_threshold = 0.01 ** 2

        # Create parent empties.
        mcg_parent = bpy.data.objects.new(f"{map_stem} MCG", None)
        node_parent = bpy.data.objects.new(f"{map_stem} Nodes", None)
        edge_parent = bpy.data.objects.new(f"{map_stem} Edges", None)
        node_parent.parent = mcg_parent
        edge_parent.parent = mcg_parent
        context.scene.collection.objects.link(mcg_parent)
        context.scene.collection.objects.link(node_parent)
        context.scene.collection.objects.link(edge_parent)

        for i, (navmesh, exit_clusters) in enumerate(zip(navmesh_parts, navmesh_exit_clusters)):
            navmesh_model_id = int(navmesh.name[1:5])  # for sorting
            self.info(f"Finding exit connections for navmesh {navmesh.name}...")
            for cluster in exit_clusters:
                for face, face_verts in cluster:

                    for j, (other_navmesh, other_exit_clusters) in enumerate(zip(navmesh_parts, navmesh_exit_clusters)):
                        if other_navmesh is navmesh:
                            continue

                        other_navmesh_id = int(other_navmesh.name[1:5])

                        for other_cluster in other_exit_clusters:
                            if navmesh_model_id < other_navmesh_id:
                                node_key = (cluster, other_cluster)
                                model_pair_key = (navmesh_model_id, other_navmesh_id)
                            else:
                                node_key = (other_cluster, cluster)
                                model_pair_key = (other_navmesh_id, navmesh_model_id)

                            if node_key in all_nodes:
                                # Already created this node.
                                continue

                            for other_face, other_face_verts in other_cluster:
                                # Check if faces are connected by an edge.
                                # As vertices may not be completely identical, this is unfortunately a bit slow.
                                hits = 0
                                for v in face_verts:
                                    for ov in other_face_verts:
                                        if sq_dist(v, ov) < sq_dist_threshold:
                                            hits += 1
                                            if hits >= 2:
                                                break
                                    else:
                                        continue
                                    break

                                if hits < 2:
                                    # No shared edge.
                                    continue

                                # Found a touching cluster.
                                instance_index = navmesh_pair_node_counts.get(model_pair_key, 0)
                                navmesh_pair_node_counts[model_pair_key] = instance_index + 1

                                # Node position is average of all vertices in both clusters.
                                node_position = Vector()
                                v_count = 0
                                for _, f_verts in cluster:
                                    for v in f_verts:
                                        node_position += Vector(v)
                                        v_count += 1
                                for _, f_verts in other_cluster:
                                    for v in f_verts:
                                        node_position += Vector(v)
                                        v_count += 1
                                node_position /= v_count

                                node_name = f"{map_stem} Node [{navmesh_model_id} | {other_navmesh_id}]"
                                if instance_index >= 1:
                                    node_name += f" ({instance_index})"  # <DEAD END> suffix may be added below
                                node = bpy.data.objects.new(node_name, None)
                                node.location = node_position
                                node.empty_display_type = "SPHERE"
                                node.parent = node_parent
                                context.scene.collection.objects.link(node)

                                if navmesh_model_id < other_navmesh_id:
                                    node["Navmesh A Name"] = navmesh.name
                                    node["Navmesh A Triangles"] = [f.index for f, _ in cluster]
                                    node["Navmesh B Name"] = other_navmesh.name
                                    node["Navmesh B Triangles"] = [f.index for f, _ in other_cluster]
                                else:
                                    node["Navmesh A Name"] = other_navmesh.name
                                    node["Navmesh A Triangles"] = [f.index for f, _ in other_cluster]
                                    node["Navmesh B Name"] = navmesh.name
                                    node["Navmesh B Triangles"] = [f.index for f, _ in cluster]

                                all_nodes[node_key] = node
                                navmesh_nodes[i].append((node, model_pair_key))
                                navmesh_nodes[j].append((node, model_pair_key))

        # Create edges.
        all_edges = []  # all MCG edges
        for navmesh, nodes in zip(navmesh_parts, navmesh_nodes):
            created = set()

            if len(nodes) == 1:
                # Dead end navmesh with a single node.
                node = nodes[0][0]
                if node.name.endswith(" <DEAD END>"):
                    # ERROR: Node cannot straddle two dead ends.
                    return self.error(f"Node {node.name} has two dead end navmeshes. Cannot create MCG.")
                node.name += " <DEAD END>"
                continue  # no edges to create

            for i, (node_a, (a_navmesh_a, a_navmesh_b)) in enumerate(nodes):
                for j, (node_b, (b_navmesh_a, b_navmesh_b)) in enumerate(nodes):
                    if i == j or (i, j) in created or (j, i) in created:
                        continue

                    if node_a["Navmesh A Name"] == navmesh.name:
                        start_face_i = min(node_a["Navmesh A Triangles"])
                    else:
                        start_face_i = min(node_a["Navmesh B Triangles"])
                    if node_b["Navmesh A Name"] == navmesh.name:
                        end_face_i = min(node_b["Navmesh A Triangles"])
                    else:
                        end_face_i = min(node_b["Navmesh B Triangles"])

                    # Note that this creates its own `BMesh` that removes vertex doubles.
                    total_cost = RecomputeEdgeCost.get_best_cost(navmesh, start_face_i, end_face_i)
                    if total_cost == 0.0:
                        total_cost = 10000.0  # arbitrary error catch

                    edge_name = (
                        f"{map_stem} Edge ([{a_navmesh_a} | {a_navmesh_b}] "
                        f"-> [{b_navmesh_a} | {b_navmesh_b}]) <{navmesh.name}>"
                    )
                    edge = bpy.data.objects.new(edge_name, None)
                    edge.parent = edge_parent
                    context.scene.collection.objects.link(edge)
                    start = node_a.location
                    end = node_b.location
                    direction = end - start
                    midpoint = (start + end) / 2.0
                    edge.empty_display_type = "PLAIN_AXES"
                    edge.location = midpoint
                    # Point empty arrow in direction of edge.
                    edge.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()

                    edge["Cost"] = total_cost
                    edge["Navmesh Name"] = navmesh.name
                    edge["Node A"] = node_a.name
                    edge["Node B"] = node_b.name
                    all_edges.append(edge)
                    created.add((i, j))

        # Since we succeeded, set MCG parent draw name.
        context.scene.mcg_draw_settings.mcg_parent_name = mcg_parent.name
        return {"FINISHED"}
