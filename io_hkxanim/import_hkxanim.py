"""VERY early/experimental system for importing/exporting DSR animations into Blender."""
from __future__ import annotations

import re
import traceback
import typing as tp
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper

from soulstruct.base.binder_entry import BinderEntry
from soulstruct.containers import BaseBinder, Binder

from soulstruct_havok.wrappers.hkx2015 import AnimationHKX

from .core import *


ANIBND_RE = re.compile(r"^.*?\.anibnd(\.dcx)?$")


class ImportHKXAnim(LoggingOperator, ImportHelper):
    bl_idname = "import_scene.hkxanim"
    bl_label = "Import HKX Animation"
    bl_description = "Import a HKX animation file. Can import from BNDs and supports DCX-compressed files"

    # ImportHelper mixin class uses this
    filename_ext = ".hkx"

    filter_glob: bpy.props.StringProperty(
        default="*.hkx;*.hkx.dcx;*.anibnd;*.anibnd.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    import_all_from_binder: bpy.props.BoolProperty(
        name="Import All From Binder",
        description="If a Binder file is opened, import all HKX anim files rather than being prompted to select one",
        default=False,
    )

    files: bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    directory: bpy.props.StringProperty(
        options={'HIDDEN'},
    )

    @classmethod
    def poll(cls, context):
        """Animation's rigged armature must be selected (to extract bone names)."""
        try:
            return context.selected_objects[0].type == "ARMATURE"
        except IndexError:
            return False

    def execute(self, context):
        print("Executing HKX animation import...")

        import cProfile
        import pstats

        with cProfile.Profile() as pr:
            self._execute(context)
        p = pstats.Stats(pr)
        p = p.strip_dirs()
        p.sort_stats("tottime").print_stats(40)

        return {"FINISHED"}

    def _execute(self, context):

        bl_armature = context.selected_objects[0]
        bl_bone_names = []
        for pose_bone in bl_armature.data.bones:
            bl_bone_names.append(pose_bone.name)

        file_paths = [Path(self.directory, file.name) for file in self.files]
        hkxs_with_paths = []  # type: list[tuple[Path, AnimationHKX | list[BinderEntry]]]

        for file_path in file_paths:

            if ANIBND_RE.match(file_path.name):
                binder = Binder(file_path)

                # Find HKX entry.
                hkx_entries = binder.find_entries_matching_name(r".*\.hkx(\.dcx)?")
                if not hkx_entries:
                    raise HKXAnimImportError(f"Cannot find any HKX animation files in binder {file_path}.")

                if len(hkx_entries) > 1:
                    if self.import_all_from_binder:
                        for entry in hkx_entries:
                            try:
                                hkx = AnimationHKX(entry.data)
                            except Exception as ex:
                                self.warning(f"Error occurred while reading HKX Binder entry '{entry.name}': {ex}")
                            else:
                                hkx.path = Path(entry.name)  # also done in `GameFile`, but explicitly needed below
                                hkxs_with_paths.append((file_path, hkx))
                    else:
                        # Queue up entire Binder; user will be prompted to choose entry below.
                        hkxs_with_paths.append((file_path, hkx_entries))
                else:
                    try:
                        hkx = AnimationHKX(hkx_entries[0].data)
                    except Exception as ex:
                        self.warning(f"Error occurred while reading HKX Binder entry '{hkx_entries[0].name}': {ex}")
                    else:
                        hkxs_with_paths.append((file_path, hkx))
            else:
                # Loose HKX.
                try:
                    hkx = AnimationHKX(file_path)
                except Exception as ex:
                    self.warning(f"Error occurred while reading HKX animation file '{file_path.name}': {ex}")
                else:
                    hkxs_with_paths.append((file_path, hkx))

        importer = HKXAnimImporter(self, context)

        for file_path, hkx_or_entries in hkxs_with_paths:

            if isinstance(hkx_or_entries, list):
                # Defer through entry selection operator.
                ImportHKXAnimWithBinderChoice.run(
                    importer=importer,
                    binder_file_path=Path(file_path),
                    hkx_entries=hkx_or_entries,
                    bl_bone_names=bl_bone_names,
                )
                continue

            hkx = hkx_or_entries
            hkx_name = hkx.path.name.split(".")[0]

            self.info(f"Importing HKX animation: {hkx_name}")

            # Import single HKX without MSB transform.
            try:
                importer.import_hkx_anim(hkx, name=hkx_name, bl_bone_names=bl_bone_names)
            except Exception as ex:
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import HKX animation: {file_path.name}. Error: {ex}")


