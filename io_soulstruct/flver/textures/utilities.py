from __future__ import annotations

__all__ = [
    "TPF_RE",
    "TextureExportInfo",
    "TextureExportException",
    "SingleTPFTextureExport",
    "BinderTPFTextureExport",
    "SplitBinderTPFTextureExport",
    "get_texture_export_info",
    "load_tpf_texture_as_png",
    "png_to_bl_image",
    "bl_image_to_dds",
    "create_lightmap_tpf",
    "TextureManager",
]

import abc
import logging
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import bpy
from soulstruct.containers import Binder, BinderEntry, EntryNotFoundError
from soulstruct.containers.tpf import TPF, TPFTexture, TPFPlatform
from soulstruct.base.textures.dds import texconv

from io_soulstruct.utilities import MAP_STEM_RE

TPF_RE = re.compile(rf"^(?P<stem>.*)\.tpf(?P<dcx>\.dcx)?$")
CHRBND_RE = re.compile(rf"^(?P<stem>.*)\.chrbnd(?P<dcx>\.dcx)?$")
CHRTPFBHD_RE = re.compile(r"(?P<stem>.*)\.chrtpfbhd?$")  # never has DCX
AEG_STEM_RE = re.compile(r"^aeg(?P<aeg>\d\d\d)$")  # checks stem only

_LOGGER = logging.getLogger(__name__)


class TextureExportException(Exception):
    """Exception raised while trying to export a texture."""


class TextureExportInfo(abc.ABC):
    """Base class for info objects returned by texture import preparer below."""

    @abc.abstractmethod
    def inject_texture(
        self,
        bl_image,
        new_name: str,
        name_to_replace: str,
        rename_tpf: bool,
    ) -> tuple[bool, str]:
        """Inject a Blender image object into TPF. Returns True if texture was exported and the format of the DDS.

        Args:
            bl_image: Blender image object to export.
            new_name: Name to give the exported texture. Will default to the name of the Blender image.
            name_to_replace: Name of the texture in the TPF to replace. Will default to `new_name`.
            rename_tpf: If True, and if the texture's TPF container also matches `name_to_replace`, the name of the TPF
                container will also be changed to `new_name`.
        """
        ...

    @abc.abstractmethod
    def write_files(self) -> str:
        ...


class SingleTPFTextureExport(TextureExportInfo):

    loose_tpf: TPF
    modified: bool
    new_tpf_file_name: str

    def __init__(self, file_path: Path):
        self.modified = False
        self.new_tpf_file_name = ""
        try:
            self.loose_tpf = TPF.from_path(file_path)
        except Exception as ex:
            raise TextureExportException(f"Could not load TPF file. Error: {ex}")

    def inject_texture(
        self,
        bl_image,
        new_name: str,
        name_to_replace: str,
        rename_tpf: bool,
    ) -> tuple[bool, str]:
        for texture in self.loose_tpf.textures:
            if texture.name == name_to_replace:
                # Replace this texture.
                try:
                    _, dds_format = bl_image_to_dds(bl_image, replace_in_tpf_texture=texture)
                except ValueError as ex:
                    raise TextureExportException(f"Could not export image texture '{bl_image.name}'. Error: {ex}")
                texture.name = new_name
                self.modified = True

                if rename_tpf:
                    # Check if we should also rename this TPF.
                    if self.source_tpf_file_name == f"{name_to_replace}.tpf":
                        self.new_tpf_file_name = f"{new_name}.tpf"
                    elif self.source_tpf_file_name == f"{name_to_replace}.tpf.dcx":
                        self.new_tpf_file_name = f"{new_name}.tpf.dcx"

                return True, dds_format

        return False, ""

    def write_files(self) -> str:
        if self.modified:
            # Just re-write TPF.
            if self.new_tpf_file_name:
                self.loose_tpf.path = self.loose_tpf.path.parent / self.new_tpf_file_name
            self.loose_tpf.write()
            return f"Wrote modified TPF: {self.loose_tpf.path}"
        else:
            raise TextureExportException("Could not find any textures to replace in TPF.")

    @property
    def source_tpf_file_name(self):
        return self.loose_tpf.path.name


