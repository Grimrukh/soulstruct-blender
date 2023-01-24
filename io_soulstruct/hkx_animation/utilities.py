from __future__ import annotations

__all__ = [
    "HKXAnimationImportError",
    "HKXAnimExportError",
    "FL_TO_BL_QUAT",
]

from mathutils import Euler, Quaternion as BlenderQuaternion
from soulstruct_havok.utilities.maths import Quaternion as GameQuaternion


class HKXAnimationImportError(Exception):
    """Exception raised during HKX animation import."""
    pass


class HKXAnimExportError(Exception):
    """Exception raised during HKX animation export."""
    pass


def FL_TO_BL_QUAT(quaternion: GameQuaternion) -> BlenderQuaternion:
    """NOTE: Blender Euler rotation mode should be 'XYZ' (corresponding to game 'XZY')."""
    # TODO: There must be a way to modify a quaternion in a way that is equivalent to negating all three Euler angles
    #  (and swapping Y and Z), but I can't find it.
    game_euler = quaternion.to_euler_angles(radians=True)
    bl_euler = Euler((-game_euler.x, -game_euler.z, -game_euler.y))
    return bl_euler.to_quaternion()
