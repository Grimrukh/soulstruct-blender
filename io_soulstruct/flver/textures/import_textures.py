from __future__ import annotations

__all__ = [
    "ImportTextures",
    "TextureImportManager",
    "import_png_as_image",
]

import logging
import re
import tempfile
import typing as tp
from dataclasses import dataclass, field
from pathlib import Path

import bpy

from soulstruct.base.textures.dds import DDS
from soulstruct.base.textures.texconv import texconv
from soulstruct.containers import Binder, BinderEntry, EntryNotFoundError
from soulstruct.containers.tpf import TPF, TPFTexture, batch_get_tpf_texture_png_data
from soulstruct.games import *

from io_soulstruct.utilities import MAP_STEM_RE
from io_soulstruct.utilities.operators import LoggingImportOperator

if tp.TYPE_CHECKING:
    from io_soulstruct.general import SoulstructSettings

_LOGGER = logging.getLogger(__name__)

TPF_RE = re.compile(r"(?P<stem>.*)\.tpf(?P<dcx>\.dcx)?$")
CHRTPFBHD_RE = re.compile(r"(?P<stem>.*)\.chrtpfbhd?$")  # never has DCX
AEG_STEM_RE = re.compile(r"^aeg(?P<aeg>\d\d\d)$")  # checks stem only


# NOTE: We don't need a PropertyGroup for texture import (yet).


