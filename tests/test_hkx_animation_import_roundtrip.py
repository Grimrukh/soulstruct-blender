"""Headless HKX animation import/export round-trip tests.

Approach
--------
Each test case defines a character FLVER (or CHRBND) *and* an ANIBND that
contains both the skeleton HKX and one or more animation HKX entries.

Because the animation-import operator normally opens a file-browser dialog
(``wm.hkx_animation_binder_choice``), headless tests drive it by:

  1. Manually loading the ANIBND via ``soulstruct.containers``.
  2. Setting the ``ImportHKXAnimationWithBinderChoice`` class-level attributes
     (``BINDER``, ``ARMATURE_OBJ``, ``SKELETON_HKX``, ``MODEL_NAME``,
     ``HKX_COMPENDIUM``) that ``invoke()`` would normally set.
  3. Writing a single stub file named ``({entry_id}) {entry_name}`` to a temp
     directory so that ``execute()`` can resolve the chosen binder entry.
  4. Calling ``bpy.ops.wm.hkx_animation_binder_choice("EXEC_DEFAULT", …)``
     with that directory and file.

Round-trip methodology per case
---------------------------------
1. Import FLVER for the character (skip if path not found).
2. Import one animation from the ANIBND (headless).
3. Verify a Blender Action was created on the armature.
4. Export the animation to a temp ``.hkx`` via ``export_scene.hkx_animation``,
   passing the ANIBND path as ``hkx_skeleton_path`` (the operator extracts the
   skeleton from within the binder).
5. Verify the exported file is non-empty.
6. Re-import the exported HKX and compare F-curve samples with the original.
7. Clean up.

Two-stage round-trip check
--------------------------
Step 4-6 are run TWICE, in this order:

1. ``force_interleaved=True`` — exports raw uncompressed interleaved frames, i.e.
   *no* wavelet/spline compression at all.  This isolates the add-on's own
   Blender <-> HKX conversion math (armature-space <-> bone-basis matrices, the
   FromSoft/Blender coordinate change of basis, and the armature <-> local
   hierarchy conversions).  Compared with a tight tolerance, since the only
   expected loss is float32 storage in ``hkQsTransform``.
2. Default compressed export (spline for most games, wavelet for Demon's Souls).
   Compared with a looser tolerance that accommodates genuine compression loss.

If stage 1 fails, the discrepancy is a *bug in the add-on* (or in the
armature/local conversions in ``soulstruct-havok``).  If stage 1 passes and only
stage 2 fails, the discrepancy is genuine lossy compression.  The failure message
is prefixed with the stage label so the two are never confused.

FILE PATHS
----------
Fill in all four path fields per case for the games you have installed.
Leave any as empty strings to auto-skip.

Run with:
    blender --background --python tests/test_hkx_animation_import_roundtrip.py
"""
import re
import sys
import shutil
import tempfile
import traceback
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import bpy
import bl_test_utils as T

T.enable_addon()

# ---------------------------------------------------------------------------
# Game path constants
# ---------------------------------------------------------------------------

from soulstruct.config import Config

# ---------------------------------------------------------------------------
# Test case descriptor
# ---------------------------------------------------------------------------

@dataclass
class HKXAnimationImportCase(T.ImportCaseBase):
    """One HKX animation import/export round-trip test.

    ``directory`` / ``filename`` → ANIBND (primary source).
    ``flver_dir`` / ``flver_filename`` → CHRBND or FLVER for the character.
    ``anim_entry_name`` → specific animation to import (empty = first found).
    """

    flver_dir: Path | str = ""
    flver_filename: str = ""
    anim_entry_name: str = ""
    # c0000 skeleton is in base ANIBND, but animations are in split ANIBNDS.
    skeleton_anibnd_filename: str = ""

    def check_skip_reason(self) -> str | None:
        """Check FLVER source first, then fall back to base check for ANIBND."""
        if not self.flver_dir:
            return "FLVER directory not configured (placeholder)"
        if not Path(self.flver_dir).is_dir():
            return f"FLVER directory not found: {self.flver_dir}"
        flver_path = Path(self.flver_dir) / self.flver_filename
        if not self.flver_filename or not flver_path.exists():
            return f"FLVER source not found: {flver_path}"
        return super().check_skip_reason()  # checks ANIBND directory/filename


# ---------------------------------------------------------------------------
# Test case definitions
# ---------------------------------------------------------------------------

