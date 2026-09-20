"""Headless check that an imported HKX animation deforms the mesh exactly as the game does.

Why a separate suite from ``test_hkx_animation_import_roundtrip.py``
-------------------------------------------------------------------
The round-trip suite proves that Blender -> HKX -> Blender is self-consistent. It cannot catch a
bug that is applied symmetrically on import and export, and it cannot run at all for games whose
animation export is unimplemented (Demon's Souls). This suite instead compares the imported pose
against an INDEPENDENT ground truth derived straight from the source files.

The invariant
-------------
What a skinned vertex actually sees is the bone's deform matrix. In Blender that is

    pose_bone.matrix @ Bone.matrix_local^-1

and in the game it is

    A_g @ M_g^-1

where ``A_g`` is the HKX animation's armature-space transform for that bone and ``M_g`` is the
FLVER bind (armature-space rest) transform INCLUDING the bone's local FLVER scale. Both are
expressed in Blender coordinates here. If those two matrices agree, the character is posed
correctly, whatever the add-on does internally.

This catches three bugs that are invisible to a round-trip test:

  * FLVER rest bone scale applied twice. ``EditBone`` cannot store scale, so the Blender rest pose
    drops it while the animation's armature-space scale still contains it. DeS c5010 (Tower Knight)
    has ``L_Shoulderpad``/``R_Shoulderpad`` scale 3.1285, and its pauldrons were 3.13x too big;
    c5020 (Penetrator) is the same bug at 1.26x.
  * Un-animated parent bones treated as identity rather than as their rest pose. Since every
    EditBone rest matrix bakes in the X-forward bone CoB -- exactly a 180 degree rotation about the
    Y+Z diagonal -- this flipped whole bone chains upside down. DeS c2075 (Prisoner Hoard) hits it
    through its extra un-animated FLVER root ``Ctl_master``.
  * Duplicate FLVER bone names binding a track to the wrong bone. DeS c6041 (Plague Baby) has two
    bones named ``c6041``, so animations drove an origin stub instead of the real skeleton root.

Run with:
    blender --background --python tests/test_hkx_animation_pose_fidelity.py
"""
import re
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import bpy
from mathutils import Matrix
import bl_test_utils as T

T.enable_addon()

from soulstruct.config import Config
from soulstruct.containers import Binder
from soulstruct.flver import FLVER
from soulstruct.flver.bone_tools import BoneTree

ADDON = T.ADDON_MODULE
_flver_utils = __import__(f"{ADDON}.soulstruct.blender.flver.utilities", fromlist=["x"])
_anim_utils = __import__(f"{ADDON}.soulstruct.blender.animation.utilities", fromlist=["x"])
game_bone_transform_to_bl_bone_matrix = _flver_utils.game_bone_transform_to_bl_bone_matrix
game_trs_to_bl_bone_trs = _flver_utils.game_trs_to_bl_bone_trs
get_armature_frames = _anim_utils.get_armature_frames

SKELETON_ENTRY_RE = re.compile(r"skeleton\.hkx(\.dcx)?", re.IGNORECASE)
# Demon's Souls ANIBNDs are inconsistent about `.hkx` vs `.HKX` (e.g. c1000 uses uppercase).
ANIMATION_ENTRY_RE = re.compile(r"a.*\.hkx(\.dcx)?", re.IGNORECASE)

# Tolerance on any single matrix element. The two sides are computed by completely different
# routes (Blender FK vs. Havok composition) in float32-sourced data, so ~1e-5 is typical; the bugs
# above produce errors of 0.5 to 12.
MAX_DEFORM_DIFF = 1e-3


@dataclass
class PoseFidelityCase(T.ImportCaseBase):
    """``directory``/``filename`` -> ANIBND. ``flver_dir``/``flver_filename`` -> CHRBND or FLVER."""

    flver_dir: Path | str = ""
    flver_filename: str = ""
    anim_entry_name: str = ""
    # Bones we specifically expect this case to exercise (documentation + a guard that the
    # character really does still have them).
    key_bones: list[str] = field(default_factory=list)

    def check_skip_reason(self) -> str | None:
        if not self.flver_dir:
            return "FLVER directory not configured (placeholder)"
        if not Path(self.flver_dir).is_dir():
            return f"FLVER directory not found: {self.flver_dir}"
        flver_path = Path(self.flver_dir) / self.flver_filename
        if not self.flver_filename or not flver_path.exists():
            return f"FLVER source not found: {flver_path}"
        return super().check_skip_reason()


