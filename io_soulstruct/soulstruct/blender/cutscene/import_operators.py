"""VERY early/experimental system for importing/exporting DSR cutscene animations into Blender."""
from __future__ import annotations

__all__ = [
    "ImportHKXCutscene",
]

import re
import traceback
import typing as tp
from pathlib import Path

import bpy

from soulstruct.havok.fromsoft.darksouls1r.remobnd import *

from ..base.operators import LoggingImportOperator
from ..base.register import io_soulstruct_class
from ..exceptions import CutsceneImportError, SoulstructTypeError
from ..msb.properties.parts import MSBPartArmatureMode
from ..msb.types.adapters import get_part_game_name
from ..msb.types.darksouls1r import *
from ..types import *
from ..utilities import *
from .types import SoulstructCutsceneAnimation

if tp.TYPE_CHECKING:
    from ..msb.types.base.parts import BaseBlenderMSBPart

REMOBND_RE = re.compile(r"^.*?\.remobnd(\.dcx)?$")


BL_PART_CLASSES = {
    RemoPartType.Player: BlenderMSBPlayerStart,
    RemoPartType.Character: BlenderMSBCharacter,
    RemoPartType.Object: BlenderMSBObject,
    RemoPartType.MapPiece: BlenderMSBMapPiece,
    RemoPartType.Collision: BlenderMSBCollision,
}


@io_soulstruct_class
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

        cutscene_animation = SoulstructCutsceneAnimation.new(remobnd.cutscene_name)

        map_cutscene_collection = find_or_create_collection(
            context.scene.collection, f"{remobnd.get_msb_stem()} Cutscenes"
        )
        cutscene_collection = bpy.data.collections.new(f"Cutscene {remobnd.cutscene_name}")
        map_cutscene_collection.children.link(cutscene_collection)

        try:
            camera = self.create_camera(remobnd, cutscene_animation, import_settings.to_60_fps)
        except Exception as ex:
            bpy.data.actions.remove(cutscene_animation.action)
            traceback.print_exc()  # for inspection in Blender console
            return self.error(f"Cannot import HKX cutscene camera data from {remobnd_path.name}. Error: {ex}")

        cutscene_collection.objects.link(camera)

        if import_settings.camera_data_only:
            cutscene_animation.set_scene_frame_range(context, reset_current_frame=True)
            self.info("Imported HKX cutscene camera data only.")
            return {"FINISHED"}

        # We don't load MSBs and attach them to the RemoBND. We look up the imported Parts in Blender directly.
        remobnd.load_remo_parts()

        self.info(f"Importing HKX cutscene: {remobnd.cutscene_name}")

        for remo_part_type, remo_parts_dict in remobnd.all_remo_parts.items():
            
            if remo_part_type == RemoPartType.Dummy:
                for remo_part in remo_parts_dict.values():
                    if remo_part_type == RemoPartType.Dummy:
                        # Create an Empty and animate its transform.
                        self.create_cutscene_dummy(
                            context,
                            remobnd,
                            remo_part,
                            cutscene_collection,
                            cutscene_animation,
                        )
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

                if bl_part.bl_model_type != SoulstructType.FLVER:
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

                # noinspection PyTypeChecker
                armature = bl_part.armature  # type: ArmatureObject

                if armature.name not in cutscene_collection.objects:
                    cutscene_collection.objects.link(armature)

                # Get bone names from first cut that includes this part.
                first_cut_frames = next(iter(remo_part.cut_arma_frames.values()))
                animated_bone_names = list(first_cut_frames[0].bone_transforms.keys())

                bl_bone_names = [b.name for b in armature.data.bones]
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
                    cutscene_animation.add_cutscene_cuts(
                        context,
                        armature_or_dummy=armature,
                        arma_cuts=all_cut_frames,
                    )
                except Exception as ex:
                    traceback.print_exc()  # for inspection in Blender console
                    self.error(
                        f"Cannot create cutscene animation for '{bl_part.name}' from cutscene {remobnd_path.name}. "
                        f"Error: {ex}"
                    )
                    continue  # next RemoPart

        cutscene_animation.set_scene_frame_range(context, reset_current_frame=True)
        frame_start, frame_end = cutscene_animation.action.frame_range
        self.info(f"Set cutscene start/end frames to: {frame_start}, {frame_end}")

        return {"FINISHED"}

    @staticmethod
    def _get_remo_part_cut_arma_frames_or_counts(
        remobnd: RemoBND, remo_part: RemoPart
    ) -> list[list[RemoPartAnimationFrame] | int]:
        """For each cut, get the Armature-space frames for the given `remo_part` or a frame count if that part
        is not in that cut (so we know how many keyframes to skip if it reappears in a later cut).

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
        cutscene_animation: SoulstructCutsceneAnimation,
    ) -> None:
        dummy_obj = new_empty_object(f"{remobnd.cutscene_name} {remo_part.name}")
        cutscene_collection.objects.link(dummy_obj)
        all_cut_frames = self._get_remo_part_cut_arma_frames_or_counts(remobnd, remo_part)

        try:
            cutscene_animation.add_cutscene_cuts(
                context,
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

    def create_camera(
        self,
        remobnd: RemoBND,
        cutscene_animation: SoulstructCutsceneAnimation,
        to_60_fps: bool,
    ) -> CameraObject:
        """Create a new Blender camera object for the cutscene."""
        camera_name = self.camera_name.format(CutsceneName=remobnd.cutscene_name)
        camera_data = bpy.data.cameras.new(self.camera_name.format(CutsceneName=remobnd.cutscene_name))
        camera_data.sensor_width = 35  # mm (seems to match game FoV appearance)
        # noinspection PyTypeChecker
        camera = bpy.data.objects.new(camera_name, camera_data)  # type: CameraObject

        # Add motion to camera.
        camera_transforms = [cut.sibcam.get_clipped_camera_animation() for cut in remobnd.cuts]
        camera_fov_keyframes = [cut.sibcam.get_fov_keyframes_scaled_to_clip() for cut in remobnd.cuts]

        try:
            cutscene_animation.add_camera_cuts(camera, camera_transforms, camera_fov_keyframes, to_60_fps)
        except Exception:
            bpy.data.objects.remove(camera)
            bpy.data.cameras.remove(camera_data)
            raise

        return camera
