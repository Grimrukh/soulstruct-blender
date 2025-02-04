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

    import_all_animations: bool

    @classmethod
    def poll(cls, context: bpy.types.Context):
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
        """Retrieve ANIBND, skeleton HKX, and compendium HKX (if applicable) in preparation for import."""
        raise NotImplementedError(
            f"Operator '{self.__class__.__name__}' does not implement `get_anibnd_skeleton_compendium`."
        )

    def scan_entries(
        self,
        anim_hkx_entries: list[BinderEntry],
        file_path: Path,
        skeleton_hkx: SKELETON_TYPING,
        compendium: HKX = None,
    ) -> list[tuple[Path, SKELETON_TYPING, ANIMATION_TYPING | list[BinderEntry]]]:
        """Scan all given `anim_hkx_entries` and parse them as Binders or individual animation HKX files.

        Note that `file_path` is attached to each queue element for source information only.
        """
        if self.import_all_animations:
            # Read and queue up HKX animations for separate import.
            hkxs_with_paths = []
            for entry in anim_hkx_entries:
                try:
                    animation_hkx = read_animation_hkx_entry(entry, compendium)
                except Exception as ex:
                    self.warning(f"Error occurred while reading HKX Binder entry '{entry.name}': {ex}")
                else:
                    hkxs_with_paths.append((file_path, skeleton_hkx, animation_hkx))
                    print(animation_hkx, animation_hkx.path)
            return hkxs_with_paths

        # Queue up all Binder entries; user will be prompted to choose entry later (even if only one entry exists).
        return [(file_path, skeleton_hkx, anim_hkx_entries)]

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

    def import_all_entries(
        self,
        context: bpy.types.Context,
        hkxs_with_paths: list[tuple[Path, SKELETON_TYPING, ANIMATION_TYPING | list[BinderEntry]]],
        compendium: HKX | None,
        bl_flver: BlenderFLVER,
    ) -> list[SoulstructAnimation]:
        animations = []
        for file_path, skeleton_hkx, hkx_or_entries in hkxs_with_paths:
            if isinstance(hkx_or_entries, list):
                # Defer through entry selection operator.
                ImportHKXAnimationWithBinderChoice.run(
                    binder_file_path=Path(file_path),
                    hkx_entries=hkx_or_entries,
                    bl_flver=bl_flver,
                    skeleton_hkx=skeleton_hkx,
                    compendium=compendium,
                )
                continue
            hkx_or_entries: ANIMATION_TYPING
            anim_name = hkx_or_entries.path_minimal_stem
            try:
                self.info(f"Creating animation '{anim_name}' in Blender.")
                bl_animation = SoulstructAnimation.new_from_hkx_animation(
                    self,
                    context,
                    animation_hkx=hkx_or_entries,
                    skeleton_hkx=skeleton_hkx,
                    name=anim_name,
                    bl_flver=bl_flver,
                )
                animations.append(bl_animation)
            except Exception as ex:
                # We don't error out here, because we want to continue importing other files.
                self.error(
                    f"Error occurred while importing HKX animation '{anim_name}' for FLVER {bl_flver.name}: {ex}"
                )

        return animations

    @staticmethod
    def read_skeleton(skeleton_anibnd: Binder, compendium: HKX = None) -> SKELETON_TYPING:
        try:
            skeleton_entry = skeleton_anibnd[SKELETON_ENTRY_RE]
        except EntryNotFoundError:
            raise AnimationImportError(f"ANIBND with path '{skeleton_anibnd.path}' has no skeleton HKX file.")
        return read_skeleton_hkx_entry(skeleton_entry, compendium)


