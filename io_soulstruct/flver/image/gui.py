from __future__ import annotations

__all__ = [
    "DDSTexturePanel",
]

import bpy
from .types import DDSTexture


class DDSTexturePanel(bpy.types.Panel):
    """Panel for Image DDS texture settings. Appears in IMAGE_EDITOR space."""
    bl_label = "DDS Settings"
    bl_idname = "SCENE_PT_dds_texture"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "DDS"

    def draw(self, context):
        layout = self.layout
        area = context.area
        if area.type != "IMAGE_EDITOR":
            return  # shouldn't be possible
        # noinspection PyTypeChecker
        space = area.spaces.active  # type: bpy.types.SpaceImageEditor
        image = space.image
        if image is None:
            layout.label(text="No image selected.")
            return
        if len(image.pixels) <= 4:
            layout.label(text="Image has 1 or less pixels.")
            return

        # Draw DDS Texture properties.
        dds_texture = DDSTexture(image)
        for prop in dds_texture.texture_properties.__annotations__:
            layout.prop(dds_texture.texture_properties, prop)
