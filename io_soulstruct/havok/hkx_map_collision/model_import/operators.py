"""
Import HKX files (with/without DCX) into Blender 3.3+ (Python 3.10+ scripting required).

The HKX's subparts are imported as separate meshes, parented to a single Empty named after the collision. The only
relevant data aside from the mesh vertices/faces are `material_index` custom properties on each subpart.

TODO: Currently only supports map collision HKX files from Dark Souls Remastered.
"""
from __future__ import annotations

__all__ = [
    "HKXImportInfo",
    "HKXMapCollisionImportError",
    "ImportHKXMapCollision",
    "ImportHKXMapCollisionWithBinderChoice",
    "ImportHKXMapCollisionFromHKXBHD",
]

import time
import re
import traceback
import typing as tp
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper

from soulstruct.containers import BinderEntry

from soulstruct_havok.wrappers.hkx2015 import MapCollisionHKX
from soulstruct_havok.wrappers.hkx2015.hkx_binder import BothResHKXBHD

from io_soulstruct.general import SoulstructGameEnums
from io_soulstruct.utilities import *
from .core import *
from .settings import *


HKX_NAME_RE = re.compile(r".*\.hkx(\.dcx)?")
HKXBHD_NAME_RE = re.compile(r"^[hl].*\.hkxbhd(\.dcx)?$")


class ImportHKXMapCollision(LoggingOperator, ImportHelper):
    """Most generic importer. Loads standalone HKX files or HKX entries from a HKXBHD Binder (one/all)."""

    bl_idname = "import_scene.hkx_map_collision"
    bl_label = "Import Map Collision"
    bl_description = "Import a HKX map collision file. Can import from HKXBHD split Binders and handles DCX compression"

    filename_ext = ".hkx"

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

    merge_submeshes: bpy.props.BoolProperty(
        name="Merge Submeshes",
        description="Merge all submeshes into a single mesh, using material to define submeshes",
        default=False,
    )

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'})

    def invoke(self, context, _event):
        """Set the initial directory based on Global Settings."""
        map_path = self.settings(context).get_import_map_path()
        if map_path and map_path.is_dir():
            self.directory = str(map_path)
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        return super().invoke(context, _event)

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
                        HKXImportInfo(f"h{hkx_stem}", hi_hkx, lo_hkx)
                        for hkx_stem, (hi_hkx, lo_hkx) in both_res_hkxbhd.get_both_res_dict()
                    ])
                elif self.collision_model_id != -1:
                    hi_hkx_entries = [
                        entry for entry in both_res_hkxbhd.hi_res.entries if self.check_hkx_entry_model_id(entry)
                    ]
                    if not hi_hkx_entries:
                        raise HKXMapCollisionImportError(
                            f"Found no entry with model ID {self.collision_model_id} in hi-res HKXBHD."
                        )
                    if len(hi_hkx_entries) > 1:
                        raise HKXMapCollisionImportError(
                            f"Found multiple entries with model ID {self.collision_model_id} in hi-res HKXBHD."
                        )
                    lo_hkx_entries = [
                        entry for entry in both_res_hkxbhd.lo_res.entries if self.check_hkx_entry_model_id(entry)
                    ]
                    if not lo_hkx_entries:
                        raise HKXMapCollisionImportError(
                            f"Found no entry with model ID {self.collision_model_id} in lo-res HKXBHD."
                        )
                    if len(lo_hkx_entries) > 1:
                        raise HKXMapCollisionImportError(
                            f"Found multiple entries with model ID {self.collision_model_id} in lo-res HKXBHD."
                        )
                    # Import single specified collision model.
                    import_infos.append(
                        HKXImportInfo(
                            hi_hkx_entries[0].minimal_stem,
                            hi_hkx_entries[0].to_binary_file(MapCollisionHKX),
                            lo_hkx_entries[0].to_binary_file(MapCollisionHKX),
                        )
                    )
                else:
                    # Defer through Binder choice operator.
                    import_infos.append(both_res_hkxbhd)
            else:
                # Loose HKX. Load directly and search for other res loose file.
                try:
                    hkx = MapCollisionHKX.from_path(file_path)
                except Exception as ex:
                    self.warning(f"Error occurred while reading HKX file '{file_path.name}': {ex}")
                else:
                    if file_path.name.startswith("h"):
                        hi_hkx = hkx
                        try:
                            lo_hkx = MapCollisionHKX.from_path(file_path.parent / f"l{file_path.name[1:]}")
                        except FileNotFoundError:
                            self.warning(f"Could not find matching 'lo' HKX next to '{file_path.name}'.")
                            lo_hkx = None
                    elif file_path.name.startswith("l"):
                        lo_hkx = hkx
                        try:
                            hi_hkx = MapCollisionHKX.from_path(file_path.parent / f"h{file_path.name[1:]}")
                        except FileNotFoundError:
                            self.warning(f"Could not find matching 'hi' HKX next to '{file_path.name}'.")
                            hi_hkx = None
                    else:
                        hi_hkx = hkx  # treat unknown file name as hi-res
                        lo_hkx = None
                    import_infos.append(HKXImportInfo(file_path.name.split(".")[0], hi_hkx, lo_hkx))

        for import_info in import_infos:

            if isinstance(import_info, BothResHKXBHD):
                # Defer through entry selection operator.
                ImportHKXMapCollisionWithBinderChoice.run(import_info, self.merge_submeshes)
                continue

            self.info(f"Importing HKX: {import_info.model_name}")

            # Import single HKX.
            try:
                if self.merge_submeshes:
                    # Single mesh object.
                    hkx_model = import_hkx_model_merged(
                        import_info.hi_hkx, import_info.model_name, lo_hkx=import_info.lo_hkx
                    )
                else:
                    # Empty parent of submesh objects.
                    hkx_model = import_hkx_model_split(
                        import_info.hi_hkx, import_info.model_name, lo_hkx=import_info.lo_hkx
                    )
            except Exception as ex:
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import HKX: {import_info.model_name}. Error: {ex}")
            context.scene.collection.objects.link(hkx_model)
            for child in hkx_model.children:
                context.scene.collection.objects.link(child)

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
    merge_submeshes: bool = False
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
        hi_hkx, lo_hkx = self.both_res_hkxbhd.get_both_hkx(
            model_name,
            allow_missing_hi=True,
            allow_missing_lo=True,
        )

        try:
            if self.merge_submeshes:
                # Single mesh object.
                hkx_model = import_hkx_model_merged(hi_hkx, model_name, lo_hkx)
            else:
                # Empty parent of submesh objects.
                hkx_model = import_hkx_model_split(hi_hkx, model_name, lo_hkx)
        except Exception as ex:
            traceback.print_exc()
            return self.error(
                f"Cannot import HKX '{model_name}' from '{self.both_res_hkxbhd.path}'. Error: {ex}"
            )
        context.scene.collection.objects.link(hkx_model)
        for child in hkx_model.children:
            context.scene.collection.objects.link(child)

        return {"FINISHED"}

    @classmethod
    def run(cls, both_res_hkxbhd: BothResHKXBHD, merge_submeshes: bool):
        cls.merge_submeshes = merge_submeshes
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


