from __future__ import annotations

__all__ = [
    "build_spatial_adjacency",
    "a_star",
    "get_navmesh_step_cost",
    "get_best_cost",
    "get_edge_cost",
    "is_mesh_clean",
]

import heapq
import itertools
import math
from collections import defaultdict

import bpy
import bmesh
from bmesh.types import BMesh, BMFace
from mathutils import Vector

from soulstruct.base.events.enums import NavmeshFlag


def build_spatial_adjacency(bm: BMesh, tolerance: float = 0.001) -> dict[int, list[int]]:
    """Build face adjacency map using spatial vertex positions (STL-style).

    Two faces are considered adjacent if they share at least two vertex positions (within `tolerance`). This matches the
    game's own connectivity resolution and works correctly even when duplicate (non-merged) vertices exist or degenerate
    (zero-area) faces are present. Neither the mesh nor its face indices are modified.

    Returns a dict mapping each face index to a list of adjacent face indices.
    """
    inv_tol = 1.0 / tolerance

    def snap(co: Vector) -> tuple[int, int, int]:
        return round(co.x * inv_tol), round(co.y * inv_tol), round(co.z * inv_tol)

    # Compute snapped vertex positions per face.
    face_snap_sets = {}  # type: dict[int, frozenset[tuple[int, int, int]]]
    for face in bm.faces:
        face_snap_sets[face.index] = frozenset(snap(v.co) for v in face.verts)

    # Map each snapped position to the set of face indices whose vertices occupy it.
    pos_to_faces = defaultdict(set)  # type: defaultdict[tuple[int, int, int], set[int]]
    for fi, snaps in face_snap_sets.items():
        for s in snaps:
            pos_to_faces[s].add(fi)

    # For every pair of faces that share at least one snapped vertex position, count total shared positions.
    pair_shared = defaultdict(int)  # type: defaultdict[tuple[int, int], int]
    for face_indices in pos_to_faces.values():
        idx_list = list(face_indices)
        for i in range(len(idx_list)):
            for j in range(i + 1, len(idx_list)):
                key = (idx_list[i], idx_list[j]) if idx_list[i] < idx_list[j] else (idx_list[j], idx_list[i])
                pair_shared[key] += 1

    # Keep pairs with >= 2 shared snapped positions (i.e. a shared spatial edge).
    adjacency = defaultdict(list)  # type: defaultdict[int, list[int]]
    for (fi, fj), count in pair_shared.items():
        if count >= 2:
            adjacency[fi].append(fj)
            adjacency[fj].append(fi)

    return dict(adjacency)


def a_star(
    start_face: BMFace,
    end_face: BMFace,
    bm: BMesh,
    all_faces_passable=False,
    try_all_faces_passable_fallback=True,
    adjacency: dict[int, list[int]] | None = None,
) -> tuple[list[BMFace] | None, float, bool]:
    """Find the shortest path between two faces in a BMesh using A* algorithm.

    Uses spatial adjacency (see `build_spatial_adjacency`) rather than topological edge connectivity, so that meshes
    with duplicate (non-merged) vertices and/or degenerate faces are handled correctly without modifying the mesh.

    If `all_faces_passable` is `True`, the cost of each step is simply the distance between the faces. Otherwise,
    some face flags may modify the distance to get the cost. If `try_all_faces_passable_fallback` is `True`, and no path
    is found when `all_faces_passable` is `False`, the function will try again with `all_faces_passable` set to
    `True` to see if a path can be found through disabled/wall-climbing faces.

    An optional pre-built `adjacency` map can be passed in to avoid rebuilding it on recursive fallback calls or when
    the caller already has one (e.g. batch edge cost computation over the same mesh).

    Returns the list of faces in the path (including start and end), the total cost of the path, and the value of
    `all_faces_passable` so the caller can tell if the fallback option was used. If no path is found, returns
    `(None, float("inf"), True/False)`.
    """

    flags_layer = bm.faces.layers.int.get("nvm_face_flags")  # could be `None` for non-NVM meshes

    # Build spatial adjacency once (reused on fallback).
    if adjacency is None:
        bm.faces.ensure_lookup_table()
        adjacency = build_spatial_adjacency(bm)

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
    counter = itertools.count()  # unique sequence count for heap ordering (prevent undefined `BMFace` comparison)
    heapq.heappush(open_set, (0.0, next(counter), start_face))  # heap of `(f_score, counter, face)` tuples

    came_from = {}
    g_score = {face: float("inf") for face in bm.faces}
    g_score[start_face] = 0

    f_score = {face: float("inf") for face in bm.faces}
    f_score[start_face] = (start_centroid - end_centroid).length

    while open_set:
        _, _, current_face = heapq.heappop(open_set)  # discard F-score and counter

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

        for neighbor_index in adjacency.get(current_face.index, []):
            neighbor = bm.faces[neighbor_index]
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
                heapq.heappush(open_set, (f_score[neighbor], next(counter), neighbor))

    # No path found.
    if not all_faces_passable and try_all_faces_passable_fallback:
        # Try again with distance cost override. Reuse the same adjacency map.
        return a_star(
            start_face, end_face, bm,
            all_faces_passable=True,
            try_all_faces_passable_fallback=False,
            adjacency=adjacency,
        )
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


def get_edge_cost(
    mesh: bpy.types.Mesh, start_face_i: int, end_face_i: int
) -> tuple[list[BMFace] | None, float, bool]:
    """Get the cost of an MCG path between `start_face_i` and `end_face_i` in `mesh`.

    No mesh modification is performed; `a_star` uses spatial adjacency to handle duplicate vertices.
    """
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    start_face = bm.faces[start_face_i]
    end_face = bm.faces[end_face_i]
    try:
        return a_star(start_face, end_face, bm)
    finally:
        bm.free()


def is_mesh_clean(mesh: bpy.types.Mesh):
    """Check if mesh is clean: no vertices, edges, or faces removed by `bpy.ops.remove_doubles(dist=0.001)`."""
    bm = bmesh.new()
    bm.from_mesh(mesh)
    vertex_count = len(bm.verts)
    edge_count = len(bm.edges)
    face_count = len(bm.faces)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    if vertex_count != len(bm.verts) or edge_count != len(bm.edges) or face_count != len(bm.faces):
        return False
    return True
