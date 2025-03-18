from __future__ import annotations

__all__ = [
    "MiscOutlinerSettings",
    "ShowAllModels",
    "ShowAllGameModels",
    "ShowAllObjectModels",
    "ShowAllCharacterModels",
    "ShowAllMapModels",
    "ShowAllMapPieceModels",
    "ShowAllCollisionModels",
    "ShowAllNavmeshModels",

    "ShowAllMSB",
    "ShowAllMSBMapPieceParts",
    "ShowAllMSBCollisionParts",
    "ShowAllMSBNavmeshParts",
    "ShowAllMSBConnectCollisionParts",
    "ShowAllMSBObjectParts",
    "ShowAllMSBCharacterParts",
    "ShowAllMSBPlayerStartParts",
    "ShowAllMSBRegionsEvents",
]

import re
import typing as tp

import bpy

from io_soulstruct.utilities import LoggingOperator


class MiscOutlinerSettings(bpy.types.PropertyGroup):

    collection_mode: bpy.props.EnumProperty(
        name="Collection Mode",
        items=[
            ("ACTIVE", "Active", "Show/hide Collection operators affect active Collection (and its children) only"),
            ("ACTIVE_MAP", "Active Map", "Show/hide Collection operators affect Collections for active map stem only"),
            ("ALL", "All", "Show/hide Collection operators affect all collections"),
        ],
        default="ACTIVE",
    )

    def get_collection_filter(self, context: bpy.types.Context) -> tp.Callable[[bpy.types.Collection], bool]:
        """Get Collection filter function, with context's active Collection and active map stem baked in."""

        active_col = context.collection
        active_map_stem = context.scene.soulstruct_settings.map_stem

        if self.collection_mode == "ACTIVE":

            def is_collection(col):
                # Note that Collection instances aren't identical; we have to check names.
                return col.name == active_col.name or col.name in [c.name for c in active_col.children_recursive]

        elif self.collection_mode == "ACTIVE_MAP":

            def is_collection(col):
                return col.name.startswith(active_map_stem)

        else:

            def is_collection(col):
                return True

        return is_collection


class _BaseShowHideCollectionOperator(LoggingOperator):

    CONFIRM_SHOW: tp.ClassVar[bool] = False
    LABEL: tp.ClassVar[str]
    COLLECTION_REGEX: tp.ClassVar[re.Pattern]

    show: bool  # property

    def invoke(self, context, event):
        """Confirmation dialog, since it may be slow."""
        if self.show and self.CONFIRM_SHOW:
            return context.window_manager.invoke_confirm(self, event, message=f"Enable {self.LABEL}?")
        return self.execute(context)

    def execute(self, context):
        return self._set_collection_visibility(context, self.COLLECTION_REGEX, self.show)

    @staticmethod
    def _set_collection_visibility(context: bpy.types.Context, pattern: re.Pattern, visibility: bool) -> set[str]:
        """Set visibility of all objects in the given model collection type."""
        collection_filter = context.scene.misc_outliner_settings.get_collection_filter(context)

        layer_col = context.view_layer.layer_collection
        for collection in _BaseShowHideCollectionOperator._get_layer_collection_recursive(layer_col):
            if not pattern.match(collection.name):
                continue  # cheaper to check this first
            if not collection_filter(collection):
                continue  # ignore matching collection (not active/active map)
            collection.hide_viewport = not visibility

        return {"FINISHED"}

    @staticmethod
    def _get_layer_collection_recursive(layer_col: bpy.types.LayerCollection):
        collections = []
        for child in layer_col.children:
            collections.append(child)
            collections.extend(_BaseShowHideCollectionOperator._get_layer_collection_recursive(child))  # depth first
        return collections


class ShowAllModels(_BaseShowHideCollectionOperator):

    bl_idname = "outliner.show_all_models"
    bl_label = "Show/Hide Models Collections"
    bl_description = "Show/hide all Models collections in the outliner"

    CONFIRM_SHOW = True
    LABEL = "Models"
    COLLECTION_REGEX = re.compile(r".* Models")

    show: bpy.props.BoolProperty(name="Show", default=True)


