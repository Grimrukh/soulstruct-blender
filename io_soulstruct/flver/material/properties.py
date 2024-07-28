from __future__ import annotations

__all__ = [
    "FLVERGXItemProps",
    "FLVERMaterialProps",
]

import ast

import bpy

from soulstruct.base.models.flver.material import GXItem


class FLVERGXItemProps(bpy.types.PropertyGroup):
    """Extension properties for FLVER `GXItem` collection on `FLVERMaterialProps`."""
    category: bpy.props.StringProperty(
        name="Category",
        description="Category of this GX item",
        default="",
    )
    index: bpy.props.IntProperty(
        name="Index",
        description="Index of this GX item",
        default=0,
    )
    data: bpy.props.StringProperty(
        name="Data",
        description="Raw data of this GX item (Python bytes literal)",
        default="b\"\"",
    )

    def from_gx_item(self, gx_item: GXItem):
        try:
            self.category = gx_item.category.decode()
        except UnicodeDecodeError:
            self.category = ""
        self.index = gx_item.index
        self.data = repr(gx_item.data)

    def to_gx_item(self) -> GXItem:
        data = self.get_data_bytes()
        gx_item = GXItem(
            category=self.category.encode(),
            index=self.index,
            size=len(data) + 12,
        )
        gx_item.data = data
        return gx_item

    def get_data_bytes(self) -> bytes:
        return ast.literal_eval(self.data)


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

    sampler_prefix: bpy.props.StringProperty(
        name="Sampler Prefix",
        description="Optional prefix for sampler names in this material to make shader nodes nicer",
        default="",
    )
