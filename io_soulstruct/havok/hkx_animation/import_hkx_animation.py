"""VERY early/experimental system for importing/exporting DSR animations into Blender."""
from __future__ import annotations

import re
import traceback
import typing as tp
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector, Quaternion as BlenderQuaternion

from soulstruct.containers import Binder, BinderEntry
from soulstruct.utilities.maths import Vector4

from soulstruct_havok.utilities.maths import TRSTransform
from soulstruct_havok.wrappers.hkx2015 import AnimationHKX, SkeletonHKX

from io_soulstruct.utilities import *
from io_soulstruct.havok.utilities import GAME_TRS_TO_BL_MATRIX, get_basis_matrix
from .utilities import *


def FL_TO_BL_VECTOR(sequence) -> Vector:
    """Simply swaps Y and Z axes."""
    return Vector((sequence[0], sequence[2], sequence[1]))


ANIBND_RE = re.compile(r"^.*?\.anibnd(\.dcx)?$")
c0000_ANIBND_RE = re.compile(r"^c0000_.*\.anibnd(\.dcx)?$")
OBJBND_RE = re.compile(r"^.*?\.objbnd(\.dcx)?$")


class ImportHKXAnimation(LoggingOperator, ImportHelper):
    bl_idname = "import_scene.hkx_animation"
    bl_label = "Import HKX Animation"
    bl_description = "Import a HKX animation file. Can import from BNDs and supports DCX-compressed files"

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
        description="Scale animation keyframes to 60 FPS (from 30 FPS)",
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

        for (file_path, skeleton_hkx, hkx_or_entries) in hkxs_with_paths:

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

            animation_hkx.animation_container.spline_to_interleaved()

            track_bone_names = [
                annotation.trackName for annotation in animation_hkx.animation_container.animation.annotationTracks
            ]
            bl_bone_names = [b.name for b in armature_data.bones]
            for bone_name in track_bone_names:
                if bone_name not in bl_bone_names:
                    raise ValueError(f"Animation bone name '{bone_name}' is missing from selected Blender Armature.")

            arma_frames = get_armature_frames(animation_hkx, skeleton_hkx, track_bone_names)
            root_motion = get_root_motion(animation_hkx)

            # Import single animation HKX.
            try:
                importer.create_action(anim_name, arma_frames, root_motion)
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Cannot import HKX animation: {file_path.name}. Error: {ex}")

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
        animation_hkx = entry.to_binary_file(AnimationHKX)
        anim_name = entry.name.split(".")[0]

        self.importer.operator = self
        self.importer.context = context

        self.info(f"Importing HKX animation for {self.bl_armature.name}: {anim_name}")

        animation_hkx.animation_container.spline_to_interleaved()

        track_bone_names = [
            annotation.trackName for annotation in animation_hkx.animation_container.animation.annotationTracks
        ]
        bl_bone_names = [b.name for b in self.bl_armature.data.bones]
        for bone_name in track_bone_names:
            if bone_name not in bl_bone_names:
                raise ValueError(f"Animation bone name '{bone_name}' is missing from selected Blender Armature.")

        arma_frames = get_armature_frames(animation_hkx, self.skeleton_hkx, track_bone_names)
        root_motion = get_root_motion(animation_hkx)

        try:
            self.importer.create_action(anim_name, arma_frames, root_motion)
        except Exception as ex:
            traceback.print_exc()
            return self.error(
                f"Cannot import HKX animation {anim_name} from '{self.binder_file_path.name}'. Error: {ex}"
            )

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


