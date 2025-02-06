from __future__ import annotations

__all__ = [
    "AddMCGNodeNavmeshATriangleIndex",
    "RemoveMCGNodeNavmeshATriangleIndex",
    "AddMCGNodeNavmeshBTriangleIndex",
    "RemoveMCGNodeNavmeshBTriangleIndex",

    "JoinMCGNodesThroughNavmesh",
    "SetNodeNavmeshTriangles",
    "RefreshMCGNames",
    "RecomputeEdgeCost",
    "FindCheapestPath",
    "AutoCreateMCG",
]

import typing as tp

import bmesh
import bpy
from mathutils import Vector

from soulstruct.base.events.enums import NavmeshFlag

from io_soulstruct.exceptions import SoulstructTypeError, MCGEdgeCreationError
from io_soulstruct.msb.darksouls1r import BlenderMSBNavmesh
from io_soulstruct.types import *
from io_soulstruct.utilities import LoggingOperator
from .utilities import *
from .types import *


class AddMCGNodeNavmeshATriangleIndex(bpy.types.Operator):
    bl_idname = "mcg_node.add_navmesh_a_triangle_index"
    bl_label = "Add Navmesh A Triangle"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object and context.active_object.soulstruct_type == SoulstructType.MCG_NODE

    def execute(self, context):
        bl_node = context.active_object
        bl_node.MCG_NODE.navmesh_a_triangles.add()
        return {'FINISHED'}


class RemoveMCGNodeNavmeshATriangleIndex(bpy.types.Operator):
    bl_idname = "mcg_node.remove_navmesh_a_triangle_index"
    bl_label = "Remove Navmesh A Triangle"

    @classmethod
    def poll(cls, context) -> bool:
        return (
            context.active_object
            and context.active_object.soulstruct_type == SoulstructType.MCG_NODE
            and len(context.active_object.MCG_NODE.navmesh_a_triangles) > 0
        )

    def execute(self, context):
        obj = context.active_object
        index = obj.MCG_NODE.navmesh_a_triangle_index
        obj.MCG_NODE.navmesh_a_triangles.remove(index)
        obj.MCG_NODE.navmesh_a_triangle_index = max(0, index - 1)
        return {'FINISHED'}


class AddMCGNodeNavmeshBTriangleIndex(bpy.types.Operator):
    bl_idname = "mcg_node.add_navmesh_b_triangle_index"
    bl_label = "Add Navmesh B Triangle"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object and context.active_object.soulstruct_type == SoulstructType.MCG_NODE

    def execute(self, context):
        bl_node = context.active_object
        bl_node.MCG_NODE.navmesh_b_triangles.add()
        return {'FINISHED'}


class RemoveMCGNodeNavmeshBTriangleIndex(bpy.types.Operator):
    bl_idname = "mcg_node.remove_navmesh_b_triangle_index"
    bl_label = "Remove Navmesh B Triangle"

    @classmethod
    def poll(cls, context) -> bool:
        return (
            context.active_object
            and context.active_object.soulstruct_type == SoulstructType.MCG_NODE
            and len(context.active_object.MCG_NODE.navmesh_b_triangles) > 0
        )

    def execute(self, context):
        obj = context.active_object
        index = obj.MCG_NODE.navmesh_b_triangle_index
        obj.MCG_NODE.navmesh_b_triangles.remove(index)
        obj.MCG_NODE.navmesh_b_triangle_index = max(0, index - 1)
        return {'FINISHED'}