class BinderTPFTextureExport(TextureExportInfo):

    binder: Binder
    binder_tpfs: dict[str, tuple[BinderEntry, TPF]]
    modified_binder_tpfs: list[TPF]

    def __init__(self, binder: Binder, tpf_entries: list[BinderEntry]):
        self.binder = binder
        self.binder_tpfs = {}
        self.modified_binder_tpfs = []
        for tpf_entry in tpf_entries:
            try:
                self.binder_tpfs[tpf_entry.name] = (tpf_entry, tpf_entry.to_binary_file(TPF))
            except Exception as ex:
                raise TextureExportException(f"Could not load TPF file '{tpf_entry.name}' in Binder. Error: {ex}")

    def inject_texture(
        self,
        bl_image,
        new_name: str,
        name_to_replace: str,
        rename_tpf: bool,
    ) -> tuple[bool, str]:
        for tpf_name, (binder_tpf_entry, binder_tpf) in self.binder_tpfs.items():
            for texture in binder_tpf.textures:
                if texture.name == name_to_replace:
                    # Replace this texture.
                    try:
                        _, dds_format = bl_image_to_dds(bl_image, replace_in_tpf_texture=texture)
                    except ValueError as ex:
                        raise TextureExportException(f"Could not export image texture '{bl_image.name}'. Error: {ex}.")
                    texture.name = new_name
                    if binder_tpf not in self.modified_binder_tpfs:
                        self.modified_binder_tpfs.append(binder_tpf)

                    if rename_tpf:
                        # Check if we should also rename this TPF.
                        if tpf_name == f"{name_to_replace}.tpf":
                            binder_tpf_entry.set_path_name(f"{new_name}.tpf")
                        elif tpf_name == f"{name_to_replace}.tpf.dcx":
                            binder_tpf_entry.set_path_name(f"{new_name}.tpf.dcx")

                    return True, dds_format
        return False, ""

    def write_files(self) -> str:
        if not self.modified_binder_tpfs:
            raise TextureExportException("Could not find any textures to replace in Binder TPFs.")
        for binder_tpf_entry, binder_tpf in self.binder_tpfs.values():
            if binder_tpf in self.modified_binder_tpfs:
                binder_tpf_entry.set_from_binary_file(binder_tpf)
        print(self.binder.path, self.binder.is_split_bxf)
        self.binder.write()  # always same path
        return f"Wrote Binder with {len(self.modified_binder_tpfs)} modified TPFs."


class SplitBinderTPFTextureExport(TextureExportInfo):

    binder: Binder
    chrtpfbxf: Binder
    chrtpfbhd_entry: BinderEntry
    chrtpfbdt_path: Path
    bxf_tpfs: dict[str, tuple[BinderEntry, TPF]]
    modified_bxf_tpfs: list[TPF]

    def __init__(self, file_path: Path, binder: Binder, chrtpfbhd_entry: BinderEntry, chrbnd_name: str):
        self.binder = binder
        chrtpfbdt_path = Path(file_path).parent / f"{chrbnd_name}.chrtpfbdt"
        if not chrtpfbdt_path.is_file():
            raise TextureExportException(f"Could not find required '{chrtpfbdt_path.name}' next to CHRBND.")
        self.chrtpfbxf = Binder.from_bytes(chrtpfbhd_entry, bdt_data=chrtpfbdt_path.read_bytes())
        bxf_tpf_entries = self.chrtpfbxf.find_entries_matching_name(TPF_RE)
        self.bxf_tpfs = {}
        self.modified_bxf_tpfs = []
        for tpf_entry in bxf_tpf_entries:
            try:
                self.bxf_tpfs[tpf_entry.name] = (tpf_entry, tpf_entry.to_binary_file(TPF))
            except Exception as ex:
                raise TextureExportException(
                    f"Could not load TPF file '{tpf_entry.name}' in CHRTPFBHD. Error: {ex}"
                )

    def inject_texture(
        self,
        bl_image,
        new_name: str,
        name_to_replace: str,
        rename_tpf: bool,
    ) -> tuple[bool, str]:
        for tpf_name, (bxf_tpf_entry, bxf_tpf) in self.bxf_tpfs.items():
            for texture in bxf_tpf.textures:
                if texture.name == name_to_replace:
                    # Replace this texture.
                    try:
                        _, dds_format = bl_image_to_dds(bl_image, replace_in_tpf_texture=texture)
                    except ValueError as ex:
                        raise TextureExportException(f"Could not export image texture '{bl_image.name}'. Error: {ex}.")

                    texture.name = new_name
                    if bxf_tpf not in self.modified_bxf_tpfs:
                        self.modified_bxf_tpfs.append(bxf_tpf)

                    if rename_tpf:
                        # Check if we should also rename this TPF.
                        if tpf_name == f"{name_to_replace}.tpf":
                            bxf_tpf_entry.set_path_name(f"{new_name}.tpf")
                        elif tpf_name == f"{name_to_replace}.tpf.dcx":
                            bxf_tpf_entry.set_path_name(f"{new_name}.tpf.dcx")

                    return True, dds_format
        return False, ""

    def write_files(self) -> str:
        if not self.modified_bxf_tpfs:
            raise TextureExportException("Could not find any textures to replace in Binder CHRTPFBHD TPFs.")
        for bxf_tpf_entry, bxf_tpf in self.bxf_tpfs.values():
            if bxf_tpf in self.modified_bxf_tpfs:
                bxf_tpf_entry.set_from_binary_file(bxf_tpf)
        self.chrtpfbxf.write_split(
            bhd_path_or_entry=self.chrtpfbhd_entry,
            bdt_path_or_entry=self.chrtpfbdt_path,
        )
        self.binder.write()  # always same path
        return (
            f"Wrote Binder with new CHRTPFBHD + adjacent CHRTPFBDT ({self.chrtpfbdt_path}) with "
            f"{len(self.modified_bxf_tpfs)} modified TPFs."
        )


