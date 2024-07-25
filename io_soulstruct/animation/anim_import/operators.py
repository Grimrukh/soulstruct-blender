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
from bpy_extras.io_utils import ImportHelper

from soulstruct.containers import Binder, BinderEntry, EntryNotFoundError
from soulstruct.eldenring.containers import DivBinder

from soulstruct_havok.core import HKX
from soulstruct_havok.wrappers import hkx2015, hkx2016, hkx2018

from io_soulstruct.utilities import *
from io_soulstruct.animation.utilities import *
from .core import HKXAnimationImporter

ANIBND_RE = re.compile(r"^.*?\.anibnd(\.dcx)?$")
c0000_ANIBND_RE = re.compile(r"^c0000_.*\.anibnd(\.dcx)?$")
OBJBND_RE = re.compile(r"^.*?\.objbnd(\.dcx)?$")
SKELETON_ENTRY_RE = re.compile(r"skeleton\.hkx(\.dcx)?", flags=re.IGNORECASE)


SKELETON_TYPING = tp.Union[hkx2015.SkeletonHKX, hkx2016.SkeletonHKX, hkx2018.SkeletonHKX]
ANIMATION_TYPING = tp.Union[hkx2015.AnimationHKX, hkx2016.AnimationHKX, hkx2018.AnimationHKX]


def read_animation_hkx_entry(hkx_entry: BinderEntry, compendium: HKX = None) -> ANIMATION_TYPING:
    data = hkx_entry.get_uncompressed_data()
    version = data[0x10:0x18]
    if version == b"20180100":  # ER
        hkx = hkx2018.AnimationHKX.from_bytes(data, compendium=compendium)
    elif version == b"20150100":  # DSR
        hkx = hkx2015.AnimationHKX.from_bytes(data, compendium=compendium)
    elif version == b"20160100":  # non-From
        hkx = hkx2016.AnimationHKX.from_bytes(data, compendium=compendium)
    else:
        raise ValueError(f"Cannot support this HKX animation file version in Soulstruct and/or Blender: {version}")
    hkx.path = Path(hkx_entry.name)
    return hkx


def read_skeleton_hkx_entry(hkx_entry: BinderEntry, compendium: HKX = None) -> SKELETON_TYPING:
    data = hkx_entry.get_uncompressed_data()
    version = data[0x10:0x18]
    if version == b"20180100":  # ER
        hkx = hkx2018.SkeletonHKX.from_bytes(data, compendium=compendium)
    elif version == b"20150100":  # DSR
        hkx = hkx2015.SkeletonHKX.from_bytes(data, compendium=compendium)
    elif version == b"20160100":  # non-From
        hkx = hkx2016.SkeletonHKX.from_bytes(data, compendium=compendium)
    else:
        raise ValueError(f"Cannot support this HKX skeleton file version in Soulstruct and/or Blender: {version}")
    hkx.path = Path(hkx_entry.name)
    return hkx


