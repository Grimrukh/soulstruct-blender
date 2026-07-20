"""Write Armature-space cutscene frames back into a `RemoBND` -- the inverse of
`RemoCut._add_cut_arma_frames`, which `soulstruct-havok` does not provide.

This is the keystone that makes cutscene export possible at all. It is grounded in the forward
parse code (FK accumulation + bone-name prefixing) but is UNTESTED against the game -- verify a
round-trip (import -> export -> import) before trusting it.

Pipeline per cut:
    edit `cut.animation` interleaved transforms in place
    -> animation_container.save_interleaved_data()
    -> animation.to_spline_hkx()        # <-- Windows-only: shells out to CompressAnim.exe
    -> cut_entry.set_from_binary_file(spline_hkx)
and finally `remobnd.write(out_path)` (inherited from `Binder`).
"""
from __future__ import annotations

__all__ = [
    "write_part_frames_into_cut",
    "finalize_cut_animation",
    "find_cut_hkx_entry",
]

import re

from soulstruct.havok.utilities.maths import TRSTransform
from soulstruct.havok.fromsoft.darksouls1r.remobnd import (
    RemoBND, RemoCut, RemoPart, RemoPartAnimationFrame,
)

# Same pattern `RemoBND.__post_init__` uses to identify per-cut HKX entries.
CUT_HKX_RE = re.compile(r"^a(\d+)\.hkx")


"""
TODO: Strategy for building a RemoBND from scratch.
    - Forget TAE for now. (Requires DSAnimStudio.)
    - Each cut needs a HKX file (`RemoAnimationHKX` instance).
        - Hard part, but only because it's easy to mess up.
        - Remember the cutscene animation is a single Blender Action.
    - Each cut needs a SIBCAM file.
        - Relatively straightforward as long as I can figure out how to write all the derivative fields.
"""


def write_part_frames_into_cut(
    cut: RemoCut,
    remo_part: RemoPart,
    frames: list[RemoPartAnimationFrame],
) -> None:
    """Invert `RemoCut._add_cut_arma_frames` for a single part, editing `cut.animation`'s
    interleaved transforms IN PLACE.

    Only the tracks belonging to `remo_part` are overwritten; every other part's tracks in the
    shared cutscene skeleton are left untouched. Does not save/compress/repack — call
    `finalize_cut_animation` once after all parts for the cut have been written.
    """
    animation = cut.animation

    # Mirror the forward path: cutscene bones are prefixed with `{map_part_name}_`.
    remo_part_root_bone, part_bones = animation.get_root_and_part_bones(
        remo_part.name, bone_prefix=remo_part.map_part_name + "_"
    )

    container = animation.animation_container
    if not container.is_interleaved:
        animation.animation_container = container = container.to_interleaved_container()
    container.load_interleaved_data()  # ensure `interleaved_data` is populated
    interleaved_data = container.interleaved_data  # list[list[TRSTransform]] (frame -> track)

    if len(frames) != len(interleaved_data):
        raise ValueError(
            f"Part '{remo_part.name}' has {len(frames)} frames but cut '{cut.name}' animation has "
            f"{len(interleaved_data)} interleaved frames. Frame counts must match exactly "
            f"(downsample 60 FPS Blender keyframes back to game frames before exporting)."
        )

    bone_track_indices = {
        bone_index: track_index
        for track_index, bone_index in enumerate(container.hkx_binding.transformTrackToBoneIndices)
    }
    root_track_index = bone_track_indices[remo_part_root_bone.index]

    # Invert the forward de-prefixing: forward built `{real_flver_name: world_transform}` from
    # `part_bones: {real_flver_name: Bone}`. We need real-name lookup keyed by the prefixed Bone.
    real_name_by_bone_name = {bone.name: real_name for real_name, bone in part_bones.items()}

    for frame_index, frame in enumerate(frames):
        track_transforms = interleaved_data[frame_index]

        # Root motion is stored verbatim on the part's root track (full TRSTransform, world space).
        track_transforms[root_track_index] = frame.root_motion

        # Forward FK:  world[bone] = parent_world @ local[track]
        # Inverse:     local[track] = parent_world.inverse() @ world[bone]
        # Immediate children of the part root use identity as parent world (root motion is separate).
        # Forward stops recursing at any bone without a track, so we mirror that exactly.
        def write_local(bone, parent_world: TRSTransform):
            track_index = bone_track_indices.get(bone.index)
            if track_index is None:
                return  # untracked bone: forward did not recurse into its children either
            real_name = real_name_by_bone_name[bone.name]
            world = frame.bone_transforms[real_name]
            track_transforms[track_index] = parent_world.inverse() @ world
            for child in bone.children:
                write_local(child, world)

        for part_root_bone in remo_part_root_bone.children:
            write_local(part_root_bone, TRSTransform.identity())


def finalize_cut_animation(remobnd: RemoBND, cut: RemoCut) -> None:
    """Flush a cut's edited interleaved data to spline-compressed HKX and repack its binder entry.

    WINDOWS-ONLY: `to_spline_hkx()` invokes the bundled `CompressAnim.exe`. On other platforms
    this raises (run under Wine, or precompute on Windows).
    """
    container = cut.animation.animation_container
    container.save_interleaved_data()  # TRSTransform lists -> Havok transform structs

    spline_hkx = cut.animation.to_spline_hkx()  # interleaved -> spline (CompressAnim.exe)

    entry = find_cut_hkx_entry(remobnd, cut)
    entry.set_from_binary_file(spline_hkx)


def find_cut_hkx_entry(remobnd: RemoBND, cut: RemoCut):
    """Recover the `BinderEntry` for a cut's HKX, matching `RemoBND.__post_init__`'s logic.

    `RemoCut` does not retain its source entry, so we re-derive it: entry name `aNNNN.hkx`
    maps to cut name `cutNNNN`.
    """
    for entry in remobnd.entries:
        match = CUT_HKX_RE.match(entry.name)
        if match and f"cut{match.group(1)}" == cut.name:
            return entry
    raise KeyError(f"Could not find HKX binder entry for cut '{cut.name}'.")
