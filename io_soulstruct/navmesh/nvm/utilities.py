from __future__ import annotations

__all__ = [
    "ANY_NVM_NAME_RE",
    "STANDARD_NVM_STEM_RE",
    "NVMBND_NAME_RE",
    "NAVMESH_FLAG_COLORS",
    "NAVMESH_MULTIPLE_FLAG_COLOR",
    "get_navmesh_msb_transforms",
    "set_face_material",
]

import math
import re
import typing as tp
from pathlib import Path

import bpy
import heapq
from bmesh.types import BMesh, BMFace
from mathutils import Vector

from soulstruct.darksouls1r.maps import MSB, get_map
from soulstruct.darksouls1r.maps.navmesh import NavmeshFlag

from io_soulstruct.utilities import Transform
from io_soulstruct.utilities.materials import hsv_color, create_basic_material

if tp.TYPE_CHECKING:
    from .misc_operators import NavmeshComputeSettings


ANY_NVM_NAME_RE = re.compile(r"^(?P<stem>.*)\.nvm(?P<dcx>\.dcx)?$")
STANDARD_NVM_STEM_RE = re.compile(r"^n(\d{4})B(?P<B>\d)A(?P<A>\d{2})$")  # no extensions
NVMBND_NAME_RE = re.compile(r"^.*?\.nvmbnd(\.dcx)?$")


# In descending priority order. All flags can be inspected in custom properties.
NAVMESH_FLAG_COLORS = {
    NavmeshFlag.Disable: hsv_color(0.0, 0.0, 0.1),  # DARK GREY
    NavmeshFlag.Degenerate: hsv_color(0.0, 0.0, 0.1),  # DARK GREY
    NavmeshFlag.Obstacle: hsv_color(0.064, 0.9, 0.2),  # DARK ORANGE
    NavmeshFlag.BlockExit: hsv_color(0.3, 0.9, 1.0),  # LIGHT GREEN
    NavmeshFlag.Hole: hsv_color(0.066, 0.9, 0.5),  # ORANGE
    NavmeshFlag.Ladder: hsv_color(0.15, 0.9, 0.5),  # YELLOW
    NavmeshFlag.ClosedDoor: hsv_color(0.66, 0.9, 0.25),  # DARK BLUE
    NavmeshFlag.Exit: hsv_color(0.33, 0.9, 0.15),  # DARK GREEN
    NavmeshFlag.Door: hsv_color(0.66, 0.9, 0.75),  # LIGHT BLUE
    NavmeshFlag.InsideWall: hsv_color(0.4, 0.9, 0.3),  # TURQUOISE
    NavmeshFlag.Edge: hsv_color(0.066, 0.9, 0.5),  # ORANGE
    NavmeshFlag.FloorBeneathWall: hsv_color(0.0, 0.8, 0.8),  # LIGHT RED
    NavmeshFlag.LandingPoint: hsv_color(0.4, 0.9, 0.7),  # LIGHT TURQUOISE
    NavmeshFlag.LargeSpace: hsv_color(0.7, 0.9, 0.7),  # PURPLE
    NavmeshFlag.Event: hsv_color(0.5, 0.9, 0.5),  # CYAN
    NavmeshFlag.Wall: hsv_color(0.0, 0.8, 0.1),  # DARK RED
    NavmeshFlag.Default: hsv_color(0.8, 0.9, 0.5),  # MAGENTA
}
NAVMESH_MULTIPLE_FLAG_COLOR = hsv_color(0.0, 0.0, 1.0)  # WHITE
NAVMESH_UNKNOWN_FLAG_COLOR = hsv_color(0.0, 0.0, 0.25)  # GREY


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

    settings = bpy.context.scene.navmesh_compute_settings
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
                    path[i], path[i + 1], step_distance, flags_layer, settings, all_faces_passable
                )
                total_cost += step_cost

            return path, total_cost, all_faces_passable

        for neighbor in get_neighbors(current_face):
            distance = get_distance(current_face, neighbor)
            cost = get_navmesh_step_cost(current_face, neighbor, distance, flags_layer, settings, all_faces_passable)
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
    flags_layer = None,
    settings: NavmeshComputeSettings = None,
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

    if all_faces_passable:
        if to_face_flags & NavmeshFlag.Disable:
            # Impassable face.
            return float("inf")
        if (from_face_flags & NavmeshFlag.FloorBeneathWall) and (to_face_flags & NavmeshFlag.Wall):
            # Cannot climb up wall (or drop is 'manually disabled' from the top).
            return float("inf")
        # NOTE: Degenerate faces are passable. They are sometimes used to join faces with different edge lengths.

    if settings is None:
        # No other flags to check for cost modification.
        return distance

    if to_face_flags & NavmeshFlag.Obstacle:
        return settings.obstacle_multiplier * distance

    # TODO: Ladders don't seem to be penalized in general.
    # if to_face_flags & NavmeshFlag.Ladder:
    #     return 200 * distance

    if to_face_flags & NavmeshFlag.Wall:
        return settings.wall_multiplier * distance  # drop

    return distance


