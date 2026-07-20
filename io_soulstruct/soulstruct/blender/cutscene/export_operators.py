"""VERY early/experimental export of DSR cutscene animations from Blender back into a RemoBND.

STATUS / BOUNDARIES
-------------------
The havok write path is now grounded in real `soulstruct-havok` API (see `remo_export.py`), but
three boundaries still depend on project code I haven't been able to read or that is inherently
lossy. They are marked `# PROJECT:`:

  1. Blender pose -> game armature-space `TRSTransform` per bone. Import goes game->Blender inside
     `SoulstructAnimation.get_bone_basis_samples`; export must use that class's inverse. The
     frame-stepping read below is a correct-but-slow fallback that still needs the final
     Blender-matrix -> game-`TRSTransform` conversion wired to YOUR converter.
  2. Root motion fidelity. Import collapses the format's full-`TRSTransform` root motion to
     translation + a single Z-rotation, so a round-trip cannot perfectly reconstruct the original
     rotation. We rebuild a `TRSTransform` from what Blender retained.
  3. Camera / SIBCAM export is left as a stub: the SIBCAM write API lives in base `soulstruct`
     (not verified here) and import discards most sibcam structure. Patching cuts' cameras
     faithfully needs the original sibcam preserved + its setters confirmed.

Round-trip strategy (unchanged): re-parse the ORIGINAL `.remobnd` as a structural template and
patch animation into it. WINDOWS-ONLY due to spline recompression (`CompressAnim.exe`).
"""
from __future__ import annotations

__all__ = [
    "ExportHKXCutscene",
]

import re
import traceback
from pathlib import Path

import bpy
from mathutils import Quaternion as BlenderQuaternion

from soulstruct.havok.utilities.maths import TRSTransform, Quaternion, Vector3
from soulstruct.havok.fromsoft.darksouls1r.remobnd import *

from ..animation.utilities import get_or_create_action_strip
from ..base.operators import LoggingExportOperator
from ..base.register import io_soulstruct_operator
from ..exceptions import CutsceneExportError
from ..msb.types.adapters import get_part_game_name
from ..types import *
from .types import *
from .remo_export import write_part_frames_into_cut, finalize_cut_animation

REMOBND_RE = re.compile(r"^.*?\.remobnd(\.dcx)?$")


