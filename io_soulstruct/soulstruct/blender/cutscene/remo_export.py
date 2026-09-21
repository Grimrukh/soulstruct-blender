"""Write Blender cutscene animation back into a template `RemoBND` (Dark Souls: Remastered).

This module patches an existing RemoBND (see `remo_build.py` for building one from scratch): the source file
supplies the TAE, each cut's amalgamated cutscene skeleton (root bone per MSB Part, prefixed part bones beneath it),
and the animation tracks of every part that has no animated counterpart in Blender (Map Pieces, Collisions, parts of
other maps that were never imported). Only the tracks of parts that ARE bound to the cutscene Action are overwritten,
along with each cut's SIBCAM camera animation. `build_cut_animation_hkx()` and `build_new_sibcam()` are shared with
the from-scratch builder.

Per cut, the pipeline is:
    template cut HKX (spline) -> interleaved LOCAL-space frames (`get_template_local_frames`)
    -> overwrite each Blender-animated part's tracks (`write_part_frames`, the inverse of
       `RemoCut._add_cut_arma_frames`)
    -> `build_cut_animation_hkx`: a plain DSR `AnimationHKX` is built from the local frames and (optionally)
       spline-compressed with `CompressAnim.exe` (Windows only), then its animation/binding are spliced into the
       template cut HKX so the cutscene skeleton is preserved
    -> `replace_cut_hkx_entry` / `write_cut_sibcam` update the binder entries in place.
"""
from __future__ import annotations

__all__ = [
    "get_template_local_frames",
    "get_part_track_bone_names",
    "write_part_frames",
    "make_track_rotations_continuous",
    "build_cut_animation_hkx",
    "replace_cut_hkx_entry",
    "find_cut_hkx_entry",
    "find_cut_sibcam_entry",
    "write_cut_sibcam",
    "build_new_sibcam",
]

import re
import typing as tp

import numpy as np

from soulstruct.base.animations.sibcam import SIBCAM, CameraFrameTransform, FoVKeyframe
from soulstruct.containers import BinderEntry
from soulstruct.havok.fromsoft.darksouls1r import AnimationHKX
from soulstruct.havok.fromsoft.darksouls1r.remobnd import RemoBND, RemoCut, RemoPart
from soulstruct.havok.utilities.maths import TRSTransform
from soulstruct.utilities.maths import EulerRad, Vector3

from ..exceptions import CutsceneExportError
from .utilities import get_catmull_rom_tangents

# Same pattern `RemoBND.__post_init__` uses to identify per-cut HKX entries.
CUT_HKX_RE = re.compile(r"^a(\d+)\.hkx")


def get_template_local_frames(cut: RemoCut) -> list[list[TRSTransform]]:
    """Copy the template cut's interleaved LOCAL-space frames (outer list = frames, inner list = tracks).

    `RemoBND.load_remo_parts()` already converts every cut animation to interleaved (in place); this just makes sure
    the data is loaded and returns a copy, so template values survive in tracks we never overwrite.
    """
    animation = cut.animation
    container = animation.animation_container
    if not container.is_interleaved:
        animation.animation_container = container = container.to_interleaved_container()
    container.load_interleaved_data()
    return [[transform.copy() for transform in frame] for frame in container.interleaved_data]


def get_part_track_bone_names(cut: RemoCut, remo_part: RemoPart) -> list[str]:
    """Real (un-prefixed) names of this part's bones that have animation tracks in `cut`, in skeleton order.

    Untracked part bones are ignored on both import and export (import poses them at identity).
    """
    _, part_bones = cut.animation.get_root_and_part_bones(remo_part.name, bone_prefix=remo_part.map_part_name + "_")
    tracked_bone_indices = set(cut.animation.animation_container.hkx_binding.transformTrackToBoneIndices)
    return [real_name for real_name, bone in part_bones.items() if bone.index in tracked_bone_indices]