def get_texture_export_info(file_path: str) -> TextureExportInfo:

    # 1. Export into loose TPF.
    if TPF_RE.match(file_path):
        return SingleTPFTextureExport(Path(file_path))

    try:
        binder = Binder.from_path(file_path)
    except Exception as ex:
        raise TextureExportException(f"Could not load Binder file. Error: {ex}")

    # 2. Find TPF entries in Binder (only used if CHRTPFBHD not found below).
    tpf_entries = binder.find_entries_matching_name(TPF_RE)

    # 3. Find CHRTPFBHD in Binder.
    if match := CHRBND_RE.match(file_path):
        chrbnd_name = match.group(1)
        try:
            chrtpfbhd_entry = binder[f"{chrbnd_name}.chrtpfbhd"]
        except EntryNotFoundError:
            pass
        else:
            if tpf_entries:
                raise TextureExportException(f"CHRBND '{file_path}' has both loose TPFs and a CHRTPFBHD.")
            return SplitBinderTPFTextureExport(Path(file_path), binder, chrtpfbhd_entry, chrbnd_name)

    if not tpf_entries:
        raise TextureExportException("Could not find any TPFs or CHRTPFBHDs in Binder.")

    return BinderTPFTextureExport(binder, tpf_entries)


def load_tpf_texture_as_png(tpf_texture: TPFTexture):
    """TODO: No longer used in favor of multiprocessing."""
    from time import perf_counter
    start = t = perf_counter()
    png_data = tpf_texture.get_png_data()
    print(f"\n    PNG data get time for {tpf_texture.name}: {perf_counter() - t}")
    temp_png_path = Path(f"~/AppData/Local/Temp/{Path(tpf_texture.name).stem}.png").expanduser()
    temp_png_path.write_bytes(png_data)
    t = perf_counter()
    bl_image = bpy.data.images.load(str(temp_png_path))
    print(f"    Blender image load time for {temp_png_path.name}: {perf_counter() - t}")
    t = perf_counter()
    bl_image.pack()  # embed PNG in `.blend` file
    print(f"    Blender image pack time for {temp_png_path.name}: {perf_counter() - t}")
    if temp_png_path.is_file():
        os.remove(temp_png_path)
    print(f"Total time: {perf_counter() - start}")
    return bl_image


def png_to_bl_image(image_name: str, png_data: bytes, write_png_directory: Path = None):
    if write_png_directory is None:
        # Use a temporarily file.
        write_png_path = Path(f"~/AppData/Local/Temp/{image_name}.png").expanduser()
        delete_png = True
    else:
        write_png_path = write_png_directory / f"{image_name}.png"
        delete_png = False

    write_png_path.write_bytes(png_data)
    bl_image = bpy.data.images.load(str(write_png_path))
    bl_image.pack()  # embed PNG in `.blend` file
    if delete_png:
        write_png_path.unlink(missing_ok=True)
    return bl_image


