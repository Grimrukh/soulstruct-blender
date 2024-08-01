from __future__ import annotations

__all__ = [
    "DDSTexture",
    "DDSTextureCollection",
]

import tempfile
import typing as tp
from pathlib import Path

import bpy
from soulstruct.containers import Binder, BinderEntry
from soulstruct.containers.tpf import TPF, TPFTexture, TPFPlatform, TextureType
from soulstruct.darksouls1r.maps.map_area_texture_manager import MapAreaTextureManager
from soulstruct.dcx import DCXType
from soulstruct.base.textures import *

from io_soulstruct.exceptions import UnsupportedGameError, SoulstructTypeError, TextureExportError
from io_soulstruct.utilities import *
from .enums import *
from .properties import *


class DDSTexture:
    """Wraps `bpy.types.Image` and saves required properties for exporting it back to DDS."""

    # Enum used in `TPFTexture`, which is unfortunately not the same as `DDS` itself.
    # Defaults to 1. Not required by every game, but definitely required in DSR.
    TPF_TEXTURE_FORMATS: tp.ClassVar[str, int] = {
        "DXT1": 1,
        "BC5_UNORM": 36,
        "BC7_UNORM": 38,
    }

    image: bpy.types.Image

    def __init__(self, image: bpy.types.Image):
        # TODO: Could there be real game textures that are 1 pixel?
        if len(image.pixels) <= 4:
            raise SoulstructTypeError(
                f"Blender image '{self.name}' contains one or less pixels. Cannot use as DDS Texture.")
        self.image = image

    @property
    def texture_properties(self) -> DDSTextureProps:
        return self.image.DDS_TEXTURE

    @property
    def dds_format(self) -> BlenderDDSFormat:
        return BlenderDDSFormat[self.texture_properties.dds_format]

    @dds_format.setter
    def dds_format(self, value: BlenderDDSFormat | str):
        self.texture_properties.dds_format = str(value)

    @property
    def tpf_platform(self) -> TPFPlatform:
        return self.texture_properties.tpf_platform

    @tpf_platform.setter
    def tpf_platform(self, value: TPFPlatform):
        self.texture_properties.tpf_platform = value

    @property
    def mipmap_count(self) -> int:
        return self.texture_properties.mipmap_count

    @mipmap_count.setter
    def mipmap_count(self, value: int):
        if value < 0:
            raise ValueError("Mipmap count cannot be negative.")
        self.texture_properties.mipmap_count = value

    @property
    def name(self) -> str:
        return self.image.name

    @name.setter
    def name(self, value: str):
        self.image.name = value

    @property
    def stem(self) -> str:
        return Path(self.image.name).stem

    @stem.setter
    def stem(self, value: str):
        self.image.name = value + Path(self.image.name).suffix

    @property
    def pixels(self) -> list[float]:
        return self.image.pixels

    @pixels.setter
    def pixels(self, value: list[float]):
        # TODO: Might be read-only?
        self.image.pixels = value

    @classmethod
    def new_from_image_path(
        cls,
        image_path: Path | str,
        pack_image_data=False,
    ) -> DDSTexture:
        """Load Blender Image from image path, and optionally pack image data into Blend file.

        Image can be any supported Blender format.
        """
        bl_image = bpy.data.images.load(str(image_path))
        if pack_image_data:
            bl_image.pack()  # embed Image data into Blend file
        return cls(bl_image)

    @classmethod
    def new_from_image_data(
        cls,
        operator: LoggingOperator,
        name: str,
        image_format: str,
        image_data: bytes,
        image_cache_directory: Path = None,
        replace_existing=False,
        pack_image_data=False,
    ) -> DDSTexture:
        """Import PNG data into Blender as an Image, optionally replacing an existing image with the same name.

        If `pack_image_data` is True and `image_cache_directory` is given, the PNG data will be embedded in the `.blend`
        file. Otherwise, it will be linked to the original PNG file.
        """
        image_name = f"{name}.{image_format.lower()}"
        if image_cache_directory is None:
            # Use a temporarily file.
            write_image_path = Path(f"~/AppData/Local/Temp/{image_name}").expanduser()
            is_temp_image = True
            if not pack_image_data:
                operator.warning(
                    "Must pack image data into Blender file when `image_cache_directory` is not given ('Write Cached "
                    "Images' disabled)."
                )
        else:
            write_image_path = image_cache_directory / image_name
            is_temp_image = False

        write_image_path.write_bytes(image_data)

        try:
            if not replace_existing:
                # Go straight to creation below.
                raise KeyError
            image = bpy.data.images[name]
        except KeyError:
            image = bpy.data.images.load(str(write_image_path))
            if is_temp_image or pack_image_data:
                image.pack()  # embed PNG in Blend file
        else:
            if image.packed_file:
                image.unpack(method="USE_ORIGINAL")
            image.filepath_raw = str(write_image_path)
            image.file_format = image_format
            image.source = "FILE"
            image.reload()
            if is_temp_image or pack_image_data:
                image.pack()  # embed new PNG in Blend file

        if is_temp_image:
            write_image_path.unlink(missing_ok=True)

        bl_image = cls(image)
        bl_image.dds_format = BlenderDDSFormat.SAME

        return bl_image

    def get_dds_format_str(self, find_same_format: tp.Callable[[str], str]) -> str:
        if self.dds_format == BlenderDDSFormat.NONE:
            raise TextureExportError(f"Blender image '{self.name}' has DDS format set to 'NONE'. Cannot get format.")
        if self.dds_format == BlenderDDSFormat.SAME:
            if not find_same_format:
                raise TextureExportError(
                    f"Blender image '{self.name}' has DDS format set to 'SAME', but no 'find_same_format' function was "
                    f"provided to resolve it."
                )
            return find_same_format(self.stem)
        return self.dds_format

    def to_dds_data(
        self,
        operator: LoggingOperator,
        find_same_format: tp.Callable[[str], str] = None,
    ) -> tuple[bytes, str]:
        """Export `bl_image` (generally as a PNG), convert it to a DDS with `texconv`, and return DDS data.

        Cannot export 'TYPELESS' DDS formats. If `mipmap_count` is left as 0, `texconv` will generate a full mipmap
        chain with `texconv`.

        Returns data and actual DDS format string used.
        """
        dds_format = self.get_dds_format_str(find_same_format)

        if len(self.pixels) <= 4:
            raise TextureExportError(
                f"Blender image '{self.name}' contains one or less pixels. Cannot export it."
            )

        temp_image_path = Path(f"~/AppData/Local/Temp/temp.{self.image.file_format.lower()}").expanduser()
        self.image.filepath_raw = temp_image_path
        self.image.save()  # TODO: sometimes fails with 'No error' (depending on how Blender is storing image data?)
        with tempfile.TemporaryDirectory() as output_dir:
            is_dx10 = self.dds_format[:3] in {"BC5", "BC7"}
            texconv_config = TexconvConfig(output_dir, dds_format, is_dx10, self.mipmap_count, temp_image_path)
            try:
                data = texconv_to_dds(texconv_config)
                if data is None:
                    raise TexconvError("Texconv file not generated.")
            except TexconvError as ex:
                operator.error(f"Could not convert texture '{self.name}' to DDS with format {dds_format}. Error: {ex}")

        return data, dds_format

    def to_tpf_texture(self, operator: LoggingOperator, find_same_format: tp.Callable[[str], str] = None) -> TPFTexture:
        data, dds_format = self.to_dds_data(operator, find_same_format)
        if data is None:
            raise TextureExportError(f"Could not convert texture '{self.name}' to DDS with format {dds_format}.")
        return TPFTexture(name=self.stem, data=data, format=self.TPF_TEXTURE_FORMATS.get(dds_format, 1))

    def to_single_texture_tpf(
        self,
        operator: LoggingOperator,
        dcx_type: DCXType,
        find_same_format: tp.Callable[[str], str] = None,
    ) -> TPF:
        tpf_texture = self.to_tpf_texture(operator, find_same_format)
        return TPF(
            textures=[tpf_texture],
            platform=self.tpf_platform,
            encoding_type=2,
            tpf_flags=3,
            path=dcx_type.process_path(f"{self.stem}.tpf"),
            dcx_type=dcx_type,
        )


