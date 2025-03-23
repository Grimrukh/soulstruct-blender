from __future__ import annotations

__all__ = [
    "MapCollisionImportExportPanel",
    "MapCollisionToolsPanel",
]

from io_soulstruct.bpy_base.panel import SoulstructPanel
from io_soulstruct.exceptions import SoulstructTypeError
from io_soulstruct.misc.misc_mesh import *
from .import_operators import *
from .export_operators import *
from .misc_operators import *
from .types import BlenderMapCollision


class MapCollisionImportExportPanel(SoulstructPanel):
    """Contains import and export operators for HKX Map Collision models."""

    bl_label = "Collision Import/Export"
    bl_idname = "HKX_PT_hkx_map_collision_import_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Collision"
    bl_options = {"DEFAULT_CLOSED"}

    # noinspection PyUnusedLocal
    def draw(self, context):
        settings = context.scene.soulstruct_settings
        if not settings.game_config.supports_collision_model:
            self.layout.label(text="Not supported for game.")
            return

        layout = self.layout
        self.draw_active_map(context, layout)

        import_box = layout.box()
        import_box.operator(ImportMapHKXMapCollision.bl_idname)
        import_box.operator(ImportAnyHKXMapCollision.bl_idname, text="Import Any Map Collision")

        export_box = self.layout.box()
        try:
            BlenderMapCollision.from_selected_objects(context)
        except SoulstructTypeError:
            export_box.label(text="Select some Collision models.")
            export_box.label(text="MSB Parts cannot be selected.")
            return

        export_box.prop(settings, "auto_detect_export_map")
        if settings.auto_detect_export_map:
            self.draw_detected_map(context, layout, use_latest_version=False)
        else:
            self.draw_active_map(context, layout)
        self.maybe_draw_export_operator(context, ExportMapHKXMapCollision.bl_idname, layout)
        export_box.operator(ExportAnyHKXMapCollision.bl_idname)
        export_box.operator(ExportHKXMapCollisionIntoAnyBinder.bl_idname)


class MapCollisionToolsPanel(SoulstructPanel):
    """Contains miscellaneous settings/operators for HKX Map Collision models."""

    bl_label = "Collision Tools"
    bl_idname = "HKX_PT_hkx_map_collision_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Collision"
    bl_options = {"DEFAULT_CLOSED"}

    # noinspection PyUnusedLocal
    def draw(self, context):

        layout = self.layout

        layout.label(text="Creation Tools:")
        layout.operator(GenerateCollisionFromMesh.bl_idname)
        layout.operator(CopyMeshSelectionOperator.bl_idname)
        layout.operator(CutMeshSelectionOperator.bl_idname)

        layout.label(text="Display Tools:")
        layout.operator(SelectHiResFaces.bl_idname)
        layout.prop(context.scene.map_collision_tool_settings, "hi_alpha")
        layout.operator(SelectLoResFaces.bl_idname)
        layout.prop(context.scene.map_collision_tool_settings, "lo_alpha")

        layout.label(text="Mesh Tools:")
        # Useful in particular for creating HKX map collisions (e.g. from FLVER or high <> low res).
        layout.operator(RenameCollision.bl_idname)
        layout.operator(BooleanMeshCut.bl_idname)
        layout.operator(ApplyLocalMatrixToMesh.bl_idname)
