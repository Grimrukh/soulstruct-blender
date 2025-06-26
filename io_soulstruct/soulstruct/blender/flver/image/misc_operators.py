"""Miscellaneous FLVER texture/image operators."""
from __future__ import annotations

__all__ = [
    "FindMissingTexturesInImageCache",
]

import bpy

from soulstruct.blender.utilities import LoggingOperator, ObjectType, is_path_and_file


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
        mat_settings = context.scene.flver_material_settings
        if not mat_settings.get_game_image_cache_directory(context):
            return False
        return context.selected_objects and all(obj.type == ObjectType.MESH for obj in context.selected_objects)

    def execute(self, context):

        mat_settings = context.scene.flver_material_settings
        checked_image_stems = set()  # to avoid looking for the same image twice

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

                    # This is currently a dummy 1x1 texture. Try to find the real texture in the image cache.
                    image_stem = image.name.removesuffix(".dds")
                    if image_stem in checked_image_stems:
                        continue
                    checked_image_stems.add(image_stem)

                    cached_image_path = mat_settings.get_cached_image_path(context, image_stem)
                    if is_path_and_file(cached_image_path):
                        # NOTE: We can't update the DDS Texture settings of the image.
                        image.filepath = str(cached_image_path)
                        image.file_format = mat_settings.bl_image_cache_format
                        image.source = "FILE"  # not packed
                        image.reload()
                        self.info(f"Found and linked texture file '{cached_image_path.name}' in image cache.")
                    else:
                        self.warning(f"Could not find texture file '{cached_image_path.name}' in image cache.")

        return {"FINISHED"}