HKX_ANIMATION_TEST_CASES: list[HKXAnimationImportCase] = [

    # ------------------------------------------------------------------
    # Demon's Souls
    # ------------------------------------------------------------------
    HKXAnimationImportCase(
        name="DeS / chr / c2010 (Boletaria Soldier)",
        game_enum="DEMONS_SOULS",
        flver_dir=Config.DES_PATH / "chr",
        flver_filename="c2010.chrbnd",
        directory=Config.DES_PATH / "chr",
        filename="c2010.anibnd",
        anim_entry_name="", # empty = use first available animation
        tags=["animation", "character"],
    ),
    HKXAnimationImportCase(
        name="DeS / chr / c0000 (Player)",
        game_enum="DEMONS_SOULS",
        flver_dir=Config.DES_PATH / "chr",
        flver_filename="c0000.chrbnd",
        directory=Config.DES_PATH / "chr",
        filename="c0000_a6x.anibnd",  # random subset of player animations (6000-6999)
        skeleton_anibnd_filename="c0000.anibnd",
        anim_entry_name="",
        tags=["animation", "character", "player"],
    ),

    # ------------------------------------------------------------------
    # Dark Souls PTDE
    # ------------------------------------------------------------------
    HKXAnimationImportCase(
        name="PTDE / chr / c1200 (Large Rat)",
        game_enum="DARK_SOULS_PTDE",
        flver_dir=Config.PTDE_PATH / "chr",
        flver_filename="c1200.chrbnd",
        directory=Config.PTDE_PATH / "chr",
        filename="c1200.anibnd",
        anim_entry_name="", # empty = use first available animation
        tags=["animation", "character"],
    ),
    HKXAnimationImportCase(
        name="PTDE / chr / c0000 (Player)",
        game_enum="DARK_SOULS_PTDE",
        flver_dir=Config.PTDE_PATH / "chr",
        flver_filename="c0000.chrbnd",
        directory=Config.PTDE_PATH / "chr",
        filename="c0000_a6x.anibnd",  # random subset of player animations (6000-6999)
        skeleton_anibnd_filename="c0000.anibnd",
        anim_entry_name="",
        tags=["animation", "character", "player"],
    ),

    # ------------------------------------------------------------------
    # Dark Souls Remastered
    # ------------------------------------------------------------------
    HKXAnimationImportCase(
        name="DSR / chr / c1200 (Large Rat)",
        game_enum="DARK_SOULS_DSR",
        flver_dir=Config.DSR_PATH / "chr",
        flver_filename="c1200.chrbnd.dcx",
        directory=Config.DSR_PATH / "chr",
        filename="c1200.anibnd.dcx",
        anim_entry_name="",
        tags=["animation", "character"],
    ),
    HKXAnimationImportCase(
        name="DSR / chr / c0000 (Player)",
        game_enum="DARK_SOULS_DSR",
        flver_dir=Config.DSR_PATH / "chr",
        flver_filename="c0000.chrbnd.dcx",
        directory=Config.DSR_PATH / "chr",
        filename="c0000_a6x.anibnd.dcx",  # random subset of player animations (6000-6999)
        skeleton_anibnd_filename="c0000.anibnd.dcx",
        anim_entry_name="",
        tags=["animation", "character", "player"],
    ),

    # ------------------------------------------------------------------
    # Bloodborne
    # ------------------------------------------------------------------
    # HKXAnimationImportCase(
    #     name="BB / chr / c1060 (Brainsucker)",
    #     game_enum="BLOODBORNE",
    #     flver_dir=Config.BB_PATH / "chr",
    #     flver_filename="c1060.chrbnd.dcx",
    #     directory=Config.BB_PATH / "chr",
    #     filename="c1060.anibnd.dcx",
    #     tags=["animation", "character"],
    # ),

    # ------------------------------------------------------------------
    # Elden Ring
    # ------------------------------------------------------------------
    # HKXAnimationImportCase(
    #     name="ER / chr / c4382 (Tunnel Miner)",
    #     game_enum="ELDEN_RING",
    #     flver_dir=Config.ER_PATH / "chr",
    #     flver_filename="c4382.chrbnd.dcx",
    #     directory=Config.ER_PATH / "chr",
    #     filename="c4382.anibnd.dcx",
    #     tags=["animation", "character"],
    # ),
]

# ---------------------------------------------------------------------------
# Round-trip constants
# ---------------------------------------------------------------------------

SKELETON_ENTRY_RE = re.compile(r"skeleton\.hkx(\.dcx)?", re.IGNORECASE)

