from __future__ import annotations

__all__ = [
    "HKXAnimationImportError",
    "HKXAnimExportError",
    "FL_TO_BL_QUAT",
    "get_armature_frames",
    "get_root_motion",
]

from mathutils import Euler, Quaternion as BlenderQuaternion
from soulstruct_havok.utilities.maths import Quaternion as GameQuaternion

from soulstruct_havok.wrappers.hkx2015 import AnimationHKX, SkeletonHKX, ANIBND


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


def get_armature_frames(animation_hkx: AnimationHKX, skeleton_hkx: SkeletonHKX, track_bone_names: list[str]):
    """Get a list of animation frame dictionaries, which each map bone names to armature-space transforms that frame."""
    anibnd = ANIBND(skeleton_hkx=skeleton_hkx, animations_hkx={0: animation_hkx})
    world_frames = []
    for frame_index in range(len(anibnd[0].interleaved_data)):
        track_transforms = anibnd.get_all_armature_space_transforms_in_frame(frame_index)
        # Get dictionary mapping Blender bone names to (game) armature space transforms this frame.
        frame_dict = {track_bone_names[i]: transform for i, transform in enumerate(track_transforms)}
        world_frames.append(frame_dict)
    return world_frames


def get_root_motion(animation_hkx: AnimationHKX):
    try:
        return animation_hkx.animation_container.get_reference_frame_samples()
    except TypeError:
        return None
