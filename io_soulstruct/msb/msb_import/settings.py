from __future__ import annotations

__all__ = [
    "MSBImportSettings",
]

import fnmatch
import re
import typing as tp

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

    def get_name_match_filter(self) -> tp.Callable[[str], bool]:
        match self.part_name_match_mode:
            case "GLOB":
                def is_name_match(name: str):
                    return self.part_name_match in {"", "*"} or fnmatch.fnmatch(name, self.part_name_match)
            case "REGEX":
                pattern = re.compile(self.part_name_match)

                def is_name_match(name: str):
                    return self.part_name_match == "" or re.match(pattern, name)
            case _:  # should never happen
                raise ValueError(f"Invalid MSB part name match mode: {self.part_name_match_mode}")

        return is_name_match

    def get_collection_name(self, map_stem: str, model_type: str):
        if self.include_pattern_in_parent_name:
            return f"{map_stem} MSB {model_type} ({self.part_name_match})"
        else:
            return f"{map_stem} MSB {model_type}"
