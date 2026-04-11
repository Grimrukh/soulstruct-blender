from __future__ import annotations

__all__ = [
    "FLVERGXItemProps",
    "FLVERMaterialProps",
    "FLVERMaterialSettings",
]

from pathlib import Path

import bpy

from soulstruct.flver import GXItem
from soulstruct.games import *

from ...base.register import io_soulstruct_class, io_soulstruct_pointer_property
from ...bpy_base.property_group import SoulstructPropertyGroup
from ...flver.image.enums import BlenderImageFormat


# noinspection PyUnusedLocal
def _check_gx_item_category(self, context: str) -> None:
    """Check that the GXItem category is four characters or empty."""
    value = self.category
    if not value:
        return  # empty is permitted
    if len(value) != 4:
        self.category = ""
        return
    # Valid.


# noinspection PyUnusedLocal
def _check_gx_item_data(self, context: str) -> None:
    """Check that the given value is a valid hexadecimal string. Otherwise, set it to an empty string."""
    value = self.data
    if not value:
        return  # empty is permitted
    value = value.replace(" ", "").upper()  # remove spaces
    if len(value) % 2 != 0:
        self.data = ""  # must be even number of characters
        return
    if not all(c in "0123456789ABCDEF" for c in value):
        self.data = ""
        return
    # Valid.


@io_soulstruct_class
class FLVERGXItemProps(bpy.types.PropertyGroup):
    """Extension properties for FLVER `GXItem` collection on `FLVERMaterialProps`.

    NOTE: This is only used as nested inside `FLVERMaterialProps`.

    NOTE: Dummy item that appears last in each list is not imported in Blender and is auto-created on export.
    """
    category: bpy.props.StringProperty(
        name="Category",
        description="Four-character category of this GX Item's function (e.g. 'GX00'). "
                    "Items with empty category will be ignored on export",
        default="",
        update=_check_gx_item_category,
    )
    index: bpy.props.IntProperty(
        name="Index",
        description="Index of this GX Item's function (e.g. 100)",
        default=0,
        min=-1,
        max=9999,  # TODO: complete guess, probably never goes this high (999?)
    )
    data: bpy.props.StringProperty(
        name="Data",
        description="Raw data of this GX Item (hex string, e.g. '00 3F 80 00')",
        default="",
        update=_check_gx_item_data,
    )

    def from_gx_item(self, gx_item: GXItem):
        try:
            self.category = gx_item.category.decode()
        except UnicodeDecodeError:
            self.category = ""
        self.index = gx_item.index
        self.data = " ".join(f"{b:02X}" for b in gx_item.data)

    def to_gx_item(self) -> GXItem:
        data = self.get_data_bytes()
        gx_item = GXItem(
            category=self.category.encode(),
            index=self.index,
            data=data,
        )
        gx_item.data = data
        return gx_item

    def get_data_bytes(self) -> bytes:
        return bytes(bytearray.fromhex(self.data))


@io_soulstruct_class
@io_soulstruct_pointer_property(bpy.types.Material, "FLVER_MATERIAL")
class FLVERMaterialProps(SoulstructPropertyGroup):
    """Extension properties for Blender materials that represent FLVER materials.

    In Blender, materials also store desired FLVER mesh settings -- that is, there may be multiple materials that are
    identical except for FLVER mesh/face set settings like backface culling. These settings are stored here.
    """

    GAME_PROP_NAMES = {
        DEMONS_SOULS: (
            "flags",
            "mat_def_path",
            "sampler_prefix",
        ),
        DARK_SOULS_PTDE: (
            "flags",
            "mat_def_path",
            "f2_unk_x18",
            "sampler_prefix",
        ),
        DARK_SOULS_DSR: (
            "flags",
            "mat_def_path",
            "f2_unk_x18",
            "sampler_prefix",
        ),
        ELDEN_RING: (
            "flags",
            "mat_def_path",
            "f2_unk_x18",
            "gx_items",
            "gx_item_index",
            "sampler_prefix",
        ),
    }

    flags: bpy.props.IntProperty(
        name="Flags",
        description="Material flags (ignored in Demon's Souls)",
        default=0,
    )
    mat_def_path: bpy.props.StringProperty(
        name="Mat Def Path",
        description="Material definition path (MATBIN name in Elden Ring, MTD name before that). Extension is ignored "
                    "by the game and always replaced with '.matbin' (Elden Ring) or '.mtd' (before Elden Ring)",
        default="",
    )
    f2_unk_x18: bpy.props.IntProperty(
        name="FLVER2 Unk x18",
        description="Unknown integer at material offset 0x18 (ignored in Demon's Souls)",
        default=0,
    )

    gx_items: bpy.props.CollectionProperty(
        name="GX Items",
        description="Collection of GX items for this material (DS2 and later only)",
        type=FLVERGXItemProps,
    )

    gx_item_index: bpy.props.IntProperty(
        name="GX Item Index",
        description="Index of selected GX item",
        default=-1,
    )

    sampler_prefix: bpy.props.StringProperty(
        name="Sampler Prefix",
        description="Optional prefix for sampler names in this material to make shader nodes nicer",
        default="",
    )

    shader_name: bpy.props.StringProperty(
        name="Shader Name (Read Only)",
        description="Name of shader found in material definition at load time",
        default="",
    )


