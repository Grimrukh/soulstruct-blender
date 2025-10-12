"""Panel collection of various operators that haven't found a better home yet."""
from __future__ import annotations

__all__ = [
    "MiscSoulstructMeshOperatorsPanel",
    "MiscSoulstructCollectionOperatorsPanel",
    "MiscSoulstructOtherOperatorsPanel",
]

import bpy

from soulstruct.blender.bpy_base.panel import SoulstructPanel
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

        # Root 'Models' collection (affecting all maps).
        self._draw_collection_operators(context, layout, "Models", "Models:")
        # Singleton model collections (not map-specific).
        self._draw_collection_operators(context, layout, "Game Models", "  Game Models")
        self._draw_collection_operators(context, layout, "Character Models", "    Character Models")
        self._draw_collection_operators(context, layout, "Object Models", "    Object Models")

        # Regex operators (affecting all maps).
        header, panel = layout.panel("All Maps", default_closed=True)
        header.label(text="All Maps")
        if panel:
            self._draw_collection_operators(context, panel, r"m[_\d]+ Models", "All Map Models", use_regex=True)
            self._draw_collection_operators(context, panel, r"m[_\d]+ Map Piece Models", "  All Map Piece Models", use_regex=True)
            self._draw_collection_operators(context, panel, r"m[_\d]+ Collision Models", "  All Collision Models", use_regex=True)
            self._draw_collection_operators(context, panel, r"m[_\d]+ Navmesh Models", "  All Navmesh Models", use_regex=True)

        # Active map-specific collections.
        header, panel = layout.panel("Active Map", default_closed=True)
        header.label(text="Active Map")
        if panel:
            self._draw_collection_operators(context, layout, "{map_stem} Models", "Active Map Models")
            self._draw_collection_operators(context, layout, "{map_stem} Map Piece Models", "  Map Piece Models")
            self._draw_collection_operators(context, layout, "{map_stem} Collision Models", "  Collision Models")
            self._draw_collection_operators(context, layout, "{map_stem} Navmesh Models", "  Navmesh Models")

        # Root 'MSBs' collection (affecting all maps).
        self._draw_collection_operators(context, layout, "MSBs", "MSBs:")

        # Regex operators (affecting all maps).
        header, panel = layout.panel("All Maps", default_closed=True)
        header.label(text="All Maps")
        if panel:
            self._draw_collection_operators(context, panel, r"m[_\d]+ MSB", "All MSBs", use_regex=True)
            self._draw_collection_operators(context, panel, r"m[_\d]+ Regions/Events", "  All Regions/Events", use_regex=True)
            self._draw_collection_operators(context, panel, r"m[_\d]+ Parts", "  All MSB Parts", use_regex=True)
            self._draw_collection_operators(context, panel, r"m[_\d]+ Map Piece Parts", "    All Map Pieces", use_regex=True)
            self._draw_collection_operators(context, panel, r"m[_\d]+ Object Parts", "    All Objects", use_regex=True)
            self._draw_collection_operators(context, panel, r"m[_\d]+ Character Parts", "    All Characters", use_regex=True)
            self._draw_collection_operators(context, panel, r"m[_\d]+ Player Start Parts", "    All Player Starts", use_regex=True)
            self._draw_collection_operators(context, panel, r"m[_\d]+ Collision Parts", "    All Collisions", use_regex=True)
            self._draw_collection_operators(context, panel, r"m[_\d]+ Navmesh Parts", "    All Navmeshes", use_regex=True)
            self._draw_collection_operators(context, panel, r"m[_\d]+ Connect Collision Parts", "    All Connect Collisions", use_regex=True)

        header, panel = layout.panel("Active Map", default_closed=True)
        header.label(text="Active Map")
        if panel:
            self._draw_collection_operators(context, panel, "{map_stem} MSB", "Active MSB")
            self._draw_collection_operators(context, panel, "{map_stem} Regions/Events", "  Regions/Events")
            self._draw_collection_operators(context, panel, "{map_stem} Parts", "  Parts")
            self._draw_collection_operators(context, panel, "{map_stem} Map Piece Parts", "    Map Pieces")
            self._draw_collection_operators(context, panel, "{map_stem} Object Parts", "    Objects")
            self._draw_collection_operators(context, panel, "{map_stem} Character Parts", "    Characters")
            self._draw_collection_operators(context, panel, "{map_stem} Player Start Parts", "    Player Starts")
            self._draw_collection_operators(context, panel, "{map_stem} Collision Parts", "    Collisions")
            self._draw_collection_operators(context, panel, "{map_stem} Navmesh Parts", "    Navmeshes")
            self._draw_collection_operators(context, panel, "{map_stem} Connect Collision Parts", "    Connect Collisions")

    @staticmethod
    def _draw_collection_operators(context, layout, name: str, label: str, use_regex=False):
        row = layout.row()
        row.label(text=label)

        if use_regex:
            all_hidden = _are_all_collections_hidden(context, name)
            if all_hidden is None:
                row.label(text="<MISSING>")
                return
            is_hidden = all_hidden
        else:
            is_hidden = _is_collection_hidden(context, name)
            if is_hidden is None:
                row.label(text="<MISSING>")
                return

        # The icon here is an indicator of current state, like in the Outliner, not the button's function.
        if is_hidden:
            operator = row.operator(ShowCollectionOperator.bl_idname, text="", icon="HIDE_ON")
            operator.name = name
            operator.use_regex = use_regex
        else:
            operator = row.operator(HideCollectionOperator.bl_idname, text="", icon="HIDE_OFF")
            operator.name = name
            operator.use_regex = use_regex


def _is_collection_hidden(context: bpy.types.Context, name: str) -> bool | None:
    """Detect if collection with `name` is currently hidden in viewport."""
    coll = find_layer_collection(context, name)
    if not coll:
        return None
    return coll.hide_viewport


def _are_all_collections_hidden(context: bpy.types.Context, pattern_str: str) -> bool | None:
    """Detect if ALL collections matching `pattern_str` are currently hidden in viewport.

    We check all-hidden rather than any-hidden (or all-visible) so we only turn ALL ON with the regex operators if
    all are currently off (as ALL ON is the less common and more intensive operation).
    """
    colls = find_layer_collections_re(context, pattern_str)
    if not colls:
        return None
    return all(coll.hide_viewport for coll in colls)


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
