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
    "TRS",
    "get_armature_rest_trs",
    "get_flver_bone_rest_scales",
    "resolve_duplicate_animated_bone_names",
    "get_basis_trs",
    "get_pose_trs_from_basis",
    "add_keyframes_batch",
]

import re
import typing as tp
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

import numpy as np

from soulstruct.havok.core import HKX
from soulstruct.havok.utilities.maths import TRSTransform
from soulstruct.havok.fromsoft.base import BaseAnimationHKX, BaseSkeletonHKX
from soulstruct.havok.fromsoft import demonssouls, darksouls1ptde, darksouls1r, bloodborne, eldenring
from soulstruct.containers import BinderEntry

from ..exceptions import UnsupportedGameError, SoulstructTypeError
from ..flver.models.types import BlenderFLVER, FLVERBoneDataType
from ..flver.utilities import game_trs_to_bl_bone_trs, permute_scale_for_cob
from ..msb.properties.parts import BlenderMSBPartSubtype
from ..msb.types.base.parts import BaseBlenderMSBPart
from ..types import ArmatureObject, MeshObject
from ..utilities import get_model_name

if tp.TYPE_CHECKING:
    from ..base.operators import LoggingOperator

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


TRS = tuple[Vector, Quaternion, Vector]  # (translation, rotation, scale)


def get_armature_rest_trs(armature: ArmatureObject) -> dict[str, TRS]:
    """Return a dict mapping Blender bone names to their rest pose (translation, rotation, scale) in armature space,
    decomposed from `Bone.matrix_local`.

    FLVER rest bones never carry scale (see `write_flver_rest_pose_to_edit_bones()`), so `matrix_local` is always a
    pure rotation+translation matrix and this decomposition is exact -- no shear is possible.
    """
    return {
        bone.name: bone.matrix_local.decompose()
        for bone in armature.data.bones
    }


_DUPE_BONE_NAME_RE = re.compile(r"^(.*?)(?: <DUPE>)*(?:\.\d+)?$")


def resolve_duplicate_animated_bone_names(
    operator: LoggingOperator,
    armature: ArmatureObject,
    skeleton_hkx: BaseSkeletonHKX,
    animated_bone_names: tp.Iterable[str],
) -> dict[str, str]:
    """Map HKX skeleton bone names to the Blender bone they should actually animate, for FLVERs that contain more than
    one bone with the same game name.

    FLVER import cannot use a game bone name twice, so `_create_bl_bones()` renames every repeat to `{name} <DUPE>`
    (and Blender may further append `.001`). The HKX skeleton has no such collision, so a name-only lookup silently
    binds the animation to whichever duplicate happened to come FIRST in the FLVER -- which is usually the wrong one.
    DeS c6041 (Plague Baby) is the only vanilla DeS character affected: its FLVER has two bones named `c6041`, an
    origin stub at index 0 and the real skeleton root at index 1, so every animation drove the stub and left the real
    root (plus the entire body hanging off it) unposed.

    Disambiguation uses the armature-space rest translation: the correct Blender bone is the one sitting where the HKX
    skeleton's reference pose puts it. Returns only the names that need remapping (usually empty).
    """
    candidates = {}  # type: dict[str, list[bpy.types.Bone]]
    for bl_bone in armature.data.bones:
        match = _DUPE_BONE_NAME_RE.match(bl_bone.name)
        game_name = match.group(1) if match else bl_bone.name
        candidates.setdefault(game_name, []).append(bl_bone)

    renames = {}  # type: dict[str, str]
    arma_ref_poses = None  # only computed if actually needed (rare)

    for bone_name in animated_bone_names:
        bl_bones = candidates.get(bone_name)
        if not bl_bones or len(bl_bones) == 1:
            continue  # no ambiguity (overwhelmingly common)
        if arma_ref_poses is None:
            arma_ref_poses = skeleton_hkx.skeleton.get_arma_space_reference_poses()
        try:
            ref_pose = arma_ref_poses[bone_name]
        except KeyError:
            continue  # not in HKX skeleton; leave alone
        hkx_arma_translate = game_trs_to_bl_bone_trs(ref_pose)[0]
        best = min(bl_bones, key=lambda b: (b.matrix_local.to_translation() - hkx_arma_translate).length)
        if best.name != bone_name:
            renames[bone_name] = best.name
            operator.warning(
                f"FLVER Armature has {len(bl_bones)} bones named '{bone_name}'. Binding this animation's "
                f"'{bone_name}' track to '{best.name}', whose rest position matches the HKX skeleton."
            )

    return renames


