"""Export a Blender cutscene (DSR) to a RemoBND.

Two operators:

    - `ExportHKXCutscene` patches a *source* RemoBND (by default, the one the cutscene was imported from): the TAE,
      the per-cut cutscene skeletons and the tracks of parts that are not animated in Blender are all kept from it,
      while the tracks of every MSB Part Armature, Dummy Empty and the Camera bound to the cutscene Action are
      rewritten from Blender (see `remo_export.py`). Cut lengths must match the source RemoBND's.
    - `ExportNewHKXCutscene` builds a complete RemoBND from scratch out of the MSB Parts and Dummies in the cutscene's
      collection and the cuts defined on the Action (see `remo_build.py`): cutscene skeletons are assembled from the
      models' ANIBND skeletons, so cuts and parts are free. A source RemoBND is optional (only its TAE events are
      reused).

Spline compression of the cut animations shells out to `CompressAnim.exe` and is Windows-only.
"""
from __future__ import annotations

__all__ = [
    "ExportHKXCutscene",
    "ExportNewHKXCutscene",
]

import re
import traceback
from pathlib import Path

import bpy

from soulstruct.games import GameType
from soulstruct.havok.fromsoft.darksouls1r.remobnd import *
from soulstruct.havok.utilities.maths import TRSTransform

from ..animation.utilities import get_armature_bone_data_type
from ..base.operators import LoggingExportOperator
from ..base.register import io_soulstruct_operator
from ..exceptions import CutsceneExportError
from ..types import *
from .misc_operators import find_cutscene_collection, get_cutscene_collection_name
from .remo_build import build_remobnd_from_scratch
from .remo_export import *
from .types import SoulstructCutsceneAnimation
from .utilities import BL_PART_CLASSES, find_remo_part_msb_part

REMOBND_RE = re.compile(r"^.*?\.remobnd(\.dcx)?$")


