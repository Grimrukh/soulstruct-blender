"""Script to update old Blender objects (circa March 2024) to the new properly-typed objects.

Only tested for DS1.

Usage script in Blender:

# INJECT OLD MAP PIECE
import bpy
from soulstruct.blender.utilities.legacy_upgrade import inject_old_flver_mesh

objs = bpy.context.selected_objects
if len(objs) != 2:
    raise ValueError("Must select two objects: the OLD FLVER object to inject and the NEW FLVER object to inject into.")
dest, source = objs

# For safety, assert that `source` is the one WITHOUT a FLVER type.
if source.soulstruct_type == "FLVER":
    raise ValueError(f"Source object {source.name} is already a FLVER object. Please select the old object FIRST.")

inject_old_flver_mesh(source, dest)
print(f"Finished injecting '{source.name}' Mesh data into '{dest.name}' with remapped materials.")
"""
from __future__ import annotations

__all__ = [
    "inject_old_flver_mesh",
]

import bpy

from soulstruct.blender.flver.material import BlenderFLVERMaterial


def get_old_material_props(old_material: bpy.types.Material):
    return dict(
        default_bone_index=old_material["Default Bone Index"],
        # face_set_count=old_material["Face Set Count"],
        flags=old_material["Flags"],
        is_bind_pose=old_material["Is Bind Pose"],
        mat_def_path=old_material["Mat Def Path"],
        unk_x18=old_material["Unk x18"],
    )


def get_new_material_props(new_material: bpy.types.Material):
    bl_material = BlenderFLVERMaterial(new_material)
    return dict(
        default_bone_index=bl_material.default_bone_index,
        # face_set_count=bl_material.face_set_count,
        flags=bl_material.flags,
        is_bind_pose=bl_material.is_bind_pose,
        mat_def_path=bl_material.mat_def_path,
        unk_x18=bl_material.f2_unk_x18,
    )


def inject_old_flver_mesh(old_flver_obj: bpy.types.MeshObject, new_bl_flver: bpy.types.MeshObject):
    """Inject old FLVER mesh data into new FLVER object.

    - Tries to map old materials to new ones on `new_bl_flver`.
    - Completely replaces Mesh datablock in new FLVER with old FLVER.
    - If new FLVER has no Armature:
        - Fine if old FLVER only has one vertex group. We can discard that group (implicit skeleton).
        - Error if old FLVER has more than one vertex group. Not expecting this to ever happen.
    """

    copy_vertex_groups = False
    if not new_bl_flver.parent or new_bl_flver.parent.type != "ARMATURE":
        # Target FLVER has no Armature. Old FLVER must have exactly one vertex group, which can be ignored.
        if len(old_flver_obj.vertex_groups) > 1:
            raise ValueError(
                f"Old FLVER object {old_flver_obj.name} has more than one vertex group, but new FLVER object "
                f"{new_bl_flver.name} has no parent Armature to copy groups to. Cannot proceed."
            )
        # No need to do anything with the old vertex group.
    else:
        # Target FLVER has an Armature. We copy vertex groups, even if only one is present.
        copy_vertex_groups = True

    material_index_map = {}

    if len(old_flver_obj.data.materials) == len(new_bl_flver.data.materials):
        # Easy case: same number of materials. We assume no mapping is needed.
        material_index_map = {i: i for i in range(len(old_flver_obj.material_slots))}
    else:
        # Harder case: we need to match by properties, since the old FLVER material names were stripped.
        # `flags` is probably most useful here. In a pinch, we can also check texture names.
        # Note that multiple old materials can map to the same new material.
        for i, old_mat in enumerate(old_flver_obj.data.materials):
            old_props = get_old_material_props(old_mat)
            for j, new_mat in enumerate(new_bl_flver.data.materials):
                if old_props == get_new_material_props(new_mat):
                    # Also check diffuse texture.
                    old_diffuse_texture = old_mat.node_tree.nodes.get("g_Diffuse").image.name.split(".")[0]
                    # `get()` searches by name, which is still 'g_Diffuse', not 'Main 0 Albedo'.
                    new_diffuse_texture = new_mat.node_tree.nodes.get("g_Diffuse").image.name.split(".")[0]
                    print(old_diffuse_texture, new_diffuse_texture)
                    if old_diffuse_texture == new_diffuse_texture:
                        material_index_map[i] = j
                        print(f"   Matched old material: '{old_mat.name}' -> '{new_mat.name}'.")
                        break
            else:
                raise ValueError(f"Could not find a matching material for old material '{old_mat.name}'.")

    new_materials = new_bl_flver.data.materials  # about to be replaced briefly

    # Now we have a map of old material indices to new material indices. We can inject the mesh data.
    new_bl_flver.data = old_flver_obj.data.copy()

    print(f"Injected old FLVER mesh data into new FLVER object {new_bl_flver.name}.")

    # But keep new materials. Same count, so `material_index_map` values are valid.
    new_bl_flver.data.materials.clear()
    for new_mat in new_materials:
        new_bl_flver.data.materials.append(new_mat)

    # Iterate over mesh faces and remap material indices.
    for old_face, new_face in zip(old_flver_obj.data.polygons, new_bl_flver.data.polygons):
        new_face.material_index = material_index_map[old_face.material_index]
    print("    Remapped material indices.")

    if copy_vertex_groups:
        # Remove old vertex groups.
        new_bl_flver.vertex_groups.clear()

        # Copy vertex groups.
        # TODO: Could probably be faster, as I do at FLVER import (batch add calls by weight).
        #  Not bothering to optimize because I'm not expecting to inject into many Map Pieces with Armatures.
        # TODO: Note that we also assume all bone names are the same, which they should be.
        for i, old_group in enumerate(old_flver_obj.vertex_groups):
            new_group = new_bl_flver.vertex_groups.new(name=old_group.name)
            for vert_index, vert in enumerate(old_flver_obj.data.vertices):
                for group in vert.groups:
                    if group.group == i:
                        new_group.add([vert_index], group.weight, "REPLACE")
        print("    Copied vertex groups.")
    else:
        print("    Discarding single source FLVER vertex group (target FLVER has an implicit skeleton).")
        new_bl_flver.vertex_groups.clear()