def get_flver_bone_rest_scales(
    armature: ArmatureObject,
    bone_data_type: FLVERBoneDataType,
) -> dict[str, Vector]:
    """Return a dict mapping Blender bone names to the FLVER *local* bone scale that their rest pose does NOT carry,
    expressed in the same space as the bone's animation pose scale (i.e. permuted for the X-forward bone CoB when
    bone data is stored in `EditBones`). Bones with (near-)identity scale are omitted.

    EditBones cannot store scale, so `write_flver_rest_pose_to_edit_bones()` builds each rest matrix with scale forced
    to 1 and stashes the real FLVER local scale on `Bone.FLVER_BONE.flver_scale` instead. The game, however, DOES bake
    that scale into the bind pose it inverts out when skinning, and every HKX animation reproduces it in the bone's
    armature-space scale. Writing that armature-space scale straight into a Blender pose channel therefore applies it
    a second time, on top of mesh geometry that already reflects it -- e.g. DeS c5010 (Tower Knight) has
    `L_Shoulderpad`/`R_Shoulderpad` scale 3.1285 in both its FLVER and its HKX skeleton, so its pauldrons ballooned to
    3.13x their size in every imported animation (c5020 Penetrator, 1.26x, is the same bug more subtly).

    Import divides each bone's armature-space pose scale by this value and export multiplies it back, which makes the
    Blender deformation `pose_arma @ rest_arma^-1` match the game's `anim_arma @ bind_arma^-1` exactly. Note that this
    is a purely per-bone correction: it does not touch translation or rotation, and (unlike putting the scale back into
    the rest pose) it cannot disturb child bone rest offsets, which FLVER deliberately leaves unscaled by their parent.

    Only applies to `EDIT` bone data. `CUSTOM` (static map piece) armatures write FLVER bone TRS to their PoseBones
    for display, so their rest pose is not missing anything, and they are never animated by HKX anyway.
    """
    if bone_data_type != FLVERBoneDataType.EDIT:
        return {}

    rest_scales = {}  # type: dict[str, Vector]
    for bone in armature.data.bones:
        try:
            flver_scale = Vector(bone.FLVER_BONE.flver_scale)
        except AttributeError:
            continue  # not a Soulstruct FLVER bone
        if all(abs(c - 1.0) < 1e-4 for c in flver_scale):
            continue  # identity scale (overwhelmingly common)
        if any(abs(c) < 1e-6 for c in flver_scale):
            continue  # degenerate; refuse to divide by ~zero
        # `flver_scale` is stored with the standard game -> Blender axis swap only, so we must apply the same CoB
        # scale permutation that `game_trs_to_bl_bone_trs()` applies to animation pose scale.
        rest_scales[bone.name] = permute_scale_for_cob(flver_scale)

    return rest_scales


def _trs_compose(t1: Vector, r1: Quaternion, s1: Vector, t2: Vector, r2: Quaternion, s2: Vector) -> TRS:
    """Shear-free composition of two (translation, rotation, scale) transforms, matching the composition rule used by
    Havok's `hkQsTransform` (and Soulstruct's `TRSTransform.compose(scale_translation=True)`):
        T' = R1 @ (S1 * T2) + T1
        R' = R1 @ R2
        S' = S1 * S2  (component-wise)

    Unlike `Matrix @ Matrix`, this can NEVER introduce shear. That matters because a plain matrix product of a
    non-uniformly-scaled parent and a rotated child generally DOES contain shear, which Havok's animation format
    (and this composition rule) cannot represent and never produces in the first place.
    """
    scaled_t2 = Vector((s1.x * t2.x, s1.y * t2.y, s1.z * t2.z))
    t = r1.to_matrix() @ scaled_t2 + t1
    r = r1 @ r2
    s = Vector((s1.x * s2.x, s1.y * s2.y, s1.z * s2.z))
    return t, r, s