class JoinMCGNodesThroughNavmesh(LoggingOperator):
    """Create an MCG edge between two nodes on a navmesh."""
    bl_idname = "io_soulstruct_scene.join_mcg_nodes"
    bl_label = "Join Nodes Through Navmesh"
    bl_description = ("Create an MCG edge between two selected MCG nodes on the selected navmesh. Same MCG root object "
                      "must be selected for drawing")

    @classmethod
    def poll(cls, context) -> bool:
        return (
            context.mode == "OBJECT"
            and len(context.selected_objects) == 3
            and bpy.context.scene.mcg_draw_settings.mcg_parent is not None
        )

    def execute(self, context):

        try:
            self.create_mcg_edge(context)
        except Exception as ex:
            return self.error(str(ex))

        return {"FINISHED"}

    @staticmethod
    def create_mcg_edge(context):
        if context.scene.mcg_draw_settings.mcg_parent is None:
            raise MCGEdgeCreationError("No MCG parent object specified.")

        try:
            bl_mcg = BlenderMCG(context.scene.mcg_draw_settings.mcg_parent)
        except ValueError:
            raise MCGEdgeCreationError("Selected MCG parent object is not a valid MCG object.")

        try:
            node_a, node_b = [obj for obj in context.selected_objects if obj.soulstruct_type == SoulstructType.MCG_NODE]
        except ValueError:
            raise MCGEdgeCreationError("Must select exactly two MCG Nodes.")

        navmesh_parts = [
            obj for obj in context.selected_objects
            if obj.soulstruct_type == SoulstructType.MSB_PART
            and obj.MSB_PART.part_subtype == "Navmesh"
        ]
        if len(navmesh_parts) > 1 or not navmesh_parts:
            raise MCGEdgeCreationError("Must select exactly one MSB Navmesh part")
        bl_navmesh = navmesh_parts[0]

        try:
            nav_id = int(bl_navmesh.name[1:5])
        except ValueError:
            raise MCGEdgeCreationError("Navmesh name must start with 'n####'.")

        # Check these nodes are not already connected.
        nav_index = 0
        for bl_edge in bl_mcg.get_edges():
            if bl_edge.navmesh_part == bl_navmesh:
                nav_index += 1
            if bl_edge.node_a == node_a and bl_edge.node_b == node_b:
                raise MCGEdgeCreationError(f"Nodes '{node_a.name}' and '{node_b.name}' are already connected.")
            if bl_edge.node_a == node_b and bl_edge.node_b == node_a:
                raise MCGEdgeCreationError(f"Nodes '{node_b.name}' and '{node_a.name}' are already connected.")

        map_stem = bl_mcg.tight_name
        edge_name = f"{map_stem} Edge [{nav_id}] ({nav_index})"

        start = node_a.location
        end = node_b.location
        length = (end - start).length
        direction = end - start
        midpoint = (start + end) / 2.0

        bl_edge = BlenderMCGEdge.new(edge_name, data=None)
        bl_edge.obj.empty_display_type = "PLAIN_AXES"
        bl_edge.obj.location = midpoint
        bl_edge.obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
        bl_edge.obj.parent = bl_mcg.edge_parent

        # Add edge to same collection(s) as parent.
        for collection in bl_mcg.obj.users_collection:
            collection.objects.link(bl_edge.obj)
        if not bl_mcg.obj.users_collection:
            # Add to context collection if parent has no collections.
            context.scene.collection.objects.link(bl_edge)

        # Initial cost is twice the distance between the nodes.
        bl_edge.cost = 2 * length
        bl_edge.navmesh_part = bl_navmesh
        bl_edge.node_a = node_a
        bl_edge.node_b = node_b


class SetNodeNavmeshTriangles(LoggingOperator):
    bl_idname = "io_soulstruct_scene.set_node_navmesh_triangles"
    bl_label = "Set Node Navmesh Triangles"
    bl_description = ("Use edited mesh to set the navmesh triangle indices of Navmesh A/B on selected MCG node. Must "
                      "be editing an MSB Navmesh part mesh that is already set as Navmesh A or B for selected node")

    @classmethod
    def poll(cls, context) -> bool:
        if context.mode != "EDIT_MESH" or not context.edit_object:
            return False
        # Have to account for the edited Mesh itself maybe not being selected. (We don't care.)
        if not context.selected_objects or len(context.selected_objects) > 2:
            return False
        return context.selected_objects[0].soulstruct_type == SoulstructType.MCG_NODE

    def execute(self, context):

        bm = None
        try:
            bl_node = BlenderMCGNode(context.selected_objects[0])
            # noinspection PyTypeChecker
            mesh = context.edit_object  # type: bpy.types.MeshObject
            if mesh is not bl_node.navmesh_a and mesh is not bl_node.navmesh_b:
                return self.error("Edited mesh must be the Navmesh A or B mesh for the selected MCG node.")
            bm = bmesh.from_edit_mesh(mesh.data)
            if mesh is bl_node.navmesh_a:
                bl_node.navmesh_a_triangles = [f.index for f in bm.faces if f.select]
            elif mesh is bl_node.navmesh_b:
                bl_node.navmesh_b_triangles = [f.index for f in bm.faces if f.select]
        except Exception as ex:
            return self.error(str(ex))
        finally:
            if bm:
                bm.free()
                del bm

        return {"FINISHED"}