class ImportHKXMapCollisionFromHKXBHD(LoggingOperator):
    bl_idname = "import_scene.hkx_map_collision_entry"
    bl_label = "Import Map Collision"
    bl_description = "Import selected HKX map collision entry from selected game map HKXBHD"

    @classmethod
    def poll(cls, context):
        game_lists = context.scene.soulstruct_game_enums  # type: SoulstructGameEnums
        return game_lists.hkx_map_collision not in {"", "0"}

    def execute(self, context):

        start_time = time.perf_counter()

        settings = self.settings(context)
        settings.save_settings()
        game_lists = context.scene.soulstruct_game_enums  # type: SoulstructGameEnums

        hkx_entry_name = game_lists.hkx_map_collision
        if hkx_entry_name in {"", "0"}:
            return self.error("No HKX map collision entry selected.")

        # Get oldest version of map folder, if option enabled.
        map_stem = settings.get_oldest_map_stem_version()

        collision_import_settings = context.scene.hkx_map_collision_import_settings  # type: HKXMapCollisionImportSettings

        try:
            # Import source may depend on suffix of entry enum.
            if hkx_entry_name.endswith(" (G)"):
                both_res_hkxbhd = BothResHKXBHD.from_map_path(settings.get_game_map_path(map_stem=map_stem))
            elif hkx_entry_name.endswith(" (P)"):
                both_res_hkxbhd = BothResHKXBHD.from_map_path(settings.get_project_map_path(map_stem=map_stem))
            else:  # no suffix, so we use whichever source is preferred
                both_res_hkxbhd = BothResHKXBHD.from_map_path(settings.get_import_map_path(map_stem=map_stem))
        except Exception as ex:
            return self.error(f"Could not load HKXBHD for map '{map_stem}'. Error: {ex}")

        # Import single HKX.
        model_name = hkx_entry_name.split(".")[0]
        hi_hkx, lo_hkx = both_res_hkxbhd.get_both_hkx(model_name)
        try:
            if collision_import_settings.merge_submeshes:
                # Single mesh object.
                hkx_model = import_hkx_model_merged(hi_hkx, model_name, lo_hkx)
            else:
                # Empty parent of submesh objects.
                hkx_model = import_hkx_model_split(hi_hkx, model_name, lo_hkx)
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            return self.error(f"Cannot import HKX '{model_name}' from HKXBHDs in {map_stem}. Error: {ex}")
        collection = get_collection(f"{map_stem} Collision Models", context.scene.collection, hide_viewport=False)
        collection.objects.link(hkx_model)
        for child in hkx_model.children:
            collection.objects.link(child)

        p = time.perf_counter() - start_time
        self.info(
            f"Imported HKX map collision '{hkx_model.name}' from {model_name} in map {map_stem} in {p} s."
        )

        # Select and frame view on newly imported Mesh.
        self.set_active_obj(hkx_model)
        if collision_import_settings.merge_submeshes:
            bpy.ops.view3d.view_selected(use_all_regions=False)

        return {"FINISHED"}