@io_soulstruct_operator
class ExportHKXCutscene(LoggingExportOperator):
    bl_idname = "export_scene.hkx_cutscene"
    bl_label = "Export HKX Cutscene"
    bl_description = (
        "Write the active object's cutscene Action (camera, MSB Part Armatures and Dummies) into a copy of the "
        "cutscene's source RemoBND. Spline compression is Windows-only"
    )

    filename_ext = ".remobnd.dcx"

    filter_glob: bpy.props.StringProperty(
        default="*.remobnd;*.remobnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    source_remobnd_path: bpy.props.StringProperty(
        name="Source RemoBND",
        description="RemoBND to patch with Blender animation data. Leave blank to use the RemoBND the cutscene was "
                    "imported from (or the game's copy of it if that path no longer exists)",
        default="",
        subtype="FILE_PATH",
    )

    DEFAULT_SUBDIR = "remo"

    @classmethod
    def poll(cls, context) -> bool:
        if not cls.settings(context).is_game(GameType.DarkSoulsDSR):
            return False
        obj = context.active_object
        return bool(obj and SoulstructCutsceneAnimation.from_animated_id(obj))

    def invoke(self, context, _event):
        cutscene = SoulstructCutsceneAnimation.from_animated_id(context.active_object)
        self.filepath = f"{cutscene.props.cutscene_name}.remobnd.dcx"
        return super().invoke(context, _event)

    def _execute(self, context):
        settings = self.settings(context)
        export_settings = context.scene.cutscene_export_settings

        cutscene = SoulstructCutsceneAnimation.from_animated_id(context.active_object)
        if cutscene is None:
            return self.error("Active object is not animated by an imported cutscene Action.")
        props = cutscene.props

        out_path = Path(self.filepath)
        if not REMOBND_RE.match(out_path.name):
            return self.error("Cutscene export path must be a `.remobnd` (optionally `.dcx`) file.")

        try:
            source_path = self._resolve_source_path(context)
        except FileNotFoundError as ex:
            return self.error(str(ex))

        try:
            remobnd = RemoBND.from_path(source_path)
            remobnd.load_remo_parts()
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Could not parse source RemoBND '{source_path}': {ex}")

        if remobnd.cutscene_name != props.cutscene_name:
            self.warning(
                f"Source RemoBND cutscene name '{remobnd.cutscene_name}' does not match Blender cutscene "
                f"'{props.cutscene_name}'. Cuts will be matched by name."
            )

        # Validate cuts before touching anything.
        bl_cuts = {cut.name: cut.frame_count for cut in props.cuts}
        for cut in remobnd.cuts:
            if cut.name not in bl_cuts:
                return self.error(
                    f"Source RemoBND cut '{cut.name}' is not present in Blender cutscene '{props.cutscene_name}'. "
                    f"Cuts: {sorted(bl_cuts)}"
                )
            if bl_cuts[cut.name] != cut.sibcam.clip_frame_count:
                return self.error(
                    f"Blender cutscene cut '{cut.name}' has {bl_cuts[cut.name]} frames but source RemoBND cut has "
                    f"{cut.sibcam.clip_frame_count}. Cut lengths cannot be changed when patching a source RemoBND."
                )
        for cut_name in bl_cuts:
            if cut_name not in {cut.name for cut in remobnd.cuts}:
                self.warning(f"Blender cutscene cut '{cut_name}' is not in the source RemoBND and will be ignored.")

        # Local-space frames per cut, seeded from the template. Parts bound in Blender overwrite their own tracks.
        local_frames = {cut.name: get_template_local_frames(cut) for cut in remobnd.cuts}

        exported_part_names = []
        for remo_part_type, remo_parts_dict in remobnd.all_remo_parts.items():
            for remo_part in remo_parts_dict.values():
                try:
                    if self._export_part(context, cutscene, remobnd, remo_part, remo_part_type, local_frames):
                        exported_part_names.append(remo_part.name)
                except Exception as ex:
                    traceback.print_exc()
                    return self.error(f"Failed to export cutscene part '{remo_part.name}': {ex}")

        camera = cutscene.get_camera()
        if export_settings.export_camera and camera is None:
            self.warning("No Camera is bound to the cutscene Action. Source RemoBND camera data will be kept.")

        for cut in remobnd.cuts:
            cut_local_frames = local_frames[cut.name]
            make_track_rotations_continuous(cut_local_frames)
            try:
                build_cut_animation_hkx(cut, cut_local_frames, spline=not export_settings.force_interleaved)
                replace_cut_hkx_entry(remobnd, cut)
            except Exception as ex:
                traceback.print_exc()
                return self.error(
                    f"Failed to build animation HKX for cut '{cut.name}'. Spline compression requires "
                    f"`CompressAnim.exe` (Windows only). Error: {ex}"
                )
            if export_settings.export_camera and camera is not None:
                try:
                    bl_frames = cutscene.get_cut_bl_frames(cut.name)
                    write_cut_sibcam(remobnd, cut, cutscene.sample_camera(camera, bl_frames))
                except Exception as ex:
                    traceback.print_exc()
                    return self.error(f"Failed to write camera SIBCAM for cut '{cut.name}': {ex}")

        try:
            remobnd.write(out_path)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Could not write RemoBND to '{out_path}': {ex}")

        self.info(
            f"Exported cutscene '{props.cutscene_name}' to '{out_path.name}' ({len(remobnd.cuts)} cuts; "
            f"{len(exported_part_names)} Blender-animated parts: {exported_part_names})."
        )
        return {"FINISHED"}

    def _resolve_source_path(self, context) -> Path:
        """Explicit operator path, then the Action's recorded import path, then the project/game `remo` directory."""
        props = SoulstructCutsceneAnimation.from_animated_id(context.active_object).props
        for candidate in (self.source_remobnd_path, props.source_remobnd_path):
            if candidate:
                path = Path(candidate)
                if path.is_file():
                    return path
                self.warning(f"Source RemoBND path '{path}' does not exist. Trying next candidate.")
        try:
            return self.settings(context).get_import_file_path("remo", f"{props.cutscene_name}.remobnd")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Could not find source RemoBND for cutscene '{props.cutscene_name}'. Set 'Source RemoBND' explicitly."
            )

    # region Parts

    def _export_part(
        self,
        context: bpy.types.Context,
        cutscene: SoulstructCutsceneAnimation,
        remobnd: RemoBND,
        remo_part: RemoPart,
        remo_part_type: RemoPartType,
        local_frames: dict[str, list[list[TRSTransform]]],
    ) -> bool:
        """Overwrite `remo_part`'s tracks in every cut it appears in from its Blender object, if that object is bound
        to the cutscene Action. Returns `False` (with a debug log) if the part is not animated in Blender."""
        animated_obj, armature = self._find_part_objects(context, cutscene, remobnd, remo_part, remo_part_type)
        if animated_obj is None:
            self.debug(f"Cutscene part '{remo_part.name}' is not animated in Blender. Keeping source RemoBND tracks.")
            return False

        bone_data_type = get_armature_bone_data_type(armature) if armature else None
        root_bone_names = set(remo_part.part_cutscene_root_bone_names)

        for cut in remobnd.cuts:
            if cut.name not in remo_part.cut_arma_frames:
                continue  # part absent from this cut
            bl_frames = cutscene.get_cut_bl_frames(cut.name)
            root_motion = cutscene.sample_root_motion(animated_obj, bl_frames)
            bone_frames = None
            if armature is not None:
                bone_names = get_part_track_bone_names(cut, remo_part)
                missing = [name for name in bone_names if name not in armature.data.bones]
                if missing:
                    raise CutsceneExportError(
                        f"Cutscene bone name(s) {sorted(missing)} of part '{remo_part.name}' (cut '{cut.name}') are "
                        f"missing from Armature '{armature.name}'."
                    )
                if bone_names:
                    bone_frames = cutscene.sample_armature_bones(
                        armature, bone_names, bl_frames, bone_data_type, root_bone_names=root_bone_names
                    )
            write_part_frames(cut, remo_part, root_motion, bone_frames, local_frames[cut.name])

        self.info(f"Exported cutscene part '{remo_part.name}' from '{animated_obj.name}'.")
        return True

    def _find_part_objects(
        self,
        context: bpy.types.Context,
        cutscene: SoulstructCutsceneAnimation,
        remobnd: RemoBND,
        remo_part: RemoPart,
        remo_part_type: RemoPartType,
    ) -> tuple[bpy.types.Object | None, ArmatureObject | None]:
        """Find `(animated_object, armature)` for a cutscene part, mirroring how import bound it: Dummies are Empties
        named `{cutscene_name} {remo_part.name}`, and every other part is an MSB Part Mesh (looked up in its map's MSB
        collection) whose Armature parent carries the animation. Returns `(None, None)` if nothing bound is found."""
        if remo_part_type == RemoPartType.Dummy:
            dummy = bpy.data.objects.get(f"{remobnd.cutscene_name} {remo_part.name}")
            if dummy is None or dummy.type != "EMPTY" or not cutscene.is_bound(dummy):
                return None, None
            return dummy, None

        bl_part_class = BL_PART_CLASSES.get(remo_part_type)
        if bl_part_class is None:
            return None, None
        bl_part = find_remo_part_msb_part(self, context, remo_part, bl_part_class, report_missing=False)
        if bl_part is None or bl_part.armature is None:
            return None, None
        armature = bl_part.armature
        if not cutscene.is_bound(armature):
            return None, None
        return armature, armature

    # endregion