class RefreshMCGNames(LoggingOperator):
    bl_idname = "scene.refresh_mcg_names"
    bl_label = "Refresh MCG Names"
    bl_description = "Refresh all MCG node and edge names in the selected MCG hierarchy"

    @classmethod
    def poll(cls, context) -> bool:
        try:
            BlenderMCG.from_active_object(context)
        except SoulstructTypeError:
            return False
        return True

    def execute(self, context):

        bl_mcg = BlenderMCG.from_active_object(context)
        map_stem = bl_mcg.tight_name

        bl_nodes = bl_mcg.get_nodes()
        bl_edges = bl_mcg.get_edges()

        new_node_indices = {}
        for node in bl_nodes:

            try:
                a_id = int(node.navmesh_a.name[1:5])
            except ValueError:
                return self.error(
                    f"Node '{node.name}' must reference a navmesh name starting with 'n####'."
                )
            try:
                b_id = int(node.navmesh_b.name[1:5])
            except ValueError:
                return self.error(
                    f"Node '{node.name}' must reference a navmesh name starting with 'n####'."
                )
            key_indices = (b_id, a_id) if a_id > b_id else (a_id, b_id)
            new_node_indices[node.name] = key_indices

        edge_navmesh_indices = {}
        for edge in bl_edges:
            try:
                nav_id = int(edge.navmesh_part.name[1:5])
            except ValueError:
                return self.error(
                    f"Edge '{edge.name}' must reference a navmesh name starting with 'n####'."
                )
            edge_navmesh_indices[edge.name] = nav_id

        navmesh_nodes = {}  # type: dict[tuple[int, int], list[BlenderMCGNode]]  # tracks nodes connecting same NVMs
        for node in bl_nodes:
            key_indices = new_node_indices[node.name]
            a_id, b_id = key_indices
            if key_indices in navmesh_nodes:
                # NOT first instance.
                index = len(navmesh_nodes[key_indices])
                if len(navmesh_nodes[key_indices]) == 1:
                    # Back-index first.
                    navmesh_nodes[key_indices][0].name += " (0)"
                node.name = f"{map_stem} Node [{a_id} | {b_id}] ({index})"
                navmesh_nodes[key_indices].append(node)
            else:
                node.name = f"{map_stem} Node [{a_id} | {b_id}]"  # assume no index needed yet
                navmesh_nodes[key_indices] = [node]

        # Update edge names.
        navmesh_edges = {}  # type: dict[int, list[BlenderMCGEdge]]  # tracks edges in same navmesh
        for edge in bl_edges:
            nav_index = edge_navmesh_indices[edge.name]
            navmesh_edge_count = len(navmesh_edges.setdefault(nav_index, []))
            edge.name = f"{map_stem} Edge [{nav_index}] ({navmesh_edge_count})"
            navmesh_edges[nav_index].append(edge)

        return {"FINISHED"}


