from __future__ import annotations

__all__ = [
    "find_flver_model",
]

import bpy

from io_soulstruct.exceptions import FLVERError, MissingPartModelError
from io_soulstruct.flver.models import BlenderFLVER
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import find_obj


def find_flver_model(model_name: str) -> BlenderFLVER:
    """Find the model of the given type in a 'Models' collection in the current scene.

    Used by Map Pieces, Collisions, and Navmeshes (assets stored per map).
    """
    model = find_obj(name=model_name, find_stem=True, soulstruct_type=SoulstructType.FLVER)
    if model is None:
        raise MissingPartModelError(f"FLVER model '{model_name}' not found in Blender data.")
    try:
        return BlenderFLVER(model)
    except FLVERError:
        raise MissingPartModelError(f"Blender object '{model_name}' is not a valid FLVER model mesh.")
