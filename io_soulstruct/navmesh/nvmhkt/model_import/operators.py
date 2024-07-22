"""
Import NVMHKT (Havok HKX) files (with/without DCX) into Blender 3.3+ (Python 3.10+ scripting required).

Currently only supported for Elden Ring.
"""
from __future__ import annotations

__all__ = [
    "ImportNVMHKT",
    "ImportNVMHKTWithBinderChoice",
    "ImportNVMHKTFromNVMHKTBND",
    "ImportAllNVMHKTsFromNVMHKTBND",
    "ImportAllOverworldNVMHKTs",
    "ImportAllDLCOverworldNVMHKTs",
]

import re
import time
import traceback
import typing as tp
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector

from soulstruct.containers import Binder, BinderEntry, EntryNotFoundError
from soulstruct_havok.wrappers.hkx2018.file_types import NavmeshHKX

from io_soulstruct.utilities import *
from io_soulstruct.general import *
from .core import *
from .settings import NVMHKTImportSettings
from ..utilities import get_dungeons_to_overworld_dict


ANY_NVMHKT_NAME_RE = re.compile(r"^(?P<stem>.*)\.hkx$")  # no DCX inside DCX-compressed NVMHKTBNDs
STANDARD_NVMHKT_STEM_RE = re.compile(r"^n(\d\d_\d\d_\d\d_\d\d)_(\d{6})$")  # no extensions
NVMHKTBND_NAME_RE = re.compile(r"^.*?\.nvmhktbnd(\.dcx)?$")


class NVMHKTImportChoiceInfo(tp.NamedTuple):
    """Holds information about a Binder entry choice that the user will make in deferred operator."""
    path: Path  # Binder path
    entries: list[BinderEntry]  # entries from which user must choose


class ImportNVMHKTMixin:

    # Type hints for `LoggingOperator`.
    error: tp.Callable[[str], set[str]]
    warning: tp.Callable[[str], set[str]]
    info: tp.Callable[[str], set[str]]

    navmesh_model_id: int
    import_all_from_binder: bool

    def load_from_binder(self, binder: Binder, file_path: Path) -> list[NVMHKTImportInfo | NVMHKTImportChoiceInfo]:
        """Load one or more `NVMHKT` files from a `Binder` and queue them for import.

        Will queue up a list of Binder entries if `self.import_all_from_binder` is False and `navmesh_model_id`
        import setting is -1.

        Returns a list of `NVMHKTImportInfo` or `NVMHKTImportChoiceInfo` objects, depending on whether the Binder contains
        multiple entries that the user may need to choose from.
        """
        nvm_entries = binder.find_entries_matching_name(ANY_NVMHKT_NAME_RE)
        if not nvm_entries:
            raise NVMHKTImportError(f"Cannot find any '.hkx{{.dcx}}' files in binder {file_path}.")

        # Filter by `navmesh_model_id` if needed.
        if self.navmesh_model_id != -1:
            nvm_entries = [entry for entry in nvm_entries if self.check_nvm_entry_model_id(entry)]
        if not nvm_entries:
            raise NVMHKTImportError(
                f"Found '.hkx{{.dcx}}' files, but none with model ID {self.navmesh_model_id} in binder {file_path}."
            )

        if len(nvm_entries) > 1:
            # Binder contains multiple (matching) entries.
            if self.import_all_from_binder:
                # Load all detected/matching KX entries in binder and queue them for import.
                new_import_infos = []  # type: list[NVMHKTImportInfo]
                for entry in nvm_entries:
                    try:
                        nvm = entry.to_binary_file(NavmeshHKX)
                    except Exception as ex:
                        self.warning(f"Error occurred while reading NVMHKT Binder entry '{entry.name}': {ex}")
                    else:
                        nvm.path = Path(entry.name)  # also done in `GameFile`, but explicitly needed below
                        new_import_infos.append(NVMHKTImportInfo(file_path, entry.minimal_stem, entry.minimal_stem, nvm))
                return new_import_infos

            # Queue up all matching Binder entries instead of loaded NVMHKT instances; user will choose entry in pop-up.
            return [NVMHKTImportChoiceInfo(file_path, nvm_entries)]

        # Binder only contains one (matching) NVMHKT.
        try:
            nvm = nvm_entries[0].to_binary_file(NavmeshHKX)
        except Exception as ex:
            self.warning(f"Error occurred while reading NVMHKT Binder entry '{nvm_entries[0].name}': {ex}")
            return []

        return [NVMHKTImportInfo(file_path, nvm_entries[0].minimal_stem, nvm_entries[0].minimal_stem, nvm)]

    def check_nvm_entry_model_id(self, nvm_entry: BinderEntry) -> bool:
        """Checks if the given NVMHKT Binder entry matches the given navmesh model ID."""
        try:
            entry_model_id = int(nvm_entry.name[1:5])  # e.g. 'n1234' -> 1234
        except ValueError:
            return False  # not a match (weird NVMHKT name)
        return entry_model_id == self.navmesh_model_id


