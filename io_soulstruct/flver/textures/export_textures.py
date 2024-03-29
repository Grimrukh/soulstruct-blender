from __future__ import annotations

__all__ = [
    "TextureExportSettings",
    "export_image_to_tpf",
    "export_images_to_tpf",
    "export_images_to_multiple_tpfs",
    "export_images_to_tpfbhd",
    "export_images_to_map_area_tpfbhds",
    "export_map_area_textures",
    "bl_image_to_dds",
    "bl_images_to_dds",
]

import math
import tempfile
from pathlib import Path

import bpy

from soulstruct.containers import Binder, BinderEntry
from soulstruct.containers.tpf import TPF, TPFTexture, TPFPlatform
from soulstruct.base.textures.texconv import texconv, batch_texconv_to_dds
from soulstruct.dcx import DCXType

from io_soulstruct.general import SoulstructSettings
from io_soulstruct.utilities import LoggingOperator, LoggingImportOperator


class TextureExportError(Exception):
    """Raised when there is a problem exporting textures."""


class TextureExportSettings(bpy.types.PropertyGroup):
    """Contains settings and enums that determine DDS compression type for each FLVER texture slot type."""
    # TODO: These defaults aren't good generically. Looks like some diffuse textures require DXT1, e.g. Could be
    #  material dependent!

    overwrite_existing_map_textures: bpy.props.BoolProperty(
        name="Overwrite Existing Map Textures",
        description="Overwrite existing map TPF textures with the same name as exported textures. Other FLVER types "
                    "that bundle their own textures will always be overwritten with a complete new set",
        default=True,
    )

    require_power_of_two: bpy.props.BoolProperty(
        name="Require Power of Two Size",
        description="Require that all exported textures have power-of-two dimensions. Even if disabled, this will "
                    "never allow 1-pixel textures to be exported",
        default=True,
    )

    platform: bpy.props.EnumProperty(
        name="Platform",
        description="Platform to export textures for. Currently only PC is supported",
        items=[
            ("PC", "PC", "PC"),
            # ("Xbox360", "Xbox 360", "Xbox 360"),
            # ("PS3", "PS3", "PS3"),
            # ("PS4", "PS4", "PS4"),
            # ("XboxOne", "Xbox One", "Xbox One"),
        ],
        default="PC",
    )

    diffuse_format: bpy.props.EnumProperty(
        name="Diffuse Format",
        description="DDS compression format for 'g_Diffuse' textures",
        items=[
            ("NONE", "None", "Do not export this texture type"),
            ("SAME", "Same", "Use same format as original texture (which must exist)"),
            ("DXT1", "DXT1", "DXT1 (no alpha)"),
            ("DXT3", "DXT3", "DXT3 (sharp alpha)"),
            ("DXT5", "DXT5", "DXT5 (smooth alpha)"),
            ("BC5_UNORM", "BC5", "BC5 (normal map)"),
            ("BC7_UNORM", "BC7", "BC7 (high quality)"),
        ],
        default="BC7_UNORM",
    )

    diffuse_mipmap_count: bpy.props.IntProperty(
        name="Diffuse Mipmap Count",
        description="Number of mipmaps to generate in DDS textures (0 = all mipmaps)",
        default=0,
        min=0,
        max=20,
    )

    specular_format: bpy.props.EnumProperty(
        name="Specular Format",
        description="DDS compression format for 'g_Specular' textures",
        items=[
            ("NONE", "None", "Do not export this texture type"),
            ("SAME", "Same", "Use same format as original texture (which must exist)"),
            ("DXT1", "DXT1", "DXT1 (no alpha)"),
            ("DXT3", "DXT3", "DXT3 (sharp alpha)"),
            ("DXT5", "DXT5", "DXT5 (smooth alpha)"),
            ("BC5_UNORM", "BC5", "BC5 (normal map)"),
            ("BC7_UNORM", "BC7", "BC7 (high quality)"),
        ],
        default="BC7_UNORM",
    )

    specular_mipmap_count: bpy.props.IntProperty(
        name="Specular Mipmap Count",
        description="Number of mipmaps to generate in DDS textures (0 = all mipmaps)",
        default=0,
        min=0,
        max=20,
    )

    bumpmap_format: bpy.props.EnumProperty(
        name="Bumpmap Format",
        description="DDS compression format for 'g_Bumpmap' (normal) textures",
        items=[
            ("NONE", "None", "Do not export this texture type"),
            ("SAME", "Same", "Use same format as original texture (which must exist)"),
            ("DXT1", "DXT1", "DXT1 (no alpha)"),
            ("DXT3", "DXT3", "DXT3 (sharp alpha)"),
            ("DXT5", "DXT5", "DXT5 (smooth alpha)"),
            ("BC5_UNORM", "BC5", "BC5 (normal map)"),
            ("BC7_UNORM", "BC7", "BC7 (high quality)"),
        ],
        default="BC5_UNORM",
    )

    bumpmap_mipmap_count: bpy.props.IntProperty(
        name="Bumpmap Mipmap Count",
        description="Number of mipmaps to generate in DDS textures (0 = all mipmaps)",
        default=0,
        min=0,
        max=20,
    )

    height_format: bpy.props.EnumProperty(
        name="Height Format",
        description="DDS compression format for 'g_Height' (parallax) textures",
        items=[
            ("NONE", "None", "Do not export this texture type"),
            ("SAME", "Same", "Use same format as original texture (which must exist)"),
            ("DXT1", "DXT1", "DXT1 (no alpha)"),
            ("DXT3", "DXT3", "DXT3 (sharp alpha)"),
            ("DXT5", "DXT5", "DXT5 (smooth alpha)"),
            ("BC5_UNORM", "BC5", "BC5 (normal map)"),
            ("BC7_UNORM", "BC7", "BC7 (high quality)"),
        ],
        default="BC5_UNORM",
    )

    height_mipmap_count: bpy.props.IntProperty(
        name="Height Mipmap Count",
        description="Number of mipmaps to generate in DDS textures (0 = all mipmaps)",
        default=0,
        min=0,
        max=20,
    )

    lightmap_format: bpy.props.EnumProperty(
        name="Lightmap Format",
        description="DDS compression format for 'g_Lightmap' textures",
        items=[
            ("NONE", "None", "Do not export this texture type"),
            ("SAME", "Same", "Use same format as original texture (which must exist)"),
            ("DXT1", "DXT1", "DXT1 (no alpha)"),
            ("DXT3", "DXT3", "DXT3 (sharp alpha)"),
            ("DXT5", "DXT5", "DXT5 (smooth alpha)"),
            ("BC5_UNORM", "BC5", "BC5 (normal map)"),
            ("BC7_UNORM", "BC7", "BC7 (high quality)"),
        ],
        default="BC7_UNORM",
    )

    lightmap_mipmap_count: bpy.props.IntProperty(
        name="Lightmap Mipmap Count",
        description="Number of mipmaps to generate in DDS textures (0 = all mipmaps)",
        default=0,
        min=0,
        max=20,
    )

    max_chrbnd_tpf_size: bpy.props.IntProperty(
        name="Max CHRBND TPF Size (KB)",
        description="Maximum size (in KB) of TPF bundled with CHRBND. Characters with total texture size beyond this "
                    "will have their texture data placed in individual TPFs in an adjacent folder (PTDE) or split "
                    "CHRTPFBDT (DSR)",
        default=5000,
    )

    map_tpfbhd_count: bpy.props.IntProperty(
        name="Map TPFBHD Count",
        description="Map texture TPFs will be alphabetized and evenly divided between this many TPFBHD binders with "
                    "suffixes '_0000', '_0001', etc. in their file stems",
        default=4,
        min=1,
        max=10,  # arbitrary
    )

    def detect_texture_dds_format_mipmap_count(self, texture_stem: str) -> tuple[str, int]:
        """Return selected DDS format and mipmap count for given texture stem."""
        # TODO: Handle other game types/suffixes like 'albedo', 'normal', 'displacement'.
        #  Probably just want a different settings group shown/used for each game.
        if texture_stem.endswith("_n"):
            return self.bumpmap_format, self.bumpmap_mipmap_count
        elif texture_stem.endswith("_s"):
            return self.specular_format, self.specular_mipmap_count
        elif texture_stem.endswith("_h"):
            return self.height_format, self.height_mipmap_count
        elif "_lit_" in texture_stem:
            return self.lightmap_format, self.lightmap_mipmap_count
        else:  # default
            return self.diffuse_format, self.diffuse_mipmap_count


