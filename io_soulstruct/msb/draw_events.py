"""Import MSB Events of any subtype as Blender Empty objects, with custom shape properties and a custom draw tool."""
from __future__ import annotations

__all__ = [
    "EventDrawSettings",
    "draw_msb_events",
]

import bpy
from io_soulstruct.types import SoulstructType
from .properties import MSBEventSubtype


class EventDrawSettings(bpy.types.PropertyGroup):

    draw_mode: bpy.props.EnumProperty(
        name="Draw Mode",
        description="When to draw MSB Events in the 3D view",
        items=[
            ("ACTIVE_COLLECTION", "Active Collection", "Draw all MSB Events in the active collection"),
            ("SELECTED", "Selected", "Draw only selected MSB Events"),
            ("MAP", "Map", "Draw all MSB Events in a collection with name starting with active map"),
            ("ALL", "All", "Draw all MSB Events in the scene"),
            ("NONE", "None", "Do not draw any MSB Events"),
        ],
        default="ALL",
    )

    draw_light: bpy.props.BoolProperty(
        name="Light",
        description="Draw Light MSB event",
        default=True,
    )
    draw_sound: bpy.props.BoolProperty(
        name="Sound",
        description="Draw Sound MSB event",
        default=True,
    )
    draw_vfx: bpy.props.BoolProperty(
        name="VFX",
        description="Draw VFX MSB events",
        default=True,
    )
    draw_wind: bpy.props.BoolProperty(
        name="Wind",
        description="Draw Wind MSB event",
        default=True,
    )
    draw_treasure: bpy.props.BoolProperty(
        name="Treasure",
        description="Draw Treasure MSB events",
        default=True,
    )
    draw_spawner: bpy.props.BoolProperty(
        name="Spawner",
        description="Draw Spawner MSB events",
        default=True,
    )
    draw_message: bpy.props.BoolProperty(
        name="Message",
        description="Draw Message MSB events",
        default=True,
    )
    draw_objact: bpy.props.BoolProperty(
        name="Obj Act",
        description="Draw ObjAct MSB events",
        default=True,
    )
    draw_spawnpoint: bpy.props.BoolProperty(
        name="Spawn Point",
        description="Draw SpawnPoint MSB events",
        default=True,
    )
    draw_mapoffset: bpy.props.BoolProperty(
        name="Map Offset",
        description="Draw MapOffset MSB events",
        default=True,
    )
    draw_navigation: bpy.props.BoolProperty(
        name="Navigation",
        description="Draw Navigation MSB events",
        default=True,
    )
    draw_environment: bpy.props.BoolProperty(
        name="Environment",
        description="Draw Environment MSB events",
        default=True,
    )
    draw_npcinvasion: bpy.props.BoolProperty(
        name="NPC Invasion",
        description="Draw NPCInvasion MSB events",
        default=True,
    )

    event_color: bpy.props.FloatVectorProperty(
        name="Event Color",
        description="Color of drawn MSB Events",
        subtype="COLOR",
        default=(0.112, 1.0, 0.565),  # cyan
        min=0.0,
        max=1.0,
    )

    radius: bpy.props.FloatProperty(
        name="Radius",
        description="Radius of drawn wireframe spheres",
        default=1.5,
        min=1.0,
        max=10.0,
    )

    line_width: bpy.props.FloatProperty(
        name="Line Width",
        description="Width of wireframe sphere lines",
        default=1.0,
        min=0.1,
        max=10.0,
    )


DEFAULT_COLOR = (0.0, 0.0, 0.0, 1.0)  # black


def draw_msb_events():
    draw_settings = bpy.context.scene.event_draw_settings
    if draw_settings.draw_mode == "NONE":
        return  # don't draw any

    # TODO: What this should ACTUALLY do is set the viewport color of the parent Part model (bounds?) or Region (wire).

    events = []  # type: list[bpy.types.Object]
    enabled_subtypes = {
        subtype.lower() for subtype in MSBEventSubtype.__members__
        if subtype != "NONE" and getattr(draw_settings, f"draw_{subtype.lower()}")
    }

    def register_obj(obj_: bpy.types.Object):
        if obj_.soulstruct_type != SoulstructType.MSB_EVENT:
            return
        events.append(obj_)

    match draw_settings.draw_mode:
        case "ACTIVE_COLLECTION":
            for obj in bpy.context.collection.objects:
                register_obj(obj)
        case "SELECTED":
            for obj in bpy.context.selected_objects:
                register_obj(obj)
        case "MAP":
            map_stem = bpy.context.scene.soulstruct_settings.get_latest_map_stem_version()  # for MSB
            for collection in bpy.data.collections:
                if not collection.name.startswith(map_stem):
                    continue
                for obj in collection.objects:
                    register_obj(obj)
        case "ALL":
            for obj in bpy.context.scene.collection.all_objects:
                register_obj(obj)

    for event in events:

        if not event.parent:
            continue  # event is not attached to any spatial element (e.g. MapOffset); nothing to color

        if event.MSB_EVENT.event_subtype.lower() not in enabled_subtypes:
            event.color = DEFAULT_COLOR
            event.parent.color = DEFAULT_COLOR
        else:
            event.color = (*draw_settings.event_color, 1.0)
            event.parent.color = (*draw_settings.event_color, 1.0)
