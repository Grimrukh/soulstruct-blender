from __future__ import annotations

__all__ = [
    "ExportLooseHKXMapCollision",
    "ExportHKXMapCollisionIntoBinder",
    "ExportHKXMapCollisionIntoHKXBHD",
]

import re
import traceback
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper

from soulstruct.dcx import DCXType
from soulstruct.games import DARK_SOULS_DSR
from soulstruct.utilities.files import create_bak

from soulstruct_havok.wrappers.hkx2015.hkx_binder import BothResHKXBHD

from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import *
from .types import *


LOOSE_HKX_COLLISION_STEM_RE = re.compile(r"^([hl])(\w{6})A(\d\d)$")  # game-readable model name; no extensions
NUMERIC_HKX_COLLISION_STEM_RE = re.compile(r"^([hl])(\d{4})B(\d)A(\d\d)$")  # standard map model name; no extensions


class ExportLooseHKXMapCollision(LoggingOperator, ExportHelper):
    """Export 'hi' and/or 'lo' HKX from a selection of Blender meshes."""
    bl_idname = "export_scene.hkx_map_collision"
    bl_label = "Export Loose Map Collision"
    bl_description = "Export child meshes of selected Blender empty parent to a HKX collision file"

    # ExportHelper mixin class uses this
    filename_ext = ".hkx"

    filter_glob: bpy.props.StringProperty(
        default="*.hkx;*.hkx.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    dcx_type: get_dcx_enum_property(DCXType.Null)  # typically no DCX compression for loose map collisions

    write_other_resolution: bpy.props.BoolProperty(
        name="Write Other Resolution",
        description="Write the other-resolution HKX file to the one named ('h' or 'l')",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        """Must select a single mesh."""
        settings = cls.settings(context)
        if not settings.is_game(DARK_SOULS_DSR):
            return False  # TODO: DS1R only.
        if not context.active_object:
            return False
        if context.active_object.soulstruct_type != SoulstructType.COLLISION:
            return False
        return True

    def invoke(self, context, _event):
        """Set default export name to name of object (before first space and without Blender dupe suffix)."""
        if not context.active_object:
            return super().invoke(context, _event)

        hkx_model = context.active_object
        model_stem = get_bl_obj_tight_name(hkx_model)
        settings = self.settings(context)
        self.filepath = settings.game.process_dcx_path(f"{model_stem}.hkx")
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if not self.poll(context):
            return self.error("Cannot use operator at this time. Try selected a single HKX mesh model.")

        # noinspection PyTypeChecker
        hkx_model = context.active_object  # type: bpy.types.MeshObject
        bl_map_collision = BlenderMapCollision(hkx_model)

        hkx_path = Path(self.filepath)
        if not LOOSE_HKX_COLLISION_STEM_RE.match(hkx_path.name) is None:
            return self.warning(
                f"HKX file name '{hkx_path.name}' does not match the expected name pattern for "
                f"a HKX collision parent object and will not function in-game: 'h......A..' or 'l......A..'"
            )

        # NOTE: We don't care if 'Model Name' doesn't match here. User chooses the exported file name.
        hi_path = hi_name = lo_path = lo_name = None
        if hkx_path.name.startswith("h"):
            hi_path = hkx_path
            hi_name = hi_path.name.split(".")[0]  # needed for internal HKX name
            if self.write_other_resolution:
                lo_path = hkx_path.with_name(f"l{hkx_path.name[1:]}")
                lo_name = lo_path.name.split(".")[0]  # needed for internal HKX name
        elif hkx_path.name.startswith("l"):
            lo_path = hkx_path
            lo_name = lo_path.name.split(".")[0]
            if self.write_other_resolution:
                hi_path = hkx_path.with_name(f"h{hkx_path.name[1:]}")
                hi_name = hi_path.name.split(".")[0]
        else:
            if self.write_other_resolution:
                self.warning(
                    f"Cannot determine other HKX resolution ('h'/'l') from file name '{hkx_path.name}'. Written file "
                    f"will contain 'Hi' submeshes only; not writing another resolution."
                )
            hi_path = hkx_path
            hi_name = hi_path.name.split(".")[0]  # needed for internal HKX name

        try:
            hi_hkx, lo_hkx = bl_map_collision.to_hkx_pair(self, hkx_model, hi_name=hi_name, lo_name=lo_name)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported HKX for '{hkx_model.name}'. Error: {ex}")

        # To ensure that NEITHER file is written if EITHER fails, we make a temporary '.tempbak' file for the hi-res
        # HKX file if it already exists, and restore that file if the lo-res write fails.

        hi_tempbak_path = None
        hi_written = False  # used to delete hi-res file if lo-res fails
        if hi_hkx:
            if hi_path.is_file():
                # Additional temporary backup.
                hi_tempbak_path = hi_path.with_suffix(f"{hi_path.suffix}.tempbak")
                hi_path.rename(hi_tempbak_path)
            hi_hkx.dcx_type = DCXType[self.dcx_type]
            try:
                # Will also create a `.bak` file automatically if absent.
                hi_hkx.write(hi_path)
            except Exception as ex:
                traceback.print_exc()
                self.error(f"Cannot write exported HKX '{hi_name}' to '{hi_path}'. Error: {ex}")
            else:
                hi_written = True
        if lo_hkx:
            lo_hkx.dcx_type = DCXType[self.dcx_type]
            try:
                # Will create a `.bak` file automatically if absent.
                lo_hkx.write(lo_path)
            except Exception as ex:
                traceback.print_exc()
                self.error(f"Cannot write exported HKX '{lo_name}' to '{lo_path}'. Error: {ex}")
                if hi_written:
                    # Restore hi-res file if lo-res write fails.
                    hi_path.unlink(missing_ok=True)
                    if hi_tempbak_path:
                        hi_tempbak_path.rename(hi_path)

        # Ensure that we don't leave '.tempbak' files lying around.
        if hi_tempbak_path and hi_tempbak_path.is_file():
            hi_tempbak_path.unlink(missing_ok=True)

        return {"FINISHED"}


class ExportHKXMapCollisionIntoBinder(LoggingOperator, ImportHelper):
    bl_idname = "export_scene.hkx_map_collision_binder"
    bl_label = "Export Map Collision Into Binder"
    bl_description = "Export a HKX collision file into a FromSoftware Binder (BND/BHD)"

    # ImportHelper mixin class uses this
    filename_ext = ".hkxbhd"

    filter_glob: bpy.props.StringProperty(
        default="*.hkxbhd;*.hkxbhd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    dcx_type: get_dcx_enum_property(DCXType.DS1_DS2)  # map collisions in DS1 binder are compressed

    @classmethod
    def poll(cls, context):
        """Must select a single mesh."""
        # TODO: Why not all selected models at once?
        settings = cls.settings(context)
        if not settings.is_game(DARK_SOULS_DSR):
            return False  # TODO: DS1R only.
        if not context.active_object:
            return False
        if context.active_object.soulstruct_type != SoulstructType.COLLISION:
            return False
        return True

    def execute(self, context):
        if not self.poll(context):
            return self.error("Cannot use operator at this time. Try selected a single HKX mesh model.")

        # noinspection PyTypeChecker
        hkx_model = context.active_object  # type: bpy.types.MeshObject
        bl_map_collision = BlenderMapCollision(hkx_model)

        model_name = bl_map_collision.tight_name
        if not LOOSE_HKX_COLLISION_STEM_RE.match(model_name):
            self.warning(
                f"HKX map collision model name '{model_name}' should generally be 'h....B.A..' or 'l....B.A..'."
            )
        # NOTE: If this is a new collision, its name must be in standard numeric format so that the map can be
        # detected for the new Binder entry path.
        # TODO: Honestly, probably don't need the full entry path in the Binder.

        both_res_hkxbhd = BothResHKXBHD.from_map_path(Path(self.filepath).parent)

        try:
            hi_hkx, lo_hkx = bl_map_collision.to_hkx_pair(self, hkx_model)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported HKX for '{hkx_model.name}'. Error: {ex}")
        if hi_hkx:
            hi_hkx.dcx_type = DCXType[self.dcx_type]
            both_res_hkxbhd.hi_res.set_hkx(hi_hkx.path_stem, hi_hkx)
        if lo_hkx:
            lo_hkx.dcx_type = DCXType[self.dcx_type]
            both_res_hkxbhd.lo_res.set_hkx(lo_hkx.path_stem, lo_hkx)

        # We only write hi-res to a new temporary file until lo-res is confirmed to write.
        hi_temp_path = None
        if hi_hkx:
            if lo_hkx:
                hi_temp_path = Path(self.filepath).with_name(both_res_hkxbhd.hi_res.path.name + ".tempnew")
                both_res_hkxbhd.hi_res.write(hi_temp_path)  # will overwrite any previous '.tempnew'
            else:
                both_res_hkxbhd.hi_res.write()
        if lo_hkx:
            try:
                both_res_hkxbhd.lo_res.write()
            except Exception as ex:
                traceback.print_exc()
                self.error(f"Cannot write exported lo-res HKX Binder to '{self.filepath}'. Error: {ex}")
                if hi_temp_path:
                    hi_temp_path.unlink(missing_ok=True)
            else:
                if hi_temp_path:
                    create_bak(both_res_hkxbhd.hi_res.path)
                    hi_temp_path.rename(both_res_hkxbhd.hi_res.path)

        # Ensure that we don't leave '.tempnew' files lying around.
        if hi_temp_path and hi_temp_path.is_file():
            hi_temp_path.unlink(missing_ok=True)

        return {"FINISHED"}


class ExportHKXMapCollisionIntoHKXBHD(LoggingOperator):
    """Export a HKX collision file into a FromSoftware DSR map directory BHD."""
    bl_idname = "export_scene_map.hkx_map_collision_entry"
    bl_label = "Export Map Collision"
    bl_description = (
        "Export HKX map collisions into HKXBHD binder in appropriate game map (DS1R only)"
    )

    @classmethod
    def poll(cls, context):
        """Must select at least one mesh.

        TODO: Also currently for DS1R only.
        """
        settings = cls.settings(context)
        if not settings.can_auto_export:
            return False
        if not settings.is_game(DARK_SOULS_DSR):
            return False
        if not context.selected_objects:
            return False
        for obj in context.selected_objects:
            if obj.soulstruct_type != SoulstructType.COLLISION:
                return False
        return True

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select at least one mesh.")

        settings = self.settings(context)
        dcx_type = DCXType.DS1_DS2  # DS1R (inside HKXBHD)
        bl_map_collisions = BlenderMapCollision.from_selected_objects(context)  # type: list[BlenderMapCollision]

        opened_both_res_hkxbhds = {}  # type: dict[str, BothResHKXBHD]  # keys are map stems
        return_strings = set()

        for bl_map_collision in bl_map_collisions:

            if bl_map_collision.name[0] not in "hl":
                self.error(
                    f"Selected mesh '{bl_map_collision.name}' must start with 'h' or 'l' to export as collision."
                )
                continue

            map_stem = settings.get_map_stem_for_export(bl_map_collision.obj, oldest=True)

            model_name = bl_map_collision.tight_name
            if not LOOSE_HKX_COLLISION_STEM_RE.match(model_name):
                return self.error(
                    f"Model name '{model_name}' detected from selected mesh '{bl_map_collision.name}' does not match "
                    f"the required name pattern for a DS1 HKX collision model: 'h......A..' or 'l......A..'"
                )
            # If HKX name is standard, check that it matches the selected map stem and warn user if not.
            numeric_match = NUMERIC_HKX_COLLISION_STEM_RE.match(model_name)
            if numeric_match is None:
                self.warning(
                    f"Model name '{model_name}' detected from selected mesh '{bl_map_collision.name}' does not match "
                    f"the standard name pattern for a DS1 HKX collision model: 'h####B#A##' or 'l####B#A##'. Exporting "
                    f"anyway."
                )
            else:
                block, area = int(numeric_match.group(3)), int(numeric_match.group(4))
                expected_map_stem = f"m{area:02d}_{block:02d}_00_00"
                if expected_map_stem != map_stem:
                    self.warning(
                        f"Map area and/or block in name of detected model name '{model_name}' of selected mesh "
                        f"'{bl_map_collision.name}' does not match the export destination map '{map_stem}'. Exporting "
                        f"anyway."
                    )

            try:
                hi_hkx, lo_hkx = bl_map_collision.to_hkx_pair(self, require_hi=True, use_hi_if_missing_lo=True)
            except Exception as ex:
                traceback.print_exc()
                self.error(f"Cannot get exported hi/lo HKX for '{bl_map_collision.name}'. Error: {ex}")
                continue
            hi_hkx.dcx_type = dcx_type
            lo_hkx.dcx_type = dcx_type

            if map_stem not in opened_both_res_hkxbhds:
                for res in ("h", "l"):
                    for suffix in ("hkxbhd", "hkxbdt"):
                        relative_path = Path(f"map/{map_stem}/{res}{map_stem[1:]}.{suffix}")
                        try:
                            settings.prepare_project_file(relative_path, must_exist=True)
                        except FileNotFoundError as ex:
                            return self.error(
                                f"Could not find file '{relative_path}' for map '{map_stem}'. Error: {ex}"
                            )

                try:
                    map_dir = settings.get_import_map_dir_path(map_stem=map_stem)
                except NotADirectoryError:
                    return self.error(f"Could not find map data directory for map '{map_stem}'.")
                opened_both_res_hkxbhds[map_stem] = BothResHKXBHD.from_map_path(map_dir)

            opened_both_res_hkxbhds[map_stem].hi_res.set_hkx(hi_hkx.path_stem, hi_hkx)
            opened_both_res_hkxbhds[map_stem].lo_res.set_hkx(lo_hkx.path_stem, lo_hkx)
            self.info(f"Added hi-res and lo-res HKX for {model_name} to {map_stem} HKXBHDs.")

        for map_stem, both_res_hkxbhd in opened_both_res_hkxbhds.items():
            return_strings |= settings.export_file(
                self, both_res_hkxbhd.hi_res, Path(f"map/{map_stem}/h{map_stem[1:]}.hkxbhd")
            )
            return_strings |= settings.export_file(
                self, both_res_hkxbhd.lo_res, Path(f"map/{map_stem}/l{map_stem[1:]}.hkxbhd")
            )

        return {"FINISHED"} if "FINISHED" in return_strings else {"CANCELLED"}  # at least one success