# Defaults to 1. Not required by every game, but definitely in DSR.
TPF_TEXTURE_FORMATS = {
    "DXT1": 1,
    "BC5_UNORM": 36,
    "BC7_UNORM": 38,
}


def export_images_to_tpf(
    context,
    operator: LoggingOperator,
    images: dict[str, bpy.types.Image],
    enforce_max_chrbnd_tpf_size=False,
) -> TPF | None:
    """Combine all given Blender images as DDS files in one TPF.

    If `maximum_texture_size > 0 ` and the combined texture size is larger than that, `None` will be returned.
    """
    if not images:
        raise ValueError("No images given to combine into TPF.")

    settings = context.scene.texture_export_settings  # type: TextureExportSettings

    tpf_textures = []
    total_dds_size = 0
    for texture_stem in sorted(images):
        image = images[texture_stem]
        # Detect texture type from name.
        dds_format, mipmap_count = settings.detect_texture_dds_format_mipmap_count(texture_stem)
        if dds_format == "NONE":
            continue  # skip
        if dds_format == "SAME":
            # TODO: Fix.
            raise NotImplementedError("Can currently only export Map Piece textures in 'SAME' mode.")
        # Convert Blender image to DDS.
        try:
            data = bl_image_to_dds(context, image, dds_format, mipmap_count)
        except TextureExportError as ex:
            operator.report({"ERROR"}, f"Could not export texture '{texture_stem}': {ex}")
            continue

        total_dds_size += len(data)
        tpf_textures.append(
            TPFTexture(name=texture_stem, data=data, format=TPF_TEXTURE_FORMATS.get(dds_format, 1))
        )

    if enforce_max_chrbnd_tpf_size and 0 < settings.max_chrbnd_tpf_size < total_dds_size // 1000:  # KB
        # Too much data for one multi-texture TPF. (Caller will likely create a split TPFBHD.)
        return None

    return TPF(
        textures=tpf_textures,
        platform=TPFPlatform[settings.platform],
        encoding_type=2,
        tpf_flags=3,
    )


