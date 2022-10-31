from __future__ import annotations

__all__ = [
    "TPF_RE",
    "TextureExportException",
    "SingleTPFTextureExport",
    "BinderTPFTextureExport",
    "SplitBinderTPFTextureExport",
    "get_texture_export_info",
    "load_tpf_texture_as_png",
    "export_image_into_tpf_texture",
]

import abc
import os
import re
import tempfile
from pathlib import Path

from soulstruct.base.textures.dds import texconv
from soulstruct.containers import Binder
from soulstruct.containers.base import BaseBinder, BinderEntry
from soulstruct.containers.bxf import BaseBXF
from soulstruct.containers.tpf import TPF, TPFTexture

import bpy

TPF_RE = re.compile(rf"^(.*)\.tpf(\.dcx)?$")
CHRBND_RE = re.compile(rf"^(.*)\.chrbnd(\.dcx)?$")


class TextureExportException(Exception):
    """Exception raised while trying to export a texture."""


class TextureExportInfo(abc.ABC):
    """Base class for info objects returned by texture import preparer below."""

    @abc.abstractmethod
    def inject_texture(
        self,
        bl_image,
        image_stem: str,
        repl_name: str,
        rename_tpf: bool,
    ) -> tuple[bool, str]:
        """Inject a Blender image object into TPF. Returns True if texture was exported and the format of the DDS."""
        ...

    @abc.abstractmethod
    def write_files(self) -> str:
        ...


class SingleTPFTextureExport(TextureExportInfo):

    loose_tpf: TPF
    modified: bool
    new_file_name: str

    def __init__(self, file_path: Path):
        self.modified = False
        self.new_file_name = ""
        try:
            self.loose_tpf = TPF(file_path)
        except Exception as ex:
            raise TextureExportException(f"Could not load TPF file. Error: {ex}")

    def inject_texture(
        self,
        bl_image,
        image_stem: str,
        repl_name: str,
        rename_tpf: bool,
    ) -> tuple[bool, str]:
        for texture in self.loose_tpf.textures:
            if texture.name == repl_name:
                # Replace this texture.
                try:
                    _, dds_format = export_image_into_tpf_texture(bl_image, replace_in_tpf_texture=texture)
                except ValueError as ex:
                    raise TextureExportException(f"Could not export image texture '{bl_image.name}'. Error: {ex}")
                texture.name = image_stem
                self.modified = True

                if rename_tpf:
                    # Check if we should also rename this TPF.
                    if self.tpf_name == f"{image_stem}.tpf":
                        self.new_file_name = f"{image_stem}.tpf"
                    elif self.tpf_name == f"{image_stem}.tpf.dcx":
                        self.new_file_name = f"{image_stem}.tpf.dcx"

                return True, dds_format

        return False, ""

    def write_files(self) -> str:
        if self.modified:
            # Just re-write TPF.
            if self.new_file_name:
                self.loose_tpf.path = self.loose_tpf.path.parent / self.new_file_name
            self.loose_tpf.write()
            return f"Wrote modified TPF: {self.loose_tpf.path}"
        return ""

    @property
    def tpf_name(self):
        return self.loose_tpf.path.name


class BinderTPFTextureExport(TextureExportInfo):

    binder: BaseBinder
    binder_tpfs: dict[str, tuple[BinderEntry, TPF]]
    modified_binder_tpfs: list[TPF]

    def __init__(self, binder: BaseBinder, tpf_entries: list[BinderEntry]):
        self.binder = binder
        self.binder_tpfs = {}
        self.modified_binder_tpfs = []
        for tpf_entry in tpf_entries:
            try:
                self.binder_tpfs[tpf_entry.name] = (tpf_entry, TPF(tpf_entry))
            except Exception as ex:
                raise TextureExportException(f"Could not load TPF file '{tpf_entry.name}' in Binder. Error: {ex}")

    def inject_texture(
        self,
        bl_image,
        image_stem: str,
        repl_name: str,
        rename_tpf: bool,
    ) -> tuple[bool, str]:
        for tpf_name, (binder_tpf_entry, binder_tpf) in self.binder_tpfs.items():
            for texture in binder_tpf.textures:
                if texture.name == repl_name:
                    # Replace this texture.
                    try:
                        _, dds_format = export_image_into_tpf_texture(bl_image, replace_in_tpf_texture=texture)
                    except ValueError as ex:
                        raise TextureExportException(f"Could not export image texture '{bl_image.name}'. Error: {ex}.")
                    texture.name = image_stem
                    if binder_tpf not in self.modified_binder_tpfs:
                        self.modified_binder_tpfs.append(binder_tpf)

                    if rename_tpf:
                        # Check if we should also rename this TPF.
                        if tpf_name == f"{image_stem}.tpf":
                            binder_tpf_entry.set_path_name(f"{image_stem}.tpf")
                        elif tpf_name == f"{image_stem}.tpf.dcx":
                            binder_tpf_entry.set_path_name(f"{image_stem}.tpf.dcx")

                    return True, dds_format
        return False, ""

    def write_files(self) -> str:
        if not self.modified_binder_tpfs:
            raise TextureExportException("Could not find any textures to replace in Binder TPFs.")
        for binder_tpf_entry, binder_tpf in self.binder_tpfs.values():
            if binder_tpf in self.modified_binder_tpfs:
                binder_tpf_entry.set_uncompressed_data(binder_tpf.pack_dcx())
        self.binder.write()  # always same path
        return f"Wrote Binder with {len(self.modified_binder_tpfs)} modified TPFs."


