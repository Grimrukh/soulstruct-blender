"""VERY early/experimental system for importing/exporting DSR cutscene animations into Blender."""
from __future__ import annotations

__all__ = [
    "ImportHKXCutscene",
]

import math
import re
import traceback
import typing as tp
from pathlib import Path

import bpy

from soulstruct.base.animations.sibcam import CameraFrameTransform, FoVKeyframe

from soulstruct_havok.fromsoft.darksouls1r.remobnd import *

from io_soulstruct.animation.types import SoulstructAnimation
from io_soulstruct.exceptions import CutsceneImportError, SoulstructTypeError
from io_soulstruct.msb.properties.parts import MSBPartArmatureMode
from io_soulstruct.msb.types.adapters import get_part_game_name
from io_soulstruct.msb.types.darksouls1r import *
from io_soulstruct.utilities import *

if tp.TYPE_CHECKING:
    from io_soulstruct.msb.types.base.parts import BaseBlenderMSBPart

REMOBND_RE = re.compile(r"^.*?\.remobnd(\.dcx)?$")


BL_PART_CLASSES = {
    RemoPartType.Player: BlenderMSBPlayerStart,
    RemoPartType.Character: BlenderMSBCharacter,
    RemoPartType.Object: BlenderMSBObject,
    RemoPartType.MapPiece: BlenderMSBMapPiece,
    RemoPartType.Collision: BlenderMSBCollision,
}


