from __future__ import annotations

__all__ = [

    "get_neighbors",
    "a_star",
    "get_navmesh_step_cost",
    "get_best_cost",
    "get_edge_cost",
]

import heapq
import math

import bpy
import bmesh
from bmesh.types import BMesh, BMFace
from mathutils import Vector

from soulstruct.base.events.enums import NavmeshFlag


def get_neighbors(face: BMFace) -> list[BMFace]:
    """Get all neighbors of BMesh face."""
    neighbors = []
    for edge in face.edges:
        linked_faces = [f for f in edge.link_faces if f != face]
        neighbors.extend(linked_faces)
    return neighbors


def a_star(
    start_face: BMFace, end_face: BMFace, bm: BMesh, all_faces_passable=False, try_all_faces_passable_fallback=True
) -> tuple[list[BMFace] | None, float, bool]:
    """Find shortest path between two faces in a BMesh using A* algorithm.

    If `all_faces_passable` is `True`, the cost of each step is simply the distance between the faces. Otherwise,
    some face flags may modify the distance to get the cost. If `try_all_faces_passable_fallback` is `True`, and no path
    is found when `all_faces_passable` is `False`, the function will try again with `all_faces_passable` set to
    `True` to see if a path can be found through disabled/wall-climbing faces.

    Returns the list of faces in the path (including start and end), the total cost of the path, and the value of
    `all_faces_passable` so the caller can tell if the fallback option was used. If no path is found, returns
    `(None, float("inf"), True/False)`.
    """

    flags_layer = bm.faces.layers.int.get("nvm_face_flags")  # could be `None` for non-NVM meshes

    # Cached centroids.
    centroids = {i: None for i in range(len(bm.faces))}  # type: dict[int, None | Vector]

    def get_centroid(_face: BMFace):
        if centroids[_face.index] is None:
            centroids[_face.index] = (_face.verts[0].co + _face.verts[1].co + _face.verts[2].co) / 3.0
        return centroids[_face.index]

    def get_distance(_face1: BMFace, _face2: BMFace):
        return (get_centroid(_face1) - get_centroid(_face2)).length

    start_centroid = get_centroid(start_face)
    end_centroid = get_centroid(end_face)

    open_set = []
    heapq.heappush(open_set, (0, start_face))

    came_from = {}
    g_score = {face: float("inf") for face in bm.faces}
    g_score[start_face] = 0

    f_score = {face: float("inf") for face in bm.faces}
    f_score[start_face] = (start_centroid - end_centroid).length

    while open_set:
        current_face = heapq.heappop(open_set)[1]

        if current_face == end_face:
            # Path complete. Compute total cost.
            path = []  # type: list[BMFace]
            total_cost = 0
            while current_face in came_from:
                path.append(current_face)
                current_face = came_from[current_face]
            path.append(start_face)
            path.reverse()

            for i in range(len(path) - 1):
                step_distance = get_distance(path[i], path[i + 1])
                step_cost = get_navmesh_step_cost(
                    path[i], path[i + 1], step_distance, flags_layer, all_faces_passable
                )
                total_cost += step_cost

            return path, total_cost, all_faces_passable

        for neighbor in get_neighbors(current_face):
            distance = get_distance(current_face, neighbor)
            cost = get_navmesh_step_cost(current_face, neighbor, distance, flags_layer, all_faces_passable)
            if math.isinf(cost):
                continue  # impassable
            tentative_g_score = g_score[current_face] + cost
            if tentative_g_score < g_score[neighbor]:
                # Found a cheaper path to `neighbor`.
                came_from[neighbor] = current_face
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + (get_centroid(neighbor) - end_centroid).length
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    # No path found.
    if not all_faces_passable and try_all_faces_passable_fallback:
        # Try again with distance cost override.
        return a_star(start_face, end_face, bm, all_faces_passable=True, try_all_faces_passable_fallback=False)
    return None, float("inf"), all_faces_passable


def get_navmesh_step_cost(
    from_face: BMFace,
    to_face: BMFace,
    distance: float,
    flags_layer=None,
    all_faces_passable=False,
) -> float:
    """Get the cost (for MCG edges) of travelling to a face with `face_flags` whose centroid is `distance` away.

    My multipliers in here are an attempt to match the costs set in vanilla MCG edges.
    """

    from_face_flags = from_face[flags_layer] if flags_layer is not None else 0
    to_face_flags = to_face[flags_layer] if flags_layer is not None else 0
    if to_face_flags == 0:
        # Cost is just distance.
        return distance

    if not all_faces_passable:
        if to_face_flags & NavmeshFlag.Disable:
            # Impassable face.
            return float("inf")
        if (from_face_flags & NavmeshFlag.FloorBeneathWall) and (to_face_flags & NavmeshFlag.Wall):
            # Cannot climb up wall (or drop is 'manually disabled' from the top).
            return float("inf")
        # NOTE: Degenerate faces are passable. They are sometimes used to join faces with different edge lengths.

    settings = bpy.context.scene.nav_graph_compute_settings

    if to_face_flags & NavmeshFlag.Obstacle:
        return settings.obstacle_multiplier * distance

    # TODO: Ladders don't seem to be penalized in general.
    # if to_face_flags & NavmeshFlag.Ladder:
    #     return 200 * distance

    if to_face_flags & NavmeshFlag.Wall:
        return settings.wall_multiplier * distance  # drop

    return distance


def get_best_cost(mesh: bpy.types.Mesh, start_face_i: int, end_face_i: int) -> float:
    """We calculate cost in both directions and use the cheaper one."""
    forward_path, forward_cost, forward_all_passable = get_edge_cost(mesh, start_face_i, end_face_i)
    backward_path, backward_cost, backward_all_passable = get_edge_cost(mesh, end_face_i, start_face_i)

    if not forward_path and not backward_path:
        return 0.0

    if forward_all_passable == backward_all_passable:
        return min(forward_cost, backward_cost)
    elif not forward_all_passable:
        # Use forward cost, as it didn't fall back to distance as cost.
        return forward_cost
    else:  # not backward_is_distance
        return backward_cost


def get_edge_cost(mesh: bpy.types.Mesh, start_face_i: int, end_face_i: int) -> tuple[list, float, bool]:
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bm.faces.ensure_lookup_table()
    start_face = bm.faces[start_face_i]
    end_face = bm.faces[end_face_i]
    try:
        return a_star(start_face, end_face, bm)
    finally:
        bm.free()
        del bm