class ImportNVMHKT(LoggingOperator, ImportHelper, ImportNVMHKTMixin):
    bl_idname = "import_scene.nvmhkt"
    bl_label = "Import NVMHKT"
    bl_description = "Import a HKX Havok navmesh file. Can import from NVMHKTBNDs and supports DCX-compressed files"

    filename_ext = ".hkx"

    filter_glob: bpy.props.StringProperty(
        default="*.hkx;*.hkx.dcx;*.nvmhktbnd;*.nvmhktbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    navmesh_model_id: bpy.props.IntProperty(
        name="Navmesh Model ID",
        description="Model ID of the navmesh model to import (e.g. 200 for '*_000200'). Leave as -1 to have a choice "
                    "pop-up appear",
        default=-1,
    )

    import_all_from_binder: bpy.props.BoolProperty(
        name="Import All From NVMHKTBND",
        description="If a NVMHKTBND binder file is opened, import all NVMHKT files rather than being prompted to "
                    "select one",
        default=False,
    )

    use_material: bpy.props.BoolProperty(
        name="Use Material",
        description="If enabled, 'NVMHKT' material will be assigned or created for all imported navmeshes",
        default=True,
    )

    files: bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    directory: bpy.props.StringProperty(
        options={'HIDDEN'},
    )

    def execute(self, context):
        self.info("Executing NVMHKT import...")

        file_paths = [Path(self.directory, file.name) for file in self.files]
        import_infos = []  # type: list[NVMHKTImportInfo | NVMHKTImportChoiceInfo]

        for file_path in file_paths:

            is_binder = NVMHKTBND_NAME_RE.match(file_path.name) is not None

            if is_binder:
                binder = Binder.from_path(file_path)
                new_import_infos = self.load_from_binder(binder, file_path)
                import_infos.extend(new_import_infos)
            else:
                # Loose NVMHKT.
                try:
                    nvm = NavmeshHKX.from_path(file_path)
                except Exception as ex:
                    self.warning(f"Error occurred while reading NVMHKT file '{file_path.name}': {ex}")
                else:
                    model_file_stem = file_path.name.split(".")[0]
                    new_non_choice_import_infos = [NVMHKTImportInfo(file_path, model_file_stem, model_file_stem, nvm)]
                    import_infos.extend(new_non_choice_import_infos)

        importer = NVMHKTImporter(self, context)

        for import_info in import_infos:

            if isinstance(import_info, NVMHKTImportChoiceInfo):
                # Defer through entry selection operator.
                ImportNVMHKTWithBinderChoice.run(
                    importer=importer,
                    binder_file_path=import_info.path,
                    use_material=self.use_material,
                    nvm_entries=import_info.entries,
                )
                continue

            self.info(f"Importing NVMHKT model {import_info.model_file_stem} as '{import_info.bl_name}'.")

            # Import single NVMHKT.
            try:
                importer.import_nvmhkt(import_info, use_material=self.use_material)
            except Exception as ex:
                # Delete any objects created prior to exception.
                for obj in importer.all_bl_objs:
                    bpy.data.objects.remove(obj)
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import NVMHKT: {import_info.path}. Error: {ex}")

        return {"FINISHED"}


# noinspection PyUnusedLocal
def get_binder_entry_choices(self, context):
    return ImportNVMHKTWithBinderChoice.enum_options