class ImportHKXAnimationMixin:

    info: tp.Callable[[str], None]
    warning: tp.Callable[[str], None]
    error: tp.Callable[[str], set[str]]

    import_all_animations: bpy.props.BoolProperty(
        name="Import All Animations",
        description="Import all HKX anim files rather than being prompted to select one (slow!)",
        default=False,
    )

    # TODO: Enabled by default. Maybe try to detect from frame timing...
    to_60_fps: bpy.props.BoolProperty(
        name="To 60 FPS",
        description="Scale animation keyframes to 60 FPS (from 30 FPS) by spacing them two frames apart",
        default=True,
    )

    def scan_entries(
        self,
        anim_hkx_entries: list[BinderEntry],
        file_path: Path,
        skeleton_hkx: SKELETON_TYPING,
        compendium: HKX = None,
    ) -> list[tuple[Path, SKELETON_TYPING, ANIMATION_TYPING | list[BinderEntry]]]:
        if len(anim_hkx_entries) > 1:
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

            # Queue up all Binder entries; user will be prompted to choose entry later.
            return [(file_path, skeleton_hkx, anim_hkx_entries)]

        try:
            animation_hkx = read_animation_hkx_entry(anim_hkx_entries[0], compendium)
        except Exception as ex:
            self.warning(f"Error occurred while reading HKX Binder entry '{anim_hkx_entries[0].name}': {ex}")
            return []

        return [(file_path, skeleton_hkx, animation_hkx)]

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

    def import_hkx(
        self,
        bl_armature: bpy.types.ArmatureObject,
        importer: HKXAnimationImporter,
        file_path: Path,
        skeleton_hkx: SKELETON_TYPING,
        animation_hkx: ANIMATION_TYPING,
    ) -> set[str]:
        anim_name = animation_hkx.path.name.split(".")[0]

        self.info(f"Importing HKX animation for {bl_armature.name}: {anim_name}")

        p = time.perf_counter()
        animation_hkx.animation_container.spline_to_interleaved()
        self.info(f"Converted spline animation to interleaved in {time.perf_counter() - p:.4f} seconds.")

        # We look up track bone names from annotations. TODO: Should just use `skeleton_hkx`?
        track_bone_names = [
            annotation.trackName for annotation in animation_hkx.animation_container.animation.annotationTracks
        ]
        bl_bone_names = [b.name for b in bl_armature.data.bones]
        for bone_name in track_bone_names:
            if bone_name not in bl_bone_names:
                raise ValueError(
                    f"Animation bone name '{bone_name}' is missing from selected Blender Armature."
                )

        p = time.perf_counter()
        arma_frames = get_armature_frames(animation_hkx, skeleton_hkx, track_bone_names)
        root_motion = get_root_motion(animation_hkx)
        self.info(f"Constructed armature animation frames in {time.perf_counter() - p:.4f} seconds.")

        # Import single animation HKX.
        p = time.perf_counter()
        try:
            importer.create_action(anim_name, arma_frames, root_motion)
        except Exception as ex:
            traceback.print_exc()
            raise HKXAnimationImportError(f"Cannot import HKX animation: {file_path.name}. Error: {ex}")
        self.info(f"Created animation action in {time.perf_counter() - p:.4f} seconds.")

        return {"FINISHED"}

    @staticmethod
    def read_skeleton(skeleton_anibnd: Binder, compendium: HKX = None) -> SKELETON_TYPING:
        try:
            skeleton_entry = skeleton_anibnd[SKELETON_ENTRY_RE]
        except EntryNotFoundError:
            raise HKXAnimationImportError(f"ANIBND with path '{skeleton_anibnd.path}' has no skeleton HKX file.")
        return read_skeleton_hkx_entry(skeleton_entry, compendium)


