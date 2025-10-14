"""Standalone add-on for tracking Soulstruct map development progress."""

bl_info = {
    "name": "Soulstruct Map Progress Manager",
    "author": "Scott Mooney (Grimrukh)",
    "version": (1, 0, 0),
    "blender": (4, 4, 0),
    "location": "3D View > N-Panel > MapTools > Map Progress",
    "description": "Per-object progress tags with visual overlay, edit lock, queue, and CSV export",
    "category": "Object",
}

import csv
import os
from datetime import datetime
from pathlib import Path

import bpy

from soulstruct.blender.types import SoulstructType
from soulstruct.blender.msb.properties.parts import BlenderMSBPartSubtype
from soulstruct.blender.utilities.operators import LoggingOperator

# region Configuration
COLOR_NONE = (1.0, 1.0, 1.0, 0.0)     # default (no overlay)
COLOR_TODO = (1.0, 0.15, 0.15, 0.35)   # red
COLOR_WIP  = (1.0, 1.0, 0.15, 0.35)    # yellow
COLOR_DONE = (0.20, 1.0, 0.20, 0.25)   # green
SUPPORTED_TYPES = {"MESH", "CURVE", "SURFACE", "META", "FONT"}
DEFAULT_EXPORT = Path("~/map_progress.csv").expanduser()
# endregion


# region Properties

class MapProgressProps(bpy.types.PropertyGroup):

    state: bpy.props.EnumProperty(
        name="State",
        description="Progress state for this object",
        items=[
            ("NONE", "Untracked", "No progress tracking"),
            ("TODO", "To Do", "Not started"),
            ("WIP",  "In Progress", "Work in progress"),
            ("DONE", "Done", "Completed"),
        ],
        default="NONE",
        update=lambda self, ctx: update_visuals_for_object(ctx, ctx.object if ctx and ctx.object else None, from_prop=True),
    )
    note: bpy.props.StringProperty(
        name="Note",
        description="Optional note for this object",
        default=""
    )
    last_edit: bpy.props.StringProperty(
        name="Last Edit",
        description="Auto-updated when state changes",
        default=""
    )


def _set_timestamp(obj: bpy.types.Object):
    # set last edited timestamp
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    obj.map_progress.last_edit = now


def _apply_visual_state(obj: bpy.types.Object):
    """Sets viewport color + selection lock based on state."""
    match obj.map_progress.state:
        case "NONE":
            obj.color = COLOR_NONE
            obj.hide_select = False
        case "TODO":
            obj.color = COLOR_TODO
            obj.hide_select = False
        case "WIP":
            obj.color = COLOR_WIP
            obj.hide_select = False
        case "DONE":
            obj.color = COLOR_DONE
            obj.hide_select = True


def update_visuals_for_object(obj: bpy.types.Object, from_prop=False):
    """Update visuals for a single object; called by prop update + ops."""
    if obj is None or obj.type not in SUPPORTED_TYPES:
        return
    if not hasattr(obj, "map_progress"):
        return
    _apply_visual_state(obj)
    if from_prop:
        _set_timestamp(obj)


def update_all_visuals():
    # update visuals for all objects with progress
    print("Refreshing map progress visuals...")
    for obj in bpy.data.objects:
        if hasattr(obj, "map_progress") and "state" in obj.map_progress.keys():
            _apply_visual_state(obj)
    print("Done.")

# endregion


# region Helpers

def iter_tracked_objects(context):
    """Generator for objects that have our progress prop and are not untracked."""
    for obj in bpy.data.objects:
        if hasattr(obj, "map_progress") and obj.map_progress.state != "NONE":
            yield obj


def count_states():
    t = w = d = 0
    total = 0
    for obj in iter_tracked_objects(bpy.context):
        s = obj.map_progress.state
        if   s == "TODO": t += 1
        elif s == "WIP":  w += 1
        elif s == "DONE": d += 1
        total += 1
    return t, w, d, total


def objects_by_state(state, name_filter=""):
    items = []
    nf = name_filter.strip().lower()
    for obj in iter_tracked_objects(bpy.context):
        if obj.map_progress.state == state:
            if nf and nf not in obj.name.lower():
                continue
            items.append(obj)
    # stable name sort for predictability
    items.sort(key=lambda o: o.name)
    return items

