from __future__ import annotations

__all__ = [
    "MSBImportSettings",
]

import bpy


class MSBImportSettings(bpy.types.PropertyGroup):
    """Common MSB import settings. Drawn manually in operator browser windows."""

    part_name_match: bpy.props.StringProperty(
        name="MSB Part Name Match",
        description="Glob/Regex for filtering MSB part names when importing all parts",
        default="*",
    )

    part_name_match_mode: bpy.props.EnumProperty(
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
