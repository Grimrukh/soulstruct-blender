from __future__ import annotations

__all__ = ["MSBExportSettings"]

import bpy


class MSBExportSettings(bpy.types.PropertyGroup):

    export_model_files: bpy.props.BoolProperty(
        name="Export Model Files",
        description="Export model files (FLVER, HKX, or NVM) in addition to MSB entry data",
        default=True,
    )
