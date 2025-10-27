from __future__ import annotations

__all__ = [
    "MSBImportPanel",
    "MSBExportPanel",
    "MSBToolsPanel",

    "MSBPartPanel",
    "MSBMapPiecePartPanel",
    "MSBObjectPartPanel",
    "MSBCharacterPartPanel",
    "MSBPlayerStartPartPanel",
    "MSBCollisionPartPanel",
    "MSBProtobossPartPanel",
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

from soulstruct.base.maps.msb.region_shapes import RegionShapeType

from soulstruct.blender.types import SoulstructType
from soulstruct.blender.bpy_base import SoulstructPanel, SoulstructPropertyGroup
from .import_operators import *
from .export_operators import *
from .misc_operators import *
from .properties import *
from .properties import MSBProtobossProps


class MSBImportPanel(SoulstructPanel):
    """Panel for Soulstruct MSB import operators."""
    bl_label = "MSB Import"
    bl_idname = "SCENE_PT_msb_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MSB"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):

        layout = self.layout
        self.draw_active_map(context, layout)

        # MSB and FLVER import settings are drawn by operator property dialogs.

        self.maybe_draw_map_import_operator(context, ImportMapMSB.bl_idname, layout)
        layout.operator(ImportAnyMSB.bl_idname)


class MSBExportPanel(SoulstructPanel):
    """Panel for Soulstruct MSB export operators."""
    bl_label = "MSB Export"
    bl_idname = "SCENE_PT_msb_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MSB"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        if not ExportMapMSB.poll(context):
            layout.label(text="Select an MSB Collection.")
            return

        settings = context.scene.soulstruct_settings

        layout.prop(settings, "auto_detect_export_map")
        if settings.auto_detect_export_map:
            self.draw_detected_map(context, layout, use_latest_version=True, detect_from_collection=True)
        else:
            self.draw_active_map(context, layout)

        self.maybe_draw_export_operator(context, ExportMapMSB.bl_idname, layout)
        layout.operator(ExportAnyMSB.bl_idname)


class MSBToolsPanel(SoulstructPanel):
    """Panel for Soulstruct MSB tool settings/operators."""
    bl_label = "MSB Tools"
    bl_idname = "SCENE_PT_msb_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MSB"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.operator(FindMSBParts.bl_idname, icon='VIEWZOOM')
        layout.operator(FindEntityID.bl_idname, icon='VIEWZOOM')
        layout.operator(EnableSelectedNames.bl_idname, icon='HIDE_OFF')
        layout.operator(DisableSelectedNames.bl_idname, icon='HIDE_ON')
        layout.operator(CreateMSBPart.bl_idname, icon='MESH_CUBE')
        layout.operator(CreateMSBRegion.bl_idname, icon='MESH_CUBE')
        layout.operator(CreateMSBEnvironmentEvent.bl_idname, icon='MESH_CUBE')
        layout.operator(DuplicateMSBPartModel.bl_idname, icon='DUPLICATE')
        layout.operator(BatchSetPartGroups.bl_idname, icon='MODIFIER')
        layout.operator(CopyDrawGroups.bl_idname, icon='MODIFIER')
        layout.operator(ApplyPartTransformToModel.bl_idname, icon='MODIFIER')
        layout.operator(CreateConnectCollision.bl_idname, icon='MODIFIER')

        event_box = layout.box()
        event_box.label(text="Event Coloring:")
        split = event_box.row().split(factor=0.25)
        split.column().label(text="Color:")
        split.column().prop(context.scene.msb_tool_settings, "event_color", text="")
        event_box.prop(context.scene.msb_tool_settings, "event_color_type", text="Type")
        event_box.prop(context.scene.msb_tool_settings, "event_color_active_collection_only")
        event_box.operator(ColorMSBEvents.bl_idname, icon='COLOR')

        header, panel = layout.panel("Region Draw Settings", default_closed=True)
        header.label(text="Region Draw Settings")
        if panel:
            layout.prop(context.scene.region_draw_settings, "draw_point_axes")
            panel.prop(context.scene.region_draw_settings, "point_radius")
            panel.prop(context.scene.region_draw_settings, "line_width")


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


