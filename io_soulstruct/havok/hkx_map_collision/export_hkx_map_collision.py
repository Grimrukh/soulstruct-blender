from __future__ import annotations

__all__ = ["ExportLooseHKXMapCollision", "ExportHKXMapCollisionIntoBinder", "QuickExportHKXMapCollision"]

import re
import traceback
import typing as tp
from pathlib import Path

import numpy as np

import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper

from soulstruct.dcx import DCXType
from soulstruct.containers import Binder, BinderEntry
from soulstruct_havok.wrappers.hkx2015 import MapCollisionHKX

from io_soulstruct.general import SoulstructSettings
from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.utilities import *
from .utilities import *

if tp.TYPE_CHECKING:
    from soulstruct.darksouls1r.maps import MSB


DEBUG_MESH_INDEX = None
DEBUG_VERTEX_INDICES = []
LOOSE_HKX_COLLISION_NAME_RE = re.compile(r"^([hl])(\w{6})A(\d\d)$")  # game-readable model name; no extensions
NUMERIC_HKX_COLLISION_NAME_RE = re.compile(r"^([hl])(\d{4})B(\d)A(\d\d)$")  # standard map model name; no extensions


def get_mesh_children(
    operator: LoggingOperator, bl_parent: bpy.types.Object, get_other_resolution: bool
) -> tuple[list, list, str]:
    """Return a tuple of `(bl_meshes, other_res_bl_meshes, other_res)`."""
    bl_meshes = []
    other_res_bl_meshes = []

    target_res = bl_parent.name[0]
    match target_res:
        case "h":
            other_res = "l"
        case "l":
            other_res = "h"
        case _:
            if get_other_resolution:
                raise HKXMapCollisionExportError(
                    f"Selected Empty parent '{bl_parent.name}' must start with 'h' or 'l' to get other resolution."
                )
            # Allow for weird future case of non-h/l prefix...
            other_res = ""

    for child in bl_parent.children:
        child_res = child.name.lower()[0]
        if child.type != "MESH":
            operator.warning(f"Ignoring non-mesh child '{child.name}' of selected Empty parent.")
        elif child_res == target_res:
            bl_meshes.append(child)
        elif get_other_resolution and child_res == other_res:  # cannot be empty here
            other_res_bl_meshes.append(child)
        else:
            operator.warning(f"Ignoring child '{child.name}' of selected Empty parent with non-'h', non-'l' name.")

    # Ensure meshes have the same order as they do in the Blender viewer.
    bl_meshes.sort(key=lambda obj: natural_keys(obj.name))
    other_res_bl_meshes.sort(key=lambda obj: natural_keys(obj.name))

    return bl_meshes, other_res_bl_meshes, other_res


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
        if obj.get("Model File Stem", None) is not None:
            self.filepath = obj["Model File Stem"] + ".hkx"
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
        # NOTE: We don't care if 'Model File Stem' doesn't match here.
        hkx_entry_stem = hkx_path.name.split(".")[0]  # needed for internal HKX name

        try:
            bl_meshes, other_res_bl_meshes, other_res = get_mesh_children(
                self, hkx_parent, self.write_other_resolution
            )
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
            other_res_hkx_entry_stem = f"{other_res}[{hkx_entry_stem[1:]}"  # needed for internal HKX name
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

        hkx_entry_stem = hkx_parent.get("Model File Stem", hkx_parent.name.split(" ")[0].split(".")[0])
        if not LOOSE_HKX_COLLISION_NAME_RE.match(hkx_entry_stem) is None:
            self.warning(
                f"HKX export file name '{hkx_entry_stem}' must be 'h####B#A##' or 'l####B#A##' "
                f"(`allow_any_name = False`)."
            )
        # NOTE: If this is a new collision, its name must be in standard numeric format so that the map can be
        # detected for the new Binder entry path.
        # TODO: Honestly, probably don't need the full entry path in the Binder.

        try:
            export_hkx_to_binder(
                self,
                context,
                hkx_parent,
                hkx_binder_path,
                hkx_entry_stem,
                dcx_type=DCXType[self.dcx_type],
                write_other_resolution=self.write_other_resolution,
                default_entry_path=self.default_entry_path,
                default_entry_flags=self.default_entry_flags,
                overwrite_existing=self.overwrite_existing,
            )
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Could not execute HKX export to Binder. Error: {ex}")

        return {"FINISHED"}


