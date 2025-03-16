"""Miscellaneous FLVER texture/image operators."""
from __future__ import annotations

__all__ = [
    "FindMissingTexturesInImageCache",
]

import bpy

from io_soulstruct.utilities import LoggingOperator


class FindMissingTexturesInImageCache(LoggingOperator):
    """Iterate over all texture nodes used by all materials of one or more selected objects (typically FLVER meshes) and
    (if currently a 1x1 dummy texture) find that file in the image cache directory.

    This modified the Blender Image data, so obviously, it will affect all models/materials that use this texture.

    Note that this will link the texture to the cached image file. It will not pack the image data into the Blend file.
    """
    bl_idname = "mesh.find_missing_textures_in_image_cache"
    bl_label = "Find Missing Textures in Image Cache"
    bl_description = "Find missing texture names used by materials of selected objects in image cache"

    @classmethod
    def poll(cls, context) -> bool:
        return context.selected_objects and all(obj.type == "MESH" for obj in context.selected_objects)

    def execute(self, context):

        settings = self.settings(context)

        checked_image_names = set()  # to avoid looking for the same image twice
        image_suffix = settings.bl_image_format.get_suffix()

        for obj in context.selected_objects:
            obj: bpy.types.MeshObject
            for material in obj.data.materials:
                # noinspection PyUnresolvedReferences,PyTypeChecker
                texture_nodes = [
                    node for node in material.node_tree.nodes
                    if node.type == "TEX_IMAGE" and node.image is not None
                ]  # type: list[bpy.types.ShaderNodeTexImage]
                for node in texture_nodes:
                    image = node.image  # type: bpy.types.Image
                    if len(image.pixels) != 4:
                        continue  # not 1x1
                    if image.pixels[:] != [1.0, 0.0, 1.0, 0.0]:
                        continue  # not magenta

                    # This is a dummy texture. Try to find it in the image cache.
                    image_name = image.name
                    if image_name.endswith(".dds"):
                        image_name = image_name.removesuffix(".dds") + image_suffix
                    elif not image_name.endswith(image_suffix):
                        image_name += image_suffix
                    if image_name in checked_image_names:
                        continue
                    checked_image_names.add(image_name)
                    image_path = settings.image_cache_directory / image_name
                    if image_path.is_file():
                        # NOTE: We can't update the DDS Texture settings of the image.
                        image.filepath = str(image_path)
                        image.file_format = settings.bl_image_format
                        image.source = "FILE"
                        image.reload()
                        self.info(f"Found and linked texture file '{image_name}' in image cache.")
                    else:
                        self.warning(f"Could not find texture file '{image_name}' in image cache.")

        return {"FINISHED"}