def export_image_to_tpf(
    context: bpy.types.Context,
    operator: LoggingOperator,
    settings: TextureExportSettings,
    texture_stem: str,
    image: bpy.types.Image,
    dcx_type: DCXType,
) -> TPF | None:
    # Detect texture type from name.
    dds_format, mipmap_count = settings.detect_texture_dds_format_mipmap_count(texture_stem)
    if dds_format == "NONE":
        return None  # no texture
    if dds_format == "SAME":
        # TODO: Fix.
        raise NotImplementedError("Can currently only export Map Piece textures in 'SAME' mode.")
    # Convert Blender image to DDS.
    try:
        data = bl_image_to_dds(context, image, dds_format, mipmap_count)
    except TextureExportError as ex:
        operator.report({"ERROR"}, f"Could not export texture '{texture_stem}': {ex}")
        return None
    # Create single-texture TPF.
    texture = TPFTexture(name=texture_stem, data=data, format=TPF_TEXTURE_FORMATS.get(dds_format, 1))
    return TPF(
        textures=[texture],
        platform=TPFPlatform[settings.platform],
        encoding_type=2,
        tpf_flags=3,
        dcx_type=dcx_type,
    )


def export_images_to_multiple_tpfs(
    context,
    operator: LoggingOperator,
    images: dict[str, bpy.types.Image],
    tpf_dcx_type: DCXType,
) -> dict[str, TPF]:
    """Put each DDS texture into its own TPF and return them all.

    Used for, e.g., 'overflow' CHRBND textures in DS1: PTDE when they do not fit into a single multi-texture CHRBND TPF.
    """
    if not images:
        raise ValueError("No images given to export to TPFs.")

    settings = context.scene.texture_export_settings  # type: TextureExportSettings

    tpfs = {}
    for texture_stem in sorted(images):
        image = images[texture_stem]
        tpf = export_image_to_tpf(context, operator, settings, texture_stem, image, tpf_dcx_type)
        if tpf:
            tpfs[texture_stem] = tpf

    return tpfs


