__all__ = ["inject_flver_content"]

import re
import shutil

import bmesh
import bpy
# noinspection PyUnresolvedReferences
import mathutils

from soulstruct.base.models.flver import FLVER
from soulstruct.utilities.maths import Vector3

MESH_RE = re.compile(r"(.*) Mesh (\d+) Obj")
NAME_RE = re.compile(r"FLVER (.*)")

DEBUG_MESH_INDEX = None
DEBUG_VERTEX_INDICES = []


def inject_mesh(
    mesh: FLVER.Mesh,
    bl_mesh_obj: bpy.types.Object,
    layout_semantics,
    face_set_count: int,
    mesh_index=-1,
):
    """Create new FLVER vertices and face sets and inject them into given existing FLVER `mesh`.

    Uses a new, much simpler algorithm for ensuring that any Blender face loops with divergent UVs/vertex colors become
    unique FLVER vertices (as FLVER does not support the concept of "loops" that can map a given vertex to multiple
    different UVs for each face it is part of).
    """
    uv_count = len(mesh.vertices[0].uvs)
    bl_mesh = bl_mesh_obj.data
    mesh_vertex_groups = bl_mesh_obj.vertex_groups

    mesh.vertices.clear()  # FLVER vertices are created as new Blender loops are encountered

    bl_mesh.calc_normals_split()  # TODO: I think `calc_tangents` calls this automatically.
    try:
        bl_mesh.calc_tangents(uvmap="UVMap1")
    except RuntimeError:
        # TODO: should I ever use UVMap2?
        # try:
        #     bl_mesh.calc_tangents(uvmap="UVMap2")
        # except RuntimeError:
        raise RuntimeError("Could not find UVMap1 or UVMap2. If this mesh is empty, delete it.")

    # Temporary BMesh is triangulated, but is never saved back to Blender.
    bm = bmesh.new()
    bm.from_mesh(bl_mesh)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    flver_indices = {}

    # TODO: Import/export actual 'cull back faces' setting into and out of Blender for each mesh.
    #  For now, just copying the setting from the first existing face set of the mesh being injected into.
    try:
        cull_back_faces = mesh.face_sets[0].cull_back_faces
    except IndexError:
        print(
            "WARNING: Mesh being injected into had no existing face sets to check `cull_back_faces`. "
            "Defaulting to `True`."
        )
        cull_back_faces = True

    mesh.face_sets = [
        mesh.FaceSet(flags=i, unk_x06=0, triangle_strip=False, cull_back_faces=cull_back_faces, vertex_indices=[])
        for i in range(face_set_count)
    ]

    # NOTE: Vertices that do not appear in any Blender faces will NOT be exported.
    triangles = bm.calc_loop_triangles()

    # noinspection PyTypeChecker
    for f_i, face in enumerate(triangles):
        flver_face = []
        for loop in face:
            v_i = loop.vert.index
            mesh_loop = bl_mesh.loops[loop.index]

            if "Position" in layout_semantics:
                position = blender_vec_to_flver_vec(bm.verts[v_i].co)
            else:
                position = None

            if "BoneIndices" in layout_semantics:  # implies "BoneWeights" as well
                bl_v = bl_mesh.vertices[v_i]
                bone_indices = []
                for vertex_group in bl_v.groups:  # generally only one for map pieces
                    for mesh_group in mesh_vertex_groups:
                        if vertex_group.group == mesh_group.index:
                            bone_indices.append(mesh_group.index)
                            break
                if len(bone_indices) > 4:
                    raise ValueError(f"Vertex has too many bones ({len(bone_indices)} > 4).")
                if len(bone_indices) == 1:
                    bone_indices *= 4  # duplicate single-element list to four-element list
                # TODO: Bone weights currently left as zero (correct for map pieces in general).
            else:
                bone_indices = None

            if "Normal" in layout_semantics:
                # TODO: 127 is the only value seen in map pieces thus far for `normal[3]`. Check other FLVER types.
                normal = [blender_vec_to_flver_vec(mesh_loop.normal), 127.0]
            else:
                normal = None

            # Get UVs from loop. We always need to do this because even if the vertex has already been filled, we need
            # to check if this loop has different UVs and create a duplicate vertex if so.
            if "UV" in layout_semantics:
                uvs = []
                for uv_index in range(1, uv_count + 1):
                    bl_uv = bl_mesh.uv_layers[f"UVMap{uv_index}"].data[loop.index].uv
                    uvs.append([bl_uv[0], -bl_uv[1], 0.0])  # FLVER UV always has Z coordinate (usually 0)
            else:
                uvs = None

            if "Tangent" in layout_semantics:
                tangents = [[*blender_vec_to_flver_vec(mesh_loop.tangent), -1.0]]
            else:
                tangents = None

            if "Bitangent" in layout_semantics:
                bitangent = [*blender_vec_to_flver_vec(mesh_loop.bitangent), -1.0]
            else:
                bitangent = None

            # Same with vertex colors. Though they are stored as a list, there should always only be one color layer.
            if "VertexColor" in layout_semantics:
                # TODO: list conversion may be redundant (check Blender type)
                colors = [list(bl_color) for bl_color in [bl_mesh.vertex_colors["VertexColors"].data[loop.index].color]]
            else:
                colors = None

            v_key = (tuple(position), tuple(uvs), tuple(colors))  # hashable
            try:
                fl_v_i = flver_indices[v_key]
            except KeyError:
                # Create new `Vertex`.
                fl_v_i = flver_indices[v_key] = len(flver_indices)
                mesh.vertices.append(FLVER.Mesh.Vertex(
                    position=position,
                    # TODO: Bone weights currently left as zero (correct for map pieces in general).
                    #  Obviously won't work for characters/objects.
                    bone_weights=[0.0, 0.0, 0.0, 0.0],
                    bone_indices=bone_indices,
                    normal=normal,
                    uvs=uvs,
                    tangents=tangents,
                    bitangent=bitangent,
                    colors=colors,
                ))
            flver_face.append(fl_v_i)

        mesh.face_sets[0].vertex_indices += flver_face

    for lod_face_set in mesh.face_sets[1:]:
        lod_face_set.vertex_indices = mesh.face_sets[0].vertex_indices.copy()


