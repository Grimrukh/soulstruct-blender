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

    entry_name_match: bpy.props.StringProperty(
        name="MSB Entry Name Match",
        description="Glob/Regex for filtering MSB entry names when importing all entries of a certain type",
        default="*",
    )

    entry_name_match_mode: bpy.props.EnumProperty(
        name="MSB Entry Name Match Mode",
        description="Whether to use glob or regex for MSB entry name matching",
        items=[
            ("GLOB", "Glob", "Use glob (*, ?, etc.) for MSB entry name matching"),
            ("REGEX", "Regex", "Use Python regular expressions for MSB entry name matching"),
        ],
        default="GLOB",
    )

    include_pattern_in_parent_name: bpy.props.BoolProperty(
        name="Include Pattern in Parent Name",
        description="Include the glob/regex pattern in the name of the parent object for imported MSB entries",
        default=True,
    )

    def get_name_match_filter(self) -> tp.Callable[[str], bool]:
        match self.entry_name_match_mode:
            case "GLOB":
                def is_name_match(name: str):
                    return self.entry_name_match in {"", "*"} or fnmatch.fnmatch(name, self.entry_name_match)
            case "REGEX":
                pattern = re.compile(self.entry_name_match)

                def is_name_match(name: str):
                    return self.entry_name_match == "" or re.match(pattern, name)
            case _:  # should never happen
                raise ValueError(f"Invalid MSB entry name match mode: {self.entry_name_match_mode}")

        return is_name_match

    def get_collection_name(self, map_stem: str, model_type: str):
        if self.include_pattern_in_parent_name:
            return f"{map_stem} MSB {model_type} ({self.entry_name_match})"
        else:
            return f"{map_stem} MSB {model_type}"
