"""Headless tests for building DSR cutscene RemoBNDs from scratch (``export_scene.hkx_cutscene_new``).

Two cases, both starting from the ``m10_01`` MSB with model import restricted to the cutscene's characters/objects:

1. **Rebuild scn100100 from scratch.** The vanilla cutscene is imported (which links every part it animates into the
   ``Cutscene scn100100`` collection), then exported WITHOUT patching the vanilla file: cutscene skeletons come from
   the models' ANIBNDs, cuts from the Action metadata, the camera from the bound Camera and the TAE events from the
   vanilla file (as the "TAE source"). The result is parsed and compared with the vanilla RemoBND: per cut, every
   vanilla part's root motion and armature-space bone transforms (for bones present in both), the cutscene bone
   hierarchy of every skinned part (which must equal the vanilla one exactly), the clipped camera frames/FoV and the
   copied TAE events. Both uncompressed and spline-compressed exports are checked, and the uncompressed one is
   re-imported to compare Blender channels with the original import.

2. **Author a new cutscene.** ``cutscene.create_hkx_cutscene`` creates an Action/Camera/collection; the player part
   (with the Armature the scn100100 import gave it), an object and a Map Piece are linked in and bound; cuts, root
   motion, a bone pose, a render-hide and the camera are keyframed by script; the RemoBND is built without any
   source file, parsed (parts, per-cut presence, TAE animations) and re-imported to compare channels with the
   authored keyframes.

Run with:
    blender --background --python tests/test_hkx_cutscene_build.py
"""
import math
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
from soulstruct.havok.fromsoft.darksouls1r.remobnd import RemoBND, RemoPartType

from bl_ext.user_default.io_soulstruct.soulstruct.blender.cutscene.utilities import get_clip_fov_values


@dataclass
class CutsceneBuildCase(T.ImportCaseBase):
    msb_dir: Path | str = ""
    msb_filename: str = ""
    model_name_regex: str = ""
    synthetic: bool = False  # case 2

    def check_skip_reason(self) -> str | None:
        if not self.msb_dir or not Path(self.msb_dir).is_dir():
            return f"MSB directory not found: {self.msb_dir}"
        msb_path = Path(self.msb_dir) / self.msb_filename
        if not self.msb_filename or not msb_path.exists():
            return f"MSB not found: {msb_path}"
        return super().check_skip_reason()


CASES: list[CutsceneBuildCase] = [
    CutsceneBuildCase(
        name="DSR / scn100100 rebuilt from scratch",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "remo",
        filename="scn100100.remobnd.dcx",
        msb_dir=Config.DSR_PATH / "map/MapStudio",
        msb_filename="m10_01_00_00.msb",
        model_name_regex=r"^(c0000|o1202|o1303)$",
        tags=["cutscene", "build"],
    ),
    CutsceneBuildCase(
        name="DSR / new cutscene authored in Blender (m10_01)",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "remo",
        filename="scn100100.remobnd.dcx",  # only used to give the player part an Armature
        msb_dir=Config.DSR_PATH / "map/MapStudio",
        msb_filename="m10_01_00_00.msb",
        model_name_regex=r"^(c0000|o1202|o1303)$",
        synthetic=True,
        tags=["cutscene", "build", "authoring"],
    ),
]

# Armature-space transforms accumulate a few float32 local transforms; uncompressed export only loses float32 storage.
INTERLEAVED_ATOL = 2e-3
COMPRESSED_ATOL = 1e-2
CAMERA_ATOL = 1e-5
FOV_ATOL = 1e-5
FCURVE_ATOL = 1e-3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _import_msb(case: CutsceneBuildCase) -> bool:
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
    result = bpy.ops.import_scene.any_msb("EXEC_DEFAULT", filepath=str(Path(case.msb_dir) / case.msb_filename))
    return "FINISHED" in result


def _load_remobnd(path: Path) -> RemoBND:
    remobnd = RemoBND.from_path(path)
    remobnd.load_remo_parts()
    return remobnd


def _all_parts(remobnd: RemoBND) -> dict[str, tuple[RemoPartType, object]]:
    return {part.name: (part_type, part) for part_type, parts in remobnd.all_remo_parts.items() for part in parts.values()}


