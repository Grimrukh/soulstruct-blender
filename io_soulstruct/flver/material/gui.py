from __future__ import annotations

__all__ = [
    "FLVERMaterialPropsPanel",
]

import bpy


class FLVERMaterialPropsPanel(bpy.types.Panel):
    """FLVER Material properties, available on all Blender materials."""
    bl_label = "FLVER Material Settings"
    bl_idname = "MATERIAL_PT_flver_material"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    def draw(self, context):
        layout = self.layout

        # Get active material on active object.
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            layout.label(text="No active mesh object.")
            return
        material = obj.active_material
        props = material.FLVER_MATERIAL

        for prop in props.__annotations__:
            layout.prop(props, prop)
