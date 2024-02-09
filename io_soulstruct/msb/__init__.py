__all__ = [
    "MSBImportSettings",
    "ImportMSBMapPiece",
    "ImportAllMSBMapPieces",
    "ImportMSBMapCollision",
    "ImportAllMSBMapCollisions",
    "ImportMSBNavmesh",
    "ImportAllMSBNavmeshes",
    "ImportMSBCharacter",
    "ImportAllMSBCharacters",
    "ImportMSBPoint",
    "ImportMSBVolume",
    "ImportAllMSBPoints",
    "ImportAllMSBVolumes",

    "RegionDrawSettings",
    "draw_region_volumes",

    "MSBExportSettings",
    "ExportMSBMapPieces",
    "ExportMSBCollisions",
    "ExportMSBNavmeshes",
    "ExportCompleteMapNavigation",

    "MSBImportPanel",
    "MSBExportPanel",
    "MSBToolsPanel",
    "MSBRegionPanel",
]

from .msb_import import *
from .msb_export import *
from .draw_regions import *

import bpy


class MSBToolsPanel(bpy.types.Panel):
    """Panel for Soulstruct MSB tool settings/operators."""
    bl_label = "MSB Tools"
    bl_idname = "SCENE_PT_msb_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct MSB"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        region_draw_box = self.layout.box()
        region_draw_box.label(text="Region Draw Settings")
        for prop in RegionDrawSettings.__annotations__:
            region_draw_box.prop(context.scene.region_draw_settings, prop)


class MSBRegionPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window."""
    bl_label = "MSB Region Settings"
    bl_idname = "OBJECT_PT_hello"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout

        obj = context.object
        if obj is not None and obj.type == "EMPTY":
            layout.prop(obj, "region_shape")
        else:
            layout.label(text="No active Empty Object.")