class ImportTextures(LoggingImportOperator):
    """Import an image file from disk into Blender, converting DDS images to PNG first, and optionally assigning
    imported texture to one or more selected `Image` nodes."""
    bl_idname = "import_image.soulstruct_texture"
    bl_label = "Import Texture"
    bl_description = (
        "Import an image file (converting DDS to PNG) or all image files inside a TPF container into Blender, and "
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

    def execute(self, context):

        # TODO: Respect general PNG cache settings, including optional data pack.

        all_bl_images = {}

        for file_path in self.file_paths:

            if TPF_RE.match(file_path.name):
                all_bl_images |= self.import_tpf(file_path)  # must be single-texture
            elif file_path.suffix == ".dds":
                # Loose DDS file.
                try:
                    all_bl_images |= self.import_dds(file_path)
                except Exception as ex:
                    self.warning(f"Could not import DDS file into Blender: {ex}")
            else:
                try:
                    all_bl_images |= self.import_native(file_path)
                except Exception as ex:
                    self.warning(f"Could not import image file into Blender: {ex}")

        if not all_bl_images:
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
            if len(all_bl_images) > 1:
                self.warning(
                    "Cannot assign multiple imported textures in 'Selected Nodes (All)' mode. A single texture "
                    "must be imported and will be assigned to ALL selected Image Texture node."
                )
            sel = [node for node in material_nt.nodes if node.select and node.bl_idname == "ShaderNodeTexImage"]
            if not sel:
                self.warning("No selected Image Texture nodes for assigning new texture.")
            else:
                texture_name, bl_image = next(iter(all_bl_images.items()))
                for image_node in sel:
                    image_node.image = bl_image
                self.info(f"Set imported texture '{texture_name}' to {len(sel)} selected Image Texture node(s).")
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

        for texture_name, bl_image in all_bl_images.items():
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

    def import_tpf(self, tpf_path: Path) -> dict[str, bpy.types.Image]:
        tpf = TPF.from_path(tpf_path)
        if self.image_node_assignment_mode == "SIMPLE_TEXTURE" and len(tpf.textures) > 1:
            self.info(
                f"Cannot import multi-texture TPF in 'Selected Nodes (All)' assignment mode: {tpf_path}"
            )
            return {}

        textures_png_data = batch_get_tpf_texture_png_data(tpf.textures)
        self.info(f"Loaded {len(textures_png_data)} texture(s) from TPF: {tpf_path.name}")
        texture_images = {}
        for texture, png_data in zip(tpf.textures, textures_png_data):
            if png_data is None:
                continue  # failed to convert this texture
            try:
                bl_image = import_png_as_image(texture.name, png_data, replace_existing=self.overwrite_existing)
            except Exception as ex:
                self.warning(f"Could not create Blender image from TPF texture '{texture.name}': {ex}")
                continue
            texture_images[texture.name] = bl_image
        return texture_images

    def import_dds(self, dds_path: Path) -> dict[str, bpy.types.Image]:
        with tempfile.TemporaryDirectory() as png_dir:

            # Check DDS format for logging.
            dds = DDS.from_path(dds_path)
            dds_format = dds.texconv_format

            temp_dds_path = Path(png_dir, dds_path.name)
            temp_dds_path.write_bytes(dds_path.read_bytes())  # write temporary DDS copy
            texconv_result = texconv("-o", png_dir, "-ft", "png", "-f", "RGBA", "-nologo", temp_dds_path)
            png_path = Path(png_dir, dds_path.with_suffix(".png"))
            if png_path.is_file():
                bl_image = bpy.data.images.load(str(png_path))
                bl_image.pack()  # embed PNG in `.blend` file
                self.info(f"Loaded '{dds_format}' DDS file as PNG: {dds_path.name}")
                return {png_path.stem: bl_image}

            # Conversion failed.
            stdout = texconv_result.stdout.decode()
            self.warning(f"Could not convert texture DDS to PNG:\n    {stdout}")
            return {}

    def import_native(self, image_path: Path) -> dict[str, bpy.types.Image]:
        """Import a non-DDS image file (assumes general Blender support).

        Does NOT pack image data into '.blend' file, unlike DDS/TPF imports.
        """
        try:
            if not self.overwrite_existing:
                # Go straight to creation below.
                raise KeyError
            bl_image = bpy.data.images[image_path.name]
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
        return {image_path.stem: bl_image}


@dataclass(slots=True)
class TextureImportManager:
    """Manages various texture sources across some import context, ensuring that Binders and TPFs are only loaded
    when requested for the first time during the operation.

    Uses selected game, FLVER name, and FLVER texture paths to determine where to find TPFs.
    """
    settings: SoulstructSettings

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

    def find_flver_textures(self, flver_source_path: Path, flver_binder: Binder = None, prefer_hi_res=True):
        """Register known game Binders/TPFs to be opened as needed.

        `flver_source_path` is the path to the Binder file containing the FLVER, or loose FLVER file.
        `flver_binder` is the Binder object that contains the FLVER, if it has already been opened.
        """
        source_name = Path(flver_source_path).name.removesuffix(".dcx")  # e.g. 'c1234.chrbnd' or 'm1234B0A10.flver'
        source_dir = flver_source_path.parent

        # MAP PIECES
        if source_name.endswith(".flver"):
            # Loose FLVER file. Likely a map piece in an older game like DS1. We look in adjacent `mXX` directory.
            self._find_map_tpfs(source_dir)
        elif source_name.endswith(".mapbnd"):
            # PARTSBND should have been given as an initial Binder. We also look in adjacent `Common*.tpf` loose TPFs.
            if flver_binder:
                self.scan_binder_textures(flver_binder)
            else:
                _LOGGER.warning(f"Opened PARTSBND '{flver_binder}' was not passed to TextureImportManager!")
            self._find_parts_common_tpfs(source_dir)

        # CHARACTERS
        elif source_name.endswith(".chrbnd"):
            # CHRBND should have been given as an initial Binder. We also look in adjacent `chrtpfbdt` file (using
            # header in CHRBND) for DSR, and adjacent loose folders for PTDE.
            if flver_binder:
                self.scan_binder_textures(flver_binder)
                if self.settings.is_game(DARK_SOULS_PTDE):
                    self._find_chr_loose_tpfs(source_dir, model_stem=source_name.split(".")[0])
                elif self.settings.is_game(DARK_SOULS_DSR):
                    self._find_chr_tpfbdts(source_dir, flver_binder)  # CHRTPFBHD is in `flver_binder`
                elif self.settings.is_game(BLOODBORNE):
                    # Bloodborne doesn't have any loose/BXF CHRBND textures.
                    pass
                elif self.settings.is_game(DARK_SOULS_3, SEKIRO):
                    self._find_texbnd(source_dir, model_stem=source_name.split(".")[0], res="")  # no res
                elif self.settings.is_game(ELDEN_RING):
                    res = "_h" if prefer_hi_res else "_l"
                    self._find_texbnd(source_dir, model_stem=source_name.split(".")[0], res=res)
                    self._find_common_body(source_dir)
            else:
                _LOGGER.warning(
                    f"Opened CHRBND '{flver_source_path}' should have been passed to TextureImportManager! Will not be "
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
                _LOGGER.warning(f"Opened PARTSBND '{flver_binder}' was not passed to TextureImportManager!")
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
                    f"Opened Binder '{flver_source_path}' should have been passed to TextureImportManager! Will not be "
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


def import_png_as_image(
    image_name: str, png_data: bytes, write_png_directory: Path = None, replace_existing=False, pack_image_data=False
) -> bpy.types.Image:
    """Import PNG data into Blender as an image, optionally replacing an existing image with the same name.

    If `pack_image_data` is True and `write_png_directory` is given, the PNG data will be embedded in the `.blend` file.
    Otherwise, it will be linked to the original PNG file.
    """
    if write_png_directory is None:
        # Use a temporarily file.
        write_png_path = Path(f"~/AppData/Local/Temp/{image_name}.png").expanduser()
        is_temp_png = True
        if not pack_image_data:
            _LOGGER.warning(
                "Must pack PNG image data into Blender file when `write_png_directory` is not given ('Write Cached "
                "PNGs' disabled)."
            )
    else:
        write_png_path = write_png_directory / f"{image_name}.png"
        is_temp_png = False

    write_png_path.write_bytes(png_data)

    try:
        if not replace_existing:
            # Go straight to creation below.
            raise KeyError
        bl_image = bpy.data.images[image_name]
    except KeyError:
        bl_image = bpy.data.images.load(str(write_png_path))
        if is_temp_png or pack_image_data:
            bl_image.pack()  # embed PNG in Blend file
    else:
        if bl_image.packed_file:
            bl_image.unpack(method="USE_ORIGINAL")
        bl_image.filepath_raw = str(write_png_path)
        bl_image.file_format = "PNG"
        bl_image.source = "FILE"
        bl_image.reload()
        if is_temp_png or pack_image_data:
            bl_image.pack()  # embed new PNG in Blend file

    if is_temp_png:
        write_png_path.unlink(missing_ok=True)

    return bl_image
