"""VERY early/experimental system for importing/exporting DSR animations into Blender."""
from __future__ import annotations

__all__ = [
    "ImportHKXAnimation",
    "ImportHKXAnimationWithBinderChoice",
    "ImportCharacterHKXAnimation",
]

import re
import time
import traceback
import typing as tp
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector, Quaternion as BlenderQuaternion

from soulstruct.containers import Binder, BinderEntry
from soulstruct.dcx import DCXType
from soulstruct.utilities.maths import Vector4

from soulstruct_havok.utilities.maths import TRSTransform
from soulstruct_havok.wrappers.hkx2015 import AnimationHKX, SkeletonHKX

from io_soulstruct.utilities import *
from io_soulstruct.general import *
from io_soulstruct.havok.utilities import GAME_TRS_TO_BL_MATRIX, get_basis_matrix
from .utilities import *


ANIBND_RE = re.compile(r"^.*?\.anibnd(\.dcx)?$")
c0000_ANIBND_RE = re.compile(r"^c0000_.*\.anibnd(\.dcx)?$")
OBJBND_RE = re.compile(r"^.*?\.objbnd(\.dcx)?$")


class ImportHKXAnimation(LoggingOperator, ImportHelper):
    bl_idname = "import_scene.hkx_animation"
    bl_label = "Import HKX Animation"
    bl_description = "Import a HKX animation file. Can import from ANIBNDs/OBJBNDs and supports DCX-compressed files"

    filename_ext = ".hkx"

    filter_glob: bpy.props.StringProperty(
        default="*.hkx;*.hkx.dcx;*.anibnd;*.anibnd.dcx;*.objbnd;*.objbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    import_all_from_binder: bpy.props.BoolProperty(
        name="Import All From Binder",
        description="If a Binder file is opened, import all HKX anim files rather than being prompted to select one",
        default=False,
    )

    to_60_fps: bpy.props.BoolProperty(
        name="To 60 FPS",
        description="Scale animation keyframes to 60 FPS (from 30 FPS) by spacing them two frames apart",
        default=True,
    )

    files: bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    directory: bpy.props.StringProperty(
        options={'HIDDEN'},
    )

    @classmethod
    def poll(cls, context):
        """Animation's rigged armature must be selected (to extract bone names)."""
        try:
            return context.selected_objects[0].type == "ARMATURE"
        except IndexError:
            return False

    def execute(self, context):

        bl_armature = context.selected_objects[0]
        # noinspection PyTypeChecker
        armature_data = bl_armature.data  # type: bpy.types.Armature

        file_paths = [Path(self.directory, file.name) for file in self.files]
        hkxs_with_paths = []  # type: list[tuple[Path, SkeletonHKX, AnimationHKX | list[BinderEntry]]]

        for file_path in file_paths:

            if OBJBND_RE.match(file_path.name):
                # Get ANIBND from OBJBND.
                objbnd = Binder.from_path(file_path)
                anibnd_entry = objbnd.find_entry_matching_name(r".*\.anibnd(\.dcx)?")
                if not anibnd_entry:
                    raise HKXAnimationImportError("OBJBND binder does not contain an ANIBND binder.")
                skeleton_anibnd = anibnd = Binder.from_binder_entry(anibnd_entry)
            elif ANIBND_RE.match(file_path.name):
                anibnd = Binder.from_path(file_path)
                if c0000_match := c0000_ANIBND_RE.match(file_path.name):
                    # c0000 skeleton is in base `c0000.anibnd{.dcx}` file.
                    skeleton_anibnd = Binder.from_path(file_path.parent / f"c0000.anibnd{c0000_match.group(1)}")
                else:
                    skeleton_anibnd = anibnd
            else:
                # TODO: Currently require Skeleton.HKX, so have to use ANIBND.
                #  Have another deferred operator that lets you choose a loose Skeleton file after a loose animation.
                raise HKXAnimationImportError(
                    "Must import animation from an ANIBND containing a skeleton HKX file or an OBJBND containing an "
                    "ANIBND."
                )

            # Find skeleton entry.
            skeleton_entry = skeleton_anibnd.find_entry_matching_name(r"[Ss]keleton\.[Hh][Kk][Xx](\.dcx)?")
            if not skeleton_entry:
                raise HKXAnimationImportError("Must import animation from an ANIBND containing a skeleton HKX file.")
            skeleton_hkx = SkeletonHKX.from_binder_entry(skeleton_entry)

            # Find animation HKX entry/entries.
            anim_hkx_entries = anibnd.find_entries_matching_name(r"a.*\.hkx(\.dcx)?")
            if not anim_hkx_entries:
                raise HKXAnimationImportError(f"Cannot find any HKX animation files in binder {file_path}.")

            if len(anim_hkx_entries) > 1:
                if self.import_all_from_binder:
                    for entry in anim_hkx_entries:
                        try:
                            animation_hkx = entry.to_binary_file(AnimationHKX)
                        except Exception as ex:
                            self.warning(f"Error occurred while reading HKX Binder entry '{entry.name}': {ex}")
                        else:
                            hkxs_with_paths.append((file_path, skeleton_hkx, animation_hkx))
                else:
                    # Queue up all Binder entries; user will be prompted to choose entry below.
                    hkxs_with_paths.append((file_path, skeleton_hkx, anim_hkx_entries))
            else:
                try:
                    animation_hkx = anim_hkx_entries[0].to_binary_file(AnimationHKX)
                except Exception as ex:
                    self.warning(f"Error occurred while reading HKX Binder entry '{anim_hkx_entries[0].name}': {ex}")
                else:
                    hkxs_with_paths.append((file_path, skeleton_hkx, animation_hkx))

        importer = HKXAnimationImporter(self, context, bl_armature, bl_armature.name, self.to_60_fps)

        for file_path, skeleton_hkx, hkx_or_entries in hkxs_with_paths:

            if isinstance(hkx_or_entries, list):
                # Defer through entry selection operator.
                ImportHKXAnimationWithBinderChoice.run(
                    importer=importer,
                    binder_file_path=Path(file_path),
                    hkx_entries=hkx_or_entries,
                    bl_armature=bl_armature,
                    skeleton_hkx=skeleton_hkx,
                )
                continue

            animation_hkx = hkx_or_entries
            anim_name = animation_hkx.path.name.split(".")[0]

            self.info(f"Importing HKX animation for {bl_armature.name}: {anim_name}")

            p = time.perf_counter()
            animation_hkx.animation_container.spline_to_interleaved()
            self.info(f"Converted spline animation to interleaved in {time.perf_counter() - p:.4f} seconds.")

            track_bone_names = [
                annotation.trackName for annotation in animation_hkx.animation_container.animation.annotationTracks
            ]
            bl_bone_names = [b.name for b in armature_data.bones]
            for bone_name in track_bone_names:
                if bone_name not in bl_bone_names:
                    raise ValueError(f"Animation bone name '{bone_name}' is missing from selected Blender Armature.")

            p = time.perf_counter()
            arma_frames = get_armature_frames(animation_hkx, skeleton_hkx, track_bone_names)
            root_motion = get_root_motion(animation_hkx)
            self.info(f"Constructed armature animation frames in {time.perf_counter() - p:.4f} seconds.")

            # Import single animation HKX.
            p = time.perf_counter()
            try:
                importer.create_action(anim_name, arma_frames, root_motion)
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Cannot import HKX animation: {file_path.name}. Error: {ex}")
            self.info(f"Created animation action in {time.perf_counter() - p:.4f} seconds.")

        return {"FINISHED"}


