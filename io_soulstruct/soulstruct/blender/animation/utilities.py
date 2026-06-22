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
    "get_armature_bone_data_type",
    "get_or_create_action_strip",
    "create_action_slot_channelbag",
    "get_basis_matrix",
    "add_keyframes_batch",
]

import typing as tp
from pathlib import Path

import bpy
from mathutils import Matrix

import numpy as np

from soulstruct.havok.core import HKX
from soulstruct.havok.utilities.maths import TRSTransform
from soulstruct.havok.fromsoft.base import BaseAnimationHKX, BaseSkeletonHKX
from soulstruct.havok.fromsoft import demonssouls, darksouls1ptde, darksouls1r, bloodborne, eldenring
from soulstruct.containers import BinderEntry

from ..exceptions import UnsupportedGameError, SoulstructTypeError
from ..flver.models.types import BlenderFLVER, FLVERBoneDataType
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
    BaseSkeletonHKX,
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
    packfile_version = data[0x28:0x36]  # exactly 14 bytes
    tagfile_version = data[0x10:0x18]  # exactly 8 bytes
    for (is_tagfile, expected_data), game_package in _HKX_GAME_PACKAGE_MAP.items():
        if (is_tagfile and expected_data == tagfile_version) or (not is_tagfile and expected_data == packfile_version):
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


def read_animation_hkx_entry(hkx_entry: BinderEntry, compendium: HKX | None = None) -> ANIMATION_TYPING:
    """Read animation HKX file from a Binder entry and return the appropriate `AnimationHKX` subclass instance."""
    animation_hkx_class = _guess_hkx_class(hkx_entry, "AnimationHKX")
    animation_hkx = animation_hkx_class.from_bytes(hkx_entry.get_uncompressed_data(), compendium=compendium)
    animation_hkx.path = Path(hkx_entry.name)
    # noinspection PyTypeChecker
    return animation_hkx


def read_skeleton_hkx_entry(hkx_entry: BinderEntry, compendium: HKX | None = None) -> SKELETON_TYPING:
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
) -> tuple[ArmatureObject | None, MeshObject | None, str, bool, FLVERBoneDataType]:
    """Get Armature, Mesh, model name, and `is_part` of active FLVER or MSB Part (Character or Object only).

    If Armature is not found, nothing is returned.
    """
    obj = context.active_object
    if not obj:
        return None, None, "", False, FLVERBoneDataType.OMITTED

    try:
        armature, mesh = BlenderFLVER.parse_flver_obj(obj)
    except SoulstructTypeError:
        pass
    else:
        if armature:
            bone_data_type = BlenderFLVER.from_armature_or_mesh(mesh).bone_data_type
            return armature, mesh, get_model_name(mesh.name), False, bone_data_type

    try:
        armature, mesh = BaseBlenderMSBPart.parse_msb_part_obj(obj)
    except SoulstructTypeError:
        pass
    else:
        if armature and mesh.MSB_PART.model and mesh.MSB_PART.entry_subtype in {
            BlenderMSBPartSubtype.Character, BlenderMSBPartSubtype.Object
        }:
            bone_data_type = mesh.MSB_PART.model.FLVER.bone_data_type
            return armature, mesh, get_model_name(mesh.MSB_PART.model.name), True, bone_data_type

    return None, None, "", False, FLVERBoneDataType.OMITTED


def get_armature_bone_data_type(armature_obj: ArmatureObject) -> FLVERBoneDataType:
    """Extract `FLVERBoneDataType` from an armature object."""

    try:
        bl_flver = BlenderFLVER.from_armature_or_mesh(armature_obj)
    except SoulstructTypeError:
        pass
    else:
        return bl_flver.bone_data_type

    try:
        bl_msb_part = BaseBlenderMSBPart.from_armature_or_mesh(armature_obj)
    except SoulstructTypeError:
        pass
    else:
        if bl_msb_part.model:
            try:
                bl_flver = BlenderFLVER.from_armature_or_mesh(bl_msb_part.model)
            except SoulstructTypeError:
                pass
            else:
                return bl_flver.bone_data_type

    return FLVERBoneDataType.OMITTED


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


def get_basis_matrix(
    armature: ArmatureObject,
    bone_name: str,
    parent_bone_name: str,
    armature_matrix: Matrix,
    armature_inv_matrices: dict[str, Matrix],
    cached_local_edit_inv_matrices: dict[str, Matrix],
):
    """Get the appropriate matrix to assign to `pose_bone.matrix_basis` from `armature_matrix` by inverting Blender's
    process (see `get_armature_matrix()`).

    The basis matrix represents the *local pose* transform of the bone relative to its *local rest* transform
    (EditBone). For root bones, local pose IS armature pose, and this reduces to just being rest-relative.

    We only consider parent bones that appear as keys in `armature_inv_matrices`. Otherwise, the parent is ignored; this
    allows e.g. untouched Master bones to be ignored in cutscene animations (where the children of Master may be treated
    as world-space transforms instead).

    Args:
        armature: Armature object containing `bone_name`.
        bone_name: Name of the pose bone for which to get the basis matrix.
        parent_bone_name: Name of the bone's parent. Can be intentionally omitted to treat any bone as root.
            This is useful for cutscene animations that, e.g., skip the c0000[Master] bone frame entirely.
        armature_matrix: The desired armature matrix for `bone_name` (i.e., `pose_bone.matrix`).
        armature_inv_matrices: Dictionary mapping bone names to their armature matrices inverted. Used to avoid
            recalculating the inverted matrices of multi-child bones. Parent bone names MUST appear in this to be used
            for making the current bone's pose parent-relative.
        cached_local_edit_inv_matrices: Dictionary mapping bone names to their local matrices inverted. Used to avoid
            recalculating the inverted matrices of multi-child bones.

    Inverse of `get_armature_matrix()`.
    """
    if bone_name not in cached_local_edit_inv_matrices:
        cached_local_edit_inv_matrices[bone_name] = armature.data.bones[bone_name].matrix_local.inverted()
    local_edit_inv = cached_local_edit_inv_matrices[bone_name]

    if not parent_bone_name:
        return local_edit_inv @ armature_matrix

    local_pose = armature_inv_matrices[parent_bone_name] @ armature_matrix
    parent_local_edit = armature.data.bones[parent_bone_name].matrix_local
    return local_edit_inv @ parent_local_edit @ local_pose


