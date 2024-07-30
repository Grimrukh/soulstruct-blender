from __future__ import annotations

__all__ = [
    "Context",
    "LoggingOperator",
    "LoggingImportOperator",
    "LoggingExportOperator",
    "BinderEntrySelectOperator",
    "get_dcx_enum_property",
]

import abc
import re
import shutil
import tempfile
import typing as tp
from pathlib import Path

import bpy
from bpy.types import Context
from bpy_extras.io_utils import ImportHelper, ExportHelper
from soulstruct.dcx import DCXType
from soulstruct.containers import Binder, BinderEntry

if tp.TYPE_CHECKING:
    from io_soulstruct.general.properties import SoulstructSettings


class LoggingOperator(bpy.types.Operator):

    # TODO: Move into `cancel()`.
    cleanup_callback: tp.Callable = None

    @staticmethod
    def settings(context) -> SoulstructSettings:
        """Retrieve and save current Soulstruct plugin general settings."""
        _settings = context.scene.soulstruct_settings
        _settings.save_settings()
        return _settings

    def info(self, msg: str):
        print(f"# INFO: {msg}")
        self.report({"INFO"}, msg)

    def warning(self, msg: str):
        print(f"# WARNING: {msg}")
        self.report({"WARNING"}, msg)

    def error(self, msg: str) -> set[str]:
        # print(f"# ERROR: {msg}")
        if self.cleanup_callback:
            try:
                self.cleanup_callback()
            except Exception as ex:
                self.report({"ERROR"}, f"Error occurred during cleanup callback: {ex}")
        self.report({"ERROR"}, msg)
        return {"CANCELLED"}

    def execute(self, context):
        try:
            execute = getattr(self, "_execute")
        except AttributeError:
            return self.error(f"Operator {self.bl_idname} does not have an `_execute` method to wrap with profiler.")
        from soulstruct.utilities.inspection import profile_function
        decorated_execute = profile_function(20, sort="cumtime")(execute)
        return decorated_execute(context)

    @staticmethod
    def to_object_mode():
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

    @staticmethod
    def to_edit_mode():
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="EDIT", toggle=False)

    @staticmethod
    def deselect_all():
        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action="DESELECT")

    @staticmethod
    def set_active_obj(obj: bpy.types.Object):
        LoggingOperator.deselect_all()
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj


class LoggingImportOperator(LoggingOperator, ImportHelper):
    """Includes default `invoke()` class method that defaults to selected game directory."""

    # Type hints for `ImportHelper` properties (must be defined by each `Operator` leaf class).
    files: tp.Collection[bpy.types.OperatorFileListElement]
    directory: str

    def invoke(self, context, _event):
        """Set the initial directory based on Global Settings."""
        game_directory = context.scene.soulstruct_settings.game_root_path
        if game_directory and game_directory.is_dir():
            self.directory = str(game_directory)
            context.window_manager.fileselect_add(self)
            return {"RUNNING_MODAL"}
        return super().invoke(context, _event)

    @property
    def file_paths(self) -> list[Path]:
        return [Path(self.directory, file.name) for file in self.files]


class LoggingExportOperator(LoggingOperator, ExportHelper):
    """Includes default `invoke()` class method that defaults to selected game directory."""

    # Type hints for `ExportHelper` properties (must be defined by each `Operator` leaf class).
    directory: str

    def invoke(self, context, _event):
        """Set the initial directory based on Global Settings."""
        project_directory = context.scene.soulstruct_settings.project_root_path
        if project_directory and Path(project_directory).is_dir():
            self.directory = str(project_directory)
            context.window_manager.fileselect_add(self)
            return {"RUNNING_MODAL"}
        return super().invoke(context, _event)