def _quat_dev(a, b) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return abs(abs(float(np.dot(a, b)) / (np.linalg.norm(a) * np.linalg.norm(b))) - 1.0)


def _compare_transform(label: str, a, b, atol: float, mismatches: list[str]) -> bool:
    t_diff = np.abs(np.asarray(a.translation, dtype=float) - np.asarray(b.translation, dtype=float)).max()
    s_diff = np.abs(np.asarray(a.scale, dtype=float) - np.asarray(b.scale, dtype=float)).max()
    r_dev = _quat_dev(a.rotation.data, b.rotation.data)
    if t_diff > atol or s_diff > atol or r_dev > atol:
        mismatches.append(f"{label}: translation diff={t_diff:.5f}, scale diff={s_diff:.5f}, rotation |dot|-1={r_dev:.5f}")
        return False
    return True


def _compare_parts_arma_frames(original: RemoBND, built: RemoBND, atol: float) -> list[str]:
    """Compare root motion and armature-space bone transforms of every vanilla part in every cut it appears in."""
    mismatches = []
    orig_parts = _all_parts(original)
    built_parts = _all_parts(built)
    for name, (orig_type, orig_part) in orig_parts.items():
        if name not in built_parts:
            mismatches.append(f"vanilla part '{name}' missing from built RemoBND")
            continue
        built_type, built_part = built_parts[name]
        if built_type != orig_type:
            mismatches.append(f"part '{name}': type {orig_type.name} -> {built_type.name}")
            continue
        for cut_name, orig_frames in orig_part.cut_arma_frames.items():
            built_frames = built_part.cut_arma_frames.get(cut_name)
            if built_frames is None:
                mismatches.append(f"part '{name}' missing from built cut '{cut_name}'")
                continue
            if len(built_frames) != len(orig_frames):
                mismatches.append(f"part '{name}' cut '{cut_name}': {len(orig_frames)} -> {len(built_frames)} frames")
                continue
            common_bones = sorted(set(orig_frames[0].bone_transforms) & set(built_frames[0].bone_transforms))
            for i, (o, b) in enumerate(zip(orig_frames, built_frames)):
                if not _compare_transform(f"part '{name}' cut '{cut_name}' frame {i} root motion", o.root_motion, b.root_motion, atol, mismatches):
                    break
                bone_bad = False
                for bone in common_bones:
                    if not _compare_transform(
                        f"part '{name}' cut '{cut_name}' frame {i} bone '{bone}'",
                        o.bone_transforms[bone], b.bone_transforms[bone], atol, mismatches,
                    ):
                        bone_bad = True
                        break
                if bone_bad:
                    break
    return mismatches


def _get_part_bone_hierarchy(remobnd: RemoBND, cut_name: str, part_name: str) -> dict[str, str | None]:
    """``{bone_name: parent_bone_name}`` for a part's cutscene bones (prefixed names), ``None`` = part root child."""
    cut = next(c for c in remobnd.cuts if c.name == cut_name)
    root_bone, part_bones = cut.animation.get_root_and_part_bones(part_name)
    return {
        bone.name: (None if bone.parent is root_bone else bone.parent.name)
        for bone in part_bones.values()
    }


def _compare_bone_hierarchies(original: RemoBND, built: RemoBND) -> list[str]:
    mismatches = []
    for cut in original.cuts:
        if cut.name not in {c.name for c in built.cuts}:
            mismatches.append(f"cut '{cut.name}' missing from built RemoBND")
            continue
        for part_name, root_bone in cut.animation.get_root_bones_by_name().items():
            if not root_bone.children:
                continue
            if part_name not in built.cuts[[c.name for c in built.cuts].index(cut.name)].animation.get_root_bones_by_name():
                mismatches.append(f"cut '{cut.name}': part '{part_name}' missing from built skeleton")
                continue
            orig = _get_part_bone_hierarchy(original, cut.name, part_name)
            new = _get_part_bone_hierarchy(built, cut.name, part_name)
            if orig != new:
                only_orig = sorted(set(orig) - set(new))
                only_new = sorted(set(new) - set(orig))
                diff_parents = sorted(b for b in set(orig) & set(new) if orig[b] != new[b])
                mismatches.append(
                    f"cut '{cut.name}' part '{part_name}' bone hierarchy differs: only vanilla={only_orig[:5]}, "
                    f"only built={only_new[:5]}, different parents={diff_parents[:5]}"
                )
    return mismatches


