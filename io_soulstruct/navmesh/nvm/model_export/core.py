from __future__ import annotations

__all__ = [
    "NVMExportError",
    "export_nvm_model",
]

import numpy as np

import bmesh
import bpy

from soulstruct.darksouls1r.maps.navmesh.nvm import NVM, NVMTriangle, NVMEventEntity

from io_soulstruct.utilities.operators import LoggingOperator


class NVMExportError(Exception):
    """Exception raised during NVM export."""
    pass


def export_nvm_model(operator: LoggingOperator, nvm_model: bpy.types.MeshObject) -> NVM:
    """Create `NVM` from a Blender mesh object.

    This is much simpler than FLVER or HKX map collision mesh export. Note that the navmesh name is not needed, as
    it appears nowhere in the NVM binary file.

    We do not do any triangulation here; the NVM model should already be triangulated exactly as desired, as the
    triangles actually matter for navigation.
    """
    nvm_verts = np.array([vert.co for vert in nvm_model.data.vertices], dtype=np.float32)
    # Swap Y and Z coordinates.
    nvm_verts[:, [1, 2]] = nvm_verts[:, [2, 1]]

    nvm_faces = []  # type: list[tuple[int, int, int]]
    for face in nvm_model.data.polygons:
        if len(face.vertices) != 3:
            raise NVMExportError(
                f"Found a non-triangle mesh face in NVM (face {face.index}). You must triangulate it first."
            )
        # noinspection PyTypeChecker
        vertices = tuple(face.vertices)  # type: tuple[int, int, int]
        nvm_faces.append(vertices)

    def find_connected_face_index(edge_v1: int, edge_v2: int, not_face) -> int:
        """Find face that shares an edge with the given edge.

        Returns -1 if no connected face is found (i.e. edge is on the edge of the mesh).
        """
        # TODO: Could surely iterate over faces just once for this?
        for i_, f_ in enumerate(nvm_faces):
            if f_ != not_face and edge_v1 in f_ and edge_v2 in f_:  # order doesn't matter
                return i_
        return -1

    # Get connected faces along each edge of each face.
    nvm_connected_face_indices = []  # type: list[tuple[int, int, int]]
    for face in nvm_faces:
        connected_v1 = find_connected_face_index(face[0], face[1], face)
        connected_v2 = find_connected_face_index(face[1], face[2], face)
        connected_v3 = find_connected_face_index(face[2], face[0], face)
        nvm_connected_face_indices.append((connected_v1, connected_v2, connected_v3))
        if connected_v1 == -1 and connected_v2 == -1 and connected_v3 == -1:
            operator.warning(f"NVM face {face} appears to have no connected faces, which is very suspicious!")

    # Create `BMesh` to access custom face layers for `flags` and `obstacle_count`.
    bm = bmesh.new()
    bm.from_mesh(nvm_model.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    flags_layer = bm.faces.layers.int.get("nvm_face_flags")
    if not flags_layer:
        raise ValueError("NVM mesh does not have 'nvm_face_flags' custom face layer.")
    obstacle_count_layer = bm.faces.layers.int.get("nvm_face_obstacle_count")
    if not obstacle_count_layer:
        raise ValueError("NVM mesh does not have 'nvm_face_obstacle_count' custom face layer.")

    nvm_flags = []
    nvm_obstacle_counts = []
    for bm_face in bm.faces:
        nvm_flags.append(bm_face[flags_layer])
        nvm_obstacle_counts.append(bm_face[obstacle_count_layer])
    if len(nvm_flags) != len(nvm_faces):
        raise ValueError("NVM mesh has different number of `Mesh` faces and `BMesh` face flags.")

    nvm_triangles = [
        NVMTriangle(
            vertex_indices=nvm_faces[i],
            connected_indices=nvm_connected_face_indices[i],
            obstacle_count=nvm_obstacle_counts[i],
            flags=nvm_flags[i],
        )
        for i in range(len(nvm_faces))
    ]

    event_entities = []
    event_prefix = f"{nvm_model.name} Event "
    for child in nvm_model.children:
        if child.name.startswith(event_prefix):
            try:
                entity_id = child["entity_id"]
            except KeyError:
                operator.warning(f"Event entity '{child.name}' does not have 'entity_id' custom property. Ignoring.")
                continue
            try:
                triangle_indices = child["triangle_indices"]
            except KeyError:
                operator.warning(
                    f"Event entity '{child.name}' does not have 'triangle_indices' custom property. Ignoring.")
                continue
            event_entities.append(NVMEventEntity(entity_id=entity_id, triangle_indices=list(triangle_indices)))
        else:
            operator.warning(
                f"Child object '{child.name}' of NVM object '{nvm_model.name}' does not start with '{event_prefix}'. "
                f"Ignoring it as a navmesh event entity."
            )

    nvm = NVM(
        big_endian=False,
        vertices=nvm_verts,
        triangles=nvm_triangles,
        event_entities=event_entities,
        # quadtree boxes generated automatically
    )

    return nvm
