from __future__ import annotations

__all__ = [
    "FLVERGXItemProps",
    "FLVERMaterialProps",
    "FLVERMaterialSettings",

    "get_cached_mtdbnd",
    "get_cached_matbinbnd",
    "clear_cached_matdefs",
]

import typing as tp
from pathlib import Path

import bpy

from soulstruct.flver import GXItem
from soulstruct.base.models.matbin import MATBINBND
from soulstruct.base.models.mtd import MTDBND
from soulstruct.games import *

from soulstruct.blender.bpy_base.property_group import SoulstructPropertyGroup
from soulstruct.blender.exceptions import InternalSoulstructBlenderError
from soulstruct.blender.flver.image.enums import BlenderImageFormat
from soulstruct.blender.general import SoulstructSettings
from soulstruct.blender.utilities import *

if tp.TYPE_CHECKING:
    from soulstruct.games import Game
    from soulstruct.blender.utilities import LoggingOperator


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


class FLVERGXItemProps(bpy.types.PropertyGroup):
    """Extension properties for FLVER `GXItem` collection on `FLVERMaterialProps`.

    NOTE: Dummy item that appears last in each list is not imported in Blender and is auto-created on export.
    """
    category: bpy.props.StringProperty(
        name="Category",
        description="Four-character category of this GX Item's function (e.g. 'GX00'). "
                    "Items with empty category will be ignored on export",
        default="",
        update=_check_gx_item_category
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


class FLVERMaterialProps(SoulstructPropertyGroup):
    """Extension properties for Blender materials that represent FLVER materials.

    In Blender, materials also store desired FLVER mesh settings -- that is, there may be multiple materials that are
    identical except for FLVER mesh/face set settings like backface culling. These settings are stored here.
    """

    GAME_PROP_NAMES = {
        DEMONS_SOULS: (
            "flags",
            "mat_def_path",
            "is_bind_pose",
            "default_bone_index",
            "face_set_count",
            "sampler_prefix",
        ),
        DARK_SOULS_PTDE: (
            "flags",
            "mat_def_path",
            "f2_unk_x18",
            "is_bind_pose",
            "default_bone_index",
            "face_set_count",
            "sampler_prefix",
        ),
        ELDEN_RING: (
            "flags",
            "mat_def_path",
            "f2_unk_x18",
            "is_bind_pose",
            "default_bone_index",
            "face_set_count",
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
    is_bind_pose: bpy.props.BoolProperty(
        name="Is Bind Pose [Mesh]",
        description="If enabled, mesh using this material is a rigged mesh. Typically disabled for Map Piece "
                    "FLVERs and enabled for everything else",
        default=False,
    )
    default_bone_index: bpy.props.IntProperty(
        name="Default Bone Index [Mesh]",
        description="Index of default bone for this mesh (if applicable). Sometimes junk in vanilla FLVERs",
        default=-1,
    )
    face_set_count: bpy.props.IntProperty(
        name="Face Set Count [Mesh]",
        description="Number of face sets in mesh using this material. This is NOT a real FLVER property, but tells "
                    "Blender how many duplicate FLVER face sets to make for this mesh. Typically used only for Map "
                    "Piece level of detail. Soulstruct cannot yet auto-generate simplified/decimated LoD face sets",
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


class FLVERMaterialSettings(SoulstructPropertyGroup):
    """Global (Scene) settings for FLVER material import/export."""

    GAME_PROP_NAMES = {
        DEMONS_SOULS: (
            "demonssouls_str_mtdbnd_path",
            "demonssouls_str_image_cache_directory",
            "image_cache_format",
            "import_cached_images",
            "cache_new_game_images",
            "pack_image_data",
        ),
        DARK_SOULS_PTDE: (
            "darksouls1ptde_str_mtdbnd_path",
            "darksouls1ptde_str_image_cache_directory",
            "image_cache_format",
            "import_cached_images",
            "cache_new_game_images",
            "pack_image_data",
        ),
        DARK_SOULS_DSR: (
            "darksouls1r_str_mtdbnd_path",
            "darksouls1r_str_image_cache_directory",
            "image_cache_format",
            "import_cached_images",
            "cache_new_game_images",
            "pack_image_data",
        ),
        BLOODBORNE: (
            "bloodborne_str_mtdbnd_path",
            "bloodborne_str_image_cache_directory",
            "image_cache_format",
            "import_cached_images",
            "cache_new_game_images",
            "pack_image_data",
        ),
        ELDEN_RING: (
            "eldenring_str_matbinbnd_path",
            "eldenring_str_image_cache_directory",
            "image_cache_format",
            "import_cached_images",
            "cache_new_game_images",
            "pack_image_data",
        ),
    }

    demonssouls_str_mtdbnd_path: bpy.props.StringProperty(
        name="MTDBND Path",
        description="Path of custom MTDBND file for detecting material setups in Demon's Souls. "
                    "Defaults to an automatic known location in selected project (preferred) or game directory",
        default="",
        subtype="FILE_PATH",
    )
    darksouls1ptde_str_mtdbnd_path: bpy.props.StringProperty(
        name="MTDBND Path",
        description="Path of custom MTDBND file for detecting material setups in Dark Souls 1 (PTDE). "
                    "Defaults to an automatic known location in selected project (preferred) or game directory",
        default="",
        subtype="FILE_PATH",
    )
    darksouls1r_str_mtdbnd_path: bpy.props.StringProperty(
        name="MTDBND Path",
        description="Path of custom MTDBND file for detecting material setups in Dark Souls 1 (Remastered). "
                    "Defaults to an automatic known location in selected project (preferred) or game directory",
        default="",
        subtype="FILE_PATH",
    )
    bloodborne_str_mtdbnd_path: bpy.props.StringProperty(
        name="MTDBND Path",
        description="Path of custom MTDBND file for detecting material setups in Bloodborne. "
                    "Defaults to an automatic known location in selected project (preferred) or game directory",
        default="",
        subtype="FILE_PATH",
    )

    eldenring_str_matbinbnd_path: bpy.props.StringProperty(
        name="MATBINBND Path",
        description="Path of custom MATBINBND file for detecting material setups in Elden Ring. "
                    "Defaults to an automatic known location in selected project (preferred) or game directory. "
                    "If '_dlc01' and '_dlc02' variants of path name are found, they will also be loaded",
        default="",
        subtype="FILE_PATH",
    )

    demonssouls_str_image_cache_directory: bpy.props.StringProperty(
        name="Image Cache Directory",
        description="Path of directory to read/write cached image textures of chosen format for Demon's Souls. "
                    "Any textures not found in this directory will attempt to be loaded from raw DDS in the project or "
                    "game directory",
        default="",
        subtype="DIR_PATH",
    )
    darksouls1ptde_str_image_cache_directory: bpy.props.StringProperty(
        name="Image Cache Directory",
        description="Path of directory to read/write cached image textures of chosen format for Dark Souls 1 (PTDE). "
                    "Any textures not found in this directory will attempt to be loaded from raw DDS in the project or "
                    "game directory",
        default="",
        subtype="DIR_PATH",
    )
    darksouls1r_str_image_cache_directory: bpy.props.StringProperty(
        name="Image Cache Directory",
        description="Path of directory to read/write cached image textures of chosen format for Dark Souls 1 "
                    "(Remastered). "
                    "Any textures not found in this directory will attempt to be loaded from raw DDS in the project or "
                    "game directory",
        default="",
        subtype="DIR_PATH",
    )
    bloodborne_str_image_cache_directory: bpy.props.StringProperty(
        name="Image Cache Directory",
        description="Path of directory to read/write cached image textures of chosen format for Bloodborne. "
                    "Any textures not found in this directory will attempt to be loaded from raw DDS in the project or "
                    "game directory",
        default="",
        subtype="DIR_PATH",
    )
    eldenring_str_image_cache_directory: bpy.props.StringProperty(
        name="Image Cache Directory",
        description="Path of directory to read/write cached image textures of chosen format for Elden Ring. "
                    "Any textures not found in this directory will attempt to be loaded from raw DDS in the project or "
                    "game directory",
        default="",
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

    @staticmethod
    def get_game_mtdbnd_path_prop_name(context: bpy.types.Context) -> str:
        """Get property name for MTDBND path string. Returns empty string if active game does not use MTDs."""
        if context.scene.soulstruct_settings.game_config.uses_matbin:
            return ""
        game = context.scene.soulstruct_settings.game
        return f"{game.submodule_name}_str_mtdbnd_path"

    def get_game_mtdbnd_path(self, context: bpy.types.Context) -> Path | None:
        prop_name = self.get_game_mtdbnd_path_prop_name(context)
        if not prop_name:
            game = context.scene.soulstruct_settings.game
            raise InternalSoulstructBlenderError(
                f"Active game '{game.name}' does not use MTDs and should not be trying to read MTDBND path."
            )
        path_str = getattr(self, prop_name)
        return Path(path_str) if path_str else None

    @staticmethod
    def get_game_matbinbnd_path_prop_name(context: bpy.types.Context) -> str:
        """Get property name for MATBINBND path string. Returns empty string if active game does not use MATBINs."""
        if not context.scene.soulstruct_settings.game_config.uses_matbin:
            return ""
        game = context.scene.soulstruct_settings.game
        return f"{game.submodule_name}_str_matbinbnd_path"

    def get_game_matbinbnd_path(self, context: bpy.types.Context) -> Path | None:
        prop_name = self.get_game_matbinbnd_path_prop_name(context)
        if not prop_name:
            game = context.scene.soulstruct_settings.game
            raise InternalSoulstructBlenderError(
                f"Active game '{game.name}' does not use MATBINs and should not be trying to read MATBINBND path."
            )
        path_str = getattr(self, prop_name)
        return Path(path_str) if path_str else None

    @staticmethod
    def get_game_image_cache_path_prop_name(context: bpy.types.Context) -> str:
        """Get property name for active game's image cache directory."""
        game = context.scene.soulstruct_settings.game
        return f"{game.submodule_name}_str_image_cache_directory"

    def get_game_image_cache_directory(self, context: bpy.types.Context) -> Path | None:
        prop_name = self.get_game_image_cache_path_prop_name(context)
        path_str = getattr(self, prop_name)
        return Path(path_str) if path_str else None

    def get_cached_image_path(self, context: bpy.types.Context, image_stem: str):
        """Get the path to a cached image file in the image cache directory."""
        image_cache_directory = self.get_game_image_cache_directory(context)
        if not image_cache_directory:
            raise NotADirectoryError("No image cache directory set.")
        image_name = f"{image_stem}{self.bl_image_cache_format.get_suffix()}"
        return image_cache_directory / image_name

    @property
    def bl_image_cache_format(self) -> BlenderImageFormat:
        return BlenderImageFormat(self.image_cache_format)

    def get_mtdbnd(self, operator: LoggingOperator, context: bpy.types.Context) -> MTDBND:
        """Load `MTDBND` from custom path, standard location in game directory, or bundled Soulstruct file.

        Should not be called for games that do not use MTDs. Otherwise, always finds a `MTDBND` or we have an error.
        """
        settings = SoulstructSettings.from_context(context)
        game = settings.game

        if settings.game_config.uses_matbin:
            raise InternalSoulstructBlenderError(f"Active game '{game.name}' does not use MTDs. Should not call this.")

        if is_path_and_file(custom_path := self.get_game_mtdbnd_path(context)):
            return MTDBND.from_path(custom_path)

        # Try to find MTDBND in project or game directory. We know their names from the bundled versions in Soulstruct,
        # but only fall back to those actual bundled files if necessary.
        mtdbnd_names = [
            resource_path.name
            for resource_key, resource_path in game.bundled_resource_paths.items()
            if resource_key.endswith("MTDBND")
        ]

        if settings.prefer_import_from_project:
            labelled_roots = (("project", settings.project_root), ("game", settings.game_root))
        else:
            labelled_roots = (("game", settings.game_root), ("project", settings.project_root))

        mtdbnd = None  # type: MTDBND | None
        for label, root in labelled_roots:
            if not root:
                continue
            for mtdbnd_name in mtdbnd_names:
                dir_mtdbnd_path = root.get_file_path(f"mtd/{mtdbnd_name}")
                if dir_mtdbnd_path.is_file():
                    operator.debug(f"Found MTDBND '{dir_mtdbnd_path.name}' in {label} directory: {dir_mtdbnd_path}")
                    if mtdbnd is None:
                        mtdbnd = MTDBND.from_path(dir_mtdbnd_path)
                    else:
                        mtdbnd |= MTDBND.from_path(dir_mtdbnd_path)
        if mtdbnd is not None:  # found
            return mtdbnd

        operator.info(f"Loading bundled MTDBND for game {game.name}...")
        return MTDBND.from_bundled(game)

    def get_matbinbnd(self, operator: LoggingOperator, context: bpy.types.Context) -> MATBINBND | None:
        """Load `MATBINBND` from custom path, standard location in game directory, or bundled Soulstruct file.

        Should not be called for games that do not use MATBINs. Otherwise, always finds a `MATBINBND` or we have an
        error.
        """

        settings = SoulstructSettings.from_context(context)
        game = settings.game

        if not settings.game_config.uses_matbin:
            raise InternalSoulstructBlenderError(
                f"Active game '{game.name}' does not use MATBINs. Should not call this."
            )

        if is_path_and_file(custom_path := self.get_game_matbinbnd_path(context)):
            return MATBINBND.from_path(custom_path)

        # Try to find MATBINBND in project or game directory.
        matbinbnd_names = [
            resource_path.name
            for resource_key, resource_path in game.bundled_resource_paths.items()
            if resource_key.endswith("MATBINBND")
        ]

        if settings.prefer_import_from_project:
            labelled_roots = (("project", settings.project_root), ("game", settings.game_root))
        else:
            labelled_roots = (("game", settings.game_root), ("project", settings.project_root))

        matbinbnd = None  # type: MATBINBND | None
        for label, root in labelled_roots:
            if not root:
                continue
            for matbinbnd_name in matbinbnd_names:
                dir_matbinbnd_path = root.get_file_path(f"material/{matbinbnd_name}")
                if dir_matbinbnd_path.is_file():
                    operator.info(
                        f"Found MATBINBND '{dir_matbinbnd_path.name}' in {label} directory: {dir_matbinbnd_path}"
                    )
                    if matbinbnd is None:
                        matbinbnd = MATBINBND.from_path(dir_matbinbnd_path)
                    else:
                        matbinbnd |= MATBINBND.from_path(dir_matbinbnd_path)
        if matbinbnd is not None:  # found
            return matbinbnd

        operator.info(f"Loading bundled MATBINBND for game {game.name}...")
        return MATBINBND.from_bundled(game)

    # endregion


# These are cached per-game on first load, which also preserves lazily loaded MATBINs. They can be cleared with
# `clear_cached_matdefs`()`.
_CACHED_MTDBNDS: dict[Game, MTDBND] = {}
_CACHED_MATBINBNDS: dict[Game, MATBINBND] = {}


def get_cached_mtdbnd(operator: LoggingOperator, context: bpy.types.Context) -> MTDBND:
    settings = context.scene.soulstruct_settings
    mat_settings = context.scene.flver_material_settings
    game = settings.game
    if game not in _CACHED_MTDBNDS:
        _CACHED_MTDBNDS[game] = mat_settings.get_mtdbnd(operator, context)
    return _CACHED_MTDBNDS[game]


def get_cached_matbinbnd(operator: LoggingOperator, context: bpy.types.Context) -> MATBINBND:
    settings = context.scene.soulstruct_settings
    mat_settings = context.scene.flver_material_settings
    game = settings.game
    if game not in _CACHED_MATBINBNDS:
        _CACHED_MATBINBNDS[game] = mat_settings.get_matbinbnd(operator, context)
    return _CACHED_MATBINBNDS[game]


def clear_cached_matdefs():
    _CACHED_MTDBNDS.clear()
    _CACHED_MATBINBNDS.clear()
