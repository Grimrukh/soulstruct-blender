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
    "ImportHKXMapCollisionFromHKXBHD",
    "ImportMSBMapCollision",
]

import time
import re
import traceback
import typing as tp
from pathlib import Path

import numpy as np

import bpy
from bpy_extras.io_utils import ImportHelper

from soulstruct.containers import Binder, BinderEntry, EntryNotFoundError

from soulstruct_havok.wrappers.hkx2015 import MapCollisionHKX

from io_soulstruct.general import SoulstructSettings, SoulstructGameEnums
from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.utilities import *
from io_soulstruct.utilities.materials import *
from .utilities import *

if tp.TYPE_CHECKING:
    from soulstruct.darksouls1r.maps.msb import MSB


HKX_NAME_RE = re.compile(r".*\.hkx(\.dcx)?")
HKX_BINDER_RE = re.compile(r"^.*?\.hkxbhd(\.dcx)?$")


class HKXImportInfo(tp.NamedTuple):
    """Holds information about a HKX to import into Blender."""
    path: Path  # source file for HKX (possibly a Binder path)
    hkx_name: str  # name of HKX file or Binder entry
    hkx: MapCollisionHKX  # parsed HKX


class HKXImportChoiceInfo(tp.NamedTuple):
    """Holds information about a Binder entry choice that the user will make in deferred operator."""
    path: Path  # Binder path
    entries: list[BinderEntry]  # entries from which user must choose


