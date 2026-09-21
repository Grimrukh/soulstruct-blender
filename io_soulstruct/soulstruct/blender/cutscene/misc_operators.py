"""Operators for authoring a cutscene from scratch in Blender (DSR).

A cutscene is a single shared Action (with `Action.cutscene` metadata: name, cut list, frames per game frame), a
Camera bound to it, and a `Cutscene {name}` collection holding the MSB Parts (and Dummy Empties) that appear in it.
`CreateHKXCutscene` sets that up; the cut list is edited in the Cutscene panel; `BindObjectsToCutscene` puts selected
objects on the Action so keyframes land in the right place; `ExportNewHKXCutscene` (in `export_operators.py`) then
builds the RemoBND.
"""
from __future__ import annotations

__all__ = [
    "CreateHKXCutscene",
    "AddCutsceneCut",
    "RemoveCutsceneCut",
    "BindObjectsToCutscene",
]

import re

import bpy

from soulstruct.games import GameType

from ..base.operators import LoggingOperator
from ..base.register import io_soulstruct_operator
from ..utilities import find_or_create_collection
from .types import SoulstructCutsceneAnimation

CUTSCENE_NAME_RE = re.compile(r"^scn(\d\d)(\d\d)\d\d$")
CUT_NAME_RE = re.compile(r"^cut\d{4}$")


def get_cutscene_collection_name(cutscene_name: str) -> str:
    return f"Cutscene {cutscene_name}"


def find_cutscene_collection(cutscene_name: str) -> bpy.types.Collection | None:
    return bpy.data.collections.get(get_cutscene_collection_name(cutscene_name))


@io_soulstruct_operator
class CreateHKXCutscene(LoggingOperator):
    bl_idname = "cutscene.create_hkx_cutscene"
    bl_label = "Create New Cutscene"
    bl_description = (
        "Create a new empty cutscene: a cutscene Action with one cut, a Camera bound to it, and a 'Cutscene {name}' "
        "collection to link the cutscene's MSB Parts and Dummies into"
    )
    bl_options = {"REGISTER", "UNDO"}

    cutscene_name: bpy.props.StringProperty(
        name="Cutscene Name",
        description="Cutscene (RemoBND) name, 'scn' + area + block + two-digit index, e.g. 'scn100100'. The area and "
                    "block give the cutscene's map, whose MSB must be loaded when it plays",
        default="scn100100",
    )

    first_cut_frames: bpy.props.IntProperty(
        name="First Cut Frames",
        description="Length of the first cut in game (30 FPS) frames",
        default=90,
        min=2,
    )

    to_60_fps: bpy.props.BoolProperty(
        name="60 FPS Timeline",
        description="Use two Blender frames per game frame (as cutscene import does with 'To 60 FPS')",
        default=True,
    )

    @classmethod
    def poll(cls, context) -> bool:
        return cls.settings(context).is_game(GameType.DarkSoulsDSR)

    def invoke(self, context, _event):
        map_stem = self.settings(context).map_stem
        if map_stem and len(map_stem) >= 6:
            self.cutscene_name = f"scn{map_stem[1:3]}{map_stem[4:6]}00"
        return context.window_manager.invoke_props_dialog(self)

    def _execute(self, context):
        settings = self.settings(context)
        name = self.cutscene_name.strip()
        match = CUTSCENE_NAME_RE.match(name)
        if not match:
            return self.error(f"Cutscene name must look like 'scn100100', not '{name}'.")
        existing = bpy.data.actions.get(name)
        if existing is not None and existing.cutscene.is_cutscene:
            return self.error(f"A cutscene Action named '{name}' already exists.")

        cutscene = SoulstructCutsceneAnimation.new(name)
        props = cutscene.props
        props.cutscene_name = name
        props.source_remobnd_path = ""
        props.bl_frames_per_game_frame = 2.0 if self.to_60_fps else 1.0
        props.set_cuts([("cut0010", self.first_cut_frames)])

        camera_name = f"{name} Camera"
        camera_data = bpy.data.cameras.new(camera_name)
        camera_data.sensor_width = 35  # matches cutscene import
        camera_data.lens_unit = "MILLIMETERS"
        camera = bpy.data.objects.new(camera_name, camera_data)
        camera.rotation_mode = "XYZ"
        cutscene.bind(camera)
        cutscene.bind(camera_data)

        map_stem = settings.get_latest_map_stem_version(f"m{match.group(1)}_{match.group(2)}_00_00")
        collection = find_or_create_collection(
            context.scene.collection, f"{map_stem} Cutscenes", get_cutscene_collection_name(name)
        )
        collection.objects.link(camera)

        context.scene.frame_start = 0
        context.scene.frame_end = int((props.get_total_frame_count() - 1) * props.bl_frames_per_game_frame)
        context.scene.frame_set(0)
        context.view_layer.objects.active = camera
        camera.select_set(True)
        self.info(
            f"Created cutscene '{name}' with Camera '{camera.name}' in collection '{collection.name}'. Link the MSB "
            f"Parts (and Dummy Empties) that appear in the cutscene into that collection, bind them with 'Bind "
            f"Selected to Cutscene', keyframe, and export with 'Export New HKX Cutscene'."
        )
        return {"FINISHED"}


