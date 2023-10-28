from __future__ import annotations

__all__ = [
    "ImportDDS",
    "ExportTexturesIntoBinder",
]

import tempfile
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper

from soulstruct.base.textures.dds import texconv
from soulstruct.containers import TPF

from io_soulstruct.utilities.operators import LoggingOperator
from .utilities import *


class ImportDDS(LoggingOperator, ImportHelper):
    """Import a DDS file (as a PNG) into a selected `Image` node."""
    bl_idname = "import_image.dds"
    bl_label = "Import DDS"
    bl_description = (
        "Import a DDS texture or single-DDS TPF binder as a PNG image, and optionally set it to all selected Image "
        "Texture nodes (does not save the PNG)"
    )

    filename_ext = ".dds"

    filter_glob: bpy.props.StringProperty(
        default="*.dds;*.tpf;*.tpf.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    set_to_selected_image_nodes: bpy.props.BoolProperty(
        name="Set to Selected Image Node(s)",
        description="Set loaded PNG texture to any selected Image nodes",
        default=True,
    )

    files: bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    directory: bpy.props.StringProperty(
        options={'HIDDEN'},
    )

    # TODO: Option to replace Blender Image with same name, if present.

    def execute(self, context):
        print("Executing DDS import...")

        file_paths = [Path(self.directory, file.name) for file in self.files]

        for file_path in file_paths:

            if TPF_RE.match(file_path.name):
                tpf = TPF.from_path(file_path)
                if len(tpf.textures) > 1:
                    # TODO: Could load all and assign to multiple selected Image Texture nodes if names match?
                    return self.error(f"Cannot import TPF file containing more than one texture: {file_path}")

                bl_image = load_tpf_texture_as_png(tpf.textures[0])
                self.info(f"Loaded DDS file from TPF as PNG: {file_path.name}")
            else:
                # Loose DDS file.
                with tempfile.TemporaryDirectory() as png_dir:
                    temp_dds_path = Path(png_dir, file_path.name)
                    temp_dds_path.write_bytes(file_path.read_bytes())  # copy
                    texconv_result = texconv("-o", png_dir, "-ft", "png", "-f", "RGBA", temp_dds_path)
                    png_path = Path(png_dir, file_path.with_suffix(".png"))
                    if png_path.is_file():
                        bl_image = bpy.data.images.load(str(png_path))
                        bl_image.pack()  # embed PNG in `.blend` file
                        self.info(f"Loaded DDS file as PNG: {file_path.name}")
                    else:
                        stdout = "\n    ".join(texconv_result.stdout.decode().split("\r\n")[3:])  # drop copyright lines
                        return self.error(f"Could not convert texture DDS to PNG:\n    {stdout}")

            # TODO: Option to iterate over ALL materials in .blend and replace a given named image with this new one.
            if self.set_to_selected_image_nodes:
                try:
                    material_nt = context.active_object.active_material.node_tree
                except AttributeError:
                    self.warning("No active object/material node tree detected to set texture to.")
                else:
                    sel = [node for node in material_nt.nodes if node.select and node.bl_idname == "ShaderNodeTexImage"]
                    if not sel:
                        self.warning("No selected Image Texture nodes to set texture to.")
                    else:
                        for image_node in sel:
                            image_node.image = bl_image
                            self.info("Set imported DDS (PNG) texture to Image Texture node.")

        return {"FINISHED"}