class RecomputeEdgeCost(LoggingOperator):
    """Compute the expected cost of moving from the given edge's start node (lowest face index) to its end node (also
    lowest face index).

    Result is stored in "New Cost" custom property on edge, which the cost label draw hook will check and display
    alongside the true loaded MCG costs. The `UpdateEdgeCost` operator can be used to override "Cost" with "Blender
    Cost" and delete the latter property, causing the new cost to be exported to MCG edges (rather than just being for
    comparison).
    """
    bl_idname = "mesh.recompute_mcg_edge_cost"
    bl_label = "Recompute Edge Costs"
    bl_description = "Recompute costs of selected MCG edges and store in \"New Cost\" custom property"

    @classmethod
    def poll(cls, context) -> bool:
        if not context.mode == "OBJECT":
            return False
        try:
            BlenderMCGEdge.from_selected_objects(context)
        except SoulstructTypeError:
            return False
        return True

    def execute(self, context):

        bl_edges = BlenderMCGEdge.from_selected_objects(context)  # type: list[BlenderMCGEdge]
        map_stem = bl_edges[0].tight_name

        for bl_edge in bl_edges:

            edge_stem = bl_edge.tight_name
            if edge_stem != map_stem:
                self.warning(
                    f"Selected edges must belong to a single map stem (first stem: {map_stem}). "
                    f"Ignoring '{bl_edge.name}'.")
                continue

            edge_navmesh = bl_edge.navmesh_part
            if edge_navmesh is None:
                self.warning(f"Navmesh part not set for edge '{bl_edge.name}'. Ignoring.")
                continue  # can't update

            node_a = bl_edge.node_a  # type: bpy.types.Object
            node_b = bl_edge.node_b  # type: bpy.types.Object
            if node_a is None or node_b is None:
                self.warning(f"Node(s) not set for edge '{bl_edge.name}'. Ignoring.")
                continue
            bl_node_a = BlenderMCGNode(node_a)
            bl_node_b = BlenderMCGNode(node_b)

            node_a_triangles = bl_node_a.get_navmesh_triangles(edge_navmesh)
            if node_a_triangles is None:
                self.warning(
                    f"Node A '{node_a.name}' does not reference navmesh '{edge_navmesh.name}'. "
                    f"Ignoring edge '{bl_edge.name}'."
                )
                continue
            node_b_triangles = bl_node_b.get_navmesh_triangles(edge_navmesh)
            if node_b_triangles is None:
                self.warning(
                    f"Node B '{node_b.name}' does not reference navmesh '{edge_navmesh.name}'. "
                    f"Ignoring edge '{bl_edge.name}'."
                )
                continue

            start_face_i = min(node_a_triangles)
            end_face_i = min(node_b_triangles)

            total_cost = get_best_cost(edge_navmesh.data, start_face_i, end_face_i)
            if total_cost == 0.0:
                self.warning(f"No path found in either direction between nodes for edge '{bl_edge.name}'.")
                continue

            # We just use a custom property for this, not a real `BlenderMCGNode` property.
            bl_edge["New Cost"] = total_cost

        return {"FINISHED"}


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
    def poll(cls, context) -> bool:
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
            if context.scene.nav_graph_compute_settings.select_path:
                for face in path:
                    face.select_set(True)
        else:
            self.info("No path found between selected faces, even when all faces are passable.")

        bmesh.update_edit_mesh(obj.data)

        return {"FINISHED"}


# Some type hints for `AutoCreateMCG` below.
FACE_WITH_VERTS = tp.Tuple[bmesh.types.BMFace, frozenset[tuple[float, ...]]]
EXIT_CLUSTER = tp.Tuple[FACE_WITH_VERTS, ...]
NODE_WITH_KEY = tp.Tuple[BlenderMCGNode, tp.Tuple[int, int]]


