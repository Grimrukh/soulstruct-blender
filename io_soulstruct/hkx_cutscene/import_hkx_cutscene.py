"""VERY early/experimental system for importing/exporting DSR cutscene animations into Blender."""
from __future__ import annotations

import math
import re
import traceback
import typing as tp
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper
from mathutils import Matrix

from soulstruct.containers import Binder
from soulstruct.base.animations.sibcam import CameraFrameTransform, FoVKeyframe
from soulstruct.base.models.flver import FLVER
from soulstruct.darksouls1r.maps import MapStudioDirectory
from soulstruct.darksouls1r.maps.parts import *

from soulstruct_havok.utilities.maths import TRSTransform
from soulstruct_havok.wrappers.hkx2015 import RemoBND

from io_soulstruct.utilities import *
from io_soulstruct.flver.import_flver import FLVERImporter
from io_soulstruct.flver.textures.utilities import collect_binder_tpfs, collect_map_tpfs
from .utilities import *


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

    game_directory: bpy.props.StringProperty(
        name="Game Directory",
        description="Directory of game files to load MSBs and missing cutscene parts from",
        default=get_last_game_directory(),
    )

    assign_to_armatures: bpy.props.BoolProperty(
        name="Assign to Armatures",
        description="Assign imported cutscene actions to part armatures immediately",
        default=True,
    )

    for_60_fps: bpy.props.BoolProperty(
        name="For 60 FPS",
        description="Scale animation keyframes to 60 FPS (from 30 FPS)",
        default=True,
    )

    camera_name: bpy.props.StringProperty(
        name="Camera Name",
        description="Name of cutscene camera object to create and animate",
        default="{CutsceneName} Camera",
    )

    camera_data_only: bpy.props.BoolProperty(
        name="Camera Data Only",
        description="Only load camera animation data",
        default=False,
    )

    load_missing_parts: bpy.props.BoolProperty(
        name="Load Missing Parts",
        description="Try to load missing cutscene parts (map pieces, objects, characters) from game files",
        default=True,
    )

    png_cache_path: bpy.props.StringProperty(
        name="Cached PNG path",
        description="Directory to use for reading/writing cached texture PNGs",
        default="D:\\blender_png_cache",
    )

    read_from_png_cache: bpy.props.BoolProperty(
        name="Read from PNG Cache",
        description="Read cached PNGs (instead of DDS files) from the above directory if available",
        default=True,
    )

    write_to_png_cache: bpy.props.BoolProperty(
        name="Write to PNG Cache",
        description="Write PNGs of any loaded textures (DDS files) to the above directory for future use",
        default=True,
    )

    enable_alpha_hashed: bpy.props.BoolProperty(
        name="Enable Alpha Hashed",
        description="Enable material Alpha Hashed (rather than Opaque) for single-texture FLVER materials",
        default=True,
    )

    def execute(self, context):

        remobnd_path = Path(self.filepath)

        if REMOBND_RE.match(remobnd_path.name):
            try:
                remobnd = RemoBND.from_path(remobnd_path)
            except Exception as ex:
                raise HKXCutsceneImportError(f"Could not parse RemoBND file '{remobnd_path}': {ex}")
        else:
            raise HKXCutsceneImportError("Must import cutscene from a `remobnd` binder file.")

        importer = HKXCutsceneImporter(self, context, self.for_60_fps)

        try:
            self.create_camera(context, remobnd, importer)
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            return self.error(f"Cannot import HKX cutscene camera data from {remobnd_path.name}. Error: {ex}")

        if self.camera_data_only:
            self.info("Imported HKX cutscene camera data.")
            return {"FINISHED"}

        loaded_map_studio_directories = {}  # type: dict[Path, MapStudioDirectory]

        if not self.game_directory:
            # Assume RemoBND is in the appropriate game `remo` folder.
            game_directory = remobnd_path.parent.parent
        else:
            game_directory = Path(self.game_directory)

        map_studio_path = Path(game_directory, "map/MapStudio")
        map_studio_directory = loaded_map_studio_directories.setdefault(
            map_studio_path, MapStudioDirectory.from_path(map_studio_path)
        )

        self.info(f"Importing MSBs for HKX cutscene: {remobnd.cutscene_name}")
        remobnd.load_remo_parts(map_studio_directory)

        self.info(f"Importing HKX cutscene: {remobnd.cutscene_name}")

        part_armatures = {}  # type: dict[str, tp.Any]
        flvers_to_import = {}  # type: dict[str, FLVER]
        attached_texture_sources = {}  # from multi-texture TPFs directly linked to FLVER
        loose_tpf_sources = {}  # one-texture TPFs that we only read if needed by FLVER

        for part_name, remo_part in remobnd.remo_parts.items():
            if remo_part.part is None:
                continue  # TODO: handle Player and dummies
            # Find `part_name` Blender armature.
            for obj in bpy.data.objects:
                if obj.type == "ARMATURE" and obj.name == part_name:
                    part_armatures[part_name] = obj
                    break
            else:
                if not self.load_missing_parts:
                    continue
                # Try to load given part from game files.
                if isinstance(remo_part.part, MSBMapPiece):
                    # Map piece FLVERs are always in map version `mAA_BB_CC_00`.
                    area, block = remo_part.map_area_block
                    map_path = game_directory / f"map/m{area:02d}_{block:02d}_00_00"
                    flver = FLVER.from_path(map_path / f"{remo_part.part.model.name}A{area:02d}.flver.dcx")
                    loose_tpf_sources |= collect_map_tpfs(map_path)
                elif isinstance(remo_part.part, MSBCharacter):
                    chrbnd_path = game_directory / f"chr/{remo_part.part.model.name}.chrbnd.dcx"
                    if not chrbnd_path.is_file():
                        self.warning(f"Could not find CHRBND to import for cutscene: {chrbnd_path}")
                        continue
                    chrbnd = Binder.from_path(chrbnd_path)
                    attached_texture_sources |= collect_binder_tpfs(chrbnd, chrbnd_path)
                    flver = chrbnd.find_entry_matching_name(r".*\.flver$").to_binary_file(FLVER)
                elif isinstance(remo_part.part, MSBObject):
                    objbnd_path = game_directory / f"obj/{remo_part.part.model.name}.objbnd.dcx"
                    if not objbnd_path.is_file():
                        self.warning(f"Could not find CHRBND to import for cutscene: {objbnd_path}")
                        continue
                    objbnd = Binder.from_path(objbnd_path)
                    attached_texture_sources |= collect_binder_tpfs(objbnd, objbnd_path)
                    flver = objbnd.find_entry_matching_name(r".*\.flver$").to_binary_file(FLVER)
                else:
                    self.warning(
                        f"Cannot load FLVER model for unknown part type: {type(remo_part.part).__name__}"
                    )
                    continue
                flvers_to_import[part_name] = flver

        # Load FLVERs.
        if flvers_to_import:
            flver_importer = FLVERImporter(
                self,
                context,
                attached_texture_sources,
                loose_tpf_sources,
                png_cache_path=Path(self.png_cache_path),
                read_from_png_cache=self.read_from_png_cache,
                write_to_png_cache=self.write_to_png_cache,
                enable_alpha_hashed=self.enable_alpha_hashed,
            )
            for part_name, flver in flvers_to_import.items():
                msb_part = remobnd.remo_parts[part_name]
                if isinstance(msb_part, MSBMapPiece):
                    transform = Transform.from_msb_part(msb_part)
                else:
                    # Even static objects are 'placed' in cutscenes by animating their root bone.
                    transform = None
                self.info(f"Importing FLVER for '{part_name}'...")
                # TODO: Catch and ignore errors?
                part_armature = flver_importer.import_flver(
                    flver,
                    name=part_name,  # exact match to cutscene part name
                    transform=transform,  # set for map pieces
                )
                part_armatures[part_name] = part_armature

        for part_name, remo_part in remobnd.remo_parts.items():
            if part_name not in part_armatures:
                continue  # part not loaded - omitted from cutscene
            part_armature = part_armatures[part_name]

            # Get bone names from first cut that includes this part.
            first_cut_transforms = list(remo_part.cut_arma_transforms.values())[0]
            track_bone_names = list(first_cut_transforms.keys())

            bl_bone_names = [b.name for b in part_armature.data.bones]
            for bone_name in track_bone_names:
                # TODO: is the 'master' check here necessary?
                if bone_name != "master" and bone_name not in bl_bone_names:
                    raise ValueError(
                        f"Cutscene bone name '{bone_name}' is missing from part armature '{part_armature.name}'."
                    )

            # Maps bone names to lists (cuts) of `TRSTransform` lists, in armature space.
            # Separate cuts are maintained so that we can disable interpolation between them as keyframes are added.
            all_cut_transforms = {}  # type: dict[str, list[list[TRSTransform]]]
            for cut in remobnd.cuts:
                if cut.name in remo_part.cut_arma_transforms:
                    # Model is present in this cut. Use real transforms.
                    for bone_name, transforms in remo_part.cut_arma_transforms[cut.name].items():
                        all_cut_transforms.setdefault(bone_name, []).append(transforms)
                else:
                    # Model is absent in this cut. Use default position.
                    # TODO: Using identity for now. Probably want to keep last known transform in previous cut?
                    frame_count = len(cut.sibcam.camera_animation)
                    default_transform = TRSTransform.identity()
                    for bone_name in ["master"] + track_bone_names:
                        all_cut_transforms.setdefault(bone_name, []).append([default_transform] * frame_count)

            # Create action for this part.
            try:
                action = importer.create_blender_action(
                    remobnd.cutscene_name, part_armature, all_cut_transforms
                )
            except Exception as ex:
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import HKX animation: {remobnd_path.name}. Error: {ex}")

            if self.assign_to_armatures:
                try:
                    part_armature.animation_data_create()
                    part_armature.animation_data.action = action
                except Exception as ex:
                    self.warning(
                        f"Animation was imported, but action could not be assigned to Armature. Error: {ex}"
                    )

        return {"FINISHED"}

    def create_camera(self, context, remobnd: RemoBND, importer: HKXCutsceneImporter) -> bpy.types.Camera:
        # Create a new Blender camera.
        camera_name = self.camera_name.format(CutsceneName=remobnd.cutscene_name)
        camera_data = bpy.data.cameras.new(self.camera_name.format(CutsceneName=remobnd.cutscene_name) + " Data")
        camera_obj = bpy.data.objects.new(camera_name, camera_data)
        context.scene.collection.objects.link(camera_obj)  # add to scene's object collection

        # Add motion to camera.
        camera_transforms = [
            cut.sibcam.camera_animation for cut in remobnd.cuts
        ]  # type: list[list[CameraFrameTransform]]
        camera_fov_keyframes = [
            cut.sibcam.fov_keyframes for cut in remobnd.cuts
        ]  # type: list[list[FoVKeyframe]]

        camera_obj_action, camera_data_action = importer.create_camera_actions(
            remobnd.cutscene_name, camera_transforms, camera_fov_keyframes
        )

        # New camera always has action assigned.
        try:
            camera_obj.animation_data_create()
            camera_obj.animation_data.action = camera_obj_action
            camera_data.animation_data_create()
            camera_data.animation_data.action = camera_data_action
        except Exception as ex:
            self.warning(
                f"Camera animation was imported, but action could not be assigned to Camera. Error: {ex}"
            )

        return camera_obj


