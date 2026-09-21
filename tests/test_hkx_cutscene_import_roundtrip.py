"""Headless HKX cutscene (RemoBND) import/export round-trip tests (Dark Souls: Remastered only).

Approach
--------
A cutscene animates MSB Parts that must already exist in Blender, so each case first imports the cutscene's MSB
with model import restricted (by regex) to the character/object models the cutscene animates -- every other Part
gets a placeholder mesh, which keeps the MSB import to a few seconds. The cutscene is then imported with
``import_scene.hkx_cutscene`` and exported with ``export_scene.hkx_cutscene``, which patches the original RemoBND
(the "template") with the Blender animation data.

Round-trip methodology per case
---------------------------------
1. Import the MSB (filtered models) and the cutscene. Check the shared Action's cut metadata, and that the camera
   and every expected part Armature are bound to it.
2. Export TWICE, in this order, each time re-parsing the exported RemoBND and comparing against the original:
   a. ``force_interleaved=True`` -- uncompressed interleaved HKX. The only expected loss is float32 storage, so a
      tight tolerance isolates the add-on's own maths: armature-space <-> cutscene-local conversion, root motion,
      the cutscene root-bone rule (part root bones ignore their FLVER parents), and the coordinate change of basis.
   b. Default spline-compressed export (``CompressAnim.exe``, Windows only), with a looser tolerance for genuine
      compression loss.
   Every cut's HKX is compared track-by-track in LOCAL (parent-relative) space, which is what the game reads, for
   ALL parts: parts animated in Blender must reproduce the original data, and parts that are not (Map Pieces,
   Collisions) must be carried over from the template untouched.
3. The SIBCAM of every cut is compared: clipped camera positions/rotations, clip range, and the FoV evaluated at
   every clipped frame (the original's sparse Hermite keyframes vs. the exported per-frame keyframes).
4. The interleaved export is re-imported into Blender and the pose/transform F-curves of every bound object are
   compared with the original import at a spread of keyframe times.

Run with:
    blender --background --python tests/test_hkx_cutscene_import_roundtrip.py
"""
import sys
import tempfile
import traceback
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import bpy
import numpy as np
import bl_test_utils as T

T.enable_addon()

from soulstruct.config import Config
from soulstruct.havok.fromsoft.darksouls1r.remobnd import RemoBND

from bl_ext.user_default.io_soulstruct.soulstruct.blender.cutscene.utilities import get_clip_fov_values


# ---------------------------------------------------------------------------
# Test case descriptor
# ---------------------------------------------------------------------------

@dataclass
class CutsceneImportCase(T.ImportCaseBase):
    """One RemoBND cutscene import/export round-trip test.

    ``directory`` / ``filename`` -> RemoBND (primary source).
    ``msb_dir`` / ``msb_filename`` -> MSB of the cutscene's map (its Parts must be imported first).
    ``model_name_regex`` -> which MSB models to actually import (others become placeholders).
    ``expect_animated_parts`` -> RemoPart names whose Blender objects must end up bound to the cutscene Action.
    """

    msb_dir: Path | str = ""
    msb_filename: str = ""
    model_name_regex: str = ""
    expect_animated_parts: list[str] = field(default_factory=list)

    def check_skip_reason(self) -> str | None:
        if not self.msb_dir or not Path(self.msb_dir).is_dir():
            return f"MSB directory not found: {self.msb_dir}"
        msb_path = Path(self.msb_dir) / self.msb_filename
        if not self.msb_filename or not msb_path.exists():
            return f"MSB not found: {msb_path}"
        return super().check_skip_reason()


# ---------------------------------------------------------------------------
# Test case definitions
# ---------------------------------------------------------------------------

CUTSCENE_TEST_CASES: list[CutsceneImportCase] = [
    CutsceneImportCase(
        name="DSR / scn100100 (m10_01 Undead Parish: Andre bell lever)",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "remo",
        filename="scn100100.remobnd.dcx",
        msb_dir=Config.DSR_PATH / "map/MapStudio",
        msb_filename="m10_01_00_00.msb",
        model_name_regex=r"^(c0000|o1202|o1303)$",
        expect_animated_parts=["c0000_0000", "o1202", "o1303"],
        tags=["cutscene", "small"],
    ),
    CutsceneImportCase(
        name="DSR / scn100110 (m10_01 Undead Parish: Bell Gargoyles intro)",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "remo",
        filename="scn100110.remobnd.dcx",
        msb_dir=Config.DSR_PATH / "map/MapStudio",
        msb_filename="m10_01_00_00.msb",
        model_name_regex=r"^(c0000|c5350)$",
        expect_animated_parts=["c0000_0000", "c5350_0000", "c5350_0001"],
        tags=["cutscene", "large"],
    ),
]