def bl_image_to_dds(
    bl_image,
    replace_in_tpf_texture: TPFTexture = None,
    dds_format: str = None,
    mipmap_count=-1,
) -> tuple[bytes, str]:
    """Export `bl_image` (generally as a PNG), convert it to a DDS of `dds_format` with `texconv`.

    Automatically redirects 'TYPELESS' DDS formats to 'UNORM', which seems to work for DS1 'BC7' lightmaps at least.

    If `replace_in_tpf_texture` is given, the DDS data will be automatically assigned to it, and `dds_format` will
    default to the format currently used in that `TPFTexture`.

    If `mipmap_count` is left as -1, it will default to matching the mipmap count in `replace_in_tpf_texture` (if given)
    or else default to 0, which will generate a full mipmap chain with `texconv`. A specified value of 0 will do this
    explicitly; any more than that will generate exactly that many mipmaps.

    Returns a tuple of the DDS bytes and the DDS format actually used.
    """
    if dds_format is None:
        if not replace_in_tpf_texture:
            raise ValueError("Must supply `replace_in_tpf_texture` to copy `dds_format` from `dds_format=None`.")
        dds_format = replace_in_tpf_texture.get_dds().texconv_format

    if "TYPELESS" in dds_format:
        old_dds_format = dds_format
        dds_format = old_dds_format.replace("TYPELESS", "UNORM")
        print(f"# INFO: Changing DDS format '{old_dds_format}' to '{dds_format}' for conversion.")

    if replace_in_tpf_texture and mipmap_count == -1:
        # Detect original mipmap count.
        mipmap_count = replace_in_tpf_texture.get_dds().header.mipmap_count
    elif mipmap_count == -1:
        # Default to 0 (no source texture to check).
        mipmap_count = 0

    temp_image_path = Path(f"~/AppData/Local/Temp/temp.png").expanduser()
    bl_image.filepath_raw = str(temp_image_path)
    bl_image.save()  # TODO: sometimes fails with 'No error' (depending on how Blender is storing image data I think)
    with tempfile.TemporaryDirectory() as output_dir:
        texconv_result = texconv(
            "-o", output_dir, "-ft", "dds", "-f", dds_format, "-m", str(mipmap_count), temp_image_path
        )
        try:
            dds_data = Path(output_dir, "temp.dds").read_bytes()
        except FileNotFoundError:
            stdout = "\n    ".join(texconv_result.stdout.decode().split("\r\n")[3:])  # drop copyright lines
            raise ValueError(f"Could not convert texture to DDS with format {dds_format}:\n    {stdout}")

    if replace_in_tpf_texture:
        replace_in_tpf_texture.data = dds_data
    return dds_data, dds_format


def create_lightmap_tpf(bl_lightmap_image, dds_format="BC7_UNORM"):
    """Construct a new TPF containing the given lightmap image in the given DDS format.

    Any DCX compression for the TPF is left to the caller.

    TODO: Currently has hard-coded DS1 values.
    """
    texture = TPFTexture()
    texture.name = str(Path(bl_lightmap_image.name).with_suffix(".dds"))
    texture.format = 38  # for DS1 lightmaps

    tpf = TPF()
    tpf.textures = [texture]
    tpf.platform = TPFPlatform.PC
    tpf.encoding = 2  # for DS1
    tpf.tpf_flags = 3  # for DS1

    # Insert DDS content.
    bl_image_to_dds(bl_lightmap_image, replace_in_tpf_texture=texture, dds_format=dds_format)
    return tpf


