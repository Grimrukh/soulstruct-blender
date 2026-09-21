"""Helpers shared by cutscene import and export."""
from __future__ import annotations

__all__ = [
    "BL_PART_CLASSES",
    "find_remo_part_msb_part",
    "fov_to_lens",
    "lens_to_fov",
    "evaluate_fov_keyframes",
    "get_clip_fov_values",
    "get_catmull_rom_tangents",
]

import math
import typing as tp

import bpy

from soulstruct.base.animations.sibcam import SIBCAM, FoVKeyframe
from soulstruct.havok.fromsoft.darksouls1r.remobnd import RemoPart, RemoPartType

from ..base.operators import LoggingOperator
from ..exceptions import SoulstructTypeError
from ..msb.types.adapters import get_part_game_name
from ..msb.types.darksouls1r import *

if tp.TYPE_CHECKING:
    from ..msb.types.base.parts import BaseBlenderMSBPart


BL_PART_CLASSES = {
    RemoPartType.Player: BlenderMSBPlayerStart,
    RemoPartType.Character: BlenderMSBCharacter,
    RemoPartType.Object: BlenderMSBObject,
    RemoPartType.MapPiece: BlenderMSBMapPiece,
    RemoPartType.Collision: BlenderMSBCollision,
}


def find_remo_part_msb_part(
    operator: LoggingOperator,
    context: bpy.types.Context,
    remo_part: RemoPart,
    bl_part_class: type[BaseBlenderMSBPart],
    report_missing=True,
) -> BaseBlenderMSBPart | None:
    """Find the already-imported MSB Part (Mesh object) that `remo_part` animates.

    Parts are looked up by game name inside the `{msb_stem} {Subtype} Parts` collection of the map the cutscene part
    belongs to (which may be another map for 'AXXBXX_'-prefixed parts), never by scanning all objects, so identically
    named parts in other loaded maps cannot be confused.
    """
    area, block = remo_part.map_area_block
    map_stem = f"m{area:02d}_{block:02d}_00_00"
    msb_stem = context.scene.soulstruct_settings.get_latest_map_stem_version(map_stem)
    collection_name = f"{msb_stem} {bl_part_class.MSB_ENTRY_SUBTYPE.get_nice_name()} Parts"
    try:
        # TODO: Restrict to Scene collections?
        part_collection = bpy.data.collections[collection_name]
    except KeyError:
        if report_missing:
            operator.error(
                f"Could not find MSB Part collection '{collection_name}' for cutscene Part "
                f"'{remo_part.map_part_name}' (full Remo name '{remo_part.name}')."
            )
        return None

    for obj in part_collection.objects:  # immediate child objects only
        # TODO: Use proper 'find object of type' utility.
        if obj.type == "MESH" and get_part_game_name(obj.name) == remo_part.map_part_name:
            try:
                return bl_part_class(obj)
            except SoulstructTypeError:
                if report_missing:
                    operator.error(
                        f"Found Mesh object '{obj.name}' in collection '{part_collection.name}', but it "
                        f"is not a valid `{bl_part_class.__name__}` object."
                    )
                return None

    if report_missing:
        operator.error(
            f"Could not find MSB Part '{remo_part.map_part_name}' in MSB collection '{part_collection.name}'."
        )
    return None


# region Camera FoV

def fov_to_lens(fov: float, sensor_width: float) -> float:
    """Convert a (horizontal) FoV in radians to a Blender focal length in mm for the given sensor width in mm."""
    return sensor_width / (2.0 * math.tan(fov / 2.0))


def lens_to_fov(lens: float, sensor_width: float) -> float:
    """Inverse of `fov_to_lens()`."""
    return 2.0 * math.atan(sensor_width / (2.0 * lens))


def evaluate_fov_keyframes(fov_keyframes: tp.Sequence[FoVKeyframe], t: float, default_fov: float) -> float:
    """Evaluate a SIBCAM FoV keyframe curve at time `t`, which is on the same absolute cut frame axis as camera
    transform frame `t` values (NOT rescaled to the clip, and not necessarily starting at 0).

    Keyframes are cubic Hermite keys: `tan_out` is the outgoing slope (radians per frame) and `tan_in` is the NEGATED
    incoming slope, as vanilla files always store `tan_in == -tan_out` with Catmull-Rom (central difference) values.
    The curve holds its first/last value outside the keyframe range, and a cut with no keyframes uses `default_fov`
    (the SIBCAM header's `initial_fov`).
    """
    if not fov_keyframes:
        return default_fov
    if len(fov_keyframes) == 1 or t <= fov_keyframes[0].fov_t:
        return fov_keyframes[0].fov
    if t >= fov_keyframes[-1].fov_t:
        return fov_keyframes[-1].fov

    # Find segment `[k0, k1]` containing `t` (keyframe count is small enough for a linear scan).
    for k0, k1 in zip(fov_keyframes[:-1], fov_keyframes[1:]):
        if k0.fov_t <= t <= k1.fov_t:
            break
    else:  # pragma: no cover  (unreachable given the range checks above)
        return fov_keyframes[-1].fov

    dt = float(k1.fov_t - k0.fov_t)
    if dt <= 0.0:
        return k1.fov
    u = (t - k0.fov_t) / dt
    m0 = k0.tan_out * dt
    m1 = -k1.tan_in * dt
    u2 = u * u
    u3 = u2 * u
    h00 = 2 * u3 - 3 * u2 + 1
    h10 = u3 - 2 * u2 + u
    h01 = -2 * u3 + 3 * u2
    h11 = u3 - u2
    return h00 * k0.fov + h10 * m0 + h01 * k1.fov + h11 * m1


def get_clip_fov_values(sibcam: SIBCAM) -> list[float]:
    """Evaluate the SIBCAM FoV curve at every clipped camera frame (same order/length as
    `sibcam.get_clipped_camera_animation()`)."""
    return [
        evaluate_fov_keyframes(sibcam.fov_keyframes, frame.t, sibcam.initial_fov)
        for frame in sibcam.get_clipped_camera_animation()
    ]


def get_catmull_rom_tangents(values: tp.Sequence[float], times: tp.Sequence[float]) -> list[float]:
    """Central-difference slopes at each sample, with one-sided differences at the ends (zero for a single sample).

    This is how vanilla SIBCAM files derive `tan_out` (and `tan_in = -tan_out`) for baked per-frame FoV keyframes,
    and also how `CameraFrameTransform.position_diff_prev`/`rotation_diff_prev` are computed (with zero at both ends
    in that case).
    """
    n = len(values)
    if n < 2:
        return [0.0] * n
    tangents = []
    for i in range(n):
        if i == 0:
            i0, i1 = 0, 1
        elif i == n - 1:
            i0, i1 = n - 2, n - 1
        else:
            i0, i1 = i - 1, i + 1
        dt = float(times[i1] - times[i0])
        tangents.append((values[i1] - values[i0]) / dt if dt > 0.0 else 0.0)
    return tangents

# endregion