@io_soulstruct_class
@io_soulstruct_pointer_property(bpy.types.Scene, "flver_material_settings")
class FLVERMaterialSettings(bpy.types.PropertyGroup):
    """Global (Scene) settings for FLVER material import/export."""

    image_cache_root_str: bpy.props.StringProperty(
        name="Image Cache Root Directory",
        description="Path of root directory to read/write cached image textures of chosen format, under game-specific "
                    "subfolders. Any textures not found in this directory will attempt to be loaded from raw DDS in "
                    "the project or game directory",
        default=Path("~/AppData/Local/soulstruct/.image_cache").expanduser().as_posix(),
        subtype="DIR_PATH",
    )

    image_cache_format: bpy.props.EnumProperty(
        name="Image Cache Format",
        description="Format of cached image textures. Both lossless; PNG files take up less space but load slower",
        items=[
            ("TARGA", "TGA", "TGA format (TARGA)"),
            ("PNG", "PNG", "PNG format"),
        ],
        default="TARGA",
    )

    import_cached_images: bpy.props.BoolProperty(
        name="Import Cached Images",
        description="Import cached images of the given format with matching stems from image cache directory if given, "
                    "rather than finding and converting DDS textures of imported FLVERs",
        default=True,
    )

    cache_new_game_images: bpy.props.BoolProperty(
        name="Cache New Game Images",
        description="Write cached images of the given format of imported FLVER textures (converted from DDS files) to "
                    "image cache directory if given and not already cached, so they can be loaded more quickly in the "
                    "future or modified without DDS headaches",
        default=True,
    )

    pack_image_data: bpy.props.BoolProperty(
        name="Pack Images in Blender",
        description="Pack Blender Image texture data into Blend file, rather than simply linking to the cached "
                    "image file on disk (if it exists and is loaded). Uncached DDS texture data will always be packed",
        default=False,
    )

    # region Wrapper Properties

    @property
    def image_cache_root_path(self) -> Path | None:
        """Get image cache root path, if set, or `None` if not set."""
        image_cache_root_str = self.image_cache_root_str
        return Path(image_cache_root_str) if image_cache_root_str else None

    @property
    def bl_image_cache_format(self) -> BlenderImageFormat:
        return BlenderImageFormat(self.image_cache_format)

    # endregion

    # region Image Retrieval

    def get_game_image_cache_directory(self, context: bpy.types.Context) -> Path | None:
        """Get the subdirectory under the image cache root for the active game."""
        image_cache_root_path = self.image_cache_root_path
        if not image_cache_root_path:
            return None
        game_submodule_name = context.scene.soulstruct_settings.game.submodule_name
        return image_cache_root_path / game_submodule_name

    def get_cached_image_path(self, context: bpy.types.Context, image_stem: str) -> Path:
        """Get the path to a cached image file in the game's image cache subdirectory."""
        image_cache_directory = self.get_game_image_cache_directory(context)
        if not image_cache_directory:
            raise NotADirectoryError("No image cache directory set.")
        image_name = f"{image_stem}{self.bl_image_cache_format.get_suffix()}"
        return image_cache_directory / image_name

    # endregion
