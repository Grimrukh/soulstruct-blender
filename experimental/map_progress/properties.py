from __future__ import annotations

__all__ = [
    "MapProgressSettings",
    "MapProgressProps",
]

from datetime import datetime

import bpy

from .config import SUPPORTED_TYPES

# noinspection PyUnusedLocal
def _on_state_changed(self: MapProgressProps, ctx):
    obj = getattr(ctx, "object", None) if ctx else None
    if not obj or not hasattr(obj, "map_progress"):
        return
    obj: bpy.types.Object
    if obj.type in SUPPORTED_TYPES:
        obj.map_progress.apply_visual_state(obj)
        obj.map_progress.sync_pass_index(obj)
        obj.map_progress.set_timestamp()



class MapProgressSettings(bpy.types.PropertyGroup):
    """Global add-on settings stored in Scene."""

    # Internal object-pass mapping that we won't want to break if enum items change:
    PROGRESS_STATE_INDICES = {
        "NONE": 0,
        "TODO": 1,
        "TODO_SCENERY": 2,
        "WIP": 3,
        "DONE": 4,
    }

    PROGRESS_STATE_COLORS = {
        "NONE": (1.0, 1.0, 1.0, 0.0),  # white/transparent
        "TODO": (1.0, 0.15, 0.15, 0.35),  # red
        "TODO_SCENERY": (0.75, 0.4, 1.0, 0.35),  # purple
        "WIP": (1.0, 1.0, 0.15, 0.35),  # yellow
        "DONE": (0.20, 1.0, 0.20, 0.25),  # green
    }

    todo_color: bpy.props.FloatVectorProperty(
        name="TODO Color", subtype="COLOR", size=4,
        default=(1.0, 0.2, 0.2, 1.0), min=0.0, max=1.0,
    )
    todo_sc_color: bpy.props.FloatVectorProperty(
        name="TODO SCENERY Color", subtype="COLOR", size=4,
        default=(0.75, 0.4, 1.0, 1.0), min=0.0, max=1.0,
    )
    wip_color: bpy.props.FloatVectorProperty(
        name="WIP Color", subtype="COLOR", size=4,
        default=(1.0, 1.0, 0.2, 1.0), min=0.0, max=1.0,
    )
    done_color: bpy.props.FloatVectorProperty(
        name="DONE Color", subtype="COLOR", size=4,
        default=(0.2, 1.0, 0.2, 1.0), min=0.0, max=1.0,
    )
    todo_strength: bpy.props.FloatProperty(
        name="TODO Strength", default=0.18, min=0.0, max=1.0,
    )
    todo_sc_strength: bpy.props.FloatProperty(
        name="TODO SCENERY Strength", default=0.12, min=0.0, max=1.0,
    )
    wip_strength: bpy.props.FloatProperty(
        name="WIP Strength", default=0.14, min=0.0, max=1.0,
    )
    done_strength: bpy.props.FloatProperty(
        name="DONE Strength", default=0.10, min=0.0, max=1.0,
    )

    name_filter: bpy.props.StringProperty(
        name="Name Filter",
        description="Filter objects by name substring in selection lists",
        default="",
    )

    # Bulk Init operation settings:
    init_collection_name: bpy.props.StringProperty(
        name="Collection Name",
        description="If set, only initialize objects in this collection (including children)",
        default="",
    )
    init_name_contains: bpy.props.StringProperty(
        name="Name contains (optional)",
        description="Only initialize objects whose names contain this substring",
        default="",
    )


class MapProgressProps(bpy.types.PropertyGroup):
    """Per-object properties for map progress tracking."""
    state: bpy.props.EnumProperty(
        name="State",
        description="Progress state for this object",
        items=[
            ("NONE", "Untracked", "No progress tracking"),
            ("TODO", "TODO", "Not started"),
            ("TODO_SCENERY", "TODO SCENERY", "Scenery-only TODO (lower priority)"),
            ("WIP", "WIP", "Work in progress"),
            ("DONE", "DONE", "Completed"),
        ],
        default="NONE",
        update=_on_state_changed,
    )
    note: bpy.props.StringProperty(
        name="Note", description="Optional note for this object", default=""
    )
    last_edit: bpy.props.StringProperty(
        name="Last Edit", description="Auto-updated when state changes", default=""
    )

    def set_timestamp(self):
        self.last_edit = datetime.now().strftime("%Y-%m-%d %H:%M")

    def apply_visual_state(self, obj: bpy.types.Object):
        """Sets viewport object color + selection lock based on state."""
        obj.color = MapProgressSettings.PROGRESS_STATE_COLORS.get(self.state, (1.0, 1.0, 1.0, 0.0))
        obj.hide_select = self.state == "DONE"

    def sync_pass_index(self, obj: bpy.types.Object):
        """Keep Object.pass_index aligned with our enum for tint masks."""
        obj.pass_index = MapProgressSettings.PROGRESS_STATE_INDICES.get(self.state, 0)
