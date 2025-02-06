from __future__ import annotations

__all__ = ["ExportHKXCutscene"]

from bpy.props import StringProperty

from soulstruct.dcx import DCXType

from io_soulstruct.utilities import *


class ExportHKXCutscene(LoggingExportOperator):
    """Export RemoBND cutscene animation from Actions attached to all selected FLVER armatures."""
    bl_idname = "export_scene.hkx_cutscene"
    bl_label = "Export HKX Cutscene"
    bl_description = "Export all selected armatures' Blender actions to a RemoBND cutscene file"

    filename_ext = ".remobnd"

    filter_glob: StringProperty(
        default="*.remobnd;*.remobnd.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    dcx_type: get_dcx_enum_property(DCXType.DS1_DS2)  # DS1 RemoBND default

    # TODO: Not ridiculously complicated anymore.
    #   - Can require camera selection for export.
    #   - Scan all MSB Parts with Armatures. Any with Actions prefixed with camera's cutscene name are used.
    #   - Export to RemoBND just like Animation export, by just recording transforms (and camera focal length).

    @classmethod
    def poll(cls, context) -> bool:
        # TODO: All selected objects must be armatures.
        try:
            return context.selected_objects[0].type == "ARMATURE"
        except IndexError:
            return False

    def execute(self, context):
        # TODO
        print("Executing HKX cutscene export...")
        return {"FINISHED"}
