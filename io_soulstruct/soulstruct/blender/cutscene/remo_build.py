"""Build a complete DSR RemoBND from scratch out of a Blender cutscene collection.

Unlike `remo_export.py` (which patches an existing RemoBND), nothing is needed beyond the game files:

    - The parts of the cutscene are the MSB Part objects (Meshes, or their Armature parents) and Dummy Empties linked
      into the cutscene's collection (`Cutscene {cutscene_name}`, as created by import or `CreateHKXCutscene`). Parts
      may belong to other maps than the cutscene's own; their cutscene names get the vanilla 'AXXBXX_' prefix and the
      game is expected to have that map loaded when the cutscene plays.
    - Each cut's amalgamated cutscene skeleton is built from the parts: a root bone per part plus, for Characters,
      the Player and Objects, the bones of the model's ANIBND skeleton (found in `chr/{model}.anibnd` or
      `obj/{model}.objbnd`) minus its top-level 'Master'/model bone, exactly as vanilla cutscenes are laid out
      (`RemoPartTracks`). Map Pieces, Collisions and Dummies are root-only.
    - Tracks are sampled from the cutscene Action per cut: root motion from each part's transform object (identity for
      Map Pieces and Collisions, which the game places itself), bone tracks from the part's Armature if it is bound to
      the Action, else the model's reference pose. A part is left out of a cut if its object is render-hidden (via a
      `hide_render`/`hide_viewport` F-curve in the Action) at the cut's first frame.
    - Each cut's SIBCAM is baked from the Camera bound to the Action, and a minimal TAE (one event-less animation per
      cut) is generated -- optionally copying the TAE events of matching cuts from a source RemoBND.
"""
from __future__ import annotations

__all__ = [
    "RemoPartSkeleton",
    "CutscenePart",
    "arma_frame_to_local",
    "collect_cutscene_parts",
    "build_cut_part_tracks",
    "build_cutscene_tae",
    "build_remobnd_from_scratch",
]

import copy
import re
import typing as tp
from dataclasses import dataclass, field

import bpy

from soulstruct.base.animations.tae import RemoTAE
from soulstruct.containers import Binder, EntryNotFoundError
from soulstruct.havok.fromsoft.base.skeleton import Skeleton
from soulstruct.havok.fromsoft.darksouls1r import RemoAnimationHKX
from soulstruct.havok.fromsoft.darksouls1r.remobnd import RemoBND, RemoPartTracks, RemoPartType
from soulstruct.havok.utilities.maths import TRSTransform

from ..animation.utilities import get_armature_bone_data_type, read_skeleton_hkx_entry
from ..base.operators import LoggingOperator
from ..exceptions import CutsceneExportError, SoulstructTypeError
from ..flver.models.types import BlenderFLVER, FLVERBoneDataType
from ..msb.operator_config import BLENDER_MSB_PART_CLASSES
from ..msb.properties import BlenderMSBPartSubtype
from ..msb.types.base.parts import BaseBlenderMSBPart
from ..types import ArmatureObject, CameraObject
from ..utilities.misc import get_collection_map_stem, get_model_name
from .remo_export import build_cut_animation_hkx, build_new_sibcam, make_track_rotations_continuous
from .types import SoulstructCutsceneAnimation

SKELETON_ENTRY_RE = re.compile(r"skeleton\.hkx(\.dcx)?", flags=re.IGNORECASE)
DUMMY_NAME_RE = re.compile(r"^(?:scn\d{6} )?(d\d{4}_\d{4})(?:\.\d+)?$")  # optional cutscene prefix / Blender dupe suffix

# MSB Part subtypes that can appear in cutscenes, and their `RemoPartType` (the Player is a Player Start part).
_PART_SUBTYPE_TO_REMO_TYPE = {
    BlenderMSBPartSubtype.PlayerStart: RemoPartType.Player,
    BlenderMSBPartSubtype.Character: RemoPartType.Character,
    BlenderMSBPartSubtype.Object: RemoPartType.Object,
    BlenderMSBPartSubtype.MapPiece: RemoPartType.MapPiece,
    BlenderMSBPartSubtype.Collision: RemoPartType.Collision,
}


