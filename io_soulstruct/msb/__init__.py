from __future__ import annotations

__all__ = [
    "MSBImportSettings",
    "ImportMSBMapPiece",
    "ImportAllMSBMapPieces",
    "ImportMSBMapCollision",
    "ImportAllMSBMapCollisions",
    "ImportMSBNavmesh",
    "ImportAllMSBNavmeshes",
    "ImportMSBCharacter",
    "ImportAllMSBCharacters",
    "ImportMSBObject",
    "ImportAllMSBObjects",
    "ImportMSBAsset",
    "ImportAllMSBAssets",
    "ImportMSBPoint",
    "ImportMSBVolume",
    "ImportAllMSBPoints",
    "ImportAllMSBVolumes",

    "RegionDrawSettings",
    "draw_region_volumes",

    "MSBExportSettings",
    "ExportMSBMapPieces",
    "ExportMSBCollisions",
    "ExportMSBNavmeshes",
    "ExportCompleteMapNavigation",

    "CreateMSBPart",
    "DuplicateMSBPartModel",

    "MSBPartProps",
    "MSBObjectProps",
    "MSBAssetProps",
    "MSBCharacterProps",
    "MSBCollisionProps",
    "MSBNavmeshProps",
    "MSBConnectCollisionProps",
    "MSBRegionProps",

    "MSBImportPanel",
    "MSBExportPanel",
    "MSBToolsPanel",
    "MSBPartPanel",
    "MSBObjectPartPanel",
    "MSBCharacterPartPanel",
    "MSBCollisionPartPanel",
    "MSBNavmeshPartPanel",
    "MSBRegionPanel",
]

import typing as tp

import bpy

from io_soulstruct.types import SoulstructType
from .msb_import import *
from .msb_export import *
from .draw_regions import *
from .misc_operators import *
from .properties import *


class MSBToolsPanel(bpy.types.Panel):
    """Panel for Soulstruct MSB tool settings/operators."""
    bl_label = "MSB Tools"
    bl_idname = "SCENE_PT_msb_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MSB"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        region_draw_box = self.layout.box()
        region_draw_box.label(text="Region Draw Settings")
        for prop in RegionDrawSettings.__annotations__:
            region_draw_box.prop(context.scene.region_draw_settings, prop)


def get_active_part_obj(context) -> bpy.types.Object | None:
    """Retrieve the active object as an MSB Part object, or None if it is not a Part."""
    obj = context.active_object
    if obj is not None and obj.soulstruct_type == SoulstructType.MSB_PART:
        return obj
    return None


class MSBPartPanel(bpy.types.Panel):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Part fields for active object."""
    bl_label = "MSB Part Settings"
    bl_idname = "OBJECT_PT_msb_part"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        return get_active_part_obj(context) is not None

    def draw(self, context):
        layout = self.layout

        obj = get_active_part_obj(context)
        if obj is None:
            # Should already fail Panel poll.
            layout.label(text="No active MSB Part.")
            return

        props = obj.msb_part_props
        for prop in MSBPartProps.__annotations__:
            if prop.startswith("draw_groups_"):
                if prop.endswith("_0"):
                    layout.label(text="Draw Groups [0 to 127]")
                layout.prop(props, prop, text="")
            elif prop.startswith("display_groups_"):
                if prop.endswith("_0"):
                    layout.label(text="Display Groups [0 to 127]")
                layout.prop(props, prop, text="")
            else:                
                layout.prop(props, prop)


class _MSBPartSubtypePanelMixin:
    """Base class for MSB Part subtype panels."""
    
    layout: bpy.types.UILayout    
    
    part_subtype: MSBPartSubtype
    prop_group_type: tp.Type[bpy.types.PropertyGroup]
    prop_attr_name: str

    @classmethod
    def poll(cls, context):
        obj = get_active_part_obj(context)
        return obj is not None and obj.msb_part_props.part_subtype == cls.part_subtype
    
    def draw(self, context):
        layout = self.layout

        obj = get_active_part_obj(context)
        if obj is None or obj.msb_part_props.part_subtype != self.part_subtype:
            # Should already fail Panel poll.
            layout.label(text=f"No active MSB {self.part_subtype}.")
            return
        
        props = getattr(obj, self.prop_attr_name)

        for prop in self.prop_group_type.__annotations__:
            if prop.startswith("navmesh_groups_"):
                # Only property across subtypes that requires special display rules.
                if prop.endswith("_0"):
                    layout.label(text="Navmesh Groups [0 to 127]")
                layout.prop(props, prop, text="")            
            else:
                layout.prop(props, prop)


class MSBObjectPartPanel(bpy.types.Panel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Object fields for active object."""
    bl_label = "MSB Object Settings"
    bl_idname = "OBJECT_PT_msb_object"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    
    part_subtype = MSBPartSubtype.OBJECT
    prop_group_type = MSBObjectProps
    prop_attr_name = "msb_object_props"


class MSBCharacterPartPanel(bpy.types.Panel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Character fields for active object."""
    bl_label = "MSB Character Settings"
    bl_idname = "OBJECT_PT_msb_character"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    
    part_subtype = MSBPartSubtype.CHARACTER
    prop_group_type = MSBCharacterProps
    prop_attr_name = "msb_character_props"


class MSBPlayerStartPartPanel(bpy.types.Panel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Character fields for active object."""
    bl_label = "MSB Character Settings"
    bl_idname = "OBJECT_PT_msb_character"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    part_subtype = MSBPartSubtype.PLAYER_START
    prop_group_type = None
    prop_attr_name = ""

    def draw(self, context):
        layout = self.layout
        layout.label(text="No additional properties.")


class MSBCollisionPartPanel(bpy.types.Panel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Collision fields for active object."""
    bl_label = "MSB Collision Settings"
    bl_idname = "OBJECT_PT_msb_collision"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    
    part_subtype = MSBPartSubtype.COLLISION
    prop_group_type = MSBCollisionProps
    prop_attr_name = "msb_collision_props"


class MSBConnectCollisionPartPanel(bpy.types.Panel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Collision fields for active object."""
    bl_label = "MSB Connect Collision Settings"
    bl_idname = "OBJECT_PT_msb_connect_collision"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    part_subtype = MSBPartSubtype.CONNECT_COLLISION
    prop_group_type = MSBConnectCollisionProps
    prop_attr_name = "msb_connect_collision_props"
    

class MSBNavmeshPartPanel(bpy.types.Panel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Navmesh fields for active object."""
    bl_label = "MSB Navmesh Settings"
    bl_idname = "OBJECT_PT_msb_navmesh"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    
    part_subtype = MSBPartSubtype.NAVMESH
    prop_group_type = MSBNavmeshProps
    prop_attr_name = "msb_navmesh_props"


class MSBRegionPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window."""
    bl_label = "MSB Region Settings"
    bl_idname = "OBJECT_PT_hello"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.soulstruct_type == "MSB_REGION"

    def draw(self, context):
        layout = self.layout

        obj = context.object
        if obj is None or obj.soulstruct_type != "MSB_REGION":
            # Should already fail poll.
            layout.label(text="No active MSB Region.")
            return

        props = obj.msb_region_props
        for prop in MSBRegionProps.__annotations__:
            layout.prop(props, prop)