# noinspection PyUnusedLocal
def get_binder_entry_choices(self, context):
    return ImportHKXAnimationWithBinderChoice.enum_options


class ImportHKXAnimationWithBinderChoice(LoggingOperator):
    """Presents user with a choice of enums from `enum_choices` class variable (set prior).

    See: https://blender.stackexchange.com/questions/6512/how-to-call-invoke-popup
    """
    bl_idname = "wm.hkx_animation_binder_choice_operator"
    bl_label = "Choose HKX Binder Entry"

    # For deferred import in `execute()`.
    importer: HKXAnimationImporter | None = None
    binder: Binder | None = None
    binder_file_path: Path = Path()
    enum_options: list[tuple[tp.Any, str, str]] = []
    hkx_entries: tp.Sequence[BinderEntry] = []
    bl_armature = None
    skeleton_hkx: SkeletonHKX | None = None

    choices_enum: bpy.props.EnumProperty(items=get_binder_entry_choices)

    # noinspection PyUnusedLocal
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    # noinspection PyUnusedLocal
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "choices_enum", expand=False)

    def execute(self, context):
        choice = int(self.choices_enum)
        entry = self.hkx_entries[choice]

        p = time.perf_counter()
        animation_hkx = entry.to_binary_file(AnimationHKX)
        self.info(f"Read `AnimationHKX` Binder entry '{entry.name}' in {time.perf_counter() - p:.4f} seconds.")

        anim_name = entry.name.split(".")[0]

        self.importer.operator = self
        self.importer.context = context

        self.info(f"Importing HKX animation for {self.bl_armature.name}: {anim_name}")

        p = time.perf_counter()
        animation_hkx.animation_container.spline_to_interleaved()
        self.info(f"Converted spline animation to interleaved in {time.perf_counter() - p:.4f} seconds.")

        track_bone_names = [
            annotation.trackName for annotation in animation_hkx.animation_container.animation.annotationTracks
        ]
        bl_bone_names = [b.name for b in self.bl_armature.data.bones]
        for bone_name in track_bone_names:
            if bone_name not in bl_bone_names:
                raise ValueError(f"Animation bone name '{bone_name}' is missing from selected Blender Armature.")

        p = time.perf_counter()
        arma_frames = get_armature_frames(animation_hkx, self.skeleton_hkx, track_bone_names)
        root_motion = get_root_motion(animation_hkx)
        self.info(f"Constructed armature animation frames in {time.perf_counter() - p:.4f} seconds.")

        p = time.perf_counter()
        try:
            self.importer.create_action(anim_name, arma_frames, root_motion)
        except Exception as ex:
            traceback.print_exc()
            return self.error(
                f"Cannot import HKX animation {anim_name} from '{self.binder_file_path.name}'. Error: {ex}"
            )
        self.info(f"Created animation action in {time.perf_counter() - p:.4f} seconds.")

        return {"FINISHED"}

    @classmethod
    def run(
        cls,
        importer: HKXAnimationImporter,
        binder_file_path: Path,
        hkx_entries: list[BinderEntry],
        bl_armature,
        skeleton_hkx: SkeletonHKX,
    ):
        cls.importer = importer
        cls.binder_file_path = binder_file_path
        cls.enum_options = [(str(i), entry.name, "") for i, entry in enumerate(hkx_entries)]
        cls.hkx_entries = hkx_entries
        cls.bl_armature = bl_armature
        cls.skeleton_hkx = skeleton_hkx
        # noinspection PyUnresolvedReferences
        bpy.ops.wm.hkx_animation_binder_choice_operator("INVOKE_DEFAULT")