def export_images_to_tpfbhd(
    context,
    operator: LoggingOperator,
    images: dict[str, bpy.types.Image],
    tpf_dcx_type: DCXType,
    entry_path_parent: str = "",
) -> Binder:
    """Put each DDS texture into its own TPF in a new TPFBHD split binder.

    Commonly used for CHRBNDs with too many textures to fit in one TPF (though that limit doesn't seem well-defined). In
    this case, the BDT data part of the split Binder is generally written next to the CHRBND as as CHRTPFBDT file, and
    the header is left inside the CHRBND as a CHRTPFBHD file.

    If given, `entry_path_parent` should end in an escaped backslash.
    """
    if not images:
        raise ValueError("No images given to combine into TPFBHD.")

    settings = context.scene.texture_export_settings  # type: TextureExportSettings

    tpfbxf = Binder.empty_bxf3()  # TODO: DS1 type
    for i, texture_stem in enumerate(sorted(images)):
        image = images[texture_stem]
        tpf = export_image_to_tpf(context, operator, settings, texture_stem, image, tpf_dcx_type)
        if not tpf:
            continue

        # Add TPF to TPFBHD.
        tpf_entry = BinderEntry(
            data=bytes(tpf),
            entry_id=i,
            path=f"{entry_path_parent}{texture_stem}.tpf",
            flags=0x2,
        )
        tpfbxf.add_entry(tpf_entry)

    return tpfbxf


def export_images_to_map_area_tpfbhds(
    context,
    operator: LoggingOperator,
    map_area_dir: Path,
    images: dict[str, bpy.types.Image],
    tpf_dcx_type: DCXType,
) -> list[Binder]:
    """Load all entries from all TPFBHDs in `map_area_dir`, export given `images` into them as single-DDS TPFs,
    re-alphabetize the entries, split them into new TPFBHDs (enforcing maximum file-per-BHD limit), and return them for
    the caller to save.

    Does NOT save the TPFBHDs to be consistent with the single-TPF and single-TPFBHD exporters above.
    """

    map_area = map_area_dir.name
    tex_export_settings = context.scene.texture_export_settings  # type: TextureExportSettings

    # Scan for all TPFs. We don't unpack the entries.
    tpf_entries = {}
    for tpfbhd_path in sorted(map_area_dir.glob(f"{map_area}_*.tpfbhd")):
        tpfbhd = Binder.from_path(tpfbhd_path)
        tpf_entries |= {entry.minimal_stem: entry for entry in tpfbhd.entries}

    if not tpf_entries:
        raise FileNotFoundError(f"No map TPFBHDs found in map area '{map_area}'.")

    new_tpf_info = []  # type: list[tuple[str, BinderEntry, str]]
    conversion_kwargs = {}  # type: dict[str, tuple[bpy.types.Image, str, int]]

    for texture_stem in images:

        dds_format, mipmap_count = tex_export_settings.detect_texture_dds_format_mipmap_count(texture_stem)
        if dds_format == "NONE":
            continue  # do not export this texture type

        # We check for existing textures with the same name as those we're exporting.
        if texture_stem in tpf_entries:
            if not tex_export_settings.overwrite_existing_map_textures:
                raise FileExistsError(f"Texture '{texture_stem}' already exists in map area TPFBHDs.")
            if dds_format == "SAME":
                existing_tpf = TPF.from_binder_entry(tpf_entries[texture_stem])
                existing_dds = existing_tpf.textures[0].get_dds()
                dds_format = existing_dds.texconv_format
                if dds_format == "BC5U":
                    dds_format = "BC5_UNORM"
                if "TYPELESS" in dds_format:
                    dds_format = dds_format.replace("TYPELESS", "UNORM")
                    operator.warning(f"Cannot export 'TYPELESS' DDS format. Changing to '{dds_format}'.")
            new_tpf_info.append(
                (texture_stem, tpf_entries[texture_stem], dds_format)
            )
        else:
            # Create a new entry for this texture.
            if dds_format == "SAME":
                raise ValueError(
                    f"Cannot export texture '{texture_stem}' with format 'SAME' because a texture with that name does "
                    f"not already exist."
                )
            new_tpf_info.append((texture_stem, BinderEntry(
                data=b"",  # handled below
                entry_id=0,  # handled below
                path=tpf_dcx_type.process_path(f"{texture_stem}.tpf"),  # no parent path
                flags=0x2,
            ), dds_format))

        conversion_kwargs[texture_stem] = (images[texture_stem], dds_format, mipmap_count)

    # Convert images to DDS.
    operator.info(f"Converting {len(conversion_kwargs)} Blender images to DDS textures...")
    dds_dict = bl_images_to_dds(operator, conversion_kwargs)

    # Export into found/new entries.
    success_count = 0
    for texture_stem, entry, dds_format in new_tpf_info:

        dds_data = dds_dict[texture_stem]
        if not dds_data:
            # Conversion failed.
            operator.report({"ERROR"}, f"Could not export texture '{texture_stem}'.")
            continue
        success_count += 1
        operator.info(f"Converted texture {texture_stem} to DDS (format {dds_format}).")
        # Create single-texture TPF.
        texture = TPFTexture(name=texture_stem, data=dds_data, format=TPF_TEXTURE_FORMATS.get(dds_format, 1))
        tpf = TPF(
            textures=[texture],
            platform=TPFPlatform[tex_export_settings.platform],
            encoding_type=2,
            tpf_flags=3,
            dcx_type=tpf_dcx_type,
        )
        entry.data = bytes(tpf)

    # Alphabetize entries.
    remaining_entries = [tpf_entries[stem] for stem in sorted(tpf_entries)]
    max_per_map = math.ceil(len(remaining_entries) / tex_export_settings.map_tpfbhd_count)

    # Split entries into TPFBHDs of maximum size.
    tpfbhds = []
    tpfbhd_index = 0
    while remaining_entries:
        tpfbhd_entries, remaining_entries = remaining_entries[:max_per_map], remaining_entries[max_per_map:]
        tpfbhd = Binder.empty_bxf3()
        tpfbhd.dcx_type = DCXType.Null
        for i, entry in enumerate(tpfbhd_entries):
            entry.entry_id = i
            tpfbhd.add_entry(entry)
        tpfbhd.path = (map_area_dir / f"{map_area}_{tpfbhd_index:04}.tpfbhd").resolve()
        tpfbhds.append(tpfbhd)
        tpfbhd_index += 1

    operator.info(f"Exported {success_count} textures to {tpfbhd_index} TPFBHDs in map area {map_area}.")

    return tpfbhds