class QuickExportHKXMapCollision(LoggingOperator):
    """Export a HKX collision file into a FromSoftware DSR map directory BHD."""
    bl_idname = "export_scene_map.quick_hkx_map_collision"
    bl_label = "Export Map Collision"
    bl_description = (
        "Export HKX map collisions into HKXBHD binder in appropriate game map (DS1R only)"
    )

    @classmethod
    def poll(cls, context):
        """Must select empty parents of only (and at least one) child meshes.

        TODO: Also currently for DS1R only.
        """
        if SoulstructSettings.get_scene_settings(context).game != "DS1R":
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

        settings = SoulstructSettings.get_scene_settings(context)
        game_directory = settings.game_directory
        map_stem = settings.map_stem
        # NOTE: Always uses DSR DCX.

        if not game_directory or not map_stem:
            return self.error("Game directory and map stem must be set in Blender's Soulstruct global settings.")

        settings.save_settings()

        map_dir_path = Path(game_directory, "map", map_stem)
        if not map_dir_path.is_dir():
            return self.error(f"Invalid game map directory: {map_dir_path}")

        at_least_one_success = False

        for hkx_parent in context.selected_objects:

            if settings.detect_map_from_parent:
                if hkx_parent.parent is None:
                    return self.error(
                        f"Object '{hkx_parent.name}' has no parent. Deselect 'Detect Map from Parent' to use single "
                        f"game map specified in Soulstruct plugin settings."
                    )
                map_stem = hkx_parent.parent.name.split(" ")[0]
                if not MAP_STEM_RE.match(map_stem):
                    return self.error(
                        f"Parent object '{hkx_parent.parent.name}' does not start with a valid map stem."
                    )
            else:
                map_stem = settings.map_stem

            if settings.msb_export_mode:
                # Get model file stem from MSB (must contain matching part).
                collision_part_name = hkx_parent.name.split(" ")[0].split(".")[0]
                msb_path = Path(game_directory, "map/MapStudio", f"{map_stem}.msb")
                msb = get_cached_file(msb_path, settings.get_game_msb_class(context))  # type: MSB
                try:
                    msb_part = msb.collisions.find_entry_name(collision_part_name)
                except KeyError:
                    return self.error(
                        f"Collision part '{collision_part_name}' not found in MSB '{msb_path}'."
                    )
                if not msb_part.model.name:
                    return self.error(
                        f"Collision part '{collision_part_name}' in MSB '{msb_path}' has no model name."
                    )
                hkx_entry_stem = msb_part.model.name + f"A{map_stem[1:3]}"

                # Warn if HKX stem in MSB is unexpected.
                if (model_file_stem := hkx_parent.get("Model File Stem", None)) is not None:
                    if model_file_stem != hkx_entry_stem:
                        self.warning(
                            f"Collision part '{hkx_entry_stem}' in MSB '{msb_path}' has model name "
                            f"'{msb_part.model.name}' but Blender mesh 'Model File Stem' is '{model_file_stem}'. "
                            f"Using HKX stem from MSB model name; you may want to update the Blender mesh."
                        )

                # Update part transform in MSB.
                bl_transform = BlenderTransform.from_bl_obj(hkx_parent)
                msb_part.translate = bl_transform.game_translate
                msb_part.rotate = bl_transform.game_rotate_deg
                msb_part.scale = bl_transform.game_scale

                # Write MSB.
                try:
                    msb.write(msb_path)
                except Exception as ex:
                    self.warning(f"Could not write MSB '{msb_path}' with updated part transform. Error: {ex}")
                else:
                    self.info(f"Wrote MSB '{msb_path}' with updated part transform.")

            else:
                # Guess HKX stem from first 10 characters of name of selected object.
                hkx_entry_stem = hkx_parent.name[:10]

                if not LOOSE_HKX_COLLISION_NAME_RE.match(hkx_entry_stem):
                    return self.error(
                        f"Selected object '{hkx_parent.name}' does not match the required name pattern for "
                        f"a HKX collision parent object: 'h......A..' or 'l......A..'"
                    )

                # If HKX name is standard, check that it matches the selected map stem and warn user if not.
                numeric_match = NUMERIC_HKX_COLLISION_NAME_RE.match(hkx_parent.name[:10])
                if numeric_match is None:
                    self.warning(
                        f"Selected object '{hkx_parent.name}' does not match the standard name pattern for "
                        f"a HKX map collision model: 'h####B#A##' or 'l####B#A##'. Exporting anyway."
                    )
                else:
                    block, area = int(numeric_match.group(3)), int(numeric_match.group(4))
                    expected_map_stem = f"m{area:02d}_{block:02d}_00_00"
                    if expected_map_stem != map_stem:
                        self.warning(
                            f"Map area and/or block in name of selected object '{hkx_parent.name}' does not match the "
                            f"export destination map '{map_stem}'. Exporting anyway."
                        )

            res = hkx_parent.name[0]  # 'h' or 'l'
            hkx_binder_path = map_dir_path / f"{res}{map_stem[1:]}.hkxbhd"  # drop 'm' from stem

            try:
                export_hkx_to_binder(
                    self,
                    context,
                    hkx_parent,
                    hkx_binder_path,
                    hkx_entry_stem,
                    dcx_type=DCXType.DS1_DS2,  # DS1R
                    write_other_resolution=True,
                    default_entry_path="{map}\\{name}.hkx.dcx",  # DS1R
                    default_entry_flags=0x2,
                    overwrite_existing=True,
                    map_stem=map_stem,
                )
                at_least_one_success = True
            except Exception as ex:
                traceback.print_exc()
                # Do not return; keep trying other selected objects.
                self.report(
                    {"ERROR"}, f"Could not export object '{hkx_parent.name}' as HKX map collision. Error: {ex}"
                )

        return {"FINISHED"} if at_least_one_success else {"CANCELLED"}