class BinderEntrySelectOperator(LoggingOperator):

    # Set by `invoke` when entry choices are written to temp directory.
    binder: Binder  # NOTE: must NOT be imported under `TYPE_CHECKING` guard, as Blender loads annotations

    temp_directory: bpy.props.StringProperty(
        name="Temp Binder Directory",
        description="Temporary directory containing Binder entry choices",
        default="",
        options={'HIDDEN'},
    )

    filter_glob: bpy.props.StringProperty(
        default="*",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Chosen Binder entry",
        maxlen=1024,
        subtype="FILE_PATH",
    )
    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'})

    ENTRY_NAME_RE = re.compile(r"\((\d+)\) (.+)")

    @classmethod
    @abc.abstractmethod
    def get_binder(cls, context) -> Binder | None:
        """Subclass must implement this function to find the relevant Binder file to unpack and offer."""
        ...

    @classmethod
    def filter_binder_entry(cls, context, entry: BinderEntry) -> bool:
        """Can be overridden to filter for only particular entries."""
        return True

    # No base `poll()` defined.

    def cancel(self, context):
        """Make sure we clear the directory even when cancelled."""
        if self.temp_directory:
            shutil.rmtree(self.temp_directory, ignore_errors=True)
            self.temp_directory = ""
        super().cancel(context)

    def invoke(self, context, event):
        """Unpack valid Binder entry choices to temp directory for user to select from."""
        if self.temp_directory:
            shutil.rmtree(self.temp_directory, ignore_errors=True)
            self.temp_directory = ""

        self.binder = self.get_binder(context)
        if self.binder is None:
            return self.error("No Binder could be loaded for entry import.")

        self.temp_directory = tempfile.mkdtemp(suffix="_" + self.binder.path_stem)
        for entry in self.binder.entries:
            if not self.filter_binder_entry(context, entry):
                continue
            # We use the index to ensure unique file names while allowing duplicate entry names (e.g. Regions).
            file_name = f"({entry.id}) {entry.name}"  # name will include extension
            file_path = Path(self.temp_directory, file_name)
            with file_path.open("w") as f:
                f.write(entry.name)

        # No subdirectories used.
        self.directory = self.temp_directory
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        try:
            entries = self.get_selected_entries()
            if not entries:
                return {"CANCELLED"}  # relevant error already reported
            for entry in entries:
                try:
                    self._import_entry(context, entry)
                except Exception as ex:
                    self.error(f"Error occurred while importing Binder entry '{entry.name}': {ex}")
                    return {"CANCELLED"}
            return {"FINISHED"}
        finally:
            if self.temp_directory:
                shutil.rmtree(self.temp_directory, ignore_errors=True)
                self.temp_directory = ""

    def get_selected_entries(self) -> list[BinderEntry]:
        if not getattr(self, "binder", None):
            self.error("No Binder loaded. Did you cancel the file selection?")
            return []

        file_paths = [Path(self.directory, file.name) for file in self.files]
        entries = []
        for path in file_paths:
            match = self.ENTRY_NAME_RE.match(path.stem)
            if not match:
                self.error(f"Selected file does not match expected format '(i) Name': {self.filepath}")
                return []  # one error cancels all imports

            entry_id, entry_name = int(match.group(1)), match.group(2)
            entry = self.binder.find_entry_id(entry_id)
            if entry is None:
                self.error(f"Could not find Binder entry with ID {entry_id} in Binder file.")
                return []
            entries.append(entry)
        return entries

    @abc.abstractmethod
    def _import_entry(self, context, entry: BinderEntry):
        """Subclass must implement this function to handle the chosen Binder entry."""
        ...


def get_dcx_enum_property(
    default: str | DCXType = "AUTO",
    name="Compression",
    description="Type of DCX compression to apply to exported file or Binder entry",
):
    """Create a Blender `EnumProperty` for selecting DCX compression type.

    Will default to `default` string, which should be one of the items below. The "default default" is "Null", which
    means no DCX compression will be applied.
    """
    return bpy.props.EnumProperty(
        name=name,
        items=[
            ("AUTO", "Auto", "Use Soulstruct default DCX for this game, file type, and export target"),
            (DCXType.Null.name, "None", "Export without any DCX compression"),
            (DCXType.DCX_EDGE.name, "DES", "Demon's Souls compression"),
            (DCXType.DCX_DFLT_10000_24_9.name, "DS1/DS2", "Dark Souls 1/2 compression"),
            (DCXType.DCX_DFLT_10000_44_9.name, "BB/DS3", "Bloodborne/Dark Souls 3 compression"),
            (DCXType.DCX_DFLT_11000_44_9.name, "Sekiro", "Sekiro compression (requires Oodle DLL)"),
            (DCXType.DCX_KRAK.name, "Elden Ring", "Elden Ring compression (requires Oodle DLL)"),
        ],
        description=description,
        default=default if isinstance(default, str) else default.name,
    )
