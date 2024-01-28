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
    "NVMImportSettings",
    "ImportNVM",
    "ImportNVMWithBinderChoice",
    "ImportNVMFromNVMBND",
    "ImportNVMMSBPart",
    "ImportAllNVMMSBParts",
]

import fnmatch
import re
import time
import traceback
import typing as tp
from pathlib import Path

import bpy
import bmesh
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector

from soulstruct.containers import Binder, BinderEntry, EntryNotFoundError
from soulstruct.darksouls1r.maps.navmesh.nvm import NVM, NVMBox, NVMEventEntity

from io_soulstruct.utilities import *
from io_soulstruct.general import *
from io_soulstruct.general.cached import get_cached_file
from .utilities import *

if tp.TYPE_CHECKING:
    from io_soulstruct.type_checking import MSB_TYPING


class NVMImportInfo(tp.NamedTuple):
    """Holds information about a navmesh to import into Blender."""
    path: Path  # source file for NVM (likely a Binder path)
    model_file_stem: str  # generally stem of NVM file or Binder entry
    bl_name: str  # name to assign to Blender object (usually same as `model_file_stem`)
    nvm: NVM  # parsed NVM


class NVMImportChoiceInfo(tp.NamedTuple):
    """Holds information about a Binder entry choice that the user will make in deferred operator."""
    path: Path  # Binder path
    entries: list[BinderEntry]  # entries from which user must choose



