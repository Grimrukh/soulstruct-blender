from __future__ import annotations

__all__ = [
    "FLVERToolSettings",
]

import bpy

from soulstruct.base.models.flver.material import Material

_MASK_ID_STRINGS = []


# noinspection PyUnusedLocal
def _get_display_mask_id_items(self, context) -> list[tuple[str, str, str]]:
    """Dynamic `EnumProperty` that iterates over all materials of selected meshes to find all unique Model Mask IDs."""
    _MASK_ID_STRINGS.clear()
    _MASK_ID_STRINGS.append("No Mask")
    items = [
        ("-1", "No Mask", "Select all materials that do not have a display mask"),
    ]  # type: list[tuple[str, str, str]]

    mask_id_set = set()  # type: set[str]
    for obj in context.selected_objects:
        if obj.type != "MESH":
            continue
        for mat in obj.data.materials:
            if match := Material.DISPLAY_MASK_RE.match(mat.name):
                mask_id = match.group(1)
                mask_id_set.add(mask_id)
    for mask_id in sorted(mask_id_set):
        _MASK_ID_STRINGS.append(mask_id)
        items.append(
            (mask_id, f"Mask {mask_id}", f"Select all materials with display mask {mask_id}")
        )
    return items


class FLVERToolSettings(bpy.types.PropertyGroup):
    """Holds settings for the various operators below. Drawn manually in operator browser windows."""

    vertex_color_layer_name: bpy.props.StringProperty(
        name="Vertex Color Layer",
        description="Name of the vertex color layer to use for setting vertex alpha",
        default="VertexColors0",
    )
    vertex_alpha: bpy.props.FloatProperty(
        name="Alpha",
        description="Alpha value to set for selected vertices",
        default=1.0,
        min=0.0,
        max=1.0,
    )
    set_selected_face_vertex_alpha_only: bpy.props.BoolProperty(
        name="Set Selected Face Vertex Alpha Only",
        description="Only set alpha values for loops (face corners) that are part of selected faces",
        default=False,
    )
    dummy_id_draw_enabled: bpy.props.BoolProperty(name="Draw Dummy IDs", default=False)
    dummy_id_font_size: bpy.props.IntProperty(name="Dummy ID Font Size", default=16, min=1, max=100)

    uv_scale: bpy.props.FloatProperty(
        name="UV Scale",
        description="Scale to apply to UVs after unwrapping",
        default=1.0,
        min=0.0,
    )

    rebone_target_bone: bpy.props.StringProperty(
        name="Rebone Target Bone",
        description="New bone (vertex group) to assign to vertices with 'Rebone Vertices' operator",
    )

    display_mask_id: bpy.props.EnumProperty(
        name="Display Mask",
        items=_get_display_mask_id_items,
    )
