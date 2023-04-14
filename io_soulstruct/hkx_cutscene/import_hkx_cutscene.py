"""VERY early/experimental system for importing/exporting DSR animations into Blender."""
from __future__ import annotations

import re
import traceback
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector, Matrix

from soulstruct.darksouls1r.maps import MSB  # TODO: will need `MapStudioDirectory` eventually
from soulstruct.base.animations.sibcam import CameraFrameTransform

from soulstruct_havok.utilities.maths import TRSTransform
from soulstruct_havok.wrappers.hkx2015 import RemoBND

from io_soulstruct.utilities import *
from .utilities import *


def FL_TO_BL_VECTOR(sequence) -> Vector:
    """Simply swaps Y and Z axes."""
    return Vector((sequence[0], sequence[2], sequence[1]))


REMOBND_RE = re.compile(r"^.*?\.remobnd(\.dcx)?$")


class ImportHKXCutscene(LoggingOperator, ImportHelper):
    bl_idname = "import_scene.hkx_cutscene"
    bl_label = "Import HKX Cutscene"
    bl_description = "Import a HKX cutscene file from a RemoBND"

    # ImportHelper mixin class uses this
    filename_ext = ".remobnd"

    filter_glob: bpy.props.StringProperty(
        default="*.remobnd;*.remobnd.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    assign_to_armature: bpy.props.BoolProperty(
        name="Assign to Armature",
        description="Assign imported cutscene action to selected FLVER armature immediately",
        default=True,
    )

    camera_data_only: bpy.props.BoolProperty(
        name="Camera Data Only",
        description="Only load camera animation data",
        default=False,
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
        remobnds_with_paths = []  # type: list[tuple[Path, RemoBND]]

        for file_path in file_paths:

            if REMOBND_RE.match(file_path.name):
                try:
                    remobnd = RemoBND.from_path(file_path)
                except Exception as ex:
                    raise HKXCutsceneImportError(f"Could not parse RemoBND file '{file_path}': {ex}")
                remobnds_with_paths.append((file_path, remobnd))
            else:
                raise HKXCutsceneImportError("Must import cutscene from a `remobnd` binder file.")

        importer = HKXCutsceneImporter(self, context, bl_armature, bl_armature.name)

        loaded_msbs = {}  # type: dict[str, MSB]

        for file_path, remobnd in remobnds_with_paths:

            # TODO: usual Darkroot DD exception yada yada (add GET_MAP method to `RemoBND`).
            msb_name = f"m{remobnd.map_area:02}_{remobnd.map_block:02}_00_00.msb"
            if msb_name not in loaded_msbs:
                msb_path = Path(file_path.parent, f"../map/MapStudio/{msb_name}")
                if not msb_path.exists():
                    raise HKXCutsceneImportError(f"MSB file '{msb_path}' does not exist. Cannot check cutscene parts.")
                loaded_msbs[msb_name] = MSB.from_path(msb_path)

            self.info(f"Importing MSB for HKX cutscene: {remobnd.cutscene_name}")
            remobnd.load_remo_parts(loaded_msbs[msb_name])

            self.info(f"Importing HKX cutscene: {remobnd.cutscene_name}")

            # TODO: Hack right now. Using selected armature -- a single character in the cutscene -- to check bone
            #  names. Eventually, search for all used part instance/model names.
            part_name = bl_armature.name
            if part_name not in remobnd.remo_parts:
                raise HKXCutsceneImportError(f"RemoBND file '{file_path}' does not contain part '{part_name}'.")
            remo_part = remobnd.remo_parts[part_name]
            # TODO: Currently checking first cut for bone names. Eventually, check all cuts.
            first_cut_transforms = list(remo_part.cut_arma_transforms.values())[0]
            track_bone_names = list(first_cut_transforms.keys())

            bl_bone_names = [b.name for b in bl_armature.data.bones]
            for bone_name in track_bone_names:
                if bone_name != "master" and bone_name not in bl_bone_names:
                    raise ValueError(
                        f"Cutscene bone name '{bone_name}' is missing from selected Blender Armature "
                        f"({bl_armature.name})."
                    )

            # TODO: again, just applying to selected armature for now
            all_cut_transforms = {}
            for cut in remobnd.cuts:
                if cut.name in remo_part.cut_arma_transforms:
                    # Model is present in this cut. Use real transforms.
                    for bone_name, transforms in remo_part.cut_arma_transforms[cut.name].items():
                        all_cut_transforms.setdefault(bone_name, []).extend(transforms)
                else:
                    # Model is absent in this cut. Use default position.
                    # TODO: Using identity for now.
                    frame_count = len(cut.sibcam.camera_animation)
                    default_transform = TRSTransform.identity()
                    for bone_name in ["master"] + track_bone_names:
                        all_cut_transforms.setdefault(bone_name, []).extend([default_transform] * frame_count)

            # Add motion to camera.
            # TODO: quick hack name access. Should probably just create a new Camera.
            camera = bpy.data.objects["Camera"]
            camera_transforms = []
            # TODO: FoV. `camera.data.lens = 100 / math.tan(fov)` seems to work.
            #  Just need to figure out how the SIBCAM FoV keyframe indices work, since they seem too low at a glance.
            for cut in remobnd.cuts:
                camera_transforms += cut.sibcam.camera_animation
            try:
                camera_action = importer.create_camera_action(remobnd.cutscene_name, camera_transforms)
            except Exception as ex:
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import HKX cutscene camera data from {file_path.name}. Error: {ex}")
            else:
                try:
                    camera.animation_data_create()
                    camera.animation_data.action = camera_action
                except Exception as ex:
                    self.warning(
                        f"Camera animation was imported, but action could not be assigned to Camera. Error: {ex}"
                    )

            if self.camera_data_only:
                continue

            # Import single animation HKX.
            # TODO: Need to add 'null' keyframes (maybe use 'master' position) for cuts from which each character (right
            #  now, just the selected armature) is absent.
            try:
                action = importer.create_blender_action(remobnd.cutscene_name, all_cut_transforms)
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


class HKXCutsceneImporter:
    """Manages imports for a batch of HKX files imported simultaneously."""

    model_name: str

    def __init__(
        self,
        operator: ImportHKXCutscene,
        context,
        bl_armature,
        model_name: str
    ):
        self.operator = operator
        self.context = context

        self.bl_armature = bl_armature
        self.model_name = model_name

    @staticmethod
    def create_camera_action(
        cutscene_name: str,
        camera_transforms: list[CameraFrameTransform],
    ):
        action_name = f"Camera|{cutscene_name}"
        action = bpy.data.actions.new(action_name)
        fast = {"FAST"}

        try:
            camera_curves = {
                "loc_x": action.fcurves.new("location", index=0),
                "loc_y": action.fcurves.new("location", index=1),
                "loc_z": action.fcurves.new("location", index=2),
                "euler_x": action.fcurves.new("rotation_euler", index=0),
                "euler_y": action.fcurves.new("rotation_euler", index=1),
                "euler_z": action.fcurves.new("rotation_euler", index=2),
            }
            for frame_index, camera_transform in enumerate(camera_transforms):
                bl_translate = GAME_TO_BL_VECTOR(camera_transform.position)
                bl_euler = GAME_TO_BL_EULER(camera_transform.rotation)
                camera_curves["loc_x"].keyframe_points.insert(frame_index, bl_translate.x, options=fast)
                camera_curves["loc_y"].keyframe_points.insert(frame_index, bl_translate.y, options=fast)
                camera_curves["loc_z"].keyframe_points.insert(frame_index, bl_translate.z, options=fast)
                camera_curves["euler_x"].keyframe_points.insert(frame_index, bl_euler.x, options=fast)
                camera_curves["euler_y"].keyframe_points.insert(frame_index, bl_euler.y, options=fast)
                camera_curves["euler_z"].keyframe_points.insert(frame_index, bl_euler.z, options=fast)
            for fcurve in camera_curves.values():
                fcurve.update()

        except Exception:
            # Delete partially created action before raising.
            bpy.data.actions.remove(action)
            raise
        else:
            action.use_fake_user = True
            return action

    def create_blender_action(
        self,
        cutscene_name: str,
        all_cut_transforms: [dict[str, list[TRSTransform]]],
    ):
        """Read a HKX animation into a Blender action."""
        self.all_cut_transforms = all_cut_transforms

        action_name = f"{self.model_name}|{cutscene_name}"
        action = bpy.data.actions.new(action_name)

        try:
            self._create_fcurves(action, all_cut_transforms)
        except Exception:
            # Delete partially created action before raising.
            bpy.data.actions.remove(action)
            raise
        else:
            action.use_fake_user = True
            return action

    def _create_fcurves(
        self,
        action,
        all_cut_transforms: dict[str, list[TRSTransform]],
    ):
        """Convert a Havok HKX animation file to a Blender action (with fully-sampled keyframes).

        `bl_armature` is required to properly set the `matrix_basis` of each pose bone relative to the bone resting
        positions (set to the edit bones).

        `skeleton_hkx` is required to compute animation frame transforms in object coordinates, as the bone hierarchy
        can differ for HKX skeletons versus the FLVER skeleton in `bl_armature`.

        TODO: Does not support changes in Blender bone names (e.g. '<DUPE>' suffix).
        TODO: Time-scaling argument (with linear interpolation)?
        """
        fast = {"FAST"}

        # Create 'root motion' (master bone) FCurves.
        # master_curves = {
        #     "loc_x": action.fcurves.new("location", index=0),
        #     "loc_y": action.fcurves.new("location", index=1),
        #     "loc_z": action.fcurves.new("location", index=2),
        #     "rot_w": action.fcurves.new("rotation_quaternion", index=0),
        #     "rot_x": action.fcurves.new("rotation_quaternion", index=1),
        #     "rot_y": action.fcurves.new("rotation_quaternion", index=2),
        #     "rot_z": action.fcurves.new("rotation_quaternion", index=3),
        #     "scale_x": action.fcurves.new("scale", index=0),
        #     "scale_y": action.fcurves.new("scale", index=1),
        #     "scale_z": action.fcurves.new("scale", index=2),
        # }

        bone_curves = {}

        # Create bone FCurves (ten per bone).
        for bone_name in all_cut_transforms.keys():
            if bone_name == "master":
                continue
            data_path_prefix = f"pose.bones[\"{bone_name}\"]"
            location_data_path = f"{data_path_prefix}.location"
            rotation_data_path = f"{data_path_prefix}.rotation_quaternion"
            scale_data_path = f"{data_path_prefix}.scale"

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

        all_bone_arma_matrices = {
            bone_name: [trs_transform_to_bl_matrix(transform) for transform in bone_frame_transforms]
            for bone_name, bone_frame_transforms in all_cut_transforms.items()
        }
        bl_arma_inv_matrices = {}  # cached per `(bone_name, frame)` as needed

        for bone_name, bone_arma_matrices in all_bone_arma_matrices.items():

            for frame_index, bl_arma_matrix in enumerate(bone_arma_matrices):

                if bone_name == "master":
                    # `bl_arma_matrix` is just raw Blender world (game) space 'root' transform. No parenting.
                    # t, r, s = bl_arma_matrix.decompose()
                    # master_curves["loc_x"].keyframe_points.insert(frame_index, t.x, options=fast)
                    # master_curves["loc_y"].keyframe_points.insert(frame_index, t.y, options=fast)
                    # master_curves["loc_z"].keyframe_points.insert(frame_index, t.z, options=fast)
                    # master_curves["rot_w"].keyframe_points.insert(frame_index, r.w, options=fast)
                    # master_curves["rot_x"].keyframe_points.insert(frame_index, r.x, options=fast)
                    # master_curves["rot_y"].keyframe_points.insert(frame_index, r.y, options=fast)
                    # master_curves["rot_z"].keyframe_points.insert(frame_index, r.z, options=fast)
                    # master_curves["scale_x"].keyframe_points.insert(frame_index, s.x, options=fast)
                    # master_curves["scale_y"].keyframe_points.insert(frame_index, s.y, options=fast)
                    # master_curves["scale_z"].keyframe_points.insert(frame_index, s.z, options=fast)
                    continue

                bl_bone = self.bl_armature.data.bones[bone_name]
                if bl_bone.parent is not None and (bl_bone.parent.name, frame_index) not in bl_arma_inv_matrices:
                    # Cache parent's inverted armature matrix (may be needed by other sibling bones this frame).
                    parent_bl_arma_matrix = all_bone_arma_matrices[bl_bone.parent.name][frame_index]
                    bl_arma_inv_matrices[bl_bone.parent.name, frame_index] = parent_bl_arma_matrix.inverted()

                bl_basis_matrix = get_basis_matrix(
                    self.bl_armature, bone_name, bl_arma_matrix, bl_arma_inv_matrices, frame_index
                )
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

        # Update all F-curves. They do NOT cycle, unlike standard animations.
        # for fcurve in master_curves.values():
        #     fcurve.update()
        for fcurve in bone_curves.values():
            fcurve.update()


def trs_transform_to_bl_matrix(transform: TRSTransform) -> Matrix:
    """Convert a game `TRSTransform` to a Blender 4x4 `Matrix`."""
    bl_translate = GAME_TO_BL_VECTOR(transform.translation)
    bl_rotate = FL_TO_BL_QUAT(transform.rotation)
    bl_scale = GAME_TO_BL_VECTOR(transform.scale)
    return Matrix.LocRotScale(bl_translate, bl_rotate, bl_scale)


def get_armature_matrix(armature, bone_name, basis=None) -> Matrix:
    """Demonstrates how Blender calculates `pose_bone.matrix` (armature matrix) for `bone_name`.

    TODO: Likely needed at export to convert the curve keyframes (in basis space) back to armature space.
    """
    local = armature.data.bones[bone_name].matrix_local
    if basis is None:
        basis = armature.pose.bones[bone_name].matrix_basis

    parent = armature.pose.bones[bone_name].parent
    if parent is None:  # root bone is simple
        # armature = local @ basis
        return local @ basis
    else:
        # Apply relative transform of local (edit bone) from parent and then armature position of parent:
        #     armature = parent_armature @ (parent_local.inv @ local) @ basis
        #  -> basis = (parent_local.inv @ local)parent_local @ parent_armature.inv @ armature
        parent_local = armature.data.bones[parent.name].matrix_local
        return get_armature_matrix(armature, parent.name) @ parent_local.inverted() @ local @ basis


def get_basis_matrix(armature, bone_name, armature_matrix, armature_inv_matrices: dict, frame_index: int):
    """Inverse of above: get `pose_bone.matrix_basis` from `armature_matrix` by inverting Blender's process."""
    local = armature.data.bones[bone_name].matrix_local
    parent = armature.pose.bones[bone_name].parent

    if parent is None:
        return local.inverted() @ armature_matrix
    else:
        # TODO: Can't I just use `parent` directly? Why the indexing?
        parent_removed = armature_inv_matrices[parent.name, frame_index] @ armature_matrix
        return local.inverted() @ armature.data.bones[parent.name].matrix_local @ parent_removed
