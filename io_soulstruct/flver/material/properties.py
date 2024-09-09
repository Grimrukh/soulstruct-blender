from __future__ import annotations

__all__ = [
    "FLVERGXItemProps",
    "FLVERMaterialProps",
]

import bpy

from soulstruct.base.models.flver.material import GXItem


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


class FLVERMaterialProps(bpy.types.PropertyGroup):
    """Extension properties for Blender materials that represent FLVER materials.

    In Blender, materials also store desired FLVER submesh settings -- that is, there may be multiple materials that are
    identical except for FLVER submesh/face set settings like backface culling. These settings are stored here.
    """

    flags: bpy.props.IntProperty(
        name="Flags",
        description="Material flags",
        default=0,
    )
    mat_def_path: bpy.props.StringProperty(
        name="Mat Def Path",
        description="Material definition path (MATBIN name in Elden Ring, MTD name before that). Extension is ignored "
                    "by the game and always replaced with '.matbin' (Elden Ring) or '.mtd' (before Elden Ring)",
        default="",
    )
    unk_x18: bpy.props.IntProperty(
        name="Unk x18",
        description="Unknown integer at material offset 0x18",
        default=0,
    )
    is_bind_pose: bpy.props.BoolProperty(
        name="Is Bind Pose [Submesh]",
        description="If enabled, submesh using this material is a rigged submesh. Typically disabled for Map Piece "
                    "FLVERs and enabled for everything else",
        default=False,
    )
    default_bone_index: bpy.props.IntProperty(
        name="Default Bone Index [Submesh]",
        description="Index of default bone for this submesh (if applicable). Sometimes junk in vanilla FLVERs",
        default=-1,
    )
    face_set_count: bpy.props.IntProperty(
        name="Face Set Count [Submesh]",
        description="Number of face sets in submesh using this material. This is NOT a real FLVER property, but tells "
                    "Blender how many duplicate FLVER face sets to make for this submesh. Typically used only for Map "
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
