from __future__ import annotations

__all__ = [
    "MapProgressPanel",
]

import bpy

from .operators import (
    MapProgressSelectObject,
    SetMapProgressState,
    ToggleMapProgressOverlay,
    ExportMapProgressCSV,
    MapProgressBulkInit,
    RefreshMapProgressVisuals,
)

from .utils import count_states, objects_by_state


class MapProgressPanel(bpy.types.Panel):
    bl_label = "Map Progress"
    bl_idname = "MAPPROG_PT_progress"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Experimental"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        # Active object block
        box = col.box()
        box.label(text="Active Object")
        obj = context.object
        if obj and hasattr(obj, "map_progress"):
            row = box.row(align=True)
            row.prop(obj.map_progress, "state", text="")
            for state in ("TODO", "TODO_SCENERY", "WIP", "DONE"):
                op = row.operator(SetMapProgressState.bl_idname, text=state)
                op.target_name = ""  # all selected
                op.state = state
            box.prop(obj.map_progress, "note", text="Note")
            if obj.map_progress.last_edit:
                box.label(text=f"Last Edit: {obj.map_progress.last_edit}")
        else:
            box.label(text="No active tracked object")

        # Summary
        t, ts, w, d, total = count_states()
        prog = col.box()
        prog.label(text="Summary")
        prog.label(text=f"Total: {total} | TODO: {t} | TODO SCENERY: {ts} | WIP: {w} | DONE: {d}")
        if total > 0:
            pct = int(round(100 * d / total))
            prog.label(text=f"Completion: {pct}%")

        col.separator()

        # Next Up lists (use map_progress_settings for filters)
        settings = context.scene.map_progress_settings

        header, next_todo = layout.panel("Next Up (TODO)", default_closed=True)
        header.label(text="Next Up (TODO)")
        if next_todo:
            next_todo.prop(settings, "name_filter", text="Name Filter")
            next_todo.prop(settings, "next_up_visible_only", text="Visible Only")
            todo_items = objects_by_state("TODO", settings.name_filter, settings.next_up_visible_only)
            lim = min(len(todo_items), 20)
            for i in range(lim):
                o = todo_items[i]
                row = next_todo.row(align=True)
                row.operator(MapProgressSelectObject.bl_idname, text=o.name).object_name = o.name
                op = row.operator(SetMapProgressState.bl_idname, text="", icon="PLAY")
                op.state = "WIP"; op.target_name = o.name
                op2 = row.operator(SetMapProgressState.bl_idname, text="", icon="CHECKMARK")
                op2.state = "DONE"; op2.target_name = o.name
            if len(todo_items) > lim:
                next_todo.label(text=f"... {len(todo_items)-lim} more")

        header, next_scenery = layout.panel("Next Up (TODO SCENERY)", default_closed=True)
        header.label(text="Next Up (TODO SCENERY)")
        if next_scenery:
            next_scenery.prop(settings, "name_filter", text="Name Filter")
            next_scenery.prop(settings, "next_up_visible_only", text="Visible Only")
            sc_items = objects_by_state("TODO_SCENERY", settings.name_filter, settings.next_up_visible_only)
            lim2 = min(len(sc_items), 20)
            for i in range(lim2):
                o = sc_items[i]
                row = next_scenery.row(align=True)
                row.operator(MapProgressSelectObject.bl_idname, text=o.name).object_name = o.name
                op = row.operator(SetMapProgressState.bl_idname, text="", icon="PLAY")
                op.state = "WIP"; op.target_name = o.name
                op2 = row.operator(SetMapProgressState.bl_idname, text="", icon="CHECKMARK")
                op2.state = "DONE"; op2.target_name = o.name
            if len(sc_items) > lim2:
                next_scenery.label(text=f"... {len(sc_items)-lim2} more")

        col.separator()

        # Tools
        tools = col.box()
        tools.label(text="Tools")
        row = tools.row(align=True)
        row.operator(ToggleMapProgressOverlay.bl_idname, icon="SHADING_SOLID")
        row.operator(RefreshMapProgressVisuals.bl_idname, icon="FILE_REFRESH")
        row = tools.row(align=True)
        row.operator(ExportMapProgressCSV.bl_idname, icon="EXPORT")
        tools.prop(settings, "hide_select_done", text="Can't Select DONE")

        col.separator()

        # Progress colors/strengths for material debug node group
        header, tint = layout.panel("Progress Tint Settings", default_closed=True)
        header.label(text="Progress Tint Settings")
        if tint:
            r = tint.row(align=True); r.prop(settings, "todo_color", text="TODO")
            r.prop(settings, "todo_strength", text="Strength")
            r = tint.row(align=True); r.prop(settings, "todo_sc_color", text="TODO SCENERY")
            r.prop(settings, "todo_sc_strength", text="Strength")
            r = tint.row(align=True); r.prop(settings, "wip_color",  text="WIP")
            r.prop(settings, "wip_strength",  text="Strength")
            r = tint.row(align=True); r.prop(settings, "done_color", text="DONE")
            r.prop(settings, "done_strength", text="Strength")

        col.separator()

        # Bulk init
        header, init = layout.panel("Bulk Initialization", default_closed=True)
        header.label(text="Bulk Initialization")
        if init:
            init.operator(MapProgressBulkInit.bl_idname, text="Initialize MSB Progress")
            row = init.row(align=True)
            row.prop(settings, "init_collection_name", text="Collection")
            row = init.row(align=True)
            row.prop(settings, "init_name_contains", text="Name contains")
