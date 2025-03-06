from __future__ import annotations

__all__ = [
    "ShowAllMapPieceModels",
    "ShowAllCollisionModels",
    "ShowAllNavmeshModels",
    "ShowAllMSBMapPieceParts",
    "ShowAllMSBCollisionParts",
    "ShowAllMSBNavmeshParts",
    "ShowAllMSBConnectCollisionParts",
    "ShowAllMSBObjectParts",
    "ShowAllMSBCharacterParts",
    "ShowAllMSBPlayerStartParts",
    "ShowAllMSBRegionsEvents",
]

import bpy

from io_soulstruct.utilities import LoggingOperator


def _set_model_collection_visibility(
    operator: LoggingOperator, context: bpy.types.Context, model_type: str, visibility: bool
) -> set[str]:
    """Set visibility of all objects in the given model collection type."""
    models_collection = context.view_layer.layer_collection.children.get("Models")
    if models_collection is None:
        return operator.error(f"Could not find root-level 'Models' collection in current view layer.")

    for map_collection in models_collection.children:
        for map_model_collection in map_collection.children:
            if map_model_collection.name.endswith(f"{model_type} Models"):
                map_model_collection.hide_viewport = not visibility
                break

    return {"FINISHED"}


def _set_msb_collection_visibility(
    operator: LoggingOperator, context: bpy.types.Context, msb_entry_type: str, visibility: bool
) -> set[str]:
    """Set visibility of all objects in the given MSB collection type."""
    msbs_collection = context.view_layer.layer_collection.children.get("MSBs")
    if msbs_collection is None:
        return operator.error(f"Could not find root-level 'MSBs' collection in current view layer.")

    for map_collection in msbs_collection.children:
        map_stem = map_collection.name.split()[0]
        if msb_entry_type.endswith("Parts"):
            parts_collection = map_collection.children.get(f"{map_stem} Parts")
            if parts_collection is not None:
                part_subtype_collection = parts_collection.children.get(f"{map_stem} {msb_entry_type}")
                if part_subtype_collection is not None:
                    part_subtype_collection.hide_viewport = not visibility
        elif msb_entry_type == "Regions/Events":
            regions_events_collection = map_collection.children.get(f"{map_stem} Regions/Events")
            if regions_events_collection is not None:
                regions_events_collection.hide_viewport = not visibility
        else:
            return operator.error(f"Invalid MSB entry type for Show/Hide operator: {msb_entry_type}")

    return {"FINISHED"}


class ShowAllMapPieceModels(LoggingOperator):

    bl_idname = "outliner.show_all_map_piece_models"
    bl_label = "Show/Hide All Map Piece Models"
    bl_description = "Show/hide all Map Piece models in the outliner (WARNING: may be slow with many models)"

    show: bpy.props.BoolProperty(name="Show", default=True)

    def invoke(self, context, event):
        """Confirmation dialog, since it may be slow."""
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        return _set_model_collection_visibility(self, context, "Map Piece", self.show)


class ShowAllCollisionModels(LoggingOperator):

    bl_idname = "outliner.show_all_collision_models"
    bl_label = "Show/Hide All Collision Models"
    bl_description = "Show/hide all Collision models in the outliner"

    show: bpy.props.BoolProperty(name="Show", default=True)

    def invoke(self, context, event):
        """Confirmation dialog, since it may be slow."""
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        return _set_model_collection_visibility(self, context, "Collision", self.show)


class ShowAllNavmeshModels(LoggingOperator):

    bl_idname = "outliner.show_all_navmesh_models"
    bl_label = "Show/Hide All Navmesh Models"
    bl_description = "Show/hide all Navmesh models in the outliner"

    show: bpy.props.BoolProperty(name="Show", default=True)

    def invoke(self, context, event):
        """Confirmation dialog, since it may be slow."""
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        return _set_model_collection_visibility(self, context, "Navmesh", self.show)


