from __future__ import annotations

__all__ = [
    "SelectGameMapDirectory",
    "SelectProjectMapDirectory",
    "SelectImageCacheDirectory",
    "SelectCustomMTDBNDFile",
    "SelectCustomMATBINBNDFile",
    "LoadCollectionsFromBlend",
]

import abc
import typing as tp
from pathlib import Path

import bpy

from io_soulstruct.general.game_config import BLENDER_GAME_CONFIG
from io_soulstruct.utilities import *

if tp.TYPE_CHECKING:
    from .game_structure import GameStructure


STEAM_COMMON_LOCATIONS = [
    Path(f"{drive}:/Program Files (x86)/Steam/steamapps/common")
    for drive in "CDEFGH"
] + [
    Path(f"{drive}:/Steam/steamapps/common")
    for drive in "CDEFGH"
]


_DETECTED_MAP_ENUM_ITEMS = []  # type: list[tuple[str, str, str]]


# noinspection PyUnusedLocal
def _get_detected_map_enum_items(self, context):
    return _DETECTED_MAP_ENUM_ITEMS


class _SelectMapDirectory(LoggingOperator):
    """Browse for game map directory to set `map_stem` setting.

    Concrete subclasses are given for 'game' and 'project' directories.

    Does not change game/project subdirectory. Purely takes the name of the chosen folder. But for clarity, raises an
    error if the chosen folder is not a game/project subdirectory.
    """
    SOURCE: tp.ClassVar[str]

    directory: str
    map_choice: str  # EnumProperty

    @classmethod
    @abc.abstractmethod
    def get_root(cls, context) -> GameStructure | None:
        ...

    @classmethod
    def poll(cls, context) -> bool:
        return cls.get_root(context) is not None

    @staticmethod
    def set_map_options(
        map_dir: Path,
        glob_str="m??_??_??_??",
        extra_filter: tp.Callable[[str], bool] = None,
        get_map_desc: tp.Callable[[str], str] = None,
    ):
        _DETECTED_MAP_ENUM_ITEMS.clear()
        for map_stem_folder in map_dir.glob(glob_str):
            map_stem = map_stem_folder.name
            if extra_filter and not extra_filter(map_stem):
                continue  # ignore this map
            if get_map_desc:
                try:
                    desc = get_map_desc(map_stem)
                except (KeyError, AttributeError, ValueError):
                    desc = f"Map {map_stem}"
            else:
                desc = f"Map {map_stem}"

            _DETECTED_MAP_ENUM_ITEMS.append((map_stem, map_stem, desc))

    def set_map_options_eldenring(self, map_dir: Path, filter_mode: str):
        """Elden Ring nests overworld maps under m60/m61, and checks an extra filter enum."""

        def get_map_desc(map_stem: str):
            return BLENDER_GAME_CONFIG["ELDEN_RING"].map_constants.get_map(map_stem).verbose_name

        if filter_mode.endswith("DUNGEONS"):
            # Dungeons. Possible extra area check.
            if filter_mode.startswith("LEGACY"):
                def extra_filter(map_stem: str):
                    return 10 <= int(map_stem[1:3]) < 30
            elif filter_mode.startswith("GENERIC"):
                def extra_filter(map_stem: str):
                    return 30 <= int(map_stem[1:3]) < 60
            else:
                extra_filter = None
            return self.set_map_options(map_dir, extra_filter=extra_filter, get_map_desc=get_map_desc)

        if filter_mode.startswith("OVERWORLD"):
            # Check 'm60' subfolder.
            glob_str = "m60/m60_??_??_"
        elif filter_mode.startswith("DLC_OVERWORLD"):
            # Check 'm61' subfolder.
            glob_str = "m61/m61_??_??_"
        else:
            # Unrecognized.
            return

        if filter_mode.endswith("_V1"):
            glob_str += "1"

        if "OVERWORLD_SMALL" in filter_mode:
            glob_str += "0"
        elif "OVERWORLD_MEDIUM" in filter_mode:
            glob_str += "1"
        elif "OVERWORLD_LARGE" in filter_mode:
            glob_str += "2"

        return self.set_map_options(map_dir, glob_str, get_map_desc=get_map_desc)

    def invoke(self, context, _event):
        """Set the initial directory."""
        global _DETECTED_MAP_ENUM_ITEMS

        settings = self.settings(context)
        root = self.get_root(context)
        if not root:
            return self.error(f"{self.SOURCE} directory not set.")
        map_dir = root.get_dir_path("map", if_exist=True)  # type: Path | None
        if not map_dir:
            return self.error(f"{self.SOURCE} 'map' directory not found.")
        if settings.is_game("ELDEN_RING"):
            self.set_map_options_eldenring(map_dir, settings.er_map_filter_mode)
        else:

            def get_map_desc(map_stem: str):
                try:
                    return BLENDER_GAME_CONFIG[settings.game].map_constants.get_map(map_stem).verbose_name
                except (KeyError, AttributeError, ValueError):
                    return map_stem

            self.set_map_options(map_dir, get_map_desc=get_map_desc)

        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        settings = self.settings(context)
        settings.map_stem = self.map_choice

        return {"FINISHED"}