class NVMImportSettings(bpy.types.PropertyGroup):
    """Common NVM import settings."""

    msb_part_name_match: bpy.props.StringProperty(
        name="MSB Part Name Match",
        description="Glob/Regex for filtering MSB part names when importing all parts",
        default="*",
    )

    msb_part_name_match_mode: bpy.props.EnumProperty(
        name="MSB Part Name Match Mode",
        description="Whether to use glob or regex for MSB part name matching",
        items=[
            ("GLOB", "Glob", "Use glob for MSB part name matching"),
            ("REGEX", "Regex", "Use regex for MSB part name matching"),
        ],
        default="GLOB",
    )

    include_pattern_in_parent_name: bpy.props.BoolProperty(
        name="Include Pattern in Parent Name",
        description="Include the glob/regex pattern in the name of the parent object for imported MSB parts",
        default=True,
    )


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
        settings.save_settings()
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

        importer = NVMImporter(self, context)

        self.info(f"Importing NVM model {import_info.model_file_stem} as '{import_info.bl_name}'.")

        try:
            bl_nvm = importer.import_nvm(
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

        bl_nvm.parent_obj = find_or_create_bl_empty(f"{map_stem} Navmeshes", context)

        p = time.perf_counter() - start_time
        self.info(f"Finished importing NVM {nvm_entry_name} from {nvmbnd_path.name} in {p} s.")

        return {"FINISHED"}


class ImportNVMMSBPart(LoggingOperator):
    """Import a NVM from the current selected value of listed game MSB navmesh entries."""
    bl_idname = "import_scene.msb_nvm"
    bl_label = "Import Navmesh Part"
    bl_description = "Import transform and model of selected Navmesh MSB part from selected game map"

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
        return game_lists.nvm_parts not in {"", "0"}

    def execute(self, context):

        start_time = time.perf_counter()

        settings = self.settings(context)
        settings.save_settings()
        if settings.game_variable_name != "DARK_SOULS_DSR":
            return self.error("MSB Navmesh import from game is only available for Dark Souls Remastered.")

        map_stem = settings.get_latest_map_stem_version()  # NVMBNDs come from latest map version
        nvmbnd_path = settings.get_import_map_path(f"{map_stem}.nvmbnd")
        if not nvmbnd_path or not nvmbnd_path.is_file():
            return self.error(f"Could not find NVMBND file for map '{map_stem}': {nvmbnd_path}")

        try:
            part_name, nvm_stem = context.scene.soulstruct_game_enums.nvm_parts.split("|")
        except ValueError:
            return self.error("Invalid MSB navmesh selection.")
        msb_path = settings.get_import_msb_path()  # will use newest MSB version
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING

        # Get MSB part transform.
        navmesh_part = msb.navmeshes.find_entry_name(part_name)
        transform = Transform.from_msb_part(navmesh_part)

        nvm_entry_name = f"{nvm_stem}.nvm"  # no DCX in DSR
        bl_name = part_name

        nvmbnd = Binder.from_path(nvmbnd_path)
        try:
            nvm_entry = nvmbnd.find_entry_name(nvm_entry_name)
        except EntryNotFoundError:
            return self.error(f"Could not find NVM entry '{nvm_entry_name}' in NVMBND file '{nvmbnd_path.name}'.")

        import_info = NVMImportInfo(
            nvmbnd_path, nvm_entry.minimal_stem, bl_name, nvm_entry.to_binary_file(NVM)
        )

        importer = NVMImporter(self, context,)

        self.info(f"Importing NVM model {import_info.model_file_stem} as '{import_info.bl_name}'.")

        try:
            bl_nvm = importer.import_nvm(
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

        # Assign detected MSB transform to navmesh.
        bl_nvm.location = transform.bl_translate
        bl_nvm.rotation_euler = transform.bl_rotate
        bl_nvm.scale = transform.bl_scale
        # Assign Model File Stem to navmesh.
        bl_nvm["Model File Stem"] = import_info.model_file_stem
        # Create/find map parent.
        bl_nvm.parent = find_or_create_bl_empty(f"{map_stem} Navmeshes", context)

        p = time.perf_counter() - start_time
        self.info(f"Finished importing NVM {nvm_entry_name} from {nvmbnd_path.name} in {p} s.")

        return {"FINISHED"}


class ImportAllNVMMSBParts(LoggingOperator):
    """Import a NVM from the current selected value of listed game MSB navmesh entries."""
    bl_idname = "import_scene.all_msb_nvm"
    bl_label = "Import All Navmesh Parts"
    bl_description = "Import NVM mesh and MSB transform of every MSB Navmesh part"

    # TODO: Currently no way to change these property defaults in GUI.

    # TODO: Linking model data is not permitted for NVMs. No two MSB parts should use the same NVM!

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
        settings = cls.settings(context)
        if settings.game_variable_name != "DARK_SOULS_DSR":
            return False
        msb_path = settings.get_import_msb_path()
        if not is_path_and_file(msb_path):
            return False
        return True  # MSB exists

    def execute(self, context):

        start_time = time.perf_counter()

        settings = self.settings(context)
        settings.save_settings()
        if settings.game_variable_name != "DARK_SOULS_DSR":
            return self.error("MSB Navmesh import from game is only available for Dark Souls Remastered.")

        nvm_import_settings = context.scene.nvm_import_settings  # type: NVMImportSettings

        part_name_match = nvm_import_settings.msb_part_name_match
        match nvm_import_settings.msb_part_name_match_mode:
            case "GLOB":
                def is_name_match(name: str):
                    return part_name_match in {"", "*"} or fnmatch.fnmatch(name, part_name_match)
            case "REGEX":
                pattern = re.compile(part_name_match)

                def is_name_match(name: str):
                    return part_name_match == "" or re.match(pattern, name)
            case _:  # should never happen
                return self.error(
                    f"Invalid MSB part name match mode: {nvm_import_settings.msb_part_name_match_mode}"
                )

        map_stem = settings.get_latest_map_stem_version()  # NVMBNDs come from latest map version
        nvmbnd_path = settings.get_import_map_path(f"{map_stem}.nvmbnd")
        if not nvmbnd_path or not nvmbnd_path.is_file():
            return self.error(f"Could not find NVMBND file for map '{map_stem}': {nvmbnd_path}")

        msb_path = settings.get_import_msb_path()  # will use newest MSB version
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING
        nvmbnd = Binder.from_path(nvmbnd_path)

        loaded_models = {}
        part_count = 0
        navmesh_parent = None  # found/created by first part

        importer = NVMImporter(self, context)

        for navmesh_part in msb.navmeshes:

            if not is_name_match(navmesh_part.name):
                # MSB navmesh name (part, not model) does not match glob/regex.
                continue

            if navmesh_part.model.name in loaded_models:
                first_part = loaded_models[navmesh_part.model.name]
                self.warning(
                    f"MSB navmesh part '{navmesh_part.name}' uses model '{navmesh_part.model.name}', which has "
                    f"already been loaded from MSB part '{first_part}'. No two MSB Navmesh parts should use the same "
                    f"NVM asset; try duplicating the NVM and and change the MSB model name first."
                )
                continue


            transform = Transform.from_msb_part(navmesh_part)
            nvm_stem = navmesh_part.model.get_model_file_stem(map_stem)

            nvm_entry_name = f"{nvm_stem}.nvm"  # no DCX in DSR

            try:
                nvm_entry = nvmbnd.find_entry_name(nvm_entry_name)
            except EntryNotFoundError:
                return self.error(f"Could not find NVM entry '{nvm_entry_name}' in NVMBND file '{nvmbnd_path.name}'.")

            import_info = NVMImportInfo(
                nvmbnd_path, nvm_entry.minimal_stem, navmesh_part.name, nvm_entry.to_binary_file(NVM)
            )

            self.info(f"Importing NVM model {import_info.model_file_stem} as '{import_info.bl_name}'.")

            try:
                nvm_obj = importer.import_nvm(
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

            # Assign detected MSB transform to navmesh.
            nvm_obj.location = transform.bl_translate
            nvm_obj.rotation_euler = transform.bl_rotate
            nvm_obj.scale = transform.bl_scale

            if not navmesh_parent:
                # Find or create parent for all imported parts.
                if nvm_import_settings.include_pattern_in_parent_name:
                    parent_name = f"{map_stem} Navmeshes ({part_name_match})"
                else:
                    parent_name = f"{map_stem} Navmeshes"
                navmesh_parent = find_or_create_bl_empty(parent_name, context)
            nvm_obj.parent = navmesh_parent

            # Assign Model File Stem to navmesh.
            nvm_obj["Model File Stem"] = import_info.model_file_stem

            # Record model usage.
            loaded_models[navmesh_part.model.name] = navmesh_part.name

            part_count += 1

        if part_count == 0:
            self.warning(f"No MSB Navmesh parts found (filter: '{part_name_match}').")
            return {"CANCELLED"}

        self.info(
            f"Imported {len(loaded_models)} NVM models and {part_count} / {len(msb.navmeshes)} MSB Navmesh parts in "
            f"{time.perf_counter() - start_time:.3f} seconds (filter: '{part_name_match}')."
        )

        return {"FINISHED"}


class NVMImporter:
    """Manages imports for a batch of NVM files imported simultaneously."""

    nvm: NVM | None
    bl_name: str

    imported_models: dict[str, bpy.types.Object]  # model file stem -> Blender object

    def __init__(
        self,
        operator: LoggingOperator,
        context,
    ):
        self.operator = operator
        self.context = context

        self.all_bl_objs = []
        self.imported_models = {}

    def import_nvm(
        self, import_info: NVMImportInfo, use_material=True, create_quadtree_boxes=False
    ) -> bpy.types.MeshObject:
        """Read a NVM into a collection of Blender mesh objects."""

        # Set mode to OBJECT and deselect all objects.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action="DESELECT")
        if bpy.ops.object.mode_set.poll():  # just to be safe
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        # Create mesh.
        nvm = import_info.nvm
        bl_mesh = bpy.data.meshes.new(name=import_info.bl_name)
        vertices = [GAME_TO_BL_VECTOR(v) for v in nvm.vertices]
        edges = []  # no edges in NVM
        faces = [triangle.vertex_indices for triangle in nvm.triangles]
        bl_mesh.from_pydata(vertices, edges, faces)
        # noinspection PyTypeChecker
        mesh_obj = bpy.data.objects.new(import_info.bl_name, bl_mesh)  # type: bpy.types.MeshObject
        self.context.scene.collection.objects.link(mesh_obj)
        self.all_bl_objs = [mesh_obj]

        if use_material:
            for bl_face, nvm_triangle in zip(bl_mesh.polygons, nvm.triangles):
                set_face_material(bl_mesh, bl_face, nvm_triangle.flags)

        # Create `BMesh` (as we need to assign face flag data to a custom `int` layer).
        bm = bmesh.new()
        bm.from_mesh(bl_mesh)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        flags_layer = bm.faces.layers.int.new("nvm_face_flags")
        obstacle_count_layer = bm.faces.layers.int.new("nvm_face_obstacle_count")

        for f_i, face in enumerate(bm.faces):
            nvm_triangle = nvm.triangles[f_i]
            face[flags_layer] = nvm_triangle.flags
            face[obstacle_count_layer] = nvm_triangle.obstacle_count

        for event in nvm.event_entities:
            bl_event = self.create_event_entity(event, bm.faces, import_info.bl_name)
            self.context.scene.collection.objects.link(bl_event)
            self.all_bl_objs.append(bl_event)
            bl_event.parent = mesh_obj

        bm.to_mesh(bl_mesh)
        del bm

        if create_quadtree_boxes:
            self.create_nvm_quadtree(mesh_obj, nvm, import_info.bl_name)

        self.imported_models[import_info.model_file_stem] = mesh_obj

        return mesh_obj

    def create_nvm_quadtree(self, bl_mesh, nvm: NVM, bl_name: str) -> list[bpy.types.Object]:
        """Create box tree (depth first creation order).

        NOTE: These boxes should be imported for inspection only. They are automatically generated from the mesh
        min/max vertex coordinates on NVM export.
        """
        boxes = []
        for box, indices in nvm.get_all_boxes(nvm.root_box):
            if not indices:
                box_name = f"{bl_name} Box ROOT"
            else:
                indices_string = "-".join(str(i) for i in indices)
                box_name = f"{bl_name} Box {indices_string}"
            bl_box = self.create_box(box)
            bl_box.name = box_name
            boxes.append(bl_box)
            self.all_bl_objs.append(bl_box)
            bl_box.parent = bl_mesh
        return boxes

    @staticmethod
    def create_box(box: NVMBox):
        """Create an AABB prism representing `box`. Position is baked into mesh data fully, just like the navmesh."""
        start_vec = GAME_TO_BL_VECTOR(box.start_corner)
        end_vec = GAME_TO_BL_VECTOR(box.end_corner)
        bpy.ops.mesh.primitive_cube_add()
        bl_box = bpy.context.active_object
        # noinspection PyTypeChecker
        box_data = bl_box.data  # type: bpy.types.Mesh
        for vertex in box_data.vertices:
            vertex.co[0] = start_vec.x if vertex.co[0] == -1.0 else end_vec.x
            vertex.co[1] = start_vec.y if vertex.co[1] == -1.0 else end_vec.y
            vertex.co[2] = start_vec.z if vertex.co[2] == -1.0 else end_vec.z
        bpy.ops.object.modifier_add(type="WIREFRAME")
        bl_box.modifiers[0].thickness = 0.02
        return bl_box

    @staticmethod
    def create_event_entity(
        nvm_event_entity: NVMEventEntity, bm_faces: bmesh.types.BMFaceSeq | list[bmesh.types.BMFace], bl_nvm_name: str
    ):
        """Create an Empty child that just holds the ID and triangle indices of a NVM event entity.

        Object is placed at the centroid of the faces it references, but this is just for convenience, and does not
        affect export. The user should move the event around if they change the attached faces.
        """
        bl_event = bpy.data.objects.new(f"{bl_nvm_name} Event {nvm_event_entity.entity_id}", None)
        bl_event.empty_display_type = "CUBE"  # to distinguish it from node spheres

        # Get the average position of the faces.
        avg_pos = Vector((0, 0, 0))
        for i in nvm_event_entity.triangle_indices:
            avg_pos += bm_faces[i].calc_center_median()
        avg_pos /= len(nvm_event_entity.triangle_indices)
        bl_event.location = avg_pos

        bl_event["entity_id"] = nvm_event_entity.entity_id
        bl_event["triangle_indices"] = nvm_event_entity.triangle_indices
        return bl_event