@dataclass(slots=True)
class RemoPartSkeleton:
    """The cutscene bones of one model: its ANIBND skeleton minus its top-level bone (see `RemoPartTracks`)."""

    bone_names: list[str]  # un-prefixed, depth-first
    parent_indices: list[int]  # into `bone_names`; -1 for cutscene root bones
    # Armature-space reference poses of every ANIBND bone (including the dropped top-level bone's contribution), used
    # to pose parts whose Armature is not animated by the cutscene.
    arma_reference_poses: dict[str, TRSTransform] = field(default_factory=dict)

    @property
    def root_bone_names(self) -> list[str]:
        return [name for name, parent_index in zip(self.bone_names, self.parent_indices) if parent_index == -1]

    @classmethod
    def from_skeleton(cls, skeleton: Skeleton) -> RemoPartSkeleton:
        """Drop the skeleton's single top-level bone ('Master' for characters, the model name for objects); its
        children become the cutscene root bones. Skeletons with several top-level bones keep them all as roots."""
        top_level_bones = skeleton.get_root_bones()
        if len(top_level_bones) == 1:
            top_level_bones = list(top_level_bones[0].children)
        bone_names = []
        parent_indices = []

        def _walk(bone, parent_index: int):
            bone_names.append(bone.name)
            parent_indices.append(parent_index)
            bone_index = len(bone_names) - 1
            for child in bone.children:
                _walk(child, bone_index)

        for top_bone in top_level_bones:
            _walk(top_bone, -1)
        return cls(bone_names, parent_indices, skeleton.get_arma_space_reference_poses())

    @classmethod
    def from_blender_armature(cls, armature: ArmatureObject) -> RemoPartSkeleton:
        """Same rule as `from_skeleton()`, applied to a Blender Armature's bone hierarchy (i.e. the FLVER skeleton).
        Used for models without an ANIBND skeleton, e.g. objects whose OBJBND has no ANIBND: vanilla cutscenes still
        animate their FLVER bones. Reference poses are left empty (the Armature itself is sampled at rest instead)."""
        top_level_bones = [bone for bone in armature.data.bones if bone.parent is None]
        if len(top_level_bones) == 1:
            top_level_bones = list(top_level_bones[0].children)
        bone_names = []
        parent_indices = []

        def _walk(bone, parent_index: int):
            bone_names.append(bone.name)
            parent_indices.append(parent_index)
            bone_index = len(bone_names) - 1
            for child in bone.children:
                _walk(child, bone_index)

        for top_bone in top_level_bones:
            _walk(top_bone, -1)
        return cls(bone_names, parent_indices)


@dataclass(slots=True)
class CutscenePart:
    """One MSB Part (or Dummy) of the cutscene collection, resolved for export."""

    remo_name: str  # cutscene root bone name, e.g. 'c5350_0001', 'd0000_0010', 'A10B02_m2350B2A10'
    map_part_name: str  # MSB Part name without any other-map prefix
    part_type: RemoPartType
    transform_obj: bpy.types.Object  # Armature parent if any, else Mesh; the Empty for Dummies
    armature: ArmatureObject | None = None
    skeleton: RemoPartSkeleton | None = None
    bone_data_type: FLVERBoneDataType = FLVERBoneDataType.OMITTED
    # Armature sampled at rest when `armature` is not bound to the cutscene: the part's own, else its model's.
    rest_armature: ArmatureObject | None = None
    # Objects whose `hide_render`/`hide_viewport` F-curves hide the part from a cut (the Mesh and its Armature).
    visibility_objs: list[bpy.types.Object] = field(default_factory=list)

    @property
    def bone_prefix(self) -> str:
        return self.map_part_name + "_"


