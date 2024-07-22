from __future__ import annotations

__all__ = [
    "HKXMapCollisionExportError",
    "LOOSE_HKX_COLLISION_STEM_RE",
    "NUMERIC_HKX_COLLISION_STEM_RE",
    "export_hkx_map_collision",
]

import re

import numpy as np

import bmesh
import bpy

from soulstruct_havok.wrappers.hkx2015 import MapCollisionHKX

from io_soulstruct.utilities import *


class HKXMapCollisionExportError(Exception):
    pass


LOOSE_HKX_COLLISION_STEM_RE = re.compile(r"^([hl])(\w{6})A(\d\d)$")  # game-readable model name; no extensions
NUMERIC_HKX_COLLISION_STEM_RE = re.compile(r"^([hl])(\d{4})B(\d)A(\d\d)$")  # standard map model name; no extensions

HKX_MATERIAL_NAME_RE = re.compile(r"HKX (?P<index>\d+) \((?P<res>Hi|Lo)\).*")  # Blender HKX material name


def export_hkx_map_collision(
    operator: LoggingOperator,
    hkx_model: bpy.types.MeshObject | bpy.types.Object,
    hi_name: str | None,
    lo_name: str | None,
    require_hi=True,
    use_hi_if_missing_lo=False,
) -> tuple[MapCollisionHKX | None, MapCollisionHKX | None]:
    """Create 'hi' and/or 'lo' HKX files by splitting given `hkx_model` into submeshes by material, or (if empty),
    directly from child submesh Mesh objects.

    `hi_name` and `lo_name` are required to set internally to the HKX file (though it probably doesn't impact
    gameplay). If passed explicitly as `None`, those submeshes will be ignored -- but they cannot BOTH be `None`.

    TODO: Currently only supported for DS1R (Havok 2015).
    """
    if not hi_name and not lo_name:
        raise ValueError("At least one of 'hi_name' and 'lo_name' must be provided.")

    if hkx_model.type == "MESH":
        # Single merged mesh. Split by material.
        hi_hkx_meshes, hi_hkx_mat_indices, lo_hkx_meshes, lo_hkx_mat_indices = _export_hkx_map_collision_merged(
            hkx_model=hkx_model,
            hi_name=hi_name,
            lo_name=lo_name,
        )
    elif hkx_model.type == "EMPTY":
        if len([c for c in hkx_model.children if c.type == "MESH"]) == 0:
            raise HKXMapCollisionExportError(
                f"Empty '{hkx_model.name}' has no child meshes to export as HKX Map Collision submeshes."
            )
        # Parent of submesh children.
        hi_hkx_meshes, hi_hkx_mat_indices, lo_hkx_meshes, lo_hkx_mat_indices = _export_hkx_map_collision_split(
            operator=operator,
            hkx_model=hkx_model,
            hi_name=hi_name,
            lo_name=lo_name,
        )
    else:
        raise HKXMapCollisionExportError(
            f"Object '{hkx_model.name}' is not a Mesh or Empty object. It cannot be exported as a HKX Map Collision."
        )

    if hi_hkx_meshes:
        hi_hkx = MapCollisionHKX.from_meshes(
            meshes=hi_hkx_meshes,
            hkx_name=hi_name,
            material_indices=hi_hkx_mat_indices,
            # Bundled template HKX serves fine.
            # DCX applied by caller.
        )
    else:
        if require_hi:
            raise HKXMapCollisionExportError(
                f"No 'hi' HKX meshes found in mesh '{hkx_model.name}'."
            )
        operator.warning(f"No 'hi' HKX meshes found in mesh '{hkx_model.name}' and `require_hi=False`.")
        hi_hkx = None

    if lo_hkx_meshes:
        lo_hkx = MapCollisionHKX.from_meshes(
            meshes=lo_hkx_meshes,
            hkx_name=lo_name,
            material_indices=lo_hkx_mat_indices,
            # Bundled template HKX serves fine.
            # DCX applied by caller.
        )
    elif use_hi_if_missing_lo:
        # Duplicate hi-res meshes and materials for lo-res (but use lo-res name).
        lo_hkx = MapCollisionHKX.from_meshes(
            meshes=hi_hkx_meshes,
            hkx_name=lo_name,
            material_indices=hi_hkx_mat_indices,
            # Bundled template HKX serves fine.
            # DCX applied by caller.
        )
    else:
        operator.warning(f"No 'lo' HKX meshes found for '{lo_name}' and `use_hi_if_missing_lo=False`.")
        lo_hkx = None

    if not hi_hkx and not lo_hkx:
        raise HKXMapCollisionExportError(
            f"No material-based HKX submeshes could be created for HKX mesh '{hkx_model.name}'. Are all faces "
            f"assigned to a material with name template 'HKX # (Hi|Lo)'?"
        )

    return hi_hkx, lo_hkx


