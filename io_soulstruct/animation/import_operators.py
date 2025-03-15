"""VERY early/experimental system for importing/exporting DSR animations into Blender."""
from __future__ import annotations

__all__ = [
    "ImportHKXAnimation",
    "ImportHKXAnimationWithBinderChoice",
    "ImportCharacterHKXAnimation",
    "ImportObjectHKXAnimation",
    "ImportAssetHKXAnimation",
]

import re
import time
import traceback
import typing as tp
from pathlib import Path

import bpy

from soulstruct.containers import Binder, BinderEntry, EntryNotFoundError
from soulstruct.eldenring.containers import DivBinder
from soulstruct_havok.core import HKX

from io_soulstruct.exceptions import SoulstructTypeError, AnimationImportError, UnsupportedGameError
from io_soulstruct.flver.models import BlenderFLVER
from io_soulstruct.utilities import *
from .types import SoulstructAnimation
from .utilities import *


ANIBND_RE = re.compile(r"^.*?\.anibnd(\.dcx)?$")
c0000_ANIBND_RE = re.compile(r"^c0000_.*\.anibnd(\.dcx)?$")
OBJBND_RE = re.compile(r"^.*?\.objbnd(\.dcx)?$")
GEOMBND_RE = re.compile(r"^.*?\.geombnd(\.dcx)?$")
SKELETON_ENTRY_RE = re.compile(r"skeleton\.hkx(\.dcx)?", flags=re.IGNORECASE)


class BaseImportHKXAnimation(LoggingOperator):
    """NOTE: Not all subclasses are `ImportHelper` operators."""

    @classmethod
    def poll(cls, context: bpy.types.Context):
        """Must have an active FLVER with an Armature and be working on a game that supports animations."""
        if not context.active_object:
            return False
        if not context.scene.soulstruct_settings.game_config.supports_animation:
            return False
        try:
            bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        except SoulstructTypeError:
            return False
        if not bl_flver.armature:
            return False
        return True

    def get_anibnd_skeleton_compendium(
        self, context: bpy.types.Context, model_name: str
    ) -> tuple[Binder, SKELETON_TYPING, HKX | None]:
        """Retrieve ANIBND, skeleton HKX, and compendium HKX (if applicable) in preparation for import.

        Must be implemented by the type-specific automatic importers.
        """
        raise NotImplementedError(
            f"Operator '{self.__class__.__name__}' does not implement `get_anibnd_skeleton_compendium`."
        )

    def load_binder_compendium(self, binder: Binder) -> HKX | None:
        """Try to find compendium HKX. Div Binders may have multiple, but they should be identical, so we use first."""
        try:
            compendium_entry = binder.find_entry_matching_name(r".*\.compendium")
        except EntryNotFoundError:
            self.info("Did not find any compendium HKX in Binder.")
            return None
        else:
            self.info(f"Loading compendium HKX from entry: {compendium_entry.name}")
            return HKX.from_binder_entry(compendium_entry)

    @staticmethod
    def read_skeleton(skeleton_anibnd: Binder, compendium: HKX = None) -> SKELETON_TYPING:
        try:
            skeleton_entry = skeleton_anibnd[SKELETON_ENTRY_RE]
        except EntryNotFoundError:
            raise AnimationImportError(f"ANIBND with path '{skeleton_anibnd.path}' has no skeleton HKX file.")
        return read_skeleton_hkx_entry(skeleton_entry, compendium)


