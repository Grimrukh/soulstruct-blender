"""VERY early/experimental system for importing/exporting DSR cutscene animations into Blender."""
from __future__ import annotations

import math
import re
import traceback
import typing as tp
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector, Quaternion as BlenderQuaternion

from soulstruct.containers import Binder
from soulstruct.base.animations.sibcam import CameraFrameTransform, FoVKeyframe
from soulstruct.base.models.flver import FLVER
from soulstruct.darksouls1r.maps import MapStudioDirectory
from soulstruct.darksouls1r.maps.parts import *

from soulstruct_havok.utilities.maths import TRSTransform
from soulstruct_havok.wrappers.hkx2015 import RemoBND

from io_soulstruct.utilities.conversion import Transform, GAME_TO_BL_VECTOR, GAME_TO_BL_EULER
from io_soulstruct.utilities.operators import LoggingOperator
from io_soulstruct.flver.import_flver import FLVERBatchImporter
from io_soulstruct.flver.textures.import_textures import TextureImportManager
from io_soulstruct.havok.utilities import GAME_TRS_TO_BL_MATRIX, get_basis_matrix
from .utilities import HKXCutsceneImportError


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

    to_60_fps: bpy.props.BoolProperty(
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

    use_mtd_binder: bpy.props.BoolProperty(
        name="Use MTD Binder",
        description="Try to find MTD shaders in game 'mtd' folder to improve Blender shader accuracy",
        default=True,
    )

    material_blend_mode: bpy.props.EnumProperty(
        name="Alpha Blend Mode",
        description="Alpha mode to use for new single-texture FLVER materials",
        items=[
            ('OPAQUE', "Opaque", "Opaque Blend Mode"),
            ('CLIP', "Clip", "Clip Blend Mode"),
            ('HASHED', "Hashed", "Hashed Blend Mode"),
            ('BLEND', "Blend", "Sorted Blend Mode"),
        ],
        default="HASHED",
    )

    base_edit_bone_length: bpy.props.FloatProperty(
        name="Base Edit Bone Length",
        description="Length of edit bones corresponding to bone scale 1",
        default=0.2,
        min=0.01,
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

        importer = HKXCutsceneImporter(self, context, self.to_60_fps)

        try:
            self.create_camera(context, remobnd, importer)
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            return self.error(f"Cannot import HKX cutscene camera data from {remobnd_path.name}. Error: {ex}")

        if self.camera_data_only:
            self.info("Imported HKX cutscene camera data.")
            return {"FINISHED"}

        loaded_map_studio_directories = {}  # type: dict[Path, MapStudioDirectory]
        settings = self.settings(context)

        # If import directory is not set, we assume the RemoBND is in the usual game `remo` folder.
        game_directory = settings.game_import_directory or remobnd_path.parent.parent

        map_studio_path = Path(game_directory, "map/MapStudio")
        map_studio_directory = loaded_map_studio_directories.setdefault(
            map_studio_path, MapStudioDirectory.from_path(map_studio_path)
        )

        self.info(f"Importing MSBs for HKX cutscene: {remobnd.cutscene_name}")
        remobnd.load_remo_parts(map_studio_directory)

        self.info(f"Importing HKX cutscene: {remobnd.cutscene_name}")

        part_armatures = {}  # type: dict[str, tp.Any]
        flvers_to_import = {}  # type: dict[str, FLVER]
        texture_manager = TextureImportManager()

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
                    flver_path = map_path / f"{remo_part.part.model.name}A{area:02d}.flver.dcx"
                    flver = FLVER.from_path(flver_path)
                    texture_manager.find_flver_textures(flver_path)
                elif isinstance(remo_part.part, MSBCharacter):
                    chrbnd_path = game_directory / f"chr/{remo_part.part.model.name}.chrbnd.dcx"
                    if not chrbnd_path.is_file():
                        self.warning(f"Could not find CHRBND to import for cutscene: {chrbnd_path}")
                        continue
                    chrbnd = Binder.from_path(chrbnd_path)
                    flver = chrbnd.find_entry_matching_name(r".*\.flver$").to_binary_file(FLVER)
                    texture_manager.find_flver_textures(chrbnd_path, chrbnd)
                elif isinstance(remo_part.part, MSBObject):
                    objbnd_path = game_directory / f"obj/{remo_part.part.model.name}.objbnd.dcx"
                    if not objbnd_path.is_file():
                        self.warning(f"Could not find CHRBND to import for cutscene: {objbnd_path}")
                        continue
                    objbnd = Binder.from_path(objbnd_path)
                    flver = objbnd.find_entry_matching_name(r".*\.flver$").to_binary_file(FLVER)
                    texture_manager.find_flver_textures(objbnd_path, objbnd)
                else:
                    self.warning(
                        f"Cannot load FLVER model for unknown part type: {type(remo_part.part).__name__}"
                    )
                    continue
                flvers_to_import[part_name] = flver

        # Load FLVERs.
        if flvers_to_import:

            flver_importer = FLVERBatchImporter(
                self,
                context,
                settings,
                texture_manager=texture_manager,
            )

            for part_name, flver in flvers_to_import.items():
                msb_part = remobnd.remo_parts[part_name]
                self.info(f"Importing FLVER for '{part_name}'...")
                # TODO: Catch and ignore errors?
                part_armature, part_mesh = flver_importer.import_flver(
                    flver,
                    name=part_name,  # exact match to cutscene part name
                )
                part_armatures[part_name] = part_armature
                if isinstance(msb_part, MSBMapPiece):
                    transform = Transform.from_msb_part(msb_part)
                    part_armature.location = transform.bl_translate
                    part_armature.rotation_euler = transform.bl_rotate
                    part_armature.scale = transform.bl_scale
                # NOTE: Even static objects are 'placed' in cutscenes by animating their root bone.

        for part_name, remo_part in remobnd.remo_parts.items():
            if part_name not in part_armatures:
                continue  # part not loaded - omitted from cutscene
            part_armature = part_armatures[part_name]

            # Get bone names from first cut that includes this part.
            first_cut_frames = next(iter(remo_part.cut_arma_frames.values()))
            track_bone_names = list(first_cut_frames[0].keys())

            bl_bone_names = [b.name for b in part_armature.data.bones]
            for bone_name in track_bone_names:
                # TODO: is the 'master' check here necessary?
                if bone_name != "master" and bone_name not in bl_bone_names:
                    print(track_bone_names)
                    raise ValueError(
                        f"Cutscene bone name '{bone_name}' is missing from part armature '{part_armature.name}'."
                    )

            # Each frame maps bone names to a `TRSTransform` in armature space. Cuts are just lists of frames.
            # Separate cuts are maintained so that we can disable interpolation between them as keyframes are added.
            all_cut_frames = []  # type: list[list[dict[str, TRSTransform]]]
            for cut in remobnd.cuts:

                if cut.name in remo_part.cut_arma_frames:
                    # Model is present in this cut. Use real transforms.
                    all_cut_frames.append(remo_part.cut_arma_frames[cut.name])
                else:
                    # Model is absent in this cut. Use default position.
                    # TODO: Using identity for now. Probably want to keep last known transform in previous cut?
                    default_transform = TRSTransform.identity()
                    default_frame = {
                        bone_name: default_transform
                        for bone_name in track_bone_names  # TODO: what about 'master' or other root bone name?
                    }
                    frame_count = len(cut.sibcam.camera_animation)
                    all_cut_frames.append([default_frame] * frame_count)

            # Create action for this part.
            # TODO: Bug: actions of different parts (and camera) are OUT OF SYNC.
            #  Not sure yet how this could be happening. Should double-check number of frames for each part in each
            #  cut?
            try:
                importer.create_part_action(
                    remobnd.cutscene_name, part_armature, all_cut_frames
                )
            except Exception as ex:
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import HKX animation: {remobnd_path.name}. Error: {ex}")

        return {"FINISHED"}

    def create_camera(self, context, remobnd: RemoBND, importer: HKXCutsceneImporter) -> bpy.types.Object:
        # Create a new Blender camera.
        camera_name = self.camera_name.format(CutsceneName=remobnd.cutscene_name)
        camera_data = bpy.data.cameras.new(self.camera_name.format(CutsceneName=remobnd.cutscene_name) + " Data")
        camera_obj = bpy.data.objects.new(camera_name, camera_data)  # type: bpy.types.Object
        context.scene.collection.objects.link(camera_obj)  # add to scene's object collection

        # Add motion to camera.
        camera_transforms = [
            cut.sibcam.camera_animation for cut in remobnd.cuts
        ]  # type: list[list[CameraFrameTransform]]
        camera_fov_keyframes = [
            cut.sibcam.fov_keyframes for cut in remobnd.cuts
        ]  # type: list[list[FoVKeyframe]]

        camera_obj_action, camera_data_action = importer.create_camera_actions(
            camera_obj, remobnd.cutscene_name, camera_transforms, camera_fov_keyframes
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

    to_60_fps: bool

    def __init__(
        self,
        operator: ImportHKXCutscene,
        context,
        to_60_fps: bool,
    ):
        self.operator = operator
        self.context = context
        self.to_60_fps = to_60_fps

    def create_camera_actions(
        self,
        camera_obj: bpy.types.Object,
        cutscene_name: str,
        camera_transforms: list[list[CameraFrameTransform]],
        camera_fov_keyframes: list[list[FoVKeyframe]],
    ):
        """Creates two new actions: one for the camera object (transform) and one for its data (focal length)."""
        # noinspection PyTypeChecker
        camera_data = camera_obj.data  # type: bpy.types.Camera

        obj_action_name = f"{cutscene_name}[Camera]"
        obj_action = None
        data_action_name = f"{cutscene_name}[CameraData]"
        data_action = None

        original_location = camera_obj.location.copy()
        original_rotation = camera_obj.rotation_euler.copy()
        original_focal_length = camera_data.lens

        try:
            camera_obj.animation_data_create()
            camera_obj.animation_data.action = obj_action = bpy.data.actions.new(name=obj_action_name)
            camera_data.animation_data_create()
            camera_data.animation_data.action = data_action = bpy.data.actions.new(name=data_action_name)
            self._add_camera_keyframes(camera_obj, camera_transforms, camera_fov_keyframes)
        except Exception:
            if obj_action:
                bpy.data.actions.remove(obj_action)
            if data_action:
                bpy.data.actions.remove(data_action)
            # Reset camera to original state. (NOTE: Redundant since camera is always created by cutscene!)
            camera_obj.location = original_location
            camera_obj.rotation_euler = original_rotation
            camera_data.lens = original_focal_length
            raise

        # Ensure actions are not deleted when not in use.
        obj_action.use_fake_user = True
        data_action.use_fake_user = True
        # Update all F-curves (they do NOT cycle).
        for fcurve in obj_action.fcurves:
            fcurve.update()
        for fcurve in data_action.fcurves:
            fcurve.update()

        # Update Blender timeline start/stop times.
        bpy.context.scene.frame_start = int(obj_action.frame_range[0])
        bpy.context.scene.frame_end = int(obj_action.frame_range[1])
        bpy.context.scene.frame_set(bpy.context.scene.frame_start)
        return obj_action, data_action

    def _add_camera_keyframes(
        self,
        camera_obj: bpy.types.Object,
        camera_transforms: list[list[CameraFrameTransform]],
        camera_fov_keyframes: list[list[FoVKeyframe]],
    ):
        """Add keyframes for camera object and data (focal length)."""
        # noinspection PyTypeChecker
        camera_data = camera_obj.data  # type: bpy.types.Camera

        final_frame_indices = set()

        # TODO: Fix any camera rotation discontinuities first?

        # NOT reset across cuts.
        cutscene_frame_index = 0

        for cut_camera_transforms in camera_transforms:

            for cut_frame_index, camera_transform in enumerate(cut_camera_transforms):
                cutscene_frame_index += 1
                bl_frame_index = cutscene_frame_index * 2 if self.to_60_fps else cutscene_frame_index
                bl_translate = GAME_TO_BL_VECTOR(camera_transform.position)
                bl_euler = GAME_TO_BL_EULER(camera_transform.rotation)
                camera_obj.location = bl_translate
                camera_obj.rotation_euler = bl_euler
                camera_obj.keyframe_insert(data_path="location", frame=bl_frame_index)
                camera_obj.keyframe_insert(data_path="rotation_euler", frame=bl_frame_index)
                if cut_frame_index == len(cut_camera_transforms) - 1:
                    final_frame_indices.add(bl_frame_index)

        cut_first_frame_index = 1  # starts at 1!

        for cut_fov_keyframes, cut_camera_transforms in zip(camera_fov_keyframes, camera_transforms):

            for keyframe_index, fov_keyframe in enumerate(cut_fov_keyframes):
                # TODO: Conversion seems... ALMOST correct.
                camera_data.lens = 100 / math.tan(fov_keyframe.fov)
                cutscene_frame_index = cut_first_frame_index + fov_keyframe.frame_index
                bl_frame_index = cutscene_frame_index * 2 if self.to_60_fps else cutscene_frame_index
                camera_data.keyframe_insert(data_path="lens", frame=bl_frame_index)

                if keyframe_index == len(cut_fov_keyframes) - 1:
                    # Do not interpolate between final cut FoV keyframe and first keyframe in next cut!
                    final_frame_indices.add(bl_frame_index)

            # TODO: This seems to randomly be off by 1 in either direction (first frame is too early or too late).
            #  I must be missing something with the alignment to camera position.
            cut_first_frame_index += len(cut_camera_transforms)

        # Make all keyframes in `cut_final_frame_indices` 'CONSTANT' interpolation.

        for action in (camera_obj.animation_data.action, camera_data.animation_data.action):
            for fcurve in action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    if keyframe.co.x in final_frame_indices:
                        keyframe.interpolation = "CONSTANT"

    def create_part_action(
        self,
        cutscene_name: str,
        part_armature: bpy.types.ArmatureObject,
        all_cut_arma_frames: list[list[dict[str, TRSTransform]]],
    ):
        """Import single animation HKX."""
        action_name = f"{cutscene_name}[{part_armature.name}]"
        action = None
        original_location = part_armature.location.copy()
        try:
            part_armature.animation_data_create()
            part_armature.animation_data.action = action = bpy.data.actions.new(name=action_name)
            print(f"# INFO: Adding keyframes to action {action_name}...")
            self._add_armature_keyframes(part_armature, all_cut_arma_frames)
        except Exception:
            if action:
                bpy.data.actions.remove(action)
            part_armature.location = original_location  # reset location (i.e. erase last root motion)
            # TODO: should reset last bone transforms (`matrix_basis`) as well
            raise

        # Ensure action is not deleted when not in use.
        action.use_fake_user = True
        # Update all F-curves and make them cycle.
        for fcurve in action.fcurves:
            fcurve.modifiers.new("CYCLES")  # default settings are fine
            fcurve.update()

    def _add_armature_keyframes(
        self,
        part_armature: bpy.types.ArmatureObject,
        all_cut_arma_frames: list[list[dict[str, TRSTransform]]],
    ):
        """Convert a Havok HKX animation file to a Blender action (with fully-sampled keyframes).

        The action to add keyframes to should already be the active action on `self.bl_armature`. This is required to
        use the `keyframe_insert()` method, which allows full-Vector and full-Quaternion keyframes to be inserted and
        have Blender properly interpolate (e.g. Quaternion slerp) between them, which it cannot do if we use FCurves and
        set the `keyframe_points` directly for each coordinate.

        We also use `self.bl_armature` to properly set the `matrix_basis` of each pose bone relative to the bone resting
        positions (set to the edit bones).

        `skeleton_hkx` is required to compute animation frame transforms in armature space, as the bone hierarchy can
        differ for HKX skeletons versus the FLVER skeleton in `bl_armature`.

        TODO: Does not support changes in Blender bone names (e.g. '<DUPE>' suffix).
        """

        # TODO: Overhaul a la HKX animation.

        # FIRST: Convert armature-space frame data to Blender `(location, rotation_quaternion, scale)` tuples.
        # Note that we decompose the basis matrices so that quaternion discontinuities are handled properly.
        all_basis_frames = []  # type: list[list[dict[str, tuple[Vector, BlenderQuaternion, Vector]]]]

        cut_final_frame_indices = set()  # type: set[int]

        for cut_arma_frames in all_cut_arma_frames:

            cut_basis_frames = []  # type: list[dict[str, tuple[Vector, BlenderQuaternion, Vector]]]
            last_frame_rotations = {}  # type: dict[str, BlenderQuaternion]

            for cut_frame_index, frame in enumerate(cut_arma_frames):

                bl_arma_matrices = {
                    bone_name: GAME_TRS_TO_BL_MATRIX(transform) for bone_name, transform in frame.items()
                }
                bl_arma_inv_matrices = {}  # cached for frame as needed

                basis_frame = {}

                for bone_name, bl_arma_matrix in bl_arma_matrices.items():

                    if bone_name == "master":
                        # TODO: Hack, because I don't know how to get the cutscene asset's root bone name reliably (as
                        #  the root in the cutscene HKX file is the name of the asset).
                        #  Never seems to be animated anyway and FLVER hierarchy (in DS1) doesn't use it.
                        continue

                    bl_edit_bone = part_armature.data.bones[bone_name]
                    if bl_edit_bone.parent is not None and bl_edit_bone.parent.name not in bl_arma_inv_matrices:
                        # Cache parent's inverted armature matrix (may be needed by other sibling bones this frame).
                        parent_name = bl_edit_bone.parent.name
                        bl_arma_inv_matrices[parent_name] = bl_arma_matrices[parent_name].inverted()

                    bl_basis_matrix = get_basis_matrix(
                        part_armature, bone_name, bl_arma_matrix, bl_arma_inv_matrices
                    )
                    t, r, s = bl_basis_matrix.decompose()

                    if bone_name in last_frame_rotations:
                        if last_frame_rotations[bone_name].dot(r) < 0:
                            r.negate()  # negate quaternion to avoid discontinuity (reverse direction of rotation)

                    basis_frame[bone_name] = (t, r, s)
                    last_frame_rotations[bone_name] = r

                cut_basis_frames.append(basis_frame)

            all_basis_frames.append(cut_basis_frames)

        # NOT reset across cuts.
        cutscene_frame_index = 0

        for cut_basis_frames in all_basis_frames:

            for cut_frame_index, basis_frame in enumerate(cut_basis_frames):

                cutscene_frame_index += 1

                # TODO: Make this a more general 'frame scaling' option, e.g. by having importer take input/output FPS.
                #  (Should be able to read/infer input FPS from HKX file, actually.)
                bl_frame_index = cutscene_frame_index * 2 if self.to_60_fps else cutscene_frame_index

                for bone_name, (t, r, s) in basis_frame.items():
                    bl_pose_bone = part_armature.pose.bones[bone_name]
                    bl_pose_bone.location = t
                    bl_pose_bone.rotation_quaternion = r
                    bl_pose_bone.scale = s

                    # Insert keyframes for location, rotation, scale.
                    bl_pose_bone.keyframe_insert(data_path="location", frame=bl_frame_index)
                    bl_pose_bone.keyframe_insert(data_path="rotation_quaternion", frame=bl_frame_index)
                    bl_pose_bone.keyframe_insert(data_path="scale", frame=bl_frame_index)

                if cut_frame_index == len(cut_basis_frames) - 1:
                    cut_final_frame_indices.add(bl_frame_index)

        # Make all keyframes in `cut_final_frame_indices` 'CONSTANT' interpolation.
        print(f"Final cut frames: {cut_final_frame_indices}")
        action = part_armature.animation_data.action
        for fcurve in action.fcurves:
            for keyframe in fcurve.keyframe_points:
                if keyframe.co.x in cut_final_frame_indices:
                    keyframe.interpolation = "CONSTANT"
