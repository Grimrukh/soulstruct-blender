"""Material operators."""
from __future__ import annotations

__all__ = ["MaterialToolSettings", "SetMaterialTexture0", "SetMaterialTexture1"]

import typing as tp

import bpy

from io_soulstruct.utilities.operators import LoggingOperator


class MaterialToolSettings(bpy.types.PropertyGroup):

    albedo_image: bpy.props.PointerProperty(
        name="Albedo Image",
        type=bpy.types.Image,
    )


class _SetMaterialTexture(LoggingOperator):

    SLOT_SUFFIX: tp.ClassVar[str]

    @classmethod
    def poll(cls, context):
        """An object must be selected."""
        return context.object is not None and context.object.active_material is not None

    def execute(self, context):
        return self.set_textures(context, self.SLOT_SUFFIX)

    def set_textures(self, context, slot_suffix: str):
        # Get selected material of selected object.
        selected_object = context.object
        if not selected_object:
            return self.error("No object selected.")
        selected_material = selected_object.active_material
        if not selected_material:
            return self.error("No material selected.")

        tool_settings = context.scene.material_tool_settings
        albedo_image = tool_settings.albedo_image
        if not albedo_image:
            return self.error("No albedo image selected.")

        # Try to find specular and normal images with "_s" and "_n" suffixes, respectively.
        albedo_image_name = albedo_image.name
        # Split name into stem and suffix.
        stem, suffix = albedo_image_name.rsplit(".", 1)
        # TODO: Game-dependent specular/normal suffixes, and also sheen.
        specular_image_name = f"{stem}_s.{suffix}"
        normal_image_name = f"{stem}_n.{suffix}"

        # These could be None. We still set them to the nodes.
        specular_image = bpy.data.images.get(specular_image_name)
        if not specular_image:
            self.warning(f"No specular texture named '{specular_image_name} found. Node image will be removed.")
        normal_image = bpy.data.images.get(normal_image_name)
        if not normal_image:
            self.warning(f"No normal texture named '{normal_image_name} found. Node image will be removed.")

        nodes = selected_material.node_tree.nodes
        for common_type, image in zip(["ALBEDO", "SPECULAR", "NORMAL"], [albedo_image, specular_image, normal_image]):
            node_name = f"{common_type}{slot_suffix}"
            try:
                node = nodes[node_name]
            except KeyError:
                self.warning(
                    f"No node named '{node_name}' found in material. Texture not {'set' if image else 'removed'}."
                )
            else:
                node.image = image

        return {"FINISHED"}


class SetMaterialTexture0(_SetMaterialTexture):

    bl_idname = "object.set_material_texture_0"
    bl_label = "Set Material Texture 0"
    bl_description = ("Set the first diffuse texture (e.g. 'g_Diffuse' in DS1) of the selected material to the selected "
                      "texture. Will attempt to set specular and normal textures as well, if nodes exist")

    SLOT_SUFFIX = "_0"


class SetMaterialTexture1(_SetMaterialTexture):

    bl_idname = "object.set_material_texture_1"
    bl_label = "Set Material Texture 1"
    bl_description = ("Set the second diffuse texture (e.g. 'g_Diffuse_2' in DS1) of the selected material to the "
                      "selected texture. Will attempt to set specular and normal textures as well, if nodes exist")

    SLOT_SUFFIX = "_1"


# TODO:
#   - Material Creator (dropdown of basic known MTD names like 'M[DB][M]')
