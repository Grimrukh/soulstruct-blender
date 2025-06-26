"""Advanced/convenience functions for interacting with Blender's `context`."""
from __future__ import annotations

__all__ = []

import typing as tp

import bpy
from bpy.types import Context

from soulstruct.blender.exceptions import ObjectTypeError
from .bpy_types import ObjectType


@tp.overload
def get_active_obj(context: Context, obj_type: tp.Literal[ObjectType.MESH]) -> bpy.types.MeshObject:
    ...


@tp.overload
def get_active_obj(context: Context, obj_type: tp.Literal[ObjectType.ARMATURE]) -> bpy.types.ArmatureObject:
    ...


@tp.overload
def get_active_obj(context: Context, obj_type: tp.Literal[ObjectType.EMPTY]) -> bpy.types.Object:
    ...


def get_active_obj(context: Context, obj_type: ObjectType = None) -> bpy.types.Object:
    """Get the active object in the given context, optionally asserting that it is of the expected Object type.

    Raises a ValueError if there is no active object in the context.
    Raises a TypeError if the active object is not of the expected type.
    """
    active_obj = context.active_object
    if active_obj is None:
        raise ValueError("No active object in context.")
    if obj_type is not None and active_obj.type != obj_type:
        raise ObjectTypeError(f"Active object is not of expected type {obj_type.name}.")
    return active_obj