class ExportTexturesIntoBinder(LoggingOperator, ImportHelper):
    bl_idname = "export_image.texture_binder"
    bl_label = "Export Textures Into Binder"
    bl_description = (
        "Export image textures from selected Image Texture node(s) into a FromSoftware TPF or TPF-containing Binder "
        "(BND/BHD)"
    )

    # ImportHelper mixin class uses this
    filename_ext = ".chrbnd"

    filter_glob: bpy.props.StringProperty(
        default="*.tpf;*.tpf.dcx;*.tpfbhd;*.chrbnd;*.chrbnd.dcx;*.objbnd;*.objbnd.dcx;*.partsbnd;*.partsbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    new_texture_stem: bpy.props.StringProperty(
        name="New Texture Name",
        description="Name (without extensions) of texture to be exported (defaults to Blender image name)",
        default="",
    )

    texture_stem_to_replace: bpy.props.StringProperty(
        name="Texture Name to Replace",
        description="Name (without extensions) of texture in binder to replace (defaults to 'New Texture Name')",
        default="",
    )

    rename_tpf_containers: bpy.props.BoolProperty(
        name="Rename TPF Containers",
        description="Also change name of texture's TPF container if its old name matches 'Texture Name to Replace'",
        default=True,
    )

    new_mipmap_count: bpy.props.IntProperty(
        name="New Mipmap Count",
        description="Number of mipmaps to generate for each texture (-1 = same as replaced file, 0 = all mipmaps)",
        default=-1,
        min=-1,
    )

    files: bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    directory: bpy.props.StringProperty(
        options={'HIDDEN'},
    )

    # TODO: Option: if texture name is changed, update that texture path in FLVER (in Binder and custom Blender prop).

    @classmethod
    def poll(cls, context):
        try:
            # TODO: What if you just want to export an image from the Image Viewer? Different operator?
            sel_tex_nodes = [
                node for node in context.active_object.active_material.node_tree.nodes
                if node.select and node.bl_idname == "ShaderNodeTexImage"
            ]
            return bool(sel_tex_nodes)
        except (AttributeError, IndexError):
            return False

    def execute(self, context):
        self.info("Executing texture export...")

        # TODO: Should this operator really support export to multiple binders simultaneously (and they'd have to be in
        #  the same folder)?
        file_paths = [Path(self.directory, file.name) for file in self.files]

        sel_tex_nodes = [
            node for node in context.active_object.active_material.node_tree.nodes
            if node.select and node.bl_idname == "ShaderNodeTexImage"
        ]
        if not sel_tex_nodes:
            return self.error("No Image Texture material node selected.")
        if len(sel_tex_nodes) > 1 and self.replace_texture_name:
            return self.error("Cannot override 'Replace Texture Name' when exporting multiple textures.")

        texture_export_infos = {}  # type: dict[Path, TextureExportInfo]
        for file_path in file_paths:
            try:
                texture_export_infos[file_path] = get_texture_export_info(str(file_path))
            except Exception as ex:
                return self.error(str(ex))

        replaced_texture_export_info = None
        for tex_node in sel_tex_nodes:
            bl_image = tex_node.image
            if not bl_image:
                self.warning("Ignoring Image Texture node with no image assigned.")
                continue

            image_stem = Path(bl_image.name).stem
            new_texture_stem = self.new_texture_stem if self.new_texture_stem else image_stem

            if self.texture_stem_to_replace:  # will only be allowed if one Image Texture is being exported
                texture_name_to_replace = Path(self.texture_stem_to_replace).stem
            else:
                texture_name_to_replace = new_texture_stem

            for file_path, texture_export_info in texture_export_infos.items():
                image_exported, dds_format = texture_export_info.inject_texture(
                    bl_image,
                    new_name=new_texture_stem,
                    name_to_replace=texture_name_to_replace,
                    rename_tpf=self.rename_tpf_containers,
                )
                if image_exported:
                    self.info(
                        f"Exported '{bl_image.name}' into '{self.filepath}', replacing texture "
                        f"'{texture_name_to_replace}', with name '{new_texture_stem}' and DDS format {dds_format}."
                    )
                    replaced_texture_export_info = texture_export_info
                    break  # do not search other file paths
                else:
                    self.info(
                        f"Could not find any TPF textures to replace with Blender image "
                        f"in {file_path.name}: '{image_stem}'"
                    )
            else:
                self.warning(
                    f"Could not find any TPF textures to replace with Blender image in ANY files: '{image_stem}'"
                )

        if replaced_texture_export_info:
            # TPFs have all been updated. Now pack modified ones back to their Binders.
            try:
                write_msg = replaced_texture_export_info.write_files()
            except Exception as ex:
                return self.error(str(ex))
            self.info(write_msg)
        return {"FINISHED"}
