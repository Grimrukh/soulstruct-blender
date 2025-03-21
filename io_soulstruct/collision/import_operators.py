"""
Import HKX files (with/without DCX) into Blender 3.3+ (Python 3.10+ scripting required).

The HKX's subparts are imported as separate meshes, parented to a single Empty named after the collision. The only
relevant data aside from the mesh vertices/faces are `material_index` custom properties on each subpart.

TODO: Currently only supports map collision HKX files from Dark Souls Remastered.
"""
from __future__ import annotations

__all__ = [
    "ImportHKXMapCollision",
    "ImportHKXMapCollisionWithBinderChoice",
    "ImportMapHKXMapCollision",
]

import shutil
import tempfile

import re
import traceback
import typing as tp
from pathlib import Path

import bpy

from soulstruct.containers import BinderEntry, EntryNotFoundError
from soulstruct.games import DARK_SOULS_PTDE, DEMONS_SOULS
from soulstruct_havok.fromsoft.shared import MapCollisionModel, BothResHKXBHD

from io_soulstruct.exceptions import MapCollisionImportError
from io_soulstruct.utilities import *
from .types import BlenderMapCollision

HKX_NAME_RE = re.compile(r".*\.hkx(\.dcx)?")
HKXBHD_NAME_RE = re.compile(r"^[hl].*\.hkxbhd(\.dcx)?$")


class HKXImportInfo(tp.NamedTuple):
    """Holds information about a HKX to import into Blender."""
    model_name: str
    hi_collision: MapCollisionModel
    lo_collision: MapCollisionModel