@dataclass(slots=True)
class TextureManager:
    """Manages various texture sources across some import context, ensuring that Binders and TPFs are only loaded
    when requested for the first time during the operation.

    Uses selected game, FLVER name, and FLVER texture paths to determine where to find TPFs.
    """

    # Maps Binder stems to Binder file paths we are aware of, but have NOT yet opened and scanned for TPF sources.
    _binder_paths: dict[str, Path] = field(default_factory=dict)

    # Maps TPF stems to file paths or Binder entries we are aware of, but have NOT yet loaded into TPF textures (below).
    _pending_tpf_sources: dict[str, Path | BinderEntry] = field(default_factory=dict)

    # Maps TPF stems to opened TPF textures.
    _tpf_textures: dict[str, TPFTexture] = field(default_factory=dict)

    # Holds Binder file paths that have already been opened and scanned, so they aren't checked again.
    _scanned_binder_paths: set[Path] = field(default_factory=set)

    # Holds TPF stems that have already been opened and scanned, so they aren't checked again.
    _scanned_tpf_sources: set[str] = field(default_factory=set)

    def find_flver_textures(self, flver_source_path: Path, flver_binder: Binder = None):
        """Register known game Binders/TPFs to be opened as needed."""
        source_name = Path(flver_source_path).name.removesuffix(".dcx")
        source_dir = flver_source_path.parent

        if source_name.endswith(".flver"):
            # Loose FLVER file. Likely a map piece in an older game like DS1. We look in adjacent `mXX` directory.
            self._find_map_tpfbhds(source_dir)
        elif source_name.endswith(".chrbnd"):
            # CHRBND should have been given as an initial Binder. We also look in adjacent `chrtpfbdt` file.
            if flver_binder:
                self.scan_binder_textures(flver_binder)
                self._find_chr_tpfbdts(source_dir, flver_binder)
            else:
                _LOGGER.warning(
                    f"Opened CHRBND '{flver_source_path}' should have been passed to TextureManager! Will not be able "
                    f"to load attached character textures."
                )
        elif source_name.endswith("bnd"):
            # Miscellaneous Binder already scanned for TPFs above. Warn if it wasn't passed in.
            if not flver_binder:
                _LOGGER.warning(
                    f"Opened Binder '{flver_source_path}' should have been passed to TextureManager! Will not be able "
                    f"to load FLVER textures from the same Binder."
                )
            else:
                self.scan_binder_textures(flver_binder)
        elif source_name.endswith(".geombnd"):
            # Likely an AEG asset FLVER from Elden Ring onwards. We look in nearby `aet` directory.
            self._find_aeg_tpfs(source_dir)

    def find_specific_map_textures(self, map_area_dir: Path):
        """Register TPFBHD Binders in a specific `map_area_dir` 'mAA' map directory.

        Some vanilla map pieces use textures from different maps, e.g. when the game expects the map piece to be loaded
        while the source map is still active. This is especially common in DS1, which has a lot of shared textures.

        A map piece FLVER importer can call this method as a backup if a texture is not found based on the initial
        same-map TPFBHD scanning, using the texture's prefix to find the correct `map_area_dir`. For example, if a map
        piece in m12 uses a texture named `m10_wall_01`, this method will be called with `map_area_dir` set to
        `{game_directory}/map/m10`.
        """
        self._find_map_area_tpfbhds(map_area_dir)

    def scan_binder_textures(self, binder: Binder):
        """Register all TPFs in an arbitrary opened Binder (usually the one containing the FLVER) as pending sources."""
        for tpf_entry in binder.find_entries_matching_name(TPF_RE):
            tpf_entry_stem = tpf_entry.name.split(".")[0]
            if tpf_entry_stem not in self._scanned_tpf_sources:
                self._pending_tpf_sources.setdefault(tpf_entry_stem, tpf_entry)

    def get_flver_texture(self, texture_stem: str) -> TPFTexture:
        """Find texture from its stem across all registered/loaded texture file sources."""
        # TODO: Add a 'hint' argument that helps efficiently find map piece textures in arbitrary maps, based on the
        #  map prefix of `texture_stem`, so that

        if texture_stem in self._tpf_textures:
            # Already found and loaded.
            return self._tpf_textures[texture_stem]

        if texture_stem in self._pending_tpf_sources:
            # Found a pending TPF with the exact same stem as the requested texture (should have only one DDS).
            self._load_tpf(texture_stem)
            try:
                return self._tpf_textures[texture_stem]
            except KeyError:
                _LOGGER.warning(
                    f"TPF named '{texture_stem}' does not actually contain a DDS texture called '{texture_stem}'."
                )
                raise

        # Search for a multi-DDS TPF whose stem is a prefix of the requested texture.
        for tpf_stem in self._pending_tpf_sources:
            if texture_stem.startswith(tpf_stem):
                # TODO: Could also enforce that the texture stem only has two extra characters (e.g. '_n' or '_s').
                self._load_tpf(tpf_stem)
                try:
                    return self._tpf_textures[texture_stem]
                except KeyError:
                    # TODO: Not sure if this should ever be allowed to happen (conflicting texture prefixes??).
                    continue

        if self._binder_paths:
            # Last resort: scan all pending Binders for new TPFs. We typically cannot tell which Binder has the texture.
            # TODO: I could at least check JUST the BHD headers of TPFBHD split Binders before loading them.

            for binder_stem in tuple(self._binder_paths):  # binder keys may be popped when textures are loaded
                self._load_binder(binder_stem)

            # Recursive call with all Binder TPFs now loaded.
            return self.get_flver_texture(texture_stem)

        raise KeyError(f"Could not find texture '{texture_stem}' in any registered Binders or TPFs.")

    def _load_binder(self, binder_stem):
        binder_path = self._binder_paths.pop(binder_stem)
        self._scanned_binder_paths.add(binder_path)
        binder = Binder.from_path(binder_path)
        for tpf_entry in binder.find_entries_matching_name(TPF_RE):
            tpf_entry_stem = tpf_entry.name.split(".")[0]
            if tpf_entry_stem not in self._scanned_tpf_sources:
                self._pending_tpf_sources.setdefault(tpf_entry_stem, tpf_entry)

    def _load_tpf(self, tpf_stem):
        tpf_path_or_entry = self._pending_tpf_sources.pop(tpf_stem)
        self._scanned_tpf_sources.add(tpf_stem)
        if isinstance(tpf_path_or_entry, BinderEntry):
            tpf = TPF.from_binder_entry(tpf_path_or_entry)
        else:
            tpf = TPF.from_path(tpf_path_or_entry)
        for texture in tpf.textures:
            # TODO: Handle duplicate textures/overwrites. Currently ignoring duplicates.
            self._tpf_textures.setdefault(texture.name, texture)

    def _find_map_tpfbhds(self, map_area_block_dir: Path):
        """Find 'mAA' directory adjacent to given 'mAA_BB_CC_DD' directory and find all TPFBHD split Binders in it."""
        map_directory_match = MAP_STEM_RE.match(map_area_block_dir.name)
        if not map_directory_match:
            _LOGGER.warning("Loose FLVER not located in a map folder (`mAA_BB_CC_DD`). Cannot find map TPFs.")
            return
        area = map_directory_match.groupdict()["area"]
        map_area_dir = map_area_block_dir / f"../m{area}"
        self._find_map_area_tpfbhds(map_area_dir)

    def _find_map_area_tpfbhds(self, map_area_dir: Path):
        if not map_area_dir.is_dir():
            _LOGGER.warning(f"`mXX` TPFBHD folder does not exist: {map_area_dir}. Cannot find map TPFs.")
            return

        for tpf_or_tpfbhd_path in map_area_dir.glob("*.tpf*"):
            if tpf_or_tpfbhd_path.name.endswith(".tpfbhd"):
                binder_stem = tpf_or_tpfbhd_path.name.split(".")[0]
                if tpf_or_tpfbhd_path not in self._scanned_binder_paths:
                    self._binder_paths.setdefault(binder_stem, tpf_or_tpfbhd_path)
            elif TPF_RE.match(tpf_or_tpfbhd_path.name):
                # Loose map TPF (usually 'mXX_9999.tpf').
                tpf_stem = tpf_or_tpfbhd_path.name.split(".")[0]
                if tpf_stem not in self._scanned_tpf_sources:
                    self._pending_tpf_sources.setdefault(tpf_stem, tpf_or_tpfbhd_path)

    def _find_chr_tpfbdts(self, source_dir: Path, chrbnd: Binder):
        try:
            tpfbhd_entry = chrbnd.find_entry_matching_name(CHRTPFBHD_RE)
        except (EntryNotFoundError, ValueError):
            # Optional, so we don't complain.
            return

        # Search for BDT.
        tpfbdt_stem = tpfbhd_entry.name.split(".")[0]
        tpfbdt_path = source_dir / f"{tpfbdt_stem}.chrtpfbdt"
        if not tpfbdt_path.is_file():
            _LOGGER.warning(f"Could not find expected CHRTPFBDT file for '{chrbnd.path}' at {tpfbdt_path}.")
            return

        tpfbxf = Binder.from_bytes(tpfbhd_entry.data, bdt_data=tpfbdt_path.read_bytes())
        for tpf_entry in tpfbxf.find_entries_matching_name(TPF_RE):
            # These are very likely to be used by the FLVER, but we still queue them up rather than open them now.
            tpf_stem = tpf_entry.name.split(".")[0]
            if tpf_stem not in self._scanned_tpf_sources:
                self._pending_tpf_sources.setdefault(tpf_stem, tpf_entry)

    def _find_aeg_tpfs(self, source_dir: Path):
        aeg_directory_match = AEG_STEM_RE.match(source_dir.name)
        if not aeg_directory_match:
            _LOGGER.warning("GEOMBND not located in an AEG folder (`aegXXX`). Cannot find AEG TPFs.")
            return
        aet_directory = source_dir / "../../aet"
        if not aet_directory.is_dir():
            _LOGGER.warning(f"`aet` directory does not exist: {aet_directory}. Cannot find AEG TPFs.")
            return

        for tpf_path in aet_directory.glob("*.tpf"):
            tpf_stem = tpf_path.name.split(".")[0]
            if tpf_stem not in self._scanned_tpf_sources:
                self._pending_tpf_sources.setdefault(tpf_stem, tpf_path)
