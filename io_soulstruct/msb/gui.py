from __future__ import annotations

__all__ = [
    "MSBImportExportPanel",
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

    "MSBEventPanel",
    "MSBLightEventPanel",
    "MSBSoundEventPanel",
    "MSBVFXEventPanel",
    "MSBWindEventPanel",
    "MSBTreasureEventPanel",
    "MSBSpawnerEventPanel",
    "MSBMessageEventPanel",
    "MSBObjActEventPanel",
    "MSBSpawnPointEventPanel",
    "MSBMapOffsetEventPanel",
    "MSBNavigationEventPanel",
    "MSBEnvironmentEventPanel",
    "MSBNPCInvasionEventPanel",
]

import typing as tp

import bpy

from io_soulstruct.general.gui import map_stem_box
from io_soulstruct.types import SoulstructType
from .draw_regions import *
from .draw_events import *
from .import_operators import *
from .export_operators import *
from .misc_operators import *
from .properties import *


class MSBImportExportPanel(bpy.types.Panel):
    """Panel for Soulstruct MSB import/export operators."""
    bl_label = "MSB Import/Export"
    bl_idname = "SCENE_PT_msb_import_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MSB"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):

        settings = context.scene.soulstruct_settings

        layout = self.layout
        map_stem_box(layout, settings)

        header, panel = layout.panel("MSB Import Settings", default_closed=True)
        header.label(text="MSB Import Settings")
        if panel:
            msb_import_settings = context.scene.msb_import_settings
            for prop_name in msb_import_settings.__annotations__:
                if prop_name == "part_name_model_filter":
                    panel.label(text="Part Name Model Import Filter:")
                    panel.prop(msb_import_settings, prop_name, text="")
                elif prop_name == "part_name_filter_match_mode":
                    panel.label(text="Part Name Filter Mode:")
                    panel.prop(msb_import_settings, prop_name, text="")
                else:
                    panel.prop(msb_import_settings, prop_name)

        header, panel = layout.panel("FLVER Import Settings", default_closed=True)
        header.label(text="FLVER Import Settings")
        if panel:
            flver_import_settings = context.scene.flver_import_settings
            for prop_name in flver_import_settings.__annotations__:
                panel.prop(flver_import_settings, prop_name)

        header, panel = layout.panel("MSB Export Settings", default_closed=True)
        header.label(text="MSB Export Settings")
        if panel:
            panel.prop(context.scene.soulstruct_settings, "detect_map_from_collection")
            msb_export_settings = context.scene.msb_export_settings
            for prop_name in msb_export_settings.__annotations__:
                if prop_name == "export_nvmdump" and not settings.is_game("DARK_SOULS_DSR"):
                    continue
                if prop_name == "export_navmesh_models" and not settings.is_game_ds1():
                    continue
                if prop_name == "export_collision_models" and not settings.is_game("DARK_SOULS_DSR"):
                    continue
                panel.prop(msb_export_settings, prop_name)

        layout.operator(ImportMSB.bl_idname)
        layout.operator(ExportMSB.bl_idname)


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

        header, panel = self.layout.panel("Event Draw Settings", default_closed=True)
        header.label(text="Event Draw Settings")
        if panel:
            for prop_name in EventDrawSettings.__annotations__:
                panel.prop(context.scene.event_draw_settings, prop_name)


def get_active_part_obj(context) -> bpy.types.Object | None:
    """Retrieve the active object as an MSB Part object, or None if it is not a Part."""
    obj = context.active_object
    if obj is not None and obj.soulstruct_type == SoulstructType.MSB_PART:
        return obj
    return None


def get_active_event_obj(context) -> bpy.types.Object | None:
    """Retrieve the active object as an MSB Event object, or None if it is not a Event."""
    obj = context.active_object
    if obj is not None and obj.soulstruct_type == SoulstructType.MSB_EVENT:
        return obj
    return None