# Tolerance for the uncompressed (interleaved) export stage. The only expected loss here is
# float32 storage of `hkQsTransform` members and matrix decompose/recompose round-tripping, both
# of which are far below this. Anything larger indicates a genuine add-on bug rather than
# compression loss.
INTERLEAVED_ATOL = 1e-4

# Tolerance for the compressed export stage, which accommodates the lossy spline compression used
# by most games (and wavelet compression in Demon's Souls). DSR adds an extra 2015-2010 conversion
# on top. Differences of up to ~0.005 in location/scale and ~0.005 in quaternion dot deviation are
# considered acceptable compression artifacts.
COMPRESSED_ATOL = 5e-3


# ---------------------------------------------------------------------------
# ActionChannelbag (FCurves container) retrieval helper for Action
# ---------------------------------------------------------------------------

def _get_action_channelbag(action: bpy.types.Action) -> bpy.types.ActionChannelbag | None:
    try:
        strip = action.layers[0].strips[0]
        action_slot = action.slots[0]
        return strip.channelbag(action_slot, ensure=False)
    except (AttributeError, IndexError):
        return None


# ---------------------------------------------------------------------------
# Round-trip data helpers
# ---------------------------------------------------------------------------

class _LogStub:
    """Minimal logging stub for calling SoulstructAnimation methods outside an operator."""
    @staticmethod
    def info(_msg): pass
    @staticmethod
    def warning(msg): print(f"[WARN] {msg}")
    @staticmethod
    def error(msg): print(f"[ERROR] {msg}"); return {"CANCELLED"}
    @staticmethod
    def debug(_msg): pass


def _sample_fcurves(
    channelbag: bpy.types.ActionChannelbag,
    frames: list[int],
) -> dict[tuple[str, int], list[float]]:
    """Evaluate all F-curves in *channelbag* at each integer frame.

    Returns ``{(data_path, array_index): [value_at_frame_0, ...]}``.
    """
    return {
        (fc.data_path, fc.array_index): [fc.evaluate(float(f)) for f in frames]
        for fc in channelbag.fcurves
    }


def _compare_fcurve_samples(
    original: dict[tuple[str, int], list[float]],
    reimported: dict[tuple[str, int], list[float]],
    atol: float = 1e-3,
) -> list[str]:
    """Return a list of mismatch descriptions (empty list means all within tolerance).

    ``rotation_quaternion`` F-curves are compared using quaternion equivalence so that
    sign-flipped quaternions (q and -q represent the same rotation) are not reported as
    mismatches.
    """
    mismatches = []
    checked_quat_paths: set[str] = set()

    for (data_path, array_index), orig_vals in original.items():

        # --- Quaternion-aware comparison (sign-insensitive) ---
        if "rotation_quaternion" in data_path:
            if data_path in checked_quat_paths:
                continue
            checked_quat_paths.add(data_path)

            all_present = all(
                (data_path, i) in original and (data_path, i) in reimported
                for i in range(4)
            )
            if all_present:
                for frame_idx in range(len(orig_vals)):
                    orig_q = [original[(data_path, i)][frame_idx] for i in range(4)]
                    reim_q = [reimported[(data_path, i)][frame_idx] for i in range(4)]
                    dot = sum(o * r for o, r in zip(orig_q, reim_q))
                    # q and -q are the same rotation: |dot| should be ≈ 1.
                    if abs(abs(dot) - 1.0) > atol:
                        mismatches.append(
                            f"{data_path!r} rotation frame {frame_idx}: "
                            f"quaternion dot={dot:.6f} (|dot|-1={abs(abs(dot) - 1.0):.6f})"
                        )
                continue
            # Fall through to component-wise comparison if not all 4 components present.

        # --- Standard component-wise comparison ---
        if (data_path, array_index) not in reimported:
            mismatches.append(f"F-curve ({data_path!r}, {array_index}) missing from re-imported action")
            continue
        for frame_idx, (o, r) in enumerate(zip(orig_vals, reimported[(data_path, array_index)])):
            if abs(o - r) > atol:
                mismatches.append(
                    f"({data_path!r}, {array_index}) frame {frame_idx}: "
                    f"orig={o:.6f}, reimport={r:.6f}, diff={abs(o - r):.6f}"
                )
    return mismatches


# ---------------------------------------------------------------------------
# Headless animation import helper
# ---------------------------------------------------------------------------

