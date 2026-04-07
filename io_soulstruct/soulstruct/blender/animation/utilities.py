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
    "get_or_create_action_strip",
    "create_action_slot_channelbag",
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

from ..exceptions import UnsupportedGameError, SoulstructTypeError
from ..flver.models.types import BlenderFLVER
from ..msb.properties.parts import BlenderMSBPartSubtype
from ..msb.types.base.parts import BaseBlenderMSBPart
from ..types import ArmatureObject, MeshObject
from ..utilities import get_model_name

ANIMATION_TYPING = tp.Union[
    BaseAnimationHKX,
    demonssouls.AnimationHKX,
    darksouls1ptde.AnimationHKX,
    darksouls1r.AnimationHKX,
    bloodborne.AnimationHKX,
    eldenring.AnimationHKX,
]
SKELETON_TYPING = tp.Union[
    BaseAnimationHKX,
    demonssouls.SkeletonHKX,
    darksouls1ptde.SkeletonHKX,
    darksouls1r.SkeletonHKX,
    bloodborne.SkeletonHKX,
    eldenring.SkeletonHKX,
]


# Map `(is_tagfile, bytes)` to `soulstruct.havok.fromsoft` subpackage.
_HKX_GAME_PACKAGE_MAP = {
    (False, b"Havok-4.5.0-r1"): demonssouls,  # DeS (c9900)
    (False, b"Havok-5.5.0-r1"): demonssouls,  # DeS
    (False, b"hk_2010.2.0-r1"): darksouls1ptde,  # PTDE
    (True, b"20150100"): darksouls1r,  # DSR
    (False, b"hk_2014.1.0-r1"): bloodborne,  # BB
    # TODO: Sekiro support.
    (True, b"20180100"): eldenring,  # ER
}


def _guess_hkx_class(hkx_entry: BinderEntry, class_name: str) -> type[HKX]:
    """Find game-specific HKX subclass from HKX file of unknown packfile/tagfile type."""
    data = hkx_entry.get_uncompressed_data()
    packfile_version = data[0x28:0x38]
    tagfile_version = data[0x10:0x18]
    for (is_tagfile, expected_data), game_package in _HKX_GAME_PACKAGE_MAP.items():
        if is_tagfile and expected_data == tagfile_version:
            try:
                return getattr(game_package, class_name)  # type: type[HKX]
            except AttributeError:
                raise UnsupportedGameError(
                    f"Havok game package '{game_package.__name__}' has no `{class_name}` class."
                )
    raise UnsupportedGameError(
        f"Cannot find a `{class_name}` class match for this HKX file version in Soulstruct and/or Blender.\n"
        f"   Possible packfile version: {packfile_version}\n"
        f"   Possible tagfile version: {tagfile_version}"
    )


def read_animation_hkx_entry(hkx_entry: BinderEntry, compendium: HKX = None) -> ANIMATION_TYPING:
    """Read animation HKX file from a Binder entry and return the appropriate `AnimationHKX` subclass instance."""
    animation_hkx_class = _guess_hkx_class(hkx_entry, "AnimationHKX")
    animation_hkx = animation_hkx_class.from_bytes(hkx_entry.get_uncompressed_data(), compendium=compendium)
    animation_hkx.path = Path(hkx_entry.name)
    # noinspection PyTypeChecker
    return animation_hkx


def read_skeleton_hkx_entry(hkx_entry: BinderEntry, compendium: HKX = None) -> SKELETON_TYPING:
    """Read skeleton HKX file from a Binder entry and return the appropriate `SkeletonHKX` subclass instance."""
    skeleton_hkx_class = _guess_hkx_class(hkx_entry, "SkeletonHKX")
    skeleton_hkx = skeleton_hkx_class.from_bytes(hkx_entry.get_uncompressed_data(), compendium=compendium)
    skeleton_hkx.path = Path(hkx_entry.name)
    # noinspection PyTypeChecker
    return skeleton_hkx


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
    animation_id_str = str(animation_id)

    if len(template.replace("_", "")) < len(animation_id_str):
        raise ValueError(
            f"Animation ID '{animation_id_str}' is too long for template '{template}'."
        )

    for part in reversed(parts):
        length = len(part)  # number of digits we want to take from the end of the animation ID
        string_parts.append(animation_id_str[-length:].zfill(length))
        animation_id_str = animation_id_str[:-length]

    return prefix + '_'.join(reversed(string_parts))


def get_active_flver_or_part_armature(
    context: bpy.types.Context
) -> tuple[ArmatureObject | None, MeshObject | None, str, bool]:
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


def get_or_create_action_strip(action: bpy.types.Action) -> bpy.types.ActionKeyframeStrip:
    """Return the unique layer/strip used by all Soulstruct-imported Actions."""
    if action.layers:
        layer = action.layers[0]
    else:
        layer = action.layers.new("Layer")

    if layer.strips:
        return layer.strips[0]
    return layer.strips.new(type="KEYFRAME")


def create_action_slot_channelbag(
    obj: bpy.types.Object, action_name: str
) -> tuple[bpy.types.Action, bpy.types.ActionSlot, bpy.types.ActionChannelbag]:
    """Modern Blender (4.4+) has moved FCurves from the `Action` to a nested `ActionSlot`-specific channelbag:

    `action.fcurves`
    becomes
    `action.layers[0].strips[0].channelbag(action_slot).fcurves`

    This helper function creates the action, action slot, and nested channelbag, and returns all three.
    """
    obj.animation_data_create()
    action = bpy.data.actions.new(name=action_name)
    action_slot = action.slots.new(id_type="OBJECT", name=obj.name)
    strip = get_or_create_action_strip(action)
    channelbag = strip.channelbag(action_slot, ensure=True)
    return action, action_slot, channelbag
