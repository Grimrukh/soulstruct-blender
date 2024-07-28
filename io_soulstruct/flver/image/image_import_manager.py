from __future__ import annotations

__all__ = [
    "ImageImportManager",
]

import logging
import re
from pathlib import Path

import bpy
from io_soulstruct.utilities import *
from soulstruct.containers import Binder, BinderEntry, EntryNotFoundError
from soulstruct.containers.tpf import TPF, TPFTexture
from soulstruct.games import *

_LOGGER = logging.getLogger(__name__)

TPF_RE = re.compile(r"(?P<stem>.*)\.tpf(?P<dcx>\.dcx)?$")
CHRTPFBHD_RE = re.compile(r"(?P<stem>.*)\.chrtpfbhd?$")  # never has DCX
AEG_STEM_RE = re.compile(r"^aeg(?P<aeg>\d\d\d)$")  # checks stem only


class ImageImportManager:
    """Manages various texture sources across some import context, ensuring that Binders and TPFs are only loaded
    when requested for the first time during the operation.

    Different methods are available for different FLVER file types that search different known locations for textures.
    """
    operator: LoggingOperator
    context: bpy.types.Context

    # Maps Binder stems to Binder file paths we are aware of, but have NOT yet opened and scanned for TPF sources.
    _binder_paths: dict[str, Path]

    # Maps TPF stems to file paths or Binder entries we are aware of, but have NOT yet loaded into TPF textures (below).
    _pending_tpf_sources: dict[str, Path | BinderEntry]

    # Maps TPF stems to opened TPF textures.
    _tpf_textures: dict[str, TPFTexture]

    # Holds Binder file paths that have already been opened and scanned, so they aren't checked again.
    _scanned_binder_paths: set[Path]

    # Holds TPF stems that have already been opened and scanned, so they aren't checked again.
    _scanned_tpf_sources: set[str]

    def __init__(self, operator: LoggingOperator, context: bpy.types.Context):
        self.operator = operator
        self.context = context

        self._binder_paths = {}
        self._pending_tpf_sources = {}
        self._tpf_textures = {}
        self._scanned_binder_paths = set()
        self._scanned_tpf_sources = set()

    def find_flver_textures(self, flver_source_path: Path, flver_binder: Binder = None, prefer_hi_res=True):
        """Register known game Binders/TPFs to be opened as needed.

        `flver_source_path` is the path to the Binder file containing the FLVER, or loose FLVER file.
        `flver_binder` is the Binder object that contains the FLVER, if it has already been opened.
        """
        source_name = Path(flver_source_path).name.removesuffix(".dcx")  # e.g. 'c1234.chrbnd' or 'm1234B0A10.flver'
        source_dir = flver_source_path.parent

        settings = self.operator.settings(self.context)

        # MAP PIECES
        if source_name.endswith(".flver"):
            # Loose FLVER file. Likely a map piece in an older game like DS1. We look in adjacent `mXX` directory.
            self._find_map_tpfs(source_dir)
        elif source_name.endswith(".mapbnd"):
            # PARTSBND should have been given as an initial Binder. We also look in adjacent `Common*.tpf` loose TPFs.
            if flver_binder:
                self.scan_binder_textures(flver_binder)
            else:
                _LOGGER.warning(f"Opened PARTSBND '{flver_binder}' was not passed to ImageImportManager!")
            self._find_parts_common_tpfs(source_dir)

        # CHARACTERS
        elif source_name.endswith(".chrbnd"):
            # CHRBND should have been given as an initial Binder. We also look in adjacent `chrtpfbdt` file (using
            # header in CHRBND) for DSR, and adjacent loose folders for PTDE.
            if flver_binder:
                self.scan_binder_textures(flver_binder)
                if settings.is_game(DARK_SOULS_PTDE):
                    self._find_chr_loose_tpfs(source_dir, model_stem=source_name.split(".")[0])
                elif settings.is_game(DARK_SOULS_DSR):
                    self._find_chr_tpfbdts(source_dir, flver_binder)  # CHRTPFBHD is in `flver_binder`
                elif settings.is_game(BLOODBORNE):
                    # Bloodborne doesn't have any loose/BXF CHRBND textures.
                    pass
                elif settings.is_game(DARK_SOULS_3, SEKIRO):
                    self._find_texbnd(source_dir, model_stem=source_name.split(".")[0], res="")  # no res
                elif settings.is_game(ELDEN_RING):
                    res = "_h" if prefer_hi_res else "_l"
                    self._find_texbnd(source_dir, model_stem=source_name.split(".")[0], res=res)
                    self._find_common_body(source_dir)
            else:
                _LOGGER.warning(
                    f"Opened CHRBND '{flver_source_path}' should have been passed to ImageImportManager! Will not be "
                    f"able to load attached character textures."
                )

            if not source_name.endswith("9.chrbnd"):
                # We also check for a 'cXXX9' CHRBND, which contains textures shared by all characters 'cXXX*'.
                # Example: c2239 in DSR has skin textures for Stray (c2230), Firesage (c2231), and Asylum Demon (c2232).
                c9_name = f"{source_name[:-8]}9.chrbnd"
                if flver_source_path.suffix == ".dcx":
                    c9_name += ".dcx"
                c9_chrbnd_path = source_dir / c9_name
                if c9_chrbnd_path not in self._scanned_binder_paths and c9_chrbnd_path.is_file():
                    # Found cXXX9 CHRBND. Mark it as scanned now, then recur this method on it.
                    self._scanned_binder_paths.add(c9_chrbnd_path)
                    c9_chrbnd = Binder.from_path(c9_chrbnd_path)
                    self.find_flver_textures(c9_chrbnd_path, flver_binder=c9_chrbnd)

        # EQUIPMENT
        elif source_name.endswith(".partsbnd"):
            # PARTSBND should have been given as an initial Binder. We also look in adjacent `Common*.tpf` loose TPFs.
            if flver_binder:
                self.scan_binder_textures(flver_binder)
            else:
                _LOGGER.warning(f"Opened PARTSBND '{flver_binder}' was not passed to ImageImportManager!")
            self._find_parts_common_tpfs(source_dir)

        # ASSETS (Elden Ring)
        elif source_name.endswith(".geombnd"):
            # Likely an AEG asset FLVER from Elden Ring onwards. We look in nearby `aet` directory.
            self._find_aeg_tpfs(source_dir)

        # GENERIC BINDERS (e.g. OBJECTS)
        elif source_name.endswith("bnd"):
            # Scan miscellaneous Binder for TPFs. Warn if it wasn't passed in.
            if not flver_binder:
                _LOGGER.warning(
                    f"Opened Binder '{flver_source_path}' should have been passed to ImageImportManager! Will not be "
                    f"able to load FLVER textures from the same Binder."
                )
            else:
                self.scan_binder_textures(flver_binder)

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

    def get_flver_texture(self, texture_stem: str, model_name: str = "") -> TPFTexture:
        """Find texture from its stem across all registered/loaded texture file sources.

        If `model_name` is given, multi-DDS TPFs with that name will also be opened and checked.
        """
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
        for tpf_stem in tuple(self._pending_tpf_sources):  # tpf keys may be popped when textures are loaded
            if texture_stem.startswith(tpf_stem) or (model_name and model_name.startswith(tpf_stem)):
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

    def _find_map_tpfs(self, map_area_block_dir: Path):
        """Find 'mAA' directory adjacent to given 'mAA_BB_CC_DD' directory and find all TPFBHD split Binders in it.

        In PTDE, also searches loose `map/tx` folder for TPFs.
        """
        map_directory_match = MAP_STEM_RE.match(map_area_block_dir.name)
        if not map_directory_match:
            _LOGGER.warning("Loose FLVER not located in a map folder (`mAA_BB_CC_DD`). Cannot find map TPFs.")
            return
        area = map_directory_match.groupdict()["area"]
        map_area_dir = map_area_block_dir / f"../m{area}"
        self._find_map_area_tpfbhds(map_area_dir)
        tx_path = map_area_block_dir / "../tx"
        if tx_path.is_dir():
            self._find_tpfs_in_dir(map_area_block_dir / "../tx")

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
                # Loose map multi-texture TPF (usually 'mXX_9999.tpf'). We unpack all textures in it immediately.
                tpf_stem = tpf_or_tpfbhd_path.name.split(".")[0]
                if tpf_stem not in self._scanned_tpf_sources:
                    tpf = TPF.from_path(tpf_or_tpfbhd_path)
                    for texture in tpf.textures:
                        # TODO: Handle duplicate textures/overwrites. Currently ignoring duplicates.
                        self._tpf_textures.setdefault(texture.name, texture)
                    self._scanned_tpf_sources.add(tpf_stem)

    def _find_tpfs_in_dir(self, tpf_dir: Path):
        """Register all TPF files in `tpf_dir` as pending sources."""
        if not tpf_dir.is_dir():
            _LOGGER.warning(f"Directory does not exist: {tpf_dir}. Cannot find TPFs in it.")
            return

        for tpf_path in tpf_dir.glob("*.tpf"):
            tpf_stem = tpf_path.name.split(".")[0]
            if tpf_stem not in self._scanned_tpf_sources:
                self._pending_tpf_sources.setdefault(tpf_stem, tpf_path)

    def _find_chr_loose_tpfs(self, source_dir: Path, model_stem: str):
        """Find character TPFs in a loose folder next to the CHRBND."""
        chr_tpf_dir = source_dir / model_stem
        if chr_tpf_dir.is_dir():
            for tpf_path in chr_tpf_dir.glob("*.tpf"):  # no DCX in PTDE
                tpf_stem = tpf_path.name.split(".")[0]
                if tpf_stem not in self._scanned_tpf_sources:
                    self._pending_tpf_sources.setdefault(tpf_stem, tpf_path)

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

    def _find_texbnd(self, source_dir: Path, model_stem: str, res: str):
        """Find character TPFs in a TEXBND next to the CHRBND. (Always DCX for games that use it.)"""
        texbnd_path = source_dir / f"{model_stem}{res}.texbnd.dcx"
        if not texbnd_path in self._scanned_binder_paths and texbnd_path.is_file():
            self._scanned_binder_paths.add(texbnd_path)
            texbnd = Binder.from_path(texbnd_path)
            for tpf_entry in texbnd.find_entries_matching_name(TPF_RE):
                # Multi-texture TPF; we unpack it now.
                tpf_stem = tpf_entry.name.split(".")[0]
                texbnd_tpf = TPF.from_binder_entry(tpf_entry)
                self._scanned_tpf_sources.add(tpf_stem)
                for texture in texbnd_tpf.textures:
                    self._tpf_textures.setdefault(texture.name, texture)

    def _find_common_body(self, source_dir):
        """Find 'parts/common_body.tpf.dcx' character TPFs. Used by many non-c0000 characters."""
        common_body_path = source_dir / "../parts/common_body.tpf.dcx"
        if not "common_body" in self._scanned_tpf_sources and common_body_path.is_file():
            # Multi-texture TPF; we unpack it now.
            self._scanned_tpf_sources.add("common_body")
            common_body = TPF.from_path(common_body_path)
            for texture in common_body.textures:
                self._tpf_textures.setdefault(texture.name, texture)

    def _find_parts_common_tpfs(self, source_dir: Path):
        """Find and immediately load all textures inside multi-texture 'Common' TPFs (e.g. player skin)."""
        for common_tpf_path in source_dir.glob("Common*.tpf"):
            common_tpf = TPF.from_path(common_tpf_path)
            common_tpf_stem = common_tpf_path.name.split(".")[0]
            self._scanned_tpf_sources.add(common_tpf_stem)
            for texture in common_tpf.textures:
                # TODO: Handle duplicate textures/overwrites. Currently ignoring duplicates.
                self._tpf_textures.setdefault(texture.name, texture)

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