def arma_frame_to_local(skeleton: RemoPartSkeleton, arma_frame: dict[str, TRSTransform]) -> list[TRSTransform]:
    """Convert armature-space bone transforms to the LOCAL space of the cutscene skeleton (`RemoPartTracks` order).

    Same rule as `remo_export.write_part_frames()`: cutscene root bones are stored as-is (relative to identity, since
    the part root's world transform is applied separately by the game); other bones are relative to their parent.
    """
    local = []
    for bone_name, parent_index in zip(skeleton.bone_names, skeleton.parent_indices):
        try:
            arma = arma_frame[bone_name]
        except KeyError:
            raise CutsceneExportError(f"No sampled transform for cutscene bone '{bone_name}'.")
        if parent_index == -1:
            local.append(arma.copy())
        else:
            local.append(arma_frame[skeleton.bone_names[parent_index]].left_divide(arma))
    return local


# region Part collection

def _get_cutscene_area_block(cutscene_name: str) -> tuple[int, int]:
    return int(cutscene_name[3:5]), int(cutscene_name[5:7])


def _get_map_stem_area_block(map_stem: str) -> tuple[int, int]:
    return int(map_stem[1:3]), int(map_stem[4:6])


def _load_model_skeleton(
    operator: LoggingOperator,
    context: bpy.types.Context,
    part_type: RemoPartType,
    model_name: str,
    cache: dict[str, RemoPartSkeleton | None],
) -> RemoPartSkeleton | None:
    """Load `model_name`'s ANIBND skeleton (character ANIBND, or the ANIBND nested in an OBJBND) from the project/game
    directory. Returns `None` (with a warning) if the model has no skeleton; the part is then root-only."""
    if model_name in cache:
        return cache[model_name]
    settings = context.scene.soulstruct_settings
    skeleton = None
    try:
        if part_type in (RemoPartType.Player, RemoPartType.Character):
            anibnd = Binder.from_path(settings.get_import_file_path("chr", f"{model_name}.anibnd"))
        elif part_type == RemoPartType.Object:
            objbnd = Binder.from_path(settings.get_import_file_path("obj", f"{model_name}.objbnd"))
            anibnd = Binder.from_binder_entry(objbnd[f"{model_name}.anibnd"])
        else:
            cache[model_name] = None
            return None
        skeleton_hkx = read_skeleton_hkx_entry(anibnd[SKELETON_ENTRY_RE])
        skeleton = RemoPartSkeleton.from_skeleton(skeleton_hkx.skeleton)
    except FileNotFoundError:
        operator.warning(
            f"No ANIBND/OBJBND found for model '{model_name}' in the project or game directory. Its cutscene part(s) "
            f"will use their Blender Armature's (FLVER) bones if they have one, else no bones."
        )
    except EntryNotFoundError:
        operator.info(
            f"Model '{model_name}' has no ANIBND skeleton. Its cutscene part(s) will use their Blender Armature's "
            f"(FLVER) bones if they have one, else no bones."
        )
    except Exception as ex:
        raise CutsceneExportError(f"Could not load ANIBND skeleton of model '{model_name}': {ex}")
    cache[model_name] = skeleton
    return skeleton