class ImportHKXMapCollision(LoggingOperator, ImportHelper):
    bl_idname = "import_scene.hkx_map_collision"
    bl_label = "Import Map Collision"
    bl_description = "Import a HKX map collision file. Can import from BHD/BDT binders and handles DCX compression"

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

    load_other_resolution: bpy.props.BoolProperty(
        name="Load Other Resolution",
        description="Try to load the other resolution (Hi/Lo) of the selected HKX (possibly in another Binder) and "
                    "parent them under the same empty object with optional MSB transform",
        default=True,
    )

    use_material: bpy.props.BoolProperty(
        name="Use Material",
        description="If enabled, 'HKX Hi' or 'HKX Lo' material will be assigned or created for all collision meshes",
        default=True,
    )

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        print("Executing HKX collision import...")

        file_paths = [Path(self.directory, file.name) for file in self.files]
        import_infos = []  # type: list[HKXImportInfo | HKXImportChoiceInfo]

        # If `load_other_resolutions = True`, this maps actual opened file paths to their other-res HKX files.
        # NOTE: Does NOT handle paths that need an entry to be chosen by the user (with queued Binder entries).
        # Those will be handled in the 'BinderChoice' operator.
        other_res_hkxs = {}  # type: dict[tuple[Path, str], MapCollisionHKX]

        for file_path in file_paths:

            new_non_choice_import_infos = []
            is_binder = HKX_BINDER_RE.match(file_path.name) is not None

            if is_binder:
                binder = Binder.from_path(file_path)
                new_import_infos = self.load_from_binder(binder, file_path)
                import_infos.extend(new_import_infos)
                new_non_choice_import_infos = [info for info in new_import_infos if isinstance(info, HKXImportInfo)]
            else:
                # Loose HKX.
                try:
                    hkx = MapCollisionHKX.from_path(file_path)
                except Exception as ex:
                    self.warning(f"Error occurred while reading HKX file '{file_path.name}': {ex}")
                else:
                    new_non_choice_import_infos = [HKXImportInfo(file_path, file_path.name, hkx)]
                    import_infos.extend(new_non_choice_import_infos)

            if self.load_other_resolution and new_non_choice_import_infos:
                for import_info in new_non_choice_import_infos:
                    other_res_hkx = load_other_res_hkx(self, file_path, import_info, is_binder)
                    if other_res_hkx:
                        other_res_hkxs[(import_info.path, import_info.hkx_name)] = other_res_hkx

        importer = HKXMapCollisionImporter(self, context)

        for import_info in import_infos:

            if isinstance(import_info, HKXImportChoiceInfo):
                # Defer through entry selection operator.
                ImportHKXMapCollisionWithBinderChoice.run(
                    importer=importer,
                    binder_file_path=import_info.path,
                    load_other_resolution=self.load_other_resolution,
                    use_material=self.use_material,
                    hkx_entries=import_info.entries,
                )
                continue

            hkx = import_info.hkx
            hkx_model_name = import_info.hkx_name.split(".")[0]
            other_res_hkx = other_res_hkxs.get((import_info.path, import_info.hkx_name), None)

            self.info(f"Importing HKX: {hkx_model_name}")

            # Import single HKX.
            try:
                hkx_parent = importer.import_hkx(hkx, bl_name=hkx_model_name, use_material=self.use_material)
            except Exception as ex:
                # Delete any objects created prior to exception.
                for obj in importer.all_bl_objs:
                    bpy.data.objects.remove(obj)
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import HKX: {import_info.path}. Error: {ex}")

            if other_res_hkx is not None:
                # Import other-res HKX.
                other_res_hkx_model_name = other_res_hkx.path.name.split(".")[0]
                try:
                    importer.import_hkx(
                        other_res_hkx,
                        bl_name=other_res_hkx_model_name,
                        use_material=self.use_material,
                        existing_parent=hkx_parent,
                    )
                except Exception as ex:
                    # Delete any objects created prior to exception.
                    for obj in importer.all_bl_objs:
                        bpy.data.objects.remove(obj)
                    traceback.print_exc()  # for inspection in Blender console
                    return self.error(f"Cannot import other-res HKX for {import_info.path}. Error: {ex}")

        return {"FINISHED"}

    def load_from_binder(self, binder: Binder, file_path: Path) -> list[HKXImportInfo | HKXImportChoiceInfo]:
        """Load one or more `MapCollisionHKX` files from a `Binder` and queue them for import.

        Will queue up a list of Binder entries if `self.import_all_from_binder` is False and `collision_model_id`
        import setting is -1.

        Returns a list of `HKXImportInfo` or `HKXImportChoiceInfo` objects, depending on whether the Binder contains
        multiple entries that the user may need to choose from.
        """
        # Find HKX entry.
        hkx_entries = binder.find_entries_matching_name(HKX_NAME_RE)
        if not hkx_entries:
            raise HKXMapCollisionImportError(f"Cannot find any '.hkx{{.dcx}}' files in binder {file_path}.")
        # Filter by `collision_model_id` if needed.
        if self.collision_model_id != -1:
            hkx_entries = [entry for entry in hkx_entries if self.check_hkx_entry_model_id(entry)]
        if not hkx_entries:
            raise HKXMapCollisionImportError(
                f"Found '.hkx{{.dcx}}' files, but none with model ID {self.collision_model_id} in binder {file_path}."
            )

        if len(hkx_entries) > 1:
            # Binder contains multiple (matching) entries.
            if self.import_all_from_binder:
                # Load all detected/matching KX entries in binder and queue them for import.
                new_import_infos = []  # type: list[HKXImportInfo]
                for entry in hkx_entries:
                    try:
                        hkx = entry.to_binary_file(MapCollisionHKX)
                    except Exception as ex:
                        self.warning(f"Error occurred while reading HKX Binder entry '{entry.name}': {ex}")
                    else:
                        hkx.path = Path(entry.name)  # also done in `GameFile`, but explicitly needed below
                        new_import_infos.append(HKXImportInfo(file_path, entry.name, hkx))
                return new_import_infos

            # Queue up all matching Binder entries instead of loaded HKX instances; user will choose entry in pop-up.
            return [HKXImportChoiceInfo(file_path, hkx_entries)]

        # Binder only contains one (matching) HKX.
        try:
            hkx = hkx_entries[0].to_binary_file(MapCollisionHKX)
        except Exception as ex:
            self.warning(f"Error occurred while reading HKX Binder entry '{hkx_entries[0].name}': {ex}")
            return []

        return [HKXImportInfo(file_path, hkx_entries[0].name, hkx)]

    def check_hkx_entry_model_id(self, hkx_entry: BinderEntry) -> bool:
        """Checks if the given HKX Binder entry matches the given collision model ID."""
        try:
            entry_model_id = int(hkx_entry.name[1:5])  # e.g. 'h1234' -> 1234
        except ValueError:
            return False  # not a match (weird HKX name)
        return entry_model_id == self.collision_model_id


