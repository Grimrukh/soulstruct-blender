"""Generate a new HKX skeleton (`Skeleton.HKX`) from a Blender FLVER Armature.

A skeleton HKX cannot practically be built from nothing: its `hkRootLevelContainer`, Havok version, packfile
header info, float slots, and so on all vary per game. We therefore always start from an existing skeleton HKX
(the one already in the target ANIBND) and rewrite only its bone data: `bones`, `parentIndices`, and
`referencePose`.
"""
from __future__ import annotations

__all__ = [
    "HKXSkeletonBoneSource",
    "HKX_SKELETON_BONE_SOURCE_ITEMS",
    "get_game_bone_name",
    "get_hkx_skeleton_bone_names",
    "write_armature_to_skeleton_hkx",
]

import re
import typing as tp
from enum import StrEnum

import bpy
from mathutils import Matrix, Vector

from soulstruct.havok.fromsoft.base.type_vars import BONE_T, QS_TRANSFORM_T
from soulstruct.havok.utilities.maths import TRSTransform

from ..flver.utilities import BONE_CoB_4x4
from ..types import ArmatureObject
from ..utilities import to_game, bl_matrix_to_game_trs

if tp.TYPE_CHECKING:
    from ..base.operators import LoggingOperator
    from .utilities import SKELETON_TYPING


_DUPE_SUFFIX_RE = re.compile(r"^(.*)\.\d\d\d$")
# Matches the `pose.bones["Bone Name"].location` data path used by all imported animation FCurves.
_POSE_BONE_FCURVE_RE = re.compile(r"^pose\.bones\[\"(.+)\"\]\.")


class HKXSkeletonBoneSource(StrEnum):
    """Determines which Blender bones are written to the new HKX skeleton."""
    TEMPLATE = "Template"  # bones already in the source skeleton (rest pose update only)
    ACTION = "Action"  # bones animated by the Armature's active Action
    SELECTED = "Selected"  # bones selected in the Armature
    ALL = "All"  # every bone in the Armature


HKX_SKELETON_BONE_SOURCE_ITEMS = [
    (
        HKXSkeletonBoneSource.TEMPLATE,
        "Source Skeleton Bones",
        "Export the same bones as the existing HKX skeleton, in the same order. Only bone rest transforms are "
        "updated, so all existing animations in the Binder remain valid",
    ),
    (
        HKXSkeletonBoneSource.ACTION,
        "Active Action Bones",
        "Export only bones animated by the Armature's active Action",
    ),
    (
        HKXSkeletonBoneSource.SELECTED,
        "Selected Bones",
        "Export only bones currently selected in the Armature",
    ),
    (
        HKXSkeletonBoneSource.ALL,
        "All Bones",
        "Export every bone in the FLVER Armature",
    ),
]


def get_game_bone_name(bl_bone_name: str) -> str:
    """Strip any number of Blender `.001`-style dupe suffixes, as FLVER bone export does."""
    while match := _DUPE_SUFFIX_RE.match(bl_bone_name):
        bl_bone_name = match.group(1)
    return bl_bone_name


def _iter_bones_depth_first(armature: ArmatureObject) -> tp.Iterator[bpy.types.Bone]:
    """Yield Armature bones root-first, parents always before their children."""

    def _recur(bone: bpy.types.Bone):
        yield bone
        for child in bone.children:
            yield from _recur(child)

    for root_bone in armature.data.bones:
        if root_bone.parent is None:
            yield from _recur(root_bone)


