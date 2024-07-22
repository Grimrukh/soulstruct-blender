"""
Import NVM files (with/without DCX) into Blender 3.3+ (Python 3.10+ scripting required).

NVM files are just basic meshes that contain:
    - per-triangle obstacle counts and flags for AI navigation
    - a quaternary box tree containing all triangles in leaf nodes
    - event entity references that allow specific triangle flags to be toggled from EMEVD

This file format is only used in DeS and DS1 (PTDE/DSR).
"""
from __future__ import annotations

__all__ = [
    "ImportNVM",
    "ImportNVMWithBinderChoice",
    "ImportNVMFromNVMBND",
]

import time
import traceback
import typing as tp
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper

from soulstruct.containers import Binder, BinderEntry, EntryNotFoundError
from soulstruct.darksouls1r.maps.navmesh.nvm import NVM

from io_soulstruct.utilities import *
from io_soulstruct.general import *
from io_soulstruct.navmesh.nvm.utilities import *
from .core import *


class NVMImportChoiceInfo(tp.NamedTuple):
    """Holds information about a Binder entry choice that the user will make in deferred operator."""
    path: Path  # Binder path
    entries: list[BinderEntry]  # entries from which user must choose


class ImportNVMMixin:

    # Type hints for `LoggingOperator`.
    error: tp.Callable[[str], set[str]]
    warning: tp.Callable[[str], set[str]]
    info: tp.Callable[[str], set[str]]

    navmesh_model_id: int
    import_all_from_binder: bool

    def load_from_binder(self, binder: Binder, file_path: Path) -> list[NVMImportInfo | NVMImportChoiceInfo]:
        """Load one or more `NVM` files from a `Binder` and queue them for import.

        Will queue up a list of Binder entries if `self.import_all_from_binder` is False and `navmesh_model_id`
        import setting is -1.

        Returns a list of `NVMImportInfo` or `NVMImportChoiceInfo` objects, depending on whether the Binder contains
        multiple entries that the user may need to choose from.
        """
        nvm_entries = binder.find_entries_matching_name(ANY_NVM_NAME_RE)
        if not nvm_entries:
            raise NVMImportError(f"Cannot find any '.nvm{{.dcx}}' files in binder {file_path}.")

        # Filter by `navmesh_model_id` if needed.
        if self.navmesh_model_id != -1:
            nvm_entries = [entry for entry in nvm_entries if self.check_nvm_entry_model_id(entry)]
        if not nvm_entries:
            raise NVMImportError(
                f"Found '.nvm{{.dcx}}' files, but none with model ID {self.navmesh_model_id} in binder {file_path}."
            )

        if len(nvm_entries) > 1:
            # Binder contains multiple (matching) entries.
            if self.import_all_from_binder:
                # Load all detected/matching KX entries in binder and queue them for import.
                new_import_infos = []  # type: list[NVMImportInfo]
                for entry in nvm_entries:
                    try:
                        nvm = entry.to_binary_file(NVM)
                    except Exception as ex:
                        self.warning(f"Error occurred while reading NVM Binder entry '{entry.name}': {ex}")
                    else:
                        nvm.path = Path(entry.name)  # also done in `GameFile`, but explicitly needed below
                        new_import_infos.append(NVMImportInfo(file_path, entry.minimal_stem, entry.minimal_stem, nvm))
                return new_import_infos

            # Queue up all matching Binder entries instead of loaded NVM instances; user will choose entry in pop-up.
            return [NVMImportChoiceInfo(file_path, nvm_entries)]

        # Binder only contains one (matching) NVM.
        try:
            nvm = nvm_entries[0].to_binary_file(NVM)
        except Exception as ex:
            self.warning(f"Error occurred while reading NVM Binder entry '{nvm_entries[0].name}': {ex}")
            return []

        return [NVMImportInfo(file_path, nvm_entries[0].minimal_stem, nvm_entries[0].minimal_stem, nvm)]

    def check_nvm_entry_model_id(self, nvm_entry: BinderEntry) -> bool:
        """Checks if the given NVM Binder entry matches the given navmesh model ID."""
        try:
            entry_model_id = int(nvm_entry.name[1:5])  # e.g. 'n1234' -> 1234
        except ValueError:
            return False  # not a match (weird NVM name)
        return entry_model_id == self.navmesh_model_id


