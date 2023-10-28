from __future__ import annotations

__all__ = [
    "ExportHKXAnimation",
    "ExportHKXAnimationIntoBinder",
    "ExportCharacterHKXAnimation",
    "ExportObjectHKXAnimation",
]

import re
import traceback
from pathlib import Path

import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper

from soulstruct.containers import Binder, EntryNotFoundError
from soulstruct.dcx import DCXType
from soulstruct_havok.wrappers.hkx2015 import SkeletonHKX, AnimationHKX
from soulstruct_havok.utilities.maths import Vector4, TRSTransform

from io_soulstruct.utilities import *
from io_soulstruct.general import *
from io_soulstruct.havok.utilities import BL_MATRIX_TO_GAME_TRS
from .utilities import *


ACTION_NAME_RE = re.compile(r"^(.*)\|(a[\d_]+)(\.\d+)?$")
BONE_DATA_PATH_RE = re.compile(r"pose\.bones\[(\w+)]\.(location|rotation_quaterion|scale)")
SKELETON_ENTRY_RE = re.compile(r"skeleton\.hkx", re.IGNORECASE)


class ExportHKXAnimation(LoggingOperator, ExportHelper):
    """Export HKX animation from an Action attached to a FLVER armature."""
    bl_idname = "export_scene.hkx_animation"
    bl_label = "Export HKX Animation"
    bl_description = "Export a Blender action to a standalone HKX animation file with manual HKX skeleton source"

    # ExportHelper mixin class uses this
    filename_ext = ".hkx"

    filter_glob: StringProperty(
        default="*.hkx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    hkx_skeleton_path: StringProperty(
        name="HKX Skeleton Path",
        description="Path to matching HKX skeleton file (required for animation export)",
        default="",
    )

    from_60_fps: bpy.props.BoolProperty(
        name="From 60 FPS",
        description="Scale animation keyframes from 60 FPS in Blender down to 30 FPS",
        default=True,
    )

    dcx_type: get_dcx_enum_property()

    @classmethod
    def poll(cls, context):
        try:
            return context.selected_objects[0].type == "ARMATURE"
        except IndexError:
            return False

    def execute(self, context):
        self.info("Executing HKX animation export...")

        settings = GlobalSettings.get_scene_settings(context)  # type: GlobalSettings

        animation_file_path = Path(self.filepath)

        skeleton_path = Path(self.hkx_skeleton_path)
        if not skeleton_path.is_file():
            return self.error(f"Invalid HKX skeleton path: {skeleton_path}")

        if skeleton_path.name.endswith(".hkx") or skeleton_path.name.endswith(".hkx.dcx"):
            skeleton_hkx = SkeletonHKX.from_path(skeleton_path)
        else:
            try:
                skeleton_binder = Binder.from_path(skeleton_path)
            except ValueError:
                return self.error(f"Could not load file as a `SkeletonHKX` or `Binder`: {skeleton_path}")
            try:
                skeleton_entry = skeleton_binder[SKELETON_ENTRY_RE]
            except EntryNotFoundError:
                return self.error(f"Could not find `skeleton.hkx` (case-insensitive) in binder: '{skeleton_path}'")
            skeleton_hkx = SkeletonHKX.from_binder_entry(skeleton_entry)

        bl_armature = context.selected_objects[0]

        current_frame = context.scene.frame_current  # store for resetting after export
        try:
            animation_hkx = create_animation_hkx(skeleton_hkx, bl_armature, self.from_60_fps)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Failed to create animation HKX: {ex}")
        finally:
            context.scene.frame_set(current_frame)

        dcx_type = settings.resolve_dcx_type(self.dcx_type, "HKX", is_binder_entry=False)
        animation_hkx.dcx_type = dcx_type
        animation_hkx.write(animation_file_path)

        return {"FINISHED"}


