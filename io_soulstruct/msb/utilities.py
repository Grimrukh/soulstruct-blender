from __future__ import annotations

__all__ = [
    "find_flver_model",
]

import bpy

from io_soulstruct.exceptions import FLVERError, MissingPartModelError
from io_soulstruct.flver.types import BlenderFLVER
from .properties import MSBPartSubtype


def find_flver_model(part_subtype: MSBPartSubtype, model_name: str) -> BlenderFLVER:
    """Find the model of the given type in a 'Models' collection in the current scene.

    Used by Map Pieces, Collisions, and Navmeshes (assets stored per map).
    """
    collection_name = f"{part_subtype.value} Models"
    try:
        collection = bpy.data.collections[collection_name]
    except KeyError:
        raise MissingPartModelError(f"Collection '{collection_name}' not found in Blender data.")
    for obj in collection.objects:
        if obj.name == model_name:
            try:
                return BlenderFLVER.from_bl_obj(obj)
            except FLVERError:
                raise MissingPartModelError(f"Blender object '{model_name}' is not a valid FLVER model.")
    raise MissingPartModelError(f"Model '{model_name}' not found in '{part_subtype.value} Models' collection.")
