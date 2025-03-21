from __future__ import annotations

__all__ = [
    "NVMHKTImportPanel",
]

from io_soulstruct.bpy_base.panel import SoulstructPanel
from .model_import import *


class NVMHKTImportPanel(SoulstructPanel):
    bl_label = "NVMHKT Import"
    bl_idname = "NVMHKT_PT_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Navmesh"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context) -> bool:
        settings = context.scene.soulstruct_settings
        return settings.is_game("ELDEN_RING")

    # noinspection PyUnusedLocal
    def draw(self, context):
        settings = context.scene.soulstruct_settings
        if not settings.is_game("ELDEN_RING"):
            self.layout.label(text="Elden Ring only.")
            return

        import_loose_box = self.layout.box()
        import_loose_box.operator(ImportNVMHKT.bl_idname)

        settings_box = self.layout.box()
        settings_box.label(text="Import Settings")
        settings_box.prop(context.scene.nvmhkt_import_settings, "import_hires_navmeshes")
        settings_box.prop(context.scene.nvmhkt_import_settings, "import_lores_navmeshes")
        settings_box.prop(context.scene.nvmhkt_import_settings, "correct_model_versions")
        settings_box.prop(context.scene.nvmhkt_import_settings, "create_dungeon_connection_points")
        settings_box.prop(context.scene.nvmhkt_import_settings, "overworld_transform_mode")
        settings_box.prop(context.scene.nvmhkt_import_settings, "dungeon_transform_mode")

        quick_box = self.layout.box()
        quick_box.label(text="From Game/Project")
        quick_box.prop(context.scene.soulstruct_settings, "import_bak_file", text="From .BAK File")
        quick_box.operator(ImportNVMHKTFromNVMHKTBND.bl_idname)
        quick_box.operator(ImportAllNVMHKTsFromNVMHKTBND.bl_idname)
        quick_box.operator(ImportAllOverworldNVMHKTs.bl_idname)
        quick_box.operator(ImportAllDLCOverworldNVMHKTs.bl_idname)