# noinspection PyUnusedLocal
def get_binder_entry_choices(self, context):
    return ImportHKXAnimWithBinderChoice.enum_options


class ImportHKXAnimWithBinderChoice(LoggingOperator):
    """Presents user with a choice of enums from `enum_choices` class variable (set prior).

    See: https://blender.stackexchange.com/questions/6512/how-to-call-invoke-popup
    """
    bl_idname = "wm.hkxanim_binder_choice_operator"
    bl_label = "Choose HKX Binder Entry"

    # For deferred import in `execute()`.
    importer: tp.Optional[HKXAnimImporter] = None
    binder: tp.Optional[BaseBinder] = None
    binder_file_path: Path = Path()
    enum_options: list[tuple[tp.Any, str, str]] = []
    hkx_entries: tp.Sequence[BinderEntry] = []
    bl_bone_names: list[str] = []

    choices_enum: bpy.props.EnumProperty(items=get_binder_entry_choices)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "choices_enum", expand=False)

    def execute(self, context):
        choice = int(self.choices_enum)
        entry = self.hkx_entries[choice]
        hkx = AnimationHKX(entry.data)
        hkx_name = entry.name.split(".")[0]

        self.importer.operator = self
        self.importer.context = context

        try:
            self.importer.import_hkx_anim(hkx, name=hkx_name, bl_bone_names=self.bl_bone_names)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot import HKX animation {hkx_name} from '{self.binder_file_path.name}'. Error: {ex}")

        return {'FINISHED'}

    @classmethod
    def run(
        cls,
        importer: HKXAnimImporter,
        binder_file_path: Path,
        hkx_entries: list[BinderEntry],
        bl_bone_names: list[str],
    ):
        cls.importer = importer
        cls.binder_file_path = binder_file_path
        cls.enum_options = [(str(i), entry.name, "") for i, entry in enumerate(hkx_entries)]
        cls.hkx_entries = hkx_entries
        cls.bl_bone_names = bl_bone_names
        # noinspection PyUnresolvedReferences
        bpy.ops.wm.hkxanim_binder_choice_operator("INVOKE_DEFAULT")


