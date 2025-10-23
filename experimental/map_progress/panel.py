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

        flt = col.box()
        flt.label(text="Next Up (TODO)")
        flt.prop(settings, "name_filter", text="Name Filter")
        todo_items = objects_by_state("TODO", settings.name_filter)
        lim = min(len(todo_items), 30)
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

        flt2 = col.box()
        flt2.label(text="Next Up (TODO SCENERY)")
        sc_items = objects_by_state("TODO_SCENERY", settings.name_filter)
        lim2 = min(len(sc_items), 30)
        for i in range(lim2):
            o = sc_items[i]
            row = flt2.row(align=True)
            row.operator(MapProgressSelectObject.bl_idname, text=o.name).object_name = o.name
            op = row.operator(SetMapProgressState.bl_idname, text="", icon="PLAY")
            op.state = "WIP"; op.target_name = o.name
            op2 = row.operator(SetMapProgressState.bl_idname, text="", icon="CHECKMARK")
            op2.state = "DONE"; op2.target_name = o.name
        if len(sc_items) > lim2:
            flt2.label(text=f"... {len(sc_items)-lim2} more")

        col.separator()

        # Tools
        tools = col.box()
        tools.label(text="Tools")
        row = tools.row(align=True)
        row.operator(ToggleMapProgressOverlay.bl_idname, icon="SHADING_SOLID")
        row.operator(RefreshMapProgressVisuals.bl_idname, icon="FILE_REFRESH")
        row = tools.row(align=True)
        row.operator(ExportMapProgressCSV.bl_idname, icon="EXPORT")

        col.separator()

        # Progress colors/strengths for material debug node group
        tint = col.box()
        tint.label(text="Progress Tint (Colors & Strengths)")
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
        init = col.box()
        init.label(text="Initialization")
        init.operator(MapProgressBulkInit.bl_idname, text="Initialize MSB Progress")
        row = init.row(align=True)
        row.prop(settings, "init_collection_name", text="Collection")
        row = init.row(align=True)
        row.prop(settings, "init_name_contains", text="Name contains")
