from __future__ import annotations

__all__ = [
    "ImportHKXMapCollision",
    "ImportHKXMapCollisionWithBinderChoice",
    "ImportHKXMapCollisionWithMSBChoice",
    "ExportHKXMapCollision",
    "ExportHKXMapCollisionIntoBinder",
    "ExportHKXMapCollisionToMapDirectoryBHD",
    "HKX_COLLISION_PT_hkx_map_collision_tools",
]

import importlib
import sys
from pathlib import Path

import bpy

# Force reload of Soulstruct module (for easier updating).
modules_path = str(Path(__file__).parent / "modules")
if modules_path not in sys.path:
    sys.path.append(modules_path)
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

from .import_hkx_map_collision import (
    ImportHKXMapCollision, ImportHKXMapCollisionWithBinderChoice, ImportHKXMapCollisionWithMSBChoice
)
from .export_hkx_map_collision import (
    ExportHKXMapCollision, ExportHKXMapCollisionIntoBinder, ExportHKXMapCollisionToMapDirectoryBHD
)


class HKX_COLLISION_PT_hkx_map_collision_tools(bpy.types.Panel):
    bl_label = "HKX Map Collision Tools"
    bl_idname = "HKX_PT_hkx_map_collision_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "HKX Map Collision"

    # noinspection PyUnusedLocal
    def draw(self, context):
        import_box = self.layout.box()
        import_box.operator(ImportHKXMapCollision.bl_idname)

        export_box = self.layout.box()
        export_box.operator(ExportHKXMapCollision.bl_idname)
        export_box.operator(ExportHKXMapCollisionIntoBinder.bl_idname)

        export_map_settings = context.scene.export_map_directory_settings
        export_to_map_box = self.layout.box()
        export_to_map_box.prop(export_map_settings, "game_directory")
        export_to_map_box.prop(export_map_settings, "map_stem")  # TODO: must match Blender collision name (for now)
        export_to_map_box.operator(ExportHKXMapCollisionToMapDirectoryBHD.bl_idname)
