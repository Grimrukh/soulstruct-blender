from __future__ import annotations

__all__ = [
    "LoggingOperator",
    "get_dcx_enum_property",
]

import typing as tp

import bpy

if tp.TYPE_CHECKING:
    from soulstruct.dcx import DCXType


class LoggingOperator(bpy.types.Operator):

    cleanup_callback: tp.Callable = None

    # TODO: `report` seems to log to console for FLVER operators, but not HKX?

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


def get_dcx_enum_property(
    default: str | DCXType = "Auto",
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
            ("Auto", "Auto", "Use Soulstruct default DCX for this game, file type, and export target"),
            ("Null", "None", "Export without any DCX compression"),
            ("DCX_EDGE", "DES", "Demon's Souls compression"),
            ("DCX_DFLT_10000_24_9", "DS1/DS2", "Dark Souls 1/2 compression"),
            ("DCX_DFLT_10000_44_9", "BB/DS3", "Bloodborne/Dark Souls 3 compression"),
            ("DCX_DFLT_11000_44_9", "Sekiro", "Sekiro compression (requires Oodle DLL)"),
            ("DCX_KRAK", "Elden Ring", "Elden Ring compression (requires Oodle DLL)"),
        ],
        description=description,
        default=default if isinstance(default, str) else default.name,
    )
