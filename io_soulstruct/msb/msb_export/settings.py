from __future__ import annotations

__all__ = ["MSBExportSettings"]

import bpy


class MSBExportSettings(bpy.types.PropertyGroup):

    export_msb_data_only: bpy.props.BoolProperty(
        name="Export MSB Data Only",
        description="Only export MSB entry data like transform and Draw Parent name (not models or textures)",
        default=False,
    )
