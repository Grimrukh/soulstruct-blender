from __future__ import annotations

__all__ = [
    "HKXImportInfo",
    "HKXMapCollisionImportError",
    "import_hkx_model_split",
    "import_hkx_model_merged",
]

import typing as tp

import numpy as np

import bpy

from soulstruct_havok.wrappers.hkx2015 import MapCollisionHKX

from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities.materials import *


# HSV values for HKX materials, out of 360/100/100.
HKX_MATERIAL_COLORS = {
    0: (0, 0, 100),  # default (white)
    1: (24, 75, 70),  # rock (orange)
    2: (130, 0, 10),  # stone (dark grey)
    3: (114, 58, 57),  # grass (green)
    4: (36, 86, 43),  # wood (dark brown)
    9: (179, 66, 64),  # metal (cyan)

    20: (214, 75, 64),  # under shallow water (light blue)
    21: (230, 85, 64),  # under deep water (dark blue)

    40: (50, 68, 80),  # trigger only (yellow)
}


class HKXImportInfo(tp.NamedTuple):
    """Holds information about a HKX to import into Blender."""
    model_name: str
    hi_hkx: MapCollisionHKX  # parsed HKX
    lo_hkx: MapCollisionHKX  # parsed HKX


class HKXMapCollisionImportError(Exception):
    pass


def import_hkx_model_split(
    hi_hkx: MapCollisionHKX,
    model_name: str,
    lo_hkx: MapCollisionHKX = None,
) -> bpy.types.Object:
    """Read a HKX or two (hi/lo) HKXs into submesh child Blender meshes of a single Empty parent."""

    hi_submeshes = hi_hkx.to_meshes()
    hi_hkx_material_indices = hi_hkx.map_collision_physics_data.get_subpart_materials()

    # Maps `(is_hi, hkx_mat_index)` to Blender materials.
    hkx_to_bl_materials = {}  # type: dict[tuple[bool, int], bpy.types.Material]
    submesh_objs = []

    def get_bl_mat(is_hi_res: bool, hkx_mat_index: int) -> bpy.types.Material:
        key = (is_hi_res, hkx_mat_index)
        if key in hkx_to_bl_materials:
            return hkx_to_bl_materials[key]
        # New Blender material for this res and index.
        _bl_material = get_hkx_material(hkx_mat_index, is_hi_res)
        hkx_to_bl_materials[key] = _bl_material
        return _bl_material

    # Construct Blender materials corresponding to HKX res and material indices and collect indices.
    for i, ((vertices, faces), hkx_material_index) in enumerate(zip(hi_submeshes, hi_hkx_material_indices)):
        bl_material = get_bl_mat(True, hkx_material_index)
        # Swap vertex Y and Z coordinates.
        vertices = np.c_[vertices[:, 0], vertices[:, 2], vertices[:, 1]]
        name = f"{model_name} Hi Submesh {i}"
        bl_mesh = bpy.data.meshes.new(name=f"{name} Mesh")
        edges = []  # no edges in HKX
        bl_mesh.from_pydata(vertices, edges, faces)
        bl_mesh.materials.append(bl_material)
        submesh_model_obj = bpy.data.objects.new(name, bl_mesh)
        submesh_objs.append(submesh_model_obj)

    if lo_hkx:
        lo_submeshes = lo_hkx.to_meshes()
        lo_hkx_material_indices = lo_hkx.map_collision_physics_data.get_subpart_materials()

        for i, ((vertices, faces), hkx_material_index) in enumerate(zip(lo_submeshes, lo_hkx_material_indices)):
            print(f"Making lo submesh {i} with mat index {hkx_material_index}")
            bl_material = get_bl_mat(False, hkx_material_index)
            # Swap vertex Y and Z coordinates.
            vertices = np.c_[vertices[:, 0], vertices[:, 2], vertices[:, 1]]
            name = f"{model_name} Lo Submesh {i}"
            bl_mesh = bpy.data.meshes.new(name=f"{name} Mesh")
            edges = []  # no edges in HKX
            bl_mesh.from_pydata(vertices, edges, faces)
            bl_mesh.materials.append(bl_material)
            submesh_model_obj = bpy.data.objects.new(name, bl_mesh)
            submesh_objs.append(submesh_model_obj)

    # Create empty parent.
    hkx_model = bpy.data.objects.new(model_name, None)
    for submesh_obj in submesh_objs:
        submesh_obj.parent = hkx_model

    return hkx_model