class ImportHKXAnimation(BaseImportHKXAnimation, LoggingImportOperator):
    bl_idname = "import_scene.hkx_animation"
    bl_label = "Import HKX Anim"
    bl_description = "Import a HKX animation file. Can import from ANIBNDs/OBJBNDs and supports DCX-compressed files"

    filter_glob: bpy.props.StringProperty(
        default="*.hkx;*.hkx.dcx;*.anibnd;*.anibnd.dcx;*.objbnd;*.objbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'})

    import_all_animations: bpy.props.BoolProperty(
        name="Import All Animations",
        description="Import all HKX anim files rather than being prompted to select one (slow!)",
        default=False,
    )

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

        file_paths = [Path(self.directory, file.name) for file in self.files]
        hkxs_with_paths = []  # type: list[tuple[Path, SKELETON_TYPING, ANIMATION_TYPING | list[BinderEntry]]]
        compendium = None

        for file_path in file_paths:

            if OBJBND_RE.match(file_path.name):
                # Get ANIBND nested inside OBJBND.
                objbnd = DivBinder.from_path(file_path)
                anibnd_entry = objbnd.find_entry_matching_name(r".*\.anibnd(\.dcx)?")
                if not anibnd_entry:
                    return self.error("OBJBND binder does not contain a nested ANIBND binder.")
                skeleton_anibnd = anibnd = DivBinder.from_binder_entry(anibnd_entry)
            elif GEOMBND_RE.match(file_path.name):
                geombnd = Binder.from_path(file_path)  # never `DivBinder`
                # Find ANIBND entry inside GEOMBND. Always uppercase. TODO: Shouldn't be case-sensitive though.
                anibnd_entry = geombnd.find_entry_matching_name(r".*\.anibnd(\.dcx)?")
                if not anibnd_entry:
                    return self.error("GEOMBND binder does not contain an ANIBND binder.")
                skeleton_anibnd = anibnd = Binder.from_binder_entry(anibnd_entry)  # never `DivBinder`
            elif ANIBND_RE.match(file_path.name):
                anibnd = DivBinder.from_path(file_path)
                if c0000_match := c0000_ANIBND_RE.match(file_path.name):
                    # c0000 skeleton is in base `c0000.anibnd{.dcx}` file.
                    skeleton_anibnd = DivBinder.from_path(file_path.parent / f"c0000.anibnd{c0000_match.group(1)}")
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

            # Find animation HKX entry/entries.
            anim_hkx_entries = anibnd.find_entries_matching_name(r"a.*\.hkx(\.dcx)?")
            if not anim_hkx_entries:
                return self.error(f"Cannot find any HKX animation files in binder {file_path}.")
            hkxs_with_paths += self.scan_entries(anim_hkx_entries, file_path, skeleton_hkx, compendium)

        animations = self.import_all_entries(context, hkxs_with_paths, compendium, bl_flver)
        return {"FINISHED"} if animations else {"CANCELLED"}  # at least one successful import


# noinspection PyUnusedLocal
def get_binder_entry_choices(self, context):
    return ImportHKXAnimationWithBinderChoice.enum_options


class ImportHKXAnimationWithBinderChoice(BaseImportHKXAnimation):
    """Presents user with a choice of enums from `enum_choices` class variable (set prior).

    See: https://blender.stackexchange.com/questions/6512/how-to-call-invoke-popup
    """
    bl_idname = "wm.hkx_animation_binder_choice"
    bl_label = "Choose HKX Binder Entry"

    # For deferred import in `execute()`.
    binder: Binder | None = None
    binder_file_path: Path = Path()
    enum_options: list[tuple[tp.Any, str, str]] = []
    hkx_entries: tp.Sequence[BinderEntry] = []
    bl_flver: BlenderFLVER = None
    skeleton_hkx: SKELETON_TYPING | None = None
    compendium: HKX | None = None

    choices_enum: bpy.props.EnumProperty(items=get_binder_entry_choices)

    import_all_animations: bpy.props.BoolProperty(
        name="Import All Animations",
        description="Import all HKX anim files rather than being prompted to select one (slow!)",
        default=False,
    )

    # noinspection PyUnusedLocal
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    # noinspection PyUnusedLocal
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "choices_enum", expand=False)

    def execute(self, context):
        choice = int(self.choices_enum)
        entry = self.hkx_entries[choice]

        p = time.perf_counter()
        animation_hkx = read_animation_hkx_entry(entry, self.compendium)
        self.info(f"Read `AnimationHKX` Binder entry '{entry.name}' in {time.perf_counter() - p:.4f} seconds.")
        # `skeleton_hkx` already set to operator.

        anim_name = entry.name.split(".")[0]
        try:
            self.info(f"Creating animation '{anim_name}' in Blender.")
            SoulstructAnimation.new_from_hkx_animation(
                self,
                context,
                animation_hkx,
                self.skeleton_hkx,
                anim_name,
                self.bl_flver,
            )
        except Exception as ex:
            traceback.print_exc()
            return self.error(
                f"Cannot import HKX animation {anim_name} from '{self.binder_file_path.name}'. Error: {ex}"
            )
        self.info(f"Created animation action in {time.perf_counter() - p:.4f} seconds.")

        return {"FINISHED"}

    @classmethod
    def run(
        cls,
        binder_file_path: Path,
        hkx_entries: list[BinderEntry],
        bl_flver: BlenderFLVER,
        skeleton_hkx: SKELETON_TYPING,
        compendium: HKX | None,
    ):
        cls.binder_file_path = binder_file_path
        cls.enum_options = [(str(i), entry.name, "") for i, entry in enumerate(hkx_entries)]
        cls.hkx_entries = hkx_entries
        cls.bl_flver = bl_flver
        cls.skeleton_hkx = skeleton_hkx
        cls.compendium = compendium
        # noinspection PyUnresolvedReferences
        bpy.ops.wm.hkx_animation_binder_choice("INVOKE_DEFAULT")