class ImportNVM(LoggingOperator, ImportHelper, ImportNVMMixin):
    bl_idname = "import_scene.nvm"
    bl_label = "Import NVM"
    bl_description = "Import a NVM navmesh file. Can import from BNDs and supports DCX-compressed files"

    filename_ext = ".nvm"

    filter_glob: bpy.props.StringProperty(
        default="*.nvm;*.nvm.dcx;*.nvmbnd;*.nvmbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    navmesh_model_id: bpy.props.IntProperty(
        name="Navmesh Model ID",
        description="Model ID of the navmesh model to import (e.g. 200 for 'n0200'). Leave as -1 to have a choice "
                    "pop-up appear",
        default=-1,
    )

    import_all_from_binder: bpy.props.BoolProperty(
        name="Import All From NVMBND",
        description="If a NVMBND binder file is opened, import all NVM files rather than being prompted to select one",
        default=False,
    )

    use_material: bpy.props.BoolProperty(
        name="Use Material",
        description="If enabled, 'NVM' material will be assigned or created for all imported navmeshes",
        default=True,
    )

    create_quadtree_boxes: bpy.props.BoolProperty(
        name="Create Quadtree Boxes",
        description="If enabled, create quadtree boxes for all imported navmeshes",
        default=False,
    )

    files: bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    directory: bpy.props.StringProperty(
        options={'HIDDEN'},
    )

    def execute(self, context):
        print("Executing NVM import...")

        file_paths = [Path(self.directory, file.name) for file in self.files]
        import_infos = []  # type: list[NVMImportInfo | NVMImportChoiceInfo]

        for file_path in file_paths:

            is_binder = NVMBND_NAME_RE.match(file_path.name) is not None

            if is_binder:
                binder = Binder.from_path(file_path)
                new_import_infos = self.load_from_binder(binder, file_path)
                import_infos.extend(new_import_infos)
            else:
                # Loose NVM.
                try:
                    nvm = NVM.from_path(file_path)
                except Exception as ex:
                    self.warning(f"Error occurred while reading NVM file '{file_path.name}': {ex}")
                else:
                    model_file_stem = file_path.name.split(".")[0]
                    new_non_choice_import_infos = [NVMImportInfo(file_path, model_file_stem, model_file_stem, nvm)]
                    import_infos.extend(new_non_choice_import_infos)

        importer = NVMImporter(self, context)

        for import_info in import_infos:

            if isinstance(import_info, NVMImportChoiceInfo):
                # Defer through entry selection operator.
                ImportNVMWithBinderChoice.run(
                    importer=importer,
                    binder_file_path=import_info.path,
                    use_material=self.use_material,
                    create_quadtree_boxes=self.create_quadtree_boxes,
                    nvm_entries=import_info.entries,
                )
                continue

            self.info(f"Importing NVM model {import_info.model_file_stem} as '{import_info.bl_name}'.")

            # Import single NVM.
            try:
                importer.import_nvm(
                    import_info,
                    use_material=self.use_material,
                    create_quadtree_boxes=self.create_quadtree_boxes,
                )
            except Exception as ex:
                # Delete any objects created prior to exception.
                for obj in importer.all_bl_objs:
                    bpy.data.objects.remove(obj)
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import NVM: {import_info.path}. Error: {ex}")

        return {"FINISHED"}


# noinspection PyUnusedLocal
def get_binder_entry_choices(self, context):
    return ImportNVMWithBinderChoice.enum_options


class ImportNVMWithBinderChoice(LoggingOperator):
    """Presents user with a choice of enums from `enum_choices` class variable (set prior).

    See: https://blender.stackexchange.com/questions/6512/how-to-call-invoke-popup
    """
    bl_idname = "wm.nvm_binder_choice_operator"
    bl_label = "Choose NVM Binder Entry"

    # For deferred import in `execute()`.
    importer: tp.Optional[NVMImporter] = None
    binder: tp.Optional[Binder] = None
    binder_file_path: Path = Path()
    nvm_entries: tp.Sequence[BinderEntry] = []
    enum_options: list[tuple[tp.Any, str, str]] = []

    use_material: bool = True
    create_quadtree_boxes: bool = False

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
        entry = self.nvm_entries[choice]

        nvm = entry.to_binary_file(NVM)
        import_info = NVMImportInfo(self.binder_file_path, entry.minimal_stem, entry.minimal_stem, nvm)
        nvm_model_name = entry.name.split(".")[0]

        self.importer.operator = self
        self.importer.context = context

        try:
            self.importer.import_nvm(
                import_info,
                use_material=self.use_material,
                create_quadtree_boxes=self.create_quadtree_boxes,
            )
        except Exception as ex:
            for obj in self.importer.all_bl_objs:
                bpy.data.objects.remove(obj)
            traceback.print_exc()
            return self.error(f"Cannot import NVM {nvm_model_name} from '{self.binder_file_path.name}'. Error: {ex}")

        return {"FINISHED"}

    @classmethod
    def run(
        cls,
        importer: NVMImporter,
        binder_file_path: Path,
        use_material: bool,
        create_quadtree_boxes: bool,
        nvm_entries: list[BinderEntry],
    ):
        cls.importer = importer
        cls.binder_file_path = binder_file_path
        cls.enum_options = [(str(i), entry.name, "") for i, entry in enumerate(nvm_entries)]
        cls.use_material = use_material
        cls.create_quadtree_boxes = create_quadtree_boxes
        cls.nvm_entries = nvm_entries
        # noinspection PyUnresolvedReferences
        bpy.ops.wm.nvm_binder_choice_operator("INVOKE_DEFAULT")