class ImportHKXAnimation(LoggingOperator, ImportHelper, ImportHKXAnimationMixin):
    bl_idname = "import_scene.hkx_animation"
    bl_label = "Import HKX Anim"
    bl_description = "Import a HKX animation file. Can import from ANIBNDs/OBJBNDs and supports DCX-compressed files"

    filename_ext = ".hkx"

    filter_glob: bpy.props.StringProperty(
        default="*.hkx;*.hkx.dcx;*.anibnd;*.anibnd.dcx;*.objbnd;*.objbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        """Animation's rigged armature must be selected (to extract bone names)."""
        try:
            return context.selected_objects[0].type == "ARMATURE"
        except IndexError:
            return False

    def invoke(self, context, _event):
        """Set the initial directory based on Global Settings."""
        game_directory = self.settings(context).game_directory
        game_chr_directory = game_directory / "chr"
        for directory in (game_chr_directory, game_directory):
            if directory and directory.is_dir():
                self.directory = str(directory)
                context.window_manager.fileselect_add(self)
                return {'RUNNING_MODAL'}
        return super().invoke(context, _event)

    def execute(self, context):

        # noinspection PyTypeChecker
        bl_armature = context.selected_objects[0]  # type: bpy.types.ArmatureObject

        file_paths = [Path(self.directory, file.name) for file in self.files]
        hkxs_with_paths = []  # type: list[tuple[Path, SKELETON_TYPING, ANIMATION_TYPING | list[BinderEntry]]]
        compendium = None

        for file_path in file_paths:

            if OBJBND_RE.match(file_path.name):
                # Get ANIBND from OBJBND.
                objbnd = DivBinder.from_path(file_path)
                anibnd_entry = objbnd.find_entry_matching_name(r".*\.anibnd(\.dcx)?")
                if not anibnd_entry:
                    return self.error("OBJBND binder does not contain an ANIBND binder.")
                skeleton_anibnd = anibnd = DivBinder.from_binder_entry(anibnd_entry)
            elif ANIBND_RE.match(file_path.name):
                anibnd = DivBinder.from_path(file_path)
                if c0000_match := c0000_ANIBND_RE.match(file_path.name):
                    # c0000 skeleton is in base `c0000.anibnd{.dcx}` file.
                    skeleton_anibnd = DivBinder.from_path(file_path.parent / f"c0000.anibnd{c0000_match.group(1)}")
                else:
                    skeleton_anibnd = anibnd
            else:
                # TODO: Currently require skeleton HKX and possibly compendium, so have to use ANIBND.
                #  Have another deferred operator that lets you choose a loose Skeleton file after a loose animation.
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

        importer = HKXAnimationImporter(self, context, bl_armature, bl_armature.name, self.to_60_fps)

        return_strings = set()
        for file_path, skeleton_hkx, hkx_or_entries in hkxs_with_paths:
            if isinstance(hkx_or_entries, list):
                # Defer through entry selection operator.
                ImportHKXAnimationWithBinderChoice.run(
                    importer=importer,
                    binder_file_path=Path(file_path),
                    hkx_entries=hkx_or_entries,
                    bl_armature=bl_armature,
                    skeleton_hkx=skeleton_hkx,
                    compendium=compendium,
                )
                continue
            try:
                return_strings |= self.import_hkx(bl_armature, importer, file_path, skeleton_hkx, hkx_or_entries)
            except Exception as ex:
                # We don't error out here, because we want to continue importing other files.
                self.error(f"Error occurred while importing HKX animation: {ex}")

        return {"FINISHED"} if "FINISHED" in return_strings else {"CANCELLED"}  # at least one finished


# noinspection PyUnusedLocal
def get_binder_entry_choices(self, context):
    return ImportHKXAnimationWithBinderChoice.enum_options


class ImportHKXAnimationWithBinderChoice(LoggingOperator):
    """Presents user with a choice of enums from `enum_choices` class variable (set prior).

    See: https://blender.stackexchange.com/questions/6512/how-to-call-invoke-popup
    """
    bl_idname = "wm.hkx_animation_binder_choice_operator"
    bl_label = "Choose HKX Binder Entry"

    # For deferred import in `execute()`.
    importer: HKXAnimationImporter | None = None
    binder: Binder | None = None
    binder_file_path: Path = Path()
    enum_options: list[tuple[tp.Any, str, str]] = []
    hkx_entries: tp.Sequence[BinderEntry] = []
    bl_armature = None
    skeleton_hkx: SKELETON_TYPING | None = None
    compendium: HKX | None = None

    choices_enum: bpy.props.EnumProperty(items=get_binder_entry_choices)

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

        anim_name = entry.name.split(".")[0]

        self.importer.operator = self
        self.importer.context = context

        self.info(f"Importing HKX animation for {self.bl_armature.name}: {anim_name}")

        p = time.perf_counter()
        animation_hkx.animation_container.spline_to_interleaved()
        self.info(f"Converted spline animation to interleaved in {time.perf_counter() - p:.4f} seconds.")

        track_bone_names = [
            annotation.trackName for annotation in animation_hkx.animation_container.animation.annotationTracks
        ]
        bl_bone_names = [b.name for b in self.bl_armature.data.bones]
        for bone_name in track_bone_names:
            if bone_name not in bl_bone_names:
                raise ValueError(f"Animation bone name '{bone_name}' is missing from selected Blender Armature.")

        p = time.perf_counter()
        arma_frames = get_armature_frames(animation_hkx, self.skeleton_hkx, track_bone_names)
        root_motion = get_root_motion(animation_hkx)
        self.info(f"Constructed armature animation frames in {time.perf_counter() - p:.4f} seconds.")

        p = time.perf_counter()
        try:
            self.importer.create_action(anim_name, arma_frames, root_motion)
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
        importer: HKXAnimationImporter,
        binder_file_path: Path,
        hkx_entries: list[BinderEntry],
        bl_armature,
        skeleton_hkx: SKELETON_TYPING,
        compendium: HKX | None,
    ):
        cls.importer = importer
        cls.binder_file_path = binder_file_path
        cls.enum_options = [(str(i), entry.name, "") for i, entry in enumerate(hkx_entries)]
        cls.hkx_entries = hkx_entries
        cls.bl_armature = bl_armature
        cls.skeleton_hkx = skeleton_hkx
        cls.compendium = compendium
        # noinspection PyUnresolvedReferences
        bpy.ops.wm.hkx_animation_binder_choice_operator("INVOKE_DEFAULT")