# endregion


# region Operators

class MapProgressSelectObject(LoggingOperator):
    """Internal helper operator."""
    
    bl_idname = "mapprog.select_object"
    bl_label = "Select Object"
    bl_options = set()

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
    bl_idname = "mapprog.set_state"
    bl_label = "Set State"
    bl_options = {"REGISTER", "UNDO"}

    state: bpy.props.EnumProperty(
        items=[
            ("NONE", "Untracked", ""),
            ("TODO", "To Do", ""),
            ("WIP", "In Progress", ""),
            ("DONE", "Done", ""),
        ],
    )

    target_name: bpy.props.StringProperty(default="")  # if empty, use active

    def execute(self, context):
        obj = bpy.data.objects.get(self.target_name) if self.target_name else context.object
        if not obj:
            return self.error("No target object")
        if not hasattr(obj, "map_progress"):
            return self.error(f"Object '{obj.name}' has no progress properties")
        obj.map_progress.state = self.state
        update_visuals_for_object(obj)
        _set_timestamp(obj)
        return {"FINISHED"}


class ToggleMapProgressOverlay(LoggingOperator):
    bl_idname = "mapprog.toggle_overlay"
    bl_label = "Enable Object-Color Shading"
    bl_options = {"REGISTER"}

    def execute(self, context):
        """Set 3D view to use Object color."""
        for area in context.window.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.shading.color_type = "OBJECT"
        self.info("Viewport shading color set to OBJECT")
        return {"FINISHED"}


class ExportMapProgressCSV(LoggingOperator):
    bl_idname = "mapprog.export_csv"
    bl_label = "Export Progress CSV"
    bl_options = {"REGISTER"}

    filepath: bpy.props.StringProperty(
        name="Filepath",
        subtype="FILE_PATH",
        default=DEFAULT_EXPORT,
    )

    def execute(self, context):
        rows = [["Name", "State", "Note", "Last Edit", "CollectionPath"]]
        for obj in iter_tracked_objects(context):
            # make a simple collection path (first parent chain)
            coll_path = []
            for coll in obj.users_collection:
                coll_path.append(coll.name)
            rows.append([
                obj.name,
                obj.map_progress.state,
                obj.map_progress.note,
                obj.map_progress.last_edit,
                " | ".join(coll_path),
            ])

        try:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(rows)
        except Exception as e:
            return self.error(f"Export failed: {e}")

        self.info(f"Exported to {self.filepath}")
        return {"FINISHED"}


class MapProgressBulkInit(LoggingOperator):
    bl_idname = "mapprog.bulk_init"
    bl_label = "Init Progress for MSB Geometry"
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
        items=[("TODO", "To Do", ""), ("WIP", "In Progress", ""), ("DONE", "Done", "")],
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
            if obj.soulstruct_type != SoulstructType.MSB_PART:
                continue
            if not (
                obj.MSB_PART.is_subtype(BlenderMSBPartSubtype.MapPiece)
                or obj.MSB_PART.is_subtype(BlenderMSBPartSubtype.Collision)
                or obj.MSB_PART.is_subtype(BlenderMSBPartSubtype.Navmesh)
            ):
                continue
            if name_filter and name_filter not in obj.name.lower():
                continue
            # ensure pointer exists
            if not hasattr(obj, "map_progress"):
                continue
            if not self.force and obj.map_progress.state != "NONE":
                continue  # already tracked

            obj.map_progress.state = self.set_state
            _set_timestamp(obj)
            update_visuals_for_object(obj)
            count += 1

        self.info(f"Initialized {count} object(s)")
        return {"FINISHED"}


class RefreshMapProgressVisuals(LoggingOperator):
    bl_idname = "mapprog.refresh_visuals"
    bl_label = "Refresh Visuals"
    bl_options = {"REGISTER"}

    def execute(self, context):
        update_all_visuals()
        self.info("Map progress visuals refreshed")
        return {"FINISHED"}

# endregion


# region UI

