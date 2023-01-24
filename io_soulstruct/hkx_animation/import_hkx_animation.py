"""VERY early/experimental system for importing/exporting DSR animations into Blender."""
from __future__ import annotations

import re
import traceback
import typing as tp
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector, Matrix

from soulstruct.base.binder_entry import BinderEntry
from soulstruct.containers import BaseBinder, Binder

from soulstruct_havok.utilities.maths import TRSTransform
from soulstruct_havok.wrappers.hkx2015 import AnimationHKX, SkeletonHKX
from soulstruct_havok.wrappers.hkx2015.animation_manager import AnimationManager

from io_soulstruct.utilities import *
from .utilities import *


def FL_TO_BL_VECTOR(sequence) -> Vector:
    """Simply swaps Y and Z axes."""
    return Vector((sequence[0], sequence[2], sequence[1]))


ANIBND_RE = re.compile(r"^.*?\.anibnd(\.dcx)?$")


class ImportHKXAnimation(LoggingOperator, ImportHelper):
    bl_idname = "import_scene.hkx_animation"
    bl_label = "Import HKX Animation"
    bl_description = "Import a HKX animation file. Can import from BNDs and supports DCX-compressed files"

    # ImportHelper mixin class uses this
    filename_ext = ".hkx"

    filter_glob: bpy.props.StringProperty(
        default="*.hkx;*.hkx.dcx;*.anibnd;*.anibnd.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    import_all_from_binder: bpy.props.BoolProperty(
        name="Import All From Binder",
        description="If a Binder file is opened, import all HKX anim files rather than being prompted to select one",
        default=False,
    )

    assign_to_armature: bpy.props.BoolProperty(
        name="Assign to Armature",
        description="Assign imported animation action to selected FLVER armature immediately",
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

        file_paths = [Path(self.directory, file.name) for file in self.files]
        hkxs_with_paths = []  # type: list[tuple[Path, AnimationHKX | list[BinderEntry]]]
        skeleton_entries = []

        for file_path in file_paths:

            if ANIBND_RE.match(file_path.name):
                binder = Binder(file_path)

                # Find skeleton entry.
                skeleton_entry = binder.find_entry_matching_name(r"[Ss]keleton\.[Hh][Kk][Xx](\.dcx)?")
                if not skeleton_entry:
                    raise HKXAnimationImportError("Must import animation from an ANIBND containing a skeleton HKX file.")
                skeleton_entries.append(skeleton_entry)

                # Find animation HKX entry/entries.
                hkx_entries = binder.find_entries_matching_name(r"a.*\.hkx(\.dcx)?")
                if not hkx_entries:
                    raise HKXAnimationImportError(f"Cannot find any HKX animation files in binder {file_path}.")

                if len(hkx_entries) > 1:
                    if self.import_all_from_binder:
                        for entry in hkx_entries:
                            try:
                                hkx = AnimationHKX(entry.data)
                            except Exception as ex:
                                self.warning(f"Error occurred while reading HKX Binder entry '{entry.name}': {ex}")
                            else:
                                hkx.path = Path(entry.name)  # also done in `GameFile`, but explicitly needed below
                                hkxs_with_paths.append((file_path, hkx))
                    else:
                        # Queue up entire Binder; user will be prompted to choose entry below.
                        hkxs_with_paths.append((file_path, hkx_entries))
                else:
                    try:
                        hkx = AnimationHKX(hkx_entries[0].data)
                    except Exception as ex:
                        self.warning(f"Error occurred while reading HKX Binder entry '{hkx_entries[0].name}': {ex}")
                    else:
                        hkxs_with_paths.append((file_path, hkx))
            else:
                # TODO: Currently require Skeleton.HKX, so have to use ANIBND.
                #  Have another deferred operator that lets you choose a loose Skeleton file after a loose animation.
                raise HKXAnimationImportError("Must import animation from an ANIBND containing a skeleton HKX file.")
                # try:
                #     hkx = AnimationHKX(file_path)
                # except Exception as ex:
                #     self.warning(f"Error occurred while reading HKX animation file '{file_path.name}': {ex}")
                # else:
                #     hkxs_with_paths.append((file_path, hkx))

        importer = HKXAnimationImporter(self, context)

        for (file_path, hkx_or_entries), skeleton_entry in zip(hkxs_with_paths, skeleton_entries):

            if isinstance(hkx_or_entries, list):
                # Defer through entry selection operator.
                ImportHKXAnimationWithBinderChoice.run(
                    importer=importer,
                    binder_file_path=Path(file_path),
                    hkx_entries=hkx_or_entries,
                    bl_armature=bl_armature,
                    skeleton_entry=skeleton_entry,
                    assign_to_armature=self.assign_to_armature,
                )
                continue

            hkx = hkx_or_entries
            hkx_name = hkx.path.name.split(".")[0]
            skeleton_hkx = SkeletonHKX(skeleton_entry)

            self.info(f"Importing HKX animation: {hkx_name}")

            # Import single HKX without MSB transform.
            try:
                action = importer.import_hkx_anim(
                    hkx, name=hkx_name, bl_armature=bl_armature, skeleton_hkx=skeleton_hkx)
            except Exception as ex:
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import HKX animation: {file_path.name}. Error: {ex}")
            else:
                try:
                    bl_armature.animation_data_create()
                    bl_armature.animation_data.action = action
                except Exception as ex:
                    self.warning(f"Animation was imported, but action could not be assigned to Armature. Error: {ex}")

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
    importer: tp.Optional[HKXAnimationImporter] = None
    binder: tp.Optional[BaseBinder] = None
    binder_file_path: Path = Path()
    enum_options: list[tuple[tp.Any, str, str]] = []
    hkx_entries: tp.Sequence[BinderEntry] = []
    bl_armature = None
    skeleton_entry: tp.Optional[BinderEntry] = None
    assign_to_armature: bool = False

    choices_enum: bpy.props.EnumProperty(items=get_binder_entry_choices)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "choices_enum", expand=False)

    def execute(self, context):
        choice = int(self.choices_enum)
        entry = self.hkx_entries[choice]
        hkx = AnimationHKX(entry.data)
        hkx_name = entry.name.split(".")[0]
        skeleton_hkx = SkeletonHKX(self.skeleton_entry)

        self.importer.operator = self
        self.importer.context = context

        try:
            action = self.importer.import_hkx_anim(
                hkx, name=hkx_name, bl_armature=self.bl_armature, skeleton_hkx=skeleton_hkx)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot import HKX animation {hkx_name} from '{self.binder_file_path.name}'. Error: {ex}")
        else:
            try:
                self.bl_armature.animation_data_create()
                self.bl_armature.animation_data.action = action
            except Exception as ex:
                self.warning(f"Animation was imported, but action could not be assigned to Armature. Error: {ex}")

        return {"FINISHED"}

    @classmethod
    def run(
        cls,
        importer: HKXAnimationImporter,
        binder_file_path: Path,
        hkx_entries: list[BinderEntry],
        bl_armature,
        skeleton_entry: BinderEntry,
        assign_to_armature: bool,
    ):
        cls.importer = importer
        cls.binder_file_path = binder_file_path
        cls.enum_options = [(str(i), entry.name, "") for i, entry in enumerate(hkx_entries)]
        cls.hkx_entries = hkx_entries
        cls.bl_armature = bl_armature
        cls.skeleton_entry = skeleton_entry
        cls.assign_to_armature = assign_to_armature
        # noinspection PyUnresolvedReferences
        bpy.ops.wm.hkx_animation_binder_choice_operator("INVOKE_DEFAULT")


