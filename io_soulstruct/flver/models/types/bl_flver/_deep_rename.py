from __future__ import annotations

__all__ = [
    "deep_rename",
]

import typing as tp

from io_soulstruct.utilities import remove_dupe_suffix

if tp.TYPE_CHECKING:
    from .core import BlenderFLVER


def deep_rename(bl_flver: BlenderFLVER, new_name: str, old_name=""):
    """Rename all components of given FLVER object (Armature, Mesh, materials, bones, dummies):

    The FLVER model name appears in numerous places in different ways throughout the object hierarchy. By default,
    names are processed by this method as though they conform to standard imported templates:

    - If Armature exists, it is named `new_name` and Mesh child is named `{new_name} Mesh`.
        - Otherwise, root Mesh is named `new_name`.
    - Each Dummy has its `model_name` name component replaced with `new_name`.
    - Each Material and Bone has a full `str.replace()` of current model `name` with `new_name`.
        - If only a single default origin bone exists, its name is set to `new_name` directly.

    The data-blocks of Armature (if present) and Mesh are ONLY renamed if they CURRENTLY match the name of the
    Armature/Mesh object itself, which indicates that they are true models and not just MSB Part instances.

    You can pass `old_name` to do the renaming as though its current name was `old_name`.

    Blender's duplicate suffix, e.g. '.001', is stripped prior to the renaming of all components.
    """

    old_name = old_name or bl_flver.export_name

    if bl_flver.armature:
        bl_flver.armature.name = f"{new_name} Armature"
        bl_flver.armature.data.name = f"{new_name} Armature"
    bl_flver.mesh.name = new_name
    bl_flver.mesh.data.name = new_name

    for mat in bl_flver.mesh.data.materials:
        # Replace all string occurrences.
        old_mat_name = remove_dupe_suffix(mat.name)
        mat.name = old_mat_name.replace(old_name, new_name)

    if bl_flver.armature:
        bone_renaming = {}
        for bone in bl_flver.armature.data.bones:
            # Replace all string occurrences.
            old_bone_name = remove_dupe_suffix(bone.name)
            bone.name = bone_renaming[bone.name] = old_bone_name.replace(old_name, new_name)
        # Vertex group names need to be updated manually, unlike when you edit bone names in the GUI.
        for vertex_group in bl_flver.mesh.vertex_groups:
            if vertex_group.name in bone_renaming:
                vertex_group.name = bone_renaming[vertex_group.name]
        for dummy in bl_flver.get_dummies():
            dummy.model_name = new_name
            dummy.update_parent_bone_name(bone_renaming)
