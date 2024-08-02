
__all__ = ["ImportFullMSB"]

import time

import bpy
from io_soulstruct.utilities import LoggingOperator
from .parts import *
from .regions import *


class ImportFullMSB(LoggingOperator):

    bl_idname = "import_scene.import_full_msb"
    bl_label = "Import Full MSB"
    bl_description = "Import all MSB entries from active map"

    @classmethod
    def poll(cls, context):
        return bool(context.scene.soulstruct_settings.map_stem)

    def invoke(self, context, event):
        """Confirmation dialog."""
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):

        p = time.perf_counter()

        import_scene = bpy.ops.import_scene
        for operator in (
            ImportAllMSBMapPieces,
            ImportAllMSBCollisions,  # important to import early!
            ImportAllMSBObjects,
            ImportAllMSBCharacters,
            ImportAllMSBPlayerStarts,
            ImportAllMSBNavmeshes,
            ImportAllMSBConnectCollisions,
            ImportAllMSBPoints,
            ImportAllMSBVolumes,
            # TODO: Events. And switch on Assets/Objects for ER.
        ):
            op = getattr(import_scene, operator.bl_idname.split(".")[-1])
            try:
                op("EXEC_DEFAULT")  # no confirmation dialog
            except Exception as ex:
                return self.error(f"Failed to run {operator.__name__}: {ex}")

        print(
            f"Full MSB import for '{context.scene.soulstruct_settings.map_stem} "
            f"took {time.perf_counter() - p:.2f} seconds."
        )

        return {"FINISHED"}
