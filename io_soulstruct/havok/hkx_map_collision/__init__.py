from __future__ import annotations

__all__ = [
    "ImportHKXMapCollision",
    "ImportHKXMapCollisionWithBinderChoice",
    "ImportHKXMapCollisionFromHKXBHD",
    "HKXMapCollisionImportSettings",

    "ExportLooseHKXMapCollision",
    "ExportHKXMapCollisionIntoBinder",
    "ExportHKXMapCollisionIntoHKXBHD",

    "SelectHiResFaces",
    "SelectLoResFaces",

    "HKX_COLLISION_PT_hkx_map_collisions",
]

import importlib
import sys

import bpy

# Force reload of Soulstruct module (for easier updating).
try:
    import soulstruct_havok
except ImportError:
    soulstruct_havok = None
else:
    importlib.reload(soulstruct_havok)
import soulstruct
importlib.reload(soulstruct)

if "HKX_PT_hkx_tools" in locals():
    importlib.reload(sys.modules["io_soulstruct.hkx_map_collision.utilities"])
    importlib.reload(sys.modules["io_soulstruct.hkx_map_collision.import_hkx"])
    importlib.reload(sys.modules["io_soulstruct.hkx_map_collision.export_hkx"])
    importlib.reload(sys.modules["io_soulstruct.misc_operators"])

from .model_import import *
from .model_export import *
from .misc_operators import *

from io_soulstruct.misc_operators import CopyMeshSelectionOperator, CutMeshSelectionOperator


class HKX_COLLISION_PT_hkx_map_collisions(bpy.types.Panel):
    bl_label = "HKX Map Collisions"
    bl_idname = "HKX_PT_hkx_map_collisions"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct Havok"
    bl_options = {'DEFAULT_CLOSED'}

    # noinspection PyUnusedLocal
    def draw(self, context):
        settings = context.scene.soulstruct_settings
        if settings.game_variable_name != "DARK_SOULS_DSR":
            self.layout.label(text="Dark Souls: Remastered only.")
            return

        import_box = self.layout.box()
        import_box.operator(ImportHKXMapCollision.bl_idname)

        game_name = context.scene.soulstruct_settings.game_variable_name

        if game_name == "DARK_SOULS_DSR":
            quick_import_box = import_box.box()
            quick_import_box.label(text="Import from Game/Project Map")
            quick_import_box.prop(context.scene.hkx_map_collision_import_settings, "merge_submeshes")
            quick_import_box.prop(context.scene.soulstruct_game_enums, "hkx_map_collision")
            quick_import_box.operator(ImportHKXMapCollisionFromHKXBHD.bl_idname)

        export_box = self.layout.box()
        export_box.operator(ExportLooseHKXMapCollision.bl_idname)
        export_box.operator(ExportHKXMapCollisionIntoBinder.bl_idname)

        if game_name == "DARK_SOULS_DSR":
            quick_export_box = export_box.box()
            quick_export_box.label(text="Export to Project/Game Map")
            quick_export_box.prop(context.scene.soulstruct_settings, "detect_map_from_collection")
            quick_export_box.operator(ExportHKXMapCollisionIntoHKXBHD.bl_idname)

        misc_operators_box = self.layout.box()
        misc_operators_box.operator(SelectHiResFaces.bl_idname)
        misc_operators_box.operator(SelectLoResFaces.bl_idname)
        # Useful in particular for creating HKX map collisions (e.g. from FLVER or high <> low res).
        misc_operators_box.prop(context.scene.mesh_move_settings, "new_material_index")
        misc_operators_box.operator(CopyMeshSelectionOperator.bl_idname)
        misc_operators_box.operator(CutMeshSelectionOperator.bl_idname)