POSE_FIDELITY_TEST_CASES: list[PoseFidelityCase] = [

    # ------------------------------------------------------------------
    # Demon's Souls -- the characters from the original bug report.
    # ------------------------------------------------------------------
    PoseFidelityCase(
        name="DeS / chr / c5010 (Tower Knight) -- scaled pauldron bones",
        game_enum="DEMONS_SOULS",
        flver_dir=Config.DES_PATH / "chr/c5010",
        flver_filename="c5010.chrbnd",
        directory=Config.DES_PATH / "chr/c5010",
        filename="c5010.anibnd",
        anim_entry_name="a00_2200.hkx",
        key_bones=["L_Shoulderpad", "R_Shoulderpad"],  # FLVER bone scale 3.1285
        tags=["animation", "character", "bone-scale"],
    ),
    PoseFidelityCase(
        name="DeS / chr / c5020 (Penetrator) -- scaled pauldron bones",
        game_enum="DEMONS_SOULS",
        flver_dir=Config.DES_PATH / "chr/c5020",
        flver_filename="c5020.chrbnd",
        directory=Config.DES_PATH / "chr/c5020",
        filename="c5020.anibnd",
        anim_entry_name="a00_2200.hkx",
        key_bones=["L_Shoulderpad", "R_Shoulderpad"],  # FLVER bone scale ~1.27
        tags=["animation", "character", "bone-scale"],
    ),
    PoseFidelityCase(
        name="DeS / chr / c2075 (Prisoner Hoard) -- un-animated FLVER root",
        game_enum="DEMONS_SOULS",
        flver_dir=Config.DES_PATH / "chr/c2075",
        flver_filename="c2075.chrbnd",
        directory=Config.DES_PATH / "chr/c2075",
        filename="c2075.anibnd",
        anim_entry_name="a00_2200.hkx",
        key_bones=["Ctl_master", "master"],  # `master`'s Blender parent is never animated
        tags=["animation", "character", "unanimated-parent"],
    ),
    PoseFidelityCase(
        name="DeS / chr / c6041 (Plague Baby) -- duplicate FLVER bone name",
        game_enum="DEMONS_SOULS",
        flver_dir=Config.DES_PATH / "chr/c6041",
        flver_filename="c6041.chrbnd",
        directory=Config.DES_PATH / "chr/c6041",
        filename="c6041.anibnd",
        anim_entry_name="a00_2200.hkx",
        key_bones=["c6041", "c6041 <DUPE>"],  # two FLVER bones share the name `c6041`
        tags=["animation", "character", "duplicate-bone-name"],
    ),
    PoseFidelityCase(
        name="DeS / chr / c1000 (Serpent Soldier) -- uppercase .HKX entries",
        game_enum="DEMONS_SOULS",
        flver_dir=Config.DES_PATH / "chr/c1000",
        flver_filename="c1000.chrbnd",
        directory=Config.DES_PATH / "chr/c1000",
        filename="c1000.anibnd",
        anim_entry_name="a00_2200.HKX",
        tags=["animation", "character", "entry-name-case"],
    ),
    PoseFidelityCase(
        name="DeS / chr / c2140 (Owl Warrior) -- hk550 annotation track pointers",
        game_enum="DEMONS_SOULS",
        flver_dir=Config.DES_PATH / "chr/c2140",
        flver_filename="c2140.chrbnd",
        directory=Config.DES_PATH / "chr/c2140",
        filename="c2140.anibnd",
        anim_entry_name="a00_2200.hkx",
        tags=["animation", "character", "hk550-types"],
    ),
    PoseFidelityCase(
        name="DeS / chr / c5090 (Leechmonger) -- 299 heavily scaled tentacle bones",
        game_enum="DEMONS_SOULS",
        flver_dir=Config.DES_PATH / "chr/c5090",
        flver_filename="c5090.chrbnd",
        directory=Config.DES_PATH / "chr/c5090",
        filename="c5090.anibnd",
        anim_entry_name="a00_2200.hkx",
        tags=["animation", "character", "non-uniform-scale"],
    ),

    # ------------------------------------------------------------------
    # Dark Souls Remastered -- guards against regressions in later games.
    # ------------------------------------------------------------------
    PoseFidelityCase(
        name="DSR / chr / c3420 (Undead Dragon) -- non-uniform animated spine scale",
        game_enum="DARK_SOULS_DSR",
        flver_dir=Config.DSR_PATH / "chr",
        flver_filename="c3420.chrbnd.dcx",
        directory=Config.DSR_PATH / "chr",
        filename="c3420.anibnd.dcx",
        anim_entry_name="a02_3001.hkx",
        tags=["animation", "character", "non-uniform-scale"],
    ),
    PoseFidelityCase(
        name="DSR / chr / c1200 (Large Rat)",
        game_enum="DARK_SOULS_DSR",
        flver_dir=Config.DSR_PATH / "chr",
        flver_filename="c1200.chrbnd.dcx",
        directory=Config.DSR_PATH / "chr",
        filename="c1200.anibnd.dcx",
        anim_entry_name="",
        tags=["animation", "character"],
    ),
]