class ImportHKXAnimationWithBinderChoice(BaseImportHKXAnimation, BinderEntrySelectOperator):
    """Presents user with a choice of enums from `enum_choices` class variable (set prior).

    See: https://blender.stackexchange.com/questions/6512/how-to-call-invoke-popup
    """
    bl_idname = "wm.hkx_animation_binder_choice"
    bl_label = "Choose HKX Binder Entry"

    # Class attributes set by `run()` before manual invocation.
    BINDER: tp.ClassVar[Binder | None] = None  # `get_binder()` just returns this
    BLENDER_FLVER: tp.ClassVar[BlenderFLVER | None] = None
    SKELETON_HKX: tp.ClassVar[SKELETON_TYPING | None] = None
    HKX_COMPENDIUM: tp.ClassVar[HKX | None] = None

    @classmethod
    def get_binder(cls, context) -> Binder | None:
        """Binder is set in `run()` before manual invocation."""
        return cls.BINDER

    @classmethod
    def filter_binder_entry(cls, context, entry: BinderEntry) -> bool:
        """Only show HKX animation entries."""
        return re.match(r"a.*\.hkx(\.dcx)?", entry.name) is not None

    def _import_entry(self, context, entry: BinderEntry):
        """Import the chosen HKX animation entry."""

        p = time.perf_counter()
        animation_hkx = read_animation_hkx_entry(entry, self.HKX_COMPENDIUM)
        self.info(f"Read `AnimationHKX` Binder entry '{entry.name}' in {time.perf_counter() - p:.4f} seconds.")
        # `skeleton_hkx` already set to operator.

        anim_name = entry.name.split(".")[0]
        try:
            self.info(f"Creating animation '{anim_name}' in Blender.")
            SoulstructAnimation.new_from_hkx_animation(
                self,
                context,
                animation_hkx,
                self.SKELETON_HKX,
                anim_name,
                self.BLENDER_FLVER,
            )
        except Exception as ex:
            traceback.print_exc()
            return self.error(
                f"Cannot import HKX animation {anim_name} from '{self.BINDER.path_name}'. Error: {ex}"
            )
        self.debug(f"Created animation action in {time.perf_counter() - p:.4f} seconds.")

        return {"FINISHED"}

    @classmethod
    def run(
        cls,
        binder: Binder,
        bl_flver: BlenderFLVER,
        skeleton_hkx: SKELETON_TYPING,
        compendium: HKX | None,
    ) -> set[str]:
        cls.BINDER = binder
        cls.BLENDER_FLVER = bl_flver
        cls.SKELETON_HKX = skeleton_hkx
        cls.HKX_COMPENDIUM = compendium

        # Invoke this operator.
        # noinspection PyUnresolvedReferences
        return bpy.ops.wm.hkx_animation_binder_choice("INVOKE_DEFAULT")


