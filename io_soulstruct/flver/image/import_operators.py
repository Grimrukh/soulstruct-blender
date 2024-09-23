from __future__ import annotations

__all__ = [
    "ImportTextures",
    "batch_get_tpf_texture_png_data",
    "batch_get_tpf_texture_tga_data",
]

import logging
import re
import tempfile
import typing as tp
from pathlib import Path

import bpy
from io_soulstruct.utilities.operators import LoggingImportOperator
from soulstruct.base.textures.dds import DDS
from soulstruct.base.textures.texconv import texconv
from soulstruct.containers.tpf import TPF, batch_get_tpf_texture_png_data, batch_get_tpf_texture_tga_data, TPFPlatform

from io_soulstruct.general.enums import BlenderImageFormat
from .types import *


_LOGGER = logging.getLogger(__name__)

TPF_RE = re.compile(r"(?P<stem>.*)\.tpf(?P<dcx>\.dcx)?$")
CHRTPFBHD_RE = re.compile(r"(?P<stem>.*)\.chrtpfbhd?$")  # never has DCX
AEG_STEM_RE = re.compile(r"^aeg(?P<aeg>\d\d\d)$")  # checks stem only


# NOTE: We don't need a PropertyGroup for texture import (yet).


class ImportTextures(LoggingImportOperator):
    """Import an image file from disk into Blender, converting DDS images to specified format first, and optionally
    assigning imported texture to one or more selected `Image` nodes."""
    bl_idname = "import_image.soulstruct_texture"
    bl_label = "Import Texture"
    bl_description = (
        "Import an image file (converting DDS to TGA/PNG) or all image files inside a TPF container into Blender, and "
        "optionally set it to selected shader Image Texture nodes. Does not save any files to disk"
    )

    filename_ext = ".dds"

    filter_glob: bpy.props.StringProperty(
        default="*.png;*.tif;*.tiff;*.bmp;*.jpg;*.jpeg;*.tga;*.dds;*.tpf;*.tpf.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    overwrite_existing: bpy.props.BoolProperty(
        name="Overwrite Existing",
        description="If a Blender Image with the same name already exists, replace its data with the new texture. "
                    "Otherwise, new texture will have a unique suffix",
        default=True,
    )

    image_node_assignment_mode: bpy.props.EnumProperty(
        name="Image Node Assignment Mode",
        description="How to assign the imported texture(s) to selected Image Texture nodes, if at all",
        items=[
            (
                "NONE",
                "Do Not Assign",
                "Do not assign imported textures to any Image Texture nodes",
            ),
            (
                "SIMPLE_TEXTURE",
                "Selected Nodes (All)",
                "Assign single imported texture to all selected Image Texture nodes. Will fail for multi-texture TPF",
            ),
            (
                "SMART_TEXTURE",
                "Selected Nodes (Smart)",
                "Use suffix of imported texture name to detect which of the selected Image Textures nodes to assign it "
                "to (e.g. '_n' texture assigned only to nodes named 'g_Bumpmap').",
            ),
            (
                "SMART_MATERIAL",
                "All Nodes (Smart)",
                "Use suffix of imported texture name to detect which of the selected material's Image Textures nodes "
                "to assign it to (e.g. '_n' texture assigned only to nodes named 'g_Bumpmap'). Checks ALL texture "
                "nodes in material, not just selected nodes",
            ),
        ],
        default="NONE",
    )

    smart_texture_slot: bpy.props.IntProperty(
        name="Smart Texture Group Slot",
        description="Slot of texture group to assign new textures to in one of the 'Smart' assignment modes",
        default=0,
    )

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'})

    def invoke(self, context, _event):
        """Offer Operator options with dialog."""
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):

        # TODO: Respect general image cache settings, including optional data pack.
        settings = context.scene.soulstruct_settings
        deswizzle_platform = settings.game_config.swizzle_platform

        texture_collection = DDSTextureCollection()

        for file_path in self.file_paths:

            if TPF_RE.match(file_path.name):
                texture_collection |= self.import_tpf(file_path, settings.bl_image_format, deswizzle_platform)
            elif file_path.suffix == ".dds":
                # Loose DDS file. (Must already be deswizzled and headerized.)
                try:
                    texture_collection |= self.import_dds(file_path, settings.bl_image_format)
                except Exception as ex:
                    self.warning(f"Could not import DDS file into Blender: {ex}")
            else:
                # Try native file format. File browser filter should prevent non-image files.
                try:
                    texture_collection |= self.import_native(file_path)
                except Exception as ex:
                    self.warning(f"Could not import image file '{file_path.name}' into Blender: {ex}")

        if not texture_collection:
            self.warning("No textures could be imported.")
            return {"CANCELLED"}

        if self.image_node_assignment_mode == "NONE":
            # Nothing more to do.
            return {"FINISHED"}

        try:
            material_nt = context.active_object.active_material.node_tree
        except AttributeError:
            self.warning("No active object/material node tree detected for assigning new texture(s).")
            return {"FINISHED"}

        if self.image_node_assignment_mode == "SIMPLE_TEXTURE":
            if len(texture_collection) > 1:
                self.warning(
                    "Cannot assign multiple imported textures in 'Selected Nodes (All)' mode. A single texture "
                    "must be imported and will be assigned to ALL selected Image Texture node."
                )
            sel = [node for node in material_nt.nodes if node.select and node.bl_idname == "ShaderNodeTexImage"]
            if not sel:
                self.warning("No selected Image Texture nodes for assigning new texture.")
            else:
                dds_texture = next(iter(texture_collection.values()))
                for image_node in sel:
                    image_node.image = dds_texture.image
                self.info(f"Set imported texture '{dds_texture.name}' to {len(sel)} selected Image Texture node(s).")
            return {"FINISHED"}

        # Smart assignment mode, either material-wide or among selected nodes only.

        slot_suffix = f"_{self.smart_texture_slot}"
        if self.image_node_assignment_mode == "SMART_MATERIAL":
            # Get all nodes in material.
            sel = [
                node for node in material_nt.nodes
                if node.bl_idname == "ShaderNodeTexImage" and node.name.endswith(slot_suffix)
            ]
        elif self.image_node_assignment_mode == "SMART_TEXTURE":
            # Get only selected nodes in material.
            sel = [
                node for node in material_nt.nodes
                if node.select and node.bl_idname == "ShaderNodeTexImage" and node.name.endswith(slot_suffix)
            ]
        else:
            raise ValueError(f"Invalid image node assignment mode: {self.image_node_assignment_mode}")

        if not sel:
            if self.image_node_assignment_mode == "SMART_TEXTURE":
                self.warning(
                    f"No selected Image Texture nodes with name slot {self.smart_texture_slot} (e.g. "
                    f"'ALBEDO_{self.smart_texture_slot}') for assigning new texture(s)."
                )
            else:
                self.warning(
                    f"No material Image Texture nodes with name slot {self.smart_texture_slot} (e.g. "
                    f"'ALBEDO_{self.smart_texture_slot}') for assigning new texture(s)."
                )

            return {"FINISHED"}

        # Filter sampler names to ensure only one of each sampler is present.
        sampler_texture_names = {key: "" for key in ("ALBEDO", "SPECULAR", "NORMAL", "HEIGHT", "LIGHTMAP")}

        def register_sampler_name(sampler_name: str, tex_name: str, check: tp.Callable[[str], bool]):
            if not check(tex_name):
                return False
            if sampler_texture_names[sampler_name]:
                self.warning(
                    f"Cannot smart-assign multiple '{sampler_name}' textures at once. Ignoring texture: {tex_name}"
                )
            else:
                sampler_texture_names[sampler_name] = tex_name
            return True

        for texture_name, bl_image in texture_collection.items():
            for args in (
                ("SPECULAR", texture_name, lambda name: name.endswith("_s")),
                ("NORMAL", texture_name, lambda name: name.endswith("_n")),
                ("HEIGHT", texture_name, lambda name: name.endswith("_h")),
                ("LIGHTMAP", texture_name, lambda name: "_lit_" in name),
                ("ALBEDO", texture_name, lambda name: True),  # catch-all
            ):
                if register_sampler_name(*args):
                    break  # found a match

        # NOTE: It's not possible for NO texture to receive node homes here, because 'ALBEDO' is a catch-all.

        for image_node in sel:
            for texture_type, bl_image in sampler_texture_names.items():
                if bl_image is None:
                    continue
                if image_node.name.startswith(texture_type):
                    image_node.image = bl_image
                    break
            else:
                self.warning(
                    f"Could not assign imported texture to selected Image Texture node with unrecognized name: "
                    f"{image_node.name}"
                )

        return {"FINISHED"}

    def import_tpf(
        self,
        tpf_path: Path,
        image_format: BlenderImageFormat,
        deswizzle_platform: TPFPlatform,
    ) -> dict[str, DDSTexture]:
        tpf = TPF.from_path(tpf_path)
        if self.image_node_assignment_mode == "SIMPLE_TEXTURE" and len(tpf.textures) > 1:
            self.info(
                f"Cannot import multi-texture TPF in 'Selected Nodes (All)' assignment mode: {tpf_path}"
            )
            return {}

        if image_format == BlenderImageFormat.TARGA:
            textures_image_data = batch_get_tpf_texture_tga_data(tpf.textures, deswizzle_platform)
        elif image_format == BlenderImageFormat.PNG:
            textures_image_data = batch_get_tpf_texture_png_data(tpf.textures, deswizzle_platform, fmt="rgba")
        else:
            raise ValueError(f"Unsupported image format: {image_format}")
        self.info(f"Loaded {len(textures_image_data)} texture(s) from TPF: {tpf_path.name}")

        texture_images = {}
        for texture, image_data in zip(tpf.textures, textures_image_data):
            if image_data is None:
                continue  # failed to convert this texture
            try:
                bl_image = DDSTexture.new_from_image_data(
                    self, texture.stem.lower(), image_format, image_data, replace_existing=self.overwrite_existing
                )
            except Exception as ex:
                self.warning(f"Could not create Blender image from TPF texture '{texture.stem}': {ex}")
                continue
            texture_images[texture.stem.lower()] = bl_image

        return texture_images

    def import_dds(
        self,
        dds_path: Path,
        image_format: BlenderImageFormat,
    ) -> dict[str, DDSTexture]:
        """NOTE: Written DDS must already be deswizzled and headerized."""
        with tempfile.TemporaryDirectory() as temp_dir:

            # Check DDS format for logging.
            dds = DDS.from_path(dds_path)
            dds_format = dds.texconv_format

            temp_dds_path = Path(temp_dir, dds_path.name)
            temp_dds_path.write_bytes(dds_path.read_bytes())  # write temporary DDS copy
            if image_format == BlenderImageFormat.TARGA:
                texconv_result = texconv("-o", temp_dir, "-ft", "tga", "-f", "RGBA", "-nologo", temp_dds_path)
            elif image_format == BlenderImageFormat.PNG:
                texconv_result = texconv("-o", temp_dir, "-ft", "png", "-f", "RGBA", "-nologo", temp_dds_path)
            else:
                raise ValueError(f"Unsupported image format: {image_format}")

            image_name = f"{dds_path.stem}{image_format.get_suffix()}".lower()  # Blender Image names kept lower-case
            image_path = Path(temp_dir, dds_path.with_name(image_name))
            if image_path.is_file():
                bl_image = bpy.data.images.load(str(image_path))
                bl_image.pack()  # embed image in `.blend` file
                self.info(f"Loaded '{dds_format}' DDS file as {image_format.name}: {dds_path.name}")
                dds_texture = DDSTexture(bl_image)
                return {image_path.stem: dds_texture}

            # Conversion failed.
            stdout = texconv_result.stdout.decode()
            self.warning(f"Could not convert texture DDS to {image_format.name}:\n    {stdout}")
            return {}

    def import_native(self, image_path: Path) -> dict[str, bpy.types.Image]:
        """Import a non-DDS image file (assumes general Blender support).

        Does NOT pack image data into '.blend' file, unlike DDS/TPF imports.
        """
        try:
            if not self.overwrite_existing:
                # Go straight to creation below.
                raise KeyError
            bl_image = bpy.data.images[image_path.name.lower()]
        except KeyError:
            bl_image = bpy.data.images.load(str(image_path))
            # NOT packed into `.blend` file.
        else:
            if bl_image.packed_file:
                bl_image.unpack(method="USE_ORIGINAL")
            bl_image.filepath = str(image_path)  # should update format automatically
            bl_image.reload()
            # NOT packed into `.blend` file.
            self.info(f"Loaded image texture file: {image_path.name}")
        return {image_path.stem: DDSTexture(bl_image)}
