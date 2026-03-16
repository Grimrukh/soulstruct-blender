from __future__ import annotations

__all__ = [
    "ArmatureObject",
    "CameraObject",
    "EmptyObject",
    "MeshObject",
    "ObjectType",
    "is_mesh_obj",
    "is_armature_obj",
    "is_empty_obj",

    "SoulstructType",
    "SoulstructCollectionType",
    "is_typed_empty_obj",
    "is_typed_mesh_obj",
    "is_active_obj_typed_mesh_obj",
    "are_all_selected_objs_typed_mesh_objs",
]

from .bpy_types import *
from .soulstruct_types import *
