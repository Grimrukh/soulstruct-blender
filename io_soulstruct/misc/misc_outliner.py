from __future__ import annotations

__all__ = [
    "ShowCollectionOperator",
    "HideCollectionOperator",
    "find_layer_collection",
]

import bpy

from io_soulstruct.utilities import LoggingOperator


class ShowCollectionOperator(LoggingOperator):

    bl_idname = "outliner.show_collection"
    bl_label = "Show Collection"
    bl_description = "Show the specified Collection"

    name: bpy.props.StringProperty(name="Collection Name", default="")

    def execute(self, context):
        coll = find_layer_collection(context, self.name)
        if coll:
            coll.hide_viewport = False
        return {"FINISHED"}


class HideCollectionOperator(LoggingOperator):

    bl_idname = "outliner.hide_collection"
    bl_label = "Hide Collection"
    bl_description = "Hide the specified Collection"

    name: bpy.props.StringProperty(name="Collection Name", default="")

    def execute(self, context):
        coll = find_layer_collection(context, self.name)
        if coll:
            coll.hide_viewport = True
        return {"FINISHED"}


def find_layer_collection(context: bpy.types.Context, name: str) -> bpy.types.LayerCollection | None:
    if "{map_stem}" in name:
        name = name.format(map_stem=context.scene.soulstruct_settings.map_stem)
    return _get_layer_collection_recursive(context.view_layer.layer_collection).get(name, None)


def _get_layer_collection_recursive(layer_col: bpy.types.LayerCollection) -> dict[str, bpy.types.LayerCollection]:
    collections = {}
    for child in layer_col.children:
        collections[child.name] = child
        collections.update(_get_layer_collection_recursive(child))  # depth first
    return collections
