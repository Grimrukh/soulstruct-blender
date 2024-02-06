from __future__ import annotations

__all__ = [
    "FLVERImportSettings",
]

import bpy


class FLVERImportSettings(bpy.types.PropertyGroup):
    """Common FLVER import settings. Drawn manually in operator browser windows."""

    import_textures: bpy.props.BoolProperty(
        name="Import Textures",
        description="Import DDS textures from TPFs in expected locations for detected FLVER model source type",
        default=True,
    )

    material_blend_mode: bpy.props.EnumProperty(
        name="Alpha Blend Mode",
        description="Alpha mode to use for new single-texture FLVER materials",
        items=[
            ("OPAQUE", "Opaque", "Opaque Blend Mode"),
            ("CLIP", "Clip", "Clip Blend Mode"),
            ("HASHED", "Hashed", "Hashed Blend Mode"),
            ("BLEND", "Blend", "Sorted Blend Mode"),
        ],
        default="HASHED",
    )

    base_edit_bone_length: bpy.props.FloatProperty(
        name="Base Edit Bone Length",
        description="Length of edit bones corresponding to bone scale 1",
        default=0.2,
        min=0.01,
    )

    msb_part_name_match: bpy.props.StringProperty(
        name="MSB Part Name Match",
        description="Glob/Regex for filtering MSB part names when importing all parts",
        default="*",
    )

    msb_part_name_match_mode: bpy.props.EnumProperty(
        name="MSB Part Name Match Mode",
        description="Whether to use glob or regex for MSB part name matching",
        items=[
            ("GLOB", "Glob", "Use glob for MSB part name matching"),
            ("REGEX", "Regex", "Use regex for MSB part name matching"),
        ],
        default="GLOB",
    )

    include_pattern_in_parent_name: bpy.props.BoolProperty(
        name="Include Pattern in Parent Name",
        description="Include the glob/regex pattern in the name of the parent object for imported MSB parts",
        default=True,
    )
