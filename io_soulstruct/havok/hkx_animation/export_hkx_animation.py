from __future__ import annotations

__all__ = [
    "ExportLooseHKXAnimation",
    "ExportHKXAnimationIntoBinder",
    "QuickExportCharacterHKXAnimation",
    "QuickExportObjectHKXAnimation",
]

import re
import traceback
from pathlib import Path

import numpy as np

import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper

from soulstruct.containers import Binder, EntryNotFoundError
from soulstruct.dcx import DCXType
from soulstruct.games import DARK_SOULS_DSR
from soulstruct_havok.wrappers.hkx2015 import SkeletonHKX, AnimationHKX
from soulstruct_havok.utilities.maths import TRSTransform

from io_soulstruct.utilities import *
from io_soulstruct.havok.utilities import BL_MATRIX_TO_GAME_TRS
from .utilities import *


ACTION_NAME_RE = re.compile(r"^(.*)\|(a[\d_]+)(\.\d+)?$")
BONE_DATA_PATH_RE = re.compile(r"pose\.bones\[(\w+)]\.(location|rotation_quaterion|scale)")
SKELETON_ENTRY_RE = re.compile(r"skeleton\.hkx", re.IGNORECASE)


class ExportLooseHKXAnimation(LoggingOperator, ExportHelper):
    """Export loose HKX animation file from an Action attached to a FLVER armature."""
    bl_idname = "export_scene.hkx_animation"
    bl_label = "Export Loose HKX Anim"
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

    def invoke(self, context, _event):
        """Set default filepath to name of Action after '|' separator, before first space, and without extension."""
        if not context.selected_objects:
            return super().invoke(context, _event)

        obj = context.selected_objects[0]
        if not obj.type == "ARMATURE" or obj.animation_data is None or obj.animation_data.action is None:
            return super().invoke(context, _event)
        action = obj.animation_data.action
        self.filepath = action.name.split("|")[-1].split(" ")[0].split(".")[0] + ".hkx"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        self.info("Executing HKX animation export...")

        settings = self.settings(context)

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

        dcx_type = settings.resolve_dcx_type(self.dcx_type, "hkx")
        animation_hkx.dcx_type = dcx_type
        animation_hkx.write(animation_file_path)

        return {"FINISHED"}


class ExportHKXAnimationIntoBinder(LoggingOperator, ImportHelper):
    """Export HKX animation from an Action attached to a FLVER armature, into an existing BND."""
    bl_idname = "export_scene.hkx_animation_binder"
    bl_label = "Export HKX Anim Into Binder"
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
        self.info(f"Exporting animation '{animation_name}' into binder {binder_path.name}...")

        current_frame = context.scene.frame_current
        try:
            animation_hkx = create_animation_hkx(skeleton_hkx, bl_armature, self.from_60_fps)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Failed to create animation HKX: {ex}")
        finally:
            context.scene.frame_set(current_frame)

        dcx_type = DCXType.Null if self.dcx_type == "Auto" else DCXType[self.dcx_type]
        animation_hkx.dcx_type = dcx_type
        entry_path = self.default_entry_path + animation_name + (".hkx" if dcx_type == DCXType.Null else ".hkx.dcx")
        # Update or create binder entry.
        binder.set_default_entry(self.animation_id, new_path=entry_path, new_data=bytes(animation_hkx))

        # Write modified binder back.
        binder.write()

        return {"FINISHED"}


class QuickExportCharacterHKXAnimation(LoggingOperator):
    """Export active animation from selected character Armature into that character's game ANIBND."""
    bl_idname = "export_scene.quick_hkx_character_animation"
    bl_label = "Export Character Anim"
    bl_description = "Export active Action into its character's ANIBND"

    # TODO: expose somehow or auto-detect (from action + game)
    from_60_fps: bpy.props.BoolProperty(
        name="From 60 FPS",
        description="Scale animation keyframes from 60 FPS in Blender down to 30 FPS",
        default=True,
    )

    # TODO: Hard-coding defaults for DSR (only supported game for now).
    ANIMATION_STEM_TEMPLATE = "##_####"
    HKX_ENTRY_PATH = "N:\\FRPG\\data\\Model\\chr\\{character_name}\\hkxx64\\{animation_stem}.hkx"
    HKX_DCX_TYPE = DCXType.Null

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)
        if not settings.is_game(DARK_SOULS_DSR):
            return False
        if not settings.can_auto_export:
            return False
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

        settings = self.settings(context)
        if settings.game_variable_name != "DARK_SOULS_DSR":
            return self.error(f"Game '{settings.game}' not supported for automatic ANIBND export.")

        bl_armature = context.selected_objects[0]

        character_name = get_bl_obj_stem(bl_armature)
        if character_name == "c0000":
            return self.error("Automatic ANIBND import is not yet supported for c0000 (player model).")

        relative_anibnd_path = Path(f"chr/{character_name}.anibnd")
        settings.prepare_project_file(relative_anibnd_path, False, must_exist=True)
        anibnd_path = settings.get_project_or_game_path(relative_anibnd_path)
        if not anibnd_path or not anibnd_path.is_file():
            return self.error(f"Cannot find ANIBND for character {character_name}: {anibnd_path}")

        # Skeleton is in ANIBND.
        skeleton_anibnd = anibnd = Binder.from_path(anibnd_path)
        # TODO: Support c0000 automatic export. Choose ANIBND based on animation ID?

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
            animation_name = get_animation_name(animation_id, self.ANIMATION_STEM_TEMPLATE, prefix="a")
        except ValueError:
            max_digits = self.ANIMATION_STEM_TEMPLATE.count("#")
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

        animation_hkx.dcx_type = self.HKX_DCX_TYPE
        entry_path = animation_hkx.dcx_type.process_path(
            self.HKX_ENTRY_PATH.format(character_name=character_name, animation_stem=animation_name)
        )

        # Update or create binder entry.
        anibnd.set_default_entry(animation_id, new_path=entry_path, new_data=animation_hkx)
        self.info(f"Successfully exported animation {animation_name} into ANIBND {anibnd_path.name}.")

        # Write modified ANIBND.
        return settings.export_file(self, anibnd, Path(f"chr/{anibnd_path.name}"))