# ---------------------------------------------------------------------------
# Tolerances
# ---------------------------------------------------------------------------

# Uncompressed export: only float32 storage loss is expected in HKX local transforms.
INTERLEAVED_ATOL = 1e-4
# Spline-compressed export (`CompressAnim.exe` tolerance 0.001; see the HKX animation round-trip suite).
COMPRESSED_ATOL = 5e-3
# SIBCAM camera transforms are stored as float32 and pass through Blender doubles unchanged.
CAMERA_ATOL = 1e-5
# FoV goes through a focal-length conversion (float64) and back.
FOV_ATOL = 1e-5
# Re-imported Blender F-curves vs. the original import (both derived from float32 HKX data).
FCURVE_ATOL = 1e-3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_remobnd(path: Path) -> RemoBND:
    remobnd = RemoBND.from_path(path)
    remobnd.load_remo_parts()  # also converts every cut animation to interleaved
    return remobnd


def _get_cut_local_frames(remobnd: RemoBND) -> dict[str, tuple[list[str], np.ndarray]]:
    """Return ``{cut_name: (track_names, (frame_count, track_count, 10) array)}`` of local-space transforms with
    columns ``tx ty tz qx qy qz qw sx sy sz``."""
    result = {}
    for cut in remobnd.cuts:
        container = cut.animation.animation_container
        if not container.is_interleaved:
            cut.animation.animation_container = container = container.to_interleaved_container()
        container.load_interleaved_data()
        bone_names = [bone.name for bone in cut.animation.skeleton.bones]
        track_names = [bone_names[i] for i in container.get_track_bone_indices()]
        data = np.array([[transform.ravel() for transform in frame] for frame in container.interleaved_data])
        result[cut.name] = (track_names, data)
    return result


def _compare_cut_local_frames(
    original: dict[str, tuple[list[str], np.ndarray]],
    exported: dict[str, tuple[list[str], np.ndarray]],
    atol: float,
) -> list[str]:
    mismatches = []
    for cut_name, (orig_names, orig) in original.items():
        if cut_name not in exported:
            mismatches.append(f"cut '{cut_name}' missing from exported RemoBND")
            continue
        exp_names, exp = exported[cut_name]
        if orig_names != exp_names:
            mismatches.append(f"cut '{cut_name}': track names changed ({len(orig_names)} -> {len(exp_names)})")
            continue
        if orig.shape != exp.shape:
            mismatches.append(f"cut '{cut_name}': shape {orig.shape} -> {exp.shape}")
            continue
        for label, cols in (("translation", slice(0, 3)), ("scale", slice(7, 10))):
            diff = np.abs(orig[:, :, cols] - exp[:, :, cols])
            if diff.max() > atol:
                frame, track, comp = np.unravel_index(diff.argmax(), diff.shape)
                mismatches.append(
                    f"cut '{cut_name}' track '{orig_names[track]}' {label}[{comp}] frame {frame}: "
                    f"orig={orig[frame, track, cols][comp]:.6f}, exported={exp[frame, track, cols][comp]:.6f}, "
                    f"diff={diff[frame, track, comp]:.6f}"
                )
        q_orig = orig[:, :, 3:7] / np.linalg.norm(orig[:, :, 3:7], axis=2, keepdims=True)
        q_exp = exp[:, :, 3:7] / np.linalg.norm(exp[:, :, 3:7], axis=2, keepdims=True)
        dot_dev = np.abs(np.abs((q_orig * q_exp).sum(axis=2)) - 1.0)
        if dot_dev.max() > atol:
            frame, track = np.unravel_index(dot_dev.argmax(), dot_dev.shape)
            mismatches.append(
                f"cut '{cut_name}' track '{orig_names[track]}' rotation frame {frame}: "
                f"quaternion |dot|-1={dot_dev[frame, track]:.6f}"
            )
    return mismatches