def _get_template_parent_names(skeleton_hkx: SKELETON_TYPING) -> dict[str, str | None]:
    """Map each HKX skeleton bone name to its HKX parent bone name (or `None` for root bones).

    The HKX skeleton hierarchy is NOT always the same as the FLVER (Blender Armature) hierarchy: real characters
    frequently omit or re-parent bones in their animation skeleton (e.g. DS1 `c1200` parents `L UpperArm` under
    `L Clavicle` in the HKX, but directly under `Neck` in the FLVER). Existing HKX parenting must therefore be
    preserved rather than re-derived from Blender.
    """
    hka_skeleton = skeleton_hkx.skeleton.skeleton
    bone_names = [bone.name for bone in hka_skeleton.bones]
    parent_indices = list(hka_skeleton.parentIndices)
    return {
        name: (bone_names[parent_indices[i]] if parent_indices[i] >= 0 else None)
        for i, name in enumerate(bone_names)
    }


def _transforms_are_close(a: TRSTransform, b: TRSTransform, tolerance=1e-4) -> bool:
    """Compare two `TRSTransform`s component-wise (rotation compared via quaternion, up to sign)."""
    for i in range(3):
        if abs(a.translation[i] - b.translation[i]) > tolerance:
            return False
        if abs(a.scale[i] - b.scale[i]) > tolerance:
            return False
    q_a, q_b = a.rotation, b.rotation
    dot = abs(q_a.x * q_b.x + q_a.y * q_b.y + q_a.z * q_b.z + q_a.w * q_b.w)
    return abs(dot - 1.0) <= tolerance


def _get_selected_bone_names(armature: ArmatureObject) -> set[str]:
    """Get names of all selected bones.

    `Bone.select` no longer exists in Blender 5.x: selection lives on `EditBone` in Edit Mode and on `PoseBone`
    everywhere else.
    """
    if armature.mode == "EDIT":
        return {edit_bone.name for edit_bone in armature.data.edit_bones if edit_bone.select}
    return {pose_bone.name for pose_bone in armature.pose.bones if pose_bone.select}


def _get_action_bone_names(armature: ArmatureObject) -> set[str]:
    """Get names of all bones with at least one FCurve in the Armature's active Action."""
    animation_data = armature.animation_data
    if not animation_data or not animation_data.action:
        return set()
    action = animation_data.action
    bone_names = set()
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                channelbag = strip.channelbag(slot)
                if not channelbag:
                    continue
                for fcurve in channelbag.fcurves:
                    if match := _POSE_BONE_FCURVE_RE.match(fcurve.data_path):
                        bone_names.add(match.group(1))
    return bone_names