class AutoCreateMCG(LoggingOperator):
    """Create a full MCG structure from scratch but detecting node placements (adjoining 'Exit' faces) and computing
    edge costs between all pairs of nodes in each navmesh.

    EXPERIMENTAL! Edge cost algorithm is not yet perfect, especially when Wall drops are involved. Some connections in
    vanilla MCG edges also seem to be manually inflated, presumably to avoid certain paths. However, I doubt this will
    matter in-game.
    """
    bl_idname = "mesh.auto_create_mcg"
    bl_label = "Create MCG from Navmeshes"
    bl_description = ("Create an entire MCG hierarchy of nodes/edges using all navmesh 'Exit' faces. Use by selecting "
                      "a COMPLETE, ORDERED collection of a map's MSB Navmesh parts")

    VERT_SQ_DIST_THRESHOLD: tp.ClassVar[float] = 0.01 ** 2

    # Holds all navmesh BMeshes so they can be freed and deleted without fail.
    navmesh_bmeshes: list[bmesh.types.BMesh]

    @classmethod
    def poll(cls, context):
        if context.mode != "OBJECT":
            return False
        try:
            BlenderMSBNavmesh.from_collection_objects(context.collection)
        except SoulstructTypeError:
            return False
        return True

    def invoke(self, context, event):
        """Confirmation dialog."""
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):

        self.navmesh_bmeshes = []

        try:
            return self.auto_create_mcg(context)
        except Exception as ex:
            import traceback
            traceback.print_exc()
            return self.error(f"An error occurred during automatic MCG creation: {ex}")
        finally:
            for bm in self.navmesh_bmeshes:
                bm.free()
                del bm

    def auto_create_mcg(self, context: bpy.types.Context):

        map_stem = context.collection.name.split(" ")[0]
        navmesh_parts = BlenderMSBNavmesh.from_collection_objects(context.collection)  # type: list[BlenderMSBNavmesh]

        navmesh_exit_clusters = []  # type: list[tuple[EXIT_CLUSTER, ...]]

        for navmesh_part in navmesh_parts:

            # Validate name format here, rather than waiting until below.
            try:
                int(navmesh_part.name[1:5])  # for sorting
            except ValueError:
                return self.error(f"Navmesh part '{navmesh_part.name}' must start with 'n####'.")

            bm = bmesh.new()
            bm.from_mesh(navmesh_part.data)  # same Mesh as NVM model
            # We do NOT remove doubles here, as it could modify face indices.
            bm.faces.ensure_lookup_table()  # face indices won't change again
            self.navmesh_bmeshes.append(bm)

            flags_layer = bm.faces.layers.int.get("nvm_face_flags")
            if flags_layer is None:
                self.warning(
                    f"Navmesh '{navmesh_part.name}' has no 'nvm_face_flags' `int` layer. Ignoring it for MCG creation."
                )
                navmesh_exit_clusters.append(())
                continue

            exit_clusters = self.get_navmesh_exit_clusters(navmesh_part, bm, flags_layer)
            self.info(f"Found {len(exit_clusters)} exit clusters for MSB Navmesh {navmesh_part.name}.")
            navmesh_exit_clusters.append(exit_clusters)

        collection = context.scene.collection
        bl_mcg = BlenderMCG.new(f"{map_stem} MCG", data=None, collection=collection)

        navmesh_nodes_and_keys = self._create_mcg_nodes(
            bl_mcg, collection, map_stem, navmesh_parts, navmesh_exit_clusters
        )
        self._create_mcg_edges(
            bl_mcg, collection, map_stem, navmesh_parts, navmesh_nodes_and_keys
        )

        # Since we succeeded, set MCG parent draw name.
        context.scene.mcg_draw_settings.mcg_parent = bl_mcg.obj
        return {"FINISHED"}

    @staticmethod
    def get_navmesh_exit_clusters(
        navmesh_part: BlenderMSBNavmesh, bm: bmesh.types.BMesh, flags_layer: bmesh.types.BMLayerItem
    ) -> tuple[EXIT_CLUSTER, ...]:

        # First, find all clusters of connected 'Exit' faces in each navmesh.
        exit_clusters = []
        checked = []

        for face in bm.faces:

            if face in checked:
                continue
            checked.append(face)

            if face[flags_layer] & NavmeshFlag.Exit:
                # Find all connected 'Exit' faces.
                cluster = []  # type: list[FACE_WITH_VERTS]
                stack = [face]
                while stack:
                    f = stack.pop()
                    if f in cluster:
                        continue

                    verts = frozenset(tuple(v.co + navmesh_part.location) for v in f.verts)
                    cluster.append((f, verts))
                    for edge in f.edges:
                        for other_face in edge.link_faces:
                            if other_face in checked:
                                continue
                            checked.append(other_face)  # cannot possibly already be checked
                            if other_face not in cluster and other_face[flags_layer] & NavmeshFlag.Exit:
                                stack.append(other_face)
                exit_clusters.append(tuple(cluster))

        return tuple(exit_clusters)

    def _create_mcg_nodes(
        self,
        bl_mcg: BlenderMCG,
        collection: bpy.types.Collection,
        map_stem: str,
        navmesh_parts: list[BlenderMSBNavmesh],
        navmesh_exit_clusters: list[tuple[EXIT_CLUSTER, ...]],
    ) -> list[list[NODE_WITH_KEY]]:
        """Find connected exit clusters across navmeshes and create MCG nodes in Blender at those sites.

        Returns a list of lists of `(BlenderMCGNode, (navmesh_a, navmesh_b))` tuples (one node list per navmesh part),
        where the inner navmesh tuples are always in ascending order.
        """

        # List of node objects stored for each navmesh part, along with ordered navmesh model IDs.
        # Actual returned list.
        navmesh_nodes_and_keys = [[] for _ in navmesh_parts]  # type: list[list[tuple[BlenderMCGNode, tuple[int, int]]]]

        # All MCG nodes, keyed by non-ordered (ascending navmesh ID) pairs of navmesh model IDs AND exact exit clusters.
        # Used to prevent the same node from being generated multiple times (from both sides).
        all_nodes = set()  # type: set[tuple[tuple[int, int], tuple[tuple[int, ...], tuple[int, ...]]]]

        # Maps non-ordered (ascending) pairs of navmesh part indices to the nodes connecting them.
        # Used to detect and add name suffix to multiple nodes between the same navmesh part pair.
        navmesh_pair_nodes = {}  # type: dict[tuple[int, int], list[BlenderMCGNode]]

        for nav_index, (navmesh_part, exit_clusters) in enumerate(
            zip(navmesh_parts, navmesh_exit_clusters, strict=True)
        ):

            navmesh_model_id = int(navmesh_part.name[1:5])  # validated above
            for cluster in exit_clusters:
                for face, face_verts in cluster:

                    for other_nav_index, (other_navmesh_part, other_exit_clusters) in enumerate(
                        zip(navmesh_parts, navmesh_exit_clusters, strict=True)
                    ):
                        if nav_index >= other_nav_index:
                            # Don't compare navmeshes we've already compared (or to self).
                            continue

                        other_navmesh_id = int(other_navmesh_part.name[1:5])  # validated above

                        # Don't forget that `i` and `j` are not necessarily equal to the navmesh model IDs.

                        for other_cluster in other_exit_clusters:

                            # Get node key and model pair key in ascending *navmesh ID* order.
                            if navmesh_model_id < other_navmesh_id:
                                model_pair_key = (navmesh_model_id, other_navmesh_id)
                                node_key = (cluster, other_cluster)
                            else:
                                model_pair_key = (other_navmesh_id, navmesh_model_id)
                                node_key = (other_cluster, cluster)

                            if (model_pair_key, node_key) in all_nodes:
                                # Already created this exact node.
                                continue

                            for other_face, other_face_verts in other_cluster:
                                # Check if faces are connected by an edge.
                                # As vertices may not be completely identical, this is unfortunately a bit slow.
                                hits = 0
                                for v in face_verts:
                                    for ov in other_face_verts:
                                        if self.sq_dist(v, ov) < self.VERT_SQ_DIST_THRESHOLD:
                                            hits += 1
                                            if hits >= 2:
                                                break
                                    else:
                                        continue
                                    break

                                if hits < 2:
                                    # No shared edge.
                                    continue

                                # Found a touching cluster. Create a new `BlenderMCGNode`.
                                node_name = f"{map_stem} Node [{model_pair_key[0]} | {model_pair_key[1]}]"
                                if model_pair_key in navmesh_pair_nodes:
                                    # Have already created a node for this pair of navmeshes. Add index suffices.
                                    index = len(navmesh_pair_nodes[model_pair_key])  # at least 1
                                    if index == 1:
                                        # Edit first node to add '(0)' suffix.
                                        navmesh_pair_nodes[model_pair_key][0].name += " (0)"
                                    node_name += f" ({index})"
                                else:
                                    # First node between these navmeshes. May not need to add index suffices.
                                    navmesh_pair_nodes[model_pair_key] = []

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

                                bl_node = BlenderMCGNode.new(node_name, None, collection)  # type: BlenderMCGNode
                                bl_node.obj.location = node_position
                                bl_node.obj.empty_display_type = "SPHERE"
                                bl_node.obj.parent = bl_mcg.node_parent

                                # Record node connecting this navmesh pair.
                                navmesh_pair_nodes[model_pair_key].append(bl_node)

                                if navmesh_model_id > other_navmesh_id:
                                    # Swap order of node's navmeshes, so node navmesh A is the earlier one.
                                    navmesh_part, other_navmesh_part = other_navmesh_part, navmesh_part
                                    cluster, other_cluster = other_cluster, cluster
                                    # Not used after this (except for logging), but for clarity:
                                    navmesh_model_id, other_navmesh_id = other_navmesh_id, navmesh_model_id

                                bl_node.navmesh_a = navmesh_part.obj
                                bl_node.navmesh_a_triangles = [f.index for f, _ in cluster]
                                bl_node.navmesh_b = other_navmesh_part.obj
                                bl_node.navmesh_b_triangles = [f.index for f, _ in other_cluster]

                                all_nodes.add((model_pair_key, node_key))
                                navmesh_nodes_and_keys[nav_index].append((bl_node, model_pair_key))
                                navmesh_nodes_and_keys[other_nav_index].append((bl_node, model_pair_key))

                                self.info(
                                    f"Created node: {bl_node.name} from {navmesh_part.name} to "
                                    f"{other_navmesh_part.name} ({bl_node.navmesh_a.name}, {bl_node.navmesh_b.name}) "
                                    f"with model IDs {navmesh_model_id} and {other_navmesh_id}."
                                )

            self.info(f"Found {len(navmesh_nodes_and_keys[nav_index])} nodes for navmesh {navmesh_part.name}.")

        return navmesh_nodes_and_keys

    def _create_mcg_edges(
        self,
        bl_mcg: BlenderMCG,
        collection: bpy.types.Collection,
        map_stem: str,
        navmesh_parts: list[BlenderMSBNavmesh],
        navmesh_nodes_and_keys: list[list[NODE_WITH_KEY]],
    ):
        """Create edges between connected node pairs in Blender MCG."""
        for navmesh_part, nodes_and_keys in zip(navmesh_parts, navmesh_nodes_and_keys, strict=True):
            created = set()

            if len(nodes_and_keys) == 1:
                # DEAD END navmesh with a single node. Only case where `MCGNode` references a navmesh part.
                bl_node = nodes_and_keys[0][0]
                if bl_node.name.endswith(" <DEAD END>"):
                    # ERROR: Node cannot straddle two dead ends.
                    return self.error(f"Node {bl_node.name} has two dead end navmeshes. Cannot create MCG.")
                bl_node.name += " <DEAD END>"  # this will cause the above error if it has no edges in ANOTHER navmesh
                continue  # no edges to create

            # We need to create non-directional edges on every pair of nodes touching this navmesh.
            for i, (bl_node_a, (a_navmesh_a, a_navmesh_b)) in enumerate(nodes_and_keys):
                for j, (bl_node_b, (b_navmesh_a, b_navmesh_b)) in enumerate(nodes_and_keys):
                    if i == j or (i, j) in created or (j, i) in created:
                        continue

                    # Neither of these can fail, by design.
                    node_a_triangles = bl_node_a.get_navmesh_triangles(navmesh_part.obj)
                    node_b_triangles = bl_node_b.get_navmesh_triangles(navmesh_part.obj)
                    if node_a_triangles is None or node_b_triangles is None:
                        print(navmesh_part.name, bl_node_a.navmesh_a.name, bl_node_b.navmesh_a.name)
                        raise ValueError(
                            f"Node {bl_node_a.name} and/or {bl_node_b.name} references no triangles in MSB Navmesh "
                            f"'{navmesh_part.name}'. Indicates MCG generator bug."
                        )

                    try:
                        start_face_i = min(node_a_triangles)
                        end_face_i = min(node_b_triangles)
                    except ValueError:
                        # No triangles! Only permitted by dead end navmeshes.
                        raise ValueError(
                            f"Node {bl_node_a.name} and/or {bl_node_b.name} references no "
                            f"triangles in MSB Navmesh '{navmesh_part.name}'."
                        )

                    if start_face_i == end_face_i:
                        raise ValueError(
                            f"Node {bl_node_a.name} and {bl_node_b.name} reference the same triangle "
                            f"({start_face_i}) in MSB Navmesh '{navmesh_part.name}'. This indicates that duplicate "
                            f"nodes have been created for the same cluster of Exit faces in the navmesh (an error)."
                        )

                    # Note that this creates its own `BMesh` that removes vertex doubles.
                    total_cost = get_best_cost(navmesh_part.data, start_face_i, end_face_i)
                    if total_cost == 0.0:
                        total_cost = 10000.0  # arbitrary error catch

                    edge_name = (
                        f"{map_stem} Edge ([{a_navmesh_a} | {a_navmesh_b}] "
                        f"-> [{b_navmesh_a} | {b_navmesh_b}]) <{navmesh_part.name}>"
                    )

                    bl_edge = BlenderMCGEdge.new(edge_name, None, collection)  # type: BlenderMCGEdge
                    bl_edge.parent = bl_mcg.edge_parent
                    start = bl_node_a.location
                    end = bl_node_b.location
                    direction = end - start
                    midpoint = (start + end) / 2.0
                    bl_edge.obj.empty_display_type = "PLAIN_AXES"
                    bl_edge.location = midpoint
                    # Point empty arrow in direction of edge.
                    bl_edge.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()

                    bl_edge.cost = total_cost
                    bl_edge.node_a = bl_node_a.obj
                    bl_edge.node_b = bl_node_b.obj
                    bl_edge.navmesh_part = navmesh_part.obj

                    created.add((i, j))

    @staticmethod
    def sq_dist(v1, v2) -> float:
        return sum((v1[_i] - v2[_i]) ** 2 for _i in range(3))