class ImportCharacterHKXAnimation(LoggingOperator, ImportHKXAnimationMixin):
    """Detects name of selected character FLVER Armature and finds their ANIBND in the game directory."""
    bl_idname = "import_scene.character_hkx_animation"
    bl_label = "Import Character Anim"
    bl_description = "Import a HKX animation file from the selected character's pre-loaded ANIBND"

    @classmethod
    def poll(cls, context):
        """Armature of a character must be selected."""
        return (
            len(context.selected_objects) == 1
            and context.selected_objects[0].type == "ARMATURE"
            and context.selected_objects[0].name.startswith("c")  # TODO: could require 'c####' template also
        )

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select a single Armature of a character (name starting with 'c').")

        settings = self.settings(context)
        # noinspection PyTypeChecker
        bl_armature = context.selected_objects[0]  # type: bpy.types.ArmatureObject

        character_name = get_bl_obj_tight_name(bl_armature)
        if character_name == "c0000":
            return self.error("Automatic ANIBND import is not yet supported for c0000 (player model).")

        anibnd_path = settings.get_import_file_path(f"chr/{character_name}.anibnd")
        if not anibnd_path or not anibnd_path.is_file():
            return self.error(f"Cannot find ANIBND for character '{character_name}' in game directory.")

        skeleton_anibnd = anibnd = DivBinder.from_path(anibnd_path)
        # TODO: Support c0000 automatic import. Combine all sub-ANIBND entries into one big choice list?
        self.info(f"Importing animation(s) from ANIBND: {anibnd_path}")

        compendium = self.load_binder_compendium(anibnd)
        skeleton_hkx = self.read_skeleton(skeleton_anibnd, compendium)

        # Find animation HKX entry/entries.
        anim_hkx_entries = anibnd.find_entries_matching_name(r"a.*\.hkx(\.dcx)?")
        if not anim_hkx_entries:
            raise HKXAnimationImportError(f"Cannot find any HKX animation files in binder {anibnd_path}.")

        hkxs_with_paths = self.scan_entries(anim_hkx_entries, anibnd_path, skeleton_hkx, compendium)

        importer = HKXAnimationImporter(self, context, bl_armature, bl_armature.name, self.to_60_fps)

        return_strings = set()
        for file_path, skeleton_hkx, hkx_or_entries in hkxs_with_paths:
            if isinstance(hkx_or_entries, list):
                # Defer through entry selection operator.
                ImportHKXAnimationWithBinderChoice.run(
                    importer=importer,
                    binder_file_path=Path(file_path),
                    hkx_entries=hkx_or_entries,
                    bl_armature=bl_armature,
                    skeleton_hkx=skeleton_hkx,
                    compendium=compendium,
                )
                continue
            try:
                return_strings |= self.import_hkx(bl_armature, importer, file_path, skeleton_hkx, hkx_or_entries)
            except Exception as ex:
                # We don't error out here, because we want to continue importing other files.
                self.error(f"Error occurred while importing character HKX animation: {ex}")

        return {"FINISHED"} if "FINISHED" in return_strings else {"CANCELLED"}  # at least one finished


class ImportObjectHKXAnimation(LoggingOperator, ImportHKXAnimationMixin):
    """Detects name of selected object FLVER Armature and finds their OBJBND in the game directory."""
    bl_idname = "import_scene.object_hkx_animation"
    bl_label = "Import Object Anim"
    bl_description = "Import a HKX animation file from the selected object's pre-loaded OBJBND"

    @classmethod
    def poll(cls, context):
        """Armature of an object (o) must be selected."""
        return (
            len(context.selected_objects) == 1
            and context.selected_objects[0].type == "ARMATURE"
            and context.selected_objects[0].name.startswith("o")  # TODO: could require 'o####' template also
        )

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select a single Armature of a object (name starting with 'o').")

        settings = self.settings(context)
        # noinspection PyTypeChecker
        bl_armature = context.selected_objects[0]  # type: bpy.types.ArmatureObject

        object_name = get_bl_obj_tight_name(bl_armature)

        objbnd_path = settings.get_import_file_path(f"obj/{object_name}.anibnd")
        if not objbnd_path or not objbnd_path.is_file():
            return self.error(f"Cannot find OBJBND for '{object_name}' in game directory.")

        objbnd = DivBinder.from_path(objbnd_path)

        # Find ANIBND entry inside OBJBND.
        try:
            anibnd_entry = objbnd[f"{object_name}.anibnd"]
        except EntryNotFoundError:
            return self.error(f"OBJBND of object '{object_name}' has no ANIBND.")
        skeleton_anibnd = anibnd = DivBinder.from_binder_entry(anibnd_entry)

        compendium = self.load_binder_compendium(anibnd)
        skeleton_hkx = self.read_skeleton(skeleton_anibnd, compendium)

        self.info(f"Importing animation(s) from ANIBND inside OBJBND: {objbnd}")

        # Find animation HKX entry/entries.
        anim_hkx_entries = anibnd.find_entries_matching_name(r"a.*\.hkx(\.dcx)?")
        if not anim_hkx_entries:
            return self.error(f"Cannot find any HKX animation files in binder {objbnd_path}.")

        hkxs_with_paths = self.scan_entries(anim_hkx_entries, objbnd_path, skeleton_hkx)

        importer = HKXAnimationImporter(self, context, bl_armature, bl_armature.name, self.to_60_fps)

        return_strings = set()
        for file_path, skeleton_hkx, hkx_or_entries in hkxs_with_paths:
            if isinstance(hkx_or_entries, list):
                # Defer through entry selection operator.
                ImportHKXAnimationWithBinderChoice.run(
                    importer=importer,
                    binder_file_path=Path(file_path),
                    hkx_entries=hkx_or_entries,
                    bl_armature=bl_armature,
                    skeleton_hkx=skeleton_hkx,
                    compendium=compendium,
                )
                continue
            try:
                return_strings |= self.import_hkx(bl_armature, importer, file_path, skeleton_hkx, hkx_or_entries)
            except Exception as ex:
                # We don't error out here, because we want to continue importing other files.
                self.error(f"Error occurred while importing object HKX animation: {ex}")

        return {"FINISHED"} if "FINISHED" in return_strings else {"CANCELLED"}  # at least one finished


