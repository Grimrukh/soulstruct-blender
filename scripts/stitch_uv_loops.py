"""Script that looks at all selected UV loops (in the UV editor) and snaps them to the nearest non-selected UV loop
that uses the same vertex index.

This is a handy way of stitching UV islands together that want to be contiguous. For example, you have a simple grid
mesh, and end up doing something to a subset of contiguous faces that makes them much more complicated, and they lose
their UV continuity with the surrounding grid. You can project the new UVs from view (or however you want), drag that
island into the appropriate place in the grid's UV (now a hole), and use this script to snap the edges together. Then
you just need to adjust the interior UVs as desired.
"""
import bpy
import bmesh


# Maximum distance (squared) in UV space for snapping (remember UVs are 0-1 range).
MAX_DISTANCE_SQ = 0.01 ** 2


def main():

    if bpy.context.mode != "EDIT_MESH":
        print("This script must be run in Edit Mode.")
        return

    # Get the active object in Edit Mode
    obj = bpy.context.edit_object
    if obj.type != "MESH":
        print("This script only works on mesh objects.")
        return

    # noinspection PyTypeChecker
    mesh_data = obj.data  # type: bpy.types.Mesh

    bm = bmesh.from_edit_mesh(mesh_data)
    uv_layer = bm.loops.layers.uv.verify()

    # Group all UV loops by their mesh vertex index (regardless of selection).
    uv_loops_by_vert = {}
    for face in bm.faces:
        for loop in face.loops:
            v_idx = loop.vert.index
            uv_loops_by_vert.setdefault(v_idx, []).append(loop)

    # For each vertex, snap selected UV loops to the nearest non-selected loop (if within max distance).
    snap_count = 0
    for v_idx, loops in uv_loops_by_vert.items():

        # Only unselected loops are snapping target candidates.
        candidate_loops = [loop for loop in loops if not loop[uv_layer].select]

        # Process each loop that is selected (the ones we want to move)
        for loop in loops:
            if loop[uv_layer].select:
                current_uv = loop[uv_layer].uv.copy()
                closest_loop = None
                min_dist_sq = MAX_DISTANCE_SQ
                # Find closest candidate.
                for candidate in candidate_loops:
                    candidate_uv = candidate[uv_layer].uv
                    dist_sq = (current_uv - candidate_uv).length_squared
                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        closest_loop = candidate
                if closest_loop:
                    # Snap the selected UV loop to the candidate's UV position.
                    loop[uv_layer].uv = closest_loop[uv_layer].uv
                    snap_count += 1

    # Update the mesh to reflect changes
    bmesh.update_edit_mesh(mesh_data)

    print("Snapped", snap_count, "UV loops to their nearest same-vertex UV loop.")


if __name__ == "__main__":
    main()
