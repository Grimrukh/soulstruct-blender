"""Panel collection of various operators that haven't found a better home yet."""
from __future__ import annotations

__all__ = [
    "MiscSoulstructMeshOperatorsPanel",
    "MiscSoulstructCollectionOperatorsPanel",
    "MiscSoulstructOtherOperatorsPanel",
]

import bpy

from io_soulstruct.bpy_base.panel import SoulstructPanel
from .misc_mesh import *
from .misc_other import *
from .misc_outliner import *


class MiscSoulstructMeshOperatorsPanel(SoulstructPanel):

    bl_label = "Mesh Operators"
    bl_idname = "SCENE_PT_misc_soulstruct_mesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Misc. Soulstruct"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        layout.label(text="Mesh Tools:")
        layout.operator(CopyMeshSelectionOperator.bl_idname)
        layout.operator(CutMeshSelectionOperator.bl_idname)
        layout.operator(BooleanMeshCut.bl_idname)
        layout.operator(ApplyLocalMatrixToMesh.bl_idname)
        layout.operator(ScaleMeshIslands.bl_idname)
        layout.operator(SelectActiveMeshVerticesNearSelected.bl_idname)
        layout.operator(ConvexHullOnEachMeshIsland.bl_idname)
        layout.operator(SetActiveFaceNormalUpward.bl_idname)
        layout.operator(SpawnObjectIntoMeshAtFaces.bl_idname)
        layout.operator(WeightVerticesWithFalloff.bl_idname)
        layout.operator(ApplyModifierNonSingleUser.bl_idname)


class MiscSoulstructCollectionOperatorsPanel(SoulstructPanel):

    bl_label = "Collection Operators"
    bl_idname = "SCENE_PT_misc_soulstruct_collection"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Misc. Soulstruct"

    def draw(self, context):
        layout = self.layout

        self.draw_active_map(context, layout)

        layout.separator()
        layout.label(text="Model Collections:")
        self._draw_collection_operators(context, layout, "Models", "All Models")
        self._draw_collection_operators(context, layout, "Game Models", "  Game Models")
        self._draw_collection_operators(context, layout, "Character Models", "    Character Models")
        self._draw_collection_operators(context, layout, "Object Models", "    Object Models")

        self._draw_collection_operators(context, layout, "{map_stem} Models", "  Active Map Models")
        self._draw_collection_operators(context, layout, "{map_stem} Map Piece Models", "    Map Piece Models")
        self._draw_collection_operators(context, layout, "{map_stem} Collision Models", "    Collision Models")
        self._draw_collection_operators(context, layout, "{map_stem} Navmesh Models", "    Navmesh Models")

        layout.separator()

        layout.label(text="MSB Collections:")
        self._draw_collection_operators(context, layout, "MSBs", "All MSBs")
        self._draw_collection_operators(context, layout, "{map_stem} MSB", "Active MSB")

        self._draw_collection_operators(context, layout, "{map_stem} Regions", "  Regions")

        self._draw_collection_operators(context, layout, "{map_stem} Events", "  Events")
        # TODO: Event subtypes.

        self._draw_collection_operators(context, layout, "{map_stem} Parts", "  Parts")
        self._draw_collection_operators(context, layout, "{map_stem} Map Piece Parts", "    Map Pieces")
        self._draw_collection_operators(context, layout, "{map_stem} Object Parts", "    Objects")
        self._draw_collection_operators(context, layout, "{map_stem} Character Parts", "    Characters")
        self._draw_collection_operators(context, layout, "{map_stem} Player Start Parts", "    Player Starts")
        self._draw_collection_operators(context, layout, "{map_stem} Collision Parts", "    Collisions")
        self._draw_collection_operators(context, layout, "{map_stem} Navmesh Parts", "    Navmeshes")
        self._draw_collection_operators(context, layout, "{map_stem} Connect Collision Parts", "    Connect Collisions")

    @staticmethod
    def _draw_collection_operators(context, layout, name: str, label: str):
        row = layout.row()
        row.label(text=label)

        is_hidden = _is_collection_hidden(context, name)
        if is_hidden is None:
            return

        # The icon here is an indicator of current state, like in the Outliner, not the button's function.
        if is_hidden:
            row.operator(ShowCollectionOperator.bl_idname, text="", icon="HIDE_ON").name = name
        else:
            row.operator(HideCollectionOperator.bl_idname, text="", icon="HIDE_OFF").name = name


def _is_collection_hidden(context: bpy.types.Context, name: str) -> bool | None:
    coll = find_layer_collection(context, name)
    if not coll:
        return None
    return coll.hide_viewport


class MiscSoulstructOtherOperatorsPanel(SoulstructPanel):

    bl_label = "Other Operators"
    bl_idname = "SCENE_PT_misc_soulstruct_other"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Misc. Soulstruct"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.operator(PrintGameTransform.bl_idname)
