from __future__ import annotations

__all__ = [
    "new_mesh_object",
    "new_armature_object",
    "new_empty_object",
    "find_obj_or_create_empty",
    "copy_obj_property_group",
    "copy_armature_pose",
]

import typing as tp

import bpy

if tp.TYPE_CHECKING:
    PROPS_TYPE = tp.Union[tp.Dict[str, tp.Any], bpy.types.Object, None]


def new_mesh_object(
    name: str, data: bpy.types.Mesh | bpy.types.ID | None = None, props: PROPS_TYPE = None
) -> bpy.types.MeshObject:
    mesh_obj = bpy.data.objects.new(name, data)
    if props:
        for key, value in props.items():
            mesh_obj[key] = value
    # noinspection PyTypeChecker
    return mesh_obj


def new_armature_object(
    name: str, data: bpy.types.Armature | bpy.types.ID | None = None, props: PROPS_TYPE = None
) -> bpy.types.ArmatureObject:
    armature_obj = bpy.data.objects.new(name, data)
    if props:
        for key, value in props.items():
            armature_obj[key] = value
    # noinspection PyTypeChecker
    return armature_obj


def new_empty_object(name: str, props: PROPS_TYPE = None) -> bpy.types.Object:
    # noinspection PyTypeChecker
    empty_obj = bpy.data.objects.new(name, None)
    if props:
        for key, value in props.items():
            empty_obj[key] = value
    return empty_obj


def find_obj_or_create_empty(name: str) -> tuple[bool, bpy.types.Object]:
    try:
        return False, bpy.data.objects[name]
    except KeyError:
        obj = bpy.data.objects.new(name, None)
        bpy.context.scene.collection.objects.link(obj)
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