def _compare_clipped_cameras(original: RemoBND, built: RemoBND) -> list[str]:
    mismatches = []
    built_cuts = {cut.name: cut for cut in built.cuts}
    for cut in original.cuts:
        if cut.name not in built_cuts:
            mismatches.append(f"cut '{cut.name}' missing from built RemoBND")
            continue
        orig_frames = cut.sibcam.get_clipped_camera_animation()
        new_sibcam = built_cuts[cut.name].sibcam
        new_frames = new_sibcam.get_clipped_camera_animation()
        if len(orig_frames) != len(new_frames):
            mismatches.append(f"cut '{cut.name}': {len(orig_frames)} clipped camera frames -> {len(new_frames)}")
            continue
        if new_sibcam.clip_start_t != 0 or new_sibcam.full_frame_count != len(new_frames):
            mismatches.append(f"cut '{cut.name}': built SIBCAM should be exactly its clip (t=0..n-1)")
        for i, (o, n) in enumerate(zip(orig_frames, new_frames)):
            pos_diff = np.abs(np.array(o.position, dtype=float) - np.array(n.position, dtype=float)).max()
            rot_diff = np.abs(np.array(o.rotation, dtype=float) - np.array(n.rotation, dtype=float)).max()
            if pos_diff > CAMERA_ATOL or rot_diff > CAMERA_ATOL:
                mismatches.append(f"cut '{cut.name}' clipped frame {i}: position diff={pos_diff:.6f}, rotation diff={rot_diff:.6f}")
                break
        fov_diff = np.abs(np.array(get_clip_fov_values(cut.sibcam)) - np.array(get_clip_fov_values(new_sibcam)))
        if fov_diff.size and fov_diff.max() > FOV_ATOL:
            mismatches.append(f"cut '{cut.name}': FoV diff {fov_diff.max():.6f} at clipped frame {int(fov_diff.argmax())}")
    return mismatches


def _compare_taes(original: RemoBND, built: RemoBND) -> list[str]:
    mismatches = []
    orig_tae = original.get_tae()
    built_tae = built.get_tae()
    for orig_anim in orig_tae.animations:
        built_anim = built_tae.get_animation(orig_anim.animation_id)
        if built_anim is None:
            mismatches.append(f"TAE animation {orig_anim.animation_id} missing from built TAE")
            continue
        if repr(built_anim.events) != repr(orig_anim.events) or repr(built_anim.event_groups) != repr(orig_anim.event_groups):
            mismatches.append(f"TAE animation {orig_anim.animation_id} events/groups differ from source")
    return mismatches


def _get_action_channel_samples(action: bpy.types.Action, frames: list[float]) -> dict[str, dict]:
    strip = action.layers[0].strips[0]
    samples = {}
    for slot in action.slots:
        channelbag = strip.channelbag(slot, ensure=False)
        if channelbag is None:
            continue
        key = f"{slot.target_id_type}:{slot.name_display}"
        samples[key] = {(fc.data_path, fc.array_index): [fc.evaluate(f) for f in frames] for fc in channelbag.fcurves}
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
                    if _quat_dev(q_orig, q_reimp) > atol:
                        mismatches.append(f"slot '{slot_key}' '{data_path}' sample {frame_i}: quaternion differs")
                        break
                continue
            if data_path in ("hide_render", "hide_viewport"):
                continue  # not round-tripped (import never writes visibility)
            if (data_path, index) not in reimp_channels:
                mismatches.append(f"slot '{slot_key}' channel ({data_path!r}, {index}) missing from re-imported Action")
                continue
            for frame_i, (o, r) in enumerate(zip(orig_values, reimp_channels[data_path, index])):
                if abs(o - r) > atol:
                    mismatches.append(f"slot '{slot_key}' ({data_path!r}, {index}) sample {frame_i}: orig={o:.6f}, reimport={r:.6f}")
                    break
    return mismatches


def _normalize_camera_keys(samples: dict[str, dict]):
    for key in list(samples):
        if key.startswith("CAMERA:") or key.startswith("OBJECT:") and "Camera" in key:
            samples[key.split(":")[0] + ":<camera>"] = samples.pop(key)