@io_soulstruct_operator
class ExportHKXCutscene(LoggingExportOperator):
    bl_idname = "export_scene.hkx_cutscene"
    bl_label = "Export HKX Cutscene"
    bl_description = "Patch a Blender cutscene's animation back into a source RemoBND (Windows only)"

    filename_ext = ".remobnd"

    filter_glob: bpy.props.StringProperty(
        default="*.remobnd;*.remobnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    source_remobnd_path: bpy.props.StringProperty(
        name="Source RemoBND",
        description="Original RemoBND to use as a structural template. Leave blank to reuse output path",
        default="",
        subtype="FILE_PATH",
    )

    export_camera: bpy.props.BoolProperty(
        name="Export Camera (stub)",
        description="Camera/SIBCAM export is not implemented; see module docstring",
        default=False,
    )

    DEFAULT_SUBDIR = "remo"

    @classmethod
    def poll(cls, context) -> bool:
        if not cls.settings(context).is_game("DARK_SOULS_DSR"):
            return False
        obj = context.active_object
        return bool(obj and obj.type == "CAMERA" and obj.animation_data and obj.animation_data.action)

    def execute(self, context):
        out_path = Path(self.filepath)
        if not REMOBND_RE.match(out_path.name):
            return self.error("Cutscene export path must be a `.remobnd` (optionally `.dcx`) file.")

        source_path = Path(self.source_remobnd_path) if self.source_remobnd_path else out_path
        if not source_path.is_file():
            return self.error(
                f"Source RemoBND template not found: '{source_path}'. Export needs the original file."
            )

        camera = context.active_object
        action = camera.animation_data.action
        export_settings = context.scene.cutscene_import_settings
        bl_frames_per_game_frame = 2.0 if export_settings.to_60_fps else 1.0
        action_strip = get_or_create_action_strip(action)

        # TODO:
        #  - Option to edit existing RemoBND (e.g. with TAE already ready). Otherwise new Binder.
        #  - Extract animation frames from every object in the Action. See Animation export.
        #    - CoB removed for EDIT-type Armatures.
        #  - Animation bone data prefixed by object (model) name + "_".
        #  - Object transform data encoded into object model name root bone.
        #  - Uses selected Blender map. Warns if scnAAABXX name doesn't match stem.
        #  - Other-map objects have "AXXBX_" additional prefix.
        #  - Convert interleaved HKX to spline HKX.
        #  - Camera: to enable proper FoV keyframing, Blender keyframes on import should be kept minimal.
        #    - Use 'tan_in' and 'tan_out' to adjust interpolation curves, I guess.
        #    - If too hard in Blender: extract full data and use Scipy to fit 'tan' keyframes to data.

        try:
            remobnd = RemoBND.from_path(source_path)
        except Exception as ex:
            return self.error(f"Could not parse source RemoBND '{source_path}': {ex}")

        if self.export_camera:
            self.warning("Camera export is a stub and was skipped. See ExportHKXCutscene docstring.")

        # We need parsed parts to know which cuts each part appears in and to map names.
        remobnd.load_remo_parts()

        # --- Write each part's frames into its cuts (in place on cut.animation) ----------------
        touched_cuts = {}  # type: dict[str, object]  # cut_name -> RemoCut, for finalization
        for remo_part_type, remo_parts_dict in remobnd.all_remo_parts.items():
            is_dummy = remo_part_type == RemoPartType.Dummy
            for remo_part in remo_parts_dict.values():
                try:
                    self._export_part(
                        context, remobnd, remo_part, is_dummy,
                        action_strip, bl_frames_per_game_frame, touched_cuts,
                    )
                except Exception as ex:
                    traceback.print_exc()  # for inspection in Blender console
                    self.error(f"Failed to export cutscene part '{remo_part.name}': {ex}")
                    continue

        if not touched_cuts:
            return self.error("No cutscene part animation was written; nothing to export.")

        # --- Compress + repack each touched cut, then write the binder -------------------------
        try:
            for cut in touched_cuts.values():
                finalize_cut_animation(remobnd, cut)  # WINDOWS-ONLY (spline recompression)
        except Exception as ex:
            traceback.print_exc()
            return self.error(
                f"Failed during spline recompression / repacking. This step is Windows-only "
                f"(CompressAnim.exe). Error: {ex}"
            )

        try:
            remobnd.write(out_path)  # inherited from Binder
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Could not write RemoBND to '{out_path}': {ex}")

        self.info(f"Exported HKX cutscene to: {out_path.name}")
        return {"FINISHED"}

    # region Per-part export

    def _export_part(
        self,
        context: bpy.types.Context,
        remobnd: RemoBND,
        remo_part: RemoPart,
        is_dummy: bool,
        action_strip: bpy.types.ActionKeyframeStrip,
        bl_frames_per_game_frame: float,
        touched_cuts: dict,
    ) -> None:
        bl_obj = self._find_blender_object_for_part(remobnd, remo_part, is_dummy)
        if bl_obj is None:
            self.warning(f"No Blender object for cutscene part '{remo_part.name}'. Skipping.")
            return

        armature = None
        if not is_dummy:
            if bl_obj.type == "ARMATURE":
                armature = bl_obj
            elif bl_obj.type == "MESH":
                armature = bl_obj.find_armature()

        animated_obj = bl_obj if (is_dummy or armature is None) else armature
        object_channelbag = self._get_channelbag(action_strip, animated_obj)

        # Only patch cuts the part was originally present in (mirrors import's sparse storage).
        present_cut_names = set(remo_part.cut_arma_frames.keys())

        game_frame_offset = 0
        for cut in remobnd.cuts:
            frame_count = cut.sibcam.clip_frame_count
            if cut.name not in present_cut_names:
                game_frame_offset += frame_count
                continue

            frames = []  # type: list[RemoPartAnimationFrame]
            for i in range(frame_count):
                bl_frame = (game_frame_offset + i) * bl_frames_per_game_frame
                root_motion = self._read_root_motion(object_channelbag, bl_frame)
                if is_dummy or armature is None:
                    bone_transforms = {}
                else:
                    bone_transforms = self._read_bone_transforms(context, remo_part, armature, bl_frame)
                frames.append(RemoPartAnimationFrame(root_motion, bone_transforms))

            write_part_frames_into_cut(cut, remo_part, frames)
            touched_cuts[cut.name] = cut
            game_frame_offset += frame_count

    def _find_blender_object_for_part(
        self, remobnd: RemoBND, remo_part: RemoPart, is_dummy: bool
    ) -> bpy.types.Object | None:
        if is_dummy:
            # Importer named dummies "{cutscene_name} {remo_part.name}".
            target = f"{remobnd.cutscene_name} {remo_part.name}"
            return bpy.data.objects.get(target) or next(
                (o for o in bpy.data.objects if o.type == "EMPTY" and o.name.endswith(remo_part.name)),
                None,
            )
        # Non-dummy: match MSB Part mesh by game name (same rule import used).
        # TODO: scope to the cutscene collection to avoid cross-map model-name collisions.
        return next(
            (o for o in bpy.data.objects
             if o.type == "MESH" and get_part_game_name(o.name) == remo_part.map_part_name),
            None,
        )

    # endregion

    # region Transform reading

    def _read_root_motion(
        self, channelbag: bpy.types.ActionChannelbag | None, bl_frame: float
    ) -> TRSTransform:
        """Rebuild a game-space root-motion `TRSTransform` from the object's transform fcurves.

        Inverts the importer:
            rm_translate = to_blender(frame.root_motion.translation)
            rm_rotate_z  = -frame.root_motion.rotation.to_euler_angles_rad("xzy").y
        PROJECT: confirm the BL->game vector/rotation convention against your `to_blender`.
        Because import kept only translation + one rotation axis, this cannot recover the
        original full rotation; scale is assumed identity.
        """
        if channelbag is None:
            return TRSTransform.identity()
        x = self._sample(channelbag, "location", 0, bl_frame)
        y = self._sample(channelbag, "location", 1, bl_frame)
        z = self._sample(channelbag, "location", 2, bl_frame)
        z_rot = self._sample(channelbag, "rotation_euler", 2, bl_frame)

        # PROJECT: replace with your BL->game conversion (axis swap / handedness).
        game_translation = Vector3((x, y, z))
        game_rotation = Quaternion.from_axis_angle((0.0, 1.0, 0.0), -z_rot)  # PROJECT: verify axis
        return TRSTransform(translation=game_translation, rotation=game_rotation)

    def _read_bone_transforms(
        self, context: bpy.types.Context, remo_part: RemoPart, armature: ArmatureObject, bl_frame: float
    ) -> dict[str, TRSTransform]:
        """Step the scene to `bl_frame` and read each pose bone's armature-space transform.

        Correct but O(frames * bones) with a scene update per frame. PREFER the inverse of
        `SoulstructAnimation.get_bone_basis_samples` (batched) if your animation module exposes it.
        """
        context.scene.frame_set(int(round(bl_frame)))
        context.view_layer.update()

        bone_transforms = {}
        for pose_bone in armature.pose.bones:
            m = pose_bone.matrix  # armature/object space (Blender)
            loc, quat, _ = m.decompose()  # scale assumed identity for cutscene bones
            # PROJECT: convert this Blender (loc, quat) to a game-space TRSTransform using the
            # exact inverse of how import produced `bone_transforms`. Placeholder pass-through:
            bone_transforms[pose_bone.name] = self._bl_to_game_trs(loc, quat)
        return bone_transforms

    @staticmethod
    def _bl_to_game_trs(loc, quat: BlenderQuaternion) -> TRSTransform:
        """PROJECT: implement BL->game basis conversion (inverse of import's bone path)."""
        return TRSTransform(
            translation=Vector3((loc.x, loc.y, loc.z)),
            rotation=Quaternion((quat.x, quat.y, quat.z, quat.w)),
        )

    # endregion

    # region Channelbag / fcurve sampling (verified Blender-side)

    @staticmethod
    def _get_channelbag(
        action_strip: bpy.types.ActionKeyframeStrip, animated_id: bpy.types.ID
    ) -> bpy.types.ActionChannelbag | None:
        anim_data = animated_id.animation_data
        if not anim_data or not anim_data.action_slot:
            return None
        try:
            return action_strip.channelbag(anim_data.action_slot)
        except Exception:
            return None

    @staticmethod
    def _sample(
        channelbag: bpy.types.ActionChannelbag, data_path: str, index: int, frame: float
    ) -> float:
        for fcurve in channelbag.fcurves:
            if fcurve.data_path == data_path and fcurve.array_index == index:
                # LINEAR/CONSTANT interpolation => evaluate() at integer frames is exact.
                return float(fcurve.evaluate(frame))
        return 0.0

    # endregion