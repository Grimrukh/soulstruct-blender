from __future__ import annotations

__all__ = ["ExportHKXMapCollision", "ExportHKXMapCollisionIntoBinder", "ExportHKXMapCollisionToMapDirectoryBHD"]

import re
import traceback
from pathlib import Path

import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper
from soulstruct.dcx import DCXType

from soulstruct.containers import Binder, BinderEntry

from soulstruct_havok.wrappers.hkx2015 import MapCollisionHKX

from io_soulstruct.general import GlobalSettings
from io_soulstruct.utilities import *
from .utilities import *


DEBUG_MESH_INDEX = None
DEBUG_VERTEX_INDICES = []
HKX_COLLISION_NAME_RE = re.compile(r"^([hl])(\d\d\d\d)B(\d)A(\d\d)$")  # no extensions


def get_mesh_children(
    operator: LoggingOperator, bl_parent: bpy.types.Object, get_other_resolution: bool, allow_any_name: bool
) -> tuple[str, list, str, list]:
    """Return a tuple of `(hkx_model_name, bl_meshes, other_res_model_name, other_res_bl_meshes)`."""
    bl_meshes = []
    other_res_bl_meshes = []
    parent_name = bl_parent.name

    if not allow_any_name:
        if not HKX_COLLISION_NAME_RE.match(parent_name[:10]):
            raise HKXMapCollisionExportError(
                f"Selected Empty parent '{parent_name}' must start with 'h####B#A##' or 'l####B#A##'."
            )
        hkx_model_name = parent_name[:10]  # string that appears in actual HKX file and is the exported file stem
    else:
        hkx_model_name = parent_name

    match hkx_model_name[0]:
        case "h":
            other_res_model_name = f"l{hkx_model_name[1:]}"
        case "l":
            other_res_model_name = f"h{hkx_model_name[1:]}"
        case _:
            if get_other_resolution:
                raise HKXMapCollisionExportError(
                    f"Selected Empty parent '{hkx_model_name}' must start with 'h' or 'l' to get other resolution."
                )
            other_res_model_name = ""

    for child in bl_parent.children:
        res = child.name.lower()[0]
        if child.type != "MESH":
            operator.warning(f"Ignoring non-mesh child '{child.name}' of selected Empty parent.")
        elif res == hkx_model_name[0]:
            bl_meshes.append(child)
        elif get_other_resolution and res == other_res_model_name[0]:  # cannot be empty here
            other_res_bl_meshes.append(child)
        else:
            operator.warning(f"Ignoring child '{child.name}' of selected Empty parent with non-'Hi', non-'Lo' name.")

    # Ensure meshes have the same order as they do in the Blender viewer.
    bl_meshes.sort(key=lambda obj: natural_keys(obj.name))
    other_res_bl_meshes.sort(key=lambda obj: natural_keys(obj.name))

    return hkx_model_name, bl_meshes, other_res_model_name, other_res_bl_meshes


class ExportHKXMapCollision(LoggingOperator, ExportHelper):
    """Export HKX from a selection of Blender meshes."""
    bl_idname = "export_scene.hkx_map_collision"
    bl_label = "Export HKX Collision"
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

    allow_any_name: BoolProperty(
        name="Allow Any Name",
        description="Allow any name for the parent Empty (i.e. does not have to start with "
                    "'h####B#A##' or 'l####B#A##')",
        default=False,
    )

    # TODO: Options to:
    #   - Detect appropriate MSB and update transform of this model instance (if unique) (low priority, especially
    #     because I handle MSB collision transforms procedurally).

    @classmethod
    def poll(cls, context):
        """Must select a single empty parent of only (and at least one) child meshes."""
        is_empty_selected = len(context.selected_objects) == 1 and context.selected_objects[0].type == "EMPTY"
        if not is_empty_selected:
            return False
        children = context.selected_objects[0].children
        return len(children) >= 1 and all(child.type == "MESH" for child in children)

    def execute(self, context):
        selected_objs = [obj for obj in context.selected_objects]
        if not selected_objs:
            return self.error("No Empty with child meshes selected for HKX export.")
        if len(selected_objs) > 1:
            return self.error("More than one object cannot be selected for HKX export.")
        hkx_parent = selected_objs[0]

        hkx_path = Path(self.filepath)
        if not self.allow_any_name and HKX_COLLISION_NAME_RE.match(hkx_path.name) is None:
            return self.error(
                f"HKX export file name '{hkx_path.name}' must be 'h####B#A##' or 'l####B#A##' "
                f"(`allow_any_name = False`)."
            )

        try:
            hkx_model_name, bl_meshes, other_res_model_name, other_res_bl_meshes = get_mesh_children(
                self, hkx_parent, self.write_other_resolution, self.allow_any_name
            )
        except HKXMapCollisionExportError as ex:
            traceback.print_exc()
            return self.error(f"Children of object '{hkx_parent.name}' cannot be exported. Error: {ex}")

        # TODO: Not needed for meshes only?
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        exporter = HKXMapCollisionExporter(self, context)

        try:
            hkx = exporter.export_hkx_map_collision(bl_meshes, name=hkx_model_name)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported HKX for '{hkx_model_name}'. Error: {ex}")
        hkx.dcx_type = DCXType[self.dcx_type]

        other_res_hkx = None
        if other_res_model_name:
            if other_res_bl_meshes:
                try:
                    other_res_hkx = exporter.export_hkx_map_collision(other_res_bl_meshes, name=other_res_model_name)
                except Exception as ex:
                    traceback.print_exc()
                    return self.error(
                        f"Cannot get exported HKX for other resolution '{other_res_model_name}. Error: {ex}"
                    )
                other_res_hkx.dcx_type = DCXType[self.dcx_type]
            else:
                self.warning(f"No Blender mesh children found for other resolution '{other_res_model_name}'.")

        try:
            # Will create a `.bak` file automatically if absent.
            hkx.write(hkx_path)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write exported HKX '{hkx_model_name}' to '{hkx_path}'. Error: {ex}")

        if other_res_hkx:
            other_res_hkx_path = hkx_path.with_name(f"{other_res_model_name[0]}{hkx_path.name[1:]}")
            try:
                # Will create a `.bak` file automatically if absent.
                other_res_hkx.write(other_res_hkx_path)
            except Exception as ex:
                traceback.print_exc()
                return self.error(
                    f"Wrote target resolution HKX '{hkx_model_name}', but cannot write other-resolution HKX "
                    f"'{other_res_model_name}' to '{other_res_hkx_path}'. Error: {ex}"
                )

        return {"FINISHED"}