class ShowAllMSBMapPieceParts(LoggingOperator):

    bl_idname = "outliner.show_all_msb_map_piece_parts"
    bl_label = "Show/Hide All MSB Map Piece Parts"
    bl_description = "Show/hide all MSB Map Piece parts in the outliner"

    show: bpy.props.BoolProperty(name="Show", default=True)

    def invoke(self, context, event):
        """Confirmation dialog, since it may be slow."""
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        return _set_msb_collection_visibility(self, context, "Map Piece Parts", self.show)


class ShowAllMSBCollisionParts(LoggingOperator):

    bl_idname = "outliner.show_all_msb_collision_parts"
    bl_label = "Show/Hide All MSB Collision Parts"
    bl_description = "Show/hide all MSB Collision parts in the outliner"

    show: bpy.props.BoolProperty(name="Show", default=True)

    def invoke(self, context, event):
        """Confirmation dialog, since it may be slow."""
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        return _set_msb_collection_visibility(self, context, "Collision Parts", self.show)


class ShowAllMSBNavmeshParts(LoggingOperator):

    bl_idname = "outliner.show_all_msb_navmesh_parts"
    bl_label = "Show/Hide All MSB Navmesh Parts"
    bl_description = "Show/hide all MSB Navmesh parts in the outliner"

    show: bpy.props.BoolProperty(name="Show", default=True)

    def invoke(self, context, event):
        """Confirmation dialog, since it may be slow."""
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        return _set_msb_collection_visibility(self, context, "Navmesh Parts", self.show)


class ShowAllMSBConnectCollisionParts(LoggingOperator):

    bl_idname = "outliner.show_all_msb_connect_collision_parts"
    bl_label = "Show/Hide All MSB Connect Collision Parts"
    bl_description = "Show/hide all MSB Connect Collision parts in the outliner"

    show: bpy.props.BoolProperty(name="Show", default=True)

    def invoke(self, context, event):
        """Confirmation dialog, since it may be slow."""
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        return _set_msb_collection_visibility(self, context, "Connect Collision Parts", self.show)


class ShowAllMSBObjectParts(LoggingOperator):

    bl_idname = "outliner.show_all_msb_object_parts"
    bl_label = "Show/Hide All MSB Object Parts"
    bl_description = "Show/hide all MSB Object parts in the outliner"

    show: bpy.props.BoolProperty(name="Show", default=True)

    def invoke(self, context, event):
        """Confirmation dialog, since it may be slow."""
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        return _set_msb_collection_visibility(self, context, "Object Parts", self.show)


class ShowAllMSBCharacterParts(LoggingOperator):

    bl_idname = "outliner.show_all_msb_character_parts"
    bl_label = "Show/Hide All MSB Character Parts"
    bl_description = "Show/hide all MSB Character parts in the outliner"

    show: bpy.props.BoolProperty(name="Show", default=True)

    def invoke(self, context, event):
        """Confirmation dialog, since it may be slow."""
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        return _set_msb_collection_visibility(self, context, "Character Parts", self.show)


class ShowAllMSBPlayerStartParts(LoggingOperator):

    bl_idname = "outliner.show_all_msb_player_start_parts"
    bl_label = "Show/Hide All MSB Player Start Parts"
    bl_description = "Show/hide all MSB Player Start parts in the outliner"

    show: bpy.props.BoolProperty(name="Show", default=True)

    def invoke(self, context, event):
        """Confirmation dialog, since it may be slow."""
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        return _set_msb_collection_visibility(self, context, "Player Start Parts", self.show)


class ShowAllMSBRegionsEvents(LoggingOperator):

    bl_idname = "outliner.show_all_msb_regions_events"
    bl_label = "Show/Hide All MSB Regions/Events"
    bl_description = "Show/hide all MSB Regions/Events in the outliner"

    show: bpy.props.BoolProperty(name="Show", default=True)

    def invoke(self, context, event):
        """Confirmation dialog, since it may be slow."""
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        return _set_msb_collection_visibility(self, context, "Regions/Events", self.show)
