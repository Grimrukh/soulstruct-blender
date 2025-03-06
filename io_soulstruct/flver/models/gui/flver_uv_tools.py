from __future__ import annotations

__all__ = [
    "FLVERUVMapsPanel",
]

import bpy

from io_soulstruct.flver.models.operators.uv_operators import *


class FLVERUVMapsPanel(bpy.types.Panel):
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