class SplitBinderTPFTextureExport(TextureExportInfo):

    binder: BaseBinder
    chrtpfbxf: BaseBXF
    chrtpfbhd_entry: BinderEntry
    chrtpfbdt_path: Path
    bxf_tpfs: dict[str, tuple[BinderEntry, TPF]]
    modified_bxf_tpfs: list[TPF]

    def __init__(self, file_path: Path, binder: BaseBinder, chrtpfbhd_entry: BinderEntry, chrbnd_name: str):
        self.binder = binder
        chrtpfbdt_path = Path(file_path).parent / f"{chrbnd_name}.chrtpfbdt"
        if not chrtpfbdt_path.is_file():
            raise TextureExportException(f"Could not find required '{chrtpfbdt_path.name}' next to CHRBND.")
        self.chrtpfbxf = Binder(chrtpfbhd_entry, bdt_source=chrtpfbdt_path)
        bxf_tpf_entries = self.chrtpfbxf.find_entries_matching_name(TPF_RE)
        self.bxf_tpfs = {}
        self.modified_bxf_tpfs = []
        for tpf_entry in bxf_tpf_entries:
            try:
                self.bxf_tpfs[tpf_entry.name] = (tpf_entry, TPF(tpf_entry))
            except Exception as ex:
                raise TextureExportException(
                    f"Could not load TPF file '{tpf_entry.name}' in CHRTPFBHD. Error: {ex}"
                )

    def inject_texture(
        self,
        bl_image,
        image_stem: str,
        repl_name: str,
        rename_tpf: bool,
    ) -> tuple[bool, str]:
        for tpf_name, (bxf_tpf_entry, bxf_tpf) in self.bxf_tpfs.items():
            for texture in bxf_tpf.textures:
                if texture.name == repl_name:
                    # Replace this texture.
                    try:
                        _, dds_format = export_image_into_tpf_texture(bl_image, replace_in_tpf_texture=texture)
                    except ValueError as ex:
                        raise TextureExportException(f"Could not export image texture '{bl_image.name}'. Error: {ex}.")

                    texture.name = image_stem
                    if bxf_tpf not in self.modified_bxf_tpfs:
                        self.modified_bxf_tpfs.append(bxf_tpf)

                    if rename_tpf:
                        # Check if we should also rename this TPF.
                        if tpf_name == f"{image_stem}.tpf":
                            bxf_tpf_entry.set_path_name(f"{image_stem}.tpf")
                        elif tpf_name == f"{image_stem}.tpf.dcx":
                            bxf_tpf_entry.set_path_name(f"{image_stem}.tpf.dcx")

                    return True, dds_format
        return False, ""

    def write_files(self) -> str:
        if not self.modified_bxf_tpfs:
            raise TextureExportException("Could not find any textures to replace in Binder CHRBNDBHD TPFs.")
        for bxf_tpf_entry, bxf_tpf in self.bxf_tpfs.values():
            if bxf_tpf in self.modified_bxf_tpfs:
                bxf_tpf_entry.set_uncompressed_data(bxf_tpf.pack_dcx())
        self.chrtpfbxf.write_split(
            bhd_path_or_entry=self.chrtpfbhd_entry,
            bdt_path_or_entry=self.chrtpfbdt_path,
        )
        self.binder.write()  # always same path
        return (f"Wrote Binder with new CHRTPFBHD + adjacent CHRTPFBDT ({self.chrtpfbdt_path}) with {len(self.modified_binder_tpfs)} modified TPFs.")


def get_texture_export_info(file_path: str) -> TextureExportInfo:

    # 1. Export into loose TPF.
    if TPF_RE.match(file_path):
        return SingleTPFTextureExport(Path(file_path))

    try:
        binder = Binder(file_path)
    except Exception as ex:
        raise TextureExportException(f"Could not load Binder file. Error: {ex}")

    # 2. Find TPF entries in Binder (only used if CHRTPFBHD not found below).
    tpf_entries = binder.find_entries_matching_name(TPF_RE)

    # 3. Find CHRTPFBHD in Binder.
    if match := CHRBND_RE.match(file_path):
        chrbnd_name = match.group(1)
        try:
            chrtpfbhd_entry = binder[f"{chrbnd_name}.chrtpfbhd"]
        except binder.BinderEntryMissing:
            pass
        else:
            if tpf_entries:
                raise TextureExportException(f"CHRBND '{file_path}' has both loose TPFs and a CHRTPFBHD.")
            return SplitBinderTPFTextureExport(Path(file_path), binder, chrtpfbhd_entry, chrbnd_name)

    if not tpf_entries:
        raise TextureExportException("Could not find any TPFs or CHRTPFBHDs in Binder.")

    return BinderTPFTextureExport(binder, tpf_entries)


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
