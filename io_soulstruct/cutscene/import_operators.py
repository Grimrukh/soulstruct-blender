"""VERY early/experimental system for importing/exporting DSR cutscene animations into Blender."""
from __future__ import annotations

import math
import re
import traceback
import typing as tp
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper
from io_soulstruct.animation.types import SoulstructAnimation
from io_soulstruct.exceptions import SoulstructTypeError, CutsceneImportError
from io_soulstruct.msb.darksouls1r import *
from io_soulstruct.utilities import *
from soulstruct.base.animations.sibcam import CameraFrameTransform, FoVKeyframe
from soulstruct.darksouls1r.maps import MapStudioDirectory
from soulstruct.darksouls1r.maps.parts import *
from soulstruct_havok.utilities.maths import TRSTransform
from soulstruct_havok.fromsoft.darksouls1r import RemoBND

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

    camera_name: bpy.props.StringProperty(
        name="Camera Name",
        description="Name of cutscene camera object to create and animate",
        default="{CutsceneName} Camera",
    )

    IGNORE_MASTER_BONE_NAME: tp.ClassVar[str] = "master"  # TODO: DS1

    @classmethod
    def poll(cls, context):
        # Only for DSR right now.
        return cls.settings(context).is_game("DARK_SOULS_DSR")

    def execute(self, context):

        remobnd_path = Path(self.filepath)
        import_settings = context.scene.cutscene_import_settings

        if REMOBND_RE.match(remobnd_path.name):
            try:
                remobnd = RemoBND.from_path(remobnd_path)
            except Exception as ex:
                raise CutsceneImportError(f"Could not parse RemoBND file '{remobnd_path}': {ex}")
        else:
            raise CutsceneImportError("Must import cutscene from a `remobnd` binder file.")

        try:
            self.create_camera(context, remobnd, import_settings.to_60_fps)
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            return self.error(f"Cannot import HKX cutscene camera data from {remobnd_path.name}. Error: {ex}")

        if import_settings.camera_data_only:
            self.info("Imported HKX cutscene camera data only.")
            return {"FINISHED"}

        settings = self.settings(context)

        # If import directory is not set, we assume the RemoBND is in the usual game `remo` folder.
        game_directory = settings.game_root_path or remobnd_path.parent.parent

        map_studio_path = Path(game_directory, "map/MapStudio")
        map_studio_directory = MapStudioDirectory.from_path(map_studio_path)

        self.info(f"Importing MSBs for HKX cutscene: {remobnd.cutscene_name}")
        remobnd.load_remo_parts(map_studio_directory)

        self.info(f"Importing HKX cutscene: {remobnd.cutscene_name}")

        bl_cutscene_parts = {}  # type: dict[str, BlenderMSBPart]

        for part_name, remo_part in remobnd.remo_parts.items():

            if remo_part.part is None:
                continue  # TODO: handle Player and dummies
            msb_part = remo_part.part

            if isinstance(msb_part, MSBMapPiece):
                bl_part_type = BlenderMSBMapPiece
            elif isinstance(msb_part, MSBCharacter):
                bl_part_type = BlenderMSBCharacter
            elif isinstance(msb_part, MSBObject):
                bl_part_type = BlenderMSBObject
            else:
                self.warning(
                    f"Cannot load FLVER model for unknown part type: {type(remo_part.part).__name__}"
                )
                continue

            area, block = remo_part.map_area_block
            map_stem = f"m{area:02d}_{block:02d}_00_00"
            part_collection = get_or_create_collection(
                context.scene.collection,
                f"{map_stem} Parts",
                f"{map_stem} {bl_part_type.PART_SUBTYPE.get_nice_name()} Parts",
            )

            try:
                bl_part = bl_part_type.find_in_data(part_name)  # type: BlenderMSBPart
            except SoulstructTypeError:
                try:
                    bl_part = BlenderMSBMapPiece.new_from_soulstruct_obj(
                        self, context, msb_part, part_name, part_collection, map_stem
                    )
                except Exception as ex:
                    traceback.print_exc()
                    self.error(f"Failed to import MSB {bl_part_type.PART_SUBTYPE} {msb_part.name}' for cutscene: {ex}")
                    continue
            bl_cutscene_parts[part_name] = bl_part

        for part_name, remo_part in remobnd.remo_parts.items():
            if isinstance(remo_part, MSBMapPiece):
                continue  # TODO: may not have an Armature. Surely none of them are actually animated...
            if part_name not in bl_cutscene_parts:
                continue  # part not loaded - omitted from cutscene

            bl_part = bl_cutscene_parts[part_name]  # type: BlenderMSBPart

            # We need to add an Armature to the Part, if it doesn't already have one.
            if not bl_part.armature:
                bl_part.duplicate_flver_model_armature(context)

            # Get bone names from first cut that includes this part.
            first_cut_frames = next(iter(remo_part.cut_arma_frames.values()))
            track_bone_names = list(first_cut_frames[0].keys())

            bl_bone_names = [b.name for b in bl_part.armature.data.bones]
            # Check that all cutscene part bone names are present in Blender Armature.
            # We ignore the FLVER 'master' bone, which does not appear in cutscene data (it's replaced by the
            # root of the amalgamated cutscene 'skeleton').
            for bone_name in track_bone_names:
                if bone_name == self.IGNORE_MASTER_BONE_NAME:
                    continue
                if bone_name not in bl_bone_names:
                    print(track_bone_names)
                    raise ValueError(
                        f"Cutscene bone name '{bone_name}' is missing from part armature '{bl_part.name}'."
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
                SoulstructAnimation.new_from_cutscene_cuts(
                    context,
                    action_name=f"{remobnd.cutscene_name}[{bl_part.export_name}]",
                    armature=bl_part.armature,
                    arma_cuts=all_cut_frames,
                    ignore_master_bone_name=self.IGNORE_MASTER_BONE_NAME,
                )
            except Exception as ex:
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import HKX animation: {remobnd_path.name}. Error: {ex}")

        return {"FINISHED"}

    def create_camera(
        self,
        context: bpy.types.Context,
        remobnd: RemoBND,
        to_60_fps: bool,
    ) -> bpy.types.CameraObject:
        """Create a new Blender camera object for the cutscene."""
        camera_name = self.camera_name.format(CutsceneName=remobnd.cutscene_name)
        camera_data = bpy.data.cameras.new(self.camera_name.format(CutsceneName=remobnd.cutscene_name))
        # noinspection PyTypeChecker
        camera = bpy.data.objects.new(camera_name, camera_data)  # type: bpy.types.CameraObject
        context.scene.collection.objects.link(camera)  # add to scene's object collection

        # Add motion to camera.
        camera_transforms = [
            cut.sibcam.camera_animation for cut in remobnd.cuts
        ]  # type: list[list[CameraFrameTransform]]
        camera_fov_keyframes = [
            cut.sibcam.fov_keyframes for cut in remobnd.cuts
        ]  # type: list[list[FoVKeyframe]]

        self.create_camera_actions(
            context,
            camera,
            cutscene_name=remobnd.cutscene_name,
            camera_transforms=camera_transforms,
            camera_fov_keyframes=camera_fov_keyframes,
            to_60_fps=to_60_fps,
        )

        return camera

    def create_camera_actions(
        self,
        context: bpy.types.Context,
        camera: bpy.types.CameraObject,
        cutscene_name: str,
        camera_transforms: list[list[CameraFrameTransform]],
        camera_fov_keyframes: list[list[FoVKeyframe]],
        to_60_fps: bool,
    ) -> tuple[bpy.types.Action, bpy.types.Action]:
        """Creates and returns two new actions
            - action on Camera object for location and rotation animation
            - action on Camera data for focal length animation
        """
        camera_data = camera.data

        obj_action_name = f"{cutscene_name}[Camera]"
        obj_action = None
        data_action_name = f"{cutscene_name}[CameraData]"
        data_action = None

        original_location = camera.location.copy()
        original_rotation = camera.rotation_euler.copy()
        original_focal_length = camera_data.lens

        try:
            camera.animation_data_create()
            camera.animation_data.action = obj_action = bpy.data.actions.new(name=obj_action_name)
            camera_data.animation_data_create()
            camera_data.animation_data.action = data_action = bpy.data.actions.new(name=data_action_name)
            self.add_camera_keyframes(camera, camera_transforms, camera_fov_keyframes, to_60_fps)
        except Exception:
            if obj_action:
                bpy.data.actions.remove(obj_action)
            if data_action:
                bpy.data.actions.remove(data_action)
            # Reset camera to original state. (NOTE: Redundant since camera is always created by cutscene!)
            camera.location = original_location
            camera.rotation_euler = original_rotation
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
        context.scene.frame_start = int(obj_action.frame_range[0])
        context.scene.frame_end = int(obj_action.frame_range[1])
        context.scene.frame_set(bpy.context.scene.frame_start)
        return obj_action, data_action

    @staticmethod
    def add_camera_keyframes(
        camera: bpy.types.CameraObject,
        camera_transforms: list[list[CameraFrameTransform]],
        camera_fov_keyframes: list[list[FoVKeyframe]],
        to_60_fps: bool,
    ):
        """Add keyframes for camera object and data (focal length)."""
        camera_data = camera.data  # type: bpy.types.Camera

        final_frame_indices = set()

        # TODO: Fix any camera rotation discontinuities first?

        # NOT reset across cuts.
        cutscene_frame_index = 0

        for cut_camera_transforms in camera_transforms:

            for cut_frame_index, camera_transform in enumerate(cut_camera_transforms):
                cutscene_frame_index += 1
                bl_frame_index = cutscene_frame_index * 2 if to_60_fps else cutscene_frame_index
                bl_translate = GAME_TO_BL_VECTOR(camera_transform.position)
                bl_euler = GAME_TO_BL_EULER(camera_transform.rotation)
                camera.location = bl_translate
                camera.rotation_euler = bl_euler
                camera.keyframe_insert(data_path="location", frame=bl_frame_index)
                camera.keyframe_insert(data_path="rotation_euler", frame=bl_frame_index)
                if cut_frame_index == len(cut_camera_transforms) - 1:
                    final_frame_indices.add(bl_frame_index)

        cut_first_frame_index = 1  # starts at 1!

        for cut_fov_keyframes, cut_camera_transforms in zip(camera_fov_keyframes, camera_transforms):

            for keyframe_index, fov_keyframe in enumerate(cut_fov_keyframes):
                # TODO: Conversion seems... ALMOST correct.
                camera_data.lens = 100 / math.tan(fov_keyframe.fov)
                cutscene_frame_index = cut_first_frame_index + fov_keyframe.frame_index
                bl_frame_index = cutscene_frame_index * 2 if to_60_fps else cutscene_frame_index
                camera_data.keyframe_insert(data_path="lens", frame=bl_frame_index)

                if keyframe_index == len(cut_fov_keyframes) - 1:
                    # Do not interpolate between final cut FoV keyframe and first keyframe in next cut!
                    final_frame_indices.add(bl_frame_index)

            # TODO: This seems to randomly be off by 1 in either direction (first frame is too early or too late).
            #  I must be missing something with the alignment to camera position.
            cut_first_frame_index += len(cut_camera_transforms)

        # Make all keyframes in `cut_final_frame_indices` 'CONSTANT' interpolation.

        for action in (camera.animation_data.action, camera_data.animation_data.action):
            for fcurve in action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    if keyframe.co.x in final_frame_indices:
                        keyframe.interpolation = "CONSTANT"