class HKXAnimationImporter:
    """Manages imports for a batch of HKX files imported simultaneously."""

    hkx: tp.Optional[AnimationHKX]
    name: str
    skeleton_hkx: tp.Optional[SkeletonHKX]

    def __init__(
        self,
        operator: ImportHKXAnimation,
        context,
    ):
        self.operator = operator
        self.context = context

        self.hkx = None
        self.name = ""
        self.skeleton_hkx = None
        self.action = None

    def import_hkx_anim(self, hkx: AnimationHKX, name: str, bl_armature, skeleton_hkx: SkeletonHKX):
        """Read a HKX animation into a Blender action."""
        self.hkx = hkx
        self.name = name  # e.g. "a00_3000"
        self.skeleton_hkx = skeleton_hkx

        try:
            self.create_blender_action(self.hkx, self.name, bl_armature, skeleton_hkx)
        except Exception:
            # Delete partially created action before raising.
            if self.action is not None:
                bpy.data.actions.remove(self.action)
                self.action = None
            raise
        else:
            self.action.use_fake_user = True
            return self.action

    def create_blender_action(
        self,
        animation_hkx: AnimationHKX,
        animation_name: str,
        bl_armature,
        skeleton_hkx: SkeletonHKX,
    ):
        """Convert a Havok HKX animation file to a Blender action (with fully-sampled keyframes).

        `bl_armature` is required to properly set the `matrix_basis` of each pose bone relative to the bone resting
        positions (set to the edit bones).

        `skeleton_hkx` is required to compute animation frame transforms in object coordinates, as the bone hierarchy
        can differ for HKX skeletons versus the FLVER skeleton in `bl_armature`.

        TODO: Does not support changes in Blender bone names (e.g. '<DUPE>' suffix).
        TODO: Time-scaling argument (with linear interpolation)?
        """

        animation_hkx.spline_to_interleaved()
        try:
            root_motion = animation_hkx.get_reference_frame_samples()
        except TypeError:
            root_motion = None
        manager = AnimationManager(skeleton_hkx, {0: animation_hkx})

        track_bone_names = [annotation.trackName for annotation in animation_hkx.animation.annotationTracks]
        bl_bone_names = [b.name for b in bl_armature.data.bones]
        for bone_name in track_bone_names:
            if bone_name not in bl_bone_names:
                raise ValueError(f"Animation bone name '{bone_name}' is missing from selected Blender Armature.")

        # Get bone local matrix list in same order as tracks.
        bl_bones = [bl_armature.data.bones[bone_name] for bone_name in track_bone_names]

        # Create Blender 'action', which is a data-block containing the animation data.
        action = self.action = bpy.data.actions.new(animation_name)
        fast = {"FAST"}

        # Create all FCurves.
        if root_motion is not None:
            root_curves = {
                "loc_x": action.fcurves.new("location", index=0),
                "loc_y": action.fcurves.new("location", index=1),
                "loc_z": action.fcurves.new("location", index=2),
            }
        else:
            root_curves = {}

        bone_curves = {}

        for bone_name in track_bone_names:
            data_path_prefix = f"pose.bones[\"{bone_name}\"]"
            location_data_path = f"{data_path_prefix}.location"
            rotation_data_path = f"{data_path_prefix}.rotation_quaternion"
            scale_data_path = f"{data_path_prefix}.scale"

            # Create 10 FCurves.
            bone_curves[bone_name, "loc_x"] = action.fcurves.new(location_data_path, index=0)
            bone_curves[bone_name, "loc_y"] = action.fcurves.new(location_data_path, index=1)
            bone_curves[bone_name, "loc_z"] = action.fcurves.new(location_data_path, index=2)

            bone_curves[bone_name, "rot_w"] = action.fcurves.new(rotation_data_path, index=0)
            bone_curves[bone_name, "rot_x"] = action.fcurves.new(rotation_data_path, index=1)
            bone_curves[bone_name, "rot_y"] = action.fcurves.new(rotation_data_path, index=2)
            bone_curves[bone_name, "rot_z"] = action.fcurves.new(rotation_data_path, index=3)

            bone_curves[bone_name, "scale_x"] = action.fcurves.new(scale_data_path, index=0)
            bone_curves[bone_name, "scale_y"] = action.fcurves.new(scale_data_path, index=1)
            bone_curves[bone_name, "scale_z"] = action.fcurves.new(scale_data_path, index=2)

        for frame_index, track_transforms in enumerate(animation_hkx.interleaved_data):

            if root_motion is not None:
                bl_frame_root_motion = GAME_TO_BL_VECTOR(root_motion[frame_index])  # drop useless fourth element
                root_curves["loc_x"].keyframe_points.insert(frame_index, bl_frame_root_motion.x, options=fast)
                root_curves["loc_y"].keyframe_points.insert(frame_index, bl_frame_root_motion.y, options=fast)
                root_curves["loc_z"].keyframe_points.insert(frame_index, bl_frame_root_motion.z, options=fast)

            world_transforms = manager.get_all_world_space_transforms_in_frame(frame_index)
            bl_world_matrices = [trs_transform_to_bl_matrix(transform) for transform in world_transforms]
            bl_world_inv_matrices = {}  # cached by bone name for frame as needed

            for bone_name, bl_world_matrix, bl_bone in zip(track_bone_names, bl_world_matrices, bl_bones):

                if bl_bone.parent is not None and bl_bone.parent.name not in bl_world_inv_matrices:
                    # Cache parent's inverted world matrix (may be needed by other sibling bones this frame).
                    parent_index = track_bone_names.index(bl_bone.parent.name)
                    bl_world_inv_matrices[bl_bone.parent.name] = bl_world_matrices[parent_index].inverted()

                bl_basis_matrix = get_basis_matrix(bl_armature, bone_name, bl_world_matrix, bl_world_inv_matrices)
                t, r, s = bl_basis_matrix.decompose()

                bone_curves[bone_name, "loc_x"].keyframe_points.insert(frame_index, t.x, options=fast)
                bone_curves[bone_name, "loc_y"].keyframe_points.insert(frame_index, t.y, options=fast)
                bone_curves[bone_name, "loc_z"].keyframe_points.insert(frame_index, t.z, options=fast)

                bone_curves[bone_name, "rot_w"].keyframe_points.insert(frame_index, r.w, options=fast)
                bone_curves[bone_name, "rot_x"].keyframe_points.insert(frame_index, r.x, options=fast)
                bone_curves[bone_name, "rot_y"].keyframe_points.insert(frame_index, r.y, options=fast)
                bone_curves[bone_name, "rot_z"].keyframe_points.insert(frame_index, r.z, options=fast)

                bone_curves[bone_name, "scale_x"].keyframe_points.insert(frame_index, s.x, options=fast)
                bone_curves[bone_name, "scale_y"].keyframe_points.insert(frame_index, s.y, options=fast)
                bone_curves[bone_name, "scale_z"].keyframe_points.insert(frame_index, s.z, options=fast)

        # Update all F-curves and make them cycle.
        for fcurve in root_curves.values():
            fcurve.modifiers.new("CYCLES")  # default settings are fine
            fcurve.update()
        for fcurve in bone_curves.values():
            fcurve.modifiers.new("CYCLES")  # default settings are fine
            fcurve.update()

        return action