def load_other_res_hkx(
    operator: LoggingOperator, file_path: Path, import_info: HKXImportInfo, is_binder: bool
) -> MapCollisionHKX | None:
    match import_info.hkx_name[0]:
        case "h":
            other_res = "l"
        case "l":
            other_res = "h"
        case _:
            operator.warning(f"Could not determine resolution (h/l) of HKX '{import_info.hkx_name}'.")
            return None
    if is_binder:
        # Look for other-resolution binder and find matching other-res HKX entry.
        other_res_binder_path = file_path.parent / f"{other_res}{file_path.name[1:]}"
        if not other_res_binder_path.is_file():
            operator.warning(
                f"Could not find corresponding '{other_res}' collision binder for '{file_path.name}'."
            )
            return None
        other_res_binder = Binder.from_path(other_res_binder_path)
        other_hkx_name = f"{other_res}{import_info.hkx_name[1:]}"
        try:
            other_res_hkx_entry = other_res_binder.find_entry_name(other_hkx_name)
        except EntryNotFoundError:
            operator.warning(
                f"Found corresponding '{other_res}' collision binder, but could not find corresponding "
                f"HKX entry '{other_hkx_name}' inside it."
            )
            return None
        try:
            other_res_hkx = MapCollisionHKX.from_binder_entry(other_res_hkx_entry)
        except Exception as ex:
            operator.warning(
                f"Error occurred while reading corresponding '{other_res}' HKX file "
                f"'{other_res_hkx_entry.path}': {ex}"
            )
            return None
        return other_res_hkx

    # Look for other-resolution loose HKX in same directory.
    other_hkx_path = file_path.parent / f"{other_res}{file_path.name[1:]}"
    if not other_hkx_path.is_file():
        operator.warning(
            f"Could not find corresponding '{other_res}' collision HKX for '{file_path.name}'."
        )
        return None
    try:
        other_res_hkx = MapCollisionHKX.from_path(other_hkx_path)
    except Exception as ex:
        operator.warning(
            f"Error occurred while reading corresponding '{other_res}' HKX file "
            f"'{other_hkx_path}': {ex}"
        )
        return None
    return other_res_hkx


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
    importer: tp.Optional[HKXMapCollisionImporter] = None
    binder_file_path: Path = Path()
    enum_options: list[tuple[tp.Any, str, str]] = []
    load_other_resolution: bool = False
    use_material: bool = True
    hkx_entries: tp.Sequence[BinderEntry] = []

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

        hkx = entry.to_binary_file(MapCollisionHKX)
        import_info = HKXImportInfo(self.binder_file_path, entry.name, hkx)
        hkx_model_name = entry.name.split(".")[0]

        if self.load_other_resolution:
            other_res_hkx = load_other_res_hkx(
                operator=self,
                file_path=self.binder_file_path,
                import_info=import_info,
                is_binder=True,
            )
        else:
            other_res_hkx = None

        self.importer.operator = self
        self.importer.context = context

        try:
            hkx_parent = self.importer.import_hkx(hkx, bl_name=hkx_model_name)
        except Exception as ex:
            for obj in self.importer.all_bl_objs:
                bpy.data.objects.remove(obj)
            traceback.print_exc()
            return self.error(f"Cannot import HKX {hkx_model_name} from '{self.binder_file_path.name}'. Error: {ex}")

        if other_res_hkx is not None:
            # Import other-resolution HKX.
            other_res_hkx_model_name = other_res_hkx.path.name.split(".")[0]
            try:
                self.importer.import_hkx(other_res_hkx, bl_name=other_res_hkx_model_name, existing_parent=hkx_parent)
            except Exception as ex:
                for obj in self.importer.all_bl_objs:
                    bpy.data.objects.remove(obj)
                traceback.print_exc()
                return self.error(
                    f"Cannot import other-resolution HKX {other_res_hkx_model_name} from "
                    f"'{self.binder_file_path.name}'. Error: {ex}"
                )

        return {"FINISHED"}

    @classmethod
    def run(
        cls,
        importer: HKXMapCollisionImporter,
        binder_file_path: Path,
        load_other_resolution: bool,
        use_material: bool,
        hkx_entries: list[BinderEntry],
    ):
        cls.importer = importer
        cls.binder_file_path = binder_file_path
        cls.enum_options = [(str(i), entry.name, "") for i, entry in enumerate(hkx_entries)]
        cls.load_other_resolution = load_other_resolution
        cls.use_material = use_material
        cls.hkx_entries = hkx_entries
        # noinspection PyUnresolvedReferences
        bpy.ops.wm.hkx_map_collision_binder_choice_operator("INVOKE_DEFAULT")