def _summarize(mismatches: list[str], limit=6) -> str:
    summary = "\n  ".join(mismatches[:limit])
    if len(mismatches) > limit:
        summary += f"\n  ... and {len(mismatches) - limit} more"
    return summary


def _find_cutscene_camera(action: bpy.types.Action) -> bpy.types.Object | None:
    for obj in bpy.data.objects:
        if obj.type == "CAMERA" and obj.animation_data and obj.animation_data.action == action:
            return obj
    return None


def _find_reimported_action(cutscene_name: str, exclude: bpy.types.Action) -> bpy.types.Action | None:
    return next((a for a in bpy.data.actions if a != exclude and a.cutscene.cutscene_name == cutscene_name), None)


def _export_new(camera, export_path: Path, source_remobnd_path: str, force_interleaved: bool) -> set[str]:
    export_settings = bpy.context.scene.cutscene_export_settings
    export_settings.export_camera = True
    export_settings.force_interleaved = force_interleaved
    T.activate(camera)
    return bpy.ops.export_scene.hkx_cutscene_new(
        "EXEC_DEFAULT", filepath=str(export_path), source_remobnd_path=source_remobnd_path
    )


# ---------------------------------------------------------------------------
# Case 1: rebuild a vanilla cutscene from scratch
# ---------------------------------------------------------------------------

def run_rebuild_case(case: CutsceneBuildCase):
    remobnd_path = case.source_path
    if not _import_msb(case):
        T.fail(case.name, "MSB import failed")
        return
    result = bpy.ops.import_scene.hkx_cutscene("EXEC_DEFAULT", filepath=str(remobnd_path))
    if "FINISHED" not in result:
        T.fail(case.name, f"Cutscene import returned {result}")
        return

    original = _load_remobnd(remobnd_path)
    cutscene_name = original.cutscene_name
    action = bpy.data.actions.get(cutscene_name)
    camera = _find_cutscene_camera(action) if action else None
    if action is None or camera is None:
        T.fail(case.name, "Cutscene Action/Camera not found after import")
        return
    props = action.cutscene
    total_frames = sum(cut.frame_count for cut in props.cuts)
    step = props.bl_frames_per_game_frame
    check_frames = [float(i * step) for i in np.linspace(0, total_frames - 1, 12).astype(int)]
    original_samples = _get_action_channel_samples(action, check_frames)

    stages = (("interleaved (uncompressed)", True, INTERLEAVED_ATOL), ("compressed", False, COMPRESSED_ATOL))
    with tempfile.TemporaryDirectory() as tmpdir:
        interleaved_path = None
        for stage_label, force_interleaved, atol in stages:
            export_path = Path(tmpdir) / f"{cutscene_name}_{'interleaved' if force_interleaved else 'spline'}.remobnd.dcx"
            try:
                result = _export_new(camera, export_path, str(remobnd_path), force_interleaved)
            except Exception as ex:
                traceback.print_exc()
                T.fail(case.name, f"[{stage_label}] Export raised exception: {ex}")
                return
            if "FINISHED" not in result or not export_path.is_file():
                T.fail(case.name, f"[{stage_label}] Export returned {result}")
                return
            try:
                built = _load_remobnd(export_path)
            except Exception as ex:
                traceback.print_exc()
                T.fail(case.name, f"[{stage_label}] Could not parse built RemoBND: {ex}")
                return

            expected_cuts = [(cut.name, cut.sibcam.clip_frame_count) for cut in original.cuts]
            built_cuts = [(cut.name, cut.sibcam.clip_frame_count) for cut in built.cuts]
            if built_cuts != expected_cuts:
                T.fail(case.name, f"[{stage_label}] built cuts {built_cuts} != vanilla {expected_cuts}")
                return
            for cut in built.cuts:
                hkx_frames = cut.animation.animation_container.frame_count
                if hkx_frames != cut.sibcam.clip_frame_count:
                    T.fail(case.name, f"[{stage_label}] cut '{cut.name}' HKX has {hkx_frames} frames, SIBCAM clip {cut.sibcam.clip_frame_count}")
                    return
            for label, mismatches in (
                ("bone hierarchy", _compare_bone_hierarchies(original, built)),
                ("armature-space part animation", _compare_parts_arma_frames(original, built, atol)),
                ("camera", _compare_clipped_cameras(original, built)),
                ("TAE", _compare_taes(original, built)),
            ):
                if mismatches:
                    T.fail(case.name, f"[{stage_label}] {label} check failed ({len(mismatches)}):\n  {_summarize(mismatches)}")
                    return
            if force_interleaved:
                interleaved_path = export_path

        result = bpy.ops.import_scene.hkx_cutscene(
            "EXEC_DEFAULT", filepath=str(interleaved_path), camera_name="{CutsceneName} Camera (reimport)"
        )
        if "FINISHED" not in result:
            T.fail(case.name, f"[reimport] returned {result}")
            return

    reimported_action = _find_reimported_action(cutscene_name, action)
    if reimported_action is None:
        T.fail(case.name, "[reimport] No second cutscene Action found")
        return
    reimported_samples = _get_action_channel_samples(reimported_action, check_frames)
    _normalize_camera_keys(original_samples)
    _normalize_camera_keys(reimported_samples)
    mismatches = _compare_channel_samples(original_samples, reimported_samples, FCURVE_ATOL)
    if mismatches:
        T.fail(case.name, f"[reimport] Blender channel check failed ({len(mismatches)}):\n  {_summarize(mismatches)}")
        return

    T.ok(
        case.name,
        f"rebuilt {len(original.cuts)} cut(s) / {len(_all_parts(original))} vanilla parts from scratch; bone "
        f"hierarchies, part animation, camera and TAE match (interleaved and compressed); re-import consistent",
    )


