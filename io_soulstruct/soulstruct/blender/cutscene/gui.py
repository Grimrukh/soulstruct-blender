from __future__ import annotations

__all__ = [
    "CutsceneCutUIList",
    "CutsceneImportExportPanel",
]

import bpy

from soulstruct.games import GameType

from ..base.register import io_soulstruct_panel
from ..bpy_base.panel import SoulstructPanel
from .import_operators import *
from .export_operators import *
from .misc_operators import *
from .types import SoulstructCutsceneAnimation


@io_soulstruct_panel
class CutsceneCutUIList(bpy.types.UIList):
    """One row per camera cut of a cutscene Action: editable name and game frame count."""

    bl_idname = "ACTION_UL_cutscene_cuts"

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index=0, flt_flag=0):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, "name", text="", emboss=False)
            row.prop(item, "frame_count", text="Frames")
        else:
            layout.label(text=item.name)


@io_soulstruct_panel
class CutsceneImportExportPanel(SoulstructPanel):
    bl_label = "Cutscenes"
    bl_idname = "CUTSCENE_PT_hkx_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cutscene"
    bl_options = {"DEFAULT_CLOSED"}

    # noinspection PyUnusedLocal
    def draw(self, context):
        layout = self.layout
        settings = context.scene.soulstruct_settings

        if not settings.is_game(GameType.DarkSoulsDSR):
            layout.label(text="Cutscenes are supported for DSR only.")
            return

        header, panel = layout.panel("Import", default_closed=False)
        header.label(text="Import")
        if panel:
            import_settings = context.scene.cutscene_import_settings
            panel.prop(import_settings, "to_60_fps")
            panel.prop(import_settings, "camera_data_only")
            panel.operator(ImportHKXCutscene.bl_idname)

        header, panel = layout.panel("Create", default_closed=False)
        header.label(text="Create / Edit")
        if panel:
            panel.operator(CreateHKXCutscene.bl_idname, icon="ADD")
            obj = context.active_object
            cutscene = SoulstructCutsceneAnimation.from_animated_id(obj) if obj else None
            if cutscene is None:
                panel.label(text="Select an object animated by a cutscene to edit its cuts.")
            else:
                props = cutscene.props
                panel.label(text=f"Cutscene: {props.cutscene_name} ({props.get_total_frame_count()} game frames)")
                row = panel.row()
                row.template_list(
                    listtype_name=CutsceneCutUIList.bl_idname,
                    list_id="",
                    dataptr=props,
                    propname="cuts",
                    active_dataptr=props,
                    active_propname="active_cut_index",
                    rows=3,
                )
                col = row.column(align=True)
                col.operator(AddCutsceneCut.bl_idname, icon="ADD", text="")
                col.operator(RemoveCutsceneCut.bl_idname, icon="REMOVE", text="")
                panel.operator(BindObjectsToCutscene.bl_idname)

        header, panel = layout.panel("Export", default_closed=False)
        header.label(text="Export")
        if panel:
            export_settings = context.scene.cutscene_export_settings
            panel.prop(export_settings, "export_camera")
            panel.prop(export_settings, "force_interleaved")
            panel.label(text="Select an object animated by a cutscene:")
            panel.operator(ExportHKXCutscene.bl_idname, text="Export (Patch Source RemoBND)")
            panel.operator(ExportNewHKXCutscene.bl_idname, text="Export New (From Collection)")