def add_keyframes_batch(
    channelbag: bpy.types.ActionChannelbag,
    bone_basis_samples: dict[str, np.ndarray],
    root_motion: np.ndarray | None,
):
    """Efficient method of adding all bone and (optional) root keyframe data.

    Constructs `FCurves` with known length and uses `foreach_set` to batch-set all the `.co` attributes of the
    curve keyframe points at once.

    `bone_basis_samples` should map bone names to a `frame_count x 11` array of data, where the 11 columns are:
        keyframe_t, location XYZ, quaternion WXYZ, scale XYZ
    Here, the `t` column should already be scaled as desired for the frame rate conversion, e.g. (0, 2, 4, ...)
    when converting 30 to 60 FPS.
    """

    def _new_fcurve(data_path_: str, index_: int) -> bpy.types.FCurve:
        """Helper to create an FCurve for the given data path and index."""
        return channelbag.fcurves.new(data_path=data_path_, index=index_)

    # Initialize FCurves for root motion and bones.
    if root_motion is not None:
        if root_motion.ndim != 2 or root_motion.shape[1] not in {5, 7, 8, 11}:
            raise ValueError(
                f"If given, root motion array must be 2D with 5/7/8/11 columns: `keyframe_t, x, y, z`, "
                f"then rotation (Z only, Euler XYZ, or Quaternion), then optional scale (with Quaternion rotate only). "
                f"Invalid shape: {root_motion.shape}"
            )
        root_fcurves = [
            _new_fcurve("location", i) for i in range(3)
        ]
        if root_motion.shape[1] in {8, 11}:
            root_fcurves += [
                _new_fcurve("rotation_quaternion", i) for i in range(4)
            ]
            if root_motion.shape[1] == 11:
                root_fcurves += [
                    _new_fcurve("scale", i) for i in range(3)
                ]
        elif root_motion.shape[1] == 7:
            root_fcurves += [
                _new_fcurve("rotation_euler", i) for i in range(3)
            ]
        else:  # Euler Z only
            root_fcurves.append(
                _new_fcurve("rotation_euler", 2)
            )
    else:
        root_fcurves = []

    # If `bone_basis_samples` is empty, no bone FCurves will be created here.
    bone_fcurves = {}
    for bone_name in bone_basis_samples.keys():
        bone_fcurves[bone_name] = []  # ten FCurves per bone
        bone_fcurves[bone_name] += [
            _new_fcurve(f"pose.bones[\"{bone_name}\"].location", i) for i in range(3)
        ]
        bone_fcurves[bone_name] += [
            _new_fcurve(f"pose.bones[\"{bone_name}\"].rotation_quaternion", i) for i in range(4)
        ]
        bone_fcurves[bone_name] += [
            _new_fcurve(f"pose.bones[\"{bone_name}\"].scale", i) for i in range(3)
        ]

    # Build lists of FCurve keyframe points by initializing their size and using `foreach_set`.
    # Each keyframe point has a `.co` attribute to which we set `(t, value)` (per dimension).
    # `foreach_set` requires that we flatten the list of tuples to be assigned, a la:
    #    `[keyframe_t_0, value_0, keyframe_t_1, value_1, ...]`
    # which we do with array column indexing and `ravel()`.
    if root_fcurves:
        # NOTE: There may be less root motion samples than bone animation samples. We spread the root motion samples
        # out to match the interval covered by the bone animation frames (done by caller).
        for fcurve_i, root_fcurve in enumerate(root_fcurves):  # x, y, z, -rz (from game ry)
            data = root_motion[:, [0, fcurve_i + 1]]  # get `keyframe_t` column plus indexed dim of root motion
            root_fcurve.keyframe_points.add(count=data.shape[0])  # row count
            root_fcurve.keyframe_points.foreach_set("co", data.ravel().tolist())
            for kp in root_fcurve.keyframe_points:
                kp.interpolation = "LINEAR"

    for bone_name, bone_transform_fcurves in bone_fcurves.items():
        basis_samples = bone_basis_samples[bone_name]
        for fcurve_i, bone_fcurve in enumerate(bone_transform_fcurves):
            bone_fcurve.keyframe_points.add(count=basis_samples.shape[0])  # row count
            data = basis_samples[:, [0, fcurve_i + 1]]  # get `keyframe_t` column plus indexed dim of bone motion
            bone_fcurve.keyframe_points.foreach_set("co", data.ravel().tolist())
            for kp in bone_fcurve.keyframe_points:
                kp.interpolation = "LINEAR"