def trs_transform_to_bl_matrix(transform: TRSTransform) -> Matrix:
    """Convert a game `TRSTransform` to a Blender 4x4 `Matrix`."""
    bl_translate = GAME_TO_BL_VECTOR(transform.translation)
    bl_rotate = FL_TO_BL_QUAT(transform.rotation)
    bl_scale = GAME_TO_BL_VECTOR(transform.scale)
    return Matrix.LocRotScale(bl_translate, bl_rotate, bl_scale)


def get_world_matrix(armature, bone_name, basis=None) -> Matrix:
    """Demonstrates how Blender calculates `pose_bone.matrix` (world matrix) for `bone_name`.

    TODO: Likely needed at export to convert the curve keyframes (in basis space) back to world space.
    """
    local = armature.data.bones[bone_name].matrix_local
    if basis is None:
        basis = armature.pose.bones[bone_name].matrix_basis

    parent = armature.pose.bones[bone_name].parent
    if parent is None:  # root bone is simple
        # world = local @ basis
        return local @ basis
    else:
        # Apply relative transform of local (edit bone) from parent and then world position of parent:
        #     world = parent_world @ (parent_local.inv @ local) @ basis
        #  -> basis = (parent_local.inv @ local)parent_local @ parent_world.inv @ world
        parent_local = armature.data.bones[parent.name].matrix_local
        return get_world_matrix(armature, parent.name) @ parent_local.inverted() @ local @ basis


def get_basis_matrix(armature, bone_name, world_matrix, world_inv_matrices: dict):
    """Inverse of above: get `pose_bone.matrix_basis` from `world_matrix` by inverted Blender's process."""
    local = armature.data.bones[bone_name].matrix_local
    parent = armature.pose.bones[bone_name].parent

    if parent is None:
        return local.inverted() @ world_matrix
    else:
        # TODO: Can't I just use `parent` directly? Why the indexing?
        parent_world_matrix_inv = world_inv_matrices[parent.name]
        return local.inverted() @ armature.data.bones[parent.name].matrix_local @ parent_world_matrix_inv @ world_matrix