def collect_cutscene_parts(
    operator: LoggingOperator,
    context: bpy.types.Context,
    cutscene: SoulstructCutsceneAnimation,
    collection: bpy.types.Collection,
) -> list[CutscenePart]:
    """Resolve every MSB Part and Dummy Empty in `collection` (recursively) into a `CutscenePart`, sorted by cutscene
    name (vanilla files mostly use alphabetical root bone order). The Camera and anything else is ignored."""
    settings = context.scene.soulstruct_settings
    cutscene_name = cutscene.props.cutscene_name
    main_area_block = _get_cutscene_area_block(cutscene_name)
    part_classes = BLENDER_MSB_PART_CLASSES[settings.game_type]
    skeleton_cache = {}  # type: dict[str, RemoPartSkeleton | None]
    parts = {}  # type: dict[str, CutscenePart]

    def _add(part: CutscenePart):
        if part.remo_name in parts:
            raise CutsceneExportError(
                f"Cutscene collection '{collection.name}' contains two parts named '{part.remo_name}' "
                f"('{parts[part.remo_name].transform_obj.name}' and '{part.transform_obj.name}')."
            )
        parts[part.remo_name] = part

    seen_meshes = set()
    for obj in collection.all_objects:
        if obj.type == "CAMERA":
            continue
        if obj.type == "EMPTY":
            match = DUMMY_NAME_RE.match(obj.name)
            if not match:
                operator.debug(f"Ignoring Empty '{obj.name}' in cutscene collection (not a 'dXXXX_XXXX' Dummy name).")
                continue
            dummy_name = match.group(1)
            _add(
                CutscenePart(
                    remo_name=dummy_name, map_part_name=dummy_name, part_type=RemoPartType.Dummy, transform_obj=obj,
                    visibility_objs=[obj],
                )
            )
            continue

        try:
            armature, mesh = BaseBlenderMSBPart.parse_msb_part_obj(obj)
        except SoulstructTypeError:
            operator.debug(f"Ignoring non-MSB Part object '{obj.name}' in cutscene collection.")
            continue
        if mesh.name in seen_meshes:
            continue  # Armature and Mesh both linked
        seen_meshes.add(mesh.name)

        try:
            subtype = mesh.MSB_PART.entry_subtype_enum
        except ValueError:
            operator.warning(f"MSB Part object '{mesh.name}' has no Part subtype set. Ignoring.")
            continue
        remo_type = _PART_SUBTYPE_TO_REMO_TYPE.get(subtype)
        if remo_type is None:
            operator.warning(f"MSB Part '{mesh.name}' has subtype {subtype.name}, which cutscenes do not support. Ignoring.")
            continue
        bl_part = part_classes[subtype](mesh)
        map_part_name = bl_part.game_name
        if remo_type == RemoPartType.Player and not map_part_name.startswith(RemoPartType.Player):
            raise CutsceneExportError(
                f"Player Start part '{map_part_name}' must be named '{RemoPartType.Player}' to appear in a cutscene."
            )
        if remo_type != RemoPartType.Player and not map_part_name.startswith(remo_type):
            raise CutsceneExportError(
                f"{subtype.get_nice_name()} part '{map_part_name}' must have a name starting with '{remo_type}'."
            )

        try:
            map_stem = get_collection_map_stem(mesh)
        except ValueError as ex:
            raise CutsceneExportError(
                f"Cannot determine the map of MSB Part '{mesh.name}' (it must be in a '{{map_stem}} ... Parts' "
                f"collection): {ex}"
            )
        area_block = _get_map_stem_area_block(map_stem)
        if area_block != main_area_block:
            remo_name = f"A{area_block[0]:02d}B{area_block[1]:02d}_{map_part_name}"
        else:
            remo_name = map_part_name

        skeleton = None
        bone_data_type = FLVERBoneDataType.OMITTED
        rest_armature = None
        if remo_type in (RemoPartType.Player, RemoPartType.Character, RemoPartType.Object):
            model_name = get_model_name(bl_part.model.name) if bl_part.model else map_part_name[:5]
            skeleton = _load_model_skeleton(operator, context, remo_type, model_name, skeleton_cache)
            rest_armature = armature
            if rest_armature is None and bl_part.model is not None:
                try:
                    rest_armature = BlenderFLVER.from_armature_or_mesh(bl_part.model).armature
                except SoulstructTypeError:
                    rest_armature = None
            if rest_armature is not None:
                bone_data_type = get_armature_bone_data_type(rest_armature)
                if skeleton is None:
                    # No ANIBND skeleton (e.g. OBJBND without ANIBND): vanilla cutscenes use the FLVER bones.
                    skeleton = RemoPartSkeleton.from_blender_armature(rest_armature)
                    operator.info(
                        f"Part '{remo_name}': cutscene bones taken from Armature '{rest_armature.name}' (FLVER "
                        f"skeleton), as model '{model_name}' has no ANIBND skeleton."
                    )
        _add(
            CutscenePart(
                remo_name=remo_name,
                map_part_name=map_part_name,
                part_type=remo_type,
                transform_obj=armature or mesh,
                armature=armature,
                skeleton=skeleton,
                bone_data_type=bone_data_type,
                rest_armature=rest_armature,
                visibility_objs=[mesh] + ([armature] if armature is not None else []),
            )
        )

    return [parts[name] for name in sorted(parts)]

