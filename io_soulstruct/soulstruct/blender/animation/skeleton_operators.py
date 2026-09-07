from __future__ import annotations

__all__ = [
    "ExportCharacterHKXSkeleton",
    "ExportObjectHKXSkeleton",
    "ExportHKXSkeletonIntoAnyBinder",
]

import re
import traceback
from pathlib import Path

import bpy

from soulstruct.containers import Binder, EntryNotFoundError
from soulstruct.havok.fromsoft.base import BaseSkeletonHKX

from ..base.operators import LoggingOperator, LoggingImportOperator
from ..base.register import io_soulstruct_operator
from ..exceptions import SoulstructTypeError
from ..flver.models import BlenderFLVER
from ..flver.models.types import FLVERBoneDataType
from ..types import ArmatureObject
from .skeleton import *
from .types import SoulstructAnimation
from .utilities import SKELETON_TYPING


SKELETON_ENTRY_RE = re.compile(r"skeleton\.hkx", re.IGNORECASE)


class _BaseExportHKXSkeleton(LoggingOperator):
    """Shared bone-source resolution and skeleton-building logic for all HKX skeleton export operators.

    Bone source options are read from `Scene.animation_export_settings` (drawn in the Animation panel).
    """

    @staticmethod
    def get_flver_armature(context: bpy.types.Context) -> ArmatureObject | None:
        """Return the FLVER Armature of the active object, if it is a dynamic (Edit Bone) FLVER."""
        obj = context.active_object
        if not obj:
            return None
        try:
            bl_flver = BlenderFLVER.from_armature_or_mesh(obj)
        except SoulstructTypeError:
            return None
        if not bl_flver.armature:
            return None
        if bl_flver.bone_data_type != FLVERBoneDataType.EDIT:
            # Static FLVERs keep their bone transforms in Pose Bones and never use HKX skeletons.
            return None
        return bl_flver.armature

    @classmethod
    def poll(cls, context) -> bool:
        if not context.scene.soulstruct_settings.game_config.supports_animation:
            return False
        return cls.get_flver_armature(context) is not None

    def build_skeleton_hkx(
        self,
        context: bpy.types.Context,
        armature: ArmatureObject,
        template_skeleton_hkx: SKELETON_TYPING,
    ) -> SKELETON_TYPING | None:
        """Rewrite `template_skeleton_hkx` bone data from `armature`. Returns `None` if an error was reported."""
        export_settings = context.scene.animation_export_settings

        try:
            bl_bone_names = get_hkx_skeleton_bone_names(
                self,
                armature,
                template_skeleton_hkx,
                HKXSkeletonBoneSource(export_settings.skeleton_bone_source),
                export_settings.skeleton_include_ancestor_bones,
            )
        except ValueError as ex:
            self.error(f"Could not resolve bones for HKX skeleton export: {ex}")
            return None

        try:
            return write_armature_to_skeleton_hkx(self, armature, template_skeleton_hkx, bl_bone_names)
        except Exception as ex:
            traceback.print_exc()
            self.error(f"Failed to generate HKX skeleton from Armature '{armature.name}'. Error: {ex}")
            return None


@io_soulstruct_operator
class ExportCharacterHKXSkeleton(_BaseExportHKXSkeleton):
    """Generate a new HKX skeleton from the active character FLVER Armature and write it into its game ANIBND."""
    bl_idname = "export_scene.hkx_character_skeleton"
    bl_label = "Export Character Skeleton"
    bl_description = (
        "Generate a new HKX skeleton from the active character's FLVER Armature and write it into that character's "
        "ANIBND, replacing the existing 'Skeleton.HKX'"
    )

    @classmethod
    def poll(cls, context) -> bool:
        if not super().poll(context):
            return False
        if not cls.settings(context).can_auto_export:
            return False
        return context.active_object.name[0] == "c"

    def execute(self, context):
        settings = self.settings(context)

        try:
            game_anim_info = SoulstructAnimation.GAME_ANIMATION_INFO_CHR[settings.game]
        except KeyError:
            return self.error(f"Automatic ANIBND export is not yet supported for game {settings.game.name}.")

        skeleton_hkx_class = settings.game_config.skeleton_hkx_class  # type: type[BaseSkeletonHKX]
        if skeleton_hkx_class is None:
            return self.error(f"No skeleton HKX class defined for game {settings.game.name}.")

        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        model_name = bl_flver.game_name

        relative_anibnd_path = Path(game_anim_info.relative_binder_path.format(model_name=model_name))
        try:
            anibnd = settings.get_initial_binder(self, relative_anibnd_path)
        except FileNotFoundError as ex:
            return self.error(f"Cannot find ANIBND for character {model_name}: {ex}")

        try:
            skeleton_entry = anibnd[SKELETON_ENTRY_RE]
        except EntryNotFoundError:
            return self.error("Could not find 'skeleton.hkx' (case-insensitive) in ANIBND.")
        template_skeleton_hkx = skeleton_hkx_class.from_binder_entry(skeleton_entry)

        skeleton_hkx = self.build_skeleton_hkx(context, bl_flver.armature, template_skeleton_hkx)
        if skeleton_hkx is None:
            return {"CANCELLED"}

        skeleton_entry.set_from_binary_file(skeleton_hkx)
        self.info(f"Exported new HKX skeleton for {model_name} into ANIBND '{anibnd.path_name}'.")

        exported_paths = settings.export_file(self, anibnd, relative_anibnd_path)
        return {"FINISHED" if exported_paths else "CANCELLED"}