def get_navmesh_msb_transforms(
    msb_model_name: str, nvm_path: Path, msb: MSB | None = None, msb_path: Path = None
) -> list[tuple[str, Transform]]:
    """Search MSB at `msb_path` (autodetected from `nvm_path.parent` by default) and return
    `(navmesh_name, Transform)` pairs for all Navmesh entries using the `nvm_name` model."""
    if msb is None and msb_path is None:
        nvm_parent_dir = nvm_path.parent
        nvm_map = get_map(nvm_parent_dir.name)
        msb_path = nvm_parent_dir.parent / f"MapStudio/{nvm_map.msb_file_stem}.msb"
    if msb is None:
        if not msb_path.is_file():
            raise FileNotFoundError(f"Cannot find MSB file '{msb_path}'.")
        try:
            msb = MSB.from_path(msb_path)
        except Exception as ex:
            raise RuntimeError(
                f"Cannot open MSB: {ex}.\n"
                f"\nCurrently, only Dark Souls 1 (either version) MSBs are supported."
            )
    elif msb_path is not None:
        raise ValueError("Cannot provide both `msb` and `msb_path`.")
    matches = []
    for navmesh in msb.navmeshes:
        if msb_model_name == navmesh.model.name:
            matches.append(navmesh)
    if not matches:
        raise ValueError(f"Cannot find any MSB Navmesh entries using MSB model '{msb_model_name}'.")
    transforms = [(m.name, Transform.from_msb_entry(m)) for m in matches]
    return transforms


def set_face_material(bl_mesh, bl_face, face_flags: int):
    """Set face materials according to their `NVMTriangle` flags.

    Searches for existing materials on the mesh with names like "Navmesh Flag <flag_name>", and creates them with
    simple diffuse colors if they don't exist in the Blender session yet.

    NOTE: `bl_face` can be from a `Mesh` or `BMesh`. Both have `material_index`.
    """

    # Color face according to its single `flag` if present.
    try:
        flag = NavmeshFlag(face_flags)
        material_name = f"Navmesh Flag {flag.name}"
    except ValueError:  # multiple flags
        flag = None
        material_name = "Navmesh Flag <Multiple>"

    material_index = bl_mesh.materials.find(material_name)
    if material_index >= 0:
        bl_face.material_index = material_index
        return bl_mesh.materials[material_name]

    # Try to get existing material from Blender.
    try:
        bl_material = bpy.data.materials[material_name]
    except KeyError:
        # Create new material with color from dictionary.
        if flag is None:
            color = NAVMESH_MULTIPLE_FLAG_COLOR
        else:
            try:
                color = NAVMESH_FLAG_COLORS[flag]
            except (ValueError, KeyError):
                # Unspecified flag color.
                color = NAVMESH_UNKNOWN_FLAG_COLOR
        bl_material = create_basic_material(material_name, color, wireframe_pixel_width=2)

    # Add material to this mesh and this face.
    bl_face.material_index = len(bl_mesh.materials)
    bl_mesh.materials.append(bl_material)
    return bl_material