def write_part_frames(
    cut: RemoCut,
    remo_part: RemoPart,
    root_motion: tp.Sequence[TRSTransform],
    bone_frames: tp.Sequence[dict[str, TRSTransform]] | None,
    local_frames: list[list[TRSTransform]],
) -> None:
    """Overwrite `remo_part`'s tracks in `local_frames` (from `get_template_local_frames()`) with new data.

    Exact inverse of `RemoCut._add_cut_arma_frames()`:
        - the part's root track stores `root_motion` verbatim (a full world-space `TRSTransform` per frame);
        - `bone_frames` map real (un-prefixed) bone names to game ARMATURE-space transforms, which are converted to
          the local (parent-relative) space of the cutscene skeleton with `TRSTransform.left_divide()`. The immediate
          children of the part root are the part's cutscene root bones and use identity as their parent (root motion
          is applied separately by the game), and recursion stops at untracked bones exactly as the forward pass does.
    Every other track in `local_frames` is left untouched. `bone_frames` may be `None` for root-motion-only parts.
    """
    frame_count = len(local_frames)
    if len(root_motion) != frame_count:
        raise CutsceneExportError(
            f"Part '{remo_part.name}' has {len(root_motion)} root motion frames but cut '{cut.name}' has "
            f"{frame_count} frames. Cut lengths cannot be changed when patching a source RemoBND."
        )
    if bone_frames is not None and len(bone_frames) != frame_count:
        raise CutsceneExportError(
            f"Part '{remo_part.name}' has {len(bone_frames)} bone frames but cut '{cut.name}' has {frame_count} frames."
        )

    animation = cut.animation
    remo_part_root_bone, part_bones = animation.get_root_and_part_bones(
        remo_part.name, bone_prefix=remo_part.map_part_name + "_"
    )
    bone_track_indices = {
        bone_index: track_index
        for track_index, bone_index in enumerate(animation.animation_container.hkx_binding.transformTrackToBoneIndices)
    }
    root_track_index = bone_track_indices[remo_part_root_bone.index]
    real_name_by_bone_name = {bone.name: real_name for real_name, bone in part_bones.items()}

    for frame_index in range(frame_count):
        track_transforms = local_frames[frame_index]
        track_transforms[root_track_index] = root_motion[frame_index].copy()
        if bone_frames is None:
            continue
        frame = bone_frames[frame_index]

        def write_local(bone, parent_world: TRSTransform | None):
            track_index = bone_track_indices.get(bone.index)
            if track_index is None:
                return  # untracked bone: forward pass did not recurse into its children either
            real_name = real_name_by_bone_name[bone.name]
            try:
                world = frame[real_name]
            except KeyError:
                raise CutsceneExportError(
                    f"No sampled transform for bone '{real_name}' of part '{remo_part.name}' in cut '{cut.name}'."
                )
            track_transforms[track_index] = world.copy() if parent_world is None else parent_world.left_divide(world)
            for child in bone.children:
                write_local(child, world)

        for part_root_bone in remo_part_root_bone.children:
            write_local(part_root_bone, None)


def make_track_rotations_continuous(local_frames: list[list[TRSTransform]]) -> None:
    """Negate any track quaternion whose dot product with the previous frame's is negative, in place.

    Both quaternion signs are the same rotation, but spline compression (and interpolation) between q and -q would
    take the long way round.
    """
    if not local_frames:
        return
    track_count = len(local_frames[0])
    for track_index in range(track_count):
        last = local_frames[0][track_index].rotation
        for frame in local_frames[1:]:
            transform = frame[track_index]
            if np.dot(transform.rotation.data, last.data) < 0.0:
                transform.rotation = -transform.rotation
            last = transform.rotation


