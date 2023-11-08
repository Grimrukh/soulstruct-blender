from __future__ import annotations

__all__ = [
    "TextureExportSettings",
    "export_images_to_tpf",
    "export_images_to_tpfbhd",
    "export_images_to_map_area_tpfbhds",
    "bl_image_to_dds",
]

import tempfile
from pathlib import Path

import bpy

from soulstruct.containers import Binder, BinderEntry
from soulstruct.containers.tpf import TPF, TPFTexture, TPFPlatform, texconv
from soulstruct.dcx import DCXType

from io_soulstruct.utilities import LoggingOperator, LoggingImportOperator


class TextureExportError(Exception):
    """Raised when there is a problem exporting textures."""


class TextureExportSettings(bpy.types.PropertyGroup):
    """Contains settings and enums that determine DDS compression type for each FLVER texture slot type."""
    # TODO: These defaults aren't good generically. Looks like some diffuse textures require DXT1, e.g. Could be
    #  material dependent!

    overwrite_existing: bpy.props.BoolProperty(
        name="Overwrite Existing Textures",
        description="Overwrite existing TPF textures with the same name as exported textures",
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
        description="Platform to export textures for",
        items=[
            ("PC", "PC", "PC"),
            ("Xbox360", "Xbox 360", "Xbox 360"),
            ("PS3", "PS3", "PS3"),
            ("PS4", "PS4", "PS4"),
            ("XboxOne", "Xbox One", "Xbox One"),
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
        max=10,
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
        max=10,
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
        max=10,
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
        max=10,
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
        max=10,
    )

    chrbnd_tpf_max_size: bpy.props.IntProperty(
        name="Max CHRBND TPF Size (KB)",
        description="Maximum size (in KB) of TPF bundled with CHRBND. Characters with total texture size beyond this "
                    "will have their texture data placed in individual TPFs in an adjacent split CHRTPFBDT",
        default=5000,
    )

    max_tpfs_per_map_tpfbhd: bpy.props.IntProperty(
        name="Max TPFs per Map TPFBHD",
        description="Maximum number of TPFs that can be bundled into a single map TPFBHD. All map TPFs will be "
                    "alphabetized and written to different TPFBHDs of no more than this many textures with suffixes "
                    "'_0000', '_0001', etc",
        default=324,
    )

    def detect_texture_dds_format(self, texture_stem: str) -> str:
        """Return DDS format and `TPFTexture` format for given texture type."""
        if texture_stem.endswith("_n"):
            return self.bumpmap_format
        elif texture_stem.endswith("_s"):
            return self.specular_format
        elif texture_stem.endswith("_h"):
            return self.height_format
        elif "_lit_" in texture_stem:
            return self.lightmap_format
        else:  # default
            return self.diffuse_format


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
    maximum_texture_size=0,
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
        dds_format = settings.detect_texture_dds_format(texture_stem)
        # Convert Blender image to DDS.
        try:
            data = bl_image_to_dds(context, image, dds_format)
        except TextureExportError as ex:
            operator.report({"ERROR"}, f"Could not export texture '{texture_stem}': {ex}")
            continue

        total_dds_size += len(data)
        tpf_textures.append(
            TPFTexture(name=texture_stem, data=data, format=TPF_TEXTURE_FORMATS.get(dds_format, 1))
        )

    if 0 < maximum_texture_size < total_dds_size:
        # Too much data for one multi-texture TPF. (Caller will likely create a split TPFBHD.)
        return None

    return TPF(
        textures=tpf_textures,
        platform=TPFPlatform[settings.platform],
        encoding_type=2,
        tpf_flags=3,
    )


def export_images_to_tpfbhd(
    context,
    operator: LoggingOperator,
    images: dict[str, bpy.types.Image],
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
        # Detect texture type from name.
        dds_format = settings.detect_texture_dds_format(texture_stem)
        # Convert Blender image to DDS.
        try:
            data = bl_image_to_dds(context, image, dds_format)
        except TextureExportError as ex:
            operator.report({"ERROR"}, f"Could not export texture '{texture_stem}': {ex}")
            continue
        # Create single-texture TPF.
        texture = TPFTexture(name=texture_stem, data=data, format=TPF_TEXTURE_FORMATS.get(dds_format, 1))
        tpf = TPF(
            textures=[texture],
            platform=TPFPlatform[settings.platform],
            encoding_type=2,
            tpf_flags=3,
        )
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
    settings = context.scene.texture_export_settings  # type: TextureExportSettings

    # Scan for all TPFs. We don't unpack the entries.
    tpf_entries = {}
    for tpfbhd_path in sorted(map_area_dir.glob(f"{map_area}_*.tpfbhd")):
        tpfbhd = Binder.from_path(tpfbhd_path)
        tpf_entries |= {entry.minimal_stem: entry for entry in tpfbhd.entries}

    new_tpf_info = []  # type: list[tuple[str, BinderEntry, str]]

    for texture_stem in images:

        dds_format = settings.detect_texture_dds_format(texture_stem)
        if dds_format == "NONE":
            continue  # do not export this texture type

        # We have to check for existing textures with the same name as those we're exporting.
        if texture_stem in tpf_entries:
            if not settings.overwrite_existing:
                raise FileExistsError(f"Texture '{texture_stem}' already exists in map area TPFBHDs.")
            if dds_format == "SAME":
                existing_tpf = TPF.from_binder_entry(tpf_entries[texture_stem])
                existing_dds = existing_tpf.textures[0].get_dds()
                dds_format = existing_dds.texconv_format
                if dds_format == "BC5U":
                    dds_format = "BC5_UNORM"
                print(f"Existing TPF {texture_stem}: DDS format '{dds_format}', "
                      f"TPF texture format {existing_tpf.textures[0].format}")
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

    # Convert images to DDS and export into found/new entries.
    success_count = 0
    for texture_stem, entry, dds_format in new_tpf_info:

        try:
            data = bl_image_to_dds(context, images[texture_stem], dds_format)
        except TextureExportError as ex:
            operator.report({"ERROR"}, f"Could not export texture '{texture_stem}': {ex}")
            continue
        success_count += 1
        operator.info(f"Converted texture {texture_stem} to DDS (format {dds_format}).")
        # Create single-texture TPF.
        texture = TPFTexture(name=texture_stem, data=data, format=TPF_TEXTURE_FORMATS.get(dds_format, 1))
        tpf = TPF(
            textures=[texture],
            platform=TPFPlatform[settings.platform],
            encoding_type=2,
            tpf_flags=3,
            dcx_type=tpf_dcx_type,
        )
        entry.data = bytes(tpf)

    # Alphabetize entries.
    remaining_entries = [tpf_entries[stem] for stem in sorted(tpf_entries)]
    max_per_map = settings.max_tpfs_per_map_tpfbhd

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

    operator.info(f"Export {success_count} textures to {tpfbhd_index} TPFBHDs in map area '{map_area}'.")

    return tpfbhds


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