def _import_animation_headless(
    case: HKXAnimationImportCase,
    armature_obj: bpy.types.Object,
    anibnd_path: Path,
) -> bool:
    """Load the ANIBND, set operator class vars, and call wm.hkx_animation_binder_choice
    in EXEC_DEFAULT mode.  Returns True on success, False on failure (error already logged).
    """
    # --- Load ANIBND ---
    try:
        from soulstruct.eldenring.containers import DivBinder
        try:
            anibnd = DivBinder.from_path(anibnd_path)
        except Exception:
            from soulstruct.containers import Binder
            anibnd = Binder.from_path(anibnd_path)
    except Exception as ex:
        T.fail(case.name, f"Could not load ANIBND '{anibnd_path.name}': {ex}")
        return False

    # --- Read skeleton HKX ---
    settings = bpy.context.scene.soulstruct_settings
    skeleton_hkx_class = settings.game_config.skeleton_hkx_class
    if skeleton_hkx_class is None:
        T.fail(case.name, f"No skeleton HKX class for game {settings.game.name}")
        return False

    # For c0000 (and any case with a separate skeleton ANIBND), load the skeleton
    # from that dedicated binder rather than the animation sub-ANIBND, mirroring
    # the special handling in ExportCharacterHKXAnimation.
    skeleton_binder = anibnd
    if case.skeleton_anibnd_filename:
        skeleton_anibnd_path = Path(case.directory) / case.skeleton_anibnd_filename
        if not skeleton_anibnd_path.exists():
            T.fail(case.name, f"Skeleton ANIBND not found: {skeleton_anibnd_path}")
            return False
        try:
            from soulstruct.containers import Binder
            skeleton_binder = Binder.from_path(skeleton_anibnd_path)
        except Exception as ex:
            T.fail(case.name, f"Could not load skeleton ANIBND '{skeleton_anibnd_path.name}': {ex}")
            return False

    skeleton_entry = skeleton_binder.find_entry_by_name_regex(SKELETON_ENTRY_RE)
    if skeleton_entry is None:
        T.fail(case.name, f"No skeleton.hkx found in ANIBND {skeleton_binder.path_name}")
        return False

    # Optionally load compendium (needed by some games).
    compendium = None
    try:
        from soulstruct.havok.core import HKX
        comp_entry = anibnd.find_entry_by_name_regex(r".*\.compendium")
        if comp_entry:
            compendium = HKX.from_binder_entry(comp_entry)
    except Exception:
        pass  # compendium not required

    try:
        if compendium is not None:
            try:
                skeleton_hkx = skeleton_hkx_class.from_binder_entry(skeleton_entry, compendium=compendium)
            except TypeError:
                skeleton_hkx = skeleton_hkx_class.from_binder_entry(skeleton_entry)
        else:
            skeleton_hkx = skeleton_hkx_class.from_binder_entry(skeleton_entry)
    except Exception as ex:
        T.fail(case.name, f"Could not load skeleton HKX: {ex}")
        return False

    # --- Find animation entry ---
    anim_entries = anibnd.find_entries_by_name_regex(r"a.*\.hkx(\.dcx)?")
    if not anim_entries:
        T.fail(case.name, "No animation entries (a*.hkx) found in ANIBND")
        return False

    if case.anim_entry_name:
        entry = next((e for e in anim_entries if e.name == case.anim_entry_name), None)
        if entry is None:
            T.fail(case.name, f"Animation '{case.anim_entry_name}' not found in ANIBND")
            return False
    else:
        entry = anim_entries[0]

    # --- Set operator class variables ---
    # The operator class is registered under 'WM_OT_hkx_animation_binder_choice'.
    try:
        ChoiceOp = bpy.types.WM_OT_hkx_animation_binder_choice
    except AttributeError:
        T.fail(case.name, "wm.hkx_animation_binder_choice operator not registered in this session")
        return False

    model_name = armature_obj.name.split(".")[0].split(" ")[0]
    ChoiceOp.BINDER = anibnd
    ChoiceOp.binder = anibnd       # instance-attribute fallback when EXEC_DEFAULT skips invoke()
    ChoiceOp.ARMATURE_OBJ = armature_obj
    ChoiceOp.PART_MESH_OBJ = None
    ChoiceOp.MODEL_NAME = model_name
    ChoiceOp.SKELETON_HKX = skeleton_hkx
    ChoiceOp.HKX_COMPENDIUM = compendium

    # --- Create stub file in temp directory ---
    tmpdir = tempfile.mkdtemp(suffix="_anim_choice")
    stub_name = f"({entry.entry_id}) {entry.name}"
    stub_path = Path(tmpdir) / stub_name
    stub_path.write_text(entry.name)

    try:
        result = bpy.ops.wm.hkx_animation_binder_choice(
            "EXEC_DEFAULT",
            directory=tmpdir + "/",
            temp_directory=tmpdir + "/",
            files=[{"name": stub_name}],
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        # Clean up class-level binder reference so it doesn't leak between tests.
        ChoiceOp.BINDER = None
        ChoiceOp.binder = None  # type: ignore[assignment]

    if "FINISHED" not in result:
        T.fail(case.name, f"wm.hkx_animation_binder_choice returned {result}")
        return False

    return True


# ---------------------------------------------------------------------------
# Headless export + re-import helper
# ---------------------------------------------------------------------------

def _export_and_reimport(
    armature_obj: bpy.types.Object,
    anim_stem: str,
    skeleton_source_path: Path,
    check_frames: list[int],
    force_interleaved: bool,
) -> tuple[dict[tuple[str, int], list[float]] | None, str]:
    """Export the Action currently assigned to `armature_obj`, then re-import the exported HKX.

    Returns `(fcurve_samples, "")` on success, or `(None, error_message)` on failure. Note that a
    successful call leaves the *re-imported* Action assigned to `armature_obj`; the caller is
    responsible for restoring the original Action before any subsequent export.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        export_path = str(Path(tmpdir) / f"{anim_stem}.hkx")
        T.activate(armature_obj)
        try:
            export_result = bpy.ops.export_scene.hkx_animation(
                "EXEC_DEFAULT",
                filepath=export_path,
                hkx_skeleton_path=str(skeleton_source_path),
                dcx_type="Null",
                force_interleaved=force_interleaved,
            )
        except Exception as ex:
            traceback.print_exc()
            return None, f"Animation export raised exception: {ex}"
        if "FINISHED" not in export_result:
            return None, f"Animation export returned {export_result}"

        # ---- Verify exported file ----
        hkx_files = list(Path(tmpdir).glob("*.hkx"))
        if not hkx_files:
            return None, "No .hkx file found after animation export"
        hkx_file = hkx_files[0]
        if hkx_file.stat().st_size == 0:
            return None, f"Exported HKX file is empty: {hkx_file.name}"

        if not check_frames:
            return {}, ""

        # ---- Re-import exported HKX ----
        settings = bpy.context.scene.soulstruct_settings
        anim_hkx_cls = settings.game_config.animation_hkx_class
        skel_hkx_cls = settings.game_config.skeleton_hkx_class
        try:
            skel_p = Path(skeleton_source_path)
            if skel_p.name.endswith(".hkx") or skel_p.name.endswith(".hkx.dcx"):
                reimport_skeleton_hkx = skel_hkx_cls.from_path(skel_p)
            else:
                from soulstruct.containers import Binder as _RtBinder
                skel_binder = _RtBinder.from_path(skel_p)
                skel_entry = skel_binder.find_entry_by_name_regex(SKELETON_ENTRY_RE)
                reimport_skeleton_hkx = skel_hkx_cls.from_binder_entry(skel_entry)
            reimport_animation_hkx = anim_hkx_cls.from_path(hkx_file)
        except Exception as ex:
            traceback.print_exc()
            return None, f"Could not load exported HKX for round-trip check: {ex}"

        from bl_ext.user_default.io_soulstruct.soulstruct.blender.animation.types import (
            SoulstructAnimation as _SoulstructAnimation,
        )
        model_name = armature_obj.name.split(".")[0].split(" ")[0]
        suffix = "_reimport_interleaved" if force_interleaved else "_reimport_compressed"
        try:
            reimport_bl_anim = _SoulstructAnimation.new_from_hkx_animation(
                _LogStub(),
                bpy.context,
                reimport_animation_hkx,
                skeleton_hkx=reimport_skeleton_hkx,
                name=anim_stem + suffix,
                armature_obj=armature_obj,
                model_name=model_name,
            )
        except Exception as ex:
            traceback.print_exc()
            return None, f"Re-import of exported HKX for round-trip check failed: {ex}"

        return _sample_fcurves(reimport_bl_anim.channelbag, check_frames), ""


# ---------------------------------------------------------------------------
# Per-case test runner
# ---------------------------------------------------------------------------

def run_case(case: HKXAnimationImportCase):
    """Import FLVER → import animation → export animation → verify."""

    anibnd_path = case.source_path

    # ---- 1. Import FLVER ----
    T.clear_scene()
    T.set_game(case.game_enum)
    bpy.context.scene.flver_import_settings.import_textures = False

    try:
        flver_result = bpy.ops.import_scene.flver(
            "EXEC_DEFAULT",
            directory=str(case.flver_dir),
            files=[{"name": case.flver_filename}],
        )
    except Exception as ex:
        T.fail(case.name, f"FLVER import raised exception: {ex}")
        return
    if "FINISHED" not in flver_result:
        T.fail(case.name, f"FLVER import returned {flver_result}")
        return

    # Find the armature object for the character.
    armature_objs = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    if not armature_objs:
        T.fail(case.name, "No Armature found after FLVER import")
        return
    armature_obj = armature_objs[0]
    T.activate(armature_obj)

    # ---- 2. Import animation (headless) ----
    if not _import_animation_headless(case, armature_obj, anibnd_path):
        return  # error already logged

    # ---- 3. Verify Action was created ----
    if armature_obj.animation_data is None or armature_obj.animation_data.action is None:
        T.fail(case.name, "No Action found on armature after animation import")
        return

    action = armature_obj.animation_data.action
    if not (channelbag := _get_action_channelbag(action)):
        T.fail(case.name, f"Imported action '{action.name}' has no Channelbag (no F-Curves)")
        return
    if len(channelbag.fcurves) == 0:
        T.fail(case.name, f"Imported action '{action.name}' has no F-Curves")
        return

    # Sample the first (up to) 5 *actual keyframe positions* for the round-trip check.
    # We intentionally avoid interpolated frames (e.g. odd frames when the animation was
    # imported with `to_60_fps`, where Blender linear interpolation differs from the HKX
    # spline interpolation in the re-imported action, causing false failures).
    keyframe_positions = sorted({
        int(pt.co[0])
        for fc in channelbag.fcurves
        for pt in fc.keyframe_points
    })
    check_frames = keyframe_positions[:5]
    original_samples = _sample_fcurves(channelbag, check_frames)

    # ---- 4. Export + re-import animation, twice ----
    anim_stem = action.name.split("|")[-1].split(" ")[0].split(".")[0] or "a000_000000"

    # For c0000, the skeleton lives in the base ANIBND, not the animation sub-ANIBND.
    # ExportAnyHKXAnimation already handles binder paths in `hkx_skeleton_path`, so we
    # just point it at the right file.
    skeleton_source_path = (
        Path(case.directory) / case.skeleton_anibnd_filename
        if case.skeleton_anibnd_filename
        else anibnd_path
    )

    # `new_from_hkx_animation()` assigns the re-imported Action to the Armature, so we must restore
    # the original Action before each export stage.
    original_action = action
    original_action_slot = armature_obj.animation_data.action_slot

    # Stage 1 (interleaved) is lossless, so any failure there is an add-on bug rather than
    # compression loss. Stage 2 is the real game format.
    stages = (
        ("interleaved (uncompressed)", True, INTERLEAVED_ATOL),
        ("compressed", False, COMPRESSED_ATOL),
    )

    for stage_label, force_interleaved, atol in stages:

        # Restore original Action (no-op on the first stage).
        armature_obj.animation_data.action = original_action
        armature_obj.animation_data.action_slot = original_action_slot

        reimported_samples, error = _export_and_reimport(
            armature_obj,
            anim_stem,
            skeleton_source_path,
            check_frames,
            force_interleaved,
        )
        if error:
            T.fail(case.name, f"[{stage_label}] {error}")
            return
        if not check_frames:
            continue

        mismatches = _compare_fcurve_samples(original_samples, reimported_samples, atol=atol)
        if mismatches:
            summary = "\n  ".join(mismatches[:5])
            if len(mismatches) > 5:
                summary += f"\n  ... and {len(mismatches) - 5} more"
            T.fail(
                case.name,
                f"[{stage_label}] Round-trip frame check failed ({len(mismatches)} mismatch(es), "
                f"atol={atol}) over frames {check_frames}:\n  {summary}",
            )
            return

    # Leave the original Action assigned for any downstream inspection.
    armature_obj.animation_data.action = original_action
    armature_obj.animation_data.action_slot = original_action_slot

    T.ok(
        case.name,
        f"animation round-trip OK — action '{action.name}', "
        f"{len(channelbag.fcurves)} F-Curve(s), "
        f"first {len(check_frames)} frame(s) consistent (interleaved and compressed)",
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    T.run_case_list(HKX_ANIMATION_TEST_CASES, run_case, suite_name="HKX animation import/export")


main()

