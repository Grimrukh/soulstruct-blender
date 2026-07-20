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
from ..base.register import io_soulstruct_operator
from ..exceptions import CutsceneImportError, SoulstructTypeError
from ..msb.properties.parts import MSBPartArmatureMode
from ..msb.types.adapters import get_part_game_name
from ..msb.types.darksouls1r import *
from ..types import *
from ..utilities import *
from .types import CutFrames, SoulstructCutsceneAnimation

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


@io_soulstruct_operator
class ImportHKXCutscene(LoggingImportOperator):
    bl_idname = "import_scene.hkx_cutscene"
    bl_label = "Import HKX Cutscene"
    bl_description = "Import a HKX cutscene file from a RemoBND"

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'}, subtype="DIR_PATH")

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
    POLL_DEFAULT_SUBDIR = False

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
        bl_frames_per_game_frame = 2.0 if import_settings.to_60_fps else 1.0

        # Create the camera FIRST. If camera import fails we only need to drop the Action,
        # leaving no dangling cutscene collections behind.
        try:
            camera = self.create_camera(remobnd, cutscene_animation, bl_frames_per_game_frame)
        except Exception as ex:
            bpy.data.actions.remove(cutscene_animation.action)
            traceback.print_exc()  # for inspection in Blender console
            return self.error(f"Cannot import HKX cutscene camera data from {remobnd_path.name}. Error: {ex}")

        # Camera succeeded: now build collections and link it.
        map_cutscene_collection = find_or_create_collection(
            context.scene.collection, f"{remobnd.get_msb_stem()} Cutscenes"
        )
        cutscene_collection = bpy.data.collections.new(f"Cutscene {remobnd.cutscene_name}")
        map_cutscene_collection.children.link(cutscene_collection)
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
                self._import_dummies(
                    remobnd, remo_parts_dict, cutscene_collection, cutscene_animation, bl_frames_per_game_frame
                )
                continue

            try:
                bl_part_class = BL_PART_CLASSES[remo_part_type]
            except KeyError:
                self.warning(
                    f"Cannot find `BaseBlenderMSBPart` subclass model for `RemoPartType`: {remo_part_type}"
                )
                continue
            bl_part_class: type[BaseBlenderMSBPart]

            for remo_part in remo_parts_dict.values():
                self._import_part(
                    context,
                    remobnd,
                    remo_part,
                    remo_part_type,
                    bl_part_class,
                    cutscene_collection,
                    cutscene_animation,
                    bl_frames_per_game_frame,
                )

        cutscene_animation.set_scene_frame_range(context, reset_current_frame=True)
        frame_start, frame_end = cutscene_animation.action.frame_range
        self.info(f"Set cutscene start/end frames to: {frame_start}, {frame_end}")

        return {"FINISHED"}

    # region Per-part import

    def _import_part(
        self,
        context: bpy.types.Context,
        remobnd: RemoBND,
        remo_part: RemoPart,
        remo_part_type: RemoPartType,
        bl_part_class: type[BaseBlenderMSBPart],
        cutscene_collection: bpy.types.Collection,
        cutscene_animation: SoulstructCutsceneAnimation,
        bl_frames_per_game_frame: float,
    ) -> None:
        """Import and animate a single (non-Dummy) RemoPart."""
        self.debug(f"Adding RemoPart: {remo_part.name}")

        bl_part = self.find_remo_part_msb_part(context, remo_part, bl_part_class)
        if bl_part is None:
            return

        # Link to cutscene collection (additively; still in MSB collection).
        cutscene_collection.objects.link(bl_part.obj)

        if bl_part.bl_model_type != SoulstructType.FLVER:
            # e.g. Collisions. Not animated, only used for display groups.
            return
        if not bl_part.model:
            # No model set. Cannot detect bone data type.
            return

        bone_data_type = bl_part.model.FLVER.bone_data_type

        cuts = self._get_remo_part_cuts(remobnd, remo_part)

        # We need to add an Armature to the Part, if it doesn't already have one (including default Armatures).
        # Map Pieces are never bone-animated (root motion only), which doesn't require an Armature.
        if not bl_part.armature:
            # TODO: try/except around duplication so a single failure doesn't abort the whole import.
            bl_part.duplicate_flver_model_armature(
                self,
                context,
                mode=MSBPartArmatureMode.IF_PRESENT,
                copy_pose=False,
            )
            context.view_layer.update()  # so we can set pose below

        if not bl_part.armature:
            if remo_part_type != RemoPartType.MapPiece:
                self.warning(f"MSB Part '{remo_part.map_part_name}' does not have an Armature. Cannot animate.")
            return

        # noinspection PyTypeChecker
        armature = bl_part.armature  # type: ArmatureObject
        if armature.name not in cutscene_collection.objects:
            cutscene_collection.objects.link(armature)

        if not self._validate_part_bones(remo_part, bl_part, armature):
            return

        # "Disable" unused high-level bones whose children are directly animated by the cutscene.
        # This is done by setting the `PoseBone.matrix_basis` to the inverse of the bone's local rest transform.
        # TODO: Can remove I think.
        # cutscene_animation.cancel_remo_root_parent_rest(armature, remo_part.part_cutscene_root_bone_names)

        try:
            cutscene_animation.add_armature_cuts(
                armature=armature,
                cuts=cuts,
                bl_frames_per_game_frame=bl_frames_per_game_frame,
                bone_data_type=bone_data_type,
                is_root_motion_only=False,
                assert_root_bone_names=remo_part.part_cutscene_root_bone_names,
            )
        except Exception as ex:
            self._log_exception(
                f"Cannot create cutscene animation for '{bl_part.name}' from cutscene "
                f"{remobnd.path.name}. Error: {ex}"
            )

    def _validate_part_bones(
        self, remo_part: RemoPart, bl_part: BaseBlenderMSBPart, armature: ArmatureObject
    ) -> bool:
        """Check that every cutscene-animated bone for this part exists in the Blender Armature.

        Bone names are unioned across the first frame of every cut the part appears in, in case a
        part uses different bone sets in different cuts. The FLVER 'master' bone is intentionally
        not required: it's replaced by the root of the amalgamated cutscene skeleton and never
        appears in cutscene data.
        """
        animated_bone_names = set()
        for cut_frames in remo_part.cut_arma_frames.values():
            if cut_frames:
                animated_bone_names.update(cut_frames[0].bone_transforms.keys())

        bl_bone_names = {b.name for b in armature.data.bones}
        missing = animated_bone_names - bl_bone_names
        if missing:
            self.error(
                f"Cutscene bone name(s) {sorted(missing)} missing from part armature "
                f"'{bl_part.name}'. Cannot apply cutscene animation."
            )
            return False
        return True

    def _import_dummies(
        self,
        remobnd: RemoBND,
        remo_parts_dict: dict[tp.Any, RemoPart],
        cutscene_collection: bpy.types.Collection,
        cutscene_animation: SoulstructCutsceneAnimation,
        bl_frames_per_game_frame: float,
    ) -> None:
        """Create an Empty for each Dummy RemoPart and animate its transform (root motion only)."""
        for remo_part in remo_parts_dict.values():
            dummy_obj = new_empty_object(f"{remobnd.cutscene_name} {remo_part.name}")
            cutscene_collection.objects.link(dummy_obj)
            cuts = self._get_remo_part_cuts(remobnd, remo_part)

            try:
                cutscene_animation.add_dummy_cuts(
                    dummy=dummy_obj,
                    cuts=cuts,
                    bl_frames_per_game_frame=bl_frames_per_game_frame,
                )
            except Exception as ex:
                self._log_exception(
                    f"Cannot create cutscene animation for Dummy '{remo_part.name}' "
                    f"from cutscene at path '{remobnd.path.name}'. Error: {ex}"
                )

    # endregion

    @staticmethod
    def _get_remo_part_cuts(remobnd: RemoBND, remo_part: RemoPart) -> list[CutFrames]:
        """Build the per-cut animation list for `remo_part`.

        Each `CutFrames` carries the cut's clip length and, when the part is present in that cut,
        its Armature-space frames (bone names -> `TRSTransform`). Cuts are kept separate so that
        interpolation can be disabled across cut boundaries when keyframes are added. For cuts the
        part is absent from, `frames` is `None` and `frame_count` (from the camera clip) pads the
        timeline so a later reappearance lands on the right frame.
        """
        cuts = []  # type: list[CutFrames]
        for cut in remobnd.cuts:
            frames = remo_part.cut_arma_frames.get(cut.name)
            frame_count = len(frames) if frames is not None else cut.sibcam.clip_frame_count
            cuts.append(CutFrames(frame_count=frame_count, frames=frames))
        return cuts

    def _log_exception(self, message: str) -> None:
        """Print the current traceback (for the Blender console) and report an operator error."""
        traceback.print_exc()
        self.error(message)

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

    def create_camera(
        self,
        remobnd: RemoBND,
        cutscene_animation: SoulstructCutsceneAnimation,
        bl_frames_per_game_frame: float,
    ) -> CameraObject:
        """Create a new Blender camera object for the cutscene and animate it."""
        camera_name = self.camera_name.format(CutsceneName=remobnd.cutscene_name)
        camera_data = bpy.data.cameras.new(camera_name)
        camera_data.sensor_width = 35  # mm (seems to match game FoV appearance)
        # noinspection PyTypeChecker
        camera = bpy.data.objects.new(camera_name, camera_data)  # type: CameraObject

        # Add motion to camera.
        camera_transforms = [cut.sibcam.get_clipped_camera_animation() for cut in remobnd.cuts]
        camera_fov_keyframes = [cut.sibcam.get_clip_timescaled_fov_keyframes() for cut in remobnd.cuts]

        try:
            cutscene_animation.add_camera_cuts(
                camera, camera_transforms, camera_fov_keyframes, bl_frames_per_game_frame
            )
        except Exception:
            bpy.data.objects.remove(camera)
            bpy.data.cameras.remove(camera_data)
            raise

        return camera
