from __future__ import annotations

__all__ = [
    "CutsceneImportSettings",
    "CutsceneExportSettings",
]

import bpy


class CutsceneImportSettings(bpy.types.PropertyGroup):

    to_60_fps: bpy.props.BoolProperty(
        name="To 60 FPS",
        description="Convert animation to 60 FPS (from FromSoft standard 30 FPS)",
        default=True,
    )

    camera_data_only: bpy.props.BoolProperty(
        name="Camera Data Only",
        description="Only load camera animation data",
        default=False,
    )


class CutsceneExportSettings(bpy.types.PropertyGroup):

    from_60_fps: bpy.props.BoolProperty(
        name="From 60 FPS",
        description="Convert animation to FromSoft standard 30 FPS from Blender 60 FPS",
        default=True,
    )

    selected_frames_only: bpy.props.BoolProperty(
        name="Selected Frames Only",
        description="Export only frames between current start and end (inclusive) of Blender timeline. Otherwise, "
                    "first to last keyframe times will be exported",
        default=False,
    )
