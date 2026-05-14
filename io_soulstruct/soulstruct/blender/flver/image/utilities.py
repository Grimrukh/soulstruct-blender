from __future__ import annotations

__all__ = [
    "get_possible_image_names",
    "find_or_create_image",
]

import bpy

from ...base.operators import LoggingOperator


def get_possible_image_names(image_stem: str) -> tuple[str, ...]:
    """Get all possible `Image` names for the given image stem, in order of preferred usage."""
    return f"{image_stem}", f"{image_stem}.tga", f"{image_stem}.png", f"{image_stem}.dds"


def find_or_create_image(operator: LoggingOperator, context: bpy.types.Context, image_stem: str) -> bpy.types.Image:
    for image_name in (
        get_possible_image_names(image_stem)
    ):
        try:
            return bpy.data.images[image_name]
        except KeyError:
            pass
    else:
        # Blender image not found. Create empty 1x1 Blender image with no extension.
        bl_image = bpy.data.images.new(name=image_stem, width=1, height=1, alpha=True)
        color = [1.0, 0.0, 1.0, 1.0]  # magenta
        do_warning = context.scene.flver_import_settings.import_textures
        if "systex" in image_stem:
            do_warning = False
            if "black" in image_stem:
                color = [0.0, 0.0, 0.0, 1.0]
            elif "white" in image_stem:
                color = [1.0, 1.0, 1.0, 1.0]
            elif "noise" in image_stem:
                color = [0.5, 0.5, 0.5, 1.0]  # grey
            elif "dummy" in image_stem:
                color = [0.5, 0.5, 0.5, 1.0]  # grey
        # noinspection PyTypeChecker
        bl_image.pixels = color
        if do_warning:
            operator.warning(
                f"Could not find texture '{image_stem}' in Blender image data. "
                f"Created 1x1 magenta Image."
            )
        return bl_image