class ImportAssetHKXAnimation(LoggingOperator, ImportHKXAnimationMixin):
    """Detects name of selected asset FLVER Armature and finds their OBJBND in the game directory.

    Elden Ring and onwards only.
    """
    bl_idname = "import_scene.asset_hkx_animation"
    bl_label = "Import Asset Anim"
    bl_description = "Import a HKX animation file from the selected asset's pre-loaded GEOMBND"

    @classmethod
    def poll(cls, context):
        """Armature of an object (o) must be selected."""
        return (
            len(context.selected_objects) == 1
            and context.selected_objects[0].type == "ARMATURE"
            and context.selected_objects[0].name.lower().startswith("aeg")  # TODO: could require 'AEG###_###' template
        )

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select a single Armature of an asset (name starting with 'AEG' or 'aeg').")

        settings = self.settings(context)
        # noinspection PyTypeChecker
        bl_armature = context.selected_objects[0]  # type: bpy.types.ArmatureObject

        asset_name = get_bl_obj_tight_name(bl_armature).lower()
        asset_category = asset_name[:6]  # e.g. "aeg099"

        geombnd_path = settings.get_import_file_path(f"asset/aeg/{asset_category}/{asset_name}.geombnd")  # always DCX
        if not geombnd_path or not geombnd_path.is_file():
            return self.error(f"Cannot find OBJBND for '{asset_name}' in game directory.")

        geombnd = Binder.from_path(geombnd_path)

        # Find ANIBND entry inside GEOMBND. Always uppercase.
        anibnd_name = f"{asset_name.upper()}.anibnd"
        try:
            anibnd_entry = geombnd[anibnd_name]
        except EntryNotFoundError:
            return self.error(f"GEOMBND of object '{asset_name}' has no ANIBND '{anibnd_name}'.")
        skeleton_anibnd = anibnd = Binder.from_binder_entry(anibnd_entry)

        compendium = self.load_binder_compendium(anibnd)
        skeleton_hkx = self.read_skeleton(skeleton_anibnd, compendium)

        self.info(f"Importing animation(s) from ANIBND inside GEOMBND: {geombnd}")

        # Find animation HKX entry/entries.
        anim_hkx_entries = anibnd.find_entries_matching_name(r"a.*\.hkx(\.dcx)?")
        if not anim_hkx_entries:
            return self.error(f"Cannot find any HKX animation files in binder {geombnd_path}.")

        hkxs_with_paths = self.scan_entries(anim_hkx_entries, geombnd_path, skeleton_hkx)

        importer = HKXAnimationImporter(self, context, bl_armature, bl_armature.name, self.to_60_fps)

        return_strings = set()
        for file_path, skeleton_hkx, hkx_or_entries in hkxs_with_paths:
            if isinstance(hkx_or_entries, list):
                # Defer through entry selection operator.
                ImportHKXAnimationWithBinderChoice.run(
                    importer=importer,
                    binder_file_path=Path(file_path),
                    hkx_entries=hkx_or_entries,
                    bl_armature=bl_armature,
                    skeleton_hkx=skeleton_hkx,
                    compendium=compendium,
                )
                continue
            try:
                return_strings |= self.import_hkx(bl_armature, importer, file_path, skeleton_hkx, hkx_or_entries)
            except Exception as ex:
                # We don't error out here, because we want to continue importing other files.
                self.error(f"Error occurred while importing asset HKX animation: {ex}")

        return {"FINISHED"} if "FINISHED" in return_strings else {"CANCELLED"}  # at least one finished
