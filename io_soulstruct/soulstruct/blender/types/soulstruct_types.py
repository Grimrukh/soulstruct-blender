"""Defines Soulstruct-specific types for Blender objects and collections."""
from __future__ import annotations

__all__ = [
    "SoulstructType",
    "SoulstructCollectionType",
    "is_typed_empty_obj",
    "is_typed_mesh_obj",
    "is_active_obj_typed_mesh_obj",
    "are_all_selected_objs_typed_mesh_objs",
]

import typing as tp
from enum import StrEnum

import bpy

from .bpy_types import *


class SoulstructType(StrEnum):
    """Set on Blender `Object` instances to indicate what kind of Soulstruct object they represent.

    Matches the name of `PropertyGroup` direct properties on `Object` as well (except "NONE").
    """
    NONE = "NONE"  # default; not a Soulstruct object

    FLVER = "FLVER"
    FLVER_DUMMY = "FLVER_DUMMY"

    COLLISION = "COLLISION"

    NAVMESH = "NAVMESH"
    NVM_EVENT_ENTITY = "NVM_EVENT_ENTITY"
    MCG = "MCG"
    MCG_NODE = "MCG_NODE"
    MCG_EDGE = "MCG_EDGE"

    MSB_PART = "MSB_PART"
    MSB_REGION = "MSB_REGION"
    MSB_EVENT = "MSB_EVENT"
    # Used for placeholder MSB models. Real models are FLVER/COLLISION/NAVMESH types.
    MSB_MODEL_PLACEHOLDER = "MSB_MODEL_PLACEHOLDER"


class SoulstructCollectionType(StrEnum):
    """Set on Blender `Collection` instances to indicate what kind of Soulstruct object they represent.

    Matches the name of `PropertyGroup` direct properties on `Collection` as well (except "NONE").
    """
    NONE = "NONE"  # default; not a Soulstruct object

    MSB = "MSB"



def is_typed_empty_obj(obj: bpy.types.Object, soulstruct_type: SoulstructType) -> tp.TypeGuard[MeshObject]:
    return obj.type == ObjectType.EMPTY and obj.soulstruct_type == soulstruct_type


def is_typed_mesh_obj(obj: bpy.types.Object, soulstruct_type: SoulstructType) -> tp.TypeGuard[MeshObject]:
    return obj.type == ObjectType.MESH and obj.soulstruct_type == soulstruct_type


def is_active_obj_typed_mesh_obj(context: bpy.types.Context, soulstruct_type: SoulstructType) -> bool:
    return context.active_object and is_typed_mesh_obj(context.active_object, soulstruct_type)


def are_all_selected_objs_typed_mesh_objs(
    context: bpy.types.Context,
    soulstruct_type: SoulstructType,
    allow_no_selection=False,
) -> bool:
    """Return True if all selected objects are Mesh objects with the given Soulstruct type.

    If `allow_no_selection` is False, return False if no objects are selected.
    """
    if not context.selected_objects and not allow_no_selection:
        return False  # no objects selected
    return all(is_typed_mesh_obj(obj, soulstruct_type) for obj in context.selected_objects)
