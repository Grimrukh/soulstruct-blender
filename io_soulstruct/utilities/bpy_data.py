"""Functions that find and/or create Blender objects, and copy data between them."""
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

from .misc import get_or_create_collection
from .bpy_types import ObjectType, SoulstructType

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


@tp.overload
def find_obj(
    name: str,
    object_type: tp.Literal[ObjectType.MESH] = None,
    soulstruct_type: SoulstructType | None = None,
    bl_name_func: tp.Callable[[str], str] | None = None,
) -> bpy.types.MeshObject | None:
    ...


@tp.overload
def find_obj(
    name: str,
    object_type: tp.Literal[ObjectType.ARMATURE] = None,
    soulstruct_type: SoulstructType | None = None,
    bl_name_func: tp.Callable[[str], str] | None = None,
) -> bpy.types.ArmatureObject | None:
    ...


@tp.overload
def find_obj(
    name: str,
    object_type: tp.Literal[ObjectType.EMPTY] = None,
    soulstruct_type: SoulstructType | None = None,
    bl_name_func: tp.Callable[[str], str] | None = None,
) -> bpy.types.EmptyObject | None:
    ...


def find_obj(
    name: str,
    object_type: ObjectType | str | None = None,
    soulstruct_type: SoulstructType | None = None,
    bl_name_func: tp.Callable[[str], str] | None = None,
) -> bpy.types.Object | None:
    """Search for a Blender object, optionally restricting its Blender type and/or Soulstruct type.

    If `bl_name_func` is given, objects will have their names passed through it before checking for quality with `name`
    UNLESS an exact name match exists (which should obviously also be a processed match). For example, this function may
    just split at the first space so existing object 'h1234 (Floor).003' can be found with `name = 'h1234'`.
    """
    try:
        obj = bpy.data.objects[name]
        if object_type and obj.type != object_type:
            raise KeyError
        if soulstruct_type and obj.soulstruct_type != soulstruct_type:
            raise KeyError
        return bpy.data.objects[name]
    except KeyError:
        if bl_name_func:
            for obj in bpy.data.objects:
                if object_type and obj.type != object_type:
                    continue
                if soulstruct_type and obj.soulstruct_type != soulstruct_type:
                    continue
                if bl_name_func(obj.name) == name:
                    return obj
    return None


@tp.overload
def find_obj_or_create_empty(
    name: str,
    object_type: tp.Literal[ObjectType.MESH] = None,
    soulstruct_type: SoulstructType | None = None,
    bl_name_func: tp.Callable[[str], str] | None = None,
    missing_collection_name="Missing MSB References",
) -> tuple[bool, bpy.types.MeshObject]:
    ...


@tp.overload
def find_obj_or_create_empty(
    name: str,
    object_type: tp.Literal[ObjectType.ARMATURE] = None,
    soulstruct_type: SoulstructType | None = None,
    bl_name_func: tp.Callable[[str], str] | None = None,
    missing_collection_name="Missing MSB References",
) -> tuple[bool, bpy.types.ArmatureObject]:
    ...


@tp.overload
def find_obj_or_create_empty(
    name: str,
    object_type: tp.Literal[ObjectType.EMPTY] = None,
    soulstruct_type: SoulstructType | None = None,
    bl_name_func: tp.Callable[[str], str] | None = None,
    missing_collection_name="Missing MSB References",
) -> tuple[bool, bpy.types.EmptyObject]:
    ...


def find_obj_or_create_empty(
    name: str,
    object_type: ObjectType | str | None = None,
    soulstruct_type: SoulstructType | None = None,
    bl_name_func: tp.Callable[[str], str] | None = None,
    missing_collection_name="Missing MSB References",
) -> tuple[bool, bpy.types.Object]:
    """Search for a Blender object, optionally restricting its Blender type and/or Soulstruct type.

    If `bl_name_func` is given, objects will have their names passed through it before checking for quality with `name`
    UNLESS an exact name match exists (which should obviously also be a processed match). For example, this function may
    just split at the first space so existing object 'h1234 (Floor).003' can be found with `name = 'h1234'`.

    If object isn't found, create it in collection `missing_collection_name`.

    Returns `(was_created, object)`.
    """
    obj = find_obj(name, object_type, soulstruct_type, bl_name_func)
    if obj:
        return False, obj

    missing_collection = get_or_create_collection(bpy.context.scene.collection, missing_collection_name)
    obj = bpy.data.objects.new(name, None)
    if soulstruct_type:
        obj.soulstruct_type = soulstruct_type
    missing_collection.objects.link(obj)
    return True, obj


def copy_obj_property_group(
    source_obj: bpy.types.Object,
    dest_obj: bpy.types.Object,
    props_name: str,
    filter_func: tp.Callable[[str], bool] | None = None,
):
    """Use annotations of `source_obj.props_name` to copy properties to `dest_obj.props_name`."""
    source_props = getattr(source_obj, props_name)
    dest_props = getattr(dest_obj, props_name)
    for prop_name in source_props.__class__.__annotations__:
        if filter_func and not filter_func(prop_name):
            continue
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