class HKXAnimationImporter:
    """Manages imports for a batch of HKX files imported simultaneously."""

    FAST = {"FAST"}

    model_name: str
    to_60_fps: bool

    def __init__(
        self,
        operator: ImportHKXAnimation,
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
        action_name = f"{self.model_name}|{animation_name}"
        action = None
        original_location = self.bl_armature.location.copy()
        try:
            self.bl_armature.animation_data_create()
            self.bl_armature.animation_data.action = action = bpy.data.actions.new(name=action_name)
            self._add_armature_keyframes(arma_frames, root_motion)
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

    def _add_armature_keyframes(
        self,
        arma_frames: list[dict[str, TRSTransform]],
        root_motion: None | list[Vector4] = None,
    ):
        """Convert a Havok HKX animation file to a Blender action (with fully-sampled keyframes).

        The action to add keyframes to should already be the active action on `self.bl_armature`. This is required to
        use the `keyframe_insert()` method, which allows full-Vector and full-Quaternion keyframes to be inserted and
        have Blender properly interpolate (e.g. Quaternion slerp) between them, which it cannot do if we use FCurves and
        set the `keyframe_points` directly for each coordinate.

        We also use `self.bl_armature` to properly set the `matrix_basis` of each pose bone relative to the bone resting
        positions (set to the edit bones).

        `skeleton_hkx` is required to compute animation frame transforms in object coordinates, as the bone hierarchy
        can differ for HKX skeletons versus the FLVER skeleton in `bl_armature`.

        TODO: Does not support changes in Blender bone names (e.g. '<DUPE>' suffix).
        """
        if root_motion is not None:
            if len(root_motion) != len(arma_frames):
                raise ValueError(
                    f"Number of animation root motion frames ({len(root_motion)}) does not match number of bone "
                    f"animation frames ({len(arma_frames)})."
                )

        # FIRST: Convert armature-space frame data to Blender `(location, rotation_quaternion, scale)` tuples.
        # Note that we decompose the basis matrices so that quaternion discontinuities are handled properly.
        last_frame_rotations = {}  # type: dict[str, BlenderQuaternion]
        basis_frames = []  # type: list[dict[str, tuple[Vector, BlenderQuaternion, Vector]]]

        for frame in arma_frames:
            bl_arma_matrices = {
                bone_name: GAME_TRS_TO_BL_MATRIX(transform) for bone_name, transform in frame.items()
            }
            bl_arma_inv_matrices = {}  # cached for frame as needed

            basis_frame = {}

            for bone_name, bl_arma_matrix in bl_arma_matrices.items():
                bl_edit_bone = self.bl_armature.data.bones[bone_name]
                if bl_edit_bone.parent is not None and bl_edit_bone.parent.name not in bl_arma_inv_matrices:
                    # Cache parent's inverted armature matrix (may be needed by other sibling bones this frame).
                    parent_name = bl_edit_bone.parent.name
                    bl_arma_inv_matrices[parent_name] = bl_arma_matrices[parent_name].inverted()

                bl_basis_matrix = get_basis_matrix(self.bl_armature, bone_name, bl_arma_matrix, bl_arma_inv_matrices)
                t, r, s = bl_basis_matrix.decompose()

                if bone_name in last_frame_rotations:
                    if last_frame_rotations[bone_name].dot(r) < 0:
                        r.negate()  # negate quaternion to avoid discontinuity (reverse direction of rotation)

                basis_frame[bone_name] = (t, r, s)
                last_frame_rotations[bone_name] = r

            basis_frames.append(basis_frame)

        for frame_index, frame in enumerate(basis_frames):

            # TODO: Make this a more general 'frame scaling' option, e.g. by having importer take input/output FPS.
            #  (Should be able to read/infer input FPS from HKX file, actually.)
            bl_frame_index = frame_index * 2 if self.to_60_fps else frame_index

            if root_motion is not None:
                self.bl_armature.location = GAME_TO_BL_VECTOR(root_motion[frame_index])  # drop useless fourth element
                self.bl_armature.keyframe_insert(data_path="location", frame=bl_frame_index)

            for bone_name, (t, r, s) in frame.items():
                bl_pose_bone = self.bl_armature.pose.bones[bone_name]
                bl_pose_bone.location = t
                bl_pose_bone.rotation_quaternion = r
                bl_pose_bone.scale = s

                # Insert keyframes for location, rotation, scale.
                bl_pose_bone.keyframe_insert(data_path="location", frame=bl_frame_index)
                bl_pose_bone.keyframe_insert(data_path="rotation_quaternion", frame=bl_frame_index)
                bl_pose_bone.keyframe_insert(data_path="scale", frame=bl_frame_index)