class ImportNVMHKTWithBinderChoice(LoggingOperator):
    """Presents user with a choice of enums from `enum_choices` class variable (set prior).

    See: https://blender.stackexchange.com/questions/6512/how-to-call-invoke-popup
    """
    bl_idname = "wm.nvmhkt_binder_choice_operator"
    bl_label = "Choose NVMHKT Binder Entry"

    # For deferred import in `execute()`.
    importer: tp.Optional[NVMHKTImporter] = None
    binder: tp.Optional[Binder] = None
    binder_file_path: Path = Path()
    nvmhkt_entries: tp.Sequence[BinderEntry] = []
    enum_options: list[tuple[tp.Any, str, str]] = []

    use_material: bool = True

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
        entry = self.nvmhkt_entries[choice]

        nvm = entry.to_binary_file(NavmeshHKX)
        import_info = NVMHKTImportInfo(self.binder_file_path, entry.minimal_stem, entry.minimal_stem, nvm)
        nvm_model_name = entry.name.split(".")[0]

        self.importer.operator = self
        self.importer.context = context

        try:
            self.importer.import_nvmhkt(import_info, use_material=self.use_material)
        except Exception as ex:
            for obj in self.importer.all_bl_objs:
                bpy.data.objects.remove(obj)
            traceback.print_exc()
            return self.error(f"Cannot import NVMHKT {nvm_model_name} from '{self.binder_file_path.name}'. Error: {ex}")

        return {"FINISHED"}

    @classmethod
    def run(
        cls,
        importer: NVMHKTImporter,
        binder_file_path: Path,
        use_material: bool,
        nvm_entries: list[BinderEntry],
    ):
        cls.importer = importer
        cls.binder_file_path = binder_file_path
        cls.enum_options = [(str(i), entry.name, "") for i, entry in enumerate(nvm_entries)]
        cls.use_material = use_material
        cls.nvmhkt_entries = nvm_entries
        # noinspection PyUnresolvedReferences
        bpy.ops.wm.nvmhkt_binder_choice_operator("INVOKE_DEFAULT")