def build_cut_animation_hkx(cut: RemoCut, local_frames: list[list[TRSTransform]], spline: bool) -> None:
    """Replace `cut.animation`'s Havok animation and binding with new ones built from `local_frames`, in place.

    The new animation is created as a plain DSR `AnimationHKX` (which knows how to spline-compress itself via the
    hk2010 `CompressAnim.exe` round trip) and then spliced into the cut's root container, so the template's
    `hkaSkeleton` (the amalgamated cutscene skeleton) is kept exactly. `spline=False` writes uncompressed interleaved
    data, which is lossless but is not known to work in-game.
    """
    container = cut.animation.animation_container
    track_bone_indices = list(container.hkx_binding.transformTrackToBoneIndices)
    track_names = [bone.name for bone in cut.animation.skeleton.bones]
    if len(track_names) != len(track_bone_indices):
        # Tracks are a subset of bones; annotate each track with its bone's name.
        bone_names = track_names
        track_names = [bone_names[bone_index] for bone_index in track_bone_indices]

    plain_hkx = AnimationHKX.from_minimal_data_interleaved(
        frame_transforms=local_frames,
        transform_track_bone_indices=track_bone_indices,
        root_motion_array=None,
        original_skeleton_name=container.hkx_binding.originalSkeletonName,
        frame_rate=30.0,
        skeleton_for_armature_to_local=None,  # already local
        track_names=track_names,
    )
    if spline:
        plain_hkx = plain_hkx.to_spline_hkx()  # WINDOWS-ONLY (`CompressAnim.exe`)

    new_animation = plain_hkx.animation_container.hkx_animation
    new_binding = plain_hkx.animation_container.hkx_binding
    new_binding.animation = new_animation
    hka_container = container.hkx_container
    hka_container.animations = [new_animation]
    hka_container.bindings = [new_binding]
    # Re-wrap so `cut.animation.animation_container` reflects the new animation (e.g. for immediate re-reading).
    cut.animation.animation_container = type(container)(cut.animation.HAVOK_MODULE, hka_container)


def find_cut_hkx_entry(remobnd: RemoBND, cut: RemoCut) -> BinderEntry:
    """Recover the `BinderEntry` for a cut's HKX, matching `RemoBND.__post_init__`'s logic (`aNNNN.hkx` -> `cutNNNN`)."""
    for entry in remobnd.entries:
        match = CUT_HKX_RE.match(entry.name)
        if match and f"cut{match.group(1)}" == cut.name:
            return entry
    raise CutsceneExportError(f"Could not find HKX binder entry for cut '{cut.name}'.")


def find_cut_sibcam_entry(remobnd: RemoBND, cut: RemoCut) -> BinderEntry:
    return remobnd.find_entry_by_path(f"\\{cut.name}\\camera_win32.sibcam")


def replace_cut_hkx_entry(remobnd: RemoBND, cut: RemoCut) -> None:
    """Pack the (modified) cut animation HKX back into its binder entry."""
    find_cut_hkx_entry(remobnd, cut).set_from_binary_file(cut.animation)


def write_cut_sibcam(
    remobnd: RemoBND,
    cut: RemoCut,
    camera_samples: tp.Sequence[tuple[Vector3, EulerRad, float]],
) -> None:
    """Overwrite the clipped frames of `cut.sibcam` with new `(position, rotation, fov)` samples (game space, one per
    clipped frame in order) and pack it back into its binder entry.

    Frames outside the clip range (pre-roll the game never shows) are kept from the template, as are the clip range,
    camera name and per-frame scale. Derived data is regenerated the way vanilla files store it:
        - `position_diff_prev`/`rotation_diff_prev` are central differences over consecutive frames (zero at both
          ends), i.e. Catmull-Rom tangents;
        - FoV is baked to one keyframe per clipped frame on the cut's absolute frame axis, with `tan_out` the
          Catmull-Rom slope and `tan_in = -tan_out`, and `initial_fov` is the first clipped frame's FoV.
    """
    sibcam = cut.sibcam
    clipped_indices = [
        i for i, frame in enumerate(sibcam.full_camera_animation)
        if sibcam.clip_start_t <= frame.t <= sibcam.clip_end_t
    ]
    if len(clipped_indices) != len(camera_samples):
        raise CutsceneExportError(
            f"Cut '{cut.name}' SIBCAM has {len(clipped_indices)} clipped camera frames but {len(camera_samples)} were "
            f"sampled from Blender. Cut lengths cannot be changed when patching a source RemoBND."
        )

    new_frames = [
        CameraFrameTransform(
            t=frame.t,
            position=frame.position,
            position_diff_prev=Vector3.zero(),
            rotation=frame.rotation,
            rotation_diff_prev=EulerRad.zero(),
            scale=frame.scale,
        )
        for frame in sibcam.full_camera_animation
    ]
    _set_sibcam_frames(sibcam, new_frames, clipped_indices, camera_samples)
    find_cut_sibcam_entry(remobnd, cut).set_from_binary_file(sibcam)


