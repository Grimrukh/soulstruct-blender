from __future__ import annotations

__all__ = [
    "SKELETON_TYPING",
    "ANIMATION_TYPING",
    "read_animation_hkx_entry",
    "read_skeleton_hkx_entry",
    "get_armature_frames",
    "get_root_motion",
    "get_animation_name",
]

import typing as tp

import numpy as np
from pathlib import Path
from soulstruct_havok.core import HKX
from soulstruct_havok.utilities.maths import TRSTransform
from soulstruct_havok.wrappers import hkx2010, hkx2015, hkx2016, hkx2018
from soulstruct_havok.wrappers.hkx2015 import AnimationHKX, SkeletonHKX, ANIBND
from soulstruct.containers import BinderEntry
from io_soulstruct.exceptions import UnsupportedGameError

ANIMATION_TYPING = tp.Union[hkx2015.AnimationHKX, hkx2016.AnimationHKX, hkx2018.AnimationHKX]
SKELETON_TYPING = tp.Union[hkx2015.SkeletonHKX, hkx2016.SkeletonHKX, hkx2018.SkeletonHKX]


def read_animation_hkx_entry(hkx_entry: BinderEntry, compendium: HKX = None) -> ANIMATION_TYPING:
    """Read animation HKX file from a Binder entry and return the appropriate `AnimationHKX` subclass instance."""
    data = hkx_entry.get_uncompressed_data()
    version = data[0x10:0x18]
    if version == b"20180100":  # ER
        hkx = hkx2018.AnimationHKX.from_bytes(data, compendium=compendium)
    elif version == b"20150100":  # DSR
        hkx = hkx2015.AnimationHKX.from_bytes(data, compendium=compendium)
    elif version == b"20160100":  # non-From
        hkx = hkx2016.AnimationHKX.from_bytes(data, compendium=compendium)
    elif data[0x28:0x36] == b"hk_2010.2.0-r1":
        hkx = hkx2010.AnimationHKX.from_bytes(data, compendium=compendium)
    else:
        raise UnsupportedGameError(
            f"Cannot support this HKX animation file version in Soulstruct and/or Blender: {version}"
        )
    hkx.path = Path(hkx_entry.name)
    return hkx


def read_skeleton_hkx_entry(hkx_entry: BinderEntry, compendium: HKX = None) -> SKELETON_TYPING:
    """Read skeleton HKX file from a Binder entry and return the appropriate `SkeletonHKX` subclass instance."""
    data = hkx_entry.get_uncompressed_data()
    version = data[0x10:0x18]
    if version == b"20180100":  # ER
        hkx = hkx2018.SkeletonHKX.from_bytes(data, compendium=compendium)
    elif version == b"20150100":  # DSR
        hkx = hkx2015.SkeletonHKX.from_bytes(data, compendium=compendium)
    elif version == b"20160100":  # non-From
        hkx = hkx2016.SkeletonHKX.from_bytes(data, compendium=compendium)
    elif data[0x28:0x36] == b"hk_2010.2.0-r1":
        hkx = hkx2010.SkeletonHKX.from_bytes(data, compendium=compendium)
    else:
        raise UnsupportedGameError(
            f"Cannot support this HKX skeleton file version in Soulstruct and/or Blender: {version}"
        )
    hkx.path = Path(hkx_entry.name)
    return hkx


def get_armature_frames(
    animation_hkx: AnimationHKX, skeleton_hkx: SkeletonHKX, track_bone_names: list[str]
) -> list[dict[str, TRSTransform]]:
    """Get a list of animation frame dictionaries, which each map bone names to armature-space transforms that frame."""

    # Create ANIBND with just this animation (always using dummy/default ID 0) to get advanced method access.
    anibnd = ANIBND(skeleton_hkx=skeleton_hkx, animations_hkx={0: animation_hkx}, default_anim_id=0)
    arma_frames = []
    for frame_index in range(len(anibnd[0].interleaved_data)):
        track_transforms = anibnd.get_all_armature_space_transforms_in_frame(frame_index)
        # Get dictionary mapping Blender bone names to (game) armature space transforms this frame.
        frame_dict = {}
        for track_index, transform in enumerate(track_transforms):
            bone_name = track_bone_names[track_index]
            frame_dict[bone_name] = transform
        arma_frames.append(frame_dict)
    return arma_frames


def get_root_motion(animation_hkx: AnimationHKX, swap_yz=True) -> np.ndarray | None:
    try:
        root_motion = animation_hkx.animation_container.get_reference_frame_samples()
    except (ValueError, TypeError):
        return None

    if swap_yz:
        # Swap Y and Z axes and negate rotation (now around Z axis). Array is read-only, so we construct a new one.
        root_motion = np.c_[root_motion[:, 0], root_motion[:, 2], root_motion[:, 1], -root_motion[:, 3]]
    return root_motion


def get_animation_name(animation_id: int, template: str, prefix="a"):
    """Takes a template like '##_####' and converts `animation_id` int (e.g. 13000) to a string (e.g. 'a01_3000')."""
    parts = template.split('_')
    string_parts = []
    animation_id = str(animation_id)

    if len(template.replace("_", "")) < len(animation_id):
        raise ValueError(
            f"Animation ID '{animation_id}' is too long for template '{template}'."
        )

    for part in reversed(parts):
        length = len(part)  # number of digits we want to take from the end of the animation ID
        string_parts.append(animation_id[-length:].zfill(length))
        animation_id = animation_id[:-length]

    return prefix + '_'.join(reversed(string_parts))