def _flver_bind_matrices(flver: FLVER) -> dict[str, Matrix]:
    """Blender-space bind matrix per bone name, INCLUDING the FLVER local bone scale.

    This is the matrix the GAME inverts out when skinning. It deliberately differs from
    ``Bone.matrix_local``, which cannot hold scale. Duplicate names get the same ' <DUPE>'
    suffix that FLVER import applies.
    """
    arma_transforms = BoneTree(flver).get_bone_armature_space_transforms()
    bind = {}
    seen = set()
    for game_bone, (translate, rotmat, scale) in zip(flver.bones, arma_transforms, strict=True):
        name = f"{game_bone.name} <DUPE>" if game_bone.name in seen else game_bone.name
        seen.add(game_bone.name)
        bind[name] = game_bone_transform_to_bl_bone_matrix(translate, rotmat, scale)
    return bind


def _read_flver(case: PoseFidelityCase) -> FLVER | None:
    """Read the case's FLVER with plain `soulstruct` (independent of how the add-on read it)."""
    path = Path(case.flver_dir) / case.flver_filename
    if path.suffix in {".flver"}:
        return FLVER.from_path(path)
    binder = Binder.from_path(path)
    entries = binder.find_entries_by_name_regex(r".*\.flver$")
    return FLVER.from_binder_entry(entries[0]) if entries else None


def _import_animation(case: PoseFidelityCase, armature_obj, anibnd_path: Path):
    """Import one animation headlessly. Returns the source `AnimationHKX`/`SkeletonHKX` pair."""
    from soulstruct.eldenring.containers import DivBinder

    try:
        anibnd = DivBinder.from_path(anibnd_path)
    except Exception:
        anibnd = Binder.from_path(anibnd_path)

    settings = bpy.context.scene.soulstruct_settings
    skeleton_entry = anibnd.find_entry_by_name_regex(SKELETON_ENTRY_RE)
    if skeleton_entry is None:
        T.fail(case.name, f"No skeleton.hkx in ANIBND {anibnd_path.name}")
        return None
    skeleton_hkx = settings.game_config.skeleton_hkx_class.from_binder_entry(skeleton_entry)

    anim_entries = anibnd.find_entries_by_name_regex(ANIMATION_ENTRY_RE)
    if not anim_entries:
        T.fail(case.name, f"No animation entries matched in ANIBND {anibnd_path.name}")
        return None
    if case.anim_entry_name:
        entry = next((e for e in anim_entries if e.name == case.anim_entry_name), None)
        if entry is None:
            T.fail(case.name, f"Animation '{case.anim_entry_name}' not found in ANIBND")
            return None
    else:
        entry = anim_entries[0]

    animation_hkx = settings.game_config.animation_hkx_class.from_binder_entry(entry)

    choice_op = __import__(
        f"{ADDON}.soulstruct.blender.animation.import_operators", fromlist=["x"]
    ).ImportHKXAnimationWithBinderChoice
    SoulstructAnimation = __import__(
        f"{ADDON}.soulstruct.blender.animation.types", fromlist=["x"]
    ).SoulstructAnimation
    BlenderFLVER = __import__(
        f"{ADDON}.soulstruct.blender.flver.models.types", fromlist=["x"]
    ).BlenderFLVER

    # Drive the importer directly; the operator itself only exists to pick the entry.
    class _Op:
        """Minimal `LoggingOperator` stand-in (this path only logs)."""
        messages: list[str] = []

        def info(self, msg): pass
        def debug(self, msg): pass
        def warning(self, msg): _Op.messages.append(msg)
        def error(self, msg): _Op.messages.append(msg)

    _Op.messages = []
    bl_flver = BlenderFLVER.from_armature_or_mesh(armature_obj)
    SoulstructAnimation.new_from_hkx_animation(
        _Op(), bpy.context, animation_hkx, skeleton_hkx, entry.name, armature_obj,
        case.flver_filename.split(".")[0], bone_data_type=bl_flver.bone_data_type,
    )
    del choice_op  # only imported to assert the operator still exists
    return animation_hkx, skeleton_hkx, _Op.messages