class ImportHKXCutscene(LoggingImportOperator):
    bl_idname = "import_scene.hkx_cutscene"
    bl_label = "Import HKX Cutscene"
    bl_description = "Import a HKX cutscene file from a RemoBND"

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

    DEFAULT_SUBDIR = "remo"

    @classmethod
    def poll(cls, context) -> bool:
        """Only for DSR right now."""
        return cls.settings(context).is_game("DARK_SOULS_DSR") and super().poll(context)

    def execute(self, context):
        remobnd_path = Path(self.filepath)
        import_settings = context.scene.cutscene_import_settings

        if not REMOBND_RE.match(remobnd_path.name):
            raise CutsceneImportError("Must import cutscene from a `remobnd` binder file.")
        
        try:
            remobnd = RemoBND.from_path(remobnd_path)
        except Exception as ex:
            raise CutsceneImportError(f"Could not parse RemoBND file '{remobnd_path}': {ex}")

        try:
            camera = self.create_camera(context, remobnd, import_settings.to_60_fps)
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            return self.error(f"Cannot import HKX cutscene camera data from {remobnd_path.name}. Error: {ex}")

        if import_settings.camera_data_only:
            self.info("Imported HKX cutscene camera data only.")
            return {"FINISHED"}

        # We don't load MSBs and attach them to the RemoBND. We look up the imported Parts in Blender directly.
        remobnd.load_remo_parts()

        self.info(f"Importing HKX cutscene: {remobnd.cutscene_name}")

        map_cutscene_collection = find_or_create_collection(
            context.scene.collection, f"{remobnd.get_msb_stem()} Cutscenes"
        )
        cutscene_collection = bpy.data.collections.new(f"Cutscene {remobnd.cutscene_name}")
        map_cutscene_collection.children.link(cutscene_collection)

        cutscene_collection.objects.link(camera)
        all_animations = [SoulstructAnimation(camera.animation_data.action)]

        for remo_part_type, remo_parts_dict in remobnd.all_remo_parts.items():
            
            if remo_part_type == RemoPartType.Dummy:
                for remo_part in remo_parts_dict.values():
                    if remo_part_type == RemoPartType.Dummy:
                        # Create an Empty and animate its transform.
                        dummy_anim = self.create_cutscene_dummy(
                            context,
                            remobnd,
                            remo_part,
                            cutscene_collection,
                        )
                        if dummy_anim:
                            all_animations.append(dummy_anim)
                continue  # next `RemoPartType`

            try:
                bl_part_class = BL_PART_CLASSES[remo_part_type]
            except KeyError:
                self.warning(
                    f"Cannot find `BaseBlenderMSBPart` subclass model for `RemoPartType`: {remo_part_type}"
                )
                continue
            bl_part_class: type[BaseBlenderMSBPart]

            for remo_part in remo_parts_dict.values():

                self.debug(f"Adding RemoPart: {remo_part.name}")

                bl_part = self.find_remo_part_msb_part(context, remo_part, bl_part_class)
                if bl_part is None:
                    continue  # next RemoPart

                # Link to cutscene collection (additively; still in MSB collection).
                cutscene_collection.objects.link(bl_part.obj)

                if bl_part._MODEL_ADAPTER.bl_model_type != SoulstructType.FLVER:
                    # e.g. Collisions. Not animated, only used for display groups.
                    continue  # next RemoPart

                all_cut_frames = self._get_remo_part_cut_arma_frames_or_counts(remobnd, remo_part)

                # TODO: `RemoPart` method that checks if animation data, for a given cut:
                #   a) is root only (no bones)
                #   b) is 100% identity transform
                #  If both are true, we can skip animating this part.
                #  If (a) is true, we can animate the object's transform only.
                #  We can maybe just assert that Map Pieces are NEVER animated, as well.

                # We need to add an Armature to the Part, if it doesn't already have one (including default Armatures).
                # TODO: Do we actually need the Map Pieces to have default Armatures...?
                #  Surely they don't have any actual animation data in the REMOBND.
                #  (Correct: just root motion, which doesn't require an Armature. Animation drives transform only.)
                if not bl_part.armature:
                    # TODO: try/except, etc.
                    bl_part.duplicate_flver_model_armature(
                        self,
                        context,
                        mode=MSBPartArmatureMode.IF_PRESENT,
                        copy_pose=False,
                    )
                    context.view_layer.update()  # so we can set pose below  TODO: slight optimization to batch this

                if not bl_part.armature:
                    if remo_part_type != RemoPartType.MapPiece:
                        self.warning(f"MSB Part '{remo_part.map_part_name}' does not have an Armature. Cannot animate.")
                    continue  # next RemoPart

                if bl_part.armature.name not in cutscene_collection.objects:
                    cutscene_collection.objects.link(bl_part.armature)

                # Get bone names from first cut that includes this part.
                first_cut_frames = next(iter(remo_part.cut_arma_frames.values()))
                animated_bone_names = list(first_cut_frames[0].bone_transforms.keys())

                bl_bone_names = [b.name for b in bl_part.armature.data.bones]
                # Check that all cutscene part bone names are present in Blender Armature.
                # We ignore the FLVER 'master' bone, which does not appear in cutscene data (it's replaced by the
                # root of the amalgamated cutscene 'skeleton').
                flver_bones_missing = False
                for bone_name in animated_bone_names:
                    if bone_name not in bl_bone_names:
                        self.error(
                            f"Cutscene bone name '{bone_name}' is missing from part armature '{bl_part.name}'. "
                            f"Cannot apply cutscene animation."
                        )
                        flver_bones_missing = True
                        break
                if flver_bones_missing:
                    continue

                # Create action for this part.
                # TODO: When scaling up frame rate, CONSTANT interpolation on final frame leaves the NEXT frame fixed
                #  before the next cut. Just a tiny visual quirk that wouldn't affect export.
                try:
                    part_anim = SoulstructAnimation.new_from_cutscene_cuts(
                        context,
                        action_name=f"{remobnd.cutscene_name}[{bl_part.game_name}]",
                        armature_or_dummy=bl_part.armature,
                        arma_cuts=all_cut_frames,
                    )
                except Exception as ex:
                    traceback.print_exc()  # for inspection in Blender console
                    self.error(
                        f"Cannot create cutscene animation for '{bl_part.name}' from cutscene {remobnd_path.name}. "
                        f"Error: {ex}"
                    )
                    continue  # next RemoPart

                all_animations.append(part_anim)

        if all_animations:
            frame_start = min(anim.action.frame_range[0] for anim in all_animations)
            frame_end = max(anim.action.frame_range[1] for anim in all_animations)
            context.scene.frame_start = int(frame_start)
            context.scene.frame_end = int(frame_end)
            context.scene.frame_set(context.scene.frame_start)
            self.info(f"Set cutscene start/end frames to: {frame_start}, {frame_end}")

        return {"FINISHED"}

    @staticmethod
    def _get_remo_part_cut_arma_frames_or_counts(
        remobnd: RemoBND, remo_part: RemoPart
    ) -> list[list[RemoPartAnimationFrame] | int]:
        """For each cut, get the Armature-space frames for the given `remo_part` or a frame count if not in cut.

        Each frame maps bone names to a `TRSTransform` in armature space. Cuts are just lists of frames.
        Separate cuts are maintained so that we can disable interpolation between them as keyframes are added.
        For cuts that don't contain this part, we include the length of the cut (from the camera) instead so
        that the appropriate number of frames can be skipped when creating the Action.
        """
        all_cut_frames = []  # type: list[list[RemoPartAnimationFrame] | int]
        for cut in remobnd.cuts:
            if cut.name in remo_part.cut_arma_frames:
                # Model is present in this cut. Use real transforms.
                all_cut_frames.append(remo_part.cut_arma_frames[cut.name])
            else:
                # Model is absent in this cut. Just include clip frame count for padding the timeline.
                all_cut_frames.append(cut.sibcam.clip_frame_count)
        return all_cut_frames

    def find_remo_part_msb_part(
        self, context: bpy.types.Context, remo_part: RemoPart, bl_part_class: type[BaseBlenderMSBPart]
    ) -> BaseBlenderMSBPart | None:

        area, block = remo_part.map_area_block
        map_stem = f"m{area:02d}_{block:02d}_00_00"
        msb_stem = context.scene.soulstruct_settings.get_latest_map_stem_version(map_stem)
        collection_name = f"{msb_stem} {bl_part_class.MSB_ENTRY_SUBTYPE.get_nice_name()} Parts"
        try:
            # TODO: Restrict to Scene collections?
            part_collection = bpy.data.collections[collection_name]
        except KeyError:
            self.error(
                f"Could not find MSB Part collection '{collection_name}' for cutscene Part "
                f"'{remo_part.map_part_name}' (full Remo name '{remo_part.name}')."
            )
            return None

        for obj in part_collection.objects:  # immediate child objects only
            # TODO: Use proper 'find object of type' utility.
            if obj.type == "MESH" and get_part_game_name(obj.name) == remo_part.map_part_name:
                try:
                    return bl_part_class(obj)
                except SoulstructTypeError:
                    self.error(
                        f"Found Mesh object '{obj.name}' in collection '{part_collection.name}', but it "
                        f"is not a valid `{bl_part_class.__name__}` object."
                    )
                    return None

        self.error(f"Could not find MSB Part '{remo_part.map_part_name}' in MSB collection '{part_collection.name}'.")
        return None

    def create_cutscene_dummy(
        self,
        context: bpy.types.Context,
        remobnd: RemoBND,
        remo_part: RemoPart,
        cutscene_collection: bpy.types.Collection,
    ) -> SoulstructAnimation | None:
        dummy_obj = new_empty_object(f"{remobnd.cutscene_name} {remo_part.name}")
        cutscene_collection.objects.link(dummy_obj)
        all_cut_frames = self._get_remo_part_cut_arma_frames_or_counts(remobnd, remo_part)

        try:
            return SoulstructAnimation.new_from_cutscene_cuts(
                context,
                action_name=f"{remobnd.cutscene_name}[{remo_part.name}]",
                armature_or_dummy=dummy_obj,
                arma_cuts=all_cut_frames,
                is_root_motion_only=True,
            )
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            self.error(
                f"Cannot create cutscene animation for Dummy '{remo_part.name}' "
                f"from cutscene at path '{remobnd.path.name}'. Error: {ex}"
            )
            return None

    def create_camera(
        self,
        context: bpy.types.Context,
        remobnd: RemoBND,
        to_60_fps: bool,
    ) -> bpy.types.CameraObject:
        """Create a new Blender camera object for the cutscene."""
        camera_name = self.camera_name.format(CutsceneName=remobnd.cutscene_name)
        camera_data = bpy.data.cameras.new(self.camera_name.format(CutsceneName=remobnd.cutscene_name))
        camera_data.sensor_width = 35  # mm (seems to match game FoV appearance)
        # noinspection PyTypeChecker
        camera = bpy.data.objects.new(camera_name, camera_data)  # type: bpy.types.CameraObject

        # Add motion to camera.
        camera_transforms = [cut.sibcam.get_clipped_camera_animation() for cut in remobnd.cuts]
        camera_fov_keyframes = [cut.sibcam.get_fov_keyframes_scaled_to_clip() for cut in remobnd.cuts]

        self.create_camera_actions(
            camera,
            cutscene_name=remobnd.cutscene_name,
            camera_transforms=camera_transforms,
            camera_fov_keyframes=camera_fov_keyframes,
            to_60_fps=to_60_fps,
        )

        return camera

    def create_camera_actions(
        self,
        camera: bpy.types.CameraObject,
        cutscene_name: str,
        camera_transforms: list[list[CameraFrameTransform]],
        camera_fov_keyframes: list[list[tuple[float, float]]],
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

        return obj_action, data_action

    @staticmethod
    def add_camera_keyframes(
        camera: bpy.types.CameraObject,
        camera_transforms: list[list[CameraFrameTransform]],
        camera_fov_keyframes: list[list[tuple[float, float]]],
        to_60_fps: bool,
    ):
        """Add keyframes for camera object and data (focal length)."""
        camera_data = camera.data  # type: bpy.types.Camera

        final_frame_indices = set()

        # TODO: Fix any camera rotation discontinuities first?

        # NOT reset across cuts.
        cutscene_frame_index = 0

        # TODO: Use array `foreach_set`, not `keyframe_insert`.

        for cut_camera_transforms in camera_transforms:

            for cut_frame_index, camera_transform in enumerate(cut_camera_transforms):
                bl_frame_index = cutscene_frame_index * 2 if to_60_fps else cutscene_frame_index
                bl_translate = GAME_TO_BL_VECTOR(camera_transform.position)
                bl_euler = GAME_TO_BL_EULER(camera_transform.rotation)
                camera.location = bl_translate
                camera.rotation_euler = bl_euler
                camera.keyframe_insert(data_path="location", frame=bl_frame_index)
                camera.keyframe_insert(data_path="rotation_euler", frame=bl_frame_index)
                if cut_frame_index == len(cut_camera_transforms) - 1:
                    final_frame_indices.add(bl_frame_index)
                cutscene_frame_index += 1

        for fcurve in camera.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                if int(keyframe.co.x) in final_frame_indices:
                    keyframe.interpolation = "CONSTANT"
                else:
                    keyframe.interpolation = "LINEAR"

        cut_fov_t_offset = 0
        camera_final_t = set()
        sensor_width = camera_data.sensor_width
        for cut_fov_keyframes, cut_camera_transforms in zip(camera_fov_keyframes, camera_transforms, strict=True):

            bl_t = -1
            for t, fov in cut_fov_keyframes:
                camera_data.lens = sensor_width / (2 * math.tan(fov / 2.0))
                bl_t = (cut_fov_t_offset + t) * 2 if to_60_fps else (cut_fov_t_offset + t)
                camera_data.keyframe_insert(data_path="lens", frame=bl_t)
            if bl_t >= 0:
                camera_final_t.add(bl_t)

            # Add transform frame count to `t` offset for next cut.
            cut_fov_t_offset += len(cut_camera_transforms)

        # Make all keyframes in `final_frame_indices` 'CONSTANT' interpolation.
        for fcurve in camera_data.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                if int(keyframe.co.x) in camera_final_t:
                    keyframe.interpolation = "CONSTANT"
                else:
                    keyframe.interpolation = "LINEAR"