class BaseImportTypedHKXAnimation(BaseImportHKXAnimation):

    def execute(self, context):
        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        model_name = bl_flver.export_name
        if model_name == "c0000":
            return self.error(
                "Automatic ANIBND import is not yet supported for character FLVER 'c0000' (Player). Use "
                "'Import Any Animation' and choose the sub-ANIBND you want to import from."
            )

        # Find animation HKX entry/entries.
        try:
            anibnd, skeleton_hkx, compendium = self.get_anibnd_skeleton_compendium(context, model_name)
        except Exception as ex:
            return self.error(str(ex))

        anim_hkx_entries = anibnd.find_entries_matching_name(r"a.*\.hkx(\.dcx)?")
        if not anim_hkx_entries:
            raise AnimationImportError(f"Cannot find any HKX animation files for FLVER '{model_name}'.")

        hkxs_with_paths = self.scan_entries(anim_hkx_entries, anibnd.path, skeleton_hkx, compendium)
        animations = self.import_all_entries(context, hkxs_with_paths, compendium, bl_flver)
        return {"FINISHED"} if animations else {"CANCELLED"}  # at least one successful import


class ImportCharacterHKXAnimation(BaseImportTypedHKXAnimation):
    """Detects name of selected character FLVER Armature and finds their ANIBND in the game directory."""
    bl_idname = "import_scene.character_hkx_animation"
    bl_label = "Import Character Anim"
    bl_description = "Import a HKX animation file from the selected character's pre-loaded ANIBND"

    import_all_animations: bpy.props.BoolProperty(
        name="Import All Animations",
        description="Import all HKX anim files rather than being prompted to select one (slow!)",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        """Character FLVER (not MSB Part) must be selected."""
        return super().poll(context) and context.active_object.name[0] == "c"

    def get_anibnd_skeleton_compendium(
        self, context: bpy.types.Context, model_name: str
    ) -> tuple[Binder, SKELETON_TYPING, HKX | None]:
        settings = self.settings(context)

        try:
            game_anim_info = SoulstructAnimation.GAME_ANIMATION_INFO_CHR.get(settings.game)
        except KeyError:
            raise AnimationImportError(f"Game '{settings.game}' is not supported for character animation import.")

        relative_anibnd_path = Path(game_anim_info.relative_binder_path.format(model_name=model_name))
        anibnd_path = settings.get_import_file_path(relative_anibnd_path)
        if not anibnd_path or not anibnd_path.is_file():
            raise FileNotFoundError(f"Cannot find ANIBND for character '{model_name}' in game directory.")

        skeleton_anibnd = anibnd = DivBinder.from_path(anibnd_path)
        # TODO: Support c0000 automatic import. Combine all sub-ANIBND entries into one big choice list?
        self.info(f"Importing animation(s) from ANIBND: {anibnd_path}")

        compendium = self.load_binder_compendium(anibnd)
        skeleton_hkx = self.read_skeleton(skeleton_anibnd, compendium)
        return anibnd, skeleton_hkx, compendium


class ImportObjectHKXAnimation(BaseImportTypedHKXAnimation):
    """Detects name of selected object FLVER Armature and finds their OBJBND in the game directory."""
    bl_idname = "import_scene.object_hkx_animation"
    bl_label = "Import Object Anim"
    bl_description = "Import a HKX animation file from the selected object's pre-loaded OBJBND"

    import_all_animations: bpy.props.BoolProperty(
        name="Import All Animations",
        description="Import all HKX anim files rather than being prompted to select one (slow!)",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        """Object FLVER (not MSB Part) must be selected."""
        return super().poll(context) and context.active_object.name[0] == "o"

    def get_anibnd_skeleton_compendium(
        self, context: bpy.types.Context, model_name: str
    ) -> tuple[Binder, SKELETON_TYPING, HKX | None]:
        settings = self.settings(context)

        try:
            game_anim_info = SoulstructAnimation.GAME_ANIMATION_INFO_OBJ.get(settings.game)
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
    def poll(cls, context):
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