def run_case(case: PoseFidelityCase):
    T.clear_scene()
    T.set_game(case.game_enum)
    bpy.context.scene.flver_import_settings.import_textures = False

    # ---- 1. Import FLVER through the real operator ----
    try:
        result = bpy.ops.import_scene.flver(
            "EXEC_DEFAULT",
            directory=str(case.flver_dir),
            files=[{"name": case.flver_filename}],
        )
    except Exception as ex:
        traceback.print_exc()
        T.fail(case.name, f"FLVER import raised exception: {ex}")
        return
    if "FINISHED" not in result:
        T.fail(case.name, f"FLVER import returned {result}")
        return

    armature_objs = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    if not armature_objs:
        T.fail(case.name, "No Armature found after FLVER import")
        return
    armature_obj = armature_objs[0]
    T.activate(armature_obj)

    bone_names = {bone.name for bone in armature_obj.data.bones}
    for key_bone in case.key_bones:
        if key_bone not in bone_names:
            T.fail(case.name, f"Expected bone '{key_bone}' is missing from the imported Armature")
            return

    # ---- 2. Import the animation ----
    anibnd_path = case.source_path
    imported = _import_animation(case, armature_obj, anibnd_path)
    if imported is None:
        return  # already logged
    animation_hkx, skeleton_hkx, messages = imported

    if armature_obj.animation_data is None or armature_obj.animation_data.action is None:
        T.fail(case.name, "No Action on Armature after animation import")
        return

    # ---- 3. Build the independent ground truth ----
    flver = _read_flver(case)
    if flver is None:
        T.fail(case.name, f"Could not read FLVER from {case.flver_filename}")
        return
    bind = _flver_bind_matrices(flver)

    interleaved = (
        animation_hkx if animation_hkx.animation_container.is_interleaved
        else animation_hkx.to_interleaved_hkx()
    )
    arma_frames = get_armature_frames(interleaved, skeleton_hkx)

    # Recover any duplicate-bone-name remapping the importer reported, so we compare the same bone.
    renames = {}
    for msg in messages:
        match = re.search(r"Binding this animation's '(.+?)' track to '(.+?)'", msg)
        if match:
            renames[match.group(1)] = match.group(2)

    # ---- 4. Compare deform matrices on a spread of frames ----
    frame_count = len(arma_frames)
    frame_indices = sorted({0, frame_count // 3, 2 * frame_count // 3, frame_count - 1})
    step = 2 if bpy.context.scene.animation_import_settings.to_60_fps else 1

    worst = 0.0
    worst_label = ""
    checked = 0
    for frame_index in frame_indices:
        bpy.context.scene.frame_set(int(frame_index * step))
        bpy.context.view_layer.update()
        for hkx_bone_name, transform in arma_frames[frame_index].items():
            bl_bone_name = renames.get(hkx_bone_name, hkx_bone_name)
            if bl_bone_name not in armature_obj.pose.bones or bl_bone_name not in bind:
                continue  # HKX bone absent from the FLVER (common, and warned about on import)
            pose_bone = armature_obj.pose.bones[bl_bone_name]
            bl_deform = pose_bone.matrix @ armature_obj.data.bones[bl_bone_name].matrix_local.inverted()
            translate, rotate, scale = game_trs_to_bl_bone_trs(transform)
            game_deform = Matrix.LocRotScale(translate, rotate, scale) @ bind[bl_bone_name].inverted()
            diff = max(
                abs(bl_deform[row][col] - game_deform[row][col])
                for row in range(4) for col in range(4)
            )
            checked += 1
            if diff > worst:
                worst, worst_label = diff, f"'{bl_bone_name}' on frame {frame_index}"

    if checked == 0:
        T.fail(case.name, "No animated bones matched the FLVER Armature; nothing was compared")
        return
    if worst > MAX_DEFORM_DIFF:
        T.fail(
            case.name,
            f"Imported pose does not match the game's deformation: worst element error {worst:.4g} "
            f"at {worst_label} (tolerance {MAX_DEFORM_DIFF:g}), over {checked} bone-frames",
        )
        return

    T.ok(
        case.name,
        f"pose matches game deformation — worst element error {worst:.3g} over {checked} "
        f"bone-frames across {len(frame_indices)} frame(s)",
    )


def main():
    import argparse
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--filter-test-names", type=str, default="")
    args = parser.parse_args(argv)
    T.run_case_list(
        POSE_FIDELITY_TEST_CASES,
        run_case,
        suite_name="HKX animation pose fidelity",
        filter_test_names=args.filter_test_names,
    )


main()
