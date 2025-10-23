from __future__ import annotations

__all__ = [
    "MapProgressSelectObject",
    "SetMapProgressState",
    "ToggleMapProgressOverlay",
    "ExportMapProgressCSV",
    "MapProgressBulkInit",
    "RefreshMapProgressVisuals",
]

import bpy

from soulstruct.blender.utilities.operators import LoggingOperator
from soulstruct.blender.types import SoulstructType
from soulstruct.blender.msb.properties.parts import BlenderMSBPartSubtype

from .utils import export_csv


class MapProgressSelectObject(LoggingOperator):
    bl_idname = "soulstruct.select_object"
    bl_label = "Select Object"
    bl_options = {"REGISTER", "UNDO"}

    object_name: bpy.props.StringProperty()

    def execute(self, context):
        obj = bpy.data.objects.get(self.object_name)
        if not obj:
            return self.error(f"Object not found: {self.object_name}")
        bpy.ops.object.select_all(action="DESELECT")
        obj.hide_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        return {"FINISHED"}


class SetMapProgressState(LoggingOperator):
    bl_idname = "soulstruct.set_state"
    bl_label = "Set State"
    bl_options = {"REGISTER", "UNDO"}

    state: bpy.props.EnumProperty(
        items=[
            ("NONE", "Untracked", ""),
            ("TODO", "TODO", ""),
            ("TODO_SCENERY", "TODO SCENERY", ""),
            ("WIP", "WIP", ""),
            ("DONE", "DONE", ""),
        ],
    )
    target_name: bpy.props.StringProperty(default="")

    def execute(self, context):
        obj = bpy.data.objects.get(self.target_name) if self.target_name else context.object
        if not obj:
            return self.error("No target object")
        if not hasattr(obj, "map_progress"):
            return self.error(f"Object '{obj.name}' has no progress properties")
        obj.map_progress.state = self.state
        _update_visuals_for_object(obj, set_timestamp=True)
        obj.map_progress.sync_pass_index(obj)
        return {"FINISHED"}


class ToggleMapProgressOverlay(LoggingOperator):
    bl_idname = "soulstruct.toggle_overlay"
    bl_label = "Enable Object-Color Shading"
    bl_options = {"REGISTER"}

    def execute(self, context):
        """Set 3D view to use Object color (Solid mode overlay look)."""
        for area in context.window.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D" and hasattr(space, "shading"):
                        space.shading.color_type = "OBJECT"
        self.info("Viewport shading color set to OBJECT")
        return {"FINISHED"}


class ExportMapProgressCSV(LoggingOperator):
    bl_idname = "soulstruct.export_csv"
    bl_label = "Export Progress CSV"
    bl_options = {"REGISTER"}

    filepath: bpy.props.StringProperty(
        name="Filepath",
        subtype="FILE_PATH",
        default="",
    )

    def invoke(self, context, event):
        if not self.filepath:
            # default path
            from .config import DEFAULT_EXPORT
            self.filepath = str(DEFAULT_EXPORT)
        return self.execute(context)

    def execute(self, context):
        try:
            path = export_csv(self.filepath)
        except Exception as e:
            return self.error(f"Export failed: {e}")
        self.info(f"Exported to {path}")
        return {"FINISHED"}


class MapProgressBulkInit(LoggingOperator):
    bl_idname = "soulstruct.bulk_init"
    bl_label = "Mark all untracked MSB geometry progress as TODO"
    bl_options = {"REGISTER", "UNDO"}

    collection_name: bpy.props.StringProperty(
        name="Collection (optional)",
        description="Limit init to this collection (and children). Leave blank for all objects",
        default="",
    )
    name_contains: bpy.props.StringProperty(
        name="Name contains (optional)",
        description="Only initialize objects whose names contain this substring",
        default="",
    )
    set_state: bpy.props.EnumProperty(
        name="Initial State",
        items=[
            ("TODO", "TODO", ""),
            ("TODO_SCENERY", "TODO SCENERY", ""),
            ("WIP", "WIP", ""),
            ("DONE", "DONE", ""),
        ],
        default="TODO",
    )
    force: bpy.props.BoolProperty(
        name="Force",
        description="Set state even if already initialized",
        default=False,
    )

    def execute(self, context):
        target_set = set()
        if self.collection_name:
            coll = bpy.data.collections.get(self.collection_name)
            if not coll:
                return self.error(f"Collection not found: {self.collection_name}")

            def walk(c):
                for o in c.objects:
                    target_set.add(o)
                for ch in c.children:
                    walk(ch)
            walk(coll)
        else:
            target_set = set(bpy.data.objects)

        count = 0
        name_filter = self.name_contains.lower().strip()
        for obj in sorted(target_set, key=lambda o: o.name):
            obj: bpy.types.Object
            if obj.type != "MESH":
                continue
            try:
                if obj.soulstruct_type != SoulstructType.MSB_PART:
                    continue
                if not (
                    obj.MSB_PART.is_subtype(BlenderMSBPartSubtype.MapPiece)
                    or obj.MSB_PART.is_subtype(BlenderMSBPartSubtype.Collision)
                    or obj.MSB_PART.is_subtype(BlenderMSBPartSubtype.Navmesh)
                ):
                    continue
            except AttributeError:
                # If Soulstruct props are absent on this object, skip quietly
                continue
            if name_filter and name_filter not in obj.name.lower():
                continue
            if not hasattr(obj, "map_progress"):
                continue
            if not self.force and obj.map_progress.state != "NONE":
                continue

            obj.map_progress.state = self.set_state
            _update_visuals_for_object(obj, set_timestamp=True)
            obj.map_progress.sync_pass_index(obj)
            count += 1

        self.info(f"Initialized {count} object(s)")
        return {"FINISHED"}


class RefreshMapProgressVisuals(LoggingOperator):
    bl_idname = "soulstruct.refresh_visuals"
    bl_label = "Refresh Visuals"
    bl_options = {"REGISTER"}

    def execute(self, context):
        _update_all_visuals()
        self.info("Map progress visuals refreshed")
        return {"FINISHED"}


def _update_visuals_for_object(obj: bpy.types.Object, set_timestamp=False):
    if obj is None or obj.type != "MESH":
        return
    obj: bpy.types.Object
    obj.map_progress.apply_visual_state(obj)
    if set_timestamp:
        obj.map_progress.set_timestamp()


def _update_all_visuals():
    for obj in bpy.data.objects:
        if not hasattr(obj, "map_progress"):
            continue
        obj.map_progress.apply_visual_state(obj)
