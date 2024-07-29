from __future__ import annotations

__all__ = [
    "SelectGameDirectory",
    "SelectProjectDirectory",
    "SelectGameMapDirectory",
    "SelectProjectMapDirectory",
    "SelectPNGCacheDirectory",
    "SelectCustomMTDBNDFile",
    "SelectCustomMATBINBNDFile",
    "LoadCollectionsFromBlend",
]

import abc
import typing as tp
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper

from io_soulstruct.utilities import LoggingOperator, MAP_STEM_RE

if tp.TYPE_CHECKING:
    from .game_structure import GameStructure


STEAM_COMMON_LOCATIONS = [
    Path(f"{drive}:/Program Files (x86)/Steam/steamapps/common")
    for drive in "CDEFGH"
] + [
    Path(f"{drive}:/Steam/steamapps/common")
    for drive in "CDEFGH"
]


class SelectGameDirectory(LoggingOperator):
    """Browse for global game directory."""
    bl_idname = "soulstruct.select_game_directory"
    bl_label = "Select Game Directory"
    bl_description = "Select game directory with browser"

    directory: bpy.props.StringProperty()

    filter_glob: bpy.props.StringProperty(
        default="",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def invoke(self, context, _event):
        """Set the initial directory to browse in, if it exists."""
        for steam_common_location in STEAM_COMMON_LOCATIONS:
            if steam_common_location.is_dir():
                self.directory = str(steam_common_location)
                break
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if self.directory:
            # We use browser's current `directory`, not `filepath` itself.
            game_directory = Path(self.directory).resolve()
            settings = self.settings(context)
            settings.str_game_directory = str(game_directory)
            settings.auto_set_game()

        return {"FINISHED"}


class SelectProjectDirectory(LoggingOperator):
    """Browse for global project directory."""
    bl_idname = "soulstruct.select_project_directory"
    bl_label = "Select Project Directory"
    bl_description = "Select project directory with browser"

    directory: bpy.props.StringProperty()

    filter_glob: bpy.props.StringProperty(
        default="",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def invoke(self, context, _event):
        """Set the initial directory to browse in, if it exists."""
        for steam_common_location in STEAM_COMMON_LOCATIONS:
            if steam_common_location.is_dir():
                self.directory = str(steam_common_location)
                break
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if self.directory:
            # We use browser's current `directory`, not `filepath` itself.
            project_directory = Path(self.directory).resolve()
            settings = self.settings(context)
            settings.str_project_directory = str(project_directory)
            # We do NOT auto-set game here, because the user may be exporting to any folder.

        return {"FINISHED"}


class _SelectMapDirectory(LoggingOperator):
    """Browse for game map directory to set `map_stem` setting.

    Concrete subclasses are given for 'game' and 'project' directories.

    Does not change game/project subdirectory. Purely takes the name of the chosen folder. But for clarity, raises an
    error if the chosen folder is not a game/project subdirectory.
    """

    directory: str

    @classmethod
    @abc.abstractmethod
    def get_root(cls, context) -> GameStructure:
        ...

    @classmethod
    def poll(cls, context):
        return cls.get_root(context) is not None

    def invoke(self, context, _event):
        """Set the initial directory."""
        root = self.get_root(context)
        if root is not None and (map_dir := root.get_dir_path("map", if_exist=True)):
            self.directory = str(map_dir)
        else:
            for steam_common_location in STEAM_COMMON_LOCATIONS:
                if steam_common_location.is_dir():
                    self.directory = str(steam_common_location)
                    break
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def validate_directory(self, context, map_directory: Path):
        """Make sure it's in '{root}/map'."""
        root = self.get_root(context)
        if not root:
            self.error("No game or project root found to validate map directory.")
            return False
        if not map_directory.is_dir():
            self.error("Selected directory does not exist.")
            return False
        if not map_directory.parent == root.get_dir_path("map"):
            self.error("Selected directory is not a subdirectory of the 'map' directory.")
            return False
        if not MAP_STEM_RE.match(map_directory.name):
            self.warning("Selected directory does not appear to be a valid map directory name. Allowing anyway.")
        return True

    def execute(self, context):
        if self.directory:
            map_directory = Path(self.directory).resolve()
            if not self.validate_directory(context, map_directory):
                return {"CANCELLED"}

            settings = self.settings(context)
            settings.map_stem = map_directory.name

        return {"FINISHED"}


class SelectGameMapDirectory(_SelectMapDirectory):
    """Browse for game map directory to set `map_stem` setting."""
    bl_idname = "soulstruct.select_game_map_directory"
    bl_label = "Select Map from Game"
    bl_description = "Select a map subdirectory in game 'map' folder"

    directory: bpy.props.StringProperty()

    filter_glob: bpy.props.StringProperty(
        default="m??_??_??_??",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
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

    directory: bpy.props.StringProperty()

    filter_glob: bpy.props.StringProperty(
        default="m??_??_??_??",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    @classmethod
    def get_root(cls, context) -> GameStructure:
        settings = cls.settings(context)
        return settings.project_root


class SelectPNGCacheDirectory(LoggingOperator):
    """Browse for global PNG texture cache directory."""
    bl_idname = "soulstruct.select_png_cache_directory"
    bl_label = "Select PNG Cache Directory"
    bl_description = "Select PNG texture cache directory with browser"

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
            png_cache_directory = Path(self.directory).resolve()
            settings = self.settings(context)
            settings.str_png_cache_directory = str(png_cache_directory)
        return {"FINISHED"}


class SelectCustomMTDBNDFile(LoggingOperator, ImportHelper):
    """Browse for custom MTDBND file."""
    bl_idname = "soulstruct.select_custom_mtdbnd_file"
    bl_label = "Select Custom MTDBND File"
    bl_description = "Select custom MTDBND file with browser"

    filename_ext = ".mtdbnd"
    filter_glob: bpy.props.StringProperty(default="*.mtdbnd;*.mtdbnd.dcx", options={"HIDDEN"})

    def execute(self, context):
        if self.filepath:
            mtdbnd_path = Path(self.filepath).resolve()
            settings = self.settings(context)
            settings.str_mtdbnd_path = str(mtdbnd_path)
        return {"FINISHED"}


class SelectCustomMATBINBNDFile(LoggingOperator, ImportHelper):
    """Browse for custom MATBINBND file."""
    bl_idname = "soulstruct.select_custom_matbinbnd_file"
    bl_label = "Select Custom MATBINBND File"
    bl_description = "Select custom MATBINBND file with browser"

    filename_ext = ".matbinbnd"
    filter_glob: bpy.props.StringProperty(default="*.matbinbnd;*.matbinbnd.dcx", options={"HIDDEN"})

    def execute(self, context):
        if self.filepath:
            matbinbnd_path = Path(self.filepath).resolve()
            settings = self.settings(context)
            settings.str_matbinbnd_path = str(matbinbnd_path)
        return {"FINISHED"}


class LoadCollectionsFromBlend(LoggingOperator, ImportHelper):
    """Load collections and objects from a '.blend' file by linking its root-level collections to this scene.

    Works best with Blend files created using `io_export_blend`, and also works best when all objects in the Blend are
    at least two collections deep.
    """
    bl_idname = "soulstruct.load_collections_from_blend"
    bl_label = "Load Collections from Blend"
    bl_description = "Load collections from a .blend file"

    filename_ext = ".blend"

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