class ImportHKXAnimation(BaseImportHKXAnimation, LoggingImportOperator):
    bl_idname = "import_scene.hkx_animation"
    bl_label = "Import HKX Anim"
    bl_description = ("Import a HKX animation file from an ANIBND, OBJBND, or GEOMBND. Loose HKX animation files "
                      "cannot be imported as the skeleton (and sometimes compendium) HKX is required")

    filter_glob: bpy.props.StringProperty(
        default="*.anibnd;*.anibnd.dcx;*.objbnd;*.objbnd.dcx;*.geombnd;*.geombnd.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    directory: bpy.props.StringProperty(options={'HIDDEN'})

    # Same `poll` method.

    def invoke(self, context, _event):
        """Set the initial directory based on Global Settings."""
        settings = self.settings(context)
        try:
            chr_path = settings.get_import_dir_path("chr")
        except NotADirectoryError:
            return super().invoke(context, _event)

        # Start in 'chr' directory.
        self.directory = str(chr_path)
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):

        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)

        binder_path = Path(self.filepath)

        if OBJBND_RE.match(binder_path.name):
            # Get ANIBND nested inside OBJBND.
            objbnd = DivBinder.from_path(binder_path)
            anibnd_entry = objbnd.find_entry_matching_name(r".*\.anibnd(\.dcx)?")
            if not anibnd_entry:
                return self.error("OBJBND binder does not contain a nested ANIBND binder.")
            skeleton_anibnd = anibnd = DivBinder.from_binder_entry(anibnd_entry)

        elif GEOMBND_RE.match(binder_path.name):
            geombnd = Binder.from_path(binder_path)  # never `DivBinder`
            # Find ANIBND entry inside GEOMBND. Always uppercase. TODO: Shouldn't be case-sensitive though.
            anibnd_entry = geombnd.find_entry_matching_name(r".*\.anibnd(\.dcx)?")
            if not anibnd_entry:
                return self.error("GEOMBND binder does not contain an ANIBND binder.")
            skeleton_anibnd = anibnd = Binder.from_binder_entry(anibnd_entry)  # never `DivBinder`

        elif ANIBND_RE.match(binder_path.name):
            anibnd = DivBinder.from_path(binder_path)
            if c0000_match := c0000_ANIBND_RE.match(binder_path.name):
                # c0000 skeleton is in base `c0000.anibnd{.dcx}` file.
                skeleton_anibnd = DivBinder.from_path(binder_path.parent / f"c0000.anibnd{c0000_match.group(1)}")
            else:
                skeleton_anibnd = anibnd

        else:
            # TODO: Currently require skeleton HKX and possibly compendium, so have to use ANIBND.
            #  Need another deferred operator that lets you choose a loose Skeleton file after a loose animation.
            return self.error(
                "Must import animation from an ANIBND containing a skeleton HKX file or an OBJBND with an ANIBND."
            )

        compendium = self.load_binder_compendium(anibnd)
        skeleton_hkx = self.read_skeleton(skeleton_anibnd, compendium)

        # Don't bother calling sub-operator if there are no HKX entries to offer.
        if not anibnd.find_entries_matching_name(r"a.*\.hkx(\.dcx)?"):
            return self.error(f"Cannot find any HKX animation files in binder '{binder_path.name}'.")

        return ImportHKXAnimationWithBinderChoice.run(
            binder=anibnd,
            bl_flver=bl_flver,
            skeleton_hkx=skeleton_hkx,
            compendium=compendium,
        )


class BaseImportTypedHKXAnimation(BaseImportHKXAnimation):
    """Base class for importing character, object, and asset FLVER animations from their specific ANIBND sources."""

    def execute(self, context):
        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        model_name = bl_flver.game_name

        # Find animation HKX entry/entries.
        try:
            anibnd, skeleton_hkx, compendium = self.get_anibnd_skeleton_compendium(context, model_name)
        except Exception as ex:
            return self.error(str(ex))

        anim_hkx_entries = anibnd.find_entries_matching_name(r"a.*\.hkx(\.dcx)?")
        if not anim_hkx_entries:
            raise AnimationImportError(
                f"Cannot find any HKX animation files in '{anibnd.path_name}' for FLVER '{model_name}'."
            )

        return ImportHKXAnimationWithBinderChoice.run(
            binder=anibnd,
            bl_flver=bl_flver,
            skeleton_hkx=skeleton_hkx,
            compendium=compendium,
        )


# noinspection PyUnusedLocal
def _sub_c0000_binder_choices(self, context):
    return ImportCharacterHKXAnimation.c0000_binder_choices