@io_soulstruct_operator
class ExportObjectHKXSkeleton(_BaseExportHKXSkeleton):
    """Generate a new HKX skeleton from the active object FLVER Armature and write it into its game OBJBND."""
    bl_idname = "export_scene.hkx_object_skeleton"
    bl_label = "Export Object Skeleton"
    bl_description = (
        "Generate a new HKX skeleton from the active object's FLVER Armature and write it into the ANIBND inside "
        "that object's OBJBND, replacing the existing 'Skeleton.HKX'"
    )

    @classmethod
    def poll(cls, context) -> bool:
        if not super().poll(context):
            return False
        if not cls.settings(context).can_auto_export:
            return False
        return context.active_object.name[0] == "o"

    def execute(self, context):
        settings = self.settings(context)

        try:
            game_anim_info = SoulstructAnimation.GAME_ANIMATION_INFO_OBJ[settings.game]
        except KeyError:
            return self.error(f"Automatic OBJBND + ANIBND export is not yet supported for game {settings.game.name}.")

        skeleton_hkx_class = settings.game_config.skeleton_hkx_class  # type: type[BaseSkeletonHKX]
        if skeleton_hkx_class is None:
            return self.error(f"No skeleton HKX class defined for game {settings.game.name}.")

        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        model_name = bl_flver.game_name

        relative_objbnd_path = Path(game_anim_info.relative_binder_path.format(model_name=model_name))
        try:
            objbnd = settings.get_initial_binder(self, relative_objbnd_path)
        except FileNotFoundError:
            return self.error(f"Cannot find OBJBND for object {model_name}.")

        try:
            anibnd_entry = objbnd[f"{model_name}.anibnd"]  # no DCX
        except EntryNotFoundError:
            return self.error(f"OBJBND for object {model_name} has no ANIBND entry.")
        anibnd = Binder.from_binder_entry(anibnd_entry)

        try:
            skeleton_entry = anibnd[SKELETON_ENTRY_RE]
        except EntryNotFoundError:
            return self.error("Could not find 'skeleton.hkx' (case-insensitive) in ANIBND inside OBJBND.")
        template_skeleton_hkx = skeleton_hkx_class.from_binder_entry(skeleton_entry)

        skeleton_hkx = self.build_skeleton_hkx(context, bl_flver.armature, template_skeleton_hkx)
        if skeleton_hkx is None:
            return {"CANCELLED"}

        skeleton_entry.set_from_binary_file(skeleton_hkx)
        # Write modified ANIBND entry back into OBJBND.
        anibnd_entry.set_from_binary_file(anibnd)
        self.info(f"Exported new HKX skeleton for {model_name} into OBJBND '{objbnd.path_name}'.")

        exported_paths = settings.export_file(self, objbnd, relative_objbnd_path)
        return {"FINISHED" if exported_paths else "CANCELLED"}


@io_soulstruct_operator
class ExportHKXSkeletonIntoAnyBinder(_BaseExportHKXSkeleton, LoggingImportOperator):
    """Generate a new HKX skeleton from the active FLVER Armature and write it into a manually chosen Binder."""
    bl_idname = "export_scene.hkx_skeleton_binder"
    bl_label = "Export HKX Skeleton Into Any Binder"
    bl_description = (
        "Generate a new HKX skeleton from the active FLVER Armature and write it into a chosen ANIBND (or the "
        "ANIBND inside a chosen OBJBND), replacing the existing 'Skeleton.HKX'"
    )

    filter_glob: bpy.props.StringProperty(
        default="*.anibnd;*.anibnd.dcx;*.objbnd;*.objbnd.dcx",
        options={"HIDDEN"},
        maxlen=255,
    )

    def execute(self, context):
        settings = self.settings(context)

        skeleton_hkx_class = settings.game_config.skeleton_hkx_class  # type: type[BaseSkeletonHKX]
        if skeleton_hkx_class is None:
            return self.error(f"No skeleton HKX class defined for game {settings.game.name}.")

        armature = self.get_flver_armature(context)
        if armature is None:
            return self.error("Active object must be a dynamic (rigged) FLVER model with an Armature.")

        binder_path = Path(self.filepath)
        try:
            binder = Binder.from_path(binder_path)
        except Exception as ex:
            return self.error(f"Could not load file as a Binder: {binder_path}. Error: {ex}")

        # If this is an OBJBND (or any Binder with a nested ANIBND), operate on the nested ANIBND instead.
        try:
            anibnd_entry = binder.find_entry_by_name_regex(r".*\.anibnd(\.dcx)?$", re.IGNORECASE)
        except EntryNotFoundError:
            anibnd_entry = None
        except ValueError as ex:
            return self.error(f"Binder contains multiple nested ANIBNDs; cannot choose one. Error: {ex}")
        anibnd = Binder.from_binder_entry(anibnd_entry) if anibnd_entry is not None else binder

        try:
            skeleton_entry = anibnd[SKELETON_ENTRY_RE]
        except EntryNotFoundError:
            return self.error(f"Could not find 'skeleton.hkx' (case-insensitive) in Binder: {binder_path.name}")
        template_skeleton_hkx = skeleton_hkx_class.from_binder_entry(skeleton_entry)

        skeleton_hkx = self.build_skeleton_hkx(context, armature, template_skeleton_hkx)
        if skeleton_hkx is None:
            return {"CANCELLED"}

        skeleton_entry.set_from_binary_file(skeleton_hkx)
        if anibnd_entry is not None:
            anibnd_entry.set_from_binary_file(anibnd)

        binder.write()
        self.info(f"Exported new HKX skeleton into Binder '{binder_path.name}'.")
        return {"FINISHED"}
