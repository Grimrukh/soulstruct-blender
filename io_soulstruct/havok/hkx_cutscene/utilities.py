from __future__ import annotations

__all__ = [
    "HKXCutsceneImportError",
    "HKXCutsceneExportError",
]

from mathutils import Euler, Quaternion as BlenderQuaternion
from soulstruct_havok.utilities.maths import Quaternion as GameQuaternion


class HKXCutsceneImportError(Exception):
    """Exception raised during HKX cutscene import."""
    pass


class HKXCutsceneExportError(Exception):
    """Exception raised during HKX cutscene export."""
    pass