class _CutsceneCutOperator(LoggingOperator):
    """Base for operators acting on the cutscene Action of the active object."""

    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context) -> bool:
        obj = context.active_object
        return bool(obj and SoulstructCutsceneAnimation.from_animated_id(obj))

    @staticmethod
    def _update_scene_frame_range(context, cutscene: SoulstructCutsceneAnimation):
        props = cutscene.props
        context.scene.frame_start = 0
        context.scene.frame_end = max(0, int((props.get_total_frame_count() - 1) * props.bl_frames_per_game_frame))


@io_soulstruct_operator
class AddCutsceneCut(_CutsceneCutOperator):
    bl_idname = "cutscene.add_cut"
    bl_label = "Add Cut"
    bl_description = "Append a new camera cut to the active object's cutscene (name and length can be edited in the list)"

    frame_count: bpy.props.IntProperty(
        name="Frame Count",
        description="Length of the new cut in game (30 FPS) frames",
        default=90,
        min=2,
    )

    def _execute(self, context):
        cutscene = SoulstructCutsceneAnimation.from_animated_id(context.active_object)
        props = cutscene.props
        cut = props.cuts.add()
        cut.name = props.get_next_cut_name()
        cut.frame_count = self.frame_count
        props.active_cut_index = len(props.cuts) - 1
        self._update_scene_frame_range(context, cutscene)
        return {"FINISHED"}


@io_soulstruct_operator
class RemoveCutsceneCut(_CutsceneCutOperator):
    bl_idname = "cutscene.remove_cut"
    bl_label = "Remove Cut"
    bl_description = "Remove the selected camera cut from the active object's cutscene (keyframes are not changed)"

    def _execute(self, context):
        cutscene = SoulstructCutsceneAnimation.from_animated_id(context.active_object)
        props = cutscene.props
        if not props.cuts:
            return self.error("Cutscene has no cuts to remove.")
        if len(props.cuts) == 1:
            return self.error("A cutscene must keep at least one cut.")
        index = min(props.active_cut_index, len(props.cuts) - 1)
        props.cuts.remove(index)
        props.active_cut_index = max(0, min(index, len(props.cuts) - 1))
        self._update_scene_frame_range(context, cutscene)
        return {"FINISHED"}


@io_soulstruct_operator
class BindObjectsToCutscene(LoggingOperator):
    bl_idname = "cutscene.bind_objects"
    bl_label = "Bind Selected to Cutscene"
    bl_description = (
        "Assign the active object's cutscene Action to every other selected object (MSB Part Armatures/Meshes, "
        "Dummy Empties, Cameras), creating an Action slot for each, so their keyframes are stored in the cutscene"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context) -> bool:
        obj = context.active_object
        return bool(obj and SoulstructCutsceneAnimation.from_animated_id(obj) and len(context.selected_objects) > 1)

    def _execute(self, context):
        cutscene = SoulstructCutsceneAnimation.from_animated_id(context.active_object)
        bound = []
        for obj in context.selected_objects:
            if obj == context.active_object or cutscene.is_bound(obj):
                continue
            if obj.type == "CAMERA":
                obj.rotation_mode = "XYZ"
                cutscene.bind(obj)
                cutscene.bind(obj.data)
            elif obj.type in {"ARMATURE", "EMPTY", "MESH"}:
                obj.rotation_mode = "QUATERNION"
                cutscene.bind(obj)
            else:
                self.warning(f"Cannot bind {obj.type} object '{obj.name}' to a cutscene. Skipping.")
                continue
            bound.append(obj.name)
        self.info(f"Bound {len(bound)} object(s) to cutscene '{cutscene.name}': {bound}")
        return {"FINISHED"}
