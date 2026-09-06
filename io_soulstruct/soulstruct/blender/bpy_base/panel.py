from __future__ import annotations

__all__ = [
    "SoulstructPanel",
    "smart_prop",
]

import typing as tp

import bpy

from ..base.icons import get_icon_id

# Ordered (most-specific-first) `Panel.__module__` substring -> custom icon name (see `base/icons.py`).
# Checked against every `SoulstructPanel` subclass automatically in `draw_header()` below, so individual Panels
# never need to set this themselves; only the small number of exceptions set `HEADER_ICON` explicitly.
_MODULE_ICON_MAP = (
    (".flver.image.", "dds"),
    (".flver.", "flver"),
    (".msb.", "msb"),
    (".navmesh.", "navmesh"),
    (".nav_graph.", "nav_graph"),
    (".animation.", "animation"),
    (".collision.", "collision"),
    (".cutscene.", "cutscene"),
    (".misc.", "misc"),
    (".general.", "general"),
)


def _detect_icon_name(module_name: str) -> str:
    dotted = f".{module_name}."
    for substring, icon_name in _MODULE_ICON_MAP:
        if substring in dotted:
            return icon_name
    return ""


def _is_plain_bool_prop(data: bpy.types.bpy_struct, property_name: str) -> bool:
    """Detect a single (non-array) `BoolProperty`, i.e. a checkbox/toggle widget.

    Used by `smart_prop()` below to decide whether a `.prop()` call needs the `use_property_split` workaround.
    """
    try:
        rna_prop = data.bl_rna.properties[property_name]
    except (AttributeError, KeyError):
        return False
    return rna_prop.type == "BOOLEAN" and not rna_prop.is_array


def smart_prop(layout: bpy.types.UILayout, data: bpy.types.bpy_struct, prop_name: str, *args, **kwargs):
    """Drop-in replacement for `layout.prop(data, property, ...)` that keeps checkboxes left-anchored.

    Blender's `use_property_split` layout mode does not split a checkbox (`BoolProperty`) into a label column and
    a value column like it does for other property types; instead it shifts the whole checkbox-plus-label widget
    to start at the split point, which centers it in the panel and clips long labels against the panel's right
    edge. The accepted per-widget fix is to disable `use_property_split` for just that one `prop()` call and
    restore it afterward -- this helper does that automatically (only when needed), so call sites don't have to.
    Non-checkbox properties are passed straight through unaffected.
    """
    if layout.use_property_split and _is_plain_bool_prop(data, prop_name):
        layout.use_property_split = False
        try:
            layout.prop(data, prop_name, *args, **kwargs)
            return
        finally:
            layout.use_property_split = True
    layout.prop(data, prop_name, *args, **kwargs)
    return


class SoulstructPanel(bpy.types.Panel):

    # Set to `False` on a subclass whose custom `draw()` should NOT get automatic property-split alignment.
    USE_PROPERTY_SPLIT: tp.ClassVar[bool] = True
    # Set on a subclass to override the automatically-detected header icon, or `""` to suppress it entirely.
    HEADER_ICON: tp.ClassVar[str | None] = None

    def __init_subclass__(cls, **kwargs):
        """Wrap any subclass-defined `draw()` so `use_property_split`/`use_property_decorate` are applied for free,
        without requiring every Panel in the add-on to repeat those two lines themselves."""
        super().__init_subclass__(**kwargs)
        if "draw" in cls.__dict__:
            user_draw = cls.__dict__["draw"]

            def _make_wrapped_draw(_draw):
                def _wrapped_draw(self, context):
                    if self.USE_PROPERTY_SPLIT:
                        self.layout.use_property_split = True
                        self.layout.use_property_decorate = False
                    _draw(self, context)
                return _wrapped_draw

            cls.draw = _make_wrapped_draw(user_draw)

    def draw_header(self, context):
        """Draw a small branded icon in the Panel header, auto-detected from the defining module unless a subclass
        sets `HEADER_ICON` explicitly."""
        icon_name = self.HEADER_ICON
        if icon_name is None:
            icon_name = _detect_icon_name(type(self).__module__)
        if icon_name:
            icon_id = get_icon_id(icon_name)
            if icon_id:
                self.layout.label(text="", icon_value=icon_id)

    def maybe_draw_map_import_operator(
        self,
        context: bpy.types.Context,
        operator_id: str,
        layout: bpy.types.UILayout | None = None,
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
        layout: bpy.types.UILayout | None = None,
        **kwargs,
    ):
        layout = layout or self.layout
        settings = context.scene.soulstruct_settings
        if settings.can_auto_export:
            layout.operator(operator_id, **kwargs)
        else:
            layout.label(text="No export directory set.")

    def draw_active_map(self, context: bpy.types.Context, layout: bpy.types.UILayout | None = None):
        layout = layout or self.layout
        box = layout.box()
        box.label(text=f"Active Map: {context.scene.soulstruct_settings.map_stem}")

    def draw_detected_map(
        self,
        context: bpy.types.Context,
        layout: bpy.types.UILayout | None = None,
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

    def draw_map_stem_choice(self, context: bpy.types.Context, layout: bpy.types.UILayout | None = None):
        layout = layout or self.layout
        map_box = layout.box()

        map_box.label(text="Choose Active Map:")
        map_box.prop(context.scene.soulstruct_settings.game_settings, "map_stem", text="")

        if context.scene.soulstruct_settings.is_game("ELDEN_RING"):
            map_box.label(text="ER Map Selection Filter:")
            map_box.prop(context.scene.soulstruct_settings.eldenring, "map_filter_mode", text="")

        row = map_box.row()
        split = row.split(factor=0.5)
        # We avoid module circularity by using the raw `bl_idname`.
        split.column().operator("soulstruct.select_game_map_directory", text="Select Game Map")
        split.column().operator("soulstruct.select_project_map_directory", text="Select Project Map")