class ImportNVMFromNVMBND(LoggingOperator):
    """Import a NVM from the current selected value of listed game map NVMs."""
    bl_idname = "import_scene.nvm_entry"
    bl_label = "Import NVM"
    bl_description = "Import selected NVM from game map directory's NVMBND binder"

    # TODO: Currently no way to change these property defaults in GUI.

    use_material: bpy.props.BoolProperty(
        name="Use Material",
        description="If enabled, 'NVM' material will be assigned or created for all imported navmeshes",
        default=True,
    )

    create_quadtree_boxes: bpy.props.BoolProperty(
        name="Create Quadtree Boxes",
        description="If enabled, create quadtree boxes for all imported navmeshes",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        if cls.settings(context).game_variable_name != "DARK_SOULS_DSR":
            return False
        game_lists = context.scene.soulstruct_game_enums  # type: SoulstructGameEnums
        return game_lists.nvm not in {"", "0"}

    def execute(self, context):

        start_time = time.perf_counter()

        settings = self.settings(context)
        if settings.game_variable_name != "DARK_SOULS_DSR":
            return self.error("NVM import from game NVMBND is only available for Dark Souls Remastered.")

        nvm_entry_name = context.scene.soulstruct_game_enums.nvm
        if nvm_entry_name in {"", "0"}:
            return self.error("No NVM entry selected.")

        # NVMBND files are sourced from the latest 'map' subfolder version.
        map_stem = settings.get_latest_map_stem_version()

        # Import source may depend on suffix of entry enum.
        if nvm_entry_name.endswith(" (G)"):
            nvm_entry_name = nvm_entry_name.removesuffix(" (G)")
            nvmbnd_path = settings.get_game_map_path(f"{map_stem}.nvmbnd")
        elif nvm_entry_name.endswith(" (P)"):
            nvm_entry_name = nvm_entry_name.removesuffix(" (P)")
            nvmbnd_path = settings.get_project_map_path(f"{map_stem}.nvmbnd")
        else:  # no suffix, so we use whichever source is preferred
            nvmbnd_path = settings.get_import_map_path(f"{map_stem}.nvmbnd")

        if not is_path_and_file(nvmbnd_path):  # validation
            return self.error(f"Could not find NVMBND file for map '{map_stem}': {nvmbnd_path}")

        bl_name = nvm_entry_name.split(".")[0]

        nvmbnd = Binder.from_path(nvmbnd_path)
        try:
            nvm_entry = nvmbnd.find_entry_name(nvm_entry_name)
        except EntryNotFoundError:
            return self.error(f"Could not find NVM entry '{nvm_entry_name}' in NVMBND file '{nvmbnd_path.name}'.")

        import_info = NVMImportInfo(
            nvmbnd_path, nvm_entry.minimal_stem, bl_name, nvm_entry.to_binary_file(NVM)
        )

        collection = get_collection(f"{map_stem} Navmesh Models", context.scene.collection)
        importer = NVMImporter(self, context, collection=collection)

        self.info(f"Importing NVM model {import_info.model_file_stem} as '{import_info.bl_name}'.")

        try:
            importer.import_nvm(
                import_info,
                use_material=self.use_material,
                create_quadtree_boxes=self.create_quadtree_boxes,
            )
        except Exception as ex:
            # Delete any objects created prior to exception.
            for obj in importer.all_bl_objs:
                bpy.data.objects.remove(obj)
            traceback.print_exc()  # for inspection in Blender console
            return self.error(f"Cannot import NVM: {import_info.path}. Error: {ex}")

        p = time.perf_counter() - start_time
        self.info(f"Imported NVM {nvm_entry_name} from {nvmbnd_path.name} in {p} s.")

        return {"FINISHED"}
