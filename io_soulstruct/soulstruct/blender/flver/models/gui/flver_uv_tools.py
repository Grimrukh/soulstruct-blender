from __future__ import annotations

__all__ = [
    "FLVERUVMapsPanel",
]

from ....base.register import io_soulstruct_class
from ....bpy_base.panel import SoulstructPanel
from ..operators.uv_operators import *


@io_soulstruct_class
class FLVERUVMapsPanel(SoulstructPanel):
    """Panel for Soulstruct FLVER UV map operators. Appears in 'IMAGE_EDITOR' space."""
    bl_label = "FLVER UV Maps"
    bl_idname = "SCENE_PT_uv_maps"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.operator(ActivateUVMap.bl_idname)