def _compare_sibcams(original: RemoBND, exported: RemoBND) -> list[str]:
    mismatches = []
    exported_cuts = {cut.name: cut for cut in exported.cuts}
    for cut in original.cuts:
        if cut.name not in exported_cuts:
            mismatches.append(f"cut '{cut.name}' missing from exported RemoBND")
            continue
        orig_sibcam = cut.sibcam
        exp_sibcam = exported_cuts[cut.name].sibcam
        if (orig_sibcam.clip_start_t, orig_sibcam.clip_end_t) != (exp_sibcam.clip_start_t, exp_sibcam.clip_end_t):
            mismatches.append(f"cut '{cut.name}': clip range changed")
        if orig_sibcam.full_frame_count != exp_sibcam.full_frame_count:
            mismatches.append(
                f"cut '{cut.name}': camera frame count {orig_sibcam.full_frame_count} -> "
                f"{exp_sibcam.full_frame_count}"
            )
            continue
        orig_frames = orig_sibcam.get_clipped_camera_animation()
        exp_frames = exp_sibcam.get_clipped_camera_animation()
        for i, (o, e) in enumerate(zip(orig_frames, exp_frames)):
            if o.t != e.t:
                mismatches.append(f"cut '{cut.name}' clipped frame {i}: t {o.t} -> {e.t}")
                break
            pos_diff = np.abs(np.array(o.position, dtype=float) - np.array(e.position, dtype=float)).max()
            rot_diff = np.abs(np.array(o.rotation, dtype=float) - np.array(e.rotation, dtype=float)).max()
            if pos_diff > CAMERA_ATOL or rot_diff > CAMERA_ATOL:
                mismatches.append(
                    f"cut '{cut.name}' clipped frame {i} (t={o.t}): position diff={pos_diff:.6f}, "
                    f"rotation diff={rot_diff:.6f}"
                )
                break
        orig_fov = np.array(get_clip_fov_values(orig_sibcam))
        exp_fov = np.array(get_clip_fov_values(exp_sibcam))
        fov_diff = np.abs(orig_fov - exp_fov)
        if fov_diff.size and fov_diff.max() > FOV_ATOL:
            i = int(fov_diff.argmax())
            mismatches.append(
                f"cut '{cut.name}' clipped frame {i}: FoV orig={orig_fov[i]:.6f}, exported={exp_fov[i]:.6f}"
            )
    return mismatches


def _get_action_channel_samples(action: bpy.types.Action, frames: list[float]) -> dict[str, dict]:
    """``{slot_display_name: {(data_path, index): [values...]}}`` for every slot of the cutscene Action."""
    strip = action.layers[0].strips[0]
    samples = {}
    for slot in action.slots:
        channelbag = strip.channelbag(slot, ensure=False)
        if channelbag is None:
            continue
        key = f"{slot.target_id_type}:{slot.name_display}"
        samples[key] = {
            (fc.data_path, fc.array_index): [fc.evaluate(f) for f in frames] for fc in channelbag.fcurves
        }
    return samples


def _compare_channel_samples(original: dict[str, dict], reimported: dict[str, dict], atol: float) -> list[str]:
    mismatches = []
    for slot_key, orig_channels in original.items():
        if slot_key not in reimported:
            mismatches.append(f"slot '{slot_key}' missing from re-imported Action")
            continue
        reimp_channels = reimported[slot_key]
        checked_quat_paths = set()
        for (data_path, index), orig_values in orig_channels.items():
            if "rotation_quaternion" in data_path:
                if data_path in checked_quat_paths:
                    continue
                checked_quat_paths.add(data_path)
                if not all((data_path, i) in orig_channels and (data_path, i) in reimp_channels for i in range(4)):
                    mismatches.append(f"slot '{slot_key}' channel '{data_path}' incomplete in re-imported Action")
                    continue
                for frame_i in range(len(orig_values)):
                    q_orig = [orig_channels[data_path, i][frame_i] for i in range(4)]
                    q_reimp = [reimp_channels[data_path, i][frame_i] for i in range(4)]
                    dot = sum(a * b for a, b in zip(q_orig, q_reimp))
                    if abs(abs(dot) - 1.0) > atol:
                        mismatches.append(
                            f"slot '{slot_key}' '{data_path}' sample {frame_i}: quaternion |dot|-1={abs(abs(dot) - 1):.6f}"
                        )
                        break
                continue
            if (data_path, index) not in reimp_channels:
                mismatches.append(f"slot '{slot_key}' channel ({data_path!r}, {index}) missing from re-imported Action")
                continue
            for frame_i, (o, r) in enumerate(zip(orig_values, reimp_channels[data_path, index])):
                if abs(o - r) > atol:
                    mismatches.append(
                        f"slot '{slot_key}' ({data_path!r}, {index}) sample {frame_i}: orig={o:.6f}, "
                        f"reimport={r:.6f}"
                    )
                    break
    return mismatches


