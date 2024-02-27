from __future__ import annotations

__all__ = ["create_animation_hkx"]

import numpy as np

import bpy

from soulstruct_havok.wrappers.hkx2015 import SkeletonHKX, AnimationHKX
from soulstruct_havok.utilities.maths import TRSTransform

from io_soulstruct.havok.utilities import BL_MATRIX_TO_GAME_TRS
from io_soulstruct.havok.hkx_animation.utilities import *


def create_animation_hkx(skeleton_hkx: SkeletonHKX, bl_armature, from_60_fps: bool) -> AnimationHKX:
    if bl_armature.animation_data is None:
        raise HKXAnimationExportError(f"Armature '{bl_armature.name}' has no animation data.")
    action = bl_armature.animation_data.action
    if action is None:
        raise HKXAnimationExportError(f"Armature '{bl_armature.name}' has no action assigned to its animation data.")

    # TODO: Technically, animation export only needs a start/end frame range, since it samples location/bone pose
    #  on every single frame anyway and does NOT need to actually use the action FCurves!

    # Determine the frame range.
    # TODO: Export bool option to just read from current scene values, rather than checking action.
    start_frame = int(min(fcurve.range()[0] for fcurve in action.fcurves))
    end_frame = int(max(fcurve.range()[1] for fcurve in action.fcurves))

    # All frame interleaved transforms, in armature space.
    root_motion_samples = []  # type: list[tuple[float, float, float, float]]
    armature_space_frames = []  # type: list[list[TRSTransform]]

    has_root_motion = False

    # Animation track order will match Blender bone order (which should come from FLVER).
    track_bone_mapping = list(range(len(skeleton_hkx.skeleton.bones)))

    # Store last bone TRS for rotation negation.
    last_bone_trs = {bone.name: TRSTransform.identity() for bone in skeleton_hkx.skeleton.bones}

    # Evaluate all curves at every frame.
    for i, frame in enumerate(range(start_frame, end_frame + 1)):

        if from_60_fps and i % 2 == 1:
            # Skip every second frame to convert 60 FPS to 30 FPS (frame 0 should generally be keyframed).
            continue

        bpy.context.scene.frame_set(frame)
        armature_space_frame = []  # type: list[TRSTransform]

        # We collect root motion vectors, as we're not sure if any root motion exists yet.
        loc = bl_armature.location
        rot = bl_armature.rotation_euler
        root_motion_sample = (loc[0], loc[1], loc[2], rot[2])  # XYZ and Z rotation (soon to be game Y)
        root_motion_samples.append(root_motion_sample)
        if not has_root_motion and len(root_motion_samples) >= 2 and root_motion_samples[-1] != root_motion_samples[-2]:
            # Some actual root motion has appeared.
            has_root_motion = True

        for bone in skeleton_hkx.skeleton.bones:
            try:
                bl_bone = bl_armature.pose.bones[bone.name]
            except KeyError:
                raise HKXAnimationExportError(f"Bone '{bone.name}' in HKX skeleton not found in Blender armature.")
            armature_space_transform = BL_MATRIX_TO_GAME_TRS(bl_bone.matrix)
            if i > 0:
                # Negate rotation quaternion if dot product is negative.
                dot = np.dot(armature_space_transform.rotation.data, last_bone_trs[bone.name].rotation.data)
                if dot < 0:
                    armature_space_transform.rotation = -armature_space_transform.rotation
            last_bone_trs[bone.name] = armature_space_transform
            armature_space_frame.append(armature_space_transform)

        armature_space_frames.append(armature_space_frame)

    if has_root_motion:
        root_motion = np.array(root_motion_samples, dtype=np.float32)
        # Swap Y and Z and negate rotation.
        root_motion = np.c_[root_motion[:, 0], root_motion[:, 2], root_motion[:, 1], -root_motion[:, 3]]
    else:
        root_motion = None

    animation_hkx = AnimationHKX.from_dsr_interleaved_template(
        skeleton_hkx=skeleton_hkx,
        interleaved_data=armature_space_frames,
        transform_track_to_bone_indices=track_bone_mapping,
        root_motion=root_motion,
        is_armature_space=True,
    )

    return animation_hkx
