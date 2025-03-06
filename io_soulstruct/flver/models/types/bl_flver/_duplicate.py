"""Implementation of `BlenderFLVER` duplication methods."""
from __future__ import annotations

__all__ = [
    "duplicate_armature",
    "duplicate_dummies",
    "duplicate",
    "duplicate_edit_mode",
]

import typing as tp

import bpy

from io_soulstruct.exceptions import *
from io_soulstruct.types import *
from io_soulstruct.utilities import *

if tp.TYPE_CHECKING:
    from .core import BlenderFLVER


def duplicate_armature(
    bl_flver: BlenderFLVER,
    context: bpy.types.Context,
    child_mesh_obj: bpy.types.MeshObject,
    copy_pose=False,
) -> bpy.types.ArmatureObject:
    if not bl_flver.armature:
        # TODO: Could copy 'implicit Armature' by creating a single-bone Armature with the same name as the model.
        raise FLVERError("No Armature to duplicate for FLVER model.")

    new_armature_obj = new_armature_object(bl_flver.armature.name, data=bl_flver.armature.data.copy())
    for collection in child_mesh_obj.users_collection:
        collection.objects.link(new_armature_obj)
    # No properties taken from Armature.
    context.view_layer.objects.active = new_armature_obj

    if copy_pose:
        # Copy pose bone transforms.
        context.view_layer.update()  # need Blender to create `linked_armature_obj.pose` now
        for new_pose_bone in new_armature_obj.pose.bones:
            source_bone = bl_flver.armature.pose.bones[new_pose_bone.name]
            new_pose_bone.rotation_mode = "QUATERNION"  # should be default but being explicit
            new_pose_bone.location = source_bone.location
            new_pose_bone.rotation_quaternion = source_bone.rotation_quaternion
            new_pose_bone.scale = source_bone.scale

    if child_mesh_obj:
        child_mesh_obj.parent = new_armature_obj
        armature_mod = child_mesh_obj.modifiers.new(name="FLVER Armature", type="ARMATURE")
        armature_mod.object = new_armature_obj
        armature_mod.show_in_editmode = True
        armature_mod.show_on_cage = True

    return new_armature_obj


def duplicate_dummies(bl_flver: BlenderFLVER,) -> list[bpy.types.Object]:
    new_dummies = []
    for dummy in bl_flver.get_dummies():
        new_dummy_obj = new_empty_object(dummy.name)
        new_dummy_obj.soulstruct_type = SoulstructType.FLVER_DUMMY
        copy_obj_property_group(dummy.obj, new_dummy_obj, "flver_dummy")
        for collection in dummy.obj.users_collection:
            collection.objects.link(new_dummy_obj)
        new_dummies.append(new_dummy_obj)

    return new_dummies


def duplicate(
    bl_flver: BlenderFLVER,
    context: bpy.types.Context,
    collections: tp.Sequence[bpy.types.Collection] = None,
    make_materials_single_user=True,
    copy_pose=True,
):
    collections = collections or [context.scene.collection]

    # noinspection PyTypeChecker
    new_mesh_obj = new_mesh_object(bl_flver.mesh.name, bl_flver.mesh.data.copy())
    new_mesh_obj.soulstruct_type = SoulstructType.FLVER
    copy_obj_property_group(bl_flver.mesh, new_mesh_obj, "FLVER")
    for collection in collections:
        collection.objects.link(new_mesh_obj)

    if make_materials_single_user:
        # Duplicate materials.
        for i, mat in enumerate(tuple(new_mesh_obj.data.materials)):
            new_mesh_obj.data.materials[i] = mat.copy()

    if bl_flver.armature:
        new_armature_obj = bl_flver.duplicate_armature(context, new_mesh_obj, copy_pose)
    else:
        new_armature_obj = None

    new_dummies = bl_flver.duplicate_dummies()
    for dummy in new_dummies:
        dummy.parent = new_armature_obj or new_mesh_obj

    return bl_flver.__class__(new_mesh_obj)


def duplicate_edit_mode(
    bl_flver: BlenderFLVER,
    context: bpy.types.Context,
    make_materials_single_user=True,
    copy_pose=True,
) -> BlenderFLVER:
    if context.edit_object != bl_flver.mesh:
        raise FLVERError(f"Mesh of FLVER model '{bl_flver.name}' is not currently being edited in Edit Mode.")

    # Duplicate selected mesh data, then separate it into new object. Note that the `separate` operator will add the
    # new mesh to the same collection(s) automatically.
    bpy.ops.mesh.duplicate()
    bpy.ops.mesh.separate(type="SELECTED")  # new data-block; also copies properties, materials, data layers, etc.

    # noinspection PyTypeChecker
    new_mesh_obj = context.selected_objects[-1]  # type: bpy.types.MeshObject
    if not new_mesh_obj.name.startswith(bl_flver.mesh.name):
        # Tells us that `separate()` was unsuccessful.
        raise FLVERError(f"Could not duplicate and separate selected part of mesh into new object.")

    # Mesh is already added to same collections as this one, but also add to those manually specified (or scene).
    for collection in bl_flver.mesh.users_collection:
        # We'll get an error if we try to add to an existing collection, so check first.
        if collection not in new_mesh_obj.users_collection:
            collection.objects.link(new_mesh_obj)

    if make_materials_single_user:
        # Duplicate materials.
        for i, mat in enumerate(tuple(new_mesh_obj.data.materials)):
            new_mesh_obj.data.materials[i] = mat.copy()

    if bl_flver.armature:
        new_armature_obj = bl_flver.duplicate_armature(context, new_mesh_obj, copy_pose)
    else:
        new_armature_obj = None

    new_dummies = bl_flver.duplicate_dummies()
    for dummy in new_dummies:
        dummy.parent = new_armature_obj or new_mesh_obj

    return bl_flver.__class__(new_mesh_obj)