class ImportCharacterHKXAnimation(LoggingOperator):
    """Detects name of selected character FLVER Armature and finds their ANIBND in the game directory."""
    bl_idname = "import_scene.hkx_character_animation"
    bl_label = "Import Character HKX Animation"
    bl_description = "Import a HKX animation file from the selected character's ANIBND"

    # TODO: Support import all?
    import_all_from_anibnd: bpy.props.BoolProperty(
        name="Import All From ANIBND",
        description="Import all HKX anim files rather than being prompted to select one (slow!)",
        default=False,
    )

    # TODO: Enabled by default. Maybe try to detect from frame timing...
    to_60_fps: bpy.props.BoolProperty(
        name="To 60 FPS",
        description="Scale animation keyframes to 60 FPS (from 30 FPS) by spacing them two frames apart",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        """Armature of a character must be selected."""
        return (
            len(context.selected_objects) == 1
            and context.selected_objects[0].type == "ARMATURE"
            and context.selected_objects[0].name.startswith("c")  # TODO: could require 'c####' template also
        )

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select a single Armature of a character (name starting with 'c').")

        settings = GlobalSettings.get_scene_settings(context)
        game_directory = settings.game_directory
        if not game_directory:
            return self.error("No game directory set in global Soulstruct Settings.")

        bl_armature = context.selected_objects[0]
        # noinspection PyTypeChecker
        armature_data = bl_armature.data  # type: bpy.types.Armature

        character_name = bl_armature.name.split(" ")[0]
        if character_name == "c0000":
            return self.error("Automatic ANIBND import is not yet supported for c0000 (player model).")

        dcx = ".dcx" if settings.resolve_dcx_type("Auto", "BINDER") != DCXType.Null else ""
        anibnd_path = Path(game_directory, "chr", f"{character_name}.anibnd{dcx}")

        if not anibnd_path.is_file():
            return self.error(f"Cannot find ANIBND for character '{character_name}' in game directory.")

        skeleton_anibnd = anibnd = Binder.from_path(anibnd_path)
        # TODO: Support c0000 automatic import. Combine all sub-ANIBND entries into one big choice list?

        # Find skeleton entry.
        skeleton_entry = skeleton_anibnd.find_entry_matching_name(r"[Ss]keleton\.[Hh][Kk][Xx](\.dcx)?")
        if not skeleton_entry:
            raise HKXAnimationImportError(
                "Must import animation from an ANIBND containing a skeleton HKX file."
            )
        skeleton_hkx = SkeletonHKX.from_binder_entry(skeleton_entry)

        # Find animation HKX entry/entries.
        anim_hkx_entries = anibnd.find_entries_matching_name(r"a.*\.hkx(\.dcx)?")
        if not anim_hkx_entries:
            raise HKXAnimationImportError(f"Cannot find any HKX animation files in binder {anibnd_path}.")

        hkxs_with_paths = []

        if len(anim_hkx_entries) > 1:
            if self.import_all_from_anibnd:
                for entry in anim_hkx_entries:
                    try:
                        animation_hkx = entry.to_binary_file(AnimationHKX)
                    except Exception as ex:
                        self.warning(f"Error occurred while reading HKX Binder entry '{entry.name}': {ex}")
                    else:
                        hkxs_with_paths.append((anibnd_path, skeleton_hkx, animation_hkx))
            else:
                # Queue up all ANIBND entries; user will be prompted to choose entry below.
                hkxs_with_paths.append((anibnd_path, skeleton_hkx, anim_hkx_entries))
        else:
            try:
                animation_hkx = anim_hkx_entries[0].to_binary_file(AnimationHKX)
            except Exception as ex:
                self.warning(
                    f"Error occurred while reading HKX Binder entry '{anim_hkx_entries[0].name}': {ex}"
                )
            else:
                hkxs_with_paths.append((anibnd_path, skeleton_hkx, animation_hkx))

        importer = HKXAnimationImporter(self, context, bl_armature, bl_armature.name, self.to_60_fps)

        for file_path, skeleton_hkx, hkx_or_entries in hkxs_with_paths:

            if isinstance(hkx_or_entries, list):
                # Defer through entry selection operator.
                ImportHKXAnimationWithBinderChoice.run(
                    importer=importer,
                    binder_file_path=Path(file_path),
                    hkx_entries=hkx_or_entries,
                    bl_armature=bl_armature,
                    skeleton_hkx=skeleton_hkx,
                )
                continue

            animation_hkx = hkx_or_entries
            anim_name = animation_hkx.path.name.split(".")[0]

            self.info(f"Importing HKX animation for {bl_armature.name}: {anim_name}")

            p = time.perf_counter()
            animation_hkx.animation_container.spline_to_interleaved()
            self.info(f"Converted spline animation to interleaved in {time.perf_counter() - p:.4f} seconds.")

            track_bone_names = [
                annotation.trackName for annotation in animation_hkx.animation_container.animation.annotationTracks
            ]
            bl_bone_names = [b.name for b in armature_data.bones]
            for bone_name in track_bone_names:
                if bone_name not in bl_bone_names:
                    raise ValueError(
                        f"Animation bone name '{bone_name}' is missing from selected Blender Armature."
                    )

            p = time.perf_counter()
            arma_frames = get_armature_frames(animation_hkx, skeleton_hkx, track_bone_names)
            root_motion = get_root_motion(animation_hkx)
            self.info(f"Constructed armature animation frames in {time.perf_counter() - p:.4f} seconds.")

            # Import single animation HKX.
            p = time.perf_counter()
            try:
                importer.create_action(anim_name, arma_frames, root_motion)
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Cannot import HKX animation: {file_path.name}. Error: {ex}")
            self.info(f"Created animation action in {time.perf_counter() - p:.4f} seconds.")

        return {"FINISHED"}


class HKXAnimationImporter:
    """Manages imports for a batch of HKX files imported simultaneously.

    TODO: Currently very slow. Takes ~1 second to load c2240 (Capra) idle, and ~8 seconds to load c5280 (Quelaag) idle.
     This step is responsible for ~90% of that time. Notes/ideas:
        - At bare minimum, we're iterating over every frame, over every bone, doing 2-3 matrix multiplications and a
        matrix inversion to get the Blender basis matrix, decomposing it into TRS, doing a dot product with the previous
        frame's rotation to avoid quat flipping, then iterating over every frame and every bone AGAIN to actually record
        the keyframes.
        - Obvious speed boost #1: I'm calculating the inverse of `bone.matrix_local` - which does NOT change at all -
        on every single frame.
        - Well, that made barely any difference.
    """

    FAST = {"FAST"}

    model_name: str
    to_60_fps: bool

    def __init__(
        self,
        operator: LoggingOperator,
        context,
        bl_armature,
        model_name: str,
        to_60_fps: bool,
    ):
        self.operator = operator
        self.context = context

        self.bl_armature = bl_armature
        self.model_name = model_name
        self.to_60_fps = to_60_fps

    def create_action(
        self,
        animation_name: str,
        arma_frames: list[dict[str, TRSTransform]],
        root_motion: None | list[Vector4] = None,
    ):
        """Import single animation HKX."""

        if root_motion is not None:
            if len(root_motion) != len(arma_frames):
                raise ValueError(
                    f"Number of animation root motion frames ({len(root_motion)}) does not match number of bone "
                    f"animation frames ({len(arma_frames)})."
                )
            root_motion_samples = [[] for _ in range(3)]
            for vector in root_motion:
                root_motion_samples[0].append(vector.x)
                root_motion_samples[1].append(vector.y)
                root_motion_samples[2].append(vector.z)
        else:
            root_motion_samples = None

        action_name = f"{self.model_name}|{animation_name}"
        action = None
        original_location = self.bl_armature.location.copy()
        frame_scaling = 2 if self.to_60_fps else 1
        try:
            self.bl_armature.animation_data_create()
            self.bl_armature.animation_data.action = action = bpy.data.actions.new(name=action_name)
            bone_basis_samples = self._get_bone_basis_samples(arma_frames)
            # self._add_keyframes_legacy(basis_frames, root_motion, frame_scaling)
            self._add_keyframes_batch(bone_basis_samples, root_motion_samples, frame_scaling)
        except Exception:
            if action:
                bpy.data.actions.remove(action)
            self.bl_armature.location = original_location  # reset location (i.e. erase last root motion)
            # TODO: should reset last bone transforms (`matrix_basis`) as well
            raise

        # Ensure action is not deleted when not in use.
        action.use_fake_user = True
        # Update all F-curves and make them cycle.
        for fcurve in action.fcurves:
            fcurve.modifiers.new("CYCLES")  # default settings are fine
            fcurve.update()
        # Update Blender timeline start/stop times.
        bpy.context.scene.frame_start = int(action.frame_range[0])
        bpy.context.scene.frame_end = int(action.frame_range[1])
        bpy.context.scene.frame_set(bpy.context.scene.frame_start)

    def _get_bone_basis_samples(
        self, arma_frames: list[dict[str, TRSTransform]]
    ) -> dict[str, list[list[float]]]:
        """Convert a Havok HKX animation file to a Blender action (with fully-sampled keyframes).

        The action to add keyframes to should already be the active action on `self.bl_armature`. This is required to
        use the `keyframe_insert()` method, which allows full-Vector and full-Quaternion keyframes to be inserted and
        have Blender properly interpolate (e.g. Quaternion slerp) between them, which it cannot do if we use FCurves and
        set the `keyframe_points` directly for each coordinate.

        We also use `self.bl_armature` to properly set the `matrix_basis` of each pose bone relative to the bone resting
        positions (set to the edit bones).

        TODO: Does not support changes in Blender bone names (e.g. '<DUPE>' suffix).
        """
        # Convert armature-space frame data to Blender `(location, rotation_quaternion, scale)` tuples.
        # Note that we decompose the basis matrices so that quaternion discontinuities are handled properly.
        last_frame_rotations = {}  # type: dict[str, BlenderQuaternion]

        bone_basis_samples = {
            bone_name: [[] for _ in range(10)] for bone_name in arma_frames[0].keys()
        }  # type: dict[str, list[list[float]]]

        # We'll be using the inverted local matrices of each bone on every frame to calculate their basis matrices.
        cached_local_inv_matrices = {
            bone.name: bone.matrix_local.inverted()
            for bone in self.bl_armature.data.bones
        }

        for frame in arma_frames:
            bl_arma_matrices = {
                bone_name: GAME_TRS_TO_BL_MATRIX(transform) for bone_name, transform in frame.items()
            }
            cached_arma_inv_matrices = {}  # cached for frame as needed

            for bone_name, bl_arma_matrix in bl_arma_matrices.items():
                basis_samples = bone_basis_samples[bone_name]

                bl_edit_bone = self.bl_armature.data.bones[bone_name]

                if bl_edit_bone.parent is not None and bl_edit_bone.parent.name not in cached_arma_inv_matrices:
                    # Cache parent's inverted armature matrix (may be needed by other sibling bones this frame).
                    parent_name = bl_edit_bone.parent.name
                    cached_arma_inv_matrices[parent_name] = bl_arma_matrices[parent_name].inverted()

                bl_basis_matrix = get_basis_matrix(
                    self.bl_armature,
                    bone_name,
                    bl_arma_matrix,
                    cached_local_inv_matrices,
                    cached_arma_inv_matrices,
                )

                t, r, s = bl_basis_matrix.decompose()

                if bone_name in last_frame_rotations:
                    if last_frame_rotations[bone_name].dot(r) < 0:
                        r.negate()  # negate quaternion to avoid discontinuity (reverse direction of rotation)

                for samples, sample_float in zip(basis_samples, [t.x, t.y, t.z, r.w, r.x, r.y, r.z, s.x, s.y, s.z]):
                    samples.append(sample_float)

                last_frame_rotations[bone_name] = r

        return bone_basis_samples

    def _add_keyframes_batch(
        self,
        bone_basis_samples: dict[str, list[list[float]]],
        root_motion_samples: list[list[float], list[float], list[float]] | None,
        frame_scaling: int,
    ):
        """
        Faster method of adding all bone and (optional) root keyframe data.

        Constructs `FCurves` with known length and uses `foreach_set` to batch-set all the `.co` attributes of the
        curve keyframe points at once.

        `bone_basis_samples` maps bone names to ten lists of floats (location_x, location_y, etc.).
        """
        p = time.perf_counter()
        action = self.bl_armature.animation_data.action

        # Initialize FCurves for root motion and bones
        if root_motion_samples is not None:
            root_loc_fcurves = [action.fcurves.new(data_path="location", index=i) for i in range(3)]
        else:
            root_loc_fcurves = []

        bone_fcurves = {}
        for bone_name in bone_basis_samples.keys():
            bone_fcurves[bone_name] = []  # ten FCurves per bone
            bone_fcurves[bone_name] += [
                action.fcurves.new(data_path=f"pose.bones[\"{bone_name}\"].location", index=i)
                for i in range(3)
            ]
            bone_fcurves[bone_name] += [
                action.fcurves.new(data_path=f"pose.bones[\"{bone_name}\"].rotation_quaternion", index=i)
                for i in range(4)
            ]
            bone_fcurves[bone_name] += [
                action.fcurves.new(data_path=f"pose.bones[\"{bone_name}\"].scale", index=i)
                for i in range(3)
            ]

        # Build lists of FCurve keyframe points by initializing their size and using `foreach_set`.
        # Each keyframe point has a `.co` attribute to which we set `(bl_frame_index, value)` (per dimension).
        # `foreach_set` requires that we flatten the list of tuples to be assigned, a la:
        #    `[bl_frame_index_0, value_0, bl_frame_index_1, value_1, ...]`
        # which we do with a list comprehension.
        if root_loc_fcurves:
            for dim_samples, fcurve in zip(root_motion_samples, root_loc_fcurves, strict=True):
                fcurve.keyframe_points.add(count=len(dim_samples))
                root_dim_flat = [
                    x
                    for frame_index, sample_float in enumerate(dim_samples)
                    for x in [frame_index * frame_scaling, sample_float]
                ]
                fcurve.keyframe_points.foreach_set("co", root_dim_flat)

        for bone_name, bone_transform_fcurves in bone_fcurves.items():
            basis_samples = bone_basis_samples[bone_name]
            for bone_fcurve, samples in zip(bone_transform_fcurves, basis_samples, strict=True):
                bone_fcurve.keyframe_points.add(count=len(samples))
                bone_dim_flat = [
                    x
                    for frame_index, sample_float in enumerate(samples)
                    for x in [frame_index * frame_scaling, sample_float]
                ]
                bone_fcurve.keyframe_points.foreach_set("co", bone_dim_flat)

        print(f"batch keyframe_time: {time.perf_counter() - p:.4f}")

    def _add_keyframes_legacy(
        self,
        basis_frames: list[dict[str, tuple[Vector, BlenderQuaternion, Vector]]],
        root_motion: None | list[Vector4],
        frame_scaling: int,
    ):
        """
        Slow `keyframe_insert()`-based method of adding all bone and (optional) root keyframes.

        The action to add keyframes to should already be the active action on `self.bl_armature`. This is required to
        use the `keyframe_insert()` method, which allows full-Vector and full-Quaternion keyframes to be inserted and
        have Blender properly interpolate (e.g. Quaternion slerp) between them, which it cannot do if we use FCurves and
        set the `keyframe_points` directly for each coordinate.
        """

        p = time.perf_counter()

        for frame_index, frame in enumerate(basis_frames):

            bl_frame_index = frame_scaling * frame_index

            if root_motion is not None:
                self.bl_armature.location = GAME_TO_BL_VECTOR(root_motion[frame_index])  # drop useless fourth element
                self.bl_armature.keyframe_insert(data_path="location", frame=bl_frame_index)

            for bone_name, (t, r, s) in frame.items():
                bl_pose_bone = self.bl_armature.pose.bones[bone_name]
                bl_pose_bone.location = t
                bl_pose_bone.rotation_quaternion = r
                bl_pose_bone.scale = s

                # Insert keyframes for location, rotation, scale.
                p = time.perf_counter()
                bl_pose_bone.keyframe_insert(data_path="location", frame=bl_frame_index)
                bl_pose_bone.keyframe_insert(data_path="rotation_quaternion", frame=bl_frame_index)
                bl_pose_bone.keyframe_insert(data_path="scale", frame=bl_frame_index)

        print(f"legacy keyframe_time: {time.perf_counter() - p:.4f}")
