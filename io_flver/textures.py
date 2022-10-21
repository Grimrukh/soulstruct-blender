__all__ = [
    "load_tpf_texture_as_png",
    "export_image_into_tpf_texture",
]

import os
import tempfile
from pathlib import Path

from soulstruct.base.textures.dds import texconv
from soulstruct.containers.tpf import TPFTexture

import bpy


def load_tpf_texture_as_png(tpf_texture: TPFTexture):
    png_data = tpf_texture.get_png_data()
    temp_png_path = Path(f"~/AppData/Local/Temp/{Path(tpf_texture.name).stem}.png").expanduser()
    temp_png_path.write_bytes(png_data)
    bl_image = bpy.data.images.load(str(temp_png_path))
    bl_image.pack()  # embed PNG in `.blend` file
    if temp_png_path.is_file():
        os.remove(temp_png_path)
    return bl_image


def export_image_into_tpf_texture(bl_image, replace_in_tpf_texture: TPFTexture, dds_format: str = None) -> (bytes, str):
    if dds_format is None:
        dds_format = replace_in_tpf_texture.get_dds().texconv_format

    if "TYPELESS" in dds_format:
        old_dds_format = dds_format
        dds_format = old_dds_format.replace("TYPELESS", "UNORM")
        print(f"# INFO: Changing DDS format '{old_dds_format}' to '{dds_format}' for conversion.")

    temp_image_path = Path(f"~/AppData/Local/Temp/temp.png").expanduser()
    bl_image.filepath_raw = str(temp_image_path)
    bl_image.save()
    with tempfile.TemporaryDirectory() as output_dir:
        texconv_result = texconv("-o", output_dir, "-ft", "dds", "-f", dds_format, temp_image_path)
        try:
            dds_data = Path(output_dir, "temp.dds").read_bytes()
        except FileNotFoundError:
            stdout = "\n    ".join(texconv_result.stdout.decode().split("\r\n")[3:])  # drop copyright lines
            raise ValueError(f"Could not convert texture to DDS with format {dds_format}:\n    {stdout}")

    if replace_in_tpf_texture:
        replace_in_tpf_texture.data = dds_data
    return dds_data, dds_format
