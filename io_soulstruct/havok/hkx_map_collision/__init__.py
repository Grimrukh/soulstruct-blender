from __future__ import annotations

__all__ = [
    "ImportHKXMapCollision",
    "ImportHKXMapCollisionWithBinderChoice",
    "ImportHKXMapCollisionFromHKXBHD",
    "ImportMSBMapCollision",

    "ExportLooseHKXMapCollision",
    "ExportHKXMapCollisionIntoBinder",
    "ExportHKXMapCollisionIntoHKXBHD",
    "ExportMSBMapCollision",

    "HKX_COLLISION_PT_hkx_map_collision_tools",
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

from .import_hkx_map_collision import *
from .export_hkx_map_collision import *

from io_soulstruct.misc_operators import CopyMeshSelectionOperator


class HKX_COLLISION_PT_hkx_map_collision_tools(bpy.types.Panel):
    bl_label = "HKX Map Collisions"
    bl_idname = "HKX_PT_hkx_map_collision_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct Havok"
    bl_options = {'DEFAULT_CLOSED'}

    # noinspection PyUnusedLocal
    def draw(self, context):
        import_box = self.layout.box()
        import_box.operator(ImportHKXMapCollision.bl_idname)
        quick_import_box = import_box.box()
        quick_import_box.label(text="Game Collision Import")
        quick_import_box.prop(context.scene.soulstruct_settings, "use_bak_file", text="From .BAK File")
        quick_import_box.prop(context.scene.soulstruct_game_enums, "hkx_map_collision")
        quick_import_box.operator(ImportHKXMapCollisionFromHKXBHD.bl_idname)

        msb_import_box = import_box.box()
        msb_import_box.label(text="Game MSB Part Import")
        msb_import_box.prop(context.scene.soulstruct_settings, "use_bak_file", text="From .BAK File")
        msb_import_box.prop(context.scene.soulstruct_game_enums, "hkx_map_collision_parts")
        msb_import_box.operator(ImportMSBMapCollision.bl_idname, text="Import Collision Part")

        export_box = self.layout.box()
        export_box.operator(ExportLooseHKXMapCollision.bl_idname)
        export_box.operator(ExportHKXMapCollisionIntoBinder.bl_idname)
        quick_export_box = export_box.box()
        quick_export_box.label(text="Game Collision Export")
        quick_export_box.prop(
            context.scene.soulstruct_settings, "detect_map_from_parent", text="Detect Map from Parent"
        )
        quick_export_box.operator(ExportHKXMapCollisionIntoHKXBHD.bl_idname)

        msb_export_box = export_box.box()
        msb_export_box.label(text="Game MSB Part Export")
        msb_export_box.prop(context.scene.soulstruct_settings, "detect_map_from_parent", text="Detect Map from Parent")
        msb_export_box.prop(context.scene.soulstruct_game_enums, "hkx_map_collision_parts")
        msb_export_box.operator(ExportMSBMapCollision.bl_idname, text="Export Collision Part")

        misc_operators_box = self.layout.box()
        # Useful in particular for creating HKX map collisions (e.g. from FLVER or high <> low res).
        misc_operators_box.operator(CopyMeshSelectionOperator.bl_idname)