def _export_hkx_map_collision_merged(
    hkx_model: bpy.types.MeshObject,
    hi_name: str | None,
    lo_name: str | None,
) -> tuple[list[tuple[np.ndarray, np.ndarray]], list[int], list[tuple[np.ndarray, np.ndarray]], list[int]]:
    """Split `hkx_model` Mesh into submeshes by face material."""

    if not hkx_model.material_slots:
        raise ValueError(f"HKX model mesh '{hkx_model.name}' has no materials for submesh detection.")

    # Automatically triangulate the mesh.
    _clear_temp_hkx()
    bm = bmesh.new()
    bm.from_mesh(hkx_model.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
    tri_mesh_data = bpy.data.meshes.new("__TEMP_HKX__")
    # No need to copy materials over (no UV, etc.)
    bm.to_mesh(tri_mesh_data)
    bm.free()
    del bm

    hi_hkx_meshes = []  # type: list[tuple[np.ndarray, np.ndarray]]  # vertices, faces
    hi_hkx_material_indices = []  # type: list[int]
    lo_hkx_meshes = []  # type: list[tuple[np.ndarray, np.ndarray]]  # vertices, faces
    lo_hkx_material_indices = []  # type: list[int]

    # Note that it is possible that the user may have faces with different materials share vertices; this is fine,
    # and that vertex will be copied into each HKX submesh with a face loop that uses it.

    # Rather than iterating over all faces once for every material, we iterate over all of them once to split them
    # up by material index, then iterate once over each of those sublists (so the full face list is iterated twice).
    faces_by_material = {i: [] for i in range(len(hkx_model.material_slots))}
    for face in tri_mesh_data.polygons:
        try:
            faces_by_material[face.material_index].append(face)
        except KeyError:
            raise HKXMapCollisionExportError(
                f"Face {face.index} of mesh '{hkx_model.name}' has material index {face.material_index}, "
                f"which is not in the material slots of the mesh."
            )

    # Now iterate over each sublist of faces and create lists of HKX vertices and faces for each one. We maintain
    # a vertex map that maps the original full-mesh Blender vertex index to the submesh index.
    for bl_material_index, faces in faces_by_material.items():
        if not faces:
            continue  # no faces use this material

        # We can use the original non-triangulated mesh's material slots.
        bl_material = hkx_model.material_slots[bl_material_index].material
        mat_match = HKX_MATERIAL_NAME_RE.match(bl_material.name)
        if not mat_match:
            raise HKXMapCollisionExportError(
                f"Material '{bl_material.name}' of mesh '{hkx_model.name}' does not match expected HKX material "
                f"name pattern: 'HKX # (Hi|Lo)'."
            )
        hkx_material_index = int(mat_match.group("index"))
        res = mat_match.group("res")[0].lower()  # 'h' or 'l'
        if (res == "h" and not hi_name) or (res == "l" and not lo_name):
            continue  # ignoring resolution

        # We can't assume that all faces with the same material index - and the vertices they use - are contiguous
        # in `polygons`, so a simple global vertex index subtraction won't work. We need to maintain a vertex map.
        vertex_map = {}
        hkx_verts_list = []
        hkx_faces_list = []
        for face in faces:
            hkx_face = []
            for vert_index in face.vertices:
                if vert_index not in vertex_map:
                    # First time this vertex has been used by this submesh.
                    hkx_vert_index = vertex_map[vert_index] = len(hkx_verts_list)
                    vert = tri_mesh_data.vertices[vert_index]
                    hkx_verts_list.append(
                        [vert.co.x, vert.co.z, vert.co.y]  # may as well swap Y and Z coordinates here
                    )
                else:
                    # Vertex has already been used by this submesh.
                    hkx_vert_index = vertex_map[vert_index]
                hkx_face.append(hkx_vert_index)
            hkx_faces_list.append(hkx_face)

        meshes, hkx_material_indices = (
            (hi_hkx_meshes, hi_hkx_material_indices) if res == "h" else (lo_hkx_meshes, lo_hkx_material_indices)
        )
        meshes.append(
            (np.array(hkx_verts_list, dtype=np.float32), np.array(hkx_faces_list, dtype=np.uint32))
        )
        hkx_material_indices.append(hkx_material_index)

    _clear_temp_hkx()

    return (
        hi_hkx_meshes,
        hi_hkx_material_indices,
        lo_hkx_meshes,
        lo_hkx_material_indices,
    )


def _export_hkx_map_collision_split(
    operator: LoggingOperator,
    hkx_model: bpy.types.Object,
    hi_name: str | None,
    lo_name: str | None,
):
    """Submeshes are already their own Mesh children of `hkx_model` Empty parent.

    Note that we extract the HKX material index from the Blender material name.
    """

    hi_hkx_meshes = []  # type: list[tuple[np.ndarray, np.ndarray]]  # vertices, faces
    hi_hkx_material_indices = []  # type: list[int]
    lo_hkx_meshes = []  # type: list[tuple[np.ndarray, np.ndarray]]  # vertices, faces
    lo_hkx_material_indices = []  # type: list[int]

    for submesh in hkx_model.children:
        if submesh.type != "MESH":
            continue  # ignore
        if len(submesh.material_slots) > 1:
            raise HKXMapCollisionExportError(
                f"Mesh '{submesh.name}' has more than one material slot, which is not supported for HKX map collision "
                f"export from split submesh children."
            )

        # Parse material name for resolution and HKX material index.
        bl_material = submesh.material_slots[0].material
        mat_match = HKX_MATERIAL_NAME_RE.match(bl_material.name)
        if not mat_match:
            raise HKXMapCollisionExportError(
                f"Material '{bl_material.name}' of mesh '{hkx_model.name}' does not match expected HKX material "
                f"name pattern: 'HKX # (Hi|Lo)'."
            )
        hkx_material_index = int(mat_match.group("index"))
        res = mat_match.group("res")[0].lower()  # 'h' or 'l'
        if (res == "h" and not hi_name) or (res == "l" and not lo_name):
            continue  # ignoring resolution
        if res == "h" and " Hi " not in submesh.name:
            operator.warning(
                f"Submesh '{submesh.name}' has 'Hi' material but does not contain ' Hi ' in its name. It will be "
                f"exported as hi-resolution."
            )
        if res == "l" and " Lo " not in submesh.name:
            operator.warning(
                f"Submesh '{submesh.name}' has 'Lo' material but does not contain ' Lo ' in its name. It will be "
                f"exported as lo-resolution."
            )

        # Automatically triangulate the mesh.
        _clear_temp_hkx()
        bm = bmesh.new()
        bm.from_mesh(submesh.data)
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
        tri_mesh_data = bpy.data.meshes.new("__TEMP_HKX__")
        # No need to copy materials over (no UV, etc.)
        bm.to_mesh(tri_mesh_data)
        bm.free()
        del bm

        # Easy: we use vertices and polygons directly (swapping vertex Y and Z).
        vertices = np.empty((len(tri_mesh_data.vertices), 3), dtype=np.float32)
        tri_mesh_data.vertices.foreach_get("co", vertices.ravel())
        vertices = np.c_[vertices[:, 0], vertices[:, 2], vertices[:, 1]]
        faces = np.empty((len(tri_mesh_data.polygons), 3), dtype=np.uint32)
        tri_mesh_data.polygons.foreach_get("vertices", faces.ravel())

        # Append meshes and materials to the correct resolution list.
        meshes, hkx_material_indices = (
            (hi_hkx_meshes, hi_hkx_material_indices) if res == "h" else (lo_hkx_meshes, lo_hkx_material_indices)
        )
        meshes.append((vertices, faces))
        hkx_material_indices.append(hkx_material_index)

    _clear_temp_hkx()

    return (
        hi_hkx_meshes,
        hi_hkx_material_indices,
        lo_hkx_meshes,
        lo_hkx_material_indices,
    )


def _clear_temp_hkx():
    """Delete temporary triangulated HKX mesh."""
    try:
        bpy.data.meshes.remove(bpy.data.meshes["__TEMP_HKX__"])
    except KeyError:
        pass
