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

    "MSBExportSettings",
    "ExportMSBMapPieces",
    "ExportMSBCollisions",
    "ExportMSBNavmeshes",
    "ExportCompleteMapNavigation",

    "MSBImportPanel",
    "MSBExportPanel",
]

from .msb_import import *
from .msb_export import *

import bpy


class MSBImportPanel(bpy.types.Panel):
    """Panel for Soulstruct MSB import operators."""
    bl_label = "MSB Import"
    bl_idname = "SCENE_PT_msb_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct MSB"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        msb_settings_box = self.layout.box()
        msb_settings_box.label(text="MSB Import Settings")
        msb_settings_box.prop(context.scene.msb_import_settings, "part_name_match")
        msb_settings_box.prop(context.scene.msb_import_settings, "part_name_match_mode")
        msb_settings_box.prop(context.scene.msb_import_settings, "include_pattern_in_parent_name")

        map_piece_box = self.layout.box()
        flver_settings_box = map_piece_box.box()
        flver_settings_box.label(text="FLVER Import Settings")
        for prop in (
            "import_textures",
            "material_blend_mode",
            "base_edit_bone_length",
        ):
            flver_settings_box.prop(context.scene.flver_import_settings, prop)
        map_piece_box.prop(context.scene.soulstruct_game_enums, "map_piece_part", text="Map Piece")
        map_piece_box.operator(ImportMSBMapPiece.bl_idname)
        # TODO: confirmation dialog for below
        map_piece_box.label(text="WARNING: Very slow!")
        map_piece_box.operator(ImportAllMSBMapPieces.bl_idname, text="Import All Map Pieces")

        collision_box = self.layout.box()
        collision_box.prop(context.scene.soulstruct_game_enums, "hkx_map_collision_part", text="Collision")
        collision_box.operator(ImportMSBMapCollision.bl_idname)
        # TODO: confirmation dialog for below
        collision_box.label(text="WARNING: Moderately slow!")
        collision_box.operator(ImportAllMSBMapCollisions.bl_idname, text="Import All Collisions")

        navmesh_box = self.layout.box()
        navmesh_box.prop(context.scene.soulstruct_game_enums, "navmesh_part", text="Navmesh")
        navmesh_box.operator(ImportMSBNavmesh.bl_idname)
        navmesh_box.label(text="WARNING: Slightly slow!")
        navmesh_box.operator(ImportAllMSBNavmeshes.bl_idname)

        character_box = self.layout.box()
        character_box.prop(context.scene.soulstruct_game_enums, "character_part", text="Character")
        character_box.operator(ImportMSBCharacter.bl_idname)
        # TODO: confirmation dialog for below
        character_box.label(text="WARNING: Very slow!")
        character_box.operator(ImportAllMSBCharacters.bl_idname)


class MSBExportPanel(bpy.types.Panel):
    """Panel for Soulstruct MSB export operators."""
    bl_label = "MSB Export"
    bl_idname = "SCENE_PT_msb_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Soulstruct MSB"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        flver_export_settings_box = self.layout.box()
        flver_export_settings_box.label(text="FLVER Export Settings")

        for prop in (
            "export_textures",
            "base_edit_bone_length",
            "allow_missing_textures",
            "allow_unknown_texture_types",
        ):
            flver_export_settings_box.prop(context.scene.flver_export_settings, prop)

        msb_export_box = self.layout.box()
        msb_export_box.prop(context.scene.soulstruct_settings, "detect_map_from_collection")
        msb_export_box.prop(context.scene.msb_export_settings, "export_msb_data_only")

        map_piece_box = self.layout.box()
        map_piece_box.operator(ExportMSBMapPieces.bl_idname)

        collision_box = self.layout.box()
        collision_box.operator(ExportMSBCollisions.bl_idname)

        navmesh_box = self.layout.box()
        navmesh_box.operator(ExportMSBNavmeshes.bl_idname)
        navmesh_box.label(text="Complete MSB Navmeshes + NVMBND + NVMDUMP Export:")
        navmesh_box.operator(ExportCompleteMapNavigation.bl_idname)
