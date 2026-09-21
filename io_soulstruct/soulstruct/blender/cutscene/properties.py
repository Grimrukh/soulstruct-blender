from __future__ import annotations

__all__ = [
    "CutsceneImportSettings",
    "CutsceneExportSettings",
    "CutsceneCutProps",
    "CutsceneActionProps",
]

import bpy

from ..base.register import io_soulstruct_properties, io_soulstruct_pointer_property


@io_soulstruct_properties
@io_soulstruct_pointer_property(bpy.types.Scene, "cutscene_import_settings")
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


@io_soulstruct_properties
@io_soulstruct_pointer_property(bpy.types.Scene, "cutscene_export_settings")
class CutsceneExportSettings(bpy.types.PropertyGroup):

    export_camera: bpy.props.BoolProperty(
        name="Export Camera",
        description="Write the Blender camera's transform and lens (FoV) animation into each cut's SIBCAM file. If "
                    "disabled, the source RemoBND's camera data is kept as-is",
        default=True,
    )

    force_interleaved: bpy.props.BoolProperty(
        name="Uncompressed (Interleaved)",
        description="Write uncompressed interleaved HKX animations instead of spline-compressed ones. Much larger "
                    "files and NOT known to work in-game; mainly for lossless round-trip testing",
        default=False,
    )


@io_soulstruct_properties
class CutsceneCutProps(bpy.types.PropertyGroup):
    """One camera cut of an imported cutscene, in the order it appears in the cutscene Action's timeline."""

    name: bpy.props.StringProperty(
        name="Cut Name",
        description="RemoBND cut name, e.g. 'cut0020'",
        default="",
    )

    frame_count: bpy.props.IntProperty(
        name="Frame Count",
        description="Number of game (30 FPS) frames in this cut's clipped camera animation",
        default=0,
        min=0,
    )


@io_soulstruct_properties
@io_soulstruct_pointer_property(bpy.types.Action, "cutscene")
class CutsceneActionProps(bpy.types.PropertyGroup):
    """Cutscene metadata stored on the single shared Action created by `ImportHKXCutscene`.

    Cuts are concatenated on one continuous timeline on import, so this is the only record of where each cut starts
    and ends, which export needs to split the Action back into per-cut HKX/SIBCAM files.
    """

    cutscene_name: bpy.props.StringProperty(
        name="Cutscene Name",
        description="Cutscene name, e.g. 'scn100100'. Empty for Actions that are not imported cutscenes",
        default="",
    )

    source_remobnd_path: bpy.props.StringProperty(
        name="Source RemoBND",
        description="Path of the RemoBND this cutscene was imported from (default export template)",
        default="",
        subtype="FILE_PATH",
    )

    bl_frames_per_game_frame: bpy.props.FloatProperty(
        name="Blender Frames per Game Frame",
        description="Blender timeline frames per game (30 FPS) frame used on import (2.0 for 60 FPS, 1.0 for 30 FPS)",
        default=2.0,
        min=1.0,
    )

    cuts: bpy.props.CollectionProperty(
        type=CutsceneCutProps,
        name="Cuts",
        description="Camera cuts in timeline order, with their game frame counts",
    )

    active_cut_index: bpy.props.IntProperty(
        name="Active Cut",
        description="Selected cut in the cutscene cut list",
        default=0,
        min=0,
    )

    @property
    def is_cutscene(self) -> bool:
        return bool(self.cutscene_name) and len(self.cuts) > 0

    def set_cuts(self, cut_names_and_frame_counts: list[tuple[str, int]]):
        self.cuts.clear()
        for cut_name, frame_count in cut_names_and_frame_counts:
            cut = self.cuts.add()
            cut.name = cut_name
            cut.frame_count = frame_count

    def get_total_frame_count(self) -> int:
        return sum(cut.frame_count for cut in self.cuts)

    def get_next_cut_name(self) -> str:
        """Next free cut name, ten past the last cut ('cut0010' for the first)."""
        last_number = 0
        for cut in self.cuts:
            try:
                last_number = max(last_number, int(cut.name[3:]))
            except ValueError:
                continue
        return f"cut{(last_number // 10 + 1) * 10:04d}"

    def get_cut_bl_frame_ranges(self) -> dict[str, tuple[float, float]]:
        """Map cut names to their inclusive `(first_bl_frame, last_bl_frame)` on the Blender timeline."""
        ranges = {}
        bl_frame = 0.0
        for cut in self.cuts:
            last = bl_frame + (cut.frame_count - 1) * self.bl_frames_per_game_frame
            ranges[cut.name] = (bl_frame, last)
            bl_frame += cut.frame_count * self.bl_frames_per_game_frame
        return ranges
