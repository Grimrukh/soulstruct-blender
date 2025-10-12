from __future__ import annotations

__all__ = [
    "ShowCollectionOperator",
    "HideCollectionOperator",
    "find_layer_collection",
    "find_layer_collections_re",
]

import re

import bpy

from soulstruct.blender.utilities import LoggingOperator


class ShowCollectionOperator(LoggingOperator):
    """Finds the collection of a given name and makes it visible in the viewport.

    Can optionally be set up to use regex instead.
    """

    bl_idname = "outliner.show_collection"
    bl_label = "Show Collection"
    bl_description = "Show the specified Collection"

    # REGISTER removed (internal operator only).
    bl_options = {"UNDO"}

    name: bpy.props.StringProperty(name="Collection Name", default="")
    use_regex: bpy.props.BoolProperty(name="Use Regex", default=False)

    def execute(self, context):
        if self.use_regex:
            colls = find_layer_collections_re(context, self.name)
            for coll in colls:
                coll.hide_viewport = False
            return {"FINISHED"}

        coll = find_layer_collection(context, self.name)
        if coll:
            coll.hide_viewport = False
        return {"FINISHED"}


class HideCollectionOperator(LoggingOperator):

    bl_idname = "outliner.hide_collection"
    bl_label = "Hide Collection"
    bl_description = "Hide the specified Collection"

    # REGISTER removed (internal operator only).
    bl_options = {"UNDO"}

    name: bpy.props.StringProperty(name="Collection Name", default="")
    use_regex: bpy.props.BoolProperty(name="Use Regex", default=False)

    def execute(self, context):
        if self.use_regex:
            colls = find_layer_collections_re(context, self.name)
            for coll in colls:
                coll.hide_viewport = True
            return {"FINISHED"}

        coll = find_layer_collection(context, self.name)
        if coll:
            coll.hide_viewport = True
        return {"FINISHED"}


def find_layer_collection(context: bpy.types.Context, name: str) -> bpy.types.LayerCollection | None:
    """Find a LayerCollection by name, searching recursively through all children of the view layer's
    root LayerCollection."""
    if "{map_stem}" in name:
        name = name.format(map_stem=context.scene.soulstruct_settings.map_stem)
    return _get_layer_collection_recursive(context.view_layer.layer_collection).get(name, None)


def find_layer_collections_re(context: bpy.types.Context, pattern_str: str) -> list[bpy.types.LayerCollection]:
    """Find all LayerCollections whose names FULLY match the regular expression `pattern_str`."""
    if "{map_stem}" in pattern_str:
        pattern_str = pattern_str.format(map_stem=context.scene.soulstruct_settings.map_stem)
    collections_dict = _get_layer_collection_recursive(context.view_layer.layer_collection)
    collections = []
    for name, coll in collections_dict.items():
        if re.fullmatch(pattern_str, name):
            collections.append(coll)
    return collections


def _get_layer_collection_recursive(layer_col: bpy.types.LayerCollection) -> dict[str, bpy.types.LayerCollection]:
    """Return a dictionary mapping LayerCollection names to LayerCollection objects, searching recursively."""
    collections = {}
    for child in layer_col.children:
        collections[child.name] = child
        collections.update(_get_layer_collection_recursive(child))  # depth first
    return collections