class ShowAllGameModels(_BaseShowHideCollectionOperator):

    bl_idname = "outliner.show_all_game_models"
    bl_label = "Show/Hide Game Models"
    bl_description = "Show/hide the generic Game Models collection in the outliner"

    CONFIRM_SHOW = True
    LABEL = "Game Models"
    COLLECTION_REGEX = re.compile("^Game Models$")  # exact match

    show: bpy.props.BoolProperty(name="Show", default=True)


class ShowAllObjectModels(_BaseShowHideCollectionOperator):

    bl_idname = "outliner.show_all_object_models"
    bl_label = "Show/Hide Object Models"
    bl_description = "Show/hide the generic Object Models collection in the outliner"

    CONFIRM_SHOW = True
    LABEL = "Object Models"
    COLLECTION_REGEX = re.compile("^Object Models$")  # exact match

    show: bpy.props.BoolProperty(name="Show", default=True)


class ShowAllCharacterModels(_BaseShowHideCollectionOperator):

    bl_idname = "outliner.show_all_character_models"
    bl_label = "Show/Hide Character Models"
    bl_description = "Show/hide the generic Character Models collection in the outliner"

    CONFIRM_SHOW = True
    LABEL = "Character Models"
    COLLECTION_REGEX = re.compile("^Character Models$")  # exact match

    show: bpy.props.BoolProperty(name="Show", default=True)


class ShowAllMapModels(_BaseShowHideCollectionOperator):

    bl_idname = "outliner.show_all_map_models"
    bl_label = "Show/Hide Map Models"
    bl_description = "Show/hide all map-specific Models collection in the outliner"

    CONFIRM_SHOW = True
    LABEL = "Map Models"
    COLLECTION_REGEX = re.compile(r"^m\d\d_\d\d_\d\d_\d\d Models$")

    show: bpy.props.BoolProperty(name="Show", default=True)


class ShowAllMapPieceModels(_BaseShowHideCollectionOperator):

    bl_idname = "outliner.show_all_map_piece_models"
    bl_label = "Show/Hide All Map Piece Models"
    bl_description = "Show/hide all Map Piece models in the outliner (WARNING: may be slow with many models)"

    CONFIRM_SHOW = True
    LABEL = "Map Piece Models"
    COLLECTION_REGEX = re.compile(r"^m\d\d_\d\d_\d\d_\d\d Map Piece Models$")

    show: bpy.props.BoolProperty(name="Show", default=True)


class ShowAllCollisionModels(_BaseShowHideCollectionOperator):

    bl_idname = "outliner.show_all_collision_models"
    bl_label = "Show/Hide All Collision Models"
    bl_description = "Show/hide all Collision models in the outliner"

    LABEL = "Collision Models"
    COLLECTION_REGEX = re.compile(r"^m\d\d_\d\d_\d\d_\d\d Collision Models$")

    show: bpy.props.BoolProperty(name="Show", default=True)


class ShowAllNavmeshModels(_BaseShowHideCollectionOperator):

    bl_idname = "outliner.show_all_navmesh_models"
    bl_label = "Show/Hide All Navmesh Models"
    bl_description = "Show/hide all Navmesh models in the outliner"

    LABEL = "Navmesh Models"
    COLLECTION_REGEX = re.compile(r"^m\d\d_\d\d_\d\d_\d\d Navmesh Models$")

    show: bpy.props.BoolProperty(name="Show", default=True)


class ShowAllMSB(_BaseShowHideCollectionOperator):

    bl_idname = "outliner.show_all_msb"
    bl_label = "Show/Hide MSB Collections"
    bl_description = "Show/hide the parent MSB Collections in the outliner"

    CONFIRM_SHOW = True
    LABEL = "MSB"
    COLLECTION_REGEX = re.compile(r"^m\d\d_\d\d_\d\d_\d\d MSB$")

    show: bpy.props.BoolProperty(name="Show", default=True)


