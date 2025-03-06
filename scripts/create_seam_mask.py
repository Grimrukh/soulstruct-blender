"""Script that lets the user select edges in Edit Mode, then creates duplicates of adjacent faces, shrinks/fattens them
slightly to cover the original edge, and sets alpha to 1 (selected edge) or 0 (other edges) to serve as a mask.

TODO: Version that blends vertex alpha from 0 to 1 or 1 to 0, rather than 0-1-0, to blend between distinct textures
 rather than just covering a generic seam. Note that this 0-1-0 still gets that job done, though.
"""

import bpy
import bmesh


def main(offset: float = 0.015, tol: float = 1e-6):

    # Get the active object (must be in Edit Mode and a mesh)
    obj = bpy.context.edit_object
    if not obj or obj.type != 'MESH':
        raise Exception("Active object must be a mesh in Edit Mode.")

    # noinspection PyTypeChecker
    mesh = obj.data  # type: bpy.types.Mesh

    bm = bmesh.from_edit_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # Get (or create) the vertex color layer named "VertexColors"
    color_layer = bm.loops.layers.color.get("VertexColors")
    if color_layer is None:
        color_layer = bm.loops.layers.color.new("VertexColors")

    # ===== Step 1: Record the positions of vertices on the selected edges =====
    selected_edges = [edge for edge in bm.edges if edge.select]
    if not selected_edges:
        raise Exception("No edges selected. Please select one or more edges first.")

    # Record copies of each vertex coordinate from each selected edge.
    original_edge_coords = []
    for edge in selected_edges:
        for v in edge.verts:
            original_edge_coords.append(v.co.copy())

    # ===== Step 2: Gather all faces connected to any selected edge =====
    faces_to_dup = set()
    for edge in selected_edges:
        for face in edge.link_faces:
            faces_to_dup.add(face)
    faces_to_dup = list(faces_to_dup)

    if not faces_to_dup:
        raise Exception("No faces connected to the selected edges.")

    # ===== Step 3: Duplicate these faces using BMesh operators =====
    dup_result = bmesh.ops.duplicate(bm, geom=faces_to_dup)
    dup_geom = dup_result["geom"]

    # ===== Step 4: Identify duplicated vertices that came from the original selected edges =====
    dup_verts = [elem for elem in dup_geom if isinstance(elem, bmesh.types.BMVert)]
    original_dup_verts = set()
    for v in dup_verts:
        for orig_co in original_edge_coords:
            if (v.co - orig_co).length < tol:
                original_dup_verts.add(v)
                break

    # ===== Step 5: For each face loop in duplicated faces using one of those vertices, set alpha to 1 =====
    dup_faces = [elem for elem in dup_geom if isinstance(elem, bmesh.types.BMFace)]
    for face in dup_faces:
        for loop in face.loops:
            if loop.vert in original_dup_verts:
                # loop[color_layer] is a 4-tuple (R, G, B, A); set alpha (index 3) to 1
                col = list(loop[color_layer])
                col[3] = 1.0
                loop[color_layer] = col

    # ===== Step 6: Invert the duplicated vertex selection (within the duplicated geometry) =====
    all_dup_verts = set(dup_verts)
    other_dup_verts = all_dup_verts - original_dup_verts

    # For each face loop using one of these "other" vertices, set vertex color alpha to 0.
    for face in dup_faces:
        for loop in face.loops:
            if loop.vert in other_dup_verts:
                col = list(loop[color_layer])
                col[3] = 0.0
                loop[color_layer] = col

    # ===== Step 7: Ensure all duplicated geometry is selected =====
    for elem in dup_geom:
        if hasattr(elem, "select"):
            elem.select = True

    bmesh.update_edit_mesh(mesh, True)

    # ===== Step 8: Run the Shrink/Fatten operator on the duplicated geometry =====
    # A positive offset fattens; a negative offset shrinks.
    bpy.ops.transform.shrink_fatten(value=offset)

    print("Operation complete.")


if __name__ == '__main__':
    main()
