from __future__ import annotations

__all__ = [
    "ArmatureObject",
    "CameraObject",
    "EmptyObject",
    "MeshObject",
    "ObjectType",
    "is_empty_obj",
    "is_armature_obj",
    "is_mesh_obj",
    "is_camera_obj",
]

import typing as tp
from enum import StrEnum

import bpy


class ArmatureObject(bpy.types.Object):
    data: bpy.types.Armature


class CameraObject(bpy.types.Object):
    data: bpy.types.Camera


class EmptyObject(bpy.types.Object):
    data: None


class MeshObject(bpy.types.Object):
    data: bpy.types.Mesh


class ObjectType(StrEnum):
    """Enum wrapper for Blender's `bpy.types.Object.type` property. Only Soulstruct-relevant values are supported."""
    ARMATURE = "ARMATURE"
    CAMERA = "CAMERA"
    EMPTY = "EMPTY"
    MESH = "MESH"


def is_armature_obj(obj: bpy.types.Object) -> tp.TypeGuard[ArmatureObject]:
    return obj.type == ObjectType.ARMATURE


def is_camera_obj(obj: bpy.types.Object) -> tp.TypeGuard[CameraObject]:
    return obj.type == ObjectType.CAMERA


def is_empty_obj(obj: bpy.types.Object) -> tp.TypeGuard[bpy.types.Object]:
    return obj.type == ObjectType.EMPTY


def is_mesh_obj(obj: bpy.types.Object) -> tp.TypeGuard[MeshObject]:
    return obj.type == ObjectType.MESH
