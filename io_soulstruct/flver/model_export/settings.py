from __future__ import annotations

__all__ = ["FLVERExportSettings"]

import bpy


class FLVERExportSettings(bpy.types.PropertyGroup):
    """Common FLVER export settings. Drawn manually in operator browser windows."""

    export_textures: bpy.props.BoolProperty(
        name="Export Textures",
        description="Export textures used by FLVER into bundled TPF, split CHRTPFBDT, or a map TPFBHD. Only works "
                    "when using a type-specific FLVER export operator. DDS formats for different texture types can be "
                    "set. Be wary of texture degradation from repeated DDS conversion at import/export",
        default=False,
    )

    base_edit_bone_length: bpy.props.FloatProperty(
        name="Base Edit Bone Length",
        description="Length of edit bones corresponding to bone scale 1",
        default=0.2,
        min=0.01,
    )

    allow_missing_textures: bpy.props.BoolProperty(
        name="Allow Missing Textures",
        description="Allow MTD-defined textures to have no node image data in Blender",
        default=False,
    )

    allow_unknown_texture_types: bpy.props.BoolProperty(
        name="Allow Unknown Texture Types",
        description="Allow and export Blender texture nodes that have non-MTD-defined texture types",
        default=False,
    )