def export_map_area_textures(
    operator: LoggingOperator,
    context: bpy.types.Context,
    settings: SoulstructSettings,
    map_area_textures: dict[str, dict[str, bpy.types.Image]],
):
    tpf_dcx_type = settings.game.get_dcx_type("tpf")  # TPFs inside map TPFBXFs use standard game DCX
    # TODO: When to use 'mAA_9999.tpf.dcx'? Never?
    for area, area_textures in map_area_textures.items():
        import_area_dir = settings.get_game_path(f"map/{area}")
        export_area_dir = settings.get_project_path(f"map/{area}")
        if not export_area_dir and not settings.also_export_to_game:
            # Should be caught by `settings.can_export` check in poll, but making extra sure here that any sort
            # of TPFBHD export is possible before the expensive DDS conversion call below.
            operator.error("Map textures not exported: game export path not set and export-to-import disabled.")
            return  # no point checking other areas
        if not (import_area_dir and import_area_dir.is_dir()) and not (export_area_dir and export_area_dir.is_dir()):
            operator.error(
                f"Textures not written. Cannot find map texture Binders to modify from either export "
                f"(preferred) or import (backup) map area directory: 'map/{area}"
            )
            continue
        if export_area_dir and import_area_dir and import_area_dir.is_dir():
            # Copy initial TPFBHDs/BDTs from import directory (will not overwrite existing).
            # Will raise a `FileNotFoundError` if import file does not exist.
            for tpfbhd_path in import_area_dir.glob("*.tpfbhd"):
                settings.prepare_project_file(Path(f"map/{area}/{tpfbhd_path.name}"), False, True)
            for tpfbdt_path in import_area_dir.glob("*.tpfbdt"):
                settings.prepare_project_file(Path(f"map/{area}/{tpfbdt_path.name}"), False, True)

        # We prefer to start with the TPFBHDs from the export directory (potentially just copied from import).
        if export_area_dir and export_area_dir.is_dir():
            map_area_dir = export_area_dir
        else:
            map_area_dir = import_area_dir

        if not map_area_dir or not map_area_dir.is_dir():
            operator.error(
                f"Textures not written. Cannot load map texture Binders from missing map area directory: "
                f"{map_area_dir}"
            )
            continue
        map_tpfbhds = export_images_to_map_area_tpfbhds(
            context, operator, map_area_dir, area_textures, tpf_dcx_type
        )
        for tpfbhd in map_tpfbhds:
            relative_tpfbhd_path = Path(f"map/{area}/{tpfbhd.path.name}")
            settings.export_file(operator, tpfbhd, relative_tpfbhd_path)