def import_hkx_model_merged(
    hi_hkx: MapCollisionHKX,
    model_name: str,
    lo_hkx: MapCollisionHKX = None,
) -> bpy.types.MeshObject:
    """Read a HKX or two (hi/lo) HKXs into a single Blender mesh, with materials representing res/submeshes."""

    hi_submeshes = hi_hkx.to_meshes()
    hkx_material_indices = hi_hkx.map_collision_physics_data.get_subpart_materials()

    # Maps `(is_hi, hkx_mat_index)` to Blender material index for both resolutions.
    hkx_to_bl_material_indices = {}  # type: dict[tuple[bool, int], int]
    # Blender materials, into which the above values index.
    bl_materials = []  # type: list[bpy.types.Material]

    def get_bl_mat_index(is_hi_res: bool, hkx_mat_index: int) -> int:
        key = (is_hi_res, hkx_mat_index)
        if key in hkx_to_bl_material_indices:
            return hkx_to_bl_material_indices[key]
        # New Blender material for this res and index.
        _i = hkx_to_bl_material_indices[key] = len(bl_materials)
        _bl_material = get_hkx_material(hkx_mat_index, is_hi_res)
        bl_materials.append(_bl_material)
        return _i

    # Construct Blender materials corresponding to HKX res and material indices and collect indices.
    hi_bl_mat_indices = []  # matches length of `hi_submeshes`
    for i in hkx_material_indices:
        bl_mat_index = get_bl_mat_index(True, i)
        hi_bl_mat_indices.append(bl_mat_index)

    vertices, faces, face_materials = join_hkx_meshes(hi_submeshes, hi_bl_mat_indices)

    if lo_hkx:
        lo_submeshes = lo_hkx.to_meshes()
        lo_hkx_material_indices = lo_hkx.map_collision_physics_data.get_subpart_materials()
        lo_bl_mat_indices = []  # matches length of `lo_submeshes`
        # Continue building `bl_materials` list and `hkx_to_bl_material_indices` dict from hi-res above.
        for i in lo_hkx_material_indices:
            bl_mat_index = get_bl_mat_index(False, i)
            lo_bl_mat_indices.append(bl_mat_index)

        lo_vertices, lo_faces, lo_face_materials = join_hkx_meshes(
            lo_submeshes, lo_bl_mat_indices, initial_offset=len(vertices)
        )
        vertices = np.row_stack((vertices, lo_vertices))
        faces = np.row_stack((faces, lo_faces))
        face_materials = np.concatenate([face_materials, lo_face_materials])

    # Swap vertex Y and Z coordinates.
    vertices = np.c_[vertices[:, 0], vertices[:, 2], vertices[:, 1]]

    bl_mesh = bpy.data.meshes.new(name=model_name)
    edges = []  # no edges in HKX
    bl_mesh.from_pydata(vertices, edges, faces)
    for material in bl_materials:
        bl_mesh.materials.append(material)
    bl_mesh.polygons.foreach_set("material_index", face_materials)

    hkx_model = bpy.data.objects.new(model_name, bl_mesh)
    hkx_model.soulstruct_type = SoulstructType.COLLISION
    # NOTE: There is no `SoulstructObject` wrapper for Collisions because they have no properties to store/access.
    # Material indices are represented in the material names.

    # noinspection PyTypeChecker
    return hkx_model


def join_hkx_meshes(
    meshes: list[tuple[np.ndarray, np.ndarray]], bl_material_indices: tp.Sequence[int], initial_offset=0
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Concatenate all vertices and faces from a list of meshes by offsetting the face indices.

    Also returns array of face material indices for use with `foreach_set()` by simply coping the corresponding
    `bl_material_indices` element to all faces.
    """
    if len(meshes) != len(bl_material_indices):
        raise ValueError("Number of HKX meshes and material indices must match.")
    vert_stack = []
    face_stack = []
    face_materials = []
    offset = initial_offset
    for (vertices, faces), material_index in zip(meshes, bl_material_indices, strict=True):
        face_stack.append(faces + offset)
        vert_stack.append(vertices)
        face_materials.extend([material_index] * len(faces))
        offset += len(vertices)
    vertices = np.row_stack(vert_stack)
    faces = np.row_stack(face_stack)
    return vertices, faces, np.array(face_materials)


def get_hkx_material(hkx_material_index: int, is_hi_res: bool) -> bpy.types.Material:
    material_name = f"HKX {hkx_material_index} ({'Hi' if is_hi_res else 'Lo'})"
    try:
        material_offset, material_base = divmod(hkx_material_index, 100)
        hkx_material_enum = MapCollisionHKX.MapCollisionMaterial(material_base)
    except ValueError:
        pass
    else:
        # Add material enum name to material name. Will be ignored on export.
        if material_offset == 0:
            material_name = f"{material_name} <{hkx_material_enum.name}>"
        else:
            material_name = f"{material_name} <{hkx_material_enum.name} + {100 * material_offset}>"

    try:
        return bpy.data.materials[material_name]
    except KeyError:
        pass
    offset_100, mod_index = divmod(hkx_material_index, 100)
    h, s, v = HKX_MATERIAL_COLORS.get(mod_index, (340, 74, 70))  # defaults to red
    if offset_100 > 0:  # rotate hue by 10 degrees for each 100 in material index
        h = (h + 10 * offset_100) % 360
    h /= 360.0
    s /= 100.0
    v /= 100.0
    if not is_hi_res:  # darken for lo-res
        v /= 2
    color = hsv_color(h, s, v)  # alpha = 1.0
    # NOTE: Not using wireframe in collision materials (unlike navmesh) as there is no per-face data.
    return create_basic_material(material_name, color, wireframe_pixel_width=0.0)
