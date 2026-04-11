from __future__ import annotations

__all__ = [
    "FLVERGXItemUIList",
    "FLVERMaterialPropsPanel",
    "FLVERMaterialToolsPanel",
]

import typing as tp

import bpy

from ...base.register import io_soulstruct_class
from ...bpy_base.panel import SoulstructPanel
from ...types import ObjectType, SoulstructType
from ...flver.image.import_operators import ImportTextures
from ...flver.image.misc_operators import FindMissingTexturesInImageCache

from .operators import *

if tp.TYPE_CHECKING:
    from .properties import FLVERGXItemProps


def is_flver_or_flver_msb_part(obj: bpy.types.Object) -> bool:
    if obj.soulstruct_type == SoulstructType.FLVER:
        return True
    if obj.soulstruct_type == SoulstructType.MSB_PART and obj.MSB_PART.entry_subtype_enum.is_flver():
        return True
    return False


@io_soulstruct_class
class FLVERGXItemUIList(bpy.types.UIList):
    """Draws a list of `GXItem` elements."""

    bl_idname = "OBJECT_UL_flver_gx_item"

    def draw_item(
        self,
        context: bpy.types.Context,
        layout: bpy.types.UILayout,
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


@io_soulstruct_class
class FLVERMaterialPropsPanel(SoulstructPanel):
    """FLVER Material properties, available on all Blender materials."""
    bl_label = "FLVER Material Properties"
    bl_idname = "MATERIAL_PT_flver_material"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj is None:
            return False
        # Show for FLVERs or MSB FLVER instances only.
        if not is_flver_or_flver_msb_part(obj):
            return False
        return obj.active_material is not None

    def draw(self, context):
        layout = self.layout

        # Get active material on active object.
        obj = context.active_object
        if obj is None or obj.type != ObjectType.MESH:
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
                    listtype_name=FLVERGXItemUIList.bl_idname,
                    list_id="",
                    dataptr=material.FLVER_MATERIAL,
                    propname="gx_items",
                    active_dataptr=material.FLVER_MATERIAL,
                    active_propname="gx_item_index",
                )
                col = row.column(align=True)
                col.operator(AddMaterialGXItem.bl_idname, icon='ADD', text="")
                col.operator(RemoveMaterialGXItem.bl_idname, icon='REMOVE', text="")
            elif prop == "shader_name":
                # Read-only.
                layout.label(text=f"Shader: {props.shader_name}")
            else:
                # Standard public property.
                layout.prop(props, prop)

        label_done = False
        for key, value in material.items():
            if key.startswith("Path["):
                if not label_done:
                    layout.label(text="Texture Overrides:")
                    label_done = True
                key = key[5:-1]
                layout.label(text=f"{key}: {value}")


@io_soulstruct_class
class FLVERMaterialToolsPanel(SoulstructPanel):
    bl_label = "FLVER Material Tools"
    bl_idname = "SCENE_PT_flver_material_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        header, panel = layout.panel("Material Tools", default_closed=True)
        header.label(text="Material Tools")
        if panel:
            material_tool_settings = context.scene.material_tool_settings
            panel.prop(material_tool_settings, "use_model_stem_in_material_name")
            panel.prop(material_tool_settings, "clean_up_identical")
            panel.operator(AutoRenameMaterials.bl_idname)
            panel.operator(MergeFLVERMaterials.bl_idname)
            panel.operator(RegenerateFLVERMaterialShaders.bl_idname)
            active_object = context.active_object
            if active_object and active_object.active_material:
                panel.label(text=active_object.active_material.name)
                panel.prop(material_tool_settings, "albedo_image")
                panel.operator(SetMaterialTexture0.bl_idname)
                panel.operator(SetMaterialTexture1.bl_idname)
            else:
                panel.label(text="No Material Selected.")

        header, panel = layout.panel("Texture Tools", default_closed=True)
        header.label(text="Texture Tools")
        if panel:
            panel.label(text="Textures:")
            panel.operator(ImportTextures.bl_idname)
            panel.operator(FindMissingTexturesInImageCache.bl_idname)
            # panel.operator(ExportTexturesIntoBinder.bl_idname)  # TODO: not yet functional