class QuickExportObjectHKXAnimation(LoggingOperator):
    """Export active animation from selected object Armature into that object's game OBJBND."""
    bl_idname = "export_scene.quick_hkx_object_animation"
    bl_label = "Export Object Anim"
    bl_description = "Export active Action into its object's OBJBND"

    # TODO: expose somehow or auto-detect (from action + game)
    from_60_fps: bpy.props.BoolProperty(
        name="From 60 FPS",
        description="Scale animation keyframes from 60 FPS in Blender down to 30 FPS",
        default=True,
    )

    # TODO: Hard-coding defaults for DSR (only supported game for now).
    ANIMATION_STEM_TEMPLATE = "##_####"
    HKX_ENTRY_PATH = "N:\\FRPG\\data\\Model\\chr\\{character_name}\\hkxx64\\{animation_stem}.hkx"
    HKX_DCX_TYPE = DCXType.Null

    @classmethod
    def poll(cls, context):
        if cls.settings(context).game_variable_name != "DARK_SOULS_DSR":
            return False
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
        settings = self.settings(context)
        if settings.game_variable_name != "DARK_SOULS_DSR":
            return self.error(f"Game '{settings.game}' not supported for automatic ANIBND export.")
        if not self.poll(context):
            return self.error("Must select a single Armature of a object (name starting with 'o') with an Action.")

        bl_armature = context.selected_objects[0]
        object_name = get_bl_obj_stem(bl_armature)

        # Get OBJBND to modify from export (preferred) or import directory.
        relative_objbnd_path = Path(f"obj/{object_name}.objbnd")
        settings.prepare_project_file(relative_objbnd_path, False, must_exist=True)
        objbnd_path = settings.get_project_or_game_path(relative_objbnd_path)
        if not objbnd_path or not objbnd_path.is_file():
            return self.error(f"Cannot find OBJBND for object {object_name}: {objbnd_path}")
        objbnd = Binder.from_path(objbnd_path)

        # Find ANIBND entry.
        try:
            anibnd_entry = objbnd[f"{object_name}.anibnd"]  # no DCX
        except EntryNotFoundError:
            return self.error(f"OBJBND for object {object_name} has no ANIBND entry.")
        skeleton_anibnd = anibnd = Binder.from_binder_entry(anibnd_entry)

        # Find skeleton entry.
        try:
            skeleton_entry = skeleton_anibnd[SKELETON_ENTRY_RE]
        except EntryNotFoundError:
            return self.error("Could not find 'skeleton.hkx' (case-insensitive) in ANIBND inside OBJBND.")
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
            animation_name = get_animation_name(animation_id, self.ANIMATION_STEM_TEMPLATE, prefix="a")
        except ValueError:
            max_digits = self.ANIMATION_STEM_TEMPLATE.count("#")
            return self.error(
                f"Animation ID {animation_id} is too large for game {settings.game}. Max is {'9' * max_digits}."
            )

        self.info(f"Exporting animation {animation_name} into OBJBND {objbnd_path.name}...")

        current_frame = context.scene.frame_current
        try:
            animation_hkx = create_animation_hkx(skeleton_hkx, bl_armature, self.from_60_fps)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Failed to create animation HKX. Error: {ex}")
        finally:
            context.scene.frame_set(current_frame)

        animation_hkx.dcx_type = DCXType.Null  # no DCX inside OBJBND/ANIBND
        entry_path = animation_hkx.dcx_type.process_path(
            self.HKX_ENTRY_PATH.format(object_name=object_name, animation_stem=animation_name)
        )

        # Update or create binder entry.
        anibnd.set_default_entry(animation_id, new_path=entry_path, new_data=bytes(animation_hkx))

        # Write modified ANIBND entry back.
        anibnd_entry.set_from_binary_file(anibnd)

        # Export modified OBJBND.
        return settings.export_file(self, objbnd, Path(f"obj/{objbnd_path.name}"))


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
    root_motion_samples = []  # type: list[tuple[float, float, float]]
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
        root_motion_samples.append(bl_armature.location.copy())
        if not has_root_motion and len(root_motion_samples) >= 2 and root_motion_samples[-1] != root_motion_samples[-2]:
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

    if has_root_motion:
        root_motion = np.array(root_motion_samples, dtype=np.float32)
        # Swap Y and Z and add fourth column of zeroes.
        root_motion = np.c_[
            root_motion[:, 0], root_motion[:, 2], root_motion[:, 1], np.zeros(len(root_motion), dtype=np.float32)
        ]
    else:
        root_motion = None

    animation_hkx = AnimationHKX.from_dsr_interleaved_template(
        skeleton_hkx=skeleton_hkx,
        interleaved_data=armature_space_frames,
        transform_track_to_bone_indices=track_bone_mapping,
        root_motion=root_motion,
        is_armature_space=True,
    )

    return animation_hkx
