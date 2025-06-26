from __future__ import annotations

__all__ = [
    "ExportAnyHKXAnimation",
    "ExportHKXAnimationIntoAnyBinder",
    "ExportCharacterHKXAnimation",
    "ExportObjectHKXAnimation",
]

import re
import traceback
import typing as tp
from pathlib import Path

import bpy

from soulstruct.containers import Binder, EntryNotFoundError
from soulstruct.dcx import DCXType
from soulstruct.havok.fromsoft.base import BaseSkeletonHKX, BaseAnimationHKX

from soulstruct.blender.exceptions import *
from soulstruct.blender.flver.models import BlenderFLVER
from soulstruct.blender.utilities import *
from .utilities import *
from .types import SoulstructAnimation


SKELETON_ENTRY_RE = re.compile(r"skeleton\.hkx", re.IGNORECASE)


def _is_bl_flver_with_animation_data(obj: bpy.types.Object) -> tp.TypeGuard[bpy.types.MeshObject]:
    if not obj:
        return False
    try:
        bl_flver = BlenderFLVER.from_armature_or_mesh(obj)
    except SoulstructTypeError:
        return False
    return bool(bl_flver.armature and bl_flver.armature.animation_data and bl_flver.armature.animation_data.action)


class ExportAnyHKXAnimation(LoggingExportOperator):
    """Export loose HKX animation file from an Action attached to active FLVER Armature."""
    bl_idname = "export_scene.hkx_animation"
    bl_label = "Export Any HKX Animation"
    bl_description = "Export a Blender action to a standalone HKX animation file with manual HKX skeleton source"

    filename_ext = ".hkx"

    filter_glob: bpy.props.StringProperty(
        default="*.hkx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    hkx_skeleton_path: bpy.props.StringProperty(
        name="HKX Skeleton Path",
        description="Path to matching HKX skeleton file (required for animation export)",
        default="",
    )

    dcx_type: get_dcx_enum_property()

    force_interleaved: bpy.props.BoolProperty(
        name="Force Interleaved",
        description="Force exported animation format to be interleaved for manual inspection/usage",
        default=False,
    )

    @classmethod
    def poll(cls, context) -> bool:
        if not context.scene.soulstruct_settings.game_config.supports_animation:
            return False
        if not context.active_object:
            return False
        return _is_bl_flver_with_animation_data(context.active_object)

    def invoke(self, context, _event):
        """Set default filepath to name of Action after '|' separator, before first space, and without extension."""
        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        bl_animation = SoulstructAnimation(bl_flver.armature.animation_data.action)
        self.filepath = bl_animation.game_name + ".hkx"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        self.info("Executing HKX animation export...")

        settings = self.settings(context)
        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        bl_animation = SoulstructAnimation.from_armature_animation_data(bl_flver.armature)

        skeleton_hkx_class = settings.game_config.skeleton_hkx_class  # type: type[BaseSkeletonHKX]
        if skeleton_hkx_class is None:
            return self.error(f"No skeleton HKX class defined for game {settings.game.name}.")
        animation_hkx_class = settings.game_config.animation_hkx_class  # type: type[BaseAnimationHKX]
        if animation_hkx_class is None:
            return self.error(f"No animation HKX class defined for game {settings.game.name}.")

        animation_file_path = Path(self.filepath)

        skeleton_path = Path(self.hkx_skeleton_path)
        if not skeleton_path.is_file():
            return self.error(f"Invalid HKX skeleton path: {skeleton_path}")

        if skeleton_path.name.endswith(".hkx") or skeleton_path.name.endswith(".hkx.dcx"):
            skeleton_hkx = skeleton_hkx_class.from_path(skeleton_path)
        else:
            try:
                skeleton_binder = Binder.from_path(skeleton_path)
            except ValueError:
                return self.error(f"Could not load file as a `SkeletonHKX` or `Binder`: {skeleton_path}")
            try:
                skeleton_entry = skeleton_binder[SKELETON_ENTRY_RE]
            except EntryNotFoundError:
                return self.error(f"Could not find `skeleton.hkx` (case-insensitive) in binder: '{skeleton_path}'")
            skeleton_hkx = skeleton_hkx_class.from_binder_entry(skeleton_entry)

        current_frame = context.scene.frame_current  # store for resetting after export
        try:
            animation_hkx = bl_animation.to_game_compressed_animation(
                self,
                context,
                settings.game,
                bl_flver.armature,
                skeleton_hkx,
                animation_hkx_class,
                self.force_interleaved,
            )
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Failed to create animation HKX. Error: {ex}")
        finally:
            context.scene.frame_set(current_frame)

        dcx_type = settings.resolve_dcx_type(self.dcx_type, "hkx")
        animation_hkx.dcx_type = dcx_type
        animation_hkx.write(animation_file_path)

        return {"FINISHED"}