def draw_group_bit_set_prop(
    layout: bpy.types.UILayout, props: bpy.types.PropertyGroup, prefix: str, label: str
) -> set[str]:
    prop_names = [prop for prop in props.__annotations__ if prop.startswith(prefix)]
    if not prop_names:
        return set()
    header, panel = layout.panel(label, default_closed=True)
    header.label(text=label)
    if panel:
        for i, prop in enumerate(sorted(prop_names)):
            # Four 8-bit rows so labels are visible.
            for row_i in range(4):
                row = panel.row()
                for j in range(8):
                    prop_index = row_i * 8 + j
                    true_index = i * 32 + prop_index
                    row.column().prop(props, prop, index=prop_index, text=f"{true_index}")
    return set(prop_names)


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
        prop_names = props.__annotations__.keys()
        handled = set()

        for pre_prop in ("part_subtype", "model", "entity_id"):
            layout.prop(props, pre_prop)
            handled.add(pre_prop)

        handled |= draw_group_bit_set_prop(layout, props, "draw_groups_", "Draw Groups")
        handled |= draw_group_bit_set_prop(layout, props, "display_groups_", "Display Groups")

        # TODO: Option to hide Part supertype properties that are known to be unused for this subtype.
        for prop in prop_names:
            if prop in handled:
                continue
            layout.prop(props, prop)


class _MSBPartSubtypePanelMixin:
    """Base class for MSB Part subtype panels."""

    layout: bpy.types.UILayout

    part_subtype: MSBPartSubtype  # also `Object` property attribute name
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
        prop_names = props.__annotations__.keys()
        handled = set()
        handled |= draw_group_bit_set_prop(layout, props, "navmesh_groups_", "Navmesh Groups")

        for prop in prop_names:
            if prop in handled:
                continue
            layout.prop(props, prop)