class MapProgressPanel(bpy.types.Panel):
    bl_label = "Map Progress"
    bl_idname = "MAPPROG_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MapTools"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        # active object controls
        obj = context.object
        box = col.box()
        box.label(text="Active Object")
        if obj and hasattr(obj, "map_progress"):
            row = box.row(align=True)
            row.prop(obj.map_progress, "state", text="")
            for state in ("TODO", "WIP", "DONE"):
                row.operator(SetMapProgressState.bl_idname, text=state).state = state
            box.prop(obj.map_progress, "note", text="Note")
            if obj.map_progress.last_edit:
                box.label(text=f"Last Edit: {obj.map_progress.last_edit}")
        else:
            box.label(text="No active tracked object")

        # progress summary
        t, w, d, total = count_states()
        prog = col.box()
        prog.label(text="Summary")
        prog.label(text=f"Total: {total} | To Do: {t} | WIP: {w} | Done: {d}")
        if total > 0:
            pct = int(round(100 * d / total))
            prog.label(text=f"Completion: {pct}%")

        # next up list
        prefs = context.window_manager
        col.separator()
        flt = col.box()
        flt.label(text="Next Up (To Do)")
        flt.prop(prefs, "mapprog_name_filter", text="Name filter")
        todo_items = objects_by_state("TODO", prefs.mapprog_name_filter)
        lim = min(len(todo_items), 30)  # avoid super long list
        for i in range(lim):
            o = todo_items[i]
            row = flt.row(align=True)
            row.operator(MapProgressSelectObject.bl_idname, text=o.name).object_name = o.name
            op = row.operator(SetMapProgressState.bl_idname, text="", icon="PLAY")
            op.state = "WIP"; op.target_name = o.name
            op2 = row.operator(SetMapProgressState.bl_idname, text="", icon="CHECKMARK")
            op2.state = "DONE"; op2.target_name = o.name
        if len(todo_items) > lim:
            flt.label(text=f"... {len(todo_items)-lim} more")

        # tools
        tools = col.box()
        tools.label(text="Tools")
        row = tools.row(align=True)
        row.operator(ToggleMapProgressOverlay.bl_idname, icon="SHADING_SOLID")
        row.operator(RefreshMapProgressVisuals.bl_idname, icon="FILE_REFRESH")
        row = tools.row(align=True)
        row.operator(ExportMapProgressCSV.bl_idname, icon="EXPORT")
        init = col.box()
        init.label(text="Bulk Init MSBs")
        init.operator(MapProgressBulkInit.bl_idname, text="Init (All MESH as TODO)")
        row = init.row(align=True)
        row.prop(context.scene, "mapprog_init_coll", text="Collection")
        row = init.row(align=True)
        row.prop(context.scene, "mapprog_init_name_contains", text="Name contains")

# endregion


# region Registration

def _ensure_runtime_props():
    """Create WindowManager + Scene scratch props as needed."""


classes = (
    MapProgressProps,
    MapProgressSelectObject,
    SetMapProgressState,
    ToggleMapProgressOverlay,
    ExportMapProgressCSV,
    MapProgressBulkInit,
    RefreshMapProgressVisuals,
    MapProgressPanel,
)

def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Object.map_progress = bpy.props.PointerProperty(type=MapProgressProps)
    bpy.types.WindowManager.mapprog_name_filter = bpy.props.StringProperty(
        name="Filter", default=""
    )
    bpy.types.Scene.mapprog_init_coll = bpy.props.StringProperty(default="")
    bpy.types.Scene.mapprog_init_name_contains = bpy.props.StringProperty(default="")

    # TODO: _RestrictContext prevents)
    # one-time visual sync
    # update_all_visuals()

def unregister():
    # TODO: _RestrictContext prevents)
    # update_all_visuals()

    if hasattr(bpy.types.Object, "map_progress"):
        del bpy.types.Object.map_progress
    if hasattr(bpy.types.WindowManager, "mapprog_name_filter"):
        del bpy.types.WindowManager.mapprog_name_filter
    if hasattr(bpy.types.Scene, "mapprog_init_coll"):
        del bpy.types.Scene.mapprog_init_coll
    if hasattr(bpy.types.Scene, "mapprog_init_name_contains"):
        del bpy.types.Scene.mapprog_init_name_contains

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
