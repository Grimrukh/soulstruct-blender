from __future__ import annotations

__all__ = [
    "HKXImportInfo",
    "HKXMapCollisionImportError",
    "import_hkx_model",
]

import typing as tp

import numpy as np

import bpy

from soulstruct_havok.wrappers.hkx2015 import MapCollisionHKX

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


def import_hkx_model(
    hi_hkx: MapCollisionHKX,
    model_name: str,
    lo_hkx: MapCollisionHKX = None,
) -> bpy.types.MeshObject:
    """Read a HKX or two (hi/lo) HKXs into a single Blender mesh, with materials representing res/submeshes."""

    meshes = hi_hkx.to_meshes()
    hkx_material_indices = hi_hkx.map_collision_physics_data.get_subpart_materials()

    # Construct Blender materials corresponding to HKX res and material indices and collect indices.
    bl_materials = []  # type: list[bpy.types.Material]
    hkx_to_bl_material_indices = {}  # type: dict[tuple[bool, int], int]
    submesh_bl_materials = []  # matches length of `submeshes`
    for i in hkx_material_indices:
        if (True, i) not in hkx_to_bl_material_indices:
            # New hi-res Blender material.
            hkx_to_bl_material_indices[True, i] = len(bl_materials)
            bl_material = get_hkx_material(i, True)
            bl_materials.append(bl_material)
        submesh_bl_materials.append(hkx_to_bl_material_indices[True, i])

    vertices, faces, face_materials = join_hkx_meshes(meshes, submesh_bl_materials)

    if lo_hkx:
        lo_submeshes = lo_hkx.to_meshes()
        lo_hkx_material_indices = lo_hkx.map_collision_physics_data.get_subpart_materials()
        lo_submesh_bl_materials = []  # matches length of `lo_submeshes`
        # Continue building `bl_materials` list and `hkx_to_bl_material_indices` dict from hi-res above.
        for i in lo_hkx_material_indices:
            if (False, i) not in hkx_to_bl_material_indices:
                # New lo-res Blender material.
                hkx_to_bl_material_indices[False, i] = len(bl_materials)
                bl_material = get_hkx_material(i, False)
                bl_materials.append(bl_material)
            lo_submesh_bl_materials.append(hkx_to_bl_material_indices[False, i])

        lo_vertices, lo_faces, lo_face_materials = join_hkx_meshes(
            lo_submeshes, lo_submesh_bl_materials, initial_offset=len(vertices)
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
