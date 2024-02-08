from __future__ import annotations

__all__ = [
    "ExportLooseHKXMapCollision",
    "ExportHKXMapCollisionIntoBinder",
    "ExportHKXMapCollisionIntoHKXBHD",
]

import traceback
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper

from soulstruct.dcx import DCXType
from soulstruct.containers import Binder
from soulstruct.games import DARK_SOULS_DSR

from io_soulstruct.utilities import *
from .core import *


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
        if len(context.selected_objects) != 1:
            return False
        if context.selected_objects[0].type != "MESH":
            return False
        return True

    def invoke(self, context, _event):
        """Set default export name to name of object (before first space and without Blender dupe suffix)."""
        if not context.selected_objects:
            return super().invoke(context, _event)

        mesh = context.selected_objects[0]
        model_name = find_model_name(self, mesh, warn_property_mismatch=False)
        settings = self.settings(context)
        self.filepath = settings.game.process_dcx_path(f"{model_name}.hkx")
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not self.poll(context):
            return self.error("Cannot use operator at this time. Try selected a single HKX mesh model.")

        # noinspection PyTypeChecker
        hkx_model = context.selected_objects[0]  # type: bpy.types.MeshObject

        hkx_path = Path(self.filepath)
        if not LOOSE_HKX_COLLISION_NAME_RE.match(hkx_path.name) is None:
            return self.warning(
                f"HKX file name '{hkx_path.name}' does not match the expected name pattern for "
                f"a HKX collision parent object and will not function in-game: 'h......A..' or 'l......A..'"
            )

        exporter = HKXMapCollisionExporter(self, context)

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
            hi_hkx, lo_hkx = exporter.export_hkx_map_collision(hkx_model, hi_name=hi_name, lo_name=lo_name)
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

    write_other_resolution: bpy.props.BoolProperty(
        name="Write Other Resolution",
        description="Write the other resolution of the collision (h/l) if its submeshes are also under this parent",
        default=True,
    )

    overwrite_existing: bpy.props.BoolProperty(
        name="Overwrite Existing",
        description="Overwrite first existing '{name}.hkx{.dcx}' matching entry in Binder",
        default=True,
    )

    default_entry_path: bpy.props.StringProperty(
        name="Default Path",
        description="Path prefix to use for Binder entry if it needs to be created. Use {name} as a format "
                    "placeholder for the name of this HKX object and {map} as a format placeholder for map string "
                    "'mAA_BB_00_00', which will try to be detected from HKX name (eg 'h0500B1A12' -> 'm12_01_00_00')",
        default="{map}\\{name}.hkx.dcx",  # note that HKX files inside DSR BHDs are indeed DCX-compressed
    )

    @classmethod
    def poll(cls, context):
        """Must select a single mesh."""
        settings = cls.settings(context)
        if not settings.is_game(DARK_SOULS_DSR):
            return False  # TODO: DS1R only.
        if len(context.selected_objects) != 1:
            return False
        if context.selected_objects[0].type != "MESH":
            return False
        return True

    def execute(self, context):
        if not self.poll(context):
            return self.error("Cannot use operator at this time. Try selected a single HKX mesh model.")

        # noinspection PyTypeChecker
        hkx_model = context.selected_objects[0]  # type: bpy.types.MeshObject

        model_name = find_model_name(self, hkx_model, warn_property_mismatch=False)  # can't automatically add map area
        if not LOOSE_HKX_COLLISION_NAME_RE.match(model_name):
            self.warning(
                f"HKX map collision model name '{model_name}' should generally be 'h....B.A..' or 'l....B.A..'."
            )
        # NOTE: If this is a new collision, its name must be in standard numeric format so that the map can be
        # detected for the new Binder entry path.
        # TODO: Honestly, probably don't need the full entry path in the Binder.

        hkx_binder_path = Path(self.filepath)
        hi_binder_path = hi_name = lo_binder_path = lo_name = None
        if hkx_binder_path.name.startswith("h"):
            hi_binder_path = hkx_binder_path
            hi_name = model_name  # needed for internal HKX name
            if self.write_other_resolution:
                lo_binder_path = hkx_binder_path.with_name(f"l{hkx_binder_path.name[1:]}")
                lo_name = f"l{model_name[1:]}"
        elif hkx_binder_path.name.startswith("l"):
            lo_binder_path = hkx_binder_path
            lo_name = model_name
            if self.write_other_resolution:
                hi_binder_path = hkx_binder_path.with_name(f"h{hkx_binder_path.name[1:]}")
                hi_name = f"h{model_name[1:]}"
        else:
            if self.write_other_resolution:
                self.warning(
                    f"Cannot determine other HKX resolution ('h'/'l') from Binder name '{hkx_binder_path.name}'. "
                    f"Written Binder entry will contain 'Hi' submeshes only; not writing another resolution."
                )
            hi_binder_path = hkx_binder_path
            hi_name = model_name  # needed for internal HKX name

        hi_hkxbhd, lo_hkxbhd = load_hkxbhds(hi_binder_path, lo_binder_path)

        exporter = HKXMapCollisionExporter(self, context)

        try:
            hi_hkx, lo_hkx = exporter.export_hkx_map_collision(hkx_model, hi_name=hi_name, lo_name=lo_name)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported HKX for '{hkx_model.name}'. Error: {ex}")

        # Add HKX entries to Binder.
        binder_kwargs = dict(
            default_entry_path=self.default_entry_path,
            default_entry_flags=0x2,
            overwrite_existing=self.overwrite_existing,
        )
        if hi_hkx:
            hi_hkx.dcx_type = DCXType[self.dcx_type]
            try:
                export_hkx_to_binder(self, hi_hkx, hi_hkxbhd, hi_name, **binder_kwargs)
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Could not add hi-res HKX entry to Binder. Error: {ex}")
        if lo_hkx:
            lo_hkx.dcx_type = DCXType[self.dcx_type]
            try:
                export_hkx_to_binder(self, lo_hkx, lo_hkxbhd, lo_name, **binder_kwargs)
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Could not add lo-res HKX entry to Binder. Error: {ex}")

        # To ensure that NEITHER Binder file is written if EITHER fails, we make a temporary '.tempbak' file for the
        # hi-res Binder file if it already exists, and restore that file if the lo-res write fails.

        hi_tempbak_path = None
        hi_written = False  # used to delete hi-res file if lo-res fails
        if hi_hkx:
            if hi_binder_path.is_file():
                # Additional temporary backup.
                hi_tempbak_path = hi_binder_path.with_suffix(f"{hi_binder_path.suffix}.tempbak")
                hi_binder_path.rename(hi_tempbak_path)
            try:
                # Will also create a `.bak` file automatically if absent.
                hi_hkxbhd.write(hi_binder_path)
                self.info(f"Exported hi-res HKX collision to '{hi_binder_path}' and wrote Binder.")
            except Exception as ex:
                traceback.print_exc()
                self.error(f"Cannot write exported hi-res Binder to '{hi_binder_path}'. Error: {ex}")
            else:
                hi_written = True
        if lo_hkx:
            try:
                # Will create a `.bak` file automatically if absent.
                lo_hkxbhd.write(lo_binder_path)
                self.info(f"Exported lo-res HKX collision to '{lo_binder_path}' and wrote Binder.")
            except Exception as ex:
                traceback.print_exc()
                self.error(f"Cannot write exported lo-res Binder to '{lo_binder_path}'. Error: {ex}")
                if hi_written:
                    # Restore hi-res file if lo-res write fails.
                    hi_binder_path.unlink(missing_ok=True)
                    if hi_tempbak_path:
                        hi_tempbak_path.rename(hi_binder_path)

        # Ensure that we don't leave '.tempbak' files lying around.
        if hi_tempbak_path and hi_tempbak_path.is_file():
            hi_tempbak_path.unlink(missing_ok=True)

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
            if obj.type != "MESH":
                return False
        return True

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select at least one mesh.")

        settings = self.settings(context)
        settings.save_settings()
        dcx_type = DCXType.DS1_DS2  # DS1R (inside HKXBHD)
        binder_kwargs = dict(
            operator=self,
            default_entry_path="{map}\\{name}.hkx.dcx",  # DS1R
            default_entry_flags=0x2,
            overwrite_existing=True,
        )

        opened_hkxbhds = {"h": {}, "l": {}}  # type: dict[str, dict[Path, Binder]]  # keys are relative HKXBHD paths
        return_strings = set()

        exporter = HKXMapCollisionExporter(self, context)

        for hkx_model in context.selected_objects:
            hkx_model: bpy.types.MeshObject

            if hkx_model.name[0] not in "hl":
                self.error(f"Selected mesh '{hkx_model.name}' must start with 'h' or 'l' to export as collision.")
                continue

            map_stem = settings.get_map_stem_for_export(hkx_model, oldest=True)

            model_name = find_model_name(self, hkx_model, process_model_name_map_area(map_stem))

            if not LOOSE_HKX_COLLISION_NAME_RE.match(model_name):
                return self.error(
                    f"Model name '{model_name}' detected from selected mesh '{hkx_model.name}' does not match the "
                    f"required name pattern for a DS1 HKX collision model: 'h......A..' or 'l......A..'"
                )

            # If HKX name is standard, check that it matches the selected map stem and warn user if not.
            numeric_match = NUMERIC_HKX_COLLISION_NAME_RE.match(model_name)
            if numeric_match is None:
                self.warning(
                    f"Model name '{model_name}' detected from selected mesh '{hkx_model.name}' does not match the "
                    f"standard name pattern for a DS1 HKX collision model: 'h####B#A##' or 'l####B#A##'. Exporting "
                    f"anyway."
                )
            else:
                block, area = int(numeric_match.group(3)), int(numeric_match.group(4))
                expected_map_stem = f"m{area:02d}_{block:02d}_00_00"
                if expected_map_stem != map_stem:
                    self.warning(
                        f"Map area and/or block in name of detected model name '{model_name}' of selected mesh "
                        f"'{hkx_model.name}' does not match the export destination map '{map_stem}'. Exporting anyway."
                    )

            if model_name.startswith("h"):
                hi_name = model_name
                lo_name = f"l{model_name[1:]}"
            else:  # must start with 'l'
                hi_name = f"h{model_name[1:]}"
                lo_name = model_name

            try:
                hi_hkx, lo_hkx = exporter.export_hkx_map_collision(
                    hkx_model, hi_name=hi_name, lo_name=lo_name, require_hi=True, use_hi_if_missing_lo=True
                )
            except Exception as ex:
                traceback.print_exc()
                self.error(f"Cannot get exported hi/lo HKX for '{hkx_model.name}'. Error: {ex}")
                continue

            for r, hkx, name in (("h", hi_hkx, hi_name), ("l", lo_hkx, lo_name)):
                # NOTE: `hkx` will never be None due to exporter arguments above.

                relative_hkxbhd_path = Path(f"map/{map_stem}/{r}{map_stem[1:]}.hkxbhd")  # no DCX
                if relative_hkxbhd_path not in opened_hkxbhds[r]:
                    try:
                        hkxbhd_path = settings.prepare_project_file(relative_hkxbhd_path, False, must_exist=True)
                    except FileNotFoundError as ex:
                        return self.error(
                            f"Could not find HKXBHD file '{relative_hkxbhd_path}' for map '{map_stem}'. Error: {ex}"
                        )

                    relative_hkxbdt_path = Path(f"map/{map_stem}/{r}{map_stem[1:]}.hkxbdt")  # no DCX
                    try:
                        settings.prepare_project_file(relative_hkxbdt_path, False, must_exist=True)  # path not needed
                    except FileNotFoundError as ex:
                        return self.error(
                            f"Could not find HKXBDT file '{relative_hkxbdt_path}' for map '{map_stem}'. Error: {ex}"
                        )

                    opened_hkxbhds[r][relative_hkxbhd_path] = Binder.from_path(hkxbhd_path)

                hkxbhd = opened_hkxbhds[r][relative_hkxbhd_path]

                hkx.dcx_type = dcx_type

                try:
                    export_hkx_to_binder(
                        hkx=hkx,
                        hkxbhd=hkxbhd,
                        hkx_entry_stem=name,
                        map_stem=map_stem,
                        **binder_kwargs,
                    )
                except Exception as ex:
                    traceback.print_exc()
                    self.error(f"Could not execute HKX export to Binder. Error: {ex}")
                    continue

        for opened_res_hkxbhds in opened_hkxbhds.values():
            for relative_hkxbhd_path, hkxbhd in opened_res_hkxbhds.items():
                # Sort entries by name.
                hkxbhd.entries.sort(key=lambda e: e.name)
                return_strings |= settings.export_file(self, hkxbhd, relative_hkxbhd_path)

        return {"FINISHED"} if "FINISHED" in return_strings else {"CANCELLED"}  # at least one success