# endregion


# region Per-cut tracks

def build_cut_part_tracks(
    cutscene: SoulstructCutsceneAnimation,
    part: CutscenePart,
    bl_frames: tp.Sequence[float],
) -> RemoPartTracks:
    """Sample `part` over `bl_frames` (one cut) into `RemoPartTracks`. See module docstring for the rules."""
    frame_count = len(bl_frames)
    if part.part_type in (RemoPartType.MapPiece, RemoPartType.Collision):
        root_frames = [TRSTransform.identity() for _ in range(frame_count)]
    else:
        root_frames = cutscene.sample_root_motion(part.transform_obj, bl_frames)

    skeleton = part.skeleton
    if skeleton is None or not skeleton.bone_names:
        return RemoPartTracks(name=part.remo_name, root_frames=root_frames)

    if part.armature is not None and cutscene.is_bound(part.armature):
        sample_armature = part.armature
    else:
        sample_armature = part.rest_armature  # not animated by the cutscene: sampled at rest (may be `None`)
    if sample_armature is not None:
        missing = [name for name in skeleton.bone_names if name not in sample_armature.data.bones]
        if missing:
            raise CutsceneExportError(
                f"Cutscene skeleton bone(s) {sorted(missing)} of part '{part.remo_name}' are missing from Armature "
                f"'{sample_armature.name}'."
            )
        arma_frames = cutscene.sample_armature_bones(
            sample_armature, skeleton.bone_names, bl_frames, part.bone_data_type,
            root_bone_names=set(skeleton.root_bone_names),
        )
    elif skeleton.arma_reference_poses:
        # No Armature in Blender at all: hold the ANIBND reference pose.
        arma_frames = [skeleton.arma_reference_poses] * frame_count
    else:
        raise CutsceneExportError(f"Part '{part.remo_name}' has cutscene bones but no Armature or reference pose.")

    return RemoPartTracks(
        name=part.remo_name,
        root_frames=root_frames,
        bone_prefix=part.bone_prefix,
        bone_names=list(skeleton.bone_names),
        bone_parent_indices=list(skeleton.parent_indices),
        bone_frames=[arma_frame_to_local(skeleton, arma_frame) for arma_frame in arma_frames],
    )

# endregion


def build_cutscene_tae(cut_numbers: tp.Sequence[int], source_remobnd: RemoBND | None = None) -> RemoTAE:
    """Minimal TAE with one event-less animation per cut. If `source_remobnd` is given, the events of its TAE
    animations with matching cut numbers are copied, as are any of its non-cut animations (the vanilla 'final'
    animation 99999 that resets cutscene settings)."""
    tae = RemoTAE.new(cut_numbers)
    if source_remobnd is None:
        return tae
    source_tae = source_remobnd.get_tae()
    for animation in tae.animations:
        source_animation = source_tae.get_animation(animation.animation_id)
        if source_animation is not None:
            animation.events = copy.deepcopy(source_animation.events)
            animation.event_groups = copy.deepcopy(source_animation.event_groups)
    source_cut_numbers = {source_remobnd.get_cut_number(cut.name) for cut in source_remobnd.cuts}
    for source_animation in source_tae.animations:
        if source_animation.animation_id not in source_cut_numbers and tae.get_animation(source_animation.animation_id) is None:
            tae.animations.append(copy.deepcopy(source_animation))
    tae.animations.sort(key=lambda a: a.animation_id)
    return tae