def _trs_left_divide(t1: Vector, r1: Quaternion, s1: Vector, t2: Vector, r2: Quaternion, s2: Vector) -> TRS:
    """Solve `(t1, r1, s1) (+) X = (t2, r2, s2)` for `X`, where `(+)` is the shear-free composition above.

    IMPORTANT: this is NOT the same as composing `(t2, r2, s2)` with the "inverse" of `(t1, r1, s1)` (i.e. it is
    NOT `_trs_compose(*inverse(t1, r1, s1), t2, r2, s2)`). Havok's own `TRSTransform.inverse()` is explicitly only a
    *one-sided* inverse -- its docstring notes `inverse(A) (+) A == identity` holds for any scale, but the reverse
    `A (+) inverse(A)` does not, "because rotation and non-uniform scaling do not commute". Composing with that
    one-sided inverse therefore does NOT recover `X` here whenever `s1` is non-uniform: it silently applies the
    unscale *before* un-rotating, instead of after, corrupting exactly the non-uniform-scale-plus-rotation cases this
    whole shear-free scheme exists to handle correctly. This function solves the composition definition directly
    (unscale happens after un-rotating), which is provably correct for any scale.
    """
    inv_r1 = r1.inverted()
    inv_s1 = Vector((1.0 / s1.x, 1.0 / s1.y, 1.0 / s1.z))
    r = inv_r1 @ r2
    s = Vector((s2.x * inv_s1.x, s2.y * inv_s1.y, s2.z * inv_s1.z))
    rotated_delta = inv_r1.to_matrix() @ (t2 - t1)
    t = Vector((rotated_delta.x * inv_s1.x, rotated_delta.y * inv_s1.y, rotated_delta.z * inv_s1.z))
    return t, r, s


def get_basis_trs(
    rest_trs: TRS,
    parent_rest_trs: TRS | None,
    pose_trs: TRS,
    parent_pose_trs: TRS | None,
) -> TRS:
    """Shear-free replacement for the old matrix-based `get_basis_matrix()`. Returns the (location, rotation, scale)
    triple to write directly to a PoseBone's FCurve samples (i.e. Blender's `matrix_basis`, pre-decomposed), given the
    bone's (and optional parent's) rest and target armature-space pose transforms.

    Solves `pose_trs = parent_pose_trs (+) (rest_rel (+) basis)` for `basis`, where `(+)` is the shear-free TRS
    composition above and `rest_rel` is this bone's rest pose expressed relative to its parent's rest pose. If
    `parent_rest_trs`/`parent_pose_trs` is `None`, the bone is treated as a root (parent transforms are identity).
    This allows e.g. untouched Master bones to be ignored in cutscene animations (where the children of Master may be
    treated as world-space transforms instead).

    Inverse of `get_pose_trs_from_basis()`.
    """
    if parent_rest_trs is None or parent_pose_trs is None:
        rest_rel = rest_trs
        local_pose = pose_trs
    else:
        rest_rel = _trs_left_divide(*parent_rest_trs, *rest_trs)
        local_pose = _trs_left_divide(*parent_pose_trs, *pose_trs)
    return _trs_left_divide(*rest_rel, *local_pose)


def get_pose_trs_from_basis(
    rest_trs: TRS,
    parent_rest_trs: TRS | None,
    basis_trs: TRS,
    parent_pose_trs: TRS | None,
) -> TRS:
    """Inverse of `get_basis_trs()`: reconstructs a bone's armature-space target (translation, rotation, scale)
    transform from its Blender pose channel values (the `basis`) plus rest/parent-pose data.

    Used by animation export in place of reading `pose_bone.matrix` directly, since that final matrix depends on each
    bone's `inherit_scale` setting. Only `ALIGNED` (which FLVER import now sets on dynamic FLVER bones) matches this
    Havok rule exactly; `FULL` composes 4x4 matrices and so introduces shear and wrong scale whenever a non-uniformly
    scaled parent has a rotated child, and `NONE`/`AVERAGE` lose the inherited scale (though Blender still scales the
    child's *location* by the parent scale in every mode). Recomposing here keeps export correct regardless of how a
    user (or older import) has configured the Armature.
    """
    if parent_rest_trs is None or parent_pose_trs is None:
        return _trs_compose(*rest_trs, *basis_trs)
    rest_rel = _trs_left_divide(*parent_rest_trs, *rest_trs)
    local_pose = _trs_compose(*rest_rel, *basis_trs)
    return _trs_compose(*parent_pose_trs, *local_pose)


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