def get_hkx_skeleton_bone_names(
    operator: LoggingOperator,
    armature: ArmatureObject,
    template_skeleton_hkx: SKELETON_TYPING,
    bone_source: HKXSkeletonBoneSource,
    include_ancestor_bones=True,
) -> list[str]:
    """Resolve the ordered list of Blender bone names to write to a new HKX skeleton.

    Bones already present in `template_skeleton_hkx` keep their existing indices (so that animations already in
    the Binder remain valid); any brand-new bones are appended afterwards in Armature hierarchy order.

    Returns Blender bone names, which may carry `.001`-style dupe suffixes that the caller must strip for the
    actual HKX bone names.
    """
    bl_bones = armature.data.bones

    # Map game bone name -> Blender bone name. First match wins (later dupes are ignored with a warning).
    game_name_to_bl_name = {}  # type: dict[str, str]
    for bl_bone in bl_bones:
        game_name = get_game_bone_name(bl_bone.name)
        if game_name in game_name_to_bl_name:
            operator.warning(
                f"Multiple Armature bones resolve to game bone name '{game_name}' (e.g. '{bl_bone.name}'). Only "
                f"'{game_name_to_bl_name[game_name]}' will be used."
            )
            continue
        game_name_to_bl_name[game_name] = bl_bone.name

    template_bone_names = [bone.name for bone in template_skeleton_hkx.skeleton.skeleton.bones]
    template_parent_names = _get_template_parent_names(template_skeleton_hkx)

    if bone_source == HKXSkeletonBoneSource.TEMPLATE:
        selected_bl_names = set()
        for game_name in template_bone_names:
            if game_name in game_name_to_bl_name:
                selected_bl_names.add(game_name_to_bl_name[game_name])
            else:
                operator.warning(
                    f"Bone '{game_name}' in source HKX skeleton is missing from FLVER Armature and will be dropped. "
                    f"This will shift bone indices and invalidate existing animations."
                )
    elif bone_source == HKXSkeletonBoneSource.ACTION:
        selected_bl_names = _get_action_bone_names(armature)
        if not selected_bl_names:
            raise ValueError("Armature has no active Action with any bone FCurves to source bones from.")
        # Drop any FCurve bone names that no longer exist in the Armature.
        missing = {name for name in selected_bl_names if name not in bl_bones}
        for name in sorted(missing):
            operator.warning(f"Action animates bone '{name}', which is not in the Armature. Ignoring.")
        selected_bl_names -= missing
    elif bone_source == HKXSkeletonBoneSource.SELECTED:
        selected_bl_names = _get_selected_bone_names(armature)
        if not selected_bl_names:
            raise ValueError("No bones are selected in the Armature (in Edit or Pose Mode).")
    elif bone_source == HKXSkeletonBoneSource.ALL:
        selected_bl_names = {bl_bone.name for bl_bone in bl_bones}
    else:
        raise ValueError(f"Invalid HKX skeleton bone source: {bone_source}")

    if not selected_bl_names:
        raise ValueError("No bones were resolved for HKX skeleton export.")

    if include_ancestor_bones and bone_source != HKXSkeletonBoneSource.TEMPLATE:
        # Bones already in the template follow the template's own hierarchy; brand-new bones follow Blender's.
        for bl_name in list(selected_bl_names):
            game_name = get_game_bone_name(bl_name)
            if game_name in template_parent_names:
                parent_game_name = template_parent_names[game_name]
                while parent_game_name is not None:
                    if parent_game_name in game_name_to_bl_name:
                        selected_bl_names.add(game_name_to_bl_name[parent_game_name])
                    parent_game_name = template_parent_names.get(parent_game_name)
            else:
                parent = bl_bones[bl_name].parent
                while parent is not None:
                    selected_bl_names.add(parent.name)
                    parent = parent.parent

    # Order: template bones first (preserving their indices), then any new bones in Armature hierarchy order.
    ordered_bl_names = []
    for game_name in template_bone_names:
        bl_name = game_name_to_bl_name.get(game_name)
        if bl_name in selected_bl_names:
            ordered_bl_names.append(bl_name)
    remaining = selected_bl_names.difference(ordered_bl_names)
    if remaining:
        new_bl_names = [bl_bone.name for bl_bone in _iter_bones_depth_first(armature) if bl_bone.name in remaining]
        operator.info(
            f"Appending {len(new_bl_names)} new bone(s) to end of HKX skeleton: {', '.join(new_bl_names)}"
        )
        ordered_bl_names += new_bl_names

    return ordered_bl_names


