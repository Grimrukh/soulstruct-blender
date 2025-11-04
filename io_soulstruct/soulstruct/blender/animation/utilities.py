from __future__ import annotations

__all__ = [
    "SKELETON_TYPING",
    "ANIMATION_TYPING",
    "read_animation_hkx_entry",
    "read_skeleton_hkx_entry",
    "get_armature_frames",
    "get_root_motion",
    "get_animation_name",
    "get_active_flver_or_part_armature",
]

import typing as tp
from pathlib import Path

import bpy

import numpy as np

from soulstruct.havok.core import HKX
from soulstruct.havok.utilities.maths import TRSTransform
from soulstruct.havok.fromsoft.base import BaseAnimationHKX, BaseSkeletonHKX
from soulstruct.havok.fromsoft import demonssouls, darksouls1ptde, darksouls1r, bloodborne, eldenring
from soulstruct.containers import BinderEntry

from soulstruct.blender.exceptions import UnsupportedGameError, SoulstructTypeError
from soulstruct.blender.flver.models.types import BlenderFLVER
from soulstruct.blender.msb.properties.parts import BlenderMSBPartSubtype
from soulstruct.blender.msb.types.base.parts import BaseBlenderMSBPart
from soulstruct.blender.utilities import get_model_name

ANIMATION_TYPING = tp.Union[
    demonssouls.AnimationHKX,
    darksouls1ptde.AnimationHKX,
    darksouls1r.AnimationHKX,
    bloodborne.AnimationHKX,
    eldenring.AnimationHKX,
]
SKELETON_TYPING = tp.Union[
    demonssouls.SkeletonHKX,
    darksouls1ptde.SkeletonHKX,
    darksouls1r.SkeletonHKX,
    bloodborne.SkeletonHKX,
    eldenring.SkeletonHKX,
]


def read_animation_hkx_entry(hkx_entry: BinderEntry, compendium: HKX = None) -> ANIMATION_TYPING:
    """Read animation HKX file from a Binder entry and return the appropriate `AnimationHKX` subclass instance."""
    data = hkx_entry.get_uncompressed_data()
    packfile_version = data[0x28:0x38]
    tagfile_version = data[0x10:0x18]
    if packfile_version.startswith(b"Havok-4.5.0-r1"):  # DeS (c9900)
        hkx = demonssouls.AnimationHKX.from_bytes(data, compendium=compendium)
    elif packfile_version.startswith(b"Havok-5.5.0-r1"):  # DeS
        hkx = demonssouls.AnimationHKX.from_bytes(data, compendium=compendium)
    elif packfile_version.startswith(b"hk_2010.2.0-r1"):  # PTDE
        hkx = darksouls1ptde.AnimationHKX.from_bytes(data, compendium=compendium)
    elif tagfile_version == b"20150100":  # DSR
        hkx = darksouls1r.AnimationHKX.from_bytes(data, compendium=compendium)
    elif packfile_version.startswith(b"hk_2014.1.0-r1"):  # BB
        hkx = bloodborne.AnimationHKX.from_bytes(data, compendium=compendium)
    elif tagfile_version == b"20180100":  # ER
        hkx = eldenring.AnimationHKX.from_bytes(data, compendium=compendium)
    else:
        raise UnsupportedGameError(
            f"Cannot support this HKX skeleton file version in Soulstruct and/or Blender.\n"
            f"   Possible packfile version: {packfile_version}\n"
            f"   Possible tagfile version: {tagfile_version}"
        )
    hkx.path = Path(hkx_entry.name)
    return hkx