class MSBMapPiecePartPanel(bpy.types.Panel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Character fields for active object."""
    bl_label = "MSB Map Piece Settings"
    bl_idname = "OBJECT_PT_msb_map_piece"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    part_subtype = MSBPartSubtype.MapPiece
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

    part_subtype = MSBPartSubtype.Object
    prop_group_type = MSBObjectProps


class MSBCharacterPartPanel(bpy.types.Panel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Character fields for active object."""
    bl_label = "MSB Character Settings"
    bl_idname = "OBJECT_PT_msb_character"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    part_subtype = MSBPartSubtype.Character
    prop_group_type = MSBCharacterProps


class MSBPlayerStartPartPanel(bpy.types.Panel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Character fields for active object."""
    bl_label = "MSB Character Settings"
    bl_idname = "OBJECT_PT_msb_player_start"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    part_subtype = MSBPartSubtype.PlayerStart
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

    part_subtype = MSBPartSubtype.Collision
    prop_group_type = MSBCollisionProps


class MSBNavmeshPartPanel(bpy.types.Panel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Navmesh fields for active object."""
    bl_label = "MSB Navmesh Settings"
    bl_idname = "OBJECT_PT_msb_navmesh"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    part_subtype = MSBPartSubtype.Navmesh
    prop_group_type = MSBNavmeshProps


class MSBConnectCollisionPartPanel(bpy.types.Panel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Collision fields for active object."""
    bl_label = "MSB Connect Collision Settings"
    bl_idname = "OBJECT_PT_msb_connect_collision"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    part_subtype = MSBPartSubtype.ConnectCollision
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


class MSBEventPanel(bpy.types.Panel):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Event fields for active object."""
    bl_label = "MSB Event Settings"
    bl_idname = "OBJECT_PT_msb_event"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        return get_active_event_obj(context) is not None

    def draw(self, context):
        layout = self.layout

        obj = get_active_event_obj(context)
        if obj is None:
            # Should already fail Panel poll.
            layout.label(text="No active MSB Event.")
            return

        props = obj.MSB_EVENT
        prop_names = props.__annotations__.keys()
        handled = set()

        for pre_prop in ("event_subtype", "entity_id"):
            layout.prop(props, pre_prop)
            handled.add(pre_prop)

        # TODO: Option to hide Event supertype properties that are known to be unused for this subtype.
        for prop in prop_names:
            if prop in handled:
                continue
            layout.prop(props, prop)


class _MSBEventSubtypePanelMixin:
    """Base class for MSB Event subtype panels."""

    layout: bpy.types.UILayout

    event_subtype: MSBEventSubtype  # also `Object` property attribute name
    prop_group_type: tp.Type[bpy.types.PropertyGroup]

    @classmethod
    def poll(cls, context):
        obj = get_active_part_obj(context)
        return obj is not None and obj.MSB_EVENT.event_subtype == cls.event_subtype

    def draw(self, context):
        layout = self.layout

        obj = get_active_event_obj(context)
        if obj is None or obj.MSB_EVENT.event_subtype != self.event_subtype:
            # Should already fail Panel poll.
            layout.label(text=f"No active MSB {self.event_subtype}.")
            return

        # noinspection PyTypeChecker
        props = getattr(obj, self.event_subtype.value)
        prop_names = props.__annotations__.keys()
        for prop in prop_names:
            layout.prop(props, prop)


class MSBLightEventPanel(bpy.types.Panel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate Light fields for active object."""
    bl_label = "MSB Light Settings"
    bl_idname = "OBJECT_PT_msb_light"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    event_subtype = MSBEventSubtype.Light
    prop_group_type = MSBLightEventProps


class MSBSoundEventPanel(bpy.types.Panel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate Sound fields for active object."""
    bl_label = "MSB Sound Settings"
    bl_idname = "OBJECT_PT_msb_sound"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    event_subtype = MSBEventSubtype.Sound
    prop_group_type = MSBSoundEventProps


class MSBVFXEventPanel(bpy.types.Panel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate VFX fields for active object."""
    bl_label = "MSB VFX Settings"
    bl_idname = "OBJECT_PT_msb_vfx"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    event_subtype = MSBEventSubtype.VFX
    prop_group_type = MSBVFXEventProps


class MSBWindEventPanel(bpy.types.Panel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate Wind fields for active object."""
    bl_label = "MSB Wind Settings"
    bl_idname = "OBJECT_PT_msb_wind"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    event_subtype = MSBEventSubtype.Wind
    prop_group_type = MSBWindEventProps


class MSBTreasureEventPanel(bpy.types.Panel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate Treasure fields for active object."""
    bl_label = "MSB Treasure Settings"
    bl_idname = "OBJECT_PT_msb_treasure"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    event_subtype = MSBEventSubtype.Treasure
    prop_group_type = MSBTreasureEventProps


class MSBSpawnerEventPanel(bpy.types.Panel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate Spawner fields for active object."""
    bl_label = "MSB Spawner Settings"
    bl_idname = "OBJECT_PT_msb_spawner"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    event_subtype = MSBEventSubtype.Spawner
    prop_group_type = MSBSpawnerEventProps


class MSBMessageEventPanel(bpy.types.Panel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate Message fields for active object."""
    bl_label = "MSB Message Settings"
    bl_idname = "OBJECT_PT_msb_message"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    event_subtype = MSBEventSubtype.Message
    prop_group_type = MSBMessageEventProps


class MSBObjActEventPanel(bpy.types.Panel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate ObjAct fields for active object."""
    bl_label = "MSB ObjAct Settings"
    bl_idname = "OBJECT_PT_msb_obj_act"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    event_subtype = MSBEventSubtype.ObjAct
    prop_group_type = MSBObjActEventProps


class MSBSpawnPointEventPanel(bpy.types.Panel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate Spawn Point fields for active object."""
    bl_label = "MSB Spawn Point Settings"
    bl_idname = "OBJECT_PT_msb_spawn_point"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    event_subtype = MSBEventSubtype.SpawnPoint
    prop_group_type = MSBSpawnPointEventProps


class MSBMapOffsetEventPanel(bpy.types.Panel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate Map Offset fields for active object."""
    bl_label = "MSB Map Offset Settings"
    bl_idname = "OBJECT_PT_msb_map_offset"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    event_subtype = MSBEventSubtype.MapOffset
    prop_group_type = MSBMapOffsetEventProps


class MSBNavigationEventPanel(bpy.types.Panel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate Navigation fields for active object."""
    bl_label = "MSB Navigation Settings"
    bl_idname = "OBJECT_PT_msb_navigation"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    event_subtype = MSBEventSubtype.Navigation
    prop_group_type = MSBNavigationEventProps


class MSBEnvironmentEventPanel(bpy.types.Panel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate Environment fields for active object."""
    bl_label = "MSB Environment Settings"
    bl_idname = "OBJECT_PT_msb_environment"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    event_subtype = MSBEventSubtype.Environment
    prop_group_type = MSBEnvironmentEventProps


class MSBNPCInvasionEventPanel(bpy.types.Panel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate NPC Invasion fields for active object."""
    bl_label = "MSB NPC Invasion Settings"
    bl_idname = "OBJECT_PT_msb_npc_invasion"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    event_subtype = MSBEventSubtype.NPCInvasion
    prop_group_type = MSBNPCInvasionEventProps

# endregion