def _summarize(mismatches: list[str], limit=5) -> str:
    summary = "\n  ".join(mismatches[:limit])
    if len(mismatches) > limit:
        summary += f"\n  ... and {len(mismatches) - limit} more"
    return summary


def _find_cutscene_camera(action: bpy.types.Action) -> bpy.types.Object | None:
    for obj in bpy.data.objects:
        if obj.type == "CAMERA" and obj.animation_data and obj.animation_data.action == action:
            return obj
    return None


# ---------------------------------------------------------------------------
# Per-case test runner
# ---------------------------------------------------------------------------

def run_case(case: CutsceneImportCase):
    remobnd_path = case.source_path

    # ---- 1. Import MSB (filtered models) and cutscene ----
    T.clear_scene()
    T.set_game(case.game_enum)
    settings = bpy.context.scene.soulstruct_settings
    settings.game_settings.game_root_str = str(Config.DSR_PATH)
    bpy.context.scene.flver_import_settings.import_textures = False

    msb_import_settings = bpy.context.scene.msb_import_settings
    msb_import_settings.import_map_piece_models = False
    msb_import_settings.import_collision_models = False
    msb_import_settings.import_navmesh_models = False
    msb_import_settings.import_object_models = True
    msb_import_settings.import_character_models = True
    msb_import_settings.model_name_filter_match_mode = "REGEX"
    msb_import_settings.model_name_filter = case.model_name_regex

    try:
        result = bpy.ops.import_scene.any_msb("EXEC_DEFAULT", filepath=str(Path(case.msb_dir) / case.msb_filename))
    except Exception as ex:
        traceback.print_exc()
        T.fail(case.name, f"MSB import raised exception: {ex}")
        return
    if "FINISHED" not in result:
        T.fail(case.name, f"MSB import returned {result}")
        return

    try:
        result = bpy.ops.import_scene.hkx_cutscene("EXEC_DEFAULT", filepath=str(remobnd_path))
    except Exception as ex:
        traceback.print_exc()
        T.fail(case.name, f"Cutscene import raised exception: {ex}")
        return
    if "FINISHED" not in result:
        T.fail(case.name, f"Cutscene import returned {result}")
        return

    original = _load_remobnd(remobnd_path)
    cutscene_name = original.cutscene_name

    action = bpy.data.actions.get(cutscene_name)
    if action is None:
        T.fail(case.name, f"No Action named '{cutscene_name}' after cutscene import")
        return
    props = action.cutscene
    if not props.is_cutscene or props.cutscene_name != cutscene_name:
        T.fail(case.name, f"Action '{action.name}' has no cutscene metadata")
        return
    expected_cuts = [(cut.name, cut.sibcam.clip_frame_count) for cut in original.cuts]
    actual_cuts = [(cut.name, cut.frame_count) for cut in props.cuts]
    if actual_cuts != expected_cuts:
        T.fail(case.name, f"Action cut metadata {actual_cuts} != RemoBND cuts {expected_cuts}")
        return
    total_frames = sum(count for _, count in expected_cuts)
    expected_end = (total_frames - 1) * props.bl_frames_per_game_frame
    if abs(action.frame_range[1] - expected_end) > 1e-6 or abs(action.frame_range[0]) > 1e-6:
        T.fail(case.name, f"Action frame range {tuple(action.frame_range)} != (0, {expected_end})")
        return

    camera = _find_cutscene_camera(action)
    if camera is None:
        T.fail(case.name, "No Camera bound to the cutscene Action")
        return

    bound_names = {obj.name for obj in bpy.data.objects if obj.animation_data and obj.animation_data.action == action}
    for part_name in case.expect_animated_parts:
        if not any(name.startswith(part_name) for name in bound_names):
            T.fail(case.name, f"No object for cutscene part '{part_name}' is bound to the Action (bound: {bound_names})")
            return

    original_local_frames = _get_cut_local_frames(original)

    # Sample the original Blender channels at a spread of keyframe times (keyframes are exact for LINEAR curves).
    step = props.bl_frames_per_game_frame
    check_frames = [float(i * step) for i in np.linspace(0, total_frames - 1, 12).astype(int)]
    original_samples = _get_action_channel_samples(action, check_frames)

    # ---- 2./3. Export twice and compare against the original RemoBND ----
    export_settings = bpy.context.scene.cutscene_export_settings
    export_settings.export_camera = True

    stages = (
        ("interleaved (uncompressed)", True, INTERLEAVED_ATOL),
        ("compressed", False, COMPRESSED_ATOL),
    )
    interleaved_export_path = None

    with tempfile.TemporaryDirectory() as tmpdir:
        for stage_label, force_interleaved, atol in stages:
            export_settings.force_interleaved = force_interleaved
            export_path = Path(tmpdir) / f"{cutscene_name}_{'interleaved' if force_interleaved else 'spline'}.remobnd.dcx"
            T.activate(camera)
            try:
                result = bpy.ops.export_scene.hkx_cutscene(
                    "EXEC_DEFAULT",
                    filepath=str(export_path),
                    source_remobnd_path=str(remobnd_path),
                )
            except Exception as ex:
                traceback.print_exc()
                T.fail(case.name, f"[{stage_label}] Cutscene export raised exception: {ex}")
                return
            if "FINISHED" not in result:
                T.fail(case.name, f"[{stage_label}] Cutscene export returned {result}")
                return
            if not export_path.is_file() or export_path.stat().st_size == 0:
                T.fail(case.name, f"[{stage_label}] Exported RemoBND missing or empty: {export_path}")
                return

            try:
                exported = _load_remobnd(export_path)
                exported_local_frames = _get_cut_local_frames(exported)
            except Exception as ex:
                traceback.print_exc()
                T.fail(case.name, f"[{stage_label}] Could not parse exported RemoBND: {ex}")
                return

            mismatches = _compare_cut_local_frames(original_local_frames, exported_local_frames, atol)
            if mismatches:
                T.fail(
                    case.name,
                    f"[{stage_label}] HKX local-space check failed ({len(mismatches)} mismatch(es), atol={atol}):"
                    f"\n  {_summarize(mismatches)}",
                )
                return

            mismatches = _compare_sibcams(original, exported)
            if mismatches:
                T.fail(
                    case.name,
                    f"[{stage_label}] SIBCAM check failed ({len(mismatches)} mismatch(es)):\n  {_summarize(mismatches)}",
                )
                return

            if force_interleaved:
                interleaved_export_path = export_path

        # ---- 4. Re-import the interleaved export and compare Blender channels ----
        try:
            result = bpy.ops.import_scene.hkx_cutscene(
                "EXEC_DEFAULT",
                filepath=str(interleaved_export_path),
                camera_name="{CutsceneName} Camera (reimport)",
            )
        except Exception as ex:
            traceback.print_exc()
            T.fail(case.name, f"[reimport] Cutscene re-import raised exception: {ex}")
            return
        if "FINISHED" not in result:
            T.fail(case.name, f"[reimport] Cutscene re-import returned {result}")
            return

    reimported_action = next(
        (a for a in bpy.data.actions if a != action and a.cutscene.cutscene_name == cutscene_name), None
    )
    if reimported_action is None:
        T.fail(case.name, "[reimport] No second cutscene Action found after re-import")
        return
    reimported_samples = _get_action_channel_samples(reimported_action, check_frames)
    # Camera slots are named after the (different) camera name; match them by ID type instead.
    for samples in (original_samples, reimported_samples):
        for key in list(samples):
            if key.startswith("CAMERA:") or key.startswith("OBJECT:") and "Camera" in key:
                samples[key.split(":")[0] + ":<camera>"] = samples.pop(key)
    mismatches = _compare_channel_samples(original_samples, reimported_samples, FCURVE_ATOL)
    if mismatches:
        T.fail(
            case.name,
            f"[reimport] Blender channel check failed ({len(mismatches)} mismatch(es), atol={FCURVE_ATOL}):"
            f"\n  {_summarize(mismatches)}",
        )
        return

    T.ok(
        case.name,
        f"cutscene round-trip OK -- {len(original.cuts)} cut(s), {total_frames} game frames, "
        f"{len(bound_names)} bound object(s); HKX local-space and SIBCAM data consistent (interleaved and "
        f"compressed); re-imported channels consistent over {len(check_frames)} sample frames",
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    import argparse
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--filter-test-names", type=str, default="")
    args = parser.parse_args(argv)
    T.run_case_list(
        CUTSCENE_TEST_CASES,
        run_case,
        suite_name="HKX cutscene import/export",
        filter_test_names=args.filter_test_names,
    )


main()