class ImportHKXMapCollision(LoggingImportOperator):
    """Most generic importer. Loads standalone HKX files or HKX entries from a HKXBHD Binder (one/all)."""

    bl_idname = "import_scene.hkx_map_collision"
    bl_label = "Import Map Collision"
    bl_description = "Import a HKX map collision file. Can import from HKXBHD split Binders and handles DCX compression"

    filter_glob: bpy.props.StringProperty(
        default="*.hkx;*.hkx.dcx;*.hkxbhd",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    collision_model_id: bpy.props.IntProperty(
        name="Collision Model ID",
        description="Model ID of the collision model to import (e.g. 200 for 'h0200'). Leave as -1 to have a choice "
                    "pop-up appear",
        default=-1,
    )

    import_all_from_binder: bpy.props.BoolProperty(
        name="Import All From Binder",
        description="If a Binder file is opened, import all HKX files rather than being prompted to select one. "
                    "Will only import HKX files that match 'Collision Model ID' (if not -1)",
        default=False,
    )

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'})

    def invoke(self, context, _event):
        """Set the initial directory based on Global Settings."""
        try:
            map_dir = self.settings(context).get_import_map_dir_path()
        except NotADirectoryError:
            return super().invoke(context, _event)

        self.directory = str(map_dir)
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):

        file_paths = [Path(self.directory, file.name) for file in self.files]
        import_infos = []  # type: list[HKXImportInfo | BothResHKXBHD]

        for file_path in file_paths:

            if HKXBHD_NAME_RE.match(file_path.name):
                both_res_hkxbhd = BothResHKXBHD.from_map_path(file_path.parent)
                if self.import_all_from_binder:
                    both_res_hkxbhd.hi_res.load_all()
                    both_res_hkxbhd.lo_res.load_all()
                    import_infos.extend([
                        HKXImportInfo(f"h{hkx_stem}", hi_collision, lo_collision)
                        for hkx_stem, (hi_collision, lo_collision) in both_res_hkxbhd.get_both_res_dict()
                    ])
                elif self.collision_model_id != -1:
                    hi_hkx_entries = [
                        entry for entry in both_res_hkxbhd.hi_res.entries if self.check_hkx_entry_model_id(entry)
                    ]
                    if not hi_hkx_entries:
                        raise MapCollisionImportError(
                            f"Found no entry with model ID {self.collision_model_id} in hi-res HKXBHD."
                        )
                    if len(hi_hkx_entries) > 1:
                        raise MapCollisionImportError(
                            f"Found multiple entries with model ID {self.collision_model_id} in hi-res HKXBHD."
                        )
                    lo_hkx_entries = [
                        entry for entry in both_res_hkxbhd.lo_res.entries if self.check_hkx_entry_model_id(entry)
                    ]
                    if not lo_hkx_entries:
                        raise MapCollisionImportError(
                            f"Found no entry with model ID {self.collision_model_id} in lo-res HKXBHD."
                        )
                    if len(lo_hkx_entries) > 1:
                        raise MapCollisionImportError(
                            f"Found multiple entries with model ID {self.collision_model_id} in lo-res HKXBHD."
                        )
                    # Import single specified collision model.
                    import_infos.append(
                        HKXImportInfo(
                            hi_hkx_entries[0].minimal_stem,
                            hi_hkx_entries[0].to_binary_file(MapCollisionModel),
                            lo_hkx_entries[0].to_binary_file(MapCollisionModel),
                        )
                    )
                else:
                    # Defer through Binder choice operator.
                    import_infos.append(both_res_hkxbhd)
            else:
                # Loose HKX. Load directly and search for other res loose file.
                try:
                    collision = MapCollisionModel.from_path(file_path)
                except Exception as ex:
                    self.warning(f"Error occurred while reading HKX file '{file_path.name}': {ex}")
                else:
                    if file_path.name.startswith("h"):
                        hi_collision = collision
                        try:
                            lo_collision = MapCollisionModel.from_path(file_path.parent / f"l{file_path.name[1:]}")
                        except FileNotFoundError:
                            self.warning(f"Could not find matching 'lo' HKX next to '{file_path.name}'.")
                            lo_collision = None
                    elif file_path.name.startswith("l"):
                        lo_collision = collision
                        try:
                            hi_collision = MapCollisionModel.from_path(file_path.parent / f"h{file_path.name[1:]}")
                        except FileNotFoundError:
                            self.warning(f"Could not find matching 'hi' HKX next to '{file_path.name}'.")
                            hi_collision = None
                    else:
                        hi_collision = collision  # treat unknown file name as hi-res
                        lo_collision = None
                    import_infos.append(HKXImportInfo(file_path.name.split(".")[0], hi_collision, lo_collision))

        for import_info in import_infos:

            if isinstance(import_info, BothResHKXBHD):
                # Defer through entry selection operator.
                ImportHKXMapCollisionWithBinderChoice.run(import_info)
                continue

            self.info(f"Importing HKX: {import_info.model_name}")

            # Import single HKX.
            try:
                BlenderMapCollision.new_from_soulstruct_obj(
                    self,
                    context,
                    import_info.hi_collision,
                    import_info.model_name,
                    lo_collision=import_info.lo_collision,
                )
            except Exception as ex:
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import HKX: {import_info.model_name}. Error: {ex}")

        return {"FINISHED"}

    def check_hkx_entry_model_id(self, hkx_entry: BinderEntry) -> bool:
        """Checks if the given HKX Binder entry matches the given collision model ID."""
        try:
            entry_model_id = int(hkx_entry.name[1:5])  # e.g. 'h1234' -> 1234
        except ValueError:
            return False  # not a match (weird HKX name)
        return entry_model_id == self.collision_model_id


# noinspection PyUnusedLocal
def get_binder_entry_choices(self, context):
    return ImportHKXMapCollisionWithBinderChoice.enum_options


class ImportHKXMapCollisionWithBinderChoice(LoggingOperator):
    """Presents user with a choice of enums from `enum_choices` class variable (set prior).

    See: https://blender.stackexchange.com/questions/6512/how-to-call-invoke-popup
    """
    bl_idname = "wm.hkx_map_collision_binder_choice_operator"
    bl_label = "Choose HKX Collision Binder Entry"

    # For deferred import in `execute()`.
    both_res_hkxbhd: BothResHKXBHD = None
    enum_options: list[tuple[tp.Any, str, str]] = []

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
        model_name = f"h{self.choices_enum.split('.')[0]}"
        hi_collision, lo_collision = self.both_res_hkxbhd.get_both_hkx(
            model_name,
            allow_missing_hi=True,
            allow_missing_lo=True,
        )

        try:
            BlenderMapCollision.new_from_soulstruct_obj(
                self,
                context,
                hi_collision,
                model_name,
                lo_collision=lo_collision,
            )
        except Exception as ex:
            traceback.print_exc()
            return self.error(
                f"Cannot import HKX '{model_name}' from '{self.both_res_hkxbhd.path}'. Error: {ex}"
            )

        return {"FINISHED"}

    @classmethod
    def run(cls, both_res_hkxbhd: BothResHKXBHD):
        cls.both_res_hkxbhd = both_res_hkxbhd
        enum_options = []
        for model_id, (hi_name, lo_name) in both_res_hkxbhd.get_both_res_entries_dict().items():
            if not hi_name:
                enum_options.append((model_id, lo_name, "Lo-res collision only"))
            elif not lo_name:
                enum_options.append((model_id, hi_name, "Hi-res collision only"))
            else:
                enum_options.append((model_id, hi_name, "Both hi-res and lo-res collision"))
        cls.enum_options = enum_options
        # noinspection PyUnresolvedReferences
        bpy.ops.wm.hkx_map_collision_binder_choice_operator("INVOKE_DEFAULT")


