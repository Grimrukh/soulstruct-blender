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

    "MSBImportPanel",
]

from .map_pieces import *
from .collisions import *
from .navmeshes import *
from .characters import *
from .regions import *
from .settings import *

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
        msb_settings_box.prop(context.scene.msb_import_settings, "entry_name_match")
        msb_settings_box.prop(context.scene.msb_import_settings, "entry_name_match_mode")
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
        map_piece_box.operator(ImportAllMSBMapPieces.bl_idname)  # uses confirmation dialog

        collision_box = self.layout.box()
        collision_box.prop(context.scene.soulstruct_game_enums, "hkx_map_collision_part", text="Collision")
        collision_box.operator(ImportMSBMapCollision.bl_idname)
        collision_box.operator(ImportAllMSBMapCollisions.bl_idname)  # uses confirmation dialog

        navmesh_box = self.layout.box()
        navmesh_box.prop(context.scene.soulstruct_game_enums, "navmesh_part", text="Navmesh")
        navmesh_box.operator(ImportMSBNavmesh.bl_idname)
        navmesh_box.operator(ImportAllMSBNavmeshes.bl_idname)  # uses confirmation dialog

        character_box = self.layout.box()
        character_box.prop(context.scene.soulstruct_game_enums, "character_part", text="Character")
        character_box.operator(ImportMSBCharacter.bl_idname)
        character_box.operator(ImportAllMSBCharacters.bl_idname)  # uses confirmation dialog

        region_box = self.layout.box()
        region_box.prop(context.scene.soulstruct_game_enums, "point_region", text="Point")
        region_box.operator(ImportMSBPoint.bl_idname)
        region_box.operator(ImportAllMSBPoints.bl_idname)  # uses confirmation dialog
        region_box.prop(context.scene.soulstruct_game_enums, "volume_region", text="Volume")
        region_box.operator(ImportMSBVolume.bl_idname)
        region_box.operator(ImportAllMSBVolumes.bl_idname)  # uses confirmation dialog