class ImportCharacterHKXAnimation(BaseImportTypedHKXAnimation):
    """Detects name of selected character FLVER Armature and finds their ANIBND in the game directory."""
    bl_idname = "import_scene.character_hkx_animation"
    bl_label = "Import Character Anim"
    bl_description = "Import a HKX animation file from the selected character's pre-loaded ANIBND"

    c0000_binder_choices: tp.ClassVar[list[tuple[str, str, str]]] = []

    sub_c0000_binder: bpy.props.EnumProperty(
        items=_sub_c0000_binder_choices,
        name="c0000 ANIBND",
        description="Choose a c0000 sub-ANIBND to import from",
    )

    @classmethod
    def poll(cls, context) -> bool:
        """Character FLVER (not MSB Part) must be selected."""
        return super().poll(context) and context.active_object.name[0] == "c"

    def invoke(self, context, _event):
        settings = self.settings(context)
        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        model_name = bl_flver.game_name
        if model_name == "c0000":
            # NOTE: The 'c0000_*.txt' registration of sub-ANIBNDs holds for all games I've seen so far.
            try:
                game_anim_info = SoulstructAnimation.GAME_ANIMATION_INFO_CHR[settings.game]
            except KeyError:
                raise AnimationImportError(f"Game '{settings.game}' is not supported for character animation import.")
            relative_anibnd_path = Path(game_anim_info.relative_binder_path.format(model_name=model_name))
            anibnd_path = settings.get_import_file_path(relative_anibnd_path)
            if not anibnd_path or not anibnd_path.is_file():
                raise FileNotFoundError(f"Cannot find ANIBND for character '{model_name}' in game directory.")
            try:
                anibnd = DivBinder.from_path(anibnd_path)  # NOTE: c0000 should never use `DivBinder` but harmless
            except Exception as ex:
                return self.error(f"Error reading ANIBND '{anibnd_path}': {ex}")

            sub_anibnd_stems = [entry.stem for entry in anibnd.find_entries_matching_name(r"c0000_.*\.txt")]
            if not sub_anibnd_stems:
                return self.error("Could not find any sub-ANIBND definitions (e.g. 'c0000_a0x.txt') in c0000 ANIBND.")
            # NOTE: We don't check if the sub-ANIBND actually exist yet; they may not yet be in the project directory,
            # for example, while the main `c0000.anibnd` is. We let the importer find them as initial binders.
            ImportCharacterHKXAnimation.c0000_binder_choices = [
                # No default option.
                (stem, stem, f"c0000 sub-ANIBND '{stem}'") for stem in sub_anibnd_stems
            ]
            # Now prompt user to select a sub-ANIBND.
            return context.window_manager.invoke_props_dialog(self)

        # No invocation dialogs needed for non-c0000 characters.
        ImportCharacterHKXAnimation.c0000_binder_choices = [("None", "None", "No sub-ANIBND")]
        self.sub_c0000_binder = "None"
        return self.execute(context)

    def get_anibnd_skeleton_compendium(
        self, context: bpy.types.Context, model_name: str
    ) -> tuple[Binder, SKELETON_TYPING, HKX | None]:
        settings = self.settings(context)

        try:
            game_anim_info = SoulstructAnimation.GAME_ANIMATION_INFO_CHR[settings.game]
        except KeyError:
            raise AnimationImportError(f"Game '{settings.game}' is not supported for character animation import.")

        # Even if a sub-ANIBND for c0000 has been chosen, we need the main one for the skeleton (but not compendium).
        relative_anibnd_path = Path(game_anim_info.relative_binder_path.format(model_name=model_name))
        anibnd_path = settings.get_import_file_path(relative_anibnd_path)
        if not anibnd_path or not anibnd_path.is_file():
            raise FileNotFoundError(f"Cannot find ANIBND for character '{model_name}' in game directory.")
        skeleton_anibnd = anibnd = DivBinder.from_path(anibnd_path)

        if self.sub_c0000_binder != "None":
            # Importing from c0000 sub-ANIBND.
            anibnd_path = settings.get_import_file_path(
                game_anim_info.relative_binder_path.format(model_name=self.sub_c0000_binder)
            )
            if not anibnd_path or not anibnd_path.is_file():
                raise FileNotFoundError(f"Cannot find ANIBND to import for c0000 sub-ANIBND '{self.sub_c0000_binder}'.")
            # NOTE: Compendium is in sub-ANIBND in relevant games.
            anibnd = DivBinder.from_path(anibnd_path)  # probably not `DivBinder`, but harmless

        self.info(f"Importing animation(s) from ANIBND: {anibnd_path}")

        compendium = self.load_binder_compendium(anibnd)
        skeleton_hkx = self.read_skeleton(skeleton_anibnd, compendium)
        return anibnd, skeleton_hkx, compendium