def find_binder_hkx_entry(
    operator: LoggingOperator,
    binder: Binder,
    hkx_entry_stem: str,
    default_entry_path: str,
    default_entry_flags: int,
    overwrite_existing: bool,
    map_stem="",
) -> BinderEntry:
    matching_entries = binder.find_entries_matching_name(rf"{hkx_entry_stem}\.hkx(\.dcx)?")

    if not matching_entries:
        # Create new entry.
        if "{map}" in default_entry_path:
            if not map_stem:
                if match := NUMERIC_HKX_COLLISION_NAME_RE.match(hkx_entry_stem):
                    block, area = int(match.group(3)), int(match.group(4))
                    map_stem = f"m{area:02d}_{block:02d}_00_00"
                else:
                    raise HKXMapCollisionExportError(
                        f"Could not determine '{{map}}' for new Binder entry from HKX name: {hkx_entry_stem}. It must "
                        f"be in the format '[hl]####A#B##' for map name 'mAA_BB_00_00' to be detected."
                    )
            entry_path = default_entry_path.format(map=map_stem, name=hkx_entry_stem)
        else:
            entry_path = default_entry_path.format(name=hkx_entry_stem)
        new_entry_id = binder.highest_entry_id + 1
        hkx_entry = BinderEntry(
            b"", entry_id=new_entry_id, path=entry_path, flags=default_entry_flags
        )
        binder.add_entry(hkx_entry)
        operator.info(f"Creating new Binder entry: ID {new_entry_id}, path '{entry_path}'")
        return hkx_entry

    if not overwrite_existing:
        raise HKXMapCollisionExportError(
            f"HKX named '{hkx_entry_stem}' already exists in Binder and overwrite is disabled."
        )

    entry = matching_entries[0]
    if len(matching_entries) > 1:
        operator.warning(
            f"Multiple HKXs named '{hkx_entry_stem}' found in Binder. Replacing first: {entry.name}"
        )
    else:
        operator.info(f"Replacing existing Binder entry: ID {entry.id}, path '{entry.path}'")
    return matching_entries[0]


