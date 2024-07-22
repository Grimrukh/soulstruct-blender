__all__ = [
    "MSBImportSettings",

    "ImportMSBMapPiece",
    "ImportAllMSBMapPieces",

    "ImportMSBMapCollision",
    "ImportAllMSBMapCollisions",

    "ImportMSBConnectCollision",
    "ImportAllMSBConnectCollisions",

    "ImportMSBNavmesh",
    "ImportAllMSBNavmeshes",

    "ImportMSBCharacter",
    "ImportAllMSBCharacters",

    "ImportMSBObject",
    "ImportAllMSBObjects",

    "ImportMSBAsset",
    "ImportAllMSBAssets",

    "ImportMSBPoint",
    "ImportMSBVolume",
    "ImportAllMSBPoints",
    "ImportAllMSBVolumes",

    "MSBImportPanel",
]

from io_soulstruct.general.core import SoulstructSettings
from .parts import *
from .regions import *
from .settings import *

import bpy


class MSBImportPanel(bpy.types.Panel):
    """Panel for Soulstruct MSB import operators."""
    bl_label = "MSB Import"
    bl_idname = "SCENE_PT_msb_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MSB"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):

        ss_settings = context.scene.soulstruct_settings  # type: SoulstructSettings

        msb_settings_box = self.layout.box()
        msb_settings_box.label(text="IMPORT SETTINGS")
        msb_settings_box.label(text="Entry Name Match:")
        msb_settings_box.prop(context.scene.msb_import_settings, "entry_name_match", text="")
        msb_settings_box.label(text="Match Mode:")
        msb_settings_box.prop(context.scene.msb_import_settings, "entry_name_match_mode", text="")
        msb_settings_box.prop(context.scene.msb_import_settings, "include_pattern_in_parent_name")

        map_piece_box = self.layout.box()
        # We re-expose FLVER import settings for MSB map pieces here.
        flver_settings_box = map_piece_box.box()
        flver_settings_box.label(text="FLVER Import Settings")
        for prop in (
            "import_textures",
            "omit_default_bone",
            "material_blend_mode",
            "base_edit_bone_length",
        ):
            flver_settings_box.prop(context.scene.flver_import_settings, prop)
        map_piece_box.label(text="Map Piece:")
        map_piece_box.prop(context.scene.soulstruct_game_enums, "map_piece_part", text="")
        map_piece_box.operator(ImportMSBMapPiece.bl_idname)
        map_piece_box.operator(ImportAllMSBMapPieces.bl_idname)  # uses confirmation dialog

        collision_box = self.layout.box()
        collision_box.label(text="Collision Import Settings")
        # TODO: Hiding collision submesh split option. Too annoying with MSB Part instances.
        # collision_box.prop(context.scene.hkx_map_collision_import_settings, "merge_submeshes")
        collision_box.label(text="Collision:")
        collision_box.prop(context.scene.soulstruct_game_enums, "collision_part", text="")
        collision_box.operator(ImportMSBMapCollision.bl_idname)
        collision_box.operator(ImportAllMSBMapCollisions.bl_idname)  # uses confirmation dialog

        navmesh_box = self.layout.box()
        navmesh_box.label(text="Navmesh:")
        navmesh_box.prop(context.scene.soulstruct_game_enums, "navmesh_part", text="")
        navmesh_box.operator(ImportMSBNavmesh.bl_idname)
        navmesh_box.operator(ImportAllMSBNavmeshes.bl_idname)  # uses confirmation dialog

        character_box = self.layout.box()
        character_box.label(text="Character:")
        character_box.prop(context.scene.soulstruct_game_enums, "character_part", text="")
        character_box.operator(ImportMSBCharacter.bl_idname)
        character_box.operator(ImportAllMSBCharacters.bl_idname)  # uses confirmation dialog

        if ss_settings.is_game("ELDEN_RING"):
            asset_box = self.layout.box()
            asset_box.label(text="Asset:")
            asset_box.prop(context.scene.soulstruct_game_enums, "asset_part", text="")
            asset_box.operator(ImportMSBAsset.bl_idname)
            asset_box.operator(ImportAllMSBAssets.bl_idname)  # uses confirmation dialog
        else:
            object_box = self.layout.box()
            object_box.label(text="Object:")
            object_box.prop(context.scene.soulstruct_game_enums, "object_part", text="")
            object_box.operator(ImportMSBObject.bl_idname)
            object_box.operator(ImportAllMSBObjects.bl_idname)  # uses confirmation dialog

        connect_col_box = self.layout.box()
        connect_col_box.label(text="Connect Collision:")
        connect_col_box.prop(context.scene.soulstruct_game_enums, "connect_collision_part", text="")
        connect_col_box.operator(ImportMSBConnectCollision.bl_idname)
        connect_col_box.operator(ImportAllMSBConnectCollisions.bl_idname)  # uses confirmation dialog

        region_box = self.layout.box()
        region_box.label(text="Point Region:")
        region_box.prop(context.scene.soulstruct_game_enums, "point_region", text="")
        region_box.operator(ImportMSBPoint.bl_idname)
        region_box.operator(ImportAllMSBPoints.bl_idname)  # uses confirmation dialog
        region_box.label(text="Volume Region:")
        region_box.prop(context.scene.soulstruct_game_enums, "volume_region", text="")
        region_box.operator(ImportMSBVolume.bl_idname)
        region_box.operator(ImportAllMSBVolumes.bl_idname)  # uses confirmation dialog
