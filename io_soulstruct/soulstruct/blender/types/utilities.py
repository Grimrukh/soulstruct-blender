from __future__ import annotations

__all__ = [
    "is_typed_empty_obj",
    "is_typed_mesh_obj",
    "is_active_obj_typed_mesh_obj",
    "are_all_selected_objs_typed_mesh_objs",
    "add_auto_type_props",
]

import typing as tp

import bpy

from soulstruct.blender.utilities.bpy_types import ObjectType, SoulstructType


def is_typed_empty_obj(obj: bpy.types.Object, soulstruct_type: SoulstructType) -> tp.TypeGuard[bpy.types.MeshObject]:
    return obj.type == ObjectType.EMPTY and obj.soulstruct_type == soulstruct_type


def is_typed_mesh_obj(obj: bpy.types.Object, soulstruct_type: SoulstructType) -> tp.TypeGuard[bpy.types.MeshObject]:
    return obj.type == ObjectType.MESH and obj.soulstruct_type == soulstruct_type


def is_active_obj_typed_mesh_obj(context: bpy.types.Context, soulstruct_type: SoulstructType) -> bool:
    return context.active_object and is_typed_mesh_obj(context.active_object, soulstruct_type)


def are_all_selected_objs_typed_mesh_objs(
    context: bpy.types.Context,
    soulstruct_type: SoulstructType,
    allow_no_selection=False,
) -> bool:
    if not context.selected_objects and not allow_no_selection:
        return False  # no objects selected
    return all(is_typed_mesh_obj(obj, soulstruct_type) for obj in context.selected_objects)


def add_auto_type_props(cls, *names):
    for prop_name in names:
        setattr(
            cls, prop_name, property(
                lambda self, pn=prop_name: getattr(self.type_properties, pn),
                lambda self, value, pn=prop_name: setattr(self.type_properties, pn, value),
            )
        )
