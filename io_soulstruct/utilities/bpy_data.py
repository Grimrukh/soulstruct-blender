from __future__ import annotations

__all__ = [
    "new_mesh_object",
    "new_armature_object",
    "new_empty_object",
    "find_obj",
    "find_obj_or_create_empty",
    "copy_obj_property_group",
    "copy_armature_pose",
]

import typing as tp

import bpy

from io_soulstruct.types import SoulstructType
from .misc import get_bl_obj_tight_name, get_collection

if tp.TYPE_CHECKING:
    PROPS_TYPE = tp.Union[tp.Dict[str, tp.Any], bpy.types.Object, None]


def new_mesh_object(
    name: str, data: bpy.types.Mesh, soulstruct_type: SoulstructType = SoulstructType.NONE
) -> bpy.types.MeshObject:
    mesh_obj = bpy.data.objects.new(name, data)
    mesh_obj.soulstruct_type = soulstruct_type
    # noinspection PyTypeChecker
    return mesh_obj


def new_armature_object(
    name: str,
    data: bpy.types.Armature,
    soulstruct_type: SoulstructType = SoulstructType.NONE,
) -> bpy.types.ArmatureObject:
    armature_obj = bpy.data.objects.new(name, data)
    armature_obj.soulstruct_type = soulstruct_type
    # noinspection PyTypeChecker
    return armature_obj


def new_empty_object(name: str, soulstruct_type: SoulstructType = SoulstructType.NONE) -> bpy.types.Object:
    # noinspection PyTypeChecker
    empty_obj = bpy.data.objects.new(name, None)
    empty_obj.soulstruct_type = soulstruct_type
    return empty_obj


def find_obj(
    name: str,
    find_stem=False,
    soulstruct_type: SoulstructType | None = None,
) -> bpy.types.Object | None:
    try:
        obj = bpy.data.objects[name]
        if soulstruct_type and obj.soulstruct_type != soulstruct_type:
            raise KeyError
        return bpy.data.objects[name]
    except KeyError:
        if find_stem:
            # Try to find an object with the same stem (e.g. "h1234" for "h1234 (Floor).003").
            for obj in bpy.data.objects:
                if get_bl_obj_tight_name(obj) == name and (soulstruct_type and obj.soulstruct_type == soulstruct_type):
                    return obj
    return None


def find_obj_or_create_empty(
    name: str,
    find_stem=False,
    soulstruct_type: SoulstructType | None = None,
    missing_collection_name="Missing MSB References",
) -> tuple[bool, bpy.types.Object]:
    try:
        obj = bpy.data.objects[name]
        if soulstruct_type and obj.soulstruct_type != soulstruct_type:
            raise KeyError
        return False, bpy.data.objects[name]
    except KeyError:
        if find_stem:
            # Try to find an object with the same stem (e.g. "h1234" for "h1234 (Floor).003").
            for obj in bpy.data.objects:
                if get_bl_obj_tight_name(obj) == name and (soulstruct_type and obj.soulstruct_type == soulstruct_type):
                    return False, obj

        missing_collection = get_collection(missing_collection_name, bpy.context.scene.collection)
        obj = bpy.data.objects.new(name, None)
        if soulstruct_type:
            obj.soulstruct_type = soulstruct_type
        missing_collection.objects.link(obj)
        return True, obj


def copy_obj_property_group(source_obj: bpy.types.Object, dest_obj: bpy.types.Object, props_name: str):
    """Use annotations of `source_obj.props_name` to copy properties to `dest_obj.props_name`."""
    source_props = getattr(source_obj, props_name)
    dest_props = getattr(dest_obj, props_name)
    for prop_name in source_props.__annotations__:
        setattr(dest_props, prop_name, getattr(source_props, prop_name))


def copy_armature_pose(source_armature: bpy.types.ArmatureObject, dest_armature: bpy.types.ArmatureObject):
    """Copy pose bone transforms."""

    # Need to ensure Blender creates `linked_armature_obj.pose` first, in case `dest_armature` was only just created.
    bpy.context.view_layer.update()

    for pose_bone in dest_armature.pose.bones:
        source_bone = source_armature.pose.bones[pose_bone.name]
        pose_bone.rotation_mode = "QUATERNION"  # should be default but being explicit
        pose_bone.location = source_bone.location
        pose_bone.rotation_quaternion = source_bone.rotation_quaternion
        pose_bone.scale = source_bone.scale