class ExportHKXAnimationIntoBinder(LoggingOperator, ImportHelper):
    """Export HKX animation from an Action attached to a FLVER armature, into an existing BND."""
    bl_idname = "export_scene.hkx_animation_binder"
    bl_label = "Export HKX Animation Into Binder"
    bl_description = "Export a Blender action to a HKX animation file inside a FromSoftware Binder (BND/BHD)"

    # ImportHelper mixin class uses this
    filename_ext = ".anibnd"

    filter_glob: StringProperty(
        default="*.anibnd;*.anibnd.dcx;*.objbnd;*.objbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    dcx_type: get_dcx_enum_property()

    from_60_fps: bpy.props.BoolProperty(
        name="From 60 FPS",
        description="Scale animation keyframes from 60 FPS in Blender down to 30 FPS",
        default=True,
    )

    animation_id: IntProperty(
        name="Animation ID",
        description="Animation ID for name and Binder entry ID to use",
        default=0,
        min=0,
    )

    overwrite_existing: BoolProperty(
        name="Overwrite Existing",
        description="Allow existing animation with this ID to be overwritten",
        default=True,
    )

    default_entry_path: StringProperty(
        name="Default Path",
        description="Path to use for Binder entry if it needs to be created. Default is for DS1R `anibnd.dcx` files",
        default="N:\\FRPG\\data\\Model\\chr\\{name}\\hkxx64\\",
    )

    name_template: StringProperty(
        name="Animation Name Template",
        description="Template for converting animation ID to entry name",
        default="a##_####",  # default for DS1
    )

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) == 1 and context.selected_objects[0].type == "ARMATURE"

    def execute(self, context):
        print("Executing HKX animation export into Binder...")

        binder_path = Path(self.filepath)
        binder = Binder.from_path(binder_path)

        if not self.overwrite_existing and self.animation_id in binder.get_entry_ids():
            return self.error(f"Animation ID {self.animation_id} already exists in Binder and overwrite is disabled")

        skeleton_entry = binder.find_entry_matching_name(r"skeleton\.hkx", re.IGNORECASE)
        if skeleton_entry is None:
            return self.error("Could not find 'skeleton.hkx' in binder.")
        skeleton_hkx = SkeletonHKX.from_binder_entry(skeleton_entry)

        bl_armature = context.selected_objects[0]

        animation_name = get_animation_name(self.animation_id, self.name_template[1:], prefix=self.name_template[0])
        print(f"Animation name: {animation_name}")

        current_frame = context.scene.frame_current
        try:
            animation_hkx = create_animation_hkx(skeleton_hkx, bl_armature, self.from_60_fps)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Failed to create animation HKX: {ex}")
        finally:
            context.scene.frame_set(current_frame)

        animation_hkx.dcx_type = DCXType[self.dcx_type]

        entry_path = self.default_entry_path + animation_name + (".hkx" if self.dcx_type == "Null" else ".hkx.dcx")

        # Update or create binder entry.
        binder.add_or_replace_entry_data(self.animation_id, animation_hkx, new_path=entry_path)

        # Write modified binder back.
        binder.write()

        return {"FINISHED"}


class ExportCharacterHKXAnimation(LoggingOperator):
    """Export active animation from selected character Armature into that character's game ANIBND."""
    bl_idname = "export_scene.character_animation"
    bl_label = "Export Character Animation"
    bl_description = "Export active Action into its character's ANIBND"

    # TODO: expose somehow or auto-detect (from action + game)
    from_60_fps: bpy.props.BoolProperty(
        name="From 60 FPS",
        description="Scale animation keyframes from 60 FPS in Blender down to 30 FPS",
        default=True,
    )

    GAME_INFO = {
        GameNames.DS1R: {
            "animation_stem_template": "##_####",
            "hkx_entry_path": "N:\\FRPG\\data\\Model\\chr\\{character_name}\\hkxx64\\{animation_stem}.hkx",
            "hkx_dcx_type": DCXType.Null,
        }
    }

    @classmethod
    def poll(cls, context):
        if len(context.selected_objects) != 1:
            return False
        obj = context.selected_objects[0]
        if not obj.name.startswith("c"):
            return False
        if obj.type != "ARMATURE":
            return False
        if obj.animation_data is None:
            return False
        if obj.animation_data.action is None:
            return False
        return True

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select a single Armature of a character (name starting with 'c') with an Action.")

        settings = GlobalSettings.get_scene_settings(context)
        game_directory = settings.game_directory
        if not game_directory:
            return self.error("No game directory set in global Soulstruct Settings.")
        game_hkx_settings = self.GAME_INFO.get(settings.game, None)
        if game_hkx_settings is None:
            return self.error(f"Game '{settings.game}' not supported for automatic ANIBND export.")

        bl_armature = context.selected_objects[0]

        character_name = bl_armature.name.split(" ")[0]
        if character_name == "c0000":
            return self.error("Automatic ANIBND import is not yet supported for c0000 (player model).")

        # Get ANIBND.
        dcx = ".dcx" if settings.resolve_dcx_type("Auto", "BINDER") != DCXType.Null else ""
        anibnd_path = Path(game_directory, "chr", f"{character_name}.anibnd{dcx}")

        if not anibnd_path.is_file():
            return self.error(f"Cannot find ANIBND for character '{character_name}' in game directory.")

        skeleton_anibnd = anibnd = Binder.from_path(anibnd_path)
        # TODO: Support c0000 automatic import. Combine all sub-ANIBND entries into one big choice list?

        try:
            skeleton_entry = skeleton_anibnd[SKELETON_ENTRY_RE]
        except EntryNotFoundError:
            return self.error("Could not find 'skeleton.hkx' (case-insensitive) in ANIBND.")
        skeleton_hkx = SkeletonHKX.from_binder_entry(skeleton_entry)

        # Get animation stem from action name. We will re-format its ID in the selected game's known format (e.g. to
        # support cross-game conversion).
        action = bl_armature.animation_data.action
        animation_id_str = action.name.split("|")[-1].split(".")[0]  # e.g. from 'c1234|a00_0000.001' to 'a00_0000'
        animation_id_str = animation_id_str.lstrip("a")
        try:
            animation_id = int(animation_id_str)
        except ValueError:
            return self.error(f"Could not parse animation ID from action name '{action.name}'.")

        try:
            animation_name = get_animation_name(animation_id, game_hkx_settings["animation_stem_template"], prefix="a")
        except ValueError:
            max_digits = game_hkx_settings["animation_stem_template"].count("#")
            return self.error(
                f"Animation ID {animation_id} is too large for game {settings.game}. Max is {'9' * max_digits}."
            )

        self.info(f"Exporting animation '{animation_name} into ANIBND '{anibnd_path.name}'...")

        current_frame = context.scene.frame_current
        try:
            animation_hkx = create_animation_hkx(skeleton_hkx, bl_armature, self.from_60_fps)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Failed to create animation HKX. Error: {ex}")
        finally:
            context.scene.frame_set(current_frame)

        animation_hkx.dcx_type = settings.resolve_dcx_type("Auto", "HKX")
        entry_path = game_hkx_settings["hkx_entry_path"].format(
            character_name=character_name, animation_stem=animation_name
        )
        if animation_hkx.dcx_type != DCXType.Null:
            entry_path += ".dcx"

        # Update or create binder entry.
        anibnd.add_or_replace_entry_data(animation_id, animation_hkx, new_path=entry_path)

        # Write modified ANIBND back.
        anibnd.write()

        return {"FINISHED"}