class SelectGameMapDirectory(_SelectMapDirectory):
    """Browse for game map directory to set `map_stem` setting."""
    bl_idname = "soulstruct.select_game_map_directory"
    bl_label = "Select Map from Game"
    bl_description = "Select a map subdirectory in game 'map' folder"

    SOURCE = "Game"

    map_choice: bpy.props.EnumProperty(
        name="Game Map",
        description="Subfolders of 'map' in selected game directory",
        items=_get_detected_map_enum_items,
    )

    @classmethod
    def get_root(cls, context) -> GameStructure:
        settings = cls.settings(context)
        return settings.game_root


class SelectProjectMapDirectory(_SelectMapDirectory):
    """Browse for project map directory to set `map_stem` setting."""
    bl_idname = "soulstruct.select_project_map_directory"
    bl_label = "Select Map from Project"
    bl_description = "Select a map subdirectory in project 'map' folder"

    SOURCE = "Project"

    map_choice: bpy.props.EnumProperty(
        name="Project Map",
        description="Subfolders of 'map' in selected project directory",
        items=_get_detected_map_enum_items,
    )

    @classmethod
    def get_root(cls, context) -> GameStructure:
        settings = cls.settings(context)
        return settings.project_root


class SelectImageCacheDirectory(LoggingOperator):
    """Browse for global image cache directory."""
    bl_idname = "soulstruct.select_image_cache_directory"
    bl_label = "Select Image Cache Directory"
    bl_description = "Select image texture cache directory with browser"

    directory: bpy.props.StringProperty()

    filter_glob: bpy.props.StringProperty(
        default="",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def invoke(self, context, _event):
        """Set the initial directory."""
        settings = self.settings(context)
        default_dir = settings.get_import_dir_path()
        if default_dir:
            self.directory = str(default_dir)
        else:
            for steam_common_location in STEAM_COMMON_LOCATIONS:
                if steam_common_location.is_dir():
                    self.directory = str(steam_common_location)
                    break
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if self.directory:
            image_cache_directory = Path(self.directory).resolve()
            settings = self.settings(context)
            settings.str_image_cache_directory = str(image_cache_directory)
        return {"FINISHED"}


class SelectCustomMTDBNDFile(LoggingImportOperator):
    """Browse for custom MTDBND file."""
    bl_idname = "soulstruct.select_custom_mtdbnd_file"
    bl_label = "Select Custom MTDBND File"
    bl_description = "Select custom MTDBND file with browser"

    filter_glob: bpy.props.StringProperty(default="*.mtdbnd;*.mtdbnd.dcx", options={"HIDDEN"})

    def execute(self, context):
        if self.filepath:
            mtdbnd_path = Path(self.filepath).resolve()
            mat_settings = context.scene.flver_material_settings
            mat_settings.str_mtdbnd_path = str(mtdbnd_path)
        return {"FINISHED"}


class SelectCustomMATBINBNDFile(LoggingImportOperator):
    """Browse for custom MATBINBND file."""
    bl_idname = "soulstruct.select_custom_matbinbnd_file"
    bl_label = "Select Custom MATBINBND File"
    bl_description = "Select custom MATBINBND file with browser"

    filter_glob: bpy.props.StringProperty(default="*.matbinbnd;*.matbinbnd.dcx", options={"HIDDEN"})

    def execute(self, context):
        if self.filepath:
            matbinbnd_path = Path(self.filepath).resolve()
            mat_settings = context.scene.flver_material_settings
            mat_settings.str_matbinbnd_path = str(matbinbnd_path)
        return {"FINISHED"}


class LoadCollectionsFromBlend(LoggingImportOperator):
    """Load collections and objects from a '.blend' file by linking its root-level collections to this scene.

    Works best with Blend files created using `io_export_blend`, and also works best when all objects in the Blend are
    at least two collections deep.
    """
    bl_idname = "soulstruct.load_collections_from_blend"
    bl_label = "Load Collections from Blend"
    bl_description = "Load collections from a .blend file"

    filter_glob: bpy.props.StringProperty(
        default="*.blend",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        if not self.filepath:
            return self.error("No file selected.")

        # Get the objects and collections from the file.
        with bpy.data.libraries.load(self.filepath, link=False) as (data_from, data_to):
            data_to.collections = data_from.collections
            data_to.objects = data_from.objects

        imported_collections = [col for col in data_to.collections if col is not None]

        def is_top_level_collection(collection):
            for col in imported_collections:
                if collection.name in col.children:
                    return False
            return True

        top_level_collections = [col for col in imported_collections if is_top_level_collection(col)]

        for top_level_collection in top_level_collections:
            bpy.context.scene.collection.children.link(top_level_collection)

        self.info(f"{len(top_level_collections)} top-level collections loaded from '{self.filepath}'.")

        for lib in bpy.data.libraries:
            if lib.name == Path(self.filepath).name:
                # Remove this library. We're not referencing it.
                bpy.data.libraries.remove(lib)

        return {"FINISHED"}