class ImportHKXMapCollisionFromHKXBHD(LoggingOperator):
    bl_idname = "import_scene.hkx_map_collision_entry"
    bl_label = "Import Map Collision"
    bl_description = "Import selected HKX map collision entry from selected game map HKXBHD"

    # TODO: No way to change these properties.

    load_other_resolution: bpy.props.BoolProperty(
        name="Load Other Resolution",
        description="Try to load the other resolution (Hi/Lo) of the selected HKX (possibly in another Binder) and "
                    "parent them under the same empty object with optional MSB transform",
        default=True,
    )

    use_material: bpy.props.BoolProperty(
        name="Use Material",
        description="If enabled, 'HKX Hi' or 'HKX Lo' material will be assigned or created for all collision meshes",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        game_lists = context.scene.soulstruct_game_enums  # type: SoulstructGameEnums
        return game_lists.hkx_map_collision not in {"", "0"}

    def execute(self, context):

        start_time = time.perf_counter()

        settings = SoulstructSettings.get_scene_settings(context)
        game_lists = context.scene.soulstruct_game_enums  # type: SoulstructGameEnums
        map_path = SoulstructSettings.get_selected_map_path(context)
        if not map_path:
            return self.error("Game directory and map stem must be set in Blender's Soulstruct global settings.")
        settings.save_settings()

        transform = None  # type: Transform | None

        hkx_entry_name = game_lists.hkx_map_collision
        bl_name = hkx_entry_name.split(".")[0]

        # BXF file never has DCX.
        hkxbhd_path = map_path / f"h{settings.map_stem[1:]}.hkxbhd"
        hkxbdt_path = map_path / f"h{settings.map_stem[1:]}.hkxbdt"
        if settings.use_bak_file:
            hkxbhd_path = hkxbhd_path.with_name(hkxbhd_path.name + ".bak")
            if not hkxbhd_path.is_file():
                return self.error(f"Could not find HKXBHD '.bak' file for map '{settings.map_stem}'.")
            hkxbdt_path = hkxbdt_path.with_name(hkxbdt_path.name + ".bak")
            if not hkxbdt_path.is_file():
                return self.error(f"Could not find HKXBDT '.bak' file for map '{settings.map_stem}'.")
        if not hkxbhd_path.is_file():
            return self.error(f"Could not find HKXBHD header file for map '{settings.map_stem}': {hkxbhd_path}")
        if not hkxbdt_path.is_file():
            return self.error(f"Could not find HKXBDT data file for map '{settings.map_stem}': {hkxbdt_path}")

        hkxbxf = Binder.from_path(hkxbhd_path)
        try:
            hkx_entry = hkxbxf.find_entry_name(hkx_entry_name)
        except EntryNotFoundError:
            return self.error(
                f"Could not find HKX map collision entry '{hkx_entry_name}' in HKXBHD file '{hkxbhd_path.name}'."
            )

        import_info = HKXImportInfo(hkxbhd_path, hkx_entry.name, hkx_entry.to_binary_file(MapCollisionHKX))

        # If `load_other_resolutions = True`, this maps actual opened file paths to their other-res HKX files.
        # NOTE: Does NOT handle paths that need an entry to be chosen by the user (with queued Binder entries).
        # Those will be handled in the 'BinderChoice' operator.
        other_res_hkxs = {
            (import_info.path, import_info.hkx_name): load_other_res_hkx(
                operator=self,
                file_path=import_info.path,
                import_info=import_info,
                is_binder=True,
            )
        }  # type: dict[tuple[Path, str], MapCollisionHKX]

        importer = HKXMapCollisionImporter(self, context)

        hkx = import_info.hkx
        hkx_model_name = import_info.hkx_name.split(".")[0]
        other_res_hkx = other_res_hkxs.get((import_info.path, import_info.hkx_name), None)

        self.info(f"Importing HKX '{hkx_model_name}' as '{bl_name}'.")

        # Import single HKX.
        try:
            hkx_parent = importer.import_hkx(hkx, bl_name=bl_name, use_material=self.use_material)
        except Exception as ex:
            # Delete any objects created prior to exception.
            for obj in importer.all_bl_objs:
                bpy.data.objects.remove(obj)
            traceback.print_exc()  # for inspection in Blender console
            return self.error(f"Cannot import HKX: {import_info.path}. Error: {ex}")

        if other_res_hkx is not None:
            # Import other-res HKX.
            other_res_hkx_model_name = other_res_hkx.path.name.split(".")[0]
            try:
                hkx_parent = importer.import_hkx(
                    other_res_hkx,
                    bl_name=other_res_hkx_model_name,
                    use_material=self.use_material,
                    existing_parent=hkx_parent,
                )
            except Exception as ex:
                # Delete any objects created prior to exception.
                for obj in importer.all_bl_objs:
                    bpy.data.objects.remove(obj)
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import other-res HKX for {import_info.path}. Error: {ex}")

        if transform is not None:
            # Assign detected MSB transform to collision mesh parent.
            hkx_parent.location = transform.bl_translate
            hkx_parent.rotation_euler = transform.bl_rotate
            hkx_parent.scale = transform.bl_scale

        map_parent = find_or_create_bl_empty(f"{settings.map_stem} Collisions", context)
        hkx_parent.parent = map_parent

        # Set 'Model File Stem' if in MSB Import Mode. (This isn't used in MSB Export Mode, which gets its model from
        # the MSB part, but is a generally useful tracker of the HKX entry stem.)
        if transform is not None:
            hkx_parent["Model File Stem"] = hkx_model_name

        p = time.perf_counter() - start_time
        self.info(f"Finished importing HKX map collision {hkx_entry_name} from {hkxbhd_path.name} in {p} s.")

        return {"FINISHED"}


class ImportMSBMapCollision(LoggingOperator):
    bl_idname = "import_scene.msb_hkx_map_collision"
    bl_label = "Import MSB Collision Part"
    bl_description = "Import selected MSB Collision entry from selected game MSB"

    # TODO: No way to change these properties.

    load_other_resolution: bpy.props.BoolProperty(
        name="Load Other Resolution",
        description="Try to load the other resolution (Hi/Lo) of the selected HKX (possibly in another Binder) and "
                    "parent them under the same empty object with optional MSB transform",
        default=True,
    )

    use_material: bpy.props.BoolProperty(
        name="Use Material",
        description="If enabled, 'HKX Hi' or 'HKX Lo' material will be assigned or created for all collision meshes",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        game_enums = context.scene.soulstruct_game_enums  # type: SoulstructGameEnums
        return game_enums.hkx_map_collision_parts not in {"", "0"}

    def execute(self, context):

        start_time = time.perf_counter()

        settings = SoulstructSettings.get_scene_settings(context)
        game_lists = context.scene.soulstruct_game_enums  # type: SoulstructGameEnums
        map_path = SoulstructSettings.get_selected_map_path(context)
        if not map_path:
            return self.error("Game directory and map stem must be set in Blender's Soulstruct global settings.")
        settings.save_settings()

        try:
            part_name, hkx_stem = game_lists.hkx_map_collision_parts.split("|")
        except ValueError:
            return self.error("Invalid MSB collision selection.")
        msb_path = settings.get_selected_map_msb_path(context)

        # Get MSB part transform.
        msb = get_cached_file(msb_path, settings.get_game_msb_class(context))  # type: MSB
        collision_part = msb.collisions.find_entry_name(part_name)
        transform = Transform.from_msb_part(collision_part)

        dcx_type = settings.resolve_dcx_type("Auto", "MapCollisionHKX", False, context)
        hkx_entry_name = f"{hkx_stem}.hkx"
        hkx_entry_name = dcx_type.process_path(hkx_entry_name)

        bl_name = part_name

        # BXF file never has DCX.
        hkxbhd_path = map_path / f"h{settings.map_stem[1:]}.hkxbhd"
        hkxbdt_path = map_path / f"h{settings.map_stem[1:]}.hkxbdt"
        if settings.use_bak_file:
            hkxbhd_path = hkxbhd_path.with_name(hkxbhd_path.name + ".bak")
            if not hkxbhd_path.is_file():
                return self.error(f"Could not find HKXBHD '.bak' file for map '{settings.map_stem}'.")
            hkxbdt_path = hkxbdt_path.with_name(hkxbdt_path.name + ".bak")
            if not hkxbdt_path.is_file():
                return self.error(f"Could not find HKXBDT '.bak' file for map '{settings.map_stem}'.")
        if not hkxbhd_path.is_file():
            return self.error(f"Could not find HKXBHD header file for map '{settings.map_stem}': {hkxbhd_path}")
        if not hkxbdt_path.is_file():
            return self.error(f"Could not find HKXBDT data file for map '{settings.map_stem}': {hkxbdt_path}")

        hkxbxf = Binder.from_path(hkxbhd_path)
        try:
            hkx_entry = hkxbxf.find_entry_name(hkx_entry_name)
        except EntryNotFoundError:
            return self.error(
                f"Could not find HKX map collision entry '{hkx_entry_name}' in HKXBHD file '{hkxbhd_path.name}'."
            )

        import_info = HKXImportInfo(hkxbhd_path, hkx_entry.name, hkx_entry.to_binary_file(MapCollisionHKX))

        # If `load_other_resolutions = True`, this maps actual opened file paths to their other-res HKX files.
        # NOTE: Does NOT handle paths that need an entry to be chosen by the user (with queued Binder entries).
        # Those will be handled in the 'BinderChoice' operator.
        other_res_hkxs = {
            (import_info.path, import_info.hkx_name): load_other_res_hkx(
                operator=self,
                file_path=import_info.path,
                import_info=import_info,
                is_binder=True,
            )
        }  # type: dict[tuple[Path, str], MapCollisionHKX]

        importer = HKXMapCollisionImporter(self, context)

        hkx = import_info.hkx
        hkx_model_name = import_info.hkx_name.split(".")[0]
        other_res_hkx = other_res_hkxs.get((import_info.path, import_info.hkx_name), None)

        self.info(f"Importing HKX '{hkx_model_name}' as '{bl_name}'.")

        # Import single HKX.
        try:
            hkx_parent = importer.import_hkx(hkx, bl_name=bl_name, use_material=self.use_material)
        except Exception as ex:
            # Delete any objects created prior to exception.
            for obj in importer.all_bl_objs:
                bpy.data.objects.remove(obj)
            traceback.print_exc()  # for inspection in Blender console
            return self.error(f"Cannot import HKX: {import_info.path}. Error: {ex}")

        if other_res_hkx is not None:
            # Import other-res HKX.
            other_res_hkx_model_name = other_res_hkx.path.name.split(".")[0]
            try:
                hkx_parent = importer.import_hkx(
                    other_res_hkx,
                    bl_name=other_res_hkx_model_name,
                    use_material=self.use_material,
                    existing_parent=hkx_parent,
                )
            except Exception as ex:
                # Delete any objects created prior to exception.
                for obj in importer.all_bl_objs:
                    bpy.data.objects.remove(obj)
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import other-res HKX for {import_info.path}. Error: {ex}")

        # Assign detected MSB transform to collision mesh parent.
        hkx_parent.location = transform.bl_translate
        hkx_parent.rotation_euler = transform.bl_rotate
        hkx_parent.scale = transform.bl_scale

        map_parent = find_or_create_bl_empty(f"{settings.map_stem} Collisions", context)
        hkx_parent.parent = map_parent

        # Set 'Model File Stem' if in MSB Import Mode. (This isn't used in MSB Export Mode, which gets its model from
        # the MSB part, but is a generally useful tracker of the HKX entry stem.)
        if transform is not None:
            hkx_parent["Model File Stem"] = hkx_model_name

        p = time.perf_counter() - start_time
        self.info(f"Finished importing HKX map collision {hkx_entry_name} from {hkxbhd_path.name} in {p} s.")

        return {"FINISHED"}


class HKXMapCollisionImporter:
    """Manages imports for a batch of HKX files imported simultaneously."""

    hkx: tp.Optional[MapCollisionHKX]
    bl_name: str

    def __init__(
        self,
        operator: LoggingOperator,
        context,
    ):
        self.operator = operator
        self.context = context

        self.hkx = None
        self.bl_name = ""
        self.all_bl_objs = []

    def import_hkx(self, hkx: MapCollisionHKX, bl_name: str, use_material=True, existing_parent=None):
        """Read a HKX into a collection of Blender mesh objects.

        TODO: Create only one mesh and use material slots? Unsure.
        """
        self.hkx = hkx
        self.bl_name = bl_name  # should not have extensions (e.g. `h0100B0A10`)

        # Set mode to OBJECT and deselect all objects.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action="DESELECT")
        if bpy.ops.object.mode_set.poll():  # just to be safe
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        if existing_parent:
            hkx_parent = existing_parent
        else:
            # Empty parent.
            hkx_parent = bpy.data.objects.new(bl_name, None)
            self.context.scene.collection.objects.link(hkx_parent)
            self.all_bl_objs = [hkx_parent]

        meshes = self.hkx.to_meshes()
        material_indices = self.hkx.map_collision_physics_data.get_subpart_materials()
        if bl_name.startswith("h"):
            is_hi_res = True
        elif bl_name.startswith("l"):
            is_hi_res = False
        else:
            is_hi_res = True
            self.operator.warning(f"Cannot determine if HKX is hi-res or lo-res: {bl_name}. Defaulting to hi-res.")

        # NOTE: We include the collision's full name in each submesh so that Blender does not add '.001' suffixes to
        # distinguish them across collisions (which could be a problem even if we just leave off the map indicator).
        # However, on export, only the first (lower-cased) letter of each submesh is used to check its resolution.
        submesh_name_prefix = f"{bl_name} Submesh"
        for i, (vertices, faces) in enumerate(meshes):

            # Swap vertex Y and Z coordinates.
            vertices = np.c_[vertices[:, 0], vertices[:, 2], vertices[:, 1]]
            mesh_name = f"{submesh_name_prefix} {i}"
            bl_mesh = self.create_mesh_obj(vertices, faces, material_indices[i], mesh_name)
            if use_material:
                material_name = "HKX Hi" if is_hi_res else "HKX Lo"
                material_name += " (Mat 1)" if material_indices[i] == 1 else " (Not Mat 1)"
                try:
                    bl_material = bpy.data.materials[material_name]
                except KeyError:
                    # Create basic material: orange (lo) or blue (hi/other), lighter for material 1 (most common).
                    # Hue rotates between 10 values. Material index 1 (very common) is mapped to nice blue hue 0.6.
                    hue = 0.1 * ((material_indices[i] + 5) % 10)
                    saturation = 0.8 if is_hi_res else 0.4
                    value = 0.5
                    color = hsv_color(hue, saturation, value)
                    # NOTE: Not using wireframe in collision materials (unlike navmesh) as there is no per-face data.
                    bl_material = create_basic_material(material_name, color, wireframe_pixel_width=0.0)
                bl_mesh.data.materials.append(bl_material)

        return hkx_parent

    def create_mesh_obj(
        self,
        vertices: np.ndarray,
        faces: np.ndarray,
        material_index: int,
        mesh_name: str,
    ) -> bpy.types.MeshObject:
        """Create a Blender mesh object. The only custom property for HKX is material index."""
        bl_mesh = bpy.data.meshes.new(name=mesh_name)

        edges = []  # no edges in HKX
        bl_mesh.from_pydata(vertices, edges, faces)

        bl_mesh_obj = self.create_obj(mesh_name, bl_mesh)
        bl_mesh_obj["Material Index"] = material_index

        # noinspection PyTypeChecker
        return bl_mesh_obj

    def create_obj(self, name: str, data=None):
        """Create a new Blender object and parent it to main Empty."""
        obj = bpy.data.objects.new(name, data)
        self.context.scene.collection.objects.link(obj)
        self.all_bl_objs.append(obj)
        obj.parent = self.all_bl_objs[0]
        return obj
