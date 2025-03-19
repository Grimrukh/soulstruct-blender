from __future__ import annotations

__all__ = [
    "ImageImportManager",
]

import logging
import re
import typing as tp
from pathlib import Path

import bpy

from soulstruct.containers import Binder, BinderEntry, EntryNotFoundError
from soulstruct.containers.tpf import TPF, TPFTexture, TPFPlatform
from soulstruct.games import *

from io_soulstruct.utilities import LoggingOperator, CheckDCXMode, MAP_STEM_RE

if tp.TYPE_CHECKING:
    from soulstruct.base.models.flver import FLVER

_LOGGER = logging.getLogger("soulstruct.io")

TPF_RE = re.compile(r"(?P<stem>.*)\.tpf(?P<dcx>\.dcx)?$")
CHRTPFBHD_RE = re.compile(r"(?P<stem>.*)\.chrtpfbhd?$")  # never has DCX
CHR_cXXX9_RE = re.compile(r"c\d\d\d9")  # checks stem only
AEG_STEM_RE = re.compile(r"^aeg(?P<aeg>\d\d\d)$")  # checks stem only
MAP_AREA_RE = re.compile(r"^m\d\d_")


def lower_name(texture: TPFTexture) -> str:
    return texture.stem.lower()


def lower_stem(path_or_entry: Path | BinderEntry) -> str:
    return path_or_entry.name.split(".")[0].lower()