class ImportMapHKXMapCollision(LoggingOperator):
    bl_idname = "import_scene.map_hkx_map_collision"
    bl_label = "Import Map Collision"
    bl_description = "Import selected HKX map collision entry from selected game map HKXBHD"

    # Set by `invoke` when entry choices are written to temp directory (for DSR).
    both_res_hkxbhd: BothResHKXBHD

    temp_directory: bpy.props.StringProperty(
        name="Temp HKXBHD Directory",
        description="Temporary directory containing hi-res HKXBHD entry choices",
        default="",
        options={'HIDDEN'},
    )

    filter_glob: bpy.props.StringProperty(
        default="*.hkx;*.hkx.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Chosen HKXBHD entry",
        maxlen=1024,
        subtype="FILE_PATH",
    )
    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'})

    ENTRY_NAME_RE = re.compile(r"\((\d+)\) (.+)")

    @classmethod
    def poll(cls, context) -> bool:
        settings = cls.settings(context)
        map_stem = settings.get_oldest_map_stem_version()  # collision uses oldest
        if not settings.game_config.supports_collision_model:
            return False
        # Either loose HKX files in map directory (PTDE) or a pair of resolution HKXBHDs (DSR).
        try:
            settings.get_import_map_dir_path(map_stem=map_stem)
        except NotADirectoryError:
            return False
        return True

    @classmethod
    def get_both_res_hkxbhd(cls, context) -> BothResHKXBHD | None:
        settings = cls.settings(context)
        oldest_map_stem = settings.get_oldest_map_stem_version()
        try:
            map_dir = settings.get_import_map_dir_path(map_stem=oldest_map_stem)
        except NotADirectoryError:
            return None
        return BothResHKXBHD.from_map_path(map_dir)

    def invoke(self, context, event):
        """Unpack valid Binder entry choices to temp directory for user to select from."""
        if self.temp_directory:
            shutil.rmtree(self.temp_directory, ignore_errors=True)
            self.temp_directory = ""

        settings = self.settings(context)
        if settings.is_game(DEMONS_SOULS, DARK_SOULS_PTDE):
            # HKX files are already loose. Just use map folder (oldest).
            try:
                map_dir = settings.get_import_map_dir_path(map_stem=settings.get_oldest_map_stem_version())
            except NotADirectoryError as ex:
                return self.error(f"Could not find map directory. Error: {ex}")
            self.directory = str(map_dir)
            context.window_manager.fileselect_add(self)
            return {"RUNNING_MODAL"}

        # Dark Souls Remastered needs an unpacked `BothResHKXBHD`.
        map_stem = settings.get_oldest_map_stem_version()
        self.both_res_hkxbhd = self.get_both_res_hkxbhd(context)
        if self.both_res_hkxbhd is None:
            return self.error("No Binders could be loaded for HKX Map Collision model import.")

        self.temp_directory = tempfile.mkdtemp(suffix="_" + map_stem)
        for entry in self.both_res_hkxbhd.hi_res.entries:
            # We use the index to ensure unique file names while allowing duplicate entry names (e.g. Regions).
            file_name = f"({entry.id}) {entry.name}"  # name will include extension
            file_path = Path(self.temp_directory, file_name)
            with file_path.open("w") as f:
                f.write(entry.name)

        # No subdirectories used.
        # TODO: Can't get this to work after the first time. Last `filepath` seems to mess it up, but setting it to ""
        #  just puts the window in Documents, even though the `directory` is correct.
        self.directory = self.temp_directory
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def get_selected_collision_pairs(self, context: Context) -> list[tuple[MapCollisionModel, MapCollisionModel]]:

        collision_pairs = []  # type: list[tuple[MapCollisionModel, MapCollisionModel]]
        settings = self.settings(context)

        if settings.is_game(DEMONS_SOULS, DARK_SOULS_PTDE):
            # DeS and PTDE read loose HKX files from map folder.
            file_paths = [Path(self.directory, file.name) for file in self.files]
            for path in file_paths:
                if path.name.startswith("h"):
                    hi_hkx_path = path
                    lo_hkx_path = Path(path.parent / f"l{path.name[1:]}")
                    if not lo_hkx_path.is_file():
                        self.warning(f"Could not find matching 'lo' HKX next to '{path.name}'. Ignoring collision.")
                        continue
                elif path.name.startswith("l"):
                    lo_hkx_path = path
                    hi_hkx_path = Path(path.parent / f"h{path.name[1:]}")
                    if not hi_hkx_path.is_file():
                        self.warning(f"Could not find matching 'hi' HKX next to '{path.name}'. Ignoring collision.")
                        continue
                else:
                    self.error(f"Unexpected HKX file name: {path.name}. It should start with 'h' or 'l'.")
                    continue

                try:
                    hi_collision = MapCollisionModel.from_path(hi_hkx_path)
                except Exception as ex:
                    self.error(f"Error reading hi-res HKX '{path}': {ex}")
                    continue
                try:
                    lo_collision = MapCollisionModel.from_path(lo_hkx_path)
                except Exception as ex:
                    self.error(f"Error reading lo-res HKX '{path}': {ex}")
                    continue

                collision_pairs.append((hi_collision, lo_collision))
            return collision_pairs

        # Dark Souls: Remastered reads HKX files from temporary unpacked HKXBHDs.
        if not getattr(self, "temp_directory", None):
            self.error("No Binder loaded. Did you cancel the file selection?")
            return []

        file_paths = [Path(self.directory, file.name) for file in self.files]
        for path in file_paths:
            match = self.ENTRY_NAME_RE.match(path.stem)
            if not match:
                self.error(f"Selected file does not match expected format '(i) Name': {self.filepath}")
                return []  # one error cancels all imports

            entry_id, entry_name = int(match.group(1)), match.group(2)
            try:
                hi_collision, lo_collision = self.both_res_hkxbhd.get_both_hkx(entry_name)  # neither can be missing
            except EntryNotFoundError as ex:
                self.error(f"Error reading HKX for '{entry_name}': {ex}")
                return []
            collision_pairs.append((hi_collision, lo_collision))
        return collision_pairs

    def execute(self, context):
        try:
            hkx_pairs = self.get_selected_collision_pairs(context)  # temp directory (DSR) or genuine loose files
            if not hkx_pairs:
                return {"CANCELLED"}  # relevant error already reported
            for hi_collision, lo_collision in hkx_pairs:
                try:
                    self._import_collision_pair(context, hi_collision, lo_collision)
                except Exception as ex:
                    self.error(f"Error occurred while importing HKX '{hi_collision.path_name}': {ex}")
                    return {"CANCELLED"}
            return {"FINISHED"}
        finally:
            if self.temp_directory:
                shutil.rmtree(self.temp_directory, ignore_errors=True)
                self.temp_directory = ""

    def _import_collision_pair(self, context, hi_collision: MapCollisionModel, lo_collision: MapCollisionModel):

        settings = self.settings(context)
        map_stem = settings.get_oldest_map_stem_version()
        # NOTE: Currently no Map Collision model import settings.

        collection = find_or_create_collection(
            context.scene.collection, "Models", f"{map_stem} Models", f"{map_stem} Collision Models"
        )

        # Import single HKX.
        model_name = hi_collision.path_minimal_stem  # set by `BothResHKXBHD` entry loader
        try:
            bl_map_collision = BlenderMapCollision.new_from_soulstruct_obj(
                self, context, hi_collision, model_name, collection=collection, lo_collision=lo_collision
            )
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            return self.error(f"Cannot import HKX '{model_name}' from HKXBHDs in map {map_stem}. Error: {ex}")

        self.info(f"Imported HKX map collision '{bl_map_collision.name}' from {model_name} in map {map_stem}.")

        # Select and frame view on newly imported Mesh.
        self.set_active_obj(bl_map_collision.obj)
        bpy.ops.view3d.view_selected(use_all_regions=False)

        return {"FINISHED"}