class ExportObjectHKXAnimation(LoggingOperator):
    """Export active animation from selected object Armature into that object's game OBJBND."""
    bl_idname = "export_scene.object_animation"
    bl_label = "Export Object Animation"
    bl_description = "Export active Action into its object's OBJBND"

    # TODO: expose somehow or auto-detect (from action + game)
    from_60_fps: bpy.props.BoolProperty(
        name="From 60 FPS",
        description="Scale animation keyframes from 60 FPS in Blender down to 30 FPS",
        default=True,
    )

    GAME_INFO = {
        GameNames.DS1R: {
            "animation_stem_template": "##_####",
            "hkx_entry_path": "N:\\FRPG\\data\\Model\\obj\\{object_name}\\hkxx64\\{animation_stem}.hkx",
            "hkx_dcx_type": DCXType.Null,
        }
    }

    @classmethod
    def poll(cls, context):
        if len(context.selected_objects) != 1:
            return False
        obj = context.selected_objects[0]
        if not obj.name.startswith("o"):
            return False
        if obj.type != "ARMATURE":
            return False
        if obj.animation_data is None:
            return False
        if obj.animation_data.action is None:
            return False
        return True

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select a single Armature of a object (name starting with 'o') with an Action.")

        settings = GlobalSettings.get_scene_settings(context)
        game_directory = settings.game_directory
        if not game_directory:
            return self.error("No game directory set in global Soulstruct Settings.")
        game_hkx_settings = self.GAME_INFO.get(settings.game, None)
        if game_hkx_settings is None:
            return self.error(f"Game '{settings.game}' not supported for automatic ANIBND export.")

        bl_armature = context.selected_objects[0]

        object_name = bl_armature.name.split(" ")[0]

        # Get OBJBND.
        dcx = ".dcx" if settings.resolve_dcx_type("Auto", "BINDER") != DCXType.Null else ""
        objbnd_path = Path(game_directory, "obj", f"{object_name}.objbnd{dcx}")
        if not objbnd_path.is_file():
            return self.error(f"Cannot find OBJBND for object '{object_name}' in game directory.")
        objbnd = Binder.from_path(objbnd_path)

        # Find ANIBND entry.
        try:
            anibnd_entry = objbnd[f"{object_name}.anibnd"]
        except EntryNotFoundError:
            return self.error(f"OBJBND of object '{object_name}' has no ANIBND.")
        skeleton_anibnd = anibnd = Binder.from_binder_entry(anibnd_entry)

        # Find skeleton entry.
        try:
            skeleton_entry = skeleton_anibnd[SKELETON_ENTRY_RE]
        except EntryNotFoundError:
            return self.error("Could not find 'skeleton.hkx' (case-insensitive) in ANIBND.")
        skeleton_hkx = SkeletonHKX.from_binder_entry(skeleton_entry)

        # Get animation stem from action name. We will re-format its ID in the selected game's known format (e.g. to
        # support cross-game conversion).
        action = bl_armature.animation_data.action
        animation_id_str = action.name.split("|")[-1].split(".")[0]  # e.g. from 'c1234|a00_0000.001' to 'a00_0000'
        animation_id_str = animation_id_str.lstrip("a")
        try:
            animation_id = int(animation_id_str)
        except ValueError:
            return self.error(f"Could not parse animation ID from action name '{action.name}'.")

        try:
            animation_name = get_animation_name(animation_id, game_hkx_settings["animation_stem_template"], prefix="a")
        except ValueError:
            max_digits = game_hkx_settings["animation_stem_template"].count("#")
            return self.error(
                f"Animation ID {animation_id} is too large for game {settings.game}. Max is {'9' * max_digits}."
            )

        self.info(f"Exporting animation '{animation_name} into OBJBND '{objbnd_path.name}'...")

        current_frame = context.scene.frame_current
        try:
            animation_hkx = create_animation_hkx(skeleton_hkx, bl_armature, self.from_60_fps)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Failed to create animation HKX. Error: {ex}")
        finally:
            context.scene.frame_set(current_frame)

        animation_hkx.dcx_type = settings.resolve_dcx_type("Auto", "HKX")
        entry_path = game_hkx_settings["hkx_entry_path"].format(object_name=object_name, animation_stem=animation_name)
        if animation_hkx.dcx_type != DCXType.Null:
            entry_path += ".dcx"

        # Update or create binder entry.
        anibnd.add_or_replace_entry_data(animation_id, animation_hkx, new_path=entry_path)

        # Write modified ANIBND entry back.
        anibnd_entry.set_from_binary_file(anibnd)

        # Write modified OBJBND file back.
        objbnd.write()

        return {"FINISHED"}


