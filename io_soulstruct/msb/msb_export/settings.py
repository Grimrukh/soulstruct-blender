from __future__ import annotations

__all__ = ["MSBExportSettings"]

import bpy


class MSBExportSettings(bpy.types.PropertyGroup):

    prefer_new_model_name: bpy.props.BoolProperty(
        name="Prefer New Model Name",
        description="Use the 'Model Name' property on the Blender mesh parent to update the model name in "
                    "the MSB and determine the model file/entry name to write (if applicable). If disabled, the MSB "
                    "model name will be used, with an added area suffix for the file/entry name",
        default=True,
    )

    export_msb_data_only: bpy.props.BoolProperty(
        name="Export MSB Data Only",
        description="Only export MSB entry data like transform and Draw Parent name (not models or textures)",
        default=False,
    )