def build_remobnd_from_scratch(
    operator: LoggingOperator,
    context: bpy.types.Context,
    cutscene: SoulstructCutsceneAnimation,
    collection: bpy.types.Collection,
    camera: CameraObject,
    spline: bool,
    source_remobnd: RemoBND | None = None,
) -> RemoBND:
    """Build a complete RemoBND for `cutscene` from the parts in `collection` and the Camera bound to the Action.

    Raises `CutsceneExportError` on any problem. Spline compression (`spline=True`) shells out to `CompressAnim.exe`.
    """
    props = cutscene.props
    if not props.cuts:
        raise CutsceneExportError(f"Cutscene '{props.cutscene_name}' has no cuts.")
    cut_numbers = []
    for cut in props.cuts:
        cut_number = RemoBND.get_cut_number(cut.name)
        if cut_numbers and cut_number <= cut_numbers[-1]:
            raise CutsceneExportError(
                f"Cutscene cuts must have ascending numbers: '{cut.name}' follows cut{cut_numbers[-1]:04d}."
            )
        if cut.frame_count < 2:
            raise CutsceneExportError(f"Cut '{cut.name}' must have at least 2 frames.")
        cut_numbers.append(cut_number)
    if not cutscene.is_bound(camera):
        raise CutsceneExportError(f"Camera '{camera.name}' is not bound to cutscene Action '{cutscene.name}'.")

    parts = collect_cutscene_parts(operator, context, cutscene, collection)
    if not parts:
        raise CutsceneExportError(f"No MSB Parts or Dummies found in cutscene collection '{collection.name}'.")
    operator.info(f"Cutscene parts: {[part.remo_name for part in parts]}")

    remobnd = RemoBND.new(props.cutscene_name, tae=build_cutscene_tae(cut_numbers, source_remobnd))
    for cut in props.cuts:
        bl_frames = cutscene.get_cut_bl_frames(cut.name)
        cut_parts = [
            part for part in parts
            if not any(cutscene.is_object_hidden_at(obj, bl_frames[0]) for obj in part.visibility_objs)
        ]
        if not cut_parts:
            raise CutsceneExportError(f"Every part is hidden in cut '{cut.name}'; a cut needs at least one part.")
        hidden = sorted({part.remo_name for part in parts} - {part.remo_name for part in cut_parts})
        if hidden:
            operator.info(f"Cut '{cut.name}': parts hidden at cut start are left out: {hidden}")

        part_tracks = [build_cut_part_tracks(cutscene, part, bl_frames) for part in cut_parts]
        animation = RemoAnimationHKX.from_remo_part_tracks(part_tracks)
        container = animation.animation_container
        container.load_interleaved_data()
        local_frames = [[transform.copy() for transform in frame] for frame in container.interleaved_data]
        make_track_rotations_continuous(local_frames)
        remo_cut = remobnd.add_cut(cut.name, animation, build_new_sibcam(cutscene.sample_camera(camera, bl_frames)),
                                   add_tae_animation=False)
        try:
            build_cut_animation_hkx(remo_cut, local_frames, spline=spline)
        except Exception as ex:
            raise CutsceneExportError(
                f"Failed to build animation HKX for cut '{cut.name}'. Spline compression requires `CompressAnim.exe` "
                f"(Windows only). Error: {ex}"
            )
        # `add_cut()` packed the uncompressed animation; repack the (possibly compressed) one.
        remobnd.find_entry_by_path(f"\\{cut.name}\\hkxx64\\a{RemoBND.get_cut_number(cut.name):04d}.hkx").set_from_binary_file(
            remo_cut.animation
        )
        operator.info(
            f"Built cut '{cut.name}': {cut.frame_count} frames, {len(cut_parts)} parts, "
            f"{len(remo_cut.animation.skeleton.bones)} bones."
        )
    return remobnd