class ShowAllMSBMapPieceParts(_BaseShowHideCollectionOperator):

    bl_idname = "outliner.show_all_msb_map_piece_parts"
    bl_label = "Show/Hide All MSB Map Piece Parts"
    bl_description = "Show/hide all MSB Map Piece parts in the outliner"

    CONFIRM_SHOW = True
    LABEL = "Map Piece Parts"
    COLLECTION_REGEX = re.compile(r"^m\d\d_\d\d_\d\d_\d\d Map Piece Parts$")

    show: bpy.props.BoolProperty(name="Show", default=True)


class ShowAllMSBCollisionParts(_BaseShowHideCollectionOperator):

    bl_idname = "outliner.show_all_msb_collision_parts"
    bl_label = "Show/Hide All MSB Collision Parts"
    bl_description = "Show/hide all MSB Collision parts in the outliner"

    LABEL = "Collision Parts"
    COLLECTION_REGEX = re.compile(r"^m\d\d_\d\d_\d\d_\d\d Collision Parts$")

    show: bpy.props.BoolProperty(name="Show", default=True)


class ShowAllMSBNavmeshParts(_BaseShowHideCollectionOperator):

    bl_idname = "outliner.show_all_msb_navmesh_parts"
    bl_label = "Show/Hide All MSB Navmesh Parts"
    bl_description = "Show/hide all MSB Navmesh parts in the outliner"

    LABEL = "Navmesh Parts"
    COLLECTION_REGEX = re.compile(r"^m\d\d_\d\d_\d\d_\d\d Navmesh Parts$")

    show: bpy.props.BoolProperty(name="Show", default=True)


class ShowAllMSBConnectCollisionParts(_BaseShowHideCollectionOperator):

    bl_idname = "outliner.show_all_msb_connect_collision_parts"
    bl_label = "Show/Hide All MSB Connect Collision Parts"
    bl_description = "Show/hide all MSB Connect Collision parts in the outliner"

    LABEL = "Connect Collision Parts"
    COLLECTION_REGEX = re.compile(r"^m\d\d_\d\d_\d\d_\d\d Connect Collision Parts$")

    show: bpy.props.BoolProperty(name="Show", default=True)


class ShowAllMSBObjectParts(_BaseShowHideCollectionOperator):

    bl_idname = "outliner.show_all_msb_object_parts"
    bl_label = "Show/Hide All MSB Object Parts"
    bl_description = "Show/hide all MSB Object parts in the outliner"

    CONFIRM_SHOW = True
    LABEL = "Object Parts"
    COLLECTION_REGEX = re.compile(r"^m\d\d_\d\d_\d\d_\d\d Object Parts$")

    show: bpy.props.BoolProperty(name="Show", default=True)


class ShowAllMSBCharacterParts(_BaseShowHideCollectionOperator):

    bl_idname = "outliner.show_all_msb_character_parts"
    bl_label = "Show/Hide All MSB Character Parts"
    bl_description = "Show/hide all MSB Character parts in the outliner"

    CONFIRM_SHOW = True
    LABEL = "Character Parts"
    COLLECTION_REGEX = re.compile(r"^m\d\d_\d\d_\d\d_\d\d Character Parts$")

    show: bpy.props.BoolProperty(name="Show", default=True)


class ShowAllMSBPlayerStartParts(_BaseShowHideCollectionOperator):

    bl_idname = "outliner.show_all_msb_player_start_parts"
    bl_label = "Show/Hide All MSB Player Start Parts"
    bl_description = "Show/hide all MSB Player Start parts in the outliner"

    LABEL = "Player Start Parts"
    COLLECTION_REGEX = re.compile(r"^m\d\d_\d\d_\d\d_\d\d Player Start Parts$")

    show: bpy.props.BoolProperty(name="Show", default=True)


class ShowAllMSBRegionsEvents(_BaseShowHideCollectionOperator):

    bl_idname = "outliner.show_all_msb_regions_events"
    bl_label = "Show/Hide All MSB Regions/Events"
    bl_description = "Show/hide all MSB Regions/Events in the outliner"

    LABEL = "Regions/Events"
    COLLECTION_REGEX = re.compile(r"^m\d\d_\d\d_\d\d_\d\d Regions/Events")

    show: bpy.props.BoolProperty(name="Show", default=True)
