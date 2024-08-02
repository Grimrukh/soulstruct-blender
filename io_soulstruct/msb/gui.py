from __future__ import annotations

__all__ = [
    "MSBToolsPanel",
    "MSBPartPanel",
    "MSBMapPiecePartPanel",
    "MSBObjectPartPanel",
    "MSBCharacterPartPanel",
    "MSBPlayerStartPartPanel",
    "MSBCollisionPartPanel",
    "MSBNavmeshPartPanel",
    "MSBConnectCollisionPartPanel",
    "MSBRegionPanel",
]

import typing as tp

import bpy

from io_soulstruct.types import SoulstructType
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
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        self.layout.operator(EnableSelectedNames.bl_idname, icon='HIDE_OFF')
        self.layout.operator(DisableSelectedNames.bl_idname, icon='HIDE_ON')
        self.layout.operator(CreateMSBPart.bl_idname, icon='MESH_CUBE')
        self.layout.operator(DuplicateMSBPartModel.bl_idname, icon='DUPLICATE')

        header, panel = self.layout.panel("Region Draw Settings", default_closed=True)
        header.label(text="Region Draw Settings")
        if panel:
            for prop_name in RegionDrawSettings.__annotations__:
                panel.prop(context.scene.region_draw_settings, prop_name)


def get_active_part_obj(context) -> bpy.types.Object | None:
    """Retrieve the active object as an MSB Part object, or None if it is not a Part."""
    obj = context.active_object
    if obj is not None and obj.soulstruct_type == SoulstructType.MSB_PART:
        return obj
    return None


# region Property Panels

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

        props = obj.MSB_PART
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

    part_subtype: MSBPartSubtype  # also `Object` propery attribute name
    prop_group_type: tp.Type[bpy.types.PropertyGroup]

    @classmethod
    def poll(cls, context):
        obj = get_active_part_obj(context)
        return obj is not None and obj.MSB_PART.part_subtype == cls.part_subtype

    def draw(self, context):
        layout = self.layout

        obj = get_active_part_obj(context)
        if obj is None or obj.MSB_PART.part_subtype != self.part_subtype:
            # Should already fail Panel poll.
            layout.label(text=f"No active MSB {self.part_subtype}.")
            return

        # noinspection PyTypeChecker
        props = getattr(obj, self.part_subtype.value)

        for prop in self.prop_group_type.__annotations__:
            if prop.startswith("navmesh_groups_"):
                # Only property across subtypes that requires special display rules.
                if prop.endswith("_0"):
                    layout.label(text="Navmesh Groups [0 to 127]")
                layout.prop(props, prop, text="")
            else:
                layout.prop(props, prop)


class MSBMapPiecePartPanel(bpy.types.Panel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Character fields for active object."""
    bl_label = "MSB Map Piece Settings"
    bl_idname = "OBJECT_PT_msb_map_piece"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    part_subtype = MSBPartSubtype.MAP_PIECE
    prop_group_type = None

    def draw(self, context):
        layout = self.layout
        layout.label(text="No additional properties.")


class MSBObjectPartPanel(bpy.types.Panel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Object fields for active object."""
    bl_label = "MSB Object Settings"
    bl_idname = "OBJECT_PT_msb_object"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    part_subtype = MSBPartSubtype.OBJECT
    prop_group_type = MSBObjectProps


class MSBCharacterPartPanel(bpy.types.Panel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Character fields for active object."""
    bl_label = "MSB Character Settings"
    bl_idname = "OBJECT_PT_msb_character"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    part_subtype = MSBPartSubtype.CHARACTER
    prop_group_type = MSBCharacterProps


class MSBPlayerStartPartPanel(bpy.types.Panel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Character fields for active object."""
    bl_label = "MSB Character Settings"
    bl_idname = "OBJECT_PT_msb_player_start"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    part_subtype = MSBPartSubtype.PLAYER_START
    prop_group_type = None

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


class MSBNavmeshPartPanel(bpy.types.Panel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Navmesh fields for active object."""
    bl_label = "MSB Navmesh Settings"
    bl_idname = "OBJECT_PT_msb_navmesh"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    part_subtype = MSBPartSubtype.NAVMESH
    prop_group_type = MSBNavmeshProps


class MSBConnectCollisionPartPanel(bpy.types.Panel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Collision fields for active object."""
    bl_label = "MSB Connect Collision Settings"
    bl_idname = "OBJECT_PT_msb_connect_collision"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    part_subtype = MSBPartSubtype.CONNECT_COLLISION
    prop_group_type = MSBConnectCollisionProps


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

        props = obj.MSB_REGION
        for prop in props.__annotations__:
            layout.prop(props, prop)

# endregion