class ImageImportManager:
    """Manages various texture sources across some import context.

    Ensures that Binders and TPFs are only loaded when needed (because a texture cannot be found in a source already
    scanned). Also separates the reading of Binder entry names, TPF texture names, and actual loading of DDS or cached
    PNG/TGA textures.

    Different methods are available for different FLVER file types that search different known locations for textures.

    Game texture paths are generally case-insensitive, but we try hard to maintain them for exporting the same texture
    path names into FLVERs (and/or writing new actual texture TPFs).
    """
    operator: LoggingOperator
    context: bpy.types.Context

    # Maps Binder stems to Binder file paths we are aware of, but have NOT yet opened and scanned for TPF sources.
    _binder_paths: dict[str, Path]

    # Maps TPF stems to file paths or Binder entries we are aware of, but have NOT yet loaded into TPF textures (below).
    _pending_tpf_sources: dict[str, Path | BinderEntry]

    # Maps TPF stems to opened TPF textures.
    _tpf_textures: dict[str, TPFTexture]

    # Records TPF platforms of found textures, which would otherwise be lost when the TPF is unpacked.
    _tpf_texture_platforms: dict[str, TPFPlatform]

    # Holds Binder file paths that have already been opened and scanned, so they aren't checked again.
    _scanned_binder_paths: set[Path]

    # Holds TPF stems that have already been opened and scanned, so they aren't checked again.
    _scanned_tpf_sources: set[str]

    def __init__(self, operator: LoggingOperator, context: bpy.types.Context):
        self.operator = operator
        self.context = context

        self._binder_paths = {}
        self._pending_tpf_sources = {}  # NOTE: keys are all lower case
        self._tpf_textures = {}  # NOTE: keys are all lower case
        self._scanned_binder_paths = set()
        self._scanned_tpf_sources = set()  # NOTE: all lower case

        # We register all `parts/common_*.tpf` textures immediately.
        parts_dir = context.scene.soulstruct_settings.get_import_dir_path("parts")
        if parts_dir:
            self._register_parts_common_tpfs(parts_dir)
        else:
            operator.warning("Could not find 'parts' directory to import common TPFs.")

    def find_flver_textures(self, flver_source_path: Path, flver_binder: Binder = None, prefer_hi_res=True):
        """Register known game Binders/TPFs to be opened as needed.

        `flver_source_path` is the path to the Binder file containing the FLVER, or loose FLVER file.
        `flver_binder` is the Binder object that contains the FLVER, if it has already been opened.
        """
        source_name = Path(flver_source_path).name.removesuffix(".dcx")  # e.g. 'c1234.chrbnd' or 'm1234B0A10.flver'
        model_stem = source_name.split(".")[0]
        source_dir = flver_source_path.parent

        settings = self.operator.settings(self.context)

        # MAP PIECES
        if model_stem.startswith("m") and source_name.endswith(".flver"):
            # Loose FLVER file. Likely a map piece in an older game like DS1. We look in adjacent `mXX` directory.
            self._register_map_tpfs(source_dir)
        elif source_name.endswith(".mapbnd"):
            # MAPBND should have been given as an initial Binder. We also look in adjacent `Common*.tpf` loose TPFs.
            _LOGGER.warning("Cannot yet find MAPBND Map Piece FLVER textures.")
            # TODO: Elden Ring MAPBND Map Piece textures are in 'asset/aet' subdirectories, I believe.
            # if flver_binder:
            #     self.scan_binder_textures(flver_binder)
            # else:
            #     _LOGGER.warning(f"Opened MAPBND '{flver_binder}' was not passed to ImageImportManager!")
            # self._find_mapbnd_tpfs(source_dir)

        # CHARACTERS
        elif model_stem.startswith("c") and source_name.endswith(".flver"):
            # Loose FLVER file, e.g. from Demon's Souls. We look for a TPF right next to it.
            self._register_chr_loose_tpfs(source_dir, CheckDCXMode.NO_DCX)
        elif source_name.endswith(".chrbnd"):
            # CHRBND should have been given as an initial Binder. We also look in adjacent `chrtpfbdt` file (using
            # header in CHRBND) for DSR, and adjacent loose folders for PTDE.
            if flver_binder:
                self.scan_binder_textures(flver_binder)
                if settings.is_game(DEMONS_SOULS):
                    # CHRBND itself is already inside model subdirectory ('chr/cXXXX') alongside the loose TPFs.
                    self._register_chr_loose_tpfs(source_dir, CheckDCXMode.NO_DCX)
                elif settings.is_game(DARK_SOULS_PTDE):
                    # CHRBND is next to a model subdirectory that contains loose TPFs ('chr/cXXXX').
                    self._register_chr_loose_tpfs(source_dir / model_stem, CheckDCXMode.NO_DCX)
                elif settings.is_game(DARK_SOULS_DSR):
                    # Some CHRBNDs have CHRTPFBDTs next to them (with the CHRTPFBHD inside the CHRBND).
                    self._register_chr_tpfbdts(source_dir, flver_binder)
                elif settings.is_game(BLOODBORNE):
                    # Bloodborne doesn't have any loose/BXF CHRBND textures. All TPFs are inside the CHRBND.
                    pass
                elif settings.is_game(DARK_SOULS_3, SEKIRO):
                    self._register_chr_texbnd(source_dir, model_stem=model_stem, res="")  # no res
                elif settings.is_game(ELDEN_RING):
                    res = "_h" if prefer_hi_res else "_l"
                    self._register_chr_texbnd(source_dir, model_stem=model_stem, res=res)
            else:
                _LOGGER.warning(
                    f"Opened CHRBND '{flver_source_path}' should have been passed to ImageImportManager! Will not be "
                    f"able to load attached character textures."
                )

            if not CHR_cXXX9_RE.match(model_stem):
                # We also check for a 'cXXX9' CHRBND, which contains textures shared by all characters 'cXXX*'.
                # Example: c2239 in DSR has skin textures for Stray (c2230), Firesage (c2231), and Asylum Demon (c2232).
                cxxx9_name = f"{model_stem[:4]}9.chrbnd"
                if flver_source_path.suffix == ".dcx":
                    cxxx9_name += ".dcx"
                cxxx9_chrbnd_path = source_dir / cxxx9_name
                if cxxx9_chrbnd_path not in self._scanned_binder_paths and cxxx9_chrbnd_path.is_file():
                    # Found cXXX9 CHRBND. Mark it as scanned now, then recur this method on it.
                    self._scanned_binder_paths.add(cxxx9_chrbnd_path)
                    c9_chrbnd = Binder.from_path(cxxx9_chrbnd_path)
                    self.find_flver_textures(cxxx9_chrbnd_path, flver_binder=c9_chrbnd)

        # EQUIPMENT
        elif source_name.endswith(".partsbnd"):
            # PARTSBND should have been given as an initial Binder. We also look in adjacent `Common*.tpf` loose TPFs.
            if flver_binder:
                self.scan_binder_textures(flver_binder)
            else:
                _LOGGER.warning(f"Opened PARTSBND '{flver_binder}' was not passed to ImageImportManager!")

        # ASSETS (Elden Ring)
        elif source_name.endswith(".geombnd"):
            # Likely an AEG asset FLVER from Elden Ring onwards. We look in nearby `aet` directory.
            self._register_aeg_tpfs(source_dir)

        # GENERIC BINDERS (e.g. Object FLVERs in OBJBNDs)
        elif source_name.endswith("bnd"):
            # Scan miscellaneous Binder for TPFs. Warn if it wasn't passed in.
            if not flver_binder:
                _LOGGER.warning(
                    f"Opened Binder '{flver_source_path}' should have been passed to ImageImportManager! Will not be "
                    f"able to load FLVER textures from the same Binder."
                )
            else:
                self.scan_binder_textures(flver_binder)

    def scan_binder_textures(self, binder: Binder):
        """Register all TPFs in an arbitrary opened Binder (usually the one containing the FLVER) as pending sources."""
        for tpf_entry in binder.find_entries_matching_name(TPF_RE):
            tpf_entry_stem = lower_stem(tpf_entry)
            if tpf_entry_stem not in self._scanned_tpf_sources:
                self._pending_tpf_sources.setdefault(tpf_entry_stem, tpf_entry)

    def get_flver_texture(self, texture_stem: str, model_name: str = "") -> TPFTexture:
        """Find texture from its stem across all registered/loaded texture file sources.

        If `model_name` is given, multi-DDS TPFs with that name will also be opened and checked.

        Texture stem is NOT case-sensitive.
        """
        model_name = model_name.lower()
        texture_stem = texture_stem.lower()

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

    def register_lazy_flver_map_textures(self, map_dir: Path, flver: FLVER) -> set[str]:
        """Check all FLVER texture stems for any 'mAA_' prefixes and register texures in that map area dir.

        Required for FLVERs that use 'lazy' texture loading:
            - Many Object FLVERs use textures from the map areas they expect to appear in.
            - Some vanilla Map Pieces also use textures from different maps that the game assumes will be loaded when
            the Map Piece appears. This is especially common in DS1, which has a lot of shared textures.

        Returns a set of map area prefixes found in the FLVER textures.
        """
        texture_map_areas = {
            texture_path.stem[:3]
            for texture_path in flver.get_all_texture_paths()
            if MAP_AREA_RE.match(texture_path.stem)
        }
        for map_area in texture_map_areas:
            map_area_dir = (map_dir / map_area).resolve()
            self._register_map_area_textures(map_area_dir)

        return texture_map_areas

    # region Source Registration Methods

    def _register_map_area_textures(self, map_area_dir: Path, check_dcx_mode: CheckDCXMode = CheckDCXMode.BOTH):
        """Register TPFBHD Binders and loose TPFs in a specific `map_area_dir` 'mAA' map directory."""
        if not map_area_dir.is_dir():
            _LOGGER.warning(f"`mXX` area folder does not exist: {map_area_dir}. Cannot register map area TPFs.")
            return

        for tpf_or_tpfbhd_path in map_area_dir.glob("*.tpf*"):
            if tpf_or_tpfbhd_path.name.endswith(".tpfbhd"):
                binder_stem = lower_stem(tpf_or_tpfbhd_path)
                if tpf_or_tpfbhd_path not in self._scanned_binder_paths:
                    self._binder_paths.setdefault(binder_stem, tpf_or_tpfbhd_path)
            elif tpf_m := TPF_RE.match(tpf_or_tpfbhd_path.name):
                if tpf_m.groupdict()["dcx"] and check_dcx_mode == CheckDCXMode.NO_DCX:
                    continue
                elif not tpf_m.groupdict()["dcx"] and check_dcx_mode == CheckDCXMode.DCX_ONLY:
                    continue

                # Loose map multi-texture TPF (usually 'mXX_9999.tpf'). We unpack all textures in it immediately.
                tpf_stem = lower_stem(tpf_or_tpfbhd_path)
                if tpf_stem not in self._scanned_tpf_sources:
                    tpf = TPF.from_path(tpf_or_tpfbhd_path)
                    for texture in tpf.textures:
                        # TODO: Handle duplicate textures/overwrites. Currently ignoring duplicates.
                        self._tpf_textures.setdefault(texture.stem.lower(), texture)
                    self._scanned_tpf_sources.add(tpf_stem)

    def _register_map_tpfs(self, map_area_block_dir: Path, check_dcx_mode=CheckDCXMode.BOTH):
        """Find 'mAA' directory adjacent to given 'mAA_BB_CC_DD' directory and find all TPFBHD split Binders in it.

        In PTDE, also searches loose `map/tx` folder for TPFs.
        """
        map_directory_match = MAP_STEM_RE.match(map_area_block_dir.name)
        if not map_directory_match:
            _LOGGER.warning("Loose FLVER not located in a map folder (`mAA_BB_CC_DD`). Cannot find map TPFs.")
            return

        # Most games have some TPFs or TPFBHDs (DSR) in the shared map area directory.
        area = map_directory_match.groupdict()["area"]
        map_area_dir = map_area_block_dir / f"../m{area}"
        self._register_map_area_textures(map_area_dir, check_dcx_mode)

        # Unpacked PTDE has a 'map/tx' folder with every loose TPF.
        tx_path = map_area_block_dir / "../tx"
        if tx_path.is_dir():
            self._register_tpfs_in_dir(map_area_block_dir / "../tx", check_dcx_mode=CheckDCXMode.NO_DCX)

    def _register_tpfs_in_dir(self, tpf_dir: Path, check_dcx_mode: CheckDCXMode = CheckDCXMode.BOTH):
        """Register all loose TPF files in `tpf_dir` as pending sources."""
        if not tpf_dir.is_dir():
            _LOGGER.warning(f"Directory does not exist: {tpf_dir}. Cannot find TPFs in it.")
            return

        for glob_pattern in check_dcx_mode.get_globs("*.tpf"):
            for tpf_path in tpf_dir.glob(glob_pattern):
                tpf_stem = lower_stem(tpf_path)
                if tpf_stem not in self._scanned_tpf_sources:
                    self._pending_tpf_sources.setdefault(tpf_stem, tpf_path)

    def _register_chr_loose_tpfs(self, chr_tpf_dir: Path, check_dcx_mode: CheckDCXMode = CheckDCXMode.BOTH):
        """Find character TPFs in a given loose folder."""
        if chr_tpf_dir.is_dir():
            for glob_pattern in check_dcx_mode.get_globs("*.tpf"):
                for tpf_path in chr_tpf_dir.glob(glob_pattern):
                    tpf_stem = lower_stem(tpf_path)
                    if tpf_stem not in self._scanned_tpf_sources:
                        self._pending_tpf_sources.setdefault(tpf_stem, tpf_path)

    def _register_chr_tpfbdts(self, source_dir: Path, chrbnd: Binder):
        """CHRTPFBDTs never have DCX."""
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
            tpf_stem = lower_stem(tpf_entry)
            if tpf_stem not in self._scanned_tpf_sources:
                self._pending_tpf_sources.setdefault(tpf_stem, tpf_entry)

    def _register_chr_texbnd(
        self,
        source_dir: Path,
        model_stem: str,
        res: str,
        check_dcx_mode: CheckDCXMode = CheckDCXMode.DCX_ONLY,
    ):
        """Find character TPFs in a TEXBND next to the CHRBND. (Always DCX for games that use it.)"""
        texbnd_path = source_dir / f"{model_stem}{res}.texbnd{'.dcx' if check_dcx_mode != CheckDCXMode.NO_DCX else ''}"
        if texbnd_path not in self._scanned_binder_paths and texbnd_path.is_file():
            self._scanned_binder_paths.add(texbnd_path)
            texbnd = Binder.from_path(texbnd_path)
            for tpf_entry in texbnd.find_entries_matching_name(TPF_RE):
                # Multi-texture TPF; we unpack it now.
                tpf_stem = lower_stem(tpf_entry)
                texbnd_tpf = TPF.from_binder_entry(tpf_entry)
                self._scanned_tpf_sources.add(tpf_stem)
                for texture in texbnd_tpf.textures:
                    self._tpf_textures.setdefault(texture.stem.lower(), texture)

    def _register_parts_common_tpfs(self, source_dir: Path, check_dcx_mode: CheckDCXMode = CheckDCXMode.BOTH):
        """Find and immediately load all textures inside multi-texture 'Common' TPFs (e.g. player skin, detail)."""
        for glob_case in ("Common*.tpf", "common*.tpf"):
            for glob_pattern in check_dcx_mode.get_globs(glob_case):
                for common_tpf_path in source_dir.glob(glob_pattern):
                    common_tpf_stem = lower_stem(common_tpf_path)
                    if common_tpf_stem not in self._scanned_tpf_sources:
                        self._scanned_tpf_sources.add(common_tpf_stem)
                        common_tpf = TPF.from_path(common_tpf_path)
                        for texture in common_tpf.textures:
                            # TODO: Handle duplicate textures/overwrites. Currently ignoring duplicates.
                            self._tpf_textures.setdefault(texture.stem.lower(), texture)

    def _register_aeg_tpfs(self, source_dir: Path, check_dcx_mode: CheckDCXMode = CheckDCXMode.DCX_ONLY):
        """Find AEG TPFs in an adjacent 'aet' directory. Always uses DCX in games that use it."""
        aeg_directory_match = AEG_STEM_RE.match(source_dir.name)
        if not aeg_directory_match:
            _LOGGER.warning("GEOMBND not located in an AEG folder (`aegXXX`). Cannot find AEG TPFs.")
            return
        aet_directory = source_dir / "../../aet"
        if not aet_directory.is_dir():
            _LOGGER.warning(f"`aet` directory does not exist: {aet_directory}. Cannot find AEG TPFs.")
            return

        for glob_pattern in check_dcx_mode.get_globs("*.tpf"):
            for tpf_path in aet_directory.glob(glob_pattern):
                tpf_stem = lower_stem(tpf_path)
                if tpf_stem not in self._scanned_tpf_sources:
                    self._pending_tpf_sources.setdefault(tpf_stem, tpf_path)

    # endregion

    # region Loading Methods

    def _load_binder(self, binder_stem):
        binder_path = self._binder_paths.pop(binder_stem)
        self._scanned_binder_paths.add(binder_path)
        binder = Binder.from_path(binder_path)
        for tpf_entry in binder.find_entries_matching_name(TPF_RE):
            tpf_entry_stem = lower_stem(tpf_entry)
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
            self._tpf_textures.setdefault(texture.stem.lower(), texture)

    # endregion
