from __future__ import annotations

__all__ = []

import typing as tp

import bpy
import bmesh
from bmesh.types import BMesh, BMVert, BMEdge, BMFace


def visit_connected_bmesh_islands(
    bm: bmesh.types.BMesh,
    selected_only=True,
    visit_verts: tp.Callable[[list[BMVert]], None] | None = None,
    visit_edges: tp.Callable[[list[BMEdge]], None] | None = None,
    visit_faces: tp.Callable[[list[BMFace]], None] | None = None,
):
    """For each connected island in `bm` (optionally, only those with at least one selected element), call any of
    the given visitor functions on the collected lists of vertices, edges, and/or faces in that island.

    Resets and uses the `tag` attribute of elements to track visited.
    """

    if not visit_verts and not visit_edges and not visit_faces:
        return  # nothing to do

    for v in bm.verts:
        v.tag = False
    for e in bm.edges:
        e.tag = False
    for f in bm.faces:
        f.tag = False

    # TODO: Need to work out switching logic for when we want to select verts/edges/faces.