class ExportHKXAnimationIntoAnyBinder(LoggingImportOperator):
    """Export HKX animation from an Action attached to a FLVER armature, into an existing BND."""
    bl_idname = "export_scene.hkx_animation_binder"
    bl_label = "Export HKX Animation Into Any Binder"
    bl_description = "Export a Blender action to a HKX animation file inside a FromSoftware Binder (BND/BHD)"

    filter_glob: bpy.props.StringProperty(
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

    animation_id: bpy.props.IntProperty(
        name="Animation ID",
        description="Animation ID for name and Binder entry ID to use",
        default=0,
        min=0,
    )

    overwrite_existing: bpy.props.BoolProperty(
        name="Overwrite Existing",
        description="Allow existing animation with this ID to be overwritten",
        default=True,
    )

    default_entry_path: bpy.props.StringProperty(
        name="Default Path",
        description="Path to use for Binder entry if it needs to be created. Default is for DS1R `anibnd.dcx` files",
        default="N:\\FRPG\\data\\Model\\chr\\{name}\\hkxx64\\",
    )

    name_template: bpy.props.StringProperty(
        name="Animation Name Template",
        description="Template for converting animation ID to entry name",
        default="a##_####",  # default for DS1
    )

    force_interleaved: bpy.props.BoolProperty(
        name="Force Interleaved",
        description="Force exported animation format to be interleaved for manual inspection/usage",
        default=False,
    )

    @classmethod
    def poll(cls, context) -> bool:
        if not context.scene.soulstruct_settings.game_config.supports_animation:
            return False
        if not context.active_object:
            return False
        try:
            bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        except SoulstructTypeError:
            return False
        return bool(bl_flver.armature and bl_flver.armature.animation_data and bl_flver.armature.animation_data.action)

    def execute(self, context):
        settings = self.settings(context)
        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        bl_animation = SoulstructAnimation.from_armature_animation_data(bl_flver.armature)

        skeleton_hkx_class = settings.game_config.skeleton_hkx_class  # type: type[BaseSkeletonHKX]
        if skeleton_hkx_class is None:
            return self.error(f"No skeleton HKX class defined for game {settings.game.name}.")
        animation_hkx_class = settings.game_config.animation_hkx_class  # type: type[BaseAnimationHKX]
        if animation_hkx_class is None:
            return self.error(f"No animation HKX class defined for game {settings.game.name}.")

        binder_path = Path(self.filepath)
        binder = Binder.from_path(binder_path)

        if not self.overwrite_existing and self.animation_id in binder.get_entry_ids():
            return self.error(f"Animation ID {self.animation_id} already exists in Binder and overwrite is disabled")

        skeleton_entry = binder.find_entry_matching_name(r"skeleton\.hkx", re.IGNORECASE)
        if skeleton_entry is None:
            return self.error("Could not find 'skeleton.hkx' in binder.")
        skeleton_hkx = skeleton_hkx_class.from_binder_entry(skeleton_entry)

        animation_name = get_animation_name(self.animation_id, self.name_template[1:], prefix=self.name_template[0])
        self.info(f"Exporting animation '{animation_name}' into binder {binder_path.name}...")

        current_frame = context.scene.frame_current
        try:
            animation_hkx = bl_animation.to_game_compressed_animation(
                self,
                context,
                settings.game,
                bl_flver.armature,
                skeleton_hkx,
                animation_hkx_class,
                self.force_interleaved,
            )
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Failed to create animation HKX. Error: {ex}")
        finally:
            context.scene.frame_set(current_frame)

        dcx_type = DCXType.Null if self.dcx_type == "AUTO" else DCXType.from_member_name(self.dcx_type)
        animation_hkx.dcx_type = dcx_type
        entry_path = self.default_entry_path + animation_name + (".hkx" if dcx_type == DCXType.Null else ".hkx.dcx")
        # Update or create binder entry.
        binder.set_default_entry(self.animation_id, new_path=entry_path).set_from_binary_file(animation_hkx)

        # Write modified binder back.
        binder.write()

        return {"FINISHED"}


class BaseExportTypedHKXAnimation(LoggingOperator):

    @classmethod
    def poll(cls, context) -> bool:
        settings = cls.settings(context)
        if not settings.game_config.supports_animation:
            return False
        if not settings.can_auto_export:
            return False
        if not context.active_object:
            return False
        obj = context.active_object
        try:
            bl_flver = BlenderFLVER.from_armature_or_mesh(obj)
        except SoulstructTypeError:
            return False
        return bool(bl_flver.armature and bl_flver.armature.animation_data and bl_flver.armature.animation_data.action)


class ExportCharacterHKXAnimation(BaseExportTypedHKXAnimation):
    """Export active animation from selected character Armature into that character's game ANIBND."""
    bl_idname = "export_scene.hkx_character_animation"
    bl_label = "Export Character Anim"
    bl_description = (
        "Export active Action into its character's ANIBND. For c0000, the best available sub-ANIBND will be chosen "
        "automatically based on animation ID. Use 'Export HKX Anim into Binder' for manual choice"
    )

    force_interleaved: bpy.props.BoolProperty(
        name="Force Interleaved",
        description="Force exported animation format to be interleaved for manual inspection/usage",
        default=False,
    )

    @classmethod
    def poll(cls, context) -> bool:
        return super().poll(context) and context.active_object.name[0] == "c"

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select a single Armature of a character (name starting with 'c') with an Action.")

        settings = self.settings(context)
        try:
            game_anim_info = SoulstructAnimation.GAME_ANIMATION_INFO_CHR[settings.game]
        except KeyError:
            return self.error(f"Automatic ANIBND export is not yet supported for game {settings.game.name}.")

        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        bl_animation = SoulstructAnimation.from_armature_animation_data(bl_flver.armature)

        skeleton_hkx_class = settings.game_config.skeleton_hkx_class  # type: type[BaseSkeletonHKX]
        if skeleton_hkx_class is None:
            return self.error(f"No skeleton HKX class defined for game {settings.game.name}.")
        animation_hkx_class = settings.game_config.animation_hkx_class  # type: type[BaseAnimationHKX]
        if animation_hkx_class is None:
            return self.error(f"No animation HKX class defined for game {settings.game.name}.")

        model_name = bl_flver.game_name

        relative_anibnd_path = Path(game_anim_info.relative_binder_path.format(model_name=model_name))
        try:
            # NOTE: We don't use the managed `ANIBND` class from `soulstruct-havok` here.
            anibnd = settings.get_initial_binder(self, relative_anibnd_path)
        except FileNotFoundError as ex:
            return self.error(f"Cannot find ANIBND for character {model_name}: {ex}")

        # Skeleton is in ANIBND.
        skeleton_anibnd = anibnd
        try:
            skeleton_entry = skeleton_anibnd[SKELETON_ENTRY_RE]
        except EntryNotFoundError:
            return self.error("Could not find 'skeleton.hkx' (case-insensitive) in ANIBND.")
        skeleton_hkx = skeleton_hkx_class.from_binder_entry(skeleton_entry)

        # Get animation stem from action name. We will re-format its ID in the selected game's known format (e.g. to
        # support cross-game conversion).
        animation_id = bl_animation.animation_id

        if model_name == "c0000":
            sub_anibnd_stems = [entry.stem for entry in anibnd.find_entries_matching_name(r"c0000_.*\.txt")]
            if not sub_anibnd_stems:
                return self.error("Could not find any sub-ANIBND definitions (e.g. 'c0000_a0x.txt') in c0000 ANIBND.")
            # For now, we keep it simple: load ALL sub-ANIBNDs, find the one with a matching animation ID to replace,
            # and fall back to using either `c0000_dlc` or `c0000_a9x` if no existing animation is found.
            for stem in sub_anibnd_stems:
                relative_sub_anibnd_path = Path(game_anim_info.relative_binder_path.format(model_name=stem))
                try:
                    sub_anibnd = settings.get_initial_binder(self, relative_sub_anibnd_path)
                except FileNotFoundError as ex:
                    return self.error(f"Cannot find sub-ANIBND for c0000: '{relative_sub_anibnd_path}'. Error: {ex}")
                if animation_id in sub_anibnd.get_entry_ids():
                    # Found matching animation. We export our new animation into this sub ANIBND.
                    self.info(f"Will replace existing animation ID {animation_id} in c0000 sub-ANIBND `{stem}`.")
                    anibnd = sub_anibnd
                    relative_anibnd_path = relative_sub_anibnd_path
                    break
            else:
                # Could not find existing animation ID in any sub-ANIBND. Fall back to DLC or a9x.
                for stem_option in ["c0000_dlc02", "c0000_dlc", "c0000_a9x"]:
                    if stem_option not in sub_anibnd_stems:
                        continue
                    relative_sub_anibnd_path = Path(game_anim_info.relative_binder_path.format(model_name=stem_option))
                    try:
                        anibnd = settings.get_initial_binder(self, relative_sub_anibnd_path)
                        relative_anibnd_path = relative_sub_anibnd_path
                    except FileNotFoundError:
                        continue  # try next option
                else:
                    return self.error(
                        f"Could not find any sub-ANIBND with existing animation ID {animation_id} for c0000, and could "
                        f"not find a backup sub-ANIBND ('c0000_dlc02', 'c0000_dlc', 'c0000_a9x') to export into."
                    )

        try:
            animation_name = get_animation_name(animation_id, game_anim_info.stem_template, prefix="a")
        except ValueError:
            max_digits = game_anim_info.stem_template.count("#")
            return self.error(
                f"Animation ID {animation_id} is too large for game {settings.game}. Max is {'9' * max_digits}."
            )

        self.info(f"Exporting animation '{animation_name}' into ANIBND '{anibnd.path_name}'...")

        current_frame = context.scene.frame_current
        try:
            animation_hkx = bl_animation.to_game_compressed_animation(
                self,
                context,
                settings.game,
                bl_flver.armature,
                skeleton_hkx,
                animation_hkx_class,
                self.force_interleaved,
            )
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Failed to create animation HKX. Error: {ex}")
        finally:
            context.scene.frame_set(current_frame)

        animation_hkx.dcx_type = game_anim_info.dcx_type
        entry_path = animation_hkx.dcx_type.process_path(
            game_anim_info.hkx_entry_path.format(model_name=model_name, animation_stem=animation_name)
        )

        # Update or create binder entry.
        anibnd.set_default_entry(animation_id, new_path=entry_path).set_from_binary_file(animation_hkx)
        self.info(f"Successfully exported animation '{animation_name}' into ANIBND {anibnd.path_name}.")

        # Write modified ANIBND.
        exported_paths = settings.export_file(self, anibnd, relative_anibnd_path)
        return {"FINISHED" if exported_paths else "CANCELLED"}


class ExportObjectHKXAnimation(BaseExportTypedHKXAnimation):
    """Export active animation from selected object Armature into that object's game OBJBND."""
    bl_idname = "export_scene.object_hkx_animation"
    bl_label = "Export Object Anim"
    bl_description = "Export active Action into its object's OBJBND"

    force_interleaved: bpy.props.BoolProperty(
        name="Force Interleaved",
        description="Force exported animation format to be interleaved for manual inspection/usage",
        default=False,
    )

    @classmethod
    def poll(cls, context) -> bool:
        return super().poll(context) and context.active_object.name[0] == "o"

    def execute(self, context):
        settings = self.settings(context)

        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        bl_animation = SoulstructAnimation.from_armature_animation_data(bl_flver.armature)
        model_name = bl_flver.game_name

        try:
            game_anim_info = SoulstructAnimation.GAME_ANIMATION_INFO_OBJ[settings.game]
        except KeyError:
            return self.error(f"Automatic OBJBND + ANIBND export is not yet supported for game {settings.game.name}.")

        skeleton_hkx_class = settings.game_config.skeleton_hkx_class  # type: type[BaseSkeletonHKX]
        if skeleton_hkx_class is None:
            return self.error(f"No skeleton HKX class defined for game {settings.game.name}.")
        animation_hkx_class = settings.game_config.animation_hkx_class  # type: type[BaseAnimationHKX]
        if animation_hkx_class is None:
            return self.error(f"No animation HKX class defined for game {settings.game.name}.")

        # Get OBJBND to modify from project (preferred) or game directory.
        relative_objbnd_path = Path(game_anim_info.relative_binder_path.format(model_name=model_name))
        try:
            objbnd = settings.get_initial_binder(self, relative_objbnd_path)  # don't need OBJBND class here
        except FileNotFoundError:
            return self.error(f"Cannot find OBJBND for object {model_name}.")

        # Find ANIBND entry inside OBJBND.
        try:
            anibnd_entry = objbnd[f"{model_name}.anibnd"]  # no DCX
        except EntryNotFoundError:
            return self.error(f"OBJBND for object {model_name} has no ANIBND entry.")
        skeleton_anibnd = anibnd = Binder.from_binder_entry(anibnd_entry)

        # Find skeleton entry.
        try:
            skeleton_entry = skeleton_anibnd[SKELETON_ENTRY_RE]
        except EntryNotFoundError:
            return self.error("Could not find 'skeleton.hkx' (case-insensitive) in ANIBND inside OBJBND.")
        skeleton_hkx = skeleton_hkx_class.from_binder_entry(skeleton_entry)

        # Get animation stem from action name. We will re-format its ID in the selected game's known format (e.g. to
        # support cross-game conversion).
        animation_id_str = bl_animation.animation_stem
        animation_id_str = animation_id_str.lstrip("a")
        try:
            animation_id = int(animation_id_str)
        except ValueError:
            return self.error(f"Could not parse animation ID from action name '{bl_animation.name}'.")

        try:
            animation_name = get_animation_name(animation_id, game_anim_info.stem_template, prefix="a")
        except ValueError:
            max_digits = game_anim_info.stem_template.count("#")
            return self.error(
                f"Animation ID {animation_id} is too large for game {settings.game}. Max is {'9' * max_digits}."
            )

        self.info(f"Exporting animation {animation_name} into OBJBND {objbnd.path_name}...")

        current_frame = context.scene.frame_current
        try:
            animation_hkx = bl_animation.to_game_compressed_animation(
                self,
                context,
                settings.game,
                bl_flver.armature,
                skeleton_hkx,
                animation_hkx_class,
                self.force_interleaved,
            )
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Failed to create animation HKX. Error: {ex}")
        finally:
            context.scene.frame_set(current_frame)

        animation_hkx.dcx_type = DCXType.Null  # no DCX inside OBJBND/ANIBND
        entry_path = animation_hkx.dcx_type.process_path(
            game_anim_info.hkx_entry_path.format(model_name=model_name, animation_stem=animation_name)
        )

        # Update or create binder entry.
        anibnd.set_default_entry(animation_id, new_path=entry_path).set_from_binary_file(animation_hkx)

        # Write modified ANIBND entry back into OBJBND.
        anibnd_entry.set_from_binary_file(anibnd)

        # Export modified OBJBND.
        exported_paths = settings.export_file(self, objbnd, relative_objbnd_path)
        return {"FINISHED" if exported_paths else "CANCELLED"}


# TODO: Export Asset animation. Requires general ER support, obviously.
