from __future__ import annotations

__all__ = [
    "new_mesh_object",
    "new_armature_object",
    "new_empty_object",
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
