from __future__ import annotations

__all__ = [
    "MapCollisionPanel",
]

import bpy

from .import_operators import *
from .export_operators import *
from .misc_operators import *

from io_soulstruct.misc_operators import CopyMeshSelectionOperator, CutMeshSelectionOperator


class MapCollisionPanel(bpy.types.Panel):
    """Contains import, export, and miscellaneous operators."""

    bl_label = "HKX Map Collisions"
    bl_idname = "HKX_PT_hkx_map_collisions"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Collision"
    bl_options = {'DEFAULT_CLOSED'}

    # noinspection PyUnusedLocal
    def draw(self, context):
        settings = context.scene.soulstruct_settings
        if settings.game_variable_name != "DARK_SOULS_DSR":
            self.layout.label(text="Dark Souls: Remastered only.")
            return

        import_box = self.layout.box()
        import_box.operator(ImportHKXMapCollision.bl_idname, text="Import Any Map Collision")

        if settings.is_game("DARK_SOULS_DSR"):
            map_import_box = import_box.box()
            map_import_box.label(text="Import from Selected Map")
            map_import_box.operator(ImportSelectedMapHKXMapCollision.bl_idname)

        export_box = self.layout.box()
        export_box.operator(ExportLooseHKXMapCollision.bl_idname)
        export_box.operator(ExportHKXMapCollisionIntoBinder.bl_idname)

        if settings.is_game("DARK_SOULS_DSR"):
            map_export_box = export_box.box()
            map_export_box.label(text="Export to Selected Map")
            map_export_box.prop(context.scene.soulstruct_settings, "detect_map_from_collection")
            map_export_box.operator(ExportHKXMapCollisionIntoHKXBHD.bl_idname)

        misc_operators_box = self.layout.box()
        misc_operators_box.operator(SelectHiResFaces.bl_idname)
        misc_operators_box.operator(SelectLoResFaces.bl_idname)
        # Useful in particular for creating HKX map collisions (e.g. from FLVER or high <> low res).
        misc_operators_box.prop(context.scene.mesh_move_settings, "new_material_index")
        misc_operators_box.operator(CopyMeshSelectionOperator.bl_idname)
        misc_operators_box.operator(CutMeshSelectionOperator.bl_idname)
