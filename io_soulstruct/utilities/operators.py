from __future__ import annotations

__all__ = [
    "Context",
    "LoggingOperator",
    "LoggingImportOperator",
    "LoggingExportOperator",
    "get_dcx_enum_property",
]

import typing as tp
from pathlib import Path

import bpy
from bpy.types import Context
from bpy_extras.io_utils import ImportHelper, ExportHelper
from soulstruct.dcx import DCXType

if tp.TYPE_CHECKING:
    from io_soulstruct.general.core import SoulstructSettings


class LoggingOperator(bpy.types.Operator):

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
        game_directory = context.scene.soulstruct_settings.game_directory
        if game_directory and game_directory.is_dir():
            self.directory = str(game_directory)
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
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
        project_directory = context.scene.soulstruct_settings.project_directory
        if project_directory and Path(project_directory).is_dir():
            self.directory = str(project_directory)
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        return super().invoke(context, _event)


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