def read_skeleton_hkx_entry(hkx_entry: BinderEntry, compendium: HKX = None) -> SKELETON_TYPING:
    """Read skeleton HKX file from a Binder entry and return the appropriate `SkeletonHKX` subclass instance."""
    data = hkx_entry.get_uncompressed_data()
    packfile_version = data[0x28:0x38]
    tagfile_version = data[0x10:0x18]
    if packfile_version.startswith(b"Havok-4.5.0-r1"):  # DeS (c9900)
        hkx = demonssouls.SkeletonHKX.from_bytes(data, compendium=compendium)
    elif packfile_version.startswith(b"Havok-5.5.0-r1"):  # DeS
        hkx = demonssouls.SkeletonHKX.from_bytes(data, compendium=compendium)
    elif packfile_version.startswith(b"hk_2010.2.0-r1"):  # PTDE
        hkx = darksouls1ptde.SkeletonHKX.from_bytes(data, compendium=compendium)
    elif tagfile_version == b"20150100":  # DSR
        hkx = darksouls1r.SkeletonHKX.from_bytes(data, compendium=compendium)
    elif packfile_version.startswith(b"hk_2014.1.0-r1"):  # BB
        hkx = bloodborne.SkeletonHKX.from_bytes(data, compendium=compendium)
    elif tagfile_version == b"20180100":  # ER
        hkx = eldenring.SkeletonHKX.from_bytes(data, compendium=compendium)
    else:
        raise UnsupportedGameError(
            f"Cannot support this HKX skeleton file version in Soulstruct and/or Blender.\n"
            f"   Possible packfile version: {packfile_version}\n"
            f"   Possible tagfile version: {tagfile_version}"
        )
    hkx.path = Path(hkx_entry.name)
    return hkx


def get_root_motion(animation_hkx: BaseAnimationHKX, swap_yz=True) -> np.ndarray | None:
    try:
        root_motion = animation_hkx.animation_container.get_reference_frame_samples()
    except (ValueError, TypeError):
        return None

    if swap_yz:
        # Swap Y and Z axes and negate rotation (now around Z axis). Array is read-only, so we construct a new one.
        root_motion = np.c_[root_motion[:, 0], root_motion[:, 2], root_motion[:, 1], -root_motion[:, 3]]
    return root_motion


def get_armature_frames(
    animation_hkx: BaseAnimationHKX, skeleton_hkx: BaseSkeletonHKX
) -> list[dict[str, TRSTransform]]:
    """Get a list of animation frame dictionaries, which each map bone names to armature-space transforms that frame."""

    # Get track bone names.
    track_bone_indices = animation_hkx.animation_container.get_track_bone_indices()
    track_bone_names = [skeleton_hkx.skeleton.bones[i].name for i in track_bone_indices]

    # Get frames as standard nested lists of transforms.
    interleaved_frames = animation_hkx.animation_container.get_interleaved_data_in_armature_space(skeleton_hkx.skeleton)

    # Convert to dictionary using given `track_bone_names` list.
    arma_frame_dicts = [
        {bone_name: transform for bone_name, transform in zip(track_bone_names, frame)}
        for frame in interleaved_frames
    ]
    return arma_frame_dicts


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


def get_active_flver_or_part_armature(
    context: bpy.types.Context
) -> tuple[bpy.types.ArmatureObject | None, bpy.types.MeshObject | None, str, bool]:
    """Get Armature, Mesh, model name, and `is_part` of active FLVER or MSB Part (Character or Object only)."""
    obj = context.active_object
    if not obj:
        return None, None, "", False

    try:
        armature, mesh = BlenderFLVER.parse_flver_obj(obj)
    except SoulstructTypeError:
        pass
    else:
        if armature:
            return armature, mesh, get_model_name(mesh.name), False

    try:
        armature, mesh = BaseBlenderMSBPart.parse_msb_part_obj(obj)
    except SoulstructTypeError:
        pass
    else:
        if armature and mesh.MSB_PART.model and mesh.MSB_PART.entry_subtype in {
            BlenderMSBPartSubtype.Character, BlenderMSBPartSubtype.Object
        }:
            return armature, mesh, get_model_name(mesh.MSB_PART.model.name), True

    return None, None, "", False