def create_animation_hkx(skeleton_hkx: SkeletonHKX, bl_armature, from_60_fps: bool) -> AnimationHKX:
    if bl_armature.animation_data is None:
        raise HKXAnimationExportError(f"Armature '{bl_armature.name}' has no animation data.")
    action = bl_armature.animation_data.action
    if action is None:
        raise HKXAnimationExportError(f"Armature '{bl_armature.name}' has no action assigned to its animation data.")

    # TODO: Technically, animation export only needs a start/end frame range, since it samples location/bone pose
    #  on every single frame anyway and does NOT need to actually use the action FCurves!

    # Determine the frame range.
    # TODO: Export bool option to just read from current scene values, rather than checking action.
    start_frame = int(min(fcurve.range()[0] for fcurve in action.fcurves))
    end_frame = int(max(fcurve.range()[1] for fcurve in action.fcurves))

    # All frame interleaved transforms, in armature space.
    root_frames = []  # type: list[Vector4]
    armature_space_frames = []  # type: list[list[TRSTransform]]

    has_root_motion = False

    # Animation track order will match Blender bone order (which should come from FLVER).
    track_bone_mapping = list(range(len(skeleton_hkx.skeleton.bones)))

    # Evaluate all curves at every frame.
    for i, frame in enumerate(range(start_frame, end_frame + 1)):

        if from_60_fps and i % 2 == 1:
            # Skip every second frame to convert 60 FPS to 30 FPS (frame 0 should generally be keyframed).
            continue

        bpy.context.scene.frame_set(frame)
        armature_space_frame = []  # type: list[TRSTransform]

        # We collect root motion vectors, as we're not sure if any root motion exists yet.
        root_frames.append(BL_TO_GAME_VECTOR4(bl_armature.location))
        if len(root_frames) >= 2 and root_frames[-1] != root_frames[-2]:
            # Some actual root motion has appeared.
            has_root_motion = True

        for bone in skeleton_hkx.skeleton.bones:
            try:
                bl_bone = bl_armature.pose.bones[bone.name]
            except KeyError:
                raise HKXAnimationExportError(f"Bone '{bone.name}' in HKX skeleton not found in Blender armature.")
            armature_space_transform = BL_MATRIX_TO_GAME_TRS(bl_bone.matrix)
            armature_space_frame.append(armature_space_transform)

        armature_space_frames.append(armature_space_frame)

    animation_hkx = AnimationHKX.from_dsr_interleaved_template(
        skeleton_hkx=skeleton_hkx,
        interleaved_data=armature_space_frames,
        transform_track_to_bone_indices=track_bone_mapping,
        reference_frame_samples=root_frames if has_root_motion else None,
        is_armature_space=True,
    )

    return animation_hkx