def bit_set_prop(
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

class MSBPartPanel(SoulstructPanel):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Part fields for active object."""
    bl_label = "MSB Part Settings"
    bl_idname = "OBJECT_PT_msb_part"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context) -> bool:
        return get_active_part_obj(context) is not None

    def draw(self, context):
        layout = self.layout

        obj = get_active_part_obj(context)
        if obj is None:
            # Should already fail Panel poll.
            layout.label(text="No active MSB Part.")
            return

        props = obj.MSB_PART
        prop_names = props.get_game_prop_names(context)
        handled = set()

        # First, we draw the custom transform operators. (Also draw current custom transform, if present.)
        if obj.parent and obj.parent.type == "ARMATURE" and obj.parent.animation_data:
            box = layout.box()
            box.label(text="MSB Part is animated. Stored MSB Transform:")
            for label, prop in (
                    ("Position", '["MSB Translate"]'),
                    ("Rotation", '["MSB Rotate"]'),
                    ("Scale", '["MSB Scale"]'),
            ):
                row = box.row()
                row.prop(obj, prop, text=label)
                row.enabled = False
                # try:
                #     vector = obj[prop]  # or Euler, technically
                #     prop_str = f"{label}: ({vector[0]:.2f}, {vector[1]:.2f}, {vector[2]:.2f})"
                # except KeyError:
                #     prop_str = f"{label}: <MISSING>"
                # box.label(text=prop_str)
            box.operator(RestoreActivePartInitialTransform.bl_idname, text="Restore + Clear Animation")
            box.operator(UpdateActiveMSBPartInitialTransform.bl_idname, text="Update Stored Transform")

        for pre_prop in ("entry_subtype", "model", "entity_id"):
            layout.prop(props, pre_prop)
            handled.add(pre_prop)

        handled |= bit_set_prop(layout, props, "draw_groups_", "Draw Groups")
        handled |= bit_set_prop(layout, props, "display_groups_", "Display Groups")

        header, panel = layout.panel("DrawParam IDs", default_closed=True)
        header.label(text="DrawParam IDs")
        if panel:
            for prop_name in obj.MSB_PART.DRAW_PARAM_PROP_NAMES:
                panel.prop(props, prop_name)
        handled |= set(obj.MSB_PART.DRAW_PARAM_PROP_NAMES)

        header, panel = layout.panel("Other Draw Settings", default_closed=True)
        header.label(text="Other Draw Settings")
        if panel:
            for prop_name in obj.MSB_PART.OTHER_DRAW_PROP_NAMES:
                panel.prop(props, prop_name)
        handled |= set(obj.MSB_PART.OTHER_DRAW_PROP_NAMES)

        # TODO: Option to hide Part supertype properties that are known to be unused for this subtype.
        for prop in prop_names:
            if prop in handled:
                continue
            layout.prop(props, prop)


class _MSBPartSubtypePanelMixin:
    """Base class for MSB Part subtype panels."""

    layout: bpy.types.UILayout

    PART_SUBTYPE: tp.ClassVar[BlenderMSBPartSubtype]  # also `Object` property attribute name
    PROP_GROUP_TYPE: tp.ClassVar[type[bpy.types.PropertyGroup]]

    @classmethod
    def poll(cls, context) -> bool:
        obj = get_active_part_obj(context)
        return obj is not None and obj.MSB_PART.entry_subtype == cls.PART_SUBTYPE

    def draw(self, context):
        layout = self.layout

        obj = get_active_part_obj(context)
        if obj is None or obj.MSB_PART.entry_subtype != self.PART_SUBTYPE:
            # Should already fail Panel poll.
            layout.label(text=f"No active MSB {self.PART_SUBTYPE}.")
            return

        props = getattr(obj, self.PART_SUBTYPE.value)  # type: SoulstructPropertyGroup
        prop_names = props.get_game_prop_names(context)
        if not prop_names:
            layout.label(text="No additional properties.")
            return

        for prop in prop_names:
            layout.prop(props, prop)


class MSBMapPiecePartPanel(SoulstructPanel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Character fields for active object."""
    bl_label = "MSB Map Piece Settings"
    bl_idname = "OBJECT_PT_msb_map_piece"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    PART_SUBTYPE = BlenderMSBPartSubtype.MapPiece
    PROP_GROUP_TYPE = None

    def draw(self, context):
        layout = self.layout
        layout.label(text="No additional properties.")


class MSBObjectPartPanel(SoulstructPanel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Object fields for active object."""
    bl_label = "MSB Object Settings"
    bl_idname = "OBJECT_PT_msb_object"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    PART_SUBTYPE = BlenderMSBPartSubtype.Object
    PROP_GROUP_TYPE = MSBObjectProps


class MSBCharacterPartPanel(SoulstructPanel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Character fields for active object."""
    bl_label = "MSB Character Settings"
    bl_idname = "OBJECT_PT_msb_character"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    PART_SUBTYPE = BlenderMSBPartSubtype.Character
    PROP_GROUP_TYPE = MSBCharacterProps

    def draw(self, context):
        layout = self.layout

        obj = get_active_part_obj(context)
        if obj is None or obj.MSB_PART.entry_subtype != self.PART_SUBTYPE:
            # Should already fail Panel poll.
            layout.label(text=f"No active MSB {self.PART_SUBTYPE}.")
            return

        props = getattr(obj, self.PART_SUBTYPE.value)  # type: SoulstructPropertyGroup
        prop_names = props.get_game_prop_names(context)

        header, panel = layout.panel("Basic Settings", default_closed=False)
        header.label(text="Basic Settings")
        for prop_name in obj.MSB_CHARACTER.BASIC_SETTINGS:
            if prop_name not in prop_names:
                continue
            prop_names.remove(prop_name)
            if panel:
                panel.prop(props, prop_name)

        header, panel = layout.panel("Patrol Settings", default_closed=True)
        header.label(text="Patrol Settings")
        for prop_name in obj.MSB_CHARACTER.PATROL_SETTINGS:
            if prop_name not in prop_names:
                continue
            prop_names.remove(prop_name)
            if panel:
                panel.prop(props, prop_name)

        header, panel = layout.panel("Advanced Settings", default_closed=True)
        header.label(text="Advanced Settings")
        for prop_name in obj.MSB_CHARACTER.ADVANCED_SETTINGS:
            if prop_name not in prop_names:
                continue
            prop_names.remove(prop_name)
            if panel:
                panel.prop(props, prop_name)

        # Leftover:
        header, panel = layout.panel("Other Settings", default_closed=True)
        header.label(text="Other Settings")
        if panel:
            for prop in prop_names:
                panel.prop(props, prop)


class MSBPlayerStartPartPanel(SoulstructPanel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB PlayerStart fields for object."""
    bl_label = "MSB Player Start Settings"
    bl_idname = "OBJECT_PT_msb_player_start"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    PART_SUBTYPE = BlenderMSBPartSubtype.PlayerStart
    PROP_GROUP_TYPE = MSBPlayerStartProps


class MSBCollisionPartPanel(SoulstructPanel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Collision fields for active object."""
    bl_label = "MSB Collision Settings"
    bl_idname = "OBJECT_PT_msb_collision"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    PART_SUBTYPE = BlenderMSBPartSubtype.Collision
    PROP_GROUP_TYPE = MSBCollisionProps

    def draw(self, context):
        layout = self.layout

        obj = get_active_part_obj(context)
        if obj is None or obj.MSB_PART.entry_subtype != self.PART_SUBTYPE:
            # Should already fail Panel poll.
            layout.label(text=f"No active MSB {self.PART_SUBTYPE}.")
            return

        props = getattr(obj, self.PART_SUBTYPE.value)  # type: SoulstructPropertyGroup
        prop_names = props.get_game_prop_names(context)
        handled = set()
        handled |= bit_set_prop(layout, props, "navmesh_groups_", "Navmesh Groups")

        for prop in prop_names:
            if prop in handled:
                continue
            layout.prop(props, prop)


class MSBProtobossPartPanel(SoulstructPanel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Protoboss fields for object."""
    bl_label = "MSB Protoboss Settings"
    bl_idname = "OBJECT_PT_msb_protoboss"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    PART_SUBTYPE = BlenderMSBPartSubtype.Protoboss
    PROP_GROUP_TYPE = MSBProtobossProps


class MSBNavmeshPartPanel(SoulstructPanel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Navmesh fields for active object."""
    bl_label = "MSB Navmesh Settings"
    bl_idname = "OBJECT_PT_msb_navmesh"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    PART_SUBTYPE = BlenderMSBPartSubtype.Navmesh
    PROP_GROUP_TYPE = MSBNavmeshProps

    def draw(self, context):
        layout = self.layout

        obj = get_active_part_obj(context)
        if obj is None or obj.MSB_PART.entry_subtype != self.PART_SUBTYPE:
            # Should already fail Panel poll.
            layout.label(text=f"No active MSB {self.PART_SUBTYPE}.")
            return

        # noinspection PyTypeChecker
        props = getattr(obj, self.PART_SUBTYPE.value)  # type: SoulstructPropertyGroup
        prop_names = props.get_game_prop_names(context)
        handled = set()
        handled |= bit_set_prop(layout, props, "navmesh_groups_", "Navmesh Groups")

        for prop in prop_names:
            if prop in handled:
                continue
            layout.prop(props, prop)


class MSBConnectCollisionPartPanel(SoulstructPanel, _MSBPartSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Collision fields for active object."""
    bl_label = "MSB Connect Collision Settings"
    bl_idname = "OBJECT_PT_msb_connect_collision"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    PART_SUBTYPE = BlenderMSBPartSubtype.ConnectCollision
    PROP_GROUP_TYPE = MSBConnectCollisionProps


class MSBRegionPanel(SoulstructPanel):
    """Creates a Panel in the Object properties window."""
    bl_label = "MSB Region Settings"
    bl_idname = "OBJECT_PT_hello"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context) -> bool:
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

        layout.prop(props, "entry_subtype")
        layout.prop(props, "entity_id")

        header, panel = layout.panel("Shape Settings", default_closed=False)
        header.label(text="Shape Settings")
        if panel:
            panel.prop(props, "shape_type")
            if props.shape_type_enum == RegionShapeType.Point:
                panel.label(text="No shape data for Point.")
            elif props.shape_type_enum == RegionShapeType.Circle:
                panel.prop(props, "shape_x", text="Radius")
            elif props.shape_type_enum == RegionShapeType.Sphere:
                panel.prop(props, "shape_x", text="Radius")
            elif props.shape_type_enum == RegionShapeType.Cylinder:
                panel.prop(props, "shape_x", text="Radius")
                panel.prop(props, "shape_z", text="Height")
            elif props.shape_type_enum == RegionShapeType.Rect:
                panel.prop(props, "shape_x", text="Width")
                panel.prop(props, "shape_y", text="Depth")
            elif props.shape_type_enum == RegionShapeType.Box:
                panel.prop(props, "shape_x", text="Width")
                panel.prop(props, "shape_y", text="Depth")
                panel.prop(props, "shape_z", text="Height")
            elif props.shape_type_enum == RegionShapeType.Composite:
                panel.label(text="TODO: Cannot yet modify Composite shape.")

        # All properties handled manually above.


class MSBEventPanel(SoulstructPanel):
    """Draw a Panel in the Object properties window exposing the appropriate MSB Event fields for active object."""
    bl_label = "MSB Event Settings"
    bl_idname = "OBJECT_PT_msb_event"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context) -> bool:
        return get_active_event_obj(context) is not None

    def draw(self, context):
        layout = self.layout

        obj = get_active_event_obj(context)
        if obj is None:
            # Should already fail Panel poll.
            layout.label(text="No active MSB Event.")
            return

        props = obj.MSB_EVENT
        prop_names = props.get_game_prop_names(context)
        handled = set()

        for pre_prop in ("entry_subtype", "entity_id"):
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

    EVENT_SUBTYPE: tp.ClassVar[BlenderMSBEventSubtype]  # also `Object` property attribute name
    PROP_GROUP_TYPE: tp.ClassVar[type[bpy.types.PropertyGroup]]

    @classmethod
    def poll(cls, context) -> bool:
        obj = get_active_event_obj(context)
        return obj is not None and obj.MSB_EVENT.entry_subtype == cls.EVENT_SUBTYPE

    def draw(self, context):
        layout = self.layout

        obj = get_active_event_obj(context)
        if obj is None or obj.MSB_EVENT.entry_subtype != self.EVENT_SUBTYPE:
            # Should already fail Panel poll.
            layout.label(text=f"No active MSB {self.EVENT_SUBTYPE}.")
            return

        # noinspection PyTypeChecker
        props = getattr(obj, self.EVENT_SUBTYPE.value)  # type: SoulstructPropertyGroup
        prop_names = props.get_game_prop_names(context)
        for prop in prop_names:
            layout.prop(props, prop)


class MSBLightEventPanel(SoulstructPanel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate Light fields for active object."""
    bl_label = "MSB Light Settings"
    bl_idname = "OBJECT_PT_msb_light"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    EVENT_SUBTYPE = BlenderMSBEventSubtype.Light
    PROP_GROUP_TYPE = MSBLightEventProps


class MSBSoundEventPanel(SoulstructPanel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate Sound fields for active object."""
    bl_label = "MSB Sound Settings"
    bl_idname = "OBJECT_PT_msb_sound"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    EVENT_SUBTYPE = BlenderMSBEventSubtype.Sound
    PROP_GROUP_TYPE = MSBSoundEventProps


class MSBVFXEventPanel(SoulstructPanel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate VFX fields for active object."""
    bl_label = "MSB VFX Settings"
    bl_idname = "OBJECT_PT_msb_vfx"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    EVENT_SUBTYPE = BlenderMSBEventSubtype.VFX
    PROP_GROUP_TYPE = MSBVFXEventProps


class MSBWindEventPanel(SoulstructPanel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate Wind fields for active object."""
    bl_label = "MSB Wind Settings"
    bl_idname = "OBJECT_PT_msb_wind"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    EVENT_SUBTYPE = BlenderMSBEventSubtype.Wind
    PROP_GROUP_TYPE = MSBWindEventProps


class MSBTreasureEventPanel(SoulstructPanel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate Treasure fields for active object."""
    bl_label = "MSB Treasure Settings"
    bl_idname = "OBJECT_PT_msb_treasure"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    EVENT_SUBTYPE = BlenderMSBEventSubtype.Treasure
    PROP_GROUP_TYPE = MSBTreasureEventProps


class MSBSpawnerEventPanel(SoulstructPanel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate Spawner fields for active object."""
    bl_label = "MSB Spawner Settings"
    bl_idname = "OBJECT_PT_msb_spawner"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    EVENT_SUBTYPE = BlenderMSBEventSubtype.Spawner
    PROP_GROUP_TYPE = MSBSpawnerEventProps


class MSBMessageEventPanel(SoulstructPanel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate Message fields for active object."""
    bl_label = "MSB Message Settings"
    bl_idname = "OBJECT_PT_msb_message"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    EVENT_SUBTYPE = BlenderMSBEventSubtype.Message
    PROP_GROUP_TYPE = MSBMessageEventProps


class MSBObjActEventPanel(SoulstructPanel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate ObjAct fields for active object."""
    bl_label = "MSB ObjAct Settings"
    bl_idname = "OBJECT_PT_msb_obj_act"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    EVENT_SUBTYPE = BlenderMSBEventSubtype.ObjAct
    PROP_GROUP_TYPE = MSBObjActEventProps


class MSBSpawnPointEventPanel(SoulstructPanel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate Spawn Point fields for active object."""
    bl_label = "MSB Spawn Point Settings"
    bl_idname = "OBJECT_PT_msb_spawn_point"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    EVENT_SUBTYPE = BlenderMSBEventSubtype.SpawnPoint
    PROP_GROUP_TYPE = MSBSpawnPointEventProps


class MSBMapOffsetEventPanel(SoulstructPanel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate Map Offset fields for active object."""
    bl_label = "MSB Map Offset Settings"
    bl_idname = "OBJECT_PT_msb_map_offset"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    EVENT_SUBTYPE = BlenderMSBEventSubtype.MapOffset
    PROP_GROUP_TYPE = MSBMapOffsetEventProps


class MSBNavigationEventPanel(SoulstructPanel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate Navigation fields for active object."""
    bl_label = "MSB Navigation Settings"
    bl_idname = "OBJECT_PT_msb_navigation"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    EVENT_SUBTYPE = BlenderMSBEventSubtype.Navigation
    PROP_GROUP_TYPE = MSBNavigationEventProps


class MSBEnvironmentEventPanel(SoulstructPanel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate Environment fields for active object."""
    bl_label = "MSB Environment Settings"
    bl_idname = "OBJECT_PT_msb_environment"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    EVENT_SUBTYPE = BlenderMSBEventSubtype.Environment
    PROP_GROUP_TYPE = MSBEnvironmentEventProps


class MSBNPCInvasionEventPanel(SoulstructPanel, _MSBEventSubtypePanelMixin):
    """Draw a Panel in the Object properties window exposing the appropriate NPC Invasion fields for active object."""
    bl_label = "MSB NPC Invasion Settings"
    bl_idname = "OBJECT_PT_msb_npc_invasion"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    EVENT_SUBTYPE = BlenderMSBEventSubtype.NPCInvasion
    PROP_GROUP_TYPE = MSBNPCInvasionEventProps

# endregion
