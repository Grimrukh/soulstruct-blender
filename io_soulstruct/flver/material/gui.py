from __future__ import annotations

__all__ = [
    "OBJECT_UL_flver_gx_item",
    "FLVERMaterialPropsPanel",
]

import typing as tp

import bpy

from .misc_operators import AddMaterialGXItem, RemoveMaterialGXItem

if tp.TYPE_CHECKING:
    from .properties import FLVERGXItemProps


class OBJECT_UL_flver_gx_item(bpy.types.UIList):
    """Draws a list of `GXItem` elements."""

    def draw_item(
        self,
        context,
        layout,
        data,
        item: FLVERGXItemProps,
        icon,
        active_data,
        active_property,
        index=0,
        flt_flag=0,
    ):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            # Split (0.2, 0.2, 0.6).
            split = row.split(factor=0.2)
            split.prop(item, "category", text="", emboss=True)
            subsplit = split.split(factor=0.25)
            subsplit.prop(item, "index", text="", emboss=True)
            subsplit.prop(item, "data", text="", emboss=True)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            split = layout.split(factor=0.2)
            split.prop(item, "category", text="", emboss=True)
            subsplit = split.split(factor=0.25)
            subsplit.prop(item, "index", text="", emboss=True)
            subsplit.prop(item, "data", text="", emboss=True)


class FLVERMaterialPropsPanel(bpy.types.Panel):
    """FLVER Material properties, available on all Blender materials."""
    bl_label = "FLVER Material Settings"
    bl_idname = "MATERIAL_PT_flver_material"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    def draw(self, context):
        layout = self.layout

        # Get active material on active object.
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            layout.label(text="No active mesh object.")
            return
        material = obj.active_material
        props = material.FLVER_MATERIAL

        for prop in props.__annotations__:
            if prop == "gx_item_index":
                continue  # internal use
            elif prop == "gx_items":
                layout.label(text="GX Items:")
                row = layout.row()
                row.template_list(
                    listtype_name=OBJECT_UL_flver_gx_item.__name__,
                    list_id="",
                    dataptr=material.FLVER_MATERIAL,
                    propname="gx_items",
                    active_dataptr=material.FLVER_MATERIAL,
                    active_propname="gx_item_index",
                )
                col = row.column(align=True)
                col.operator(AddMaterialGXItem.bl_idname, icon='ADD', text="")
                col.operator(RemoveMaterialGXItem.bl_idname, icon='REMOVE', text="")
            else:
                # Standard public property.
                layout.prop(props, prop)