class DDSTextureCollection(dict[str, DDSTexture]):
    """Collection of `DDSTexture`s that behaves like a dictionary mapping stems (NOT full names) to `DDSTexture`s."""

    def add(self, texture: DDSTexture):
        self[texture.stem] = texture

    def get_sorted_textures(self) -> list[DDSTexture]:
        images = list(self.values())
        images.sort(key=lambda i: i.stem)
        return images

    def to_dds_data_batch(
        self,
        operator: LoggingOperator,
        find_same_format: tp.Callable[[str], str] = None,
    ) -> list[tuple[DDSTexture, bytes, str]]:
        """Batch convert all textures in this collection to DDS format using `texconv`.

        Returns DDS data and actual DDS format used.
        """

        dds_formats = []
        configs = []  # type: list[TexconvConfig]

        textures = self.get_sorted_textures()

        with tempfile.TemporaryDirectory() as input_dir:
            with tempfile.TemporaryDirectory() as output_dir:
                for texture in textures:
                    dds_format = texture.get_dds_format_str(find_same_format)
                    if len(texture.pixels) <= 4:
                        # Shouldn't be possible by `DDSTexture` initialization, but Image may be modified after that...
                        raise TextureExportError(
                            f"Blender image '{texture.name}' contains one or less pixels. Cannot export it."
                        )
                    temp_image_path = Path(input_dir, texture.image.name)
                    texture.image.filepath_raw = str(temp_image_path)
                    texture.image.save()  # TODO: sometimes fails with 'No error'?
                    is_dx10 = texture.dds_format[:3] in {"BC5", "BC7"}
                    texconv_config = TexconvConfig(
                        output_dir, dds_format, is_dx10, texture.mipmap_count, temp_image_path
                    )

                    dds_formats.append(dds_format)
                    configs.append(texconv_config)

                dds_data_list = batch_texconv_to_dds(configs)

        data_formats = []
        for dds_texture, dds_data, dds_format in zip(textures, dds_data_list, dds_formats):
            if dds_data is None:
                operator.error(f"Could not convert texture '{dds_texture.name}' to DDS with format '{dds_format}'.")
            data_formats.append((dds_texture, dds_data, dds_format))

        return data_formats

    def to_multi_texture_tpf(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        enforce_max_chrbnd_tpf_size=False,
        find_same_format: tp.Callable[[str], str] = None,
    ) -> TPF | None:
        """Combine all given Blender images as DDS files in one TPF. Generally only used for TPFs inside CHRBNDs or
        OBJBNDs.

        If `enforce_max_chrbnd_tpf_size` is True, and the combined texture size is larger than `max_chrbnd_tpf_size` in
        texture export settings, then `None` will be returned, which should prompt the caller to create a CHRTPFBHD
        Binder instead (header file inside CHRBND, data file next to it).
        """
        if not self:
            raise TextureExportError("No DDSTextures in collection to combine into TPF.")

        settings = context.scene.texture_export_settings

        dds_data_batch = self.to_dds_data_batch(operator, find_same_format)
        tpf_textures = []
        tpf_platform = None

        if enforce_max_chrbnd_tpf_size:
            total_dds_size = 0
            for _, dds_data, _ in dds_data_batch:
                if dds_data:
                    total_dds_size += len(dds_data)
            if 0 < settings.max_chrbnd_tpf_size < total_dds_size // 1000:  # kB
                # Too much data for one multi-texture TPF. (Caller will likely create a split TPFBHD.)
                return None

        for dds_texture, dds_data, dds_format in dds_data_batch:
            if dds_data is None:
                continue

            if tpf_platform is not None:
                if dds_texture.tpf_platform != tpf_platform:
                    operator.warning(
                        f"DDSTexture collection contains textures with different TPF platforms. Multi-texture TPF "
                        f"will use first: {tpf_platform}"
                    )
            else:
                tpf_platform = dds_texture.tpf_platform

            tpf_textures.append(
                TPFTexture(
                    name=dds_texture.stem,
                    data=dds_data,
                    format=DDSTexture.TPF_TEXTURE_FORMATS.get(dds_format, 1),
                )
            )

        if not tpf_textures:
            raise TextureExportError("No DDS textures were successfully converted to DDS data for multi-texture TPF.")

        return TPF(
            textures=tpf_textures,
            platform=tpf_platform,
            encoding_type=2,
            tpf_flags=3,
        )

    def to_single_texture_tpfs(
        self,
        operator: LoggingOperator,
        tpf_dcx_type: DCXType,
        find_same_format: tp.Callable[[str], str] = None,
    ) -> list[TPF | None]:
        """Put each DDS texture into its own TPF and return them all.

        Used for, e.g., 'overflow' CHRBND textures in DS1: PTDE when they do not fit into a single multi-texture CHRBND
        TPF. Note that we don't just call `DDSTexture.to_single_texture_tpf()`, since we can batch DDS conversion here.

        Any DDS conversion failures will place `None` into returned list rather than a `TPF`.
        """
        if not self:
            raise TextureExportError("No DDSTextures in collection to export to TPFs.")

        dds_data_batch = self.to_dds_data_batch(operator, find_same_format)
        tpfs = []

        for dds_texture, dds_data, dds_format in dds_data_batch:
            if dds_data is None:
                # Error already reported.
                tpfs.append(None)
                continue

            # Create single-texture TPF.
            texture = TPFTexture(
                name=dds_texture.stem,
                data=dds_data,
                format=DDSTexture.TPF_TEXTURE_FORMATS.get(dds_format, 1),
            )
            tpf = TPF(
                textures=[texture],
                platform=dds_texture.tpf_platform,
                encoding_type=2,
                tpf_flags=3,
                path=tpf_dcx_type.process_path(f"{dds_texture.stem}.tpf"),
                dcx_type=tpf_dcx_type,
            )
            tpfs.append(tpf)

        # We don't need to check if `tpfs` is empty. Caller may be fine with that.

        return tpfs

    def to_tpfbhd(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        tpf_dcx_type: DCXType,
        entry_path_parent: str = "",
        find_same_format: tp.Callable[[str], str] = None,
    ) -> Binder:
        """Put each DDS texture into its own TPF in a new TPFBHD split binder.

        Commonly used for CHRBNDs with too many textures to fit in one TPF (though that limit doesn't seem
        well-defined). In this case, the BDT data part of the split Binder is generally written next to the CHRBND as a
        `CHRTPFBDT` file, and the header is left inside the CHRBND as a `CHRTPFBHD` file.

        If given, `entry_path_parent` should end in an escaped backslash. However, it's not necessary inside TPFBHDs.
        """
        if not self:
            raise TextureExportError("No images given to combine into TPFBHD.")

        if entry_path_parent and entry_path_parent[-1] != "\\":
            entry_path_parent += "\\"

        settings = operator.settings(context)
        if settings.is_game("DARK_SOULS_PTDE", "DARK_SOULS_DSR"):
            tpfbxf = Binder.empty_bxf3()
        else:
            raise UnsupportedGameError(f"Cannot yet export TPFBHDs for game {settings.game.name}.")

        tpfs = self.to_single_texture_tpfs(operator, tpf_dcx_type, find_same_format)

        entry_id = 0  # only incremented for successful TPFs
        for dds_texture, tpf in zip(self.get_sorted_textures(), tpfs):
            if tpf is None:
                # Error already reported.
                continue

            # Add TPF to TPFBHD.
            tpf_entry = BinderEntry(
                data=bytes(tpf),
                entry_id=entry_id,
                path=f"{entry_path_parent}{dds_texture.stem}.tpf",
                flags=0x2,
            )
            tpfbxf.add_entry(tpf_entry)
            entry_id += 1

        if entry_id == 0:
            raise TextureExportError("No textures were successfully exported to TPFs for TPFBHD.")

        return tpfbxf

    def into_map_area_tpfbhds(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_area_dir: Path,
    ) -> list[Binder]:
        """Load all entries from all TPFBHDs in `map_area_dir`, export given `images` into them as single-DDS TPFs,
        re-alphabetize the entries, split them into new TPFBHDs (enforcing maximum file-per-BHD limit), and return them
        for the caller to save.

        Does NOT save the TPFBHDs, to be consistent with the single-TPF and single-TPFBHD exporters above. Caller must
        do that.
        """
        settings = operator.settings(context)
        if not settings.is_game("DARK_SOULS_DSR"):
            raise UnsupportedGameError(f"Cannot yet export map area TPFBHDs for game {settings.game.name}.")

        map_directory = map_area_dir.parent  # game 'map' folder
        map_area = map_area_dir.name
        area_id = int(map_area[1:3])
        manager = MapAreaTextureManager.from_existing_area_directory(map_directory, area_id)

        overwrite = context.scene.texture_export_settings.overwrite_existing_map_textures
        textures = self.get_sorted_textures()

        def find_same_format(_stem: str) -> BlenderDDSFormat:
            try:
                existing_entry = manager[_stem]
            except KeyError:
                raise KeyError(f"Texture '{stem}' not found in map area TPFBHDs. Cannot detect 'SAME' DDS format.")
            existing_tpf = TPF.from_binder_entry(existing_entry)
            existing_dds = existing_tpf.textures[0].get_dds()
            _format = existing_dds.texconv_format
            if _format == "BC5U":
                _format = "BC5_UNORM"
            if "TYPELESS" in _format:
                _format = _format.replace("TYPELESS", "UNORM")
                operator.warning(f"Cannot export 'TYPELESS' DDS format. Changing to '{_format}'.")
            return BlenderDDSFormat[_format]

        for dds_texture in textures:

            if dds_texture.dds_format == BlenderDDSFormat.NONE:
                raise TextureExportError(f"Cannot export texture '{dds_texture.stem}' with format 'NONE'.")
            if dds_texture.dds_format == BlenderDDSFormat.SAME:
                # Check now if we can find an existing texture with the same name to determine the format. Otherwise,
                # we know it will fail during batch DDS conversion.
                if dds_texture.stem not in manager.tpfbhd_entries:
                    raise ValueError(
                        f"Cannot export texture '{dds_texture.stem}' with format 'SAME' because a texture with that "
                        f"name does not already exist in map area TPFBHDs."
                    )

        # Convert images to DDS.
        operator.info(f"Converting {len(self)} Blender Images to DDS textures for map area {map_area}...")
        dds_data_batch = self.to_dds_data_batch(operator, find_same_format)

        # Export into found/new entries.
        success_count = 0
        for dds_texture, dds_data, dds_format in dds_data_batch:
            if not dds_data:
                # Conversion of this texture failed. (Error already reported.)
                continue
            success_count += 1

            stem = dds_texture.stem
            operator.info(f"Converted texture {stem} to DDS (format {dds_format}).")
            # Create single-texture TPF.
            tpf_texture = TPFTexture(
                name=stem,
                data=dds_data,
                format=DDSTexture.TPF_TEXTURE_FORMATS.get(dds_format, 1),
                texture_type=TextureType.Texture,
            )
            manager.add_tpfbhd_texture(tpf_texture, overwrite=overwrite)

        tpfbhds = manager.get_tpfbhds()
        operator.info(f"Exported {success_count} textures to {len(tpfbhds)} TPFBHDs in map area {map_area}.")

        return tpfbhds