def bl_image_to_dds(
    context: bpy.types.Context,
    bl_image: bpy.types.Image,
    dds_format="",
    mipmap_count=0,
) -> bytes:
    """Export `bl_image` (generally as a PNG), convert it to a DDS of `dds_format` with `texconv` and return DDS data.

    If `dds_format` is left empty, it will be detected from the stem of the Blender image and the per-type formats given
    in the scene `TextureExportSettings`.

    Cannot export 'TYPELESS' DDS formats. If `mipmap_count` is left as 0, `texconv` will generate a full mipmap chain
    with `texconv`.

    TODO: Need a batch multiprocessing version of this:
        - Pass in all (bl_image, format, mipmaps) tuples to be converted.
        - Create a temporary PNG for each. Update filepath_raw and save Blender image.
        - Call a simple starmap function that calls `texconv` on each PNG with the appropriate format/mipmap args.
        - Read in all DDS files and return a dict mapping the Blender texture stems to DDS bytes.
        - Any conversion that failed just has `None` for its DDS bytes.
    """
    if "TYPELESS" in dds_format:
        # `texconv` does not support TYPELESS.
        raise TextureExportError(
            f"DDS format '{dds_format}' is not supported by `texconv`. Try UNORM instead of TYPELESS."
        )

    if not dds_format:
        dds_format = context.scene.texture_export_settings.get_texture_format(bl_image.name.split(".")[0])

    if len(bl_image.pixels) <= 4:
        raise TextureExportError(
            f"Blender image '{bl_image.name}' contains one or less pixels. Cannot export it."
        )

    temp_image_path = Path(f"~/AppData/Local/Temp/temp.png").expanduser()
    bl_image.filepath_raw = str(temp_image_path)  # TODO: matters if Blender file is not actually a PNG?
    bl_image.save()  # TODO: sometimes fails with 'No error' (depending on how Blender is storing image data I think)
    with tempfile.TemporaryDirectory() as output_dir:
        args = [
            "-o", output_dir, "-ft", "dds", "-f", dds_format,
            "-m", str(mipmap_count), "-nologo", temp_image_path
        ]
        if dds_format[:3] in {"BC5", "BC7"}:
            args.insert(4, "-dx10")  # force use of extended DX10 header (not critical but for vanilla consistency)
        texconv_result = texconv(*args)
        try:
            return Path(output_dir, "temp.dds").read_bytes()
        except FileNotFoundError:
            stdout = texconv_result.stdout.decode()
            raise TextureExportError(f"Could not convert texture to DDS with format {dds_format}:\n    {stdout}")


def bl_images_to_dds(
    operator: LoggingOperator,
    bl_images_formats_mipmaps: dict[str, tuple[bpy.types.Image, str, int]],
) -> dict[str, bytes]:
    processed_kwargs = {}

    for texture_stem, (bl_image, dds_format, mipmap_count) in bl_images_formats_mipmaps.items():
        if "TYPELESS" in dds_format:
            # `texconv` does not support TYPELESS.
            operator.error(
                f"DDS format '{dds_format}' is not supported by `texconv`. Try UNORM instead of TYPELESS."
            )
            continue

        if len(bl_image.pixels) <= 4:
            operator.error(
                f"Blender image '{bl_image.name}' contains one or less pixels. Cannot export it."
            )
            continue

        temp_image_path = Path(f"~/AppData/Local/Temp/{bl_image.name}").expanduser()
        bl_image.filepath_raw = str(temp_image_path)
        bl_image.save()  # TODO: sometimes fails with 'No error' (depending on how Blender is storing data I think)

        processed_kwargs[texture_stem] = {
            "dds_format": dds_format,
            "is_dx10": dds_format[:3] in {"BC5", "BC7"},
            "mipmap_count": mipmap_count,
            "input_path": temp_image_path,
        }

    with tempfile.TemporaryDirectory() as output_dir:
        dds_dict = batch_texconv_to_dds(Path(output_dir), processed_kwargs)

    return dds_dict


class ExportTexturesIntoBinder(LoggingImportOperator):
    """
    TODO: Shelved for now. Will basically just be a glorified converter to DDS formats. Probably want a version that
     exports ONE selected texture node or Image Viewer texture to a loose DDS or TPF, and another that exports all
     textures in a selected material into separate TPFs (maps) or multi TPFs (characters, etc.) in an existing Binder,
     like this one currently sort of does.
    """

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

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'})

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