class ImportObjectHKXAnimation(BaseImportTypedHKXAnimation):
    """Detects name of selected object FLVER Armature and finds their OBJBND in the game directory."""
    bl_idname = "import_scene.object_hkx_animation"
    bl_label = "Import Object Anim"
    bl_description = "Import a HKX animation file from the selected object's pre-loaded OBJBND"

    @classmethod
    def poll(cls, context) -> bool:
        """Object FLVER (not MSB Part) must be selected."""
        return super().poll(context) and context.active_object.name[0] == "o"

    def get_anibnd_skeleton_compendium(
        self, context: bpy.types.Context, model_name: str
    ) -> tuple[Binder, SKELETON_TYPING, HKX | None]:
        settings = self.settings(context)

        try:
            game_anim_info = SoulstructAnimation.GAME_ANIMATION_INFO_OBJ[settings.game]
        except KeyError:
            raise UnsupportedGameError(f"Game '{settings.game}' is not supported for object animation import.")

        relative_objbnd_path = Path(game_anim_info.relative_binder_path.format(model_name=model_name))
        objbnd_path = settings.get_import_file_path(relative_objbnd_path)
        if not objbnd_path or not objbnd_path.is_file():
            raise AnimationImportError(f"Cannot find OBJBND for '{model_name}' in game directory.")
        objbnd = DivBinder.from_path(objbnd_path)
        # Find ANIBND entry inside OBJBND.
        try:
            anibnd_entry = objbnd[f"{model_name}.anibnd"]
        except EntryNotFoundError:
            raise AnimationImportError(f"OBJBND of object '{model_name}' has no nested ANIBND.")
        # Skeleton is inside same ANIBND.
        skeleton_anibnd = anibnd = DivBinder.from_binder_entry(anibnd_entry)
        compendium = self.load_binder_compendium(anibnd)
        skeleton_hkx = self.read_skeleton(skeleton_anibnd, compendium)
        return anibnd, skeleton_hkx, compendium


class ImportAssetHKXAnimation(BaseImportTypedHKXAnimation):
    """Detects name of selected asset FLVER Armature and finds their GEOMBND in the game directory.

    Elden Ring and onwards only.
    """
    bl_idname = "import_scene.asset_hkx_animation"
    bl_label = "Import Asset Anim"
    bl_description = "Import a HKX animation file from the selected asset's pre-loaded GEOMBND"

    @classmethod
    def poll(cls, context) -> bool:
        """Asset FLVER (not MSB Part) must be selected."""
        return super().poll(context) and context.active_object.name[:3].lower() == "aeg"

    def get_anibnd_skeleton_compendium(
        self, context: bpy.types.Context, model_name: str
    ) -> tuple[Binder, SKELETON_TYPING, HKX | None]:
        settings = self.settings(context)
        asset_category = model_name[:6]  # e.g. "aeg099"
        # Note additional category subfolder.
        geombnd_path = settings.get_import_file_path(f"asset/aeg/{asset_category}/{model_name}.geombnd")  # always DCX
        if not geombnd_path or not geombnd_path.is_file():
            raise AnimationImportError(f"Cannot find GEOMBND for Asset '{model_name}' in game directory.")
        geombnd = Binder.from_path(geombnd_path)
        # Find ANIBND entry inside GEOMBND. Always uppercase, but we ignore case anyway.
        anibnd_name = f"{model_name.upper()}.anibnd"
        try:
            anibnd_entry = geombnd.find_entry_matching_name(anibnd_name, flags=re.IGNORECASE)
        except EntryNotFoundError:
            raise AnimationImportError(f"GEOMBND of object '{model_name}' has no ANIBND '{anibnd_name}'.")
        skeleton_anibnd = anibnd = Binder.from_binder_entry(anibnd_entry)
        compendium = self.load_binder_compendium(anibnd)
        skeleton_hkx = self.read_skeleton(skeleton_anibnd, compendium)
        return anibnd, skeleton_hkx, compendium
