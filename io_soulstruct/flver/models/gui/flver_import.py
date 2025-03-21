from __future__ import annotations

__all__ = [
    "FLVERImportPanel",
]

from io_soulstruct.bpy_base.panel import SoulstructPanel

from ..operators.import_operators import *


class FLVERImportPanel(SoulstructPanel):
    """Panel for Soulstruct FLVER operators."""
    bl_label = "FLVER Import"
    bl_idname = "SCENE_PT_flver_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        settings = context.scene.soulstruct_settings

        self.draw_active_map(context, layout)

        # NOTE: FLVER import settings are exposed within each individual operator (all use browser pop-ups).

        layout.label(text="Import from Game/Project:")
        layout.operator(ImportMapPieceFLVER.bl_idname)
        layout.operator(ImportCharacterFLVER.bl_idname)
        if settings.is_game("ELDEN_RING"):
            layout.operator(ImportAssetFLVER.bl_idname)
        else:
            layout.operator(ImportObjectFLVER.bl_idname)
        layout.operator(ImportEquipmentFLVER.bl_idname)

        layout.label(text="Generic Import:")
        layout.operator(ImportFLVER.bl_idname, text="Import Any FLVER")