def export_hkx_to_binder(
    operator: LoggingOperator,
    context: bpy.types.Context,
    hkx_parent: bpy.types.Object,
    hkx_binder_path: Path,
    hkx_entry_stem: str,
    dcx_type: DCXType,
    write_other_resolution: bool,
    default_entry_path: str,
    default_entry_flags: int,
    overwrite_existing: bool,
    map_stem="",
):
    try:
        bl_meshes, other_res_bl_meshes, other_res = get_mesh_children(
            operator, hkx_parent, write_other_resolution
        )
    except HKXMapCollisionExportError as ex:
        raise HKXMapCollisionExportError(f"Children of object '{hkx_parent}' cannot be exported. Error: {ex}")

    # Try loading (and finding other) Binder first, so we don't bother exporting any meshes if it fails.
    try:
        binder = Binder.from_path(hkx_binder_path)
    except Exception as ex:
        raise HKXMapCollisionExportError(f"Could not load Binder file. Error: {ex}.")

    other_res_binder = None  # type: Binder | None
    if other_res_bl_meshes:
        other_res_binder_name = f"{other_res}{hkx_binder_path.name[1:]}"
        other_res_binder_path = hkx_binder_path.with_name(other_res_binder_name)
        try:
            other_res_binder = Binder.from_path(other_res_binder_path)
        except Exception as ex:
            raise HKXMapCollisionExportError(f"Could not load Binder file for other resolution. Error: {ex}.")
        if other_res == hkx_binder_path.name[0]:
            # Tried to export, e.g., 'h' parent into 'l' binder. Just swap the binders.
            binder, other_res_binder = other_res_binder, binder

    # Find Binder entries.
    try:
        hkx_entry = find_binder_hkx_entry(
            operator,
            binder,
            hkx_entry_stem,
            default_entry_path,
            default_entry_flags,
            overwrite_existing,
            map_stem,
        )
    except Exception as ex:
        raise HKXMapCollisionExportError(f"Cannot find or create Binder entry for '{hkx_entry_stem}'. Error: {ex}")

    other_res_hkx_entry = None
    if other_res:
        other_res_hkx_entry_stem = f"{other_res}{hkx_entry_stem[1:]}"
        try:
            other_res_hkx_entry = find_binder_hkx_entry(
                operator,
                other_res_binder,
                other_res_hkx_entry_stem,
                default_entry_path,
                default_entry_flags,
                overwrite_existing,
                map_stem,
            )
        except Exception as ex:
            raise HKXMapCollisionExportError(
                f"Cannot find or create Binder entry for '{other_res_hkx_entry_stem}'. Error: {ex}"
            )

    # TODO: Not needed for meshes only?
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

    exporter = HKXMapCollisionExporter(operator, context)

    try:
        hkx = exporter.export_hkx_map_collision(bl_meshes, name=hkx_entry_stem)
    except Exception as ex:
        raise HKXMapCollisionExportError(f"Cannot get exported HKX for '{hkx_entry_stem}'. Error: {ex}")
    hkx.dcx_type = dcx_type

    other_res_hkx = None
    if other_res:
        other_res_hkx_entry_stem = f"{other_res}{hkx_entry_stem[1:]}"
        if other_res_bl_meshes:
            try:
                other_res_hkx = exporter.export_hkx_map_collision(other_res_bl_meshes, name=other_res_hkx_entry_stem)
            except Exception as ex:
                raise HKXMapCollisionExportError(
                    f"Cannot get exported HKX for other resolution '{other_res_hkx_entry_stem}. Error: {ex}"
                )
            other_res_hkx.dcx_type = dcx_type
        else:
            operator.warning(f"No Blender mesh children found for other resolution '{other_res_hkx_entry_stem}'.")

    try:
        hkx_entry.set_from_binary_file(hkx)
    except Exception as ex:
        raise HKXMapCollisionExportError(f"Cannot pack exported HKX '{hkx_entry_stem}'. Error: {ex}")

    if other_res:
        try:
            other_res_hkx_entry.set_from_binary_file(other_res_hkx)
        except Exception as ex:
            raise HKXMapCollisionExportError(
                f"Cannot pack exported other-resolution HKX entry '{other_res_hkx_entry.name}'. Error: {ex}"
            )

    try:
        # Will create a `.bak` file automatically if absent.
        binder.write()
    except Exception as ex:
        raise HKXMapCollisionExportError(f"Cannot write Binder with new HKX '{hkx_entry_stem}'. Error: {ex}")

    if other_res_binder:
        try:
            # Will create a `.bak` file automatically if absent.
            other_res_binder.write()
        except Exception as ex:
            raise HKXMapCollisionExportError(f"Cannot write other-resolution Binder with new HKX. Error: {ex}")


class HKXMapCollisionExporter:

    operator: LoggingOperator

    def __init__(self, operator: LoggingOperator, context):
        self.operator = operator
        self.context = context

    def warning(self, msg: str):
        self.operator.report({"WARNING"}, msg)
        print(f"# WARNING: {msg}")

    @staticmethod
    def export_hkx_map_collision(bl_meshes, name: str) -> MapCollisionHKX:
        """Create HKX from Blender meshes (subparts).

        TODO: Currently only supported for DSR and Havok 2015.
        """
        if not bl_meshes:
            raise ValueError("No meshes given to export to HKX.")

        hkx_meshes = []  # type: list[tuple[np.ndarray, np.ndarray]]
        hkx_material_indices = []  # type: list[int]

        for bl_mesh in bl_meshes:

            if bl_mesh.get("Material Index", None) is None and bl_mesh.get("material_index", None) is not None:
                # NOTE: Legacy code for previous name of this property. TODO: Remove after a few releases.
                material_index = get_bl_prop(bl_mesh, "material_index", int, default=0)
                # Move property to new name.
                bl_mesh["Material Index"] = material_index
                del bl_mesh["material_index"]
            else:
                material_index = get_bl_prop(bl_mesh, "Material Index", int, default=0)
            hkx_material_indices.append(material_index)

            # Swap Y and Z coordinates.
            hkx_verts_list = [[vert.co.x, vert.co.z, vert.co.y] for vert in bl_mesh.data.vertices]
            hkx_verts = np.array(hkx_verts_list, dtype=np.float32)
            hkx_faces = np.empty((len(bl_mesh.data.polygons), 3), dtype=np.uint32)
            for i, face in enumerate(bl_mesh.data.polygons):
                if len(face.vertices) != 3:
                    raise ValueError(
                        f"Found a non-triangular mesh face in HKX (index {i}). Mesh must be triangulated first."
                    )
                hkx_faces[i] = face.vertices

            hkx_meshes.append((hkx_verts, hkx_faces))

        hkx = MapCollisionHKX.from_meshes(
            meshes=hkx_meshes,
            hkx_name=name,
            material_indices=hkx_material_indices,
            # Bundled template HKX serves fine.
            # DCX applied by caller.
        )

        return hkx