def recompute_bounding_box(flver: FLVER, bones: list[FLVER.Bone]):
    """Update bounding box min/max for `flver.header` and all bones in `bones`."""
    x = [v.position.x for mesh in flver.meshes for v in mesh.vertices]
    y = [v.position.y for mesh in flver.meshes for v in mesh.vertices]
    z = [v.position.z for mesh in flver.meshes for v in mesh.vertices]
    if x or y or z:
        bb_min = Vector3(min(x), min(y), min(z))
        bb_max = Vector3(max(x), max(y), max(z))
    else:
        # No vertex data in ANY mesh. Highly suspect, obviously.
        bb_min = Vector3.zero()
        bb_max = Vector3.zero()
    flver.header.bounding_box_min = bb_min
    flver.header.bounding_box_max = bb_max
    for bone in bones:
        bone.bounding_box_min = bb_min
        bone.bounding_box_max = bb_max


def inject_flver_content(parent_obj, flver_path):
    """Updates FLVER bones, meshes, and materials from child objects of parent FLVER object.

    Automatically renumbers mesh child objects in Blender according to their new index in the FLVER (e.g. if some meshes
    were deleted in Blender).

    TODO: Currently cannot add new meshes, because they need a vertex buffer layout assigned that I don't support yet.
    """
    parent_match = NAME_RE.match(parent_obj.name)
    if not parent_match:
        raise ValueError(f"Name of selected FLVER object should be 'FLVER {{name}}', not '{parent_obj.name}'.")
    flver_name = parent_match.group(1)

    child_objs = [obj for obj in bpy.data.objects if obj.parent is parent_obj]
    flver = FLVER(flver_path)

    # TODO: Inject Bones and Materials.

    new_meshes = []

    for mesh_index, mesh in enumerate(flver.meshes):
        if mesh_index not in {-1, mesh_index}:
            continue  # skip mesh

        if len(mesh.vertex_buffers) != 1:
            raise ValueError(f"Can only inject into meshes with one vertex buffer (mesh {mesh_index}).")
        bl_mesh = find_mesh_child(child_objs, flver_name, mesh_index=mesh_index)
        if bl_mesh is None:
            continue  # don't add to new meshes

        layout = flver.buffer_layouts[mesh.vertex_buffers[0].layout_index]
        layout_semantics = [member.semantic.name for member in layout]
        print(f"Injecting mesh index {mesh_index}...")
        inject_mesh(mesh, bl_mesh, layout_semantics, int(bl_mesh["Face Set Count"]), mesh_index)

        new_meshes.append(mesh)

        # Update Blender mesh name index.
        bl_mesh.name = f"{flver_name} Mesh {len(new_meshes) - 1} Obj"
        bl_mesh.data.name = f"{flver_name} Mesh {len(new_meshes) - 1} Data"

    flver.meshes = new_meshes
    # TODO: Updates all bones by default (correct for most DS1 map pieces).
    #  Models with multiple bones may have excessively large per-bone BBs for now.
    #  To handle it properly, for each bone, I need to get the min/max points of all vertices using that bone,
    #  presumably.
    recompute_bounding_box(flver, flver.bones)
    flver_bak_path = flver.path.with_suffix(flver.path.suffix + ".bak")
    if not flver_bak_path.is_file():
        shutil.copy2(flver.path, flver_bak_path)
    flver.write()
    print(f"FLVER written: {flver.path}")


def blender_vec_to_flver_vec(bl_vec) -> list[float]:
    return [-bl_vec.x, bl_vec.z, -bl_vec.y]


def find_mesh_child(child_objs, flver_name: str, mesh_index: int):
    mesh_index_str = str(mesh_index)
    for obj in child_objs:
        mesh_match = MESH_RE.match(obj.name)
        if mesh_match and mesh_match.group(1) == flver_name and mesh_match.group(2) == mesh_index_str:
            return obj
    return None  # not found