class HKXCutsceneImporter:
    """Manages imports for a batch of HKX files imported simultaneously."""

    FAST = {"FAST"}

    for_60_fps: bool

    def __init__(
        self,
        operator: ImportHKXCutscene,
        context,
        for_60_fps: bool,
    ):
        self.operator = operator
        self.context = context
        self.for_60_fps = for_60_fps

    def create_camera_actions(
        self,
        cutscene_name: str,
        camera_transforms: list[list[CameraFrameTransform]],
        camera_fov_keyframes: list[list[FoVKeyframe]],
    ):
        """Creates two new Blender action for a cutscene camera: one for the object (transform) and one for its data
        (focal length)."""
        # TODO: Pass in lists of cuts, not all transforms at once, to set last frame of each cut to CONSTANT.
        obj_action_name = f"{cutscene_name}[Camera]"
        obj_action = bpy.data.actions.new(obj_action_name)
        data_action_name = f"{cutscene_name}[CameraData]"
        data_action = bpy.data.actions.new(data_action_name)
        fast = {"FAST"}

        try:
            obj_curves = {
                "loc_x": obj_action.fcurves.new("location", index=0),
                "loc_y": obj_action.fcurves.new("location", index=1),
                "loc_z": obj_action.fcurves.new("location", index=2),
                "euler_x": obj_action.fcurves.new("rotation_euler", index=0),
                "euler_y": obj_action.fcurves.new("rotation_euler", index=1),
                "euler_z": obj_action.fcurves.new("rotation_euler", index=2),
            }
            data_curves = {
                "lens": data_action.fcurves.new("lens"),
            }

            # NOT reset across cuts.
            frame_index = 0

            for cut_camera_transforms in camera_transforms:

                for cut_frame_index, camera_transform in enumerate(cut_camera_transforms):
                    frame_index += 1
                    bl_frame_index = frame_index * 2 if self.for_60_fps else frame_index
                    bl_translate = GAME_TO_BL_VECTOR(camera_transform.position)
                    bl_euler = GAME_TO_BL_EULER(camera_transform.rotation)
                    new_keyframes = [
                        obj_curves["loc_x"].keyframe_points.insert(bl_frame_index, bl_translate.x, options=fast),
                        obj_curves["loc_y"].keyframe_points.insert(bl_frame_index, bl_translate.y, options=fast),
                        obj_curves["loc_z"].keyframe_points.insert(bl_frame_index, bl_translate.z, options=fast),
                        obj_curves["euler_x"].keyframe_points.insert(bl_frame_index, bl_euler.x, options=fast),
                        obj_curves["euler_y"].keyframe_points.insert(bl_frame_index, bl_euler.y, options=fast),
                        obj_curves["euler_z"].keyframe_points.insert(bl_frame_index, bl_euler.z, options=fast),
                    ]
                    for keyframe in new_keyframes:
                        if cut_frame_index == len(cut_camera_transforms) - 1:
                            keyframe.interpolation = "CONSTANT"
                        else:
                            keyframe.interpolation = "LINEAR"  # TODO: I assume this is fine for 30 -> 60 FPS.

            cut_first_frame_index = 0

            for cut_fov_keyframes in camera_fov_keyframes:
                # TODO: Conversion seems... ALMOST correct.
                for fov_keyframe in cut_fov_keyframes:
                    focal_length = 100 / math.tan(fov_keyframe.fov)
                    frame_index = cut_first_frame_index + fov_keyframe.frame_index
                    bl_frame_index = frame_index * 2 if self.for_60_fps else frame_index
                    keyframe = data_curves["lens"].keyframe_points.insert(bl_frame_index, focal_length, options=fast)
                    if fov_keyframe.frame_index == len(cut_fov_keyframes) - 1:
                        keyframe.interpolation = "CONSTANT"  # probably rare/never for sparse FoV keyframes
                    else:
                        keyframe.interpolation = "LINEAR"
                cut_first_frame_index += len(cut_fov_keyframes)

            for fcurve in obj_curves.values():
                fcurve.update()
            for fcurve in data_curves.values():
                fcurve.update()

        except Exception:
            # Delete partially created action before raising.
            bpy.data.actions.remove(obj_action)
            bpy.data.actions.remove(data_action)
            raise
        else:
            obj_action.use_fake_user = True
            data_action.use_fake_user = True
            return obj_action, data_action

    def create_blender_action(
        self,
        cutscene_name: str,
        part_armature,
        all_cut_transforms: [dict[str, list[list[TRSTransform]]]],
    ):
        """Read a HKX animation into a Blender action."""
        action_name = f"{cutscene_name}[{part_armature.name}]"
        action = bpy.data.actions.new(action_name)

        try:
            self._create_fcurves(part_armature, action, all_cut_transforms)
        except Exception:
            # Delete partially created action before raising.
            bpy.data.actions.remove(action)
            raise
        else:
            action.use_fake_user = True  # prevent Blender from deleting Action if unassigned
            return action

    def _create_fcurves(
        self,
        part_armature,
        action,
        all_cut_transforms: dict[str, list[list[TRSTransform]]],
    ):
        """Convert a Havok HKX animation file to a Blender action (with fully-sampled keyframes).

        `bl_armature` is required to properly set the `matrix_basis` of each pose bone relative to the bone resting
        positions (set to the edit bones).

        `skeleton_hkx` is required to compute animation frame transforms in object coordinates, as the bone hierarchy
        can differ for HKX skeletons versus the FLVER skeleton in `bl_armature`.

        TODO: Does not support changes in Blender bone names (e.g. '<DUPE>' suffix).
        """

        bone_curves = {}

        # Create bone FCurves (ten per bone).
        for bone_name in all_cut_transforms.keys():
            if bone_name == "master":
                continue
            data_prefix = f"pose.bones[\"{bone_name}\"]"

            for i, c in enumerate("xyz"):
                bone_curves[bone_name, f"loc_{c}"] = action.fcurves.new(f"{data_prefix}.location", index=i)
            for i, c in enumerate("wxyz"):
                bone_curves[bone_name, f"rot_{c}"] = action.fcurves.new(f"{data_prefix}.rotation_quaternion", index=i)
            for i, c in enumerate("xyz"):
                bone_curves[bone_name, f"scale_{c}"] = action.fcurves.new(f"{data_prefix}.scale", index=i)

        all_bone_arma_matrices = {
            bone_name: [
                [trs_transform_to_bl_matrix(transform) for transform in cut_transforms]
                for cut_transforms in bone_frame_transforms
            ]
            for bone_name, bone_frame_transforms in all_cut_transforms.items()
        }
        bl_arma_inv_matrices = {}  # cached per `(bone_name, frame)` as needed

        def add_keyframe(bone: str, key: str, index: int, v: float):
            return bone_curves[bone, key].keyframe_points.insert(index, v, options=self.FAST)

        for bone_name, bone_arma_matrices in all_bone_arma_matrices.items():

            # NOT reset for each cut.
            frame_index = 0

            for cut_bl_arma_matrices in bone_arma_matrices:
                for cut_frame_index, bl_arma_matrix in enumerate(cut_bl_arma_matrices):

                    frame_index += 1
                    bl_i = frame_index * 2 if self.for_60_fps else frame_index

                    if bone_name == "master":
                        # TODO: Cutscenes do not seem to animate 'master' for characters? Not sure if I need to skip it
                        #  like this, though - might be harmless.
                        continue

                    bl_bone = part_armature.data.bones[bone_name]
                    if bl_bone.parent is not None and (bl_bone.parent.name, frame_index) not in bl_arma_inv_matrices:
                        # Cache parent's inverted armature matrix (may be needed by other sibling bones this frame).
                        parent_bl_arma_matrix = all_bone_arma_matrices[bl_bone.parent.name][frame_index]
                        bl_arma_inv_matrices[bl_bone.parent.name, frame_index] = parent_bl_arma_matrix.inverted()

                    bl_basis_matrix = get_basis_matrix(
                        part_armature, bone_name, bl_arma_matrix, bl_arma_inv_matrices, frame_index
                    )
                    t, r, s = bl_basis_matrix.decompose()

                    new_keyframes = [
                        add_keyframe(bone_name, "loc_x", bl_i, t.x),
                        add_keyframe(bone_name, "loc_y", bl_i, t.y),
                        add_keyframe(bone_name, "loc_z", bl_i, t.z),
                        add_keyframe(bone_name, "rot_w", bl_i, r.w),
                        add_keyframe(bone_name, "rot_x", bl_i, r.x),
                        add_keyframe(bone_name, "rot_y", bl_i, r.y),
                        add_keyframe(bone_name, "rot_z", bl_i, r.z),
                        add_keyframe(bone_name, "scale_x", bl_i, s.x),
                        add_keyframe(bone_name, "scale_y", bl_i, s.y),
                        add_keyframe(bone_name, "scale_z", bl_i, s.z),
                    ]

                    # Interpolation is LINEAR by default, or CONSTANT for the last keyframe.
                    for keyframe in new_keyframes:
                        if cut_frame_index == len(cut_bl_arma_matrices) - 1:
                            keyframe.interpolation = "CONSTANT"
                        else:
                            keyframe.interpolation = "LINEAR"  # TODO: I assume this is fine for 30 -> 60 FPS.

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
