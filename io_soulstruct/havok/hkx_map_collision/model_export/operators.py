from __future__ import annotations

__all__ = [
    "ExportLooseHKXMapCollision",
    "ExportHKXMapCollisionIntoBinder",
    "ExportHKXMapCollisionIntoHKXBHD",
]

import traceback
from pathlib import Path

import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper

from soulstruct.dcx import DCXType
from soulstruct.containers import Binder
from soulstruct.games import DARK_SOULS_DSR

from io_soulstruct.utilities import *
from .core import *


class ExportLooseHKXMapCollision(LoggingOperator, ExportHelper):
    """Export HKX from a selection of Blender meshes."""
    bl_idname = "export_scene.hkx_map_collision"
    bl_label = "Export Loose Map Collision"
    bl_description = "Export child meshes of selected Blender empty parent to a HKX collision file"

    # ExportHelper mixin class uses this
    filename_ext = ".hkx"

    filter_glob: StringProperty(
        default="*.hkx;*.hkx.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    dcx_type: get_dcx_enum_property(DCXType.Null)  # typically no DCX compression for map collisions

    write_other_resolution: BoolProperty(
        name="Write Other Resolution",
        description="Write the other resolution of the collision (h/l) if its submeshes are also under this parent",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        """Must select a single empty parent of only (and at least one) child meshes."""
        settings = cls.settings(context)
        if not settings.is_game(DARK_SOULS_DSR):
            return False  # TODO: DS1R only.
        is_empty_selected = len(context.selected_objects) == 1 and context.selected_objects[0].type == "EMPTY"
        if not is_empty_selected:
            return False
        children = context.selected_objects[0].children
        return len(children) >= 1 and all(child.type == "MESH" for child in children)

    def invoke(self, context, _event):
        """Set default export name to name of object (before first space and without Blender dupe suffix)."""
        if not context.selected_objects:
            return super().invoke(context, _event)

        obj = context.selected_objects[0]
        if obj.get("Model Name", None) is not None:
            self.filepath = obj["Model Name"] + ".hkx"
        self.filepath = obj.name.split(" ")[0].split(".")[0] + ".hkx"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        selected_objs = [obj for obj in context.selected_objects]
        if not selected_objs:
            return self.error("No Empty with child meshes selected for HKX export.")
        if len(selected_objs) > 1:
            return self.error("More than one object cannot be selected for HKX export.")
        hkx_parent = selected_objs[0]

        hkx_path = Path(self.filepath)
        if not LOOSE_HKX_COLLISION_NAME_RE.match(hkx_path.name) is None:
            return self.warning(
                f"HKX file name '{hkx_path.name}' does not match the expected name pattern for "
                f"a HKX collision parent object and will not function in-game: 'h......A..' or 'l......A..'"
            )
        # NOTE: We don't care if 'Model Name' doesn't match here.
        hkx_entry_stem = hkx_path.name.split(".")[0]  # needed for internal HKX name

        try:
            bl_meshes, other_res_bl_meshes, other_res = get_mesh_children(self, hkx_parent, self.write_other_resolution)
        except HKXMapCollisionExportError as ex:
            traceback.print_exc()
            return self.error(f"Children of object '{hkx_parent.name}' cannot be exported. Error: {ex}")

        # TODO: Not needed for meshes only?
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        exporter = HKXMapCollisionExporter(self, context)

        try:
            hkx = exporter.export_hkx_map_collision(bl_meshes, name=hkx_entry_stem)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported HKX for '{hkx_parent.name}'. Error: {ex}")
        hkx.dcx_type = DCXType[self.dcx_type]

        other_res_hkx = None
        if other_res:
            other_res_hkx_entry_stem = f"{other_res}{hkx_entry_stem[1:]}"  # needed for internal HKX name
            if other_res_bl_meshes:
                try:
                    other_res_hkx = exporter.export_hkx_map_collision(
                        other_res_bl_meshes, name=other_res_hkx_entry_stem
                    )
                except Exception as ex:
                    traceback.print_exc()
                    return self.error(
                        f"Cannot get exported HKX for other resolution '{other_res_hkx_entry_stem}. Error: {ex}"
                    )
                other_res_hkx.dcx_type = DCXType[self.dcx_type]
            else:
                self.warning(f"No Blender mesh children found for other resolution '{other_res_hkx_entry_stem}'.")

        try:
            # Will create a `.bak` file automatically if absent.
            hkx.write(hkx_path)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write exported HKX '{hkx_parent.name}' to '{hkx_path}'. Error: {ex}")

        if other_res_hkx:
            other_res_hkx_path = hkx_path.with_name(f"{other_res}{hkx_path.name[1:]}")  # `other_res` guaranteed here
            try:
                # Will create a `.bak` file automatically if absent.
                other_res_hkx.write(other_res_hkx_path)
            except Exception as ex:
                traceback.print_exc()
                return self.error(
                    f"Wrote target resolution HKX '{hkx_path}', but cannot write other-resolution HKX "
                    f"to '{other_res_hkx_path}'. Error: {ex}"
                )

        return {"FINISHED"}


class ExportHKXMapCollisionIntoBinder(LoggingOperator, ImportHelper):
    bl_idname = "export_scene.hkx_map_collision_binder"
    bl_label = "Export Map Collision Into Binder"
    bl_description = "Export a HKX collision file into a FromSoftware Binder (BND/BHD)"

    # ImportHelper mixin class uses this
    filename_ext = ".hkxbhd"

    filter_glob: StringProperty(
        default="*.hkxbhd;*.hkxbhd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    dcx_type: get_dcx_enum_property(DCXType.DS1_DS2)  # map collisions in DS1 binder are compressed

    write_other_resolution: BoolProperty(
        name="Write Other Resolution",
        description="Write the other resolution of the collision (h/l) if its submeshes are also under this parent",
        default=True,
    )

    overwrite_existing: BoolProperty(
        name="Overwrite Existing",
        description="Overwrite first existing '{name}.hkx{.dcx}' matching entry in Binder",
        default=True,
    )

    default_entry_flags: IntProperty(
        name="Default Flags",
        description="Flags to set to Binder entry if it needs to be created",
        default=0x2,
    )

    default_entry_path: StringProperty(
        name="Default Path",
        description="Path prefix to use for Binder entry if it needs to be created. Use {name} as a format "
                    "placeholder for the name of this HKX object and {map} as a format placeholder for map string "
                    "'mAA_BB_00_00', which will try to be detected from HKX name (eg 'h0500B1A12' -> 'm12_01_00_00')",
        default="{map}\\{name}.hkx.dcx",  # note that HKX files inside DSR BHDs are indeed DCX-compressed
    )

    @classmethod
    def poll(cls, context):
        """Must select a single empty parent of only (and at least one) child meshes."""
        settings = cls.settings(context)
        if not settings.is_game(DARK_SOULS_DSR):
            return False  # TODO: DS1R only.
        is_empty_selected = len(context.selected_objects) == 1 and context.selected_objects[0].type == "EMPTY"
        if not is_empty_selected:
            return False
        children = context.selected_objects[0].children
        return len(children) >= 1 and all(child.type == "MESH" for child in children)

    def execute(self, context):
        print("Executing HKX export to Binder...")

        selected_objs = [obj for obj in context.selected_objects]
        if not selected_objs:
            return self.error("No Empty with child meshes selected for HKX export.")
        if len(selected_objs) > 1:
            return self.error("More than one object cannot be selected for HKX export.")
        hkx_parent = selected_objs[0]

        hkx_binder_path = Path(self.filepath)

        hkx_entry_stem = hkx_parent.get("Model Name", get_bl_obj_stem(hkx_parent))
        if not LOOSE_HKX_COLLISION_NAME_RE.match(hkx_entry_stem) is None:
            self.warning(
                f"HKX map collision model name '{hkx_entry_stem}' should generally be 'h....B.A..' or 'l....B.A..'."
            )
        # NOTE: If this is a new collision, its name must be in standard numeric format so that the map can be
        # detected for the new Binder entry path.
        # TODO: Honestly, probably don't need the full entry path in the Binder.

        try:
            bl_meshes, other_res_bl_meshes, other_res = get_mesh_children(self, hkx_parent, self.write_other_resolution)
        except HKXMapCollisionExportError as ex:
            raise HKXMapCollisionExportError(f"Children of object '{hkx_parent}' cannot be exported. Error: {ex}")

        hkxbhd, other_res_hkxbhd = load_hkxbhds(hkx_binder_path, other_res=other_res)

        try:
            export_hkx_to_binder(
                self,
                context,
                bl_meshes,
                hkxbhd,
                hkx_entry_stem,
                dcx_type=DCXType[self.dcx_type],
                default_entry_path=self.default_entry_path,
                default_entry_flags=self.default_entry_flags,
                overwrite_existing=self.overwrite_existing,
            )
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Could not execute HKX export to Binder. Error: {ex}")

        if other_res:
            other_res_hkx_entry_stem = f"{other_res}{hkx_entry_stem[1:]}" if other_res else None
            try:
                export_hkx_to_binder(
                    self,
                    context,
                    other_res_bl_meshes,
                    other_res_hkxbhd,
                    other_res_hkx_entry_stem,
                    dcx_type=DCXType[self.dcx_type],
                    default_entry_path=self.default_entry_path,
                    default_entry_flags=self.default_entry_flags,
                    overwrite_existing=self.overwrite_existing,
                )
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Could not execute HKX export to Binder. Error: {ex}")

        try:
            hkxbhd.write()
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Could not write Binder to '{hkx_binder_path}'. Error: {ex}")

        if other_res_hkxbhd:
            try:
                other_res_hkxbhd.write()
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Could not write Binder to '{hkx_binder_path}'. Error: {ex}")

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
        """Must select empty parents of only (and at least one) child meshes.

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
            if obj.type != "EMPTY":
                return False
            if not obj.children:
                return False
            if not all(child.type == "MESH" for child in obj.children):
                return False
        return True

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select a parent of one or more collision submeshes.")

        settings = self.settings(context)
        settings.save_settings()

        export_kwargs = dict(
            operator=self,
            context=context,
            dcx_type=DCXType.DS1_DS2,  # DS1R (inside HKXBHD)
            default_entry_path="{map}\\{name}.hkx.dcx",  # DS1R
            default_entry_flags=0x2,
            overwrite_existing=True,
        )

        opened_hkxbhds = {"h": {}, "l": {}}  # type: dict[str, dict[Path, Binder]]  # keys are relative HKXBHD paths
        return_strings = set()

        for hkx_parent in context.selected_objects:

            res = hkx_parent.name[0]
            if res not in "hl":
                self.error(f"Selected object '{hkx_parent.name}' must start with 'h' or 'l' to export.")
                continue

            map_stem = settings.get_map_stem_for_export(hkx_parent, oldest=True)

            # Guess HKX stem from first 10 characters of name of selected object if 'Model Name' is not set.
            # TODO: This assumes DS1 model stem formatting.
            hkx_entry_stem = hkx_parent.get("Model Name", hkx_parent.name[:10])

            if not LOOSE_HKX_COLLISION_NAME_RE.match(hkx_entry_stem):
                return self.error(
                    f"Selected object's model stem '{hkx_entry_stem}' does not match the required name pattern for "
                    f"a DS1 HKX collision parent object: 'h......A..' or 'l......A..'"
                )

            # If HKX name is standard, check that it matches the selected map stem and warn user if not.
            numeric_match = NUMERIC_HKX_COLLISION_NAME_RE.match(hkx_entry_stem)
            if numeric_match is None:
                self.warning(
                    f"Selected object model stem '{hkx_entry_stem}' does not match the standard name pattern for "
                    f"a DS1 HKX map collision model: 'h####B#A##' or 'l####B#A##'. Exporting anyway."
                )
            else:
                block, area = int(numeric_match.group(3)), int(numeric_match.group(4))
                expected_map_stem = f"m{area:02d}_{block:02d}_00_00"
                if expected_map_stem != map_stem:
                    self.warning(
                        f"Map area and/or block in name of selected object model stem '{hkx_entry_stem}' does not "
                        f"match the export destination map '{map_stem}'. Exporting anyway."
                    )

            try:
                bl_meshes, other_res_bl_meshes, other_res = get_mesh_children(self, hkx_parent, True)
            except HKXMapCollisionExportError as ex:
                raise HKXMapCollisionExportError(f"Children of object '{hkx_parent}' cannot be exported. Error: {ex}")

            if res == "h":
                res_meshes = {
                    "h": bl_meshes,
                    "l": other_res_bl_meshes,
                }
            else:
                # Swap res and meshes.
                res_meshes = {
                    "h": other_res_bl_meshes,
                    "l": bl_meshes,
                }

            for r in "hl":
                meshes = res_meshes[r]
                res_entry_stem = f"{r}{hkx_entry_stem[1:]}"
                if not meshes:
                    continue
                opened_res_hkxbhds = opened_hkxbhds[r]
                relative_hkxbhd_path = Path(f"map/{map_stem}/{r}{map_stem[1:]}.hkxbhd")  # no DCX
                if relative_hkxbhd_path not in opened_res_hkxbhds:
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

                    opened_res_hkxbhds[relative_hkxbhd_path] = Binder.from_path(hkxbhd_path)

                hkxbhd = opened_res_hkxbhds[relative_hkxbhd_path]

                try:
                    export_hkx_to_binder(
                        bl_meshes=meshes,
                        hkxbhd=hkxbhd,
                        hkx_entry_stem=res_entry_stem,
                        map_stem=map_stem,
                        **export_kwargs,
                    )
                except Exception as ex:
                    traceback.print_exc()
                    self.error(f"Could not execute HKX export to Binder. Error: {ex}")

        for opened_res_hkxbhds in opened_hkxbhds.values():
            for relative_hkxbhd_path, hkxbhd in opened_res_hkxbhds.items():
                # Sort entries by name.
                hkxbhd.entries.sort(key=lambda e: e.name)
                return_strings |= settings.export_file(self, hkxbhd, relative_hkxbhd_path)

        return {"FINISHED"} if "FINISHED" in return_strings else {"CANCELLED"}  # at least one success

