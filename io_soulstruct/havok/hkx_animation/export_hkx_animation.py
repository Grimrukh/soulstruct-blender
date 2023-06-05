from __future__ import annotations

__all__ = ["ExportHKXAnimation", "ExportHKXAnimationIntoBinder"]

import re
import traceback
from pathlib import Path

import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper

from soulstruct.containers import Binder, BinderFlags, DCXType
from soulstruct_havok.wrappers.hkx2015 import SkeletonHKX, AnimationHKX
from soulstruct_havok.utilities.maths import Vector4, TRSTransform

from io_soulstruct.utilities import *
from io_soulstruct.havok.utilities import BL_MATRIX_TO_GAME_TRS
from .utilities import *


BONE_DATA_PATH_RE = re.compile(r"pose\.bones\[(\w+)]\.(location|rotation_quaterion|scale)")


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
            # Skip every second frame (frame 0 should generally be keyframed).
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


class ExportHKXAnimation(LoggingOperator, ExportHelper):
    """Export HKX animation from an Action attached to a FLVER armature."""
    bl_idname = "export_scene.hkx_animation"
    bl_label = "Export HKX Animation"
    bl_description = "Export a Blender action to a standalone HKX animation file"

    # ExportHelper mixin class uses this
    filename_ext = ".hkx"

    filter_glob: StringProperty(
        default="*.hkx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    hkx_skeleton_path: StringProperty(
        name="HKX Skeleton Path",
        description="Path to HKX skeleton file (required for animation)",
        default="",
    )

    from_60_fps: bpy.props.BoolProperty(
        name="From 60 FPS",
        description="Scale animation keyframes from 60 FPS in Blender down to 30 FPS",
        default=True,
    )

    dcx_type: EnumProperty(
        name="Compression",
        items=[
            ("Null", "None", "Export without any DCX compression"),
            ("DCX_EDGE", "DES", "Demon's Souls compression"),
            ("DCX_DFLT_10000_24_9", "DS1/DS2", "Dark Souls 1/2 compression"),
            ("DCX_DFLT_10000_44_9", "BB/DS3", "Bloodborne/Dark Souls 3 compression"),
            ("DCX_DFLT_11000_44_9", "Sekiro", "Sekiro compression (requires Oodle DLL)"),
            ("DCX_KRAK", "Elden Ring", "Elden Ring compression (requires Oodle DLL)"),
        ],
        description="Type of DCX compression to apply to exported file",
        default="DCX_DFLT_10000_24_9",  # DS1 default
    )

    @classmethod
    def poll(cls, context):
        try:
            return context.selected_objects[0].type == "ARMATURE"
        except IndexError:
            return False

    def execute(self, context):
        print("Executing HKX animation export...")

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
            skeleton_entry = skeleton_binder.find_entry_matching_name(r"skeleton\.hkx", re.IGNORECASE)
            if skeleton_entry is None:
                return self.error(f"Could not find skeleton.hkx in binder: '{skeleton_path}'")
            skeleton_hkx = SkeletonHKX.from_binder_entry(skeleton_entry)

        bl_armature = context.selected_objects[0]

        try:
            animation_hkx = create_animation_hkx(skeleton_hkx, bl_armature, self.from_60_fps)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Failed to create animation HKX: {ex}")

        animation_hkx.dcx_type = DCXType[self.dcx_type]

        animation_hkx.write(animation_file_path)

        return {'FINISHED'}


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

    dcx_type: EnumProperty(
        name="Compression",
        items=[
            ("Null", "None", "Export without any DCX compression"),
            ("DCX_EDGE", "DES", "Demon's Souls compression"),
            ("DCX_DFLT_10000_24_9", "DS1/DS2", "Dark Souls 1/2 compression"),
            ("DCX_DFLT_10000_44_9", "BB/DS3", "Bloodborne/Dark Souls 3 compression"),
            ("DCX_DFLT_11000_44_9", "Sekiro", "Sekiro compression (requires Oodle DLL)"),
            ("DCX_KRAK", "Elden Ring", "Elden Ring compression (requires Oodle DLL)"),
        ],
        description="Type of DCX compression to apply to exported file (typically not used in Binder)",
        default="Null",  # typically no DCX compression inside Binder
    )

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

    # TODO: Probably need a template for the 'aXX_XXXX' animation name (number of digits per chunk, etc.).

    @classmethod
    def poll(cls, context):
        try:
            return context.selected_objects[0].type == "ARMATURE"
        except IndexError:
            return False

    def execute(self, context):
        print("Executing HKX animation export into Binder...")

        binder = Binder.from_path(Path(self.filepath))

        if not self.overwrite_existing and self.animation_id in binder.entries_by_id:
            return self.error(f"Animation ID {self.animation_id} already exists in Binder and overwrite is disabled")

        skeleton_entry = binder.find_entry_matching_name(r"skeleton\.hkx", re.IGNORECASE)
        if skeleton_entry is None:
            return self.error("Could not find 'skeleton.hkx' in binder.")
        skeleton_hkx = SkeletonHKX.from_binder_entry(skeleton_entry)

        bl_armature = context.selected_objects[0]

        animation_name = get_animation_name(self.animation_id, self.name_template[1:], prefix=self.name_template[0])
        print(f"Animation name: {animation_name}")

        try:
            animation_hkx = create_animation_hkx(skeleton_hkx, bl_armature, self.from_60_fps)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Failed to create animation HKX: {ex}")

        animation_hkx.dcx_type = DCXType[self.dcx_type]

        entry_path = self.default_entry_path + animation_name + (".hkx" if self.dcx_type == "Null" else ".hkx.dcx")

        # Update or create binder entry.
        binder.add_or_replace_entry_id(self.animation_id, animation_hkx, entry_path, BinderFlags(0x2))

        # Write modified binder back.
        binder.write()

        return {'FINISHED'}