def write_armature_to_skeleton_hkx(
    operator: LoggingOperator,
    armature: ArmatureObject,
    skeleton_hkx: SKELETON_TYPING,
    bl_bone_names: list[str],
) -> SKELETON_TYPING:
    """Overwrite the bone data of `skeleton_hkx` (used as a template) with `bl_bone_names` from `armature`.

    `skeleton_hkx` is modified in place and returned. Everything other than `bones`, `parentIndices`,
    `referencePose` (and `partitions`, if the Havok version has them) is left exactly as loaded.

    Bone rest transforms are read from Edit Bone data (`Bone.matrix_local`), with the FLVER X-forward change of
    basis undone, and local bone scale is read from the `FLVER_BONE.flver_scale` custom property (Edit Bones
    cannot store scale). This requires the FLVER to use `EditBone` bone data, i.e. to be a dynamic (rigged) FLVER.

    Bone PARENTING is taken from the template HKX skeleton wherever possible, NOT from the Blender Armature: the
    FLVER and HKX hierarchies genuinely differ for many models. Only brand-new bones (absent from the template)
    derive their parent from the Blender hierarchy. Each bone's local reference pose is computed relative to
    whichever parent is resolved, so it is always geometrically correct.
    """
    havok_module = skeleton_hkx.HAVOK_MODULE
    bone_type = havok_module.get_type_from_var(BONE_T)
    qs_transform_type = havok_module.get_type_from_var(QS_TRANSFORM_T)

    hka_skeleton = skeleton_hkx.skeleton.skeleton  # raw `hkaSkeleton`
    # Preserve `lockTranslation` for any bone that already existed in the template skeleton.
    template_lock_translation = {bone.name: bone.lockTranslation for bone in hka_skeleton.bones}
    template_bone_names = [bone.name for bone in hka_skeleton.bones]
    template_parent_names = _get_template_parent_names(skeleton_hkx)
    template_reference_pose = {
        name: hka_skeleton.referencePose[i].to_trs_transform() for i, name in enumerate(template_bone_names)
    }

    bl_bones = armature.data.bones
    bl_name_set = set(bl_bone_names)
    bl_name_to_index = {bl_name: i for i, bl_name in enumerate(bl_bone_names)}
    game_name_to_bl_name = {get_game_bone_name(bl_name): bl_name for bl_name in bl_bone_names}

    def resolve_parent_bl_name(child_bl_name: str) -> str | None:
        """Find the exported parent of `child_bl_name`, preferring the template HKX hierarchy."""
        child_game_name = get_game_bone_name(child_bl_name)
        if child_game_name in template_parent_names:
            parent_game_name = template_parent_names[child_game_name]
            while parent_game_name is not None:
                parent_bl_name = game_name_to_bl_name.get(parent_game_name)
                if parent_bl_name is not None and parent_bl_name != child_bl_name:
                    return parent_bl_name
                parent_game_name = template_parent_names.get(parent_game_name)
            return None
        # Brand-new bone: fall back to nearest exported Blender ancestor.
        parent = bl_bones[child_bl_name].parent
        while parent is not None and parent.name not in bl_name_set:
            parent = parent.parent
        return parent.name if parent is not None else None

    # Armature-space rest matrices with the FLVER X-forward CoB undone (`BONE_CoB_4x4` is its own inverse), i.e.
    # the game's own bone basis expressed in Blender coordinates.
    arma_matrices = {bl_name: bl_bones[bl_name].matrix_local @ BONE_CoB_4x4 for bl_name in bl_bone_names}

    hkx_parent_bl_names = {bl_name: resolve_parent_bl_name(bl_name) for bl_name in bl_bone_names}

    # Effective HKX armature-space matrices. These are NOT simply the Blender armature-space matrices, because
    # FromSoft FLVERs routinely leave HKX-only bones (clavicles, `*Nub` tips, ...) detached at the FLVER root
    # while still storing the local transform their HKX parent expects. Such bones are therefore anchored to
    # their HKX parent. Bones that DO have a Blender parent keep their Blender-relative placement, anchored to
    # that parent's own effective matrix. The exception is a detached bone whose HKX parent is ALSO detached in
    # Blender: both then live in the same (armature) space, so their transforms are treated as absolute.
    hkx_arma_matrices = {}  # type: dict[str, Matrix]

    def is_bl_detached(bl_name: str) -> bool:
        bl_parent = bl_bones[bl_name].parent
        return bl_parent is None or bl_parent.name not in bl_name_set

    def get_hkx_arma_matrix(bl_name: str, pending: frozenset[str] = frozenset()) -> Matrix:
        if bl_name in hkx_arma_matrices:
            return hkx_arma_matrices[bl_name]
        if bl_name in pending:  # cyclic FLVER/HKX hierarchy mix; anchor at armature origin
            return arma_matrices[bl_name]
        pending = pending | {bl_name}

        if not is_bl_detached(bl_name):
            bl_parent_name = bl_bones[bl_name].parent.name
            bl_local_matrix = arma_matrices[bl_parent_name].inverted() @ arma_matrices[bl_name]
            matrix = get_hkx_arma_matrix(bl_parent_name, pending) @ bl_local_matrix
        else:
            hkx_parent_bl_name = hkx_parent_bl_names[bl_name]
            if hkx_parent_bl_name is None or is_bl_detached(hkx_parent_bl_name):
                matrix = arma_matrices[bl_name]
            else:
                matrix = get_hkx_arma_matrix(hkx_parent_bl_name, pending) @ arma_matrices[bl_name]

        hkx_arma_matrices[bl_name] = matrix
        return matrix

    new_bones = []
    parent_indices = []
    reference_pose = []
    changed_bone_names = []  # bones whose rest transform differs from the template's

    for bl_name in bl_bone_names:
        bl_bone = bl_bones[bl_name]

        parent_bl_name = hkx_parent_bl_names[bl_name]

        if parent_bl_name is None:
            parent_indices.append(-1)
            bl_local_matrix = get_hkx_arma_matrix(bl_name)
        else:
            parent_indices.append(bl_name_to_index[parent_bl_name])
            bl_local_matrix = get_hkx_arma_matrix(parent_bl_name).inverted() @ get_hkx_arma_matrix(bl_name)

        # `to_game()` on a matrix is a conjugation by the Y/Z-swap permutation, so composition is preserved and
        # local matrices can be converted independently.
        transform = bl_matrix_to_game_trs(bl_local_matrix)
        # Edit Bones never store scale, so local FLVER bone scale always comes from the custom property.
        transform.scale = to_game(Vector(bl_bone.FLVER_BONE.flver_scale))
        reference_pose.append(qs_transform_type.from_trs_transform(transform))

        game_bone_name = get_game_bone_name(bl_name)
        new_bones.append(
            bone_type(
                name=game_bone_name,
                lockTranslation=template_lock_translation.get(game_bone_name, False),
            )
        )

        old_transform = template_reference_pose.get(game_bone_name)
        if old_transform is not None and not _transforms_are_close(old_transform, transform):
            changed_bone_names.append(game_bone_name)

    hka_skeleton.bones = new_bones
    hka_skeleton.parentIndices = parent_indices
    hka_skeleton.referencePose = reference_pose

    # Older Havok versions (e.g. `hk550`) have no partitions. If the bone set changed, the template's partition
    # bone ranges are no longer valid, so collapse to a single partition spanning all bones.
    new_bone_names = [bone.name for bone in new_bones]
    if new_bone_names != template_bone_names:
        partitions = getattr(hka_skeleton, "partitions", None)
        if partitions:
            partition = partitions[0]
            partition.startBoneIndex = 0
            partition.numBones = len(new_bones)
            hka_skeleton.partitions = [partition]

    # Rebuild `Bone` wrappers so the returned `SkeletonHKX` is immediately usable (e.g. for animation export).
    skeleton_hkx.skeleton.refresh_bones()

    operator.info(f"Generated HKX skeleton '{hka_skeleton.name}' with {len(new_bones)} bone(s).")

    if changed_bone_names:
        # Note that vanilla FLVER and HKX skeletons are not always in perfect agreement (e.g. DS1 `c1200` places
        # `master` 0.6 units lower in its HKX than its FLVER, and mirrors `L Toe0Nub` with a negative scale that
        # its FLVER does not have), so some bones may be reported as changed even with an unmodified Armature.
        shown = ", ".join(changed_bone_names[:20])
        if len(changed_bone_names) > 20:
            shown += f", ... (+{len(changed_bone_names) - 20} more)"
        operator.info(
            f"{len(changed_bone_names)} bone rest transform(s) differ from the source HKX skeleton: {shown}"
        )

    return skeleton_hkx