class HKXAnimImporter:
    """Manages imports for a batch of HKX files imported simultaneously."""

    hkx: tp.Optional[AnimationHKX]
    name: str

    def __init__(
        self,
        operator: ImportHKXAnim,
        context,
    ):
        self.operator = operator
        self.context = context

        self.hkx = None
        self.name = ""

    def import_hkx_anim(self, hkx: AnimationHKX, name: str, bl_bone_names: list[str]):
        """Read a HKX animation into a Blender action."""
        self.hkx = hkx
        self.name = name  # e.g. "a00_3000"

        self.create_blender_action(self.hkx, self.name, bl_bone_names)

    @staticmethod
    def create_blender_action(
        animation_hkx: AnimationHKX,
        animation_name: str,
        bl_bone_names: list[str],  # from selected Armature
    ):
        """Convert a Havok HKX animation file to a Blender action (with fully-sampled keyframes).

        TODO: Test.
        TODO: Time-scaling argument (with linear interpolation)?
        """

        animation_hkx.spline_to_interleaved()
        track_bone_names = [annotation.trackName for annotation in animation_hkx.animation.annotationTracks]
        for bone_name in track_bone_names:
            if bone_name not in bl_bone_names:
                raise ValueError(f"Animation bone name '{bone_name}' is missing from selected Armature.")

        # Create Blender 'action', which is a data-block containing the animation data.
        # TODO: Delete if anything goes wrong.
        action = bpy.data.actions.new(animation_name)
        action.use_fake_user = True  # saves action even if it has no users
        fast = {"FAST"}

        # Create all FCurves.
        bone_curves = {}
        for bone_name in track_bone_names:
            data_path_prefix = f"pose.bones[\"{bone_name}\"]"
            location_data_path = f"{data_path_prefix}.location"
            rotation_data_path = f"{data_path_prefix}.rotation_quaternion"
            scale_data_path = f"{data_path_prefix}.scale"

            # Create 10 FCurves.
            bone_curves[bone_name, "loc_x"] = action.fcurves.new(location_data_path, index=0)
            bone_curves[bone_name, "loc_y"] = action.fcurves.new(location_data_path, index=1)
            bone_curves[bone_name, "loc_z"] = action.fcurves.new(location_data_path, index=2)

            bone_curves[bone_name, "rot_w"] = action.fcurves.new(rotation_data_path, index=0)
            bone_curves[bone_name, "rot_x"] = action.fcurves.new(rotation_data_path, index=1)
            bone_curves[bone_name, "rot_y"] = action.fcurves.new(rotation_data_path, index=2)
            bone_curves[bone_name, "rot_z"] = action.fcurves.new(rotation_data_path, index=3)

            bone_curves[bone_name, "scale_x"] = action.fcurves.new(scale_data_path, index=0)
            bone_curves[bone_name, "scale_y"] = action.fcurves.new(scale_data_path, index=1)
            bone_curves[bone_name, "scale_z"] = action.fcurves.new(scale_data_path, index=2)

        for frame_index, tracks in enumerate(animation_hkx.interleaved_data):
            for bone_name, transform in zip(track_bone_names, tracks):

                # TODO: Confirm default keyframe interpolation is "CONSTANT" or "LINEAR".
                fl_translate = transform.translation
                bl_translate = (-fl_translate.x, -fl_translate.z, fl_translate.y)
                bone_curves[bone_name, "loc_x"].keyframe_points.insert(frame_index, bl_translate[0], options=fast)
                bone_curves[bone_name, "loc_y"].keyframe_points.insert(frame_index, bl_translate[1], options=fast)
                bone_curves[bone_name, "loc_z"].keyframe_points.insert(frame_index, bl_translate[2], options=fast)

                fl_rotate = transform.rotation
                bl_rotate = (fl_rotate.w, fl_rotate.x, fl_rotate.z, -fl_rotate.y)
                bone_curves[bone_name, "rot_w"].keyframe_points.insert(frame_index, bl_rotate[3], options=fast)  # w is last in Soulstruct/Havok
                bone_curves[bone_name, "rot_x"].keyframe_points.insert(frame_index, bl_rotate[0], options=fast)
                bone_curves[bone_name, "rot_y"].keyframe_points.insert(frame_index, bl_rotate[1], options=fast)
                bone_curves[bone_name, "rot_z"].keyframe_points.insert(frame_index, bl_rotate[2], options=fast)

                fl_scale = transform.scale
                bl_scale = (-fl_scale.x, fl_scale.z, fl_scale.y)
                bone_curves[bone_name, "scale_x"].keyframe_points.insert(frame_index, bl_scale[0], options=fast)
                bone_curves[bone_name, "scale_y"].keyframe_points.insert(frame_index, bl_scale[1], options=fast)
                bone_curves[bone_name, "scale_z"].keyframe_points.insert(frame_index, bl_scale[2], options=fast)

        for fcurve in bone_curves.values():
            fcurve.update()

        return action