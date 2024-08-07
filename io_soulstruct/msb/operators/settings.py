from __future__ import annotations

__all__ = [
    "MSBImportSettings",
    "MSBExportSettings",
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


class MSBExportSettings(bpy.types.PropertyGroup):

    model_export_mode: bpy.props.EnumProperty(
        name="Model Export Mode",
        description="Determines when to also export model of MSB Parts, if at all. Note that Characters and Objects "
                    "are never exported here; you must select their models and export them",
        items=[
            ("NEVER", "Never", "Never export model of MSB Parts"),
            (
                "ALWAYS_GEOMETRY",
                "Always (Geometry)",
                "Always export geometry MSB Parts (Map Pieces, Collisions, Navmeshes",
            ),
            (
                "IF_NEW_GEOMETRY",
                "If New (Geometry)",
                "Only export model if its name is absent from the MSB",
            ),
        ],
        default="ALWAYS_GEOMETRY",
    )