@io_soulstruct_operator
class ExportNewHKXCutscene(LoggingExportOperator):
    bl_idname = "export_scene.hkx_cutscene_new"
    bl_label = "Export New HKX Cutscene"
    bl_description = (
        "Build a complete RemoBND from scratch for the active object's cutscene Action: every MSB Part and Dummy "
        "Empty in the 'Cutscene {name}' collection appears in every cut (unless render-hidden at the cut's start), "
        "animated by the Action where bound. Character/Object skeletons come from their ANIBNDs. Spline compression "
        "is Windows-only"
    )

    filename_ext = ".remobnd.dcx"

    filter_glob: bpy.props.StringProperty(
        default="*.remobnd;*.remobnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    source_remobnd_path: bpy.props.StringProperty(
        name="TAE Source RemoBND",
        description="Optional RemoBND whose TAE events (fades, sounds, draw parameter changes) are copied for cuts "
                    "with the same cut numbers. Leave blank for a minimal, event-less TAE. Defaults to the RemoBND "
                    "the cutscene was imported from, if any",
        default="",
        subtype="FILE_PATH",
    )

    collection_name: bpy.props.StringProperty(
        name="Cutscene Collection",
        description="Collection holding the cutscene's MSB Parts and Dummies. Leave blank for 'Cutscene {name}'",
        default="",
    )

    DEFAULT_SUBDIR = "remo"

    @classmethod
    def poll(cls, context) -> bool:
        if not cls.settings(context).is_game(GameType.DarkSoulsDSR):
            return False
        obj = context.active_object
        return bool(obj and SoulstructCutsceneAnimation.from_animated_id(obj))

    def invoke(self, context, _event):
        cutscene = SoulstructCutsceneAnimation.from_animated_id(context.active_object)
        self.filepath = f"{cutscene.props.cutscene_name}.remobnd.dcx"
        if not self.source_remobnd_path:
            self.source_remobnd_path = cutscene.props.source_remobnd_path
        return super().invoke(context, _event)

    def _execute(self, context):
        export_settings = context.scene.cutscene_export_settings
        cutscene = SoulstructCutsceneAnimation.from_animated_id(context.active_object)
        if cutscene is None:
            return self.error("Active object is not animated by a cutscene Action.")
        props = cutscene.props

        out_path = Path(self.filepath)
        if not REMOBND_RE.match(out_path.name):
            return self.error("Cutscene export path must be a `.remobnd` (optionally `.dcx`) file.")

        collection_name = self.collection_name or get_cutscene_collection_name(props.cutscene_name)
        collection = bpy.data.collections.get(collection_name) or find_cutscene_collection(props.cutscene_name)
        if collection is None:
            return self.error(
                f"Cutscene collection '{collection_name}' not found. Link the cutscene's MSB Parts and Dummies into a "
                f"collection with that name (created by cutscene import or 'Create New Cutscene')."
            )

        camera = cutscene.get_camera()
        if camera is None:
            return self.error(
                f"No Camera is bound to cutscene Action '{cutscene.name}'. Every cut needs camera animation."
            )

        source_remobnd = None
        source_path = self.source_remobnd_path or props.source_remobnd_path
        if source_path:
            source_path = Path(source_path)
            if not source_path.is_file():
                self.warning(f"TAE source RemoBND '{source_path}' does not exist. A minimal TAE will be generated.")
            else:
                try:
                    source_remobnd = RemoBND.from_path(source_path)
                except Exception as ex:
                    traceback.print_exc()
                    return self.error(f"Could not parse TAE source RemoBND '{source_path}': {ex}")

        try:
            remobnd = build_remobnd_from_scratch(
                self, context, cutscene, collection, camera,
                spline=not export_settings.force_interleaved,
                source_remobnd=source_remobnd,
            )
        except CutsceneExportError as ex:
            traceback.print_exc()
            return self.error(str(ex))
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Failed to build cutscene '{props.cutscene_name}': {ex}")

        try:
            remobnd.write(out_path)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Could not write RemoBND to '{out_path}': {ex}")

        self.info(
            f"Exported new cutscene '{props.cutscene_name}' to '{out_path.name}' ({len(remobnd.cuts)} cuts, "
            f"{len(remobnd.get_tae().animations)} TAE animations)."
        )
        return {"FINISHED"}
