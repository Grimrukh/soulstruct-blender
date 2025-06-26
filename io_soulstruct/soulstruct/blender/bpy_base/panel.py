from __future__ import annotations

__all__ = [
    "SoulstructPanel"
]

import bpy


class SoulstructPanel(bpy.types.Panel):

    def maybe_draw_map_import_operator(
        self,
        context: bpy.types.Context,
        operator_id: str,
        layout: bpy.types.UILayout = None,
        **kwargs,
    ):
        layout = layout or self.layout
        settings = context.scene.soulstruct_settings
        if settings.map_stem:
            layout.operator(operator_id, **kwargs)
        else:
            layout.label(text="No active map.")

    def maybe_draw_export_operator(
        self,
        context: bpy.types.Context,
        operator_id: str,
        layout: bpy.types.UILayout = None,
        **kwargs,
    ):
        layout = layout or self.layout
        settings = context.scene.soulstruct_settings
        if settings.can_auto_export:
            layout.operator(operator_id, **kwargs)
        else:
            layout.label(text="No export directory set.")

    def draw_active_map(self, context: bpy.types.Context, layout: bpy.types.UILayout = None):
        layout = layout or self.layout
        box = layout.box()
        box.label(text=f"Active Map: {context.scene.soulstruct_settings.map_stem}")

    def draw_detected_map(
        self,
        context: bpy.types.Context,
        layout: bpy.types.UILayout = None,
        use_latest_version=False,
        detect_from_collection=False,  # rather than active object
    ):
        """Draw a label showing the detected map.

        If `use_latest_version` is True, the latest version of the detected map will be shown IF smart map version
        handling is enabled globally.
        """
        layout = layout or self.layout
        settings = context.scene.soulstruct_settings
        if detect_from_collection:
            map_stem = settings.get_active_collection_detected_map(context)
        else:
            map_stem = settings.get_active_object_detected_map(context)
        if use_latest_version:
            map_stem = settings.get_latest_map_stem_version(map_stem)

        box = layout.box()
        if not map_stem:
            box.label(text="Detected Map: <None>")
        else:
            box.label(text=f"Detected Map: {map_stem}")

    def draw_map_stem_choice(self, context: bpy.types.Context, layout: bpy.types.UILayout = None):
        layout = layout or self.layout
        map_box = layout.box()
        map_box.label(text="Choose Active Map:")
        map_box.prop(context.scene.soulstruct_settings, "map_stem", text="")
        row = map_box.row()
        split = row.split(factor=0.5)

        # We avoid module circularity by using the raw `bl_idname`.
        split.column().operator("soulstruct.select_game_map_directory", text="Select Game Map")
        split.column().operator("soulstruct.select_project_map_directory", text="Select Project Map")