class ImportNVMHKTFromNVMHKTBND(LoggingOperator):
    """Import a NVMHKT from the current selected value of listed game map NVMHKTs."""
    bl_idname = "import_scene.nvmhkt_entry"
    bl_label = "Import NVMHKT"
    bl_description = "Import selected NVMHKT from game map directory's NVMHKTBND binder"

    # TODO: Currently no way to change these property defaults in GUI.

    use_material: bpy.props.BoolProperty(
        name="Use Material",
        description="If enabled, 'NVMHKT' material will be assigned or created for all imported navmeshes",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        if not cls.settings(context).is_game("ELDEN_RING"):
            return False
        game_lists = context.scene.soulstruct_game_enums  # type: SoulstructGameEnums
        return game_lists.nvmhkt not in {"", "0"}

    def execute(self, context):

        start_time = time.perf_counter()

        settings = self.settings(context)
        if settings.game_variable_name != "ELDEN_RING":
            return self.error("NVMHKT import from game NVMHKTBND is only available for Elden Ring.")

        nvmhkt_entry_name = context.scene.soulstruct_game_enums.nvmhkt
        if nvmhkt_entry_name in {"", "0"}:
            return self.error("No NVMHKT entry selected.")

        # NVMHKTBND files are sourced from the latest 'map' subfolder version.
        map_stem = settings.get_latest_map_stem_version()

        # Import source may depend on suffix of entry enum.
        if nvmhkt_entry_name.endswith(" (G)"):
            nvmhkt_entry_name = nvmhkt_entry_name.removesuffix(" (G)")
            nvmbnd_path = settings.get_game_map_path(f"{map_stem}.nvmhktbnd")
        elif nvmhkt_entry_name.endswith(" (P)"):
            nvmhkt_entry_name = nvmhkt_entry_name.removesuffix(" (P)")
            nvmbnd_path = settings.get_project_map_path(f"{map_stem}.nvmhktbnd")
        else:  # no suffix, so we use whichever source is preferred
            nvmbnd_path = settings.get_import_map_path(f"{map_stem}.nvmhktbnd")

        if not is_path_and_file(nvmbnd_path):  # validation
            return self.error(f"Could not find NVMHKTBND file for map '{map_stem}': {nvmbnd_path}")

        bl_name = nvmhkt_entry_name.split(".")[0]

        nvmhktbnd = Binder.from_path(nvmbnd_path)
        try:
            nvm_entry = nvmhktbnd.find_entry_name(nvmhkt_entry_name)
        except EntryNotFoundError:
            return self.error(f"Could not find NVMHKT entry '{nvmhkt_entry_name}' in NVMHKTBND file '{nvmbnd_path.name}'.")

        import_info = NVMHKTImportInfo(
            nvmbnd_path, nvm_entry.minimal_stem, bl_name, nvm_entry.to_binary_file(NavmeshHKX)
        )

        collection = get_collection(f"{map_stem} Navmesh Models", context.scene.collection)
        importer = NVMHKTImporter(self, context, collection=collection)

        self.info(f"Importing NVMHKT model {import_info.model_file_stem} as '{import_info.bl_name}'.")

        try:
            importer.import_nvmhkt(import_info, use_material=self.use_material)
        except Exception as ex:
            # Delete any objects created prior to exception.
            for obj in importer.all_bl_objs:
                bpy.data.objects.remove(obj)
            traceback.print_exc()  # for inspection in Blender console
            return self.error(f"Cannot import NVMHKT: {import_info.path}. Error: {ex}")

        p = time.perf_counter() - start_time
        self.info(f"Imported NVMHKT {nvmhkt_entry_name} from {nvmbnd_path.name} in {p} s.")

        return {"FINISHED"}


class ImportAllNVMHKTBase(LoggingOperator):

    use_material: bool

    def import_nvmhktbnd_entry(
        self,
        context,
        collection: bpy.types.Collection,
        nvmhktbnd: Binder,
        entry_name: str,
    ) -> bpy.types.MeshObject:
        try:
            hkx_entry = nvmhktbnd.find_entry_name(entry_name)
        except EntryNotFoundError:
            self.warning(
                f"Could not find NVMHKT entry '{entry_name}' in NVMHKTBND file '{nvmhktbnd.path.name}'."
            )
            raise

        bl_name = entry_name.split(".")[0]

        import_info = NVMHKTImportInfo(
            nvmhktbnd.path, hkx_entry.minimal_stem, bl_name, hkx_entry.to_binary_file(NavmeshHKX)
        )

        importer = NVMHKTImporter(self, context, collection=collection)

        self.info(f"Importing NVMHKT model {import_info.model_file_stem} as '{import_info.bl_name}'.")

        try:
            return importer.import_nvmhkt(import_info, use_material=self.use_material)
        except Exception:
            # Delete any objects created prior to exception.
            for obj in importer.all_bl_objs:
                bpy.data.objects.remove(obj)
            traceback.print_exc()  # for inspection in Blender console
            raise


class ImportAllNVMHKTsFromNVMHKTBND(ImportAllNVMHKTBase):
    """Import all NVMHKTs of chosen resolution(s) from selected map."""
    bl_idname = "import_scene.all_nvmhkt"
    bl_label = "Import All Map NVMHKTs"
    bl_description = "Import all NVMHKTs of chosen resolution(s) from selected map"

    # TODO: Currently no way to change these property defaults in GUI.

    use_material: bpy.props.BoolProperty(
        name="Use Material",
        description="If enabled, 'NVMHKT' material will be assigned or created for all imported navmeshes",
        default=True,
    )

    # Small tile coordinates considered to be the origin of the world.
    grid_world_origin = (46, 49)  # center of Erdtree picture on world map
    small_tile_width = 256.0

    # TODO: Need dictionary built from 'WorldMapLegacy

    @classmethod
    def poll(cls, context):
        if not cls.settings(context).is_game("ELDEN_RING"):
            return False
        settings = cls.settings(context)
        if settings.map_stem in {"", "0"}:
            return False  # no map selected
        return True

    def execute(self, context):

        start_time = time.perf_counter()

        import_settings = bpy.context.scene.nvmhkt_import_settings  # type: NVMHKTImportSettings

        settings = self.settings(context)
        if settings.game_variable_name != "ELDEN_RING":
            return self.error("NVMHKT import from game NVMHKTBND is only available for Elden Ring.")

        map_stem = settings.map_stem
        nvmhktbnd_path = settings.get_import_map_path(f"{map_stem}.nvmhktbnd.dcx")
        if not nvmhktbnd_path:
            return self.error(f"Could not find NVMHKTBND file for map '{map_stem}'.")
        small_tile_match = re.match(r"(m60|m61)_(\d\d)_(\d\d)_(\d)0", map_stem)

        collection = get_collection(f"{map_stem} Navmesh Models", context.scene.collection)

        if small_tile_match:
            grid_x = int(small_tile_match.group(1))
            grid_y = int(small_tile_match.group(2))  # Z in game but Y in Blender
        else:
            grid_x = grid_y = -1  # unused

        nvmhktbnd = Binder.from_path(nvmhktbnd_path)
        importer = NVMHKTImporter(self, context, collection=collection)
        models = []

        def get_bl_name(entry_):
            bl_name_ = entry_.name.split(".")[0]
            if import_settings.correct_model_versions and map_stem[10] != "0":
                if bl_name_[10] == map_stem[10]:
                    self.info(f"Model version in NVMHKT name already matches V1+ map version: {bl_name_}")
                    return bl_name_
                # Correct model version to match map version.
                # Note that we only correct the stem part, not the '_XXYYVS' suffix, which keeps 00 even when the
                # navmesh is actually versioned.
                versioned_suffix = map_stem[10:12]
                bl_name_ = f"{bl_name_[:10]}{versioned_suffix}{bl_name_[12:]}"
                self.info(f"Correcting NVMHKT model name with map version: {bl_name_}")
            return bl_name_

        if import_settings.import_hires_navmeshes:

            for entry in nvmhktbnd.find_entries_matching_name(re.compile("n.*\.hkx")):
                bl_name = get_bl_name(entry)

                import_info = NVMHKTImportInfo(
                    nvmhktbnd.path, entry.minimal_stem, bl_name, entry.to_binary_file(NavmeshHKX)
                )

                self.info(f"Importing NVMHKT model {import_info.model_file_stem} as '{import_info.bl_name}'.")

                try:
                    bl_nvmhkt = importer.import_nvmhkt(import_info, use_material=self.use_material)
                except Exception:
                    # Delete any objects created prior to exception.
                    for obj in importer.all_bl_objs:
                        bpy.data.objects.remove(obj)
                    traceback.print_exc()  # for inspection in Blender console
                    raise

                if small_tile_match and len(bl_nvmhkt.data.vertices) == 0:
                    # Import 'q' quarter navmeshes instead.
                    for i in range(4):
                        hkx_entry_name = f"q{map_stem[1:]}_{grid_x:02}{grid_y:02}00_{i}.hkx"
                        try:
                            bl_nvmhkt_q = self.import_nvmhktbnd_entry(context, collection, nvmhktbnd, hkx_entry_name)
                        except EntryNotFoundError:
                            continue
                        except Exception as ex:
                            self.error(f"Cannot import NVMHKT '{hkx_entry_name}' from '{nvmhktbnd_path}'. Error: {ex}")
                            continue
                        models.append(bl_nvmhkt_q)
                    self.info(
                        f"Imported four 'q' quarter navmeshes instead of empty overworld 'n' navmesh '{entry.name}'."
                    )

                models.append(bl_nvmhkt)

        if import_settings.import_lores_navmeshes:
            for entry in nvmhktbnd.find_entries_matching_name(re.compile("o.*\.hkx")):
                bl_name = get_bl_name(entry)

                import_info = NVMHKTImportInfo(
                    nvmhktbnd.path, entry.minimal_stem, bl_name, entry.to_binary_file(NavmeshHKX)
                )

                self.info(f"Importing NVMHKT model {import_info.model_file_stem} as '{import_info.bl_name}'.")

                try:
                    bl_nvmhkt = importer.import_nvmhkt(import_info, use_material=self.use_material)
                except Exception:
                    # Delete any objects created prior to exception.
                    for obj in importer.all_bl_objs:
                        bpy.data.objects.remove(obj)
                    traceback.print_exc()  # for inspection in Blender console
                    raise

                models.append(bl_nvmhkt)

        location = None  # type: None | Vector
        connection_points = []

        if small_tile_match:
            if import_settings.overworld_transform_mode == "WORLD":
                origin_x, origin_y = self.grid_world_origin
                location = Vector((
                    (grid_x - origin_x) * self.small_tile_width,
                    (grid_y - origin_y) * self.small_tile_width,
                    0,  # correct world height is baked into overworld navmeshes
                ))
        elif map_stem.startswith(("m60", "m61")):
            self.warning("Found a non-small tile navmesh, which is unexpected. No transform applied.")
        elif import_settings.dungeon_transform_mode == "NONE":
            pass  # no transform
        else:
            # Apply dungeon-to-overworld transform and optionally add tile-to-world on top of it.
            # er_regulation_path = settings.get_import_file_path("regulation.bin")  # cached after first call
            # self.info("Getting dungeon to overworld coordinates from Elden Ring `GameParamBND` (regulation)...")
            dungeons_to_overworld = get_dungeons_to_overworld_dict()
            if map_stem not in dungeons_to_overworld:
                self.warning(f"Transform to move dungeon '{map_stem}' to overworld is not known. No transform applied.")
            else:
                overworld_connections = dungeons_to_overworld[map_stem]

                if import_settings.create_dungeon_connection_points:
                    for dungeon_to_overworld in overworld_connections:
                        if dungeon_to_overworld[1] is None:
                            continue  # source point not known for this connection
                        source_connection_point = bpy.data.objects.new(f"{map_stem} -- {dungeon_to_overworld[0]}", None)
                        source_connection_point.location = GAME_TO_BL_VECTOR(dungeon_to_overworld[1])
                        connection_points.append(source_connection_point)
                        collection.objects.link(source_connection_point)

                # Use first connection to move dungeon to tile.
                overworld_tile_map_stem, _, dungeon_to_overworld = overworld_connections[0]

                location = GAME_TO_BL_VECTOR(dungeon_to_overworld)
                if import_settings.dungeon_transform_mode == "TILE":
                    # Just apply the dungeon-to-tile transform, not tile-to-world.
                    # This will look correct if that tile is imported with no transform applied.
                    if len(overworld_connections) > 1:
                        self.warning(
                            f"Multiple connections from dungeon '{map_stem}' to overworld. Transforming to first tile "
                            f"only: {overworld_tile_map_stem}"
                        )
                    pass
                elif import_settings.dungeon_transform_mode == "WORLD":
                    # Apply both dungeon-to-tile transform and tile-to-world transform.
                    # TODO: Assuming that all overworld connections end up with the same world transform for dungeon!
                    origin_x, origin_y = self.grid_world_origin
                    tile_grid_x = int(overworld_tile_map_stem[4:6])
                    tile_grid_y = int(overworld_tile_map_stem[7:9])
                    location += Vector((
                        (tile_grid_x - origin_x) * self.small_tile_width,
                        (tile_grid_y - origin_y) * self.small_tile_width,
                        0,  # correct world height is baked into overworld navmeshes
                    ))
                else:
                    self.warning(
                        f"Unknown dungeon transform mode '{import_settings.dungeon_transform_mode}'. "
                        f"No transform applied."
                    )

        if location is not None:
            for bl_nvmhkt in models:
                bl_nvmhkt.location = location
            for point in connection_points:
                # Need to ADD transform to connection points, not set them, as local position isn't stored in any mesh.
                point.location += location

        p = time.perf_counter() - start_time
        self.info(f"Imported {len(models)} NVMHKT files from map {map_stem} in {p} s.")

        return {"FINISHED"}


class ImportAllOverworldNVMHKTsBase(ImportAllNVMHKTBase):
    """Import all NVMHKTs from ALL base game overworld small tile maps (m60_XX_ZZ_00).

    Note that large/medium overworld tiles do not have navmeshes in Elden Ring.
    """
    AREA: str

    # TODO: Currently no way to change these property defaults in GUI.

    use_material: bpy.props.BoolProperty(
        name="Use Material",
        description="If enabled, 'NVMHKT' material will be assigned or created for all imported navmeshes",
        default=True,
    )

    # Small tile coordinates considered to be the origin of the world.
    grid_world_origin = (46, 49)  # center of Erdtree picture on world map
    small_tile_width = 256.0

    @classmethod
    def poll(cls, context):
        if not cls.settings(context).is_game("ELDEN_RING"):
            return False
        return True

    def execute(self, context):

        start_time = time.perf_counter()

        import_settings = bpy.context.scene.nvmhkt_import_settings  # type: NVMHKTImportSettings

        settings = self.settings(context)
        if settings.game_variable_name != "ELDEN_RING":
            return self.error("NVMHKT import from game NVMHKTBND is only available for Elden Ring.")

        overworld_map_dir = settings.get_import_dir_path(f"map/{self.AREA}")

        map_count = 0
        model_count = 0

        collection = get_collection(f"{self.AREA} Navmesh Models", context.scene.collection)

        for nvmhktbnd_path in overworld_map_dir.rglob(f"{self.AREA}_??_??_00.nvmhktbnd.dcx"):

            map_stem = nvmhktbnd_path.stem.split(".")[0]

            grid_x = int(nvmhktbnd_path.name[4:6])
            grid_y = int(nvmhktbnd_path.name[7:9])  # Z in game, but Y in Blender

            nvmhktbnd = Binder.from_path(nvmhktbnd_path)

            models = []

            if import_settings.import_hires_navmeshes:

                # Should be only one 'n' entry.
                hkx_entry_name = f"n{map_stem[1:]}_{grid_x:02}{grid_y:02}00.hkx"

                try:
                    bl_nvmhkt_n = self.import_nvmhktbnd_entry(context, collection, nvmhktbnd, hkx_entry_name)
                except EntryNotFoundError:
                    continue
                except Exception as ex:
                    self.error(f"Cannot import NVMHKT '{hkx_entry_name}' from '{nvmhktbnd_path}'. Error: {ex}")
                    continue

                if len(bl_nvmhkt_n.data.vertices) == 0:
                    # 'n' navmesh is empty (happens for a few tiles). Load four 'q' navmeshes.

                    # Delete empty 'n' model first.
                    bpy.data.objects.remove(bl_nvmhkt_n)

                    for i in range(4):
                        hkx_entry_name = f"q{map_stem[1:]}_{grid_x:02}{grid_y:02}00_{i}.hkx"
                        try:
                            bl_nvmhkt_q = self.import_nvmhktbnd_entry(context, collection, nvmhktbnd, hkx_entry_name)
                        except EntryNotFoundError:
                            continue
                        except Exception as ex:
                            self.error(f"Cannot import NVMHKT '{hkx_entry_name}' from '{nvmhktbnd_path}'. Error: {ex}")
                            continue
                        models.append(bl_nvmhkt_q)

                    self.info(f"Imported four 'q' quarter navmeshes instead of empty 'n' navmesh '{hkx_entry_name}'.")

                else:
                    models.append(bl_nvmhkt_n)

            if import_settings.import_lores_navmeshes:

                # Should be only one 'o' entry.
                hkx_entry_name = f"o{map_stem[1:]}_{grid_x:02}{grid_y:02}00.hkx"

                try:
                    bl_nvmhkt_o = self.import_nvmhktbnd_entry(context, collection, nvmhktbnd, hkx_entry_name)
                except EntryNotFoundError:
                    continue
                except Exception as ex:
                    self.error(f"Cannot import NVMHKT '{hkx_entry_name}' from '{nvmhktbnd_path}'. Error: {ex}")
                    continue

                models.append(bl_nvmhkt_o)

            if import_settings.overworld_transform_mode == "WORLD":
                origin_x, origin_y = self.grid_world_origin
                for bl_nvmhkt in models:
                    bl_nvmhkt.location = (
                        (grid_x - origin_x) * self.small_tile_width,
                        (grid_y - origin_y) * self.small_tile_width,
                        0,  # correct world height is baked into overworld navmeshes
                    )

            map_count += 1
            model_count += len(models)

        p = time.perf_counter() - start_time
        self.info(f"Imported {model_count} NVMHKT files from {map_count} overworld small tile maps in {p} s.")

        return {"FINISHED"}


class ImportAllOverworldNVMHKTs(ImportAllOverworldNVMHKTsBase):
    """Import all NVMHKTs from ALL base game overworld small tile maps (m60_XX_ZZ_00).

    Note that large/medium overworld tiles do not have navmeshes in Elden Ring.
    """
    bl_idname = "import_scene.all_nvmhkt_overworld"
    bl_label = "Import All Overworld NVMHKTs"
    bl_description = "Import all NVMHKTs of chosen resolution(s) from all base overworld small tile maps (m60_XX_ZZ_00)"

    AREA = "m60"


class ImportAllDLCOverworldNVMHKTs(ImportAllOverworldNVMHKTsBase):
    """Import all NVMHKTs from ALL DLC overworld small tile maps (m61_XX_ZZ_00).

    Note that large/medium overworld tiles do not have navmeshes in Elden Ring.
    """
    bl_idname = "import_scene.all_nvmhkt_dlc_overworld"
    bl_label = "Import All DLC Overworld NVMHKTs"
    bl_description = "Import all NVMHKTs of chosen resolution(s) from all DLC overworld small tile maps (m61_XX_ZZ_00)"

    AREA = "m61"
