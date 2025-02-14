"""Script to help unwrap UVs using connected pinned UVs.

This script starts with an initial selection of vertices, pins the UVs of those vertices, then flood-fills outwards from
those vertices to select all faces whose loops are either in the initial selection or have UV (0, 0). It then unwraps
those faces, which should make them contiguous with the pinned section.

NOTE: UV Sync Selection must be enabled. This lets us select vertices in the 3D view and have their UV loops selected
automatically.
"""
import bpy
import bmesh
from mathutils import Vector

# Tolerance for comparing UVs to (0,0)
EPS = 1e-6
ZERO = Vector((0.0, 0.0))


def is_loop_zero_uv(loop, uv_layer):
    return (loop[uv_layer].uv - ZERO).length < EPS


def main():

    # Check if UV Sync Selection is enabled.
    if not bpy.context.scene.tool_settings.use_uv_select_sync:
        raise RuntimeError("UV Sync Selection must be enabled in the UV Editor.")

    obj = bpy.context.edit_object
    if not obj or obj.type != 'MESH':
        raise RuntimeError("Active object must be a mesh in Edit Mode.")

    # Get BMesh and the active UV layer
    bm = bmesh.from_edit_mesh(obj.data)
    uv_layer = bm.loops.layers.uv.verify()

    # Record any currently selected faces, as we don't want to unwrap those faces below. Also untag them.
    initial_faces = []
    for face in bm.faces:
        face.tag = False
        if face.select:
            initial_faces.append(face)

    # Get faces with any selected edges, which we start our flood-fill from.
    face_queue = [face for face in bm.faces if any(edge.select for edge in face.edges)]
    if not face_queue:
        raise RuntimeError("No faces connected to selected edges (or no edges selected).")

    while face_queue:
        face = face_queue.pop()
        if face.tag:
            continue
        face.tag = True
        # Visit face: if each loop has pinned OR zero UV, select the face and visit its connected faces.
        for loop in face.loops:
            if not (loop[uv_layer].pin_uv or is_loop_zero_uv(loop, uv_layer)):
                break  # abandon this face (tagged above)
        else:
            # All loops in this face are either pinned or zero UV. Select the face and visit connected faces.
            face.select = True
            for edge in face.edges:
                for linked_face in edge.link_faces:
                    if not linked_face.tag:
                        face_queue.append(linked_face)

    # Deselect the initial faces so we don't unwrap them.
    for face in initial_faces:
        face.select = False

    bmesh.update_edit_mesh(obj.data)

    return  # TODO

    # Step 4: Unwrap the selected faces. The pinned vertices remain fixed.
#    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)


main()
