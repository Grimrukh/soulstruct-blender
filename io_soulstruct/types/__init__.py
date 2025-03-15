from __future__ import annotations

__all__ = [
    "BaseBlenderSoulstructObject",
    "SOULSTRUCT_T",
    "TYPE_PROPS_T",
    "is_typed_empty_obj",
    "is_typed_mesh_obj",
    "is_active_obj_typed_mesh_obj",
    "are_all_selected_objs_typed_mesh_objs",
    "add_auto_type_props",

    # Convenience imports:
    "ObjectType",
    "SoulstructType",
    "is_mesh_obj",
    "is_armature_obj",
    "is_empty_obj",
]

from .soulstruct_object import *
from .utilities import *
from io_soulstruct.utilities.bpy_types import *  # for convenience
