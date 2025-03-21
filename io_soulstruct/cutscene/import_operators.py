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

    @classmethod
    def poll(cls, context) -> bool:
        # Only for DSR right now.
        return cls.settings(context).is_game("DARK_SOULS_DSR")

    def execute(self, context):
        """
        TODO: What's the battle plan here?
            - Assert that MSB has already been loaded. We only animate Parts we can find; no MSB import here.
                - But happy to lazily duplicate Part Armatures here as needed.
            - Animation should be NON-DESTRUCTIVE in the MSB.
                - That means, don't lose MSB Parts' transforms by animating them.
                - Problem is that in the game, cutscene animations genuinely can move Parts around. The game doesn't
                care about losing the initial MSB positions of its Parts.
                - We could animate the '<PART_ROOT>' bone I create for Parts, but the problem is that the REMOBND
                animation data is in absolute map space, not relative to the Part's initial position.
                    - One idea: correct the animation data to be relative to the Part's initial position.
                    - Very confusing for the user, though, when they're creating their own cutscene animations.
                - Another idea: before assigning ANY action to an MSB Part, store its last known transform ('initial
                MSB transform') in custom Vector properties. If these custom properties are present on MSB export, they
                are used in place of the current local transform.
                    - Can have an operator button that restore the initial MSB transform (and removes the properties).
                    - And an operator button that just clears the initial MSB transform properties, which will make the
                    current local transform the new initial transform. (Or, clear if any animation is assigned, but
                    just update if an animation is still assigned.)

        """

        settings = self.settings(context)
        remobnd_path = Path(self.filepath)
        import_settings = context.scene.cutscene_import_settings

        if not REMOBND_RE.match(remobnd_path.name):
            raise CutsceneImportError("Must import cutscene from a `remobnd` binder file.")
        
        try:
            remobnd = RemoBND.from_path(remobnd_path)
        except Exception as ex:
            raise CutsceneImportError(f"Could not parse RemoBND file '{remobnd_path}': {ex}")

        try:
            self.create_camera(context, remobnd, import_settings.to_60_fps)
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            return self.error(f"Cannot import HKX cutscene camera data from {remobnd_path.name}. Error: {ex}")

        if import_settings.camera_data_only:
            self.info("Imported HKX cutscene camera data only.")
            return {"FINISHED"}

        # We don't load MSBs and attach them to the RemoBND. We look up the imported Parts in Blender directly.
        remobnd.load_remo_parts()

        self.info(f"Importing HKX cutscene: {remobnd.cutscene_name}")

        for remo_part_type, remo_parts_dict in remobnd.all_remo_parts.items():
            
            try:
                bl_part_class = BL_PART_CLASSES[remo_part_type]
            except KeyError:
                self.warning(
                    f"Cannot find `BaseBlenderMSBPart` subclass model for `RemoPartType`: {remo_part_type}"
                )
                continue
            bl_part_class: type[BaseBlenderMSBPart]

            for remo_part in remo_parts_dict.values():
    
                area, block = remo_part.map_area_block
                map_stem = f"m{area:02d}_{block:02d}_00_00"
                msb_stem = settings.get_latest_map_stem_version(map_stem)
                collection_name = f"{msb_stem} {bl_part_class.MSB_ENTRY_SUBTYPE.get_nice_name()} Parts"
                try:
                    # TODO: Restrict to Scene collections?
                    part_collection = bpy.data.collections[collection_name]
                except KeyError:
                    self.error(f"Could not find MSB Part collection '{collection_name}' for cutscene Part "
                               f"'{remo_part.map_part_name}' (full Remo name '{remo_part.name}').")
                    continue
    
                bl_part = None  # type: BaseBlenderMSBPart | None
                for obj in part_collection.objects:  # immediate child objects only
                    if obj.type == "MESH" and get_part_game_name(obj.name) == remo_part.map_part_name:
                        try:
                            bl_part = bl_part_class(obj)
                        except SoulstructTypeError:
                            self.error(f"Found Mesh object '{obj.name}' in collection '{part_collection.name}', but it "
                                       f"is not a valid `{bl_part_class.__name__}` object.")
                            break

                if bl_part is None:
                    self.error(
                        f"Could not find MSB Part '{remo_part.map_part_name}' in collection '{part_collection.name}'."
                    )
                    continue

                # We need to add an Armature to the Part, if it doesn't already have one (including default Armatures).
                # TODO: Do we actually need the Map Pieces to have default Armatures...?
                #  Surely they don't have any actual animation data in the REMOBND.
                #  (Correct: just root motion, which doesn't require an Armature. Animation drives transform only.)
                if bl_part._MODEL_ADAPTER.bl_model_type == SoulstructType.FLVER and not bl_part.armature:
                    # TODO: try/except, etc.
                    bl_part.duplicate_flver_model_armature(
                        self,
                        context,
                        mode=MSBPartArmatureMode.IF_PRESENT,
                        copy_pose=False,
                    )

                if not bl_part.armature:
                    self.warning(f"MSB Part '{remo_part.map_part_name}' does not have an Armature. Cannot animate.")
                    continue

                # Get bone names from first cut that includes this part.
                first_cut_frames = next(iter(remo_part.cut_arma_frames.values()))
                animated_bone_names = list(first_cut_frames[0].bone_transforms.keys())
                # TODO: If not `animated_bone_names`... `SoulstructAnimation` class method that only does root motion
                #  (no Armature required).

                bl_bone_names = [b.name for b in bl_part.armature.data.bones]
                # Check that all cutscene part bone names are present in Blender Armature.
                # We ignore the FLVER 'master' bone, which does not appear in cutscene data (it's replaced by the
                # root of the amalgamated cutscene 'skeleton').
                for bone_name in animated_bone_names:
                    if bone_name not in bl_bone_names:
                        print(animated_bone_names)
                        raise ValueError(
                            f"Cutscene bone name '{bone_name}' is missing from part armature '{bl_part.name}'."
                        )

                # Each frame maps bone names to a `TRSTransform` in armature space. Cuts are just lists of frames.
                # Separate cuts are maintained so that we can disable interpolation between them as keyframes are added.
                # For cuts that don't contain this part, we include the length of the cut (from the camera) instead so
                # that the appropriate number of frames can be skipped when creating the Action.
                all_cut_frames = []  # type: list[list[RemoPartAnimationFrame] | int]
                for cut in remobnd.cuts:
                    if cut.name in remo_part.cut_arma_frames:
                        # Model is present in this cut. Use real transforms.
                        all_cut_frames.append(remo_part.cut_arma_frames[cut.name])
                    else:
                        # Model is absent in this cut. Just include frame count.
                        frame_count = len(cut.sibcam.camera_animation)
                        all_cut_frames.append(frame_count)

                # Create action for this part.
                # TODO: Bug: actions of different parts (and camera) are OUT OF SYNC.
                #  Not sure yet how this could be happening. Should double-check number of frames for each part in each
                #  cut?
                try:
                    SoulstructAnimation.new_from_cutscene_cuts(
                        context,
                        action_name=f"{remobnd.cutscene_name}[{bl_part.game_name}]",
                        armature=bl_part.armature,
                        arma_cuts=all_cut_frames,
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