class ExportHKXMapCollisionIntoBinder(LoggingOperator, ImportHelper):
    bl_idname = "export_scene.hkx_map_collision_binder"
    bl_label = "Export HKX Collision Into Binder"
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

    allow_any_name: BoolProperty(
        name="Allow Any Name",
        description="Allow any name for the parent Empty (i.e. does not have to start with "
                    "'h####B#A##' or 'l####B#A##')",
        default=False,
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

        try:
            export_hkx_to_binder(
                self,
                context,
                hkx_parent,
                hkx_binder_path,
                dcx_type=DCXType[self.dcx_type],
                write_other_resolution=self.write_other_resolution,
                allow_any_name=self.allow_any_name,
                default_entry_path=self.default_entry_path,
                default_entry_flags=self.default_entry_flags,
                overwrite_existing=self.overwrite_existing,
            )
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Could not execute HKX export to Binder. Error: {ex}")

        return {"FINISHED"}


class ExportHKXMapCollisionToMapDirectoryBHD(LoggingOperator):
    """Export a HKX collision file into a FromSoftware DSR map directory BHD."""
    bl_idname = "export_scene_map.hkx_map_collision"
    bl_label = "Export HKX Collision to Map Directory BHD"
    bl_description = (
        "Export a HKX collision file into a FromSoftware '.hkxbhd' Binder in a specific map directory in DSR"
    )

    @classmethod
    def poll(cls, context):
        """Must select a single empty parent of only (and at least one) child meshes.

        TODO: Also currently for DS1R only.
        """
        if GlobalSettings.get_scene_settings(context).game != "DS1R":
            return False
        is_empty_selected = len(context.selected_objects) == 1 and context.selected_objects[0].type == "EMPTY"
        if not is_empty_selected:
            return False
        children = context.selected_objects[0].children
        return len(children) >= 1 and all(child.type == "MESH" for child in children)

    def execute(self, context):

        settings = GlobalSettings.get_scene_settings(context)
        game_directory = settings.game_directory
        map_stem = settings.map_stem
        # NOTE: Always uses DSR DCX.

        if not game_directory or not map_stem:
            return self.error("Game directory and map stem must be set in Blender's Soulstruct global settings.")

        settings.save_settings()

        map_dir_path = Path(game_directory, "map", map_stem)
        if not map_dir_path.is_dir():
            return self.error(f"Invalid game map directory: {map_dir_path}")

        selected_objs = [obj for obj in context.selected_objects]
        if not selected_objs:
            return self.error("No Empty with child meshes selected for HKX export.")
        if len(selected_objs) > 1:
            return self.error("More than one object cannot be selected for HKX export.")
        hkx_parent = selected_objs[0]

        name_match = HKX_COLLISION_NAME_RE.match(hkx_parent.name[:10])
        if name_match is None:
            return self.error(
                f"Selected object '{hkx_parent.name}' does not match the expected name pattern for "
                f"a HKX collision parent object: 'h....A.B..' or 'l....A.B..'."
            )

        block, area = int(name_match.group(3)), int(name_match.group(4))
        name_map_stem = f"m{area:02d}_{block:02d}_00_00"  # TODO: 01 suffix for Darkroot collisions? Don't think so...
        # TODO: could theoretically do some kind of name swizzling to quickly export to the 'wrong map', but just
        #  enforcing a match between selected map stem and collision name for now.
        if name_map_stem != map_stem:
            return self.error(
                f"Selected object '{hkx_parent.name}' does not match the expected map stem '{map_stem}'."
            )

        res = hkx_parent.name[0]
        hkx_binder_path = map_dir_path / f"{res}{map_stem[1:]}.hkxbhd"  # drop 'm' from stem

        try:
            export_hkx_to_binder(
                self,
                context,
                hkx_parent,
                hkx_binder_path,
                dcx_type=DCXType.DS1_DS2,
                write_other_resolution=True,
                allow_any_name=False,
                default_entry_path="{map}\\{name}.hkx.dcx",
                default_entry_flags=0x2,
                overwrite_existing=True,
            )
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Could not execute HKX export to Binder. Error: {ex}")

        return {"FINISHED"}


def find_binder_hkx_entry(
    operator: LoggingOperator,
    binder: Binder,
    hkx_model_name: str,
    default_entry_path: str,
    default_entry_flags: int,
    overwrite_existing: bool,
) -> BinderEntry:
    matching_entries = binder.find_entries_matching_name(rf"{hkx_model_name}\.hkx(\.dcx)?")

    if not matching_entries:
        # Create new entry.
        if "{map}" in default_entry_path:
            if match := HKX_COLLISION_NAME_RE.match(hkx_model_name):
                block, area = int(match.group(3)), int(match.group(4))
                map_str = f"m{area:02d}_{block:02d}_00_00"
            else:
                raise HKXMapCollisionExportError(
                    f"Could not determine '{{map}}' for new Binder entry from HKX name: {hkx_model_name}. It must "
                    f"be in the format '[hl]####A#B##' for map name 'mAA_BB_00_00' to be detected."
                )
            entry_path = default_entry_path.format(map=map_str, name=hkx_model_name)
        else:
            entry_path = default_entry_path.format(name=hkx_model_name)
        new_entry_id = binder.highest_entry_id + 1
        hkx_entry = BinderEntry(
            b"", entry_id=new_entry_id, path=entry_path, flags=default_entry_flags
        )
        binder.add_entry(hkx_entry)
        operator.info(f"Creating new Binder entry: ID {new_entry_id}, path '{entry_path}'")
        return hkx_entry

    if not overwrite_existing:
        raise HKXMapCollisionExportError(
            f"HKX named '{hkx_model_name}' already exists in Binder and overwrite is disabled."
        )

    entry = matching_entries[0]
    if len(matching_entries) > 1:
        operator.warning(
            f"Multiple HKXs named '{hkx_model_name}' found in Binder. Replacing first: {entry.name}"
        )
    else:
        operator.info(f"Replacing existing Binder entry: ID {entry.id}, path '{entry.path}'")
    return matching_entries[0]


def export_hkx_to_binder(
    operator: LoggingOperator,
    context: bpy.types.Context,
    hkx_parent: bpy.types.Object,
    hkx_binder_path: Path,
    dcx_type: DCXType,
    write_other_resolution: bool,
    allow_any_name: bool,
    default_entry_path: str,
    default_entry_flags: int,
    overwrite_existing: bool,
):
    try:
        hkx_model_name, bl_meshes, other_res_model_name, other_res_bl_meshes = get_mesh_children(
            operator, hkx_parent, write_other_resolution, allow_any_name
        )
    except HKXMapCollisionExportError as ex:
        raise HKXMapCollisionExportError(f"Children of object '{hkx_parent}' cannot be exported. Error: {ex}")

    # Try loading (and finding other) Binder first, so we don't bother exporting any meshes if it fails.
    try:
        binder = Binder.from_path(hkx_binder_path)
    except Exception as ex:
        raise HKXMapCollisionExportError(f"Could not load Binder file. Error: {ex}.")

    other_res_binder = None  # type: Binder | None
    if other_res_model_name and other_res_bl_meshes:
        other_res_binder_name = f"{other_res_model_name[0]}{hkx_binder_path.name[1:]}"
        other_res_binder_path = hkx_binder_path.with_name(other_res_binder_name)
        try:
            other_res_binder = Binder.from_path(other_res_binder_path)
        except Exception as ex:
            raise HKXMapCollisionExportError(f"Could not load Binder file for other resolution. Error: {ex}.")
        if other_res_binder_name[0] == hkx_binder_path.name[0]:
            # Tried to export, e.g., 'h' parent into 'l' binder. Just swap the binders.
            binder, other_res_binder = other_res_binder, binder

    # Find Binder entries.
    try:
        hkx_entry = find_binder_hkx_entry(
            operator,
            binder,
            hkx_model_name,
            default_entry_path,
            default_entry_flags,
            overwrite_existing,
        )
    except Exception as ex:
        raise HKXMapCollisionExportError(f"Cannot find or create Binder entry for '{hkx_model_name}'. Error: {ex}")

    other_res_hkx_entry = None
    if other_res_model_name:
        try:
            other_res_hkx_entry = find_binder_hkx_entry(
                operator,
                other_res_binder,
                other_res_model_name,
                default_entry_path,
                default_entry_flags,
                overwrite_existing,
            )
        except Exception as ex:
            raise HKXMapCollisionExportError(
                f"Cannot find or create Binder entry for '{other_res_model_name}'. Error: {ex}"
            )

    # TODO: Not needed for meshes only?
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

    exporter = HKXMapCollisionExporter(operator, context)

    try:
        hkx = exporter.export_hkx_map_collision(bl_meshes, name=hkx_model_name)
    except Exception as ex:
        raise HKXMapCollisionExportError(f"Cannot get exported HKX for '{hkx_model_name}'. Error: {ex}")
    hkx.dcx_type = dcx_type

    other_res_hkx = None
    if other_res_model_name:
        if other_res_bl_meshes:
            try:
                other_res_hkx = exporter.export_hkx_map_collision(other_res_bl_meshes, name=other_res_model_name)
            except Exception as ex:
                raise HKXMapCollisionExportError(
                    f"Cannot get exported HKX for other resolution '{other_res_model_name}. Error: {ex}"
                )
            other_res_hkx.dcx_type = dcx_type
        else:
            operator.warning(f"No Blender mesh children found for other resolution '{other_res_model_name}'.")

    try:
        hkx_entry.set_from_binary_file(hkx)
    except Exception as ex:
        raise HKXMapCollisionExportError(f"Cannot pack exported HKX '{hkx_model_name}'. Error: {ex}")

    if other_res_model_name:
        try:
            other_res_hkx_entry.set_from_binary_file(other_res_hkx)
        except Exception as ex:
            raise HKXMapCollisionExportError(f"Cannot pack exported HKX '{other_res_model_name}'. Error: {ex}")

    try:
        # Will create a `.bak` file automatically if absent.
        binder.write()
    except Exception as ex:
        raise HKXMapCollisionExportError(f"Cannot write Binder with new HKX '{hkx_model_name}'. Error: {ex}")

    if other_res_binder:
        try:
            # Will create a `.bak` file automatically if absent.
            other_res_binder.write()
        except Exception as ex:
            raise HKXMapCollisionExportError(f"Cannot write Binder with new HKX '{other_res_model_name}'. Error: {ex}")


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

        TODO: Update to use single mesh (per hi/lo).
        """
        if not bl_meshes:
            raise ValueError("No meshes given to export to HKX.")

        hkx_meshes = []  # type: list[HKX_MESH_TYPING]
        hkx_material_indices = []  # type: list[int]

        for bl_mesh in bl_meshes:

            material_index = get_bl_prop(bl_mesh, "material_index", int, default=0)
            hkx_material_indices.append(material_index)

            hkx_verts = [BL_TO_GAME_VECTOR3_LIST(vert.co) for vert in bl_mesh.data.vertices]
            hkx_faces = []
            for face in bl_mesh.data.polygons:
                if len(face.vertices) != 3:
                    raise ValueError(f"Found a non-triangular mesh face in HKX. Mesh must be triangulated first.")
                hkx_faces.append(tuple(face.vertices))

            hkx_meshes.append((hkx_verts, hkx_faces))

        hkx = MapCollisionHKX.from_meshes(
            meshes=hkx_meshes,
            hkx_name=name,
            material_indices=hkx_material_indices,
            # Bundled template HKX serves fine.
            # DCX applied by caller.
        )

        return hkx