# ---------------------------------------------------------------------------
# Case 2: author a new cutscene in Blender
# ---------------------------------------------------------------------------

def _find_msb_part(collection_name: str, game_name: str) -> bpy.types.Object | None:
    collection = bpy.data.collections.get(collection_name)
    if collection is None:
        return None
    for obj in collection.objects:
        if obj.type == "MESH" and obj.name.split(" ")[0].split(".")[0] == game_name:
            return obj
    return None


def run_synthetic_case(case: CutsceneBuildCase):
    if not _import_msb(case):
        T.fail(case.name, "MSB import failed")
        return
    # Import the vanilla cutscene only so that the player part gets an Armature (and c0000 bones exist in Blender).
    result = bpy.ops.import_scene.hkx_cutscene("EXEC_DEFAULT", filepath=str(case.source_path))
    if "FINISHED" not in result:
        T.fail(case.name, f"Cutscene import (for part Armatures) returned {result}")
        return

    new_name = "scn100199"
    result = bpy.ops.cutscene.create_hkx_cutscene(
        "EXEC_DEFAULT", cutscene_name=new_name, first_cut_frames=20, to_60_fps=False
    )
    if "FINISHED" not in result:
        T.fail(case.name, f"create_hkx_cutscene returned {result}")
        return
    action = bpy.data.actions.get(new_name)
    camera = _find_cutscene_camera(action) if action else None
    collection = bpy.data.collections.get(f"Cutscene {new_name}")
    if action is None or camera is None or collection is None:
        T.fail(case.name, "create_hkx_cutscene did not create Action/Camera/collection")
        return
    props = action.cutscene
    T.activate(camera)
    result = bpy.ops.cutscene.add_cut("EXEC_DEFAULT", frame_count=10)
    if "FINISHED" not in result or [(c.name, c.frame_count) for c in props.cuts] != [("cut0010", 20), ("cut0020", 10)]:
        T.fail(case.name, f"add_cut failed: {[(c.name, c.frame_count) for c in props.cuts]}")
        return

    player_mesh = _find_msb_part("m10_01_00_00 Player Start Parts", "c0000_0000")
    object_mesh = _find_msb_part("m10_01_00_00 Object Parts", "o1303")
    map_piece_mesh = _find_msb_part("m10_01_00_00 Map Piece Parts", "m2510B1")
    if player_mesh is None or object_mesh is None or map_piece_mesh is None:
        T.fail(case.name, "Could not find c0000_0000 / o1303 / m2510B1 MSB Parts")
        return
    player_armature = player_mesh.parent
    if player_armature is None or player_armature.type != "ARMATURE":
        T.fail(case.name, "Player part has no Armature after vanilla cutscene import")
        return

    # Link parts (Armature + Mesh for the player) and a Dummy into the new cutscene collection; bind the animated ones.
    for obj in (player_armature, player_mesh, object_mesh, map_piece_mesh):
        collection.objects.link(obj)
    dummy = bpy.data.objects.new("d0000_0010", None)
    collection.objects.link(dummy)
    T.activate(camera)  # deselects everything else first
    for obj in (player_armature, object_mesh, dummy):
        obj.select_set(True)
    result = bpy.ops.cutscene.bind_objects("EXEC_DEFAULT")
    if "FINISHED" not in result:
        T.fail(case.name, f"bind_objects returned {result}")
        return
    for obj in (player_armature, object_mesh, dummy):
        if not (obj.animation_data and obj.animation_data.action == action):
            T.fail(case.name, f"'{obj.name}' not bound to the new cutscene Action")
            return

    # Keyframe (30 game frames = Blender frames 0..29 with 1 frame per game frame).
    last_frame = 29
    player_armature.location = (10.0, -134.0, 76.0)
    player_armature.keyframe_insert("location", frame=0)
    player_armature.location = (12.0, -130.0, 76.5)
    player_armature.keyframe_insert("location", frame=last_frame)
    pelvis = player_armature.pose.bones.get("Pelvis")
    if pelvis is None:
        T.fail(case.name, "Player Armature has no 'Pelvis' bone")
        return
    pelvis.rotation_mode = "QUATERNION"
    pelvis.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
    pelvis.keyframe_insert("rotation_quaternion", frame=0)
    pelvis.rotation_quaternion = (math.cos(0.3), 0.0, 0.0, math.sin(0.3))
    pelvis.keyframe_insert("rotation_quaternion", frame=last_frame)
    dummy.location = (1.0, 2.0, 3.0)
    dummy.keyframe_insert("location", frame=0)
    dummy.location = (1.0, 2.0, 6.0)
    dummy.keyframe_insert("location", frame=last_frame)
    # Object: static transform, but hidden from the second cut (frame 20) onwards.
    object_mesh.hide_render = False
    object_mesh.keyframe_insert("hide_render", frame=0)
    object_mesh.hide_render = True
    object_mesh.keyframe_insert("hide_render", frame=20)
    camera.location = (5.0, -6.0, 7.0)
    camera.rotation_euler = (1.2, 0.0, 0.5)
    camera.keyframe_insert("location", frame=0)
    camera.keyframe_insert("rotation_euler", frame=0)
    camera.location = (6.0, -8.0, 7.5)
    camera.rotation_euler = (1.0, 0.1, 0.9)
    camera.keyframe_insert("location", frame=last_frame)
    camera.keyframe_insert("rotation_euler", frame=last_frame)
    camera.data.lens = 35.0
    camera.data.keyframe_insert("lens", frame=0)
    camera.data.lens = 50.0
    camera.data.keyframe_insert("lens", frame=last_frame)
    # Linear keys everywhere, so re-imported per-frame LINEAR keys reproduce the authored curves exactly.
    strip = action.layers[0].strips[0]
    for slot in action.slots:
        channelbag = strip.channelbag(slot, ensure=False)
        if channelbag is None:
            continue
        for fcurve in channelbag.fcurves:
            for kp in fcurve.keyframe_points:
                kp.interpolation = "LINEAR"

    check_frames = [0.0, 7.0, 15.0, 19.0, 20.0, 25.0, 29.0]
    authored_samples = _get_action_channel_samples(action, check_frames)

    with tempfile.TemporaryDirectory() as tmpdir:
        export_path = Path(tmpdir) / f"{new_name}.remobnd.dcx"
        try:
            result = _export_new(camera, export_path, "", force_interleaved=True)
        except Exception as ex:
            traceback.print_exc()
            T.fail(case.name, f"Export raised exception: {ex}")
            return
        if "FINISHED" not in result or not export_path.is_file():
            T.fail(case.name, f"Export returned {result}")
            return
        try:
            built = _load_remobnd(export_path)
        except Exception as ex:
            traceback.print_exc()
            T.fail(case.name, f"Could not parse built RemoBND: {ex}")
            return

        built_cuts = [(cut.name, cut.sibcam.clip_frame_count) for cut in built.cuts]
        if built_cuts != [("cut0010", 20), ("cut0020", 10)]:
            T.fail(case.name, f"built cuts {built_cuts}")
            return
        parts = _all_parts(built)
        expected = {"c0000_0000": RemoPartType.Player, "o1303": RemoPartType.Object, "m2510B1": RemoPartType.MapPiece, "d0000_0010": RemoPartType.Dummy}
        got = {name: t for name, (t, _) in parts.items()}
        if got != expected:
            T.fail(case.name, f"built parts {got} != {expected}")
            return
        o1303 = parts["o1303"][1]
        if set(o1303.cut_arma_frames) != {"cut0010"}:
            T.fail(case.name, f"o1303 (render-hidden from frame 20) should only be in cut0010, got {sorted(o1303.cut_arma_frames)}")
            return
        player = parts["c0000_0000"][1]
        if set(player.cut_arma_frames) != {"cut0010", "cut0020"} or "Pelvis" not in player.cut_arma_frames["cut0010"][0].bone_transforms:
            T.fail(case.name, "player part missing cuts or Pelvis bone track")
            return
        if len(player.cut_arma_frames["cut0010"][0].bone_transforms) < 50:
            T.fail(case.name, f"player has only {len(player.cut_arma_frames['cut0010'][0].bone_transforms)} bones (expected c0000 ANIBND skeleton)")
            return
        if [a.animation_id for a in built.get_tae().animations] != [10, 20]:
            T.fail(case.name, f"TAE animations {[a.animation_id for a in built.get_tae().animations]}")
            return
        rm0 = player.cut_arma_frames["cut0010"][0].root_motion
        if not np.allclose(rm0.translation, (10.0, 76.0, -134.0), atol=1e-4):  # game (x, z, y) of Blender (x, y, z)
            T.fail(case.name, f"player root motion frame 0 {rm0.translation} != game (10, 76, -134)")
            return

        bpy.context.scene.cutscene_import_settings.to_60_fps = False  # authored with 1 Blender frame per game frame
        result = bpy.ops.import_scene.hkx_cutscene(
            "EXEC_DEFAULT", filepath=str(export_path), camera_name="{CutsceneName} Camera (reimport)"
        )
        if "FINISHED" not in result:
            T.fail(case.name, f"[reimport] returned {result}")
            return

    reimported_action = _find_reimported_action(new_name, action)
    if reimported_action is None:
        T.fail(case.name, "[reimport] No second cutscene Action found")
        return
    reimported_samples = _get_action_channel_samples(reimported_action, check_frames)
    # Only the animated objects' channels are compared (o1303 is static; the Dummy is re-created under a new name).
    authored = {k: v for k, v in authored_samples.items() if "Camera" in k or player_armature.name in k or k.startswith("CAMERA")}
    _normalize_camera_keys(authored)
    _normalize_camera_keys(reimported_samples)
    mismatches = _compare_channel_samples(authored, reimported_samples, FCURVE_ATOL)
    dummy_key = next((k for k in reimported_samples if "d0000_0010" in k), None)
    if dummy_key is None:
        mismatches.append("re-imported Dummy 'd0000_0010' not found")
    else:
        z = reimported_samples[dummy_key][("location", 2)]
        if abs(z[0] - 3.0) > FCURVE_ATOL or abs(z[-1] - 6.0) > FCURVE_ATOL:
            mismatches.append(f"Dummy Z location {z[0]:.4f}..{z[-1]:.4f} != 3..6")
    if mismatches:
        T.fail(case.name, f"[reimport] channel check failed ({len(mismatches)}):\n  {_summarize(mismatches)}")
        return

    T.ok(case.name, "authored cutscene built without a source RemoBND, parsed and re-imported consistently")


def run_case(case: CutsceneBuildCase):
    if case.synthetic:
        run_synthetic_case(case)
    else:
        run_rebuild_case(case)


def main():
    import argparse
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--filter-test-names", type=str, default="")
    args = parser.parse_args(argv)
    T.run_case_list(CASES, run_case, suite_name="HKX cutscene build from scratch", filter_test_names=args.filter_test_names)


main()
