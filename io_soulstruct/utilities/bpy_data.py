from __future__ import annotations

__all__ = [
    "new_mesh_object",
    "new_armature_object",
    "new_empty_object",
]

import bpy


def new_mesh_object(
    name: str, data: bpy.types.Mesh | bpy.types.ID | None = None, **props
) -> bpy.types.MeshObject:
    mesh_obj = bpy.data.objects.new(name, data)
    for key, value in props.items():
        mesh_obj[key] = value
    # noinspection PyTypeChecker
    return mesh_obj


def new_armature_object(
    name: str, data: bpy.types.Armature | bpy.types.ID | None = None, **props
) -> bpy.types.ArmatureObject:
    armature_obj = bpy.data.objects.new(name, data)
    for key, value in props.items():
        armature_obj[key] = value
    # noinspection PyTypeChecker
    return armature_obj


def new_empty_object(name: str, **props) -> bpy.types.Object:
    # noinspection PyTypeChecker
    empty_obj = bpy.data.objects.new(name, None)
    for key, value in props.items():
        empty_obj[key] = value
    return empty_obj
