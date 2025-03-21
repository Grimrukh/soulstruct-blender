from __future__ import annotations

__all__ = [
    "ObjectType",
    "SoulstructType",
    "SoulstructCollectionType",
    "is_mesh_obj",
    "is_armature_obj",
    "is_empty_obj",
]

import typing as tp
from enum import StrEnum

import bpy


class ObjectType(StrEnum):
    """Enum wrapper for Blender's `bpy.types.Object.type` property. Only Soulstruct-relevant values are supported."""
    MESH = "MESH"
    ARMATURE = "ARMATURE"
    EMPTY = "EMPTY"


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


def is_mesh_obj(obj: bpy.types.Object) -> tp.TypeGuard[bpy.types.MeshObject]:
    return obj.type == ObjectType.MESH


def is_armature_obj(obj: bpy.types.Object) -> tp.TypeGuard[bpy.types.ArmatureObject]:
    return obj.type == ObjectType.ARMATURE


def is_empty_obj(obj: bpy.types.Object) -> tp.TypeGuard[bpy.types.Object]:
    return obj.type == ObjectType.EMPTY