def build_new_sibcam(
    camera_samples: tp.Sequence[tuple[Vector3, EulerRad, float]],
    camera_name: str = "FreeCam01",
) -> SIBCAM:
    """Create a SIBCAM from scratch for one cut: one camera frame per sample at `t = 0, 1, ...` (the whole animation is
    the clip), unit scale, and derived data as in `write_cut_sibcam()`. 'FreeCam01' is the usual vanilla camera name.
    """
    if len(camera_samples) < 1:
        raise CutsceneExportError("A cut needs at least one camera sample.")
    new_frames = [
        CameraFrameTransform(
            t=i,
            position=Vector3.zero(),
            position_diff_prev=Vector3.zero(),
            rotation=EulerRad.zero(),
            rotation_diff_prev=EulerRad.zero(),
            scale=Vector3.one(),
        )
        for i in range(len(camera_samples))
    ]
    sibcam = SIBCAM(
        camera_name=camera_name,
        clip_start_t=0,
        clip_end_t=len(camera_samples) - 1,
        full_camera_animation=new_frames,
    )
    _set_sibcam_frames(sibcam, new_frames, list(range(len(camera_samples))), camera_samples)
    return sibcam


def _set_sibcam_frames(
    sibcam: SIBCAM,
    new_frames: list[CameraFrameTransform],
    clipped_indices: tp.Sequence[int],
    camera_samples: tp.Sequence[tuple[Vector3, EulerRad, float]],
) -> None:
    """Write `camera_samples` into `new_frames[clipped_indices]`, regenerate the derived Catmull-Rom data and baked FoV
    keyframes, and install `new_frames` in `sibcam`."""
    for i, (position, rotation, _) in zip(clipped_indices, camera_samples, strict=True):
        new_frames[i].position = Vector3(position)
        new_frames[i].rotation = EulerRad(rotation)

    for prev_frame, frame, next_frame in zip(new_frames[:-2], new_frames[1:-1], new_frames[2:]):
        frame.position_diff_prev = Vector3(
            (np.array(next_frame.position, dtype=float) - np.array(prev_frame.position, dtype=float)) / 2.0
        )
        frame.rotation_diff_prev = EulerRad(
            (np.array(next_frame.rotation, dtype=float) - np.array(prev_frame.rotation, dtype=float)) / 2.0
        )

    fov_t = [new_frames[i].t for i in clipped_indices]
    fovs = [float(fov) for _, _, fov in camera_samples]
    tangents = get_catmull_rom_tangents(fovs, fov_t)
    sibcam.fov_keyframes = [
        FoVKeyframe(fov_t=t, fov=fov, tan_in=-tangent, tan_out=tangent)
        for t, fov, tangent in zip(fov_t, fovs, tangents)
    ]
    sibcam.fov_keyframe_count = len(sibcam.fov_keyframes)
    sibcam.initial_fov = fovs[0] if fovs else sibcam.initial_fov
    sibcam.full_camera_animation = new_frames
