from __future__ import annotations

__all__ = ["ExportHKXMapCollision", "ExportHKXMapCollisionIntoBinder"]

import re
import traceback
from pathlib import Path

import bpy
import bpy_types
from bpy.props import StringProperty, BoolProperty, IntProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper
from soulstruct.containers.dcx import DCXType

from soulstruct.containers import Binder, BinderEntry

from soulstruct_havok.wrappers.hkx2015 import MapCollisionHKX

from io_soulstruct.utilities import *
from .utilities import *


DEBUG_MESH_INDEX = None
DEBUG_VERTEX_INDICES = []
HKX_COLLISION_NAME_RE = re.compile(r"^([hl])(\d\d\d\d)B(\d)A(\d\d)$")  # no extensions


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

    # TODO: Options to:
    #   - Detect appropriate MSB and update transform of this model instance (if unique) (low priority).

    @classmethod
    def poll(cls, context):
        """Requires selected of multiple meshes or a single empty (which should have child subpart meshes)."""
        return len(context.selected_objects) == 1 and context.selected_objects[0].type == "EMPTY"

    def execute(self, context):
        selected_objs = [obj for obj in context.selected_objects]
        if not selected_objs:
            return self.error("No Empty with child meshes selected for HKX export.")
        if len(selected_objs) > 1:
            return self.error("More than one object cannot be selected for HKX export.")

        bl_meshes = []
        hkx_name = selected_objs[0].name
        children = [obj for obj in bpy.data.objects if obj.parent is selected_objs[0]]
        for child in children:
            if child.type != "MESH":
                return self.error(f"Ignoring non-mesh child '{child.name}' of selected Empty parent.")
            else:
                bl_meshes.append(child)

        bl_meshes.sort(key=lambda obj: natural_keys(obj.name))

        # TODO: Not needed for meshes only?
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        exporter = HKXMapCollisionExporter(self, context)

        try:
            hkx = exporter.export_hkx_map_collision(bl_meshes, name=hkx_name)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported HKX. Error: {ex}")
        else:
            hkx.dcx_type = DCXType[self.dcx_type]
            try:
                # Will create a `.bak` file automatically if absent.
                hkx.write(Path(self.filepath))
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Cannot write exported HKX. Error: {ex}")

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
        default="{map}\\{name}.hkx.dcx",
    )

    @classmethod
    def poll(cls, context):
        """Requires selected of multiple meshes or a single empty (which should have child subpart meshes)."""
        return len(context.selected_objects) == 1 and context.selected_objects[0].type == "EMPTY"

    def execute(self, context):
        print("Executing HKX export to Binder...")

        selected_objs = [obj for obj in context.selected_objects]
        if not selected_objs:
            return self.error("No Empty with child meshes selected for HKX export.")
        if len(selected_objs) > 1:
            return self.error("More than one object cannot be selected for HKX export.")

        bl_meshes = []
        hkx_name = selected_objs[0].name
        children = [obj for obj in bpy.data.objects if obj.parent is selected_objs[0]]
        for child in children:
            if child.type != "MESH":
                return self.error(f"Ignoring non-mesh child '{child.name}' of selected Empty parent.")
            else:
                bl_meshes.append(child)

        bl_meshes.sort(key=lambda obj: natural_keys(obj.name))

        # TODO: Not needed for meshes only?
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        exporter = HKXMapCollisionExporter(self, context)

        try:
            hkx = exporter.export_hkx_map_collision(bl_meshes, name=hkx_name)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported HKX. Error: {ex}")
        else:
            hkx.dcx_type = DCXType[self.dcx_type]

        try:
            binder = Binder.from_path(self.filepath)
        except Exception as ex:
            return self.error(f"Could not load Binder file. Error: {ex}.")

        matching_entries = binder.find_entries_matching_name(rf"{hkx_name}\.hkx(\.dcx)?")
        if not matching_entries:
            # Create new entry.
            if "{map}" in self.default_entry_path:
                if match := HKX_COLLISION_NAME_RE.match(hkx_name):
                    block, area = int(match.group(3)), int(match.group(4))
                    map_str = f"m{area:02d}_{block:02d}_00_00"
                else:
                    return self.error(
                        f"Could not determine '{{map}}' for new Binder entry from HKX name: {hkx_name}. It must be in "
                        f"the format '[hl]####A#B##' for map name 'mAA_BB_00_00' to be detected."
                    )
                entry_path = self.default_entry_path.format(map=map_str, name=hkx_name)
            else:
                entry_path = self.default_entry_path.format(name=hkx_name)
            new_entry_id = binder.highest_entry_id + 1
            hkx_entry = BinderEntry(
                b"", entry_id=new_entry_id, path=entry_path, flags=self.default_entry_flags
            )
            binder.add_entry(hkx_entry)
            self.info(f"Creating new Binder entry: ID {new_entry_id}, path '{entry_path}'")
        else:
            if not self.overwrite_existing:
                return self.error(f"HKX named '{hkx_name}' already exists in Binder and overwrite is disabled.")

            if len(matching_entries) > 1:
                self.warning(
                    f"Multiple HKXs named '{hkx_name}' found in Binder. Replacing first: {matching_entries[0].name}"
                )
            else:
                self.info(f"Replacing existing Binder entry: ID {matching_entries[0]}, path '{matching_entries[0]}'")
            hkx_entry = matching_entries[0]

        hkx.dcx_type = DCXType[self.dcx_type]

        try:
            hkx_entry.set_from_binary_file(hkx)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write exported HKX. Error: {ex}")

        try:
            # Will create a `.bak` file automatically if absent.
            binder.write()
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write Binder with new HKX. Error: {ex}")

        return {"FINISHED"}


class HKXMapCollisionExporter:

    props: BlenderPropertyManager
    operator: bpy_types.Operator

    def __init__(self, operator: ExportHKXMapCollision, context):
        self.operator = operator
        self.context = context
        self.props = BlenderPropertyManager({
            "HKX": {"material_index": BlenderProp(int, 0)},
        })

    def warning(self, msg: str):
        self.operator.report({"WARNING"}, msg)
        print(f"# WARNING: {msg}")

    def export_hkx_map_collision(self, bl_meshes, name: str) -> MapCollisionHKX:
        """Create HKX from Blender meshes (subparts).

        TODO: Currently only supported for DSR and Havok 2015.
        """
        if not bl_meshes:
            raise ValueError("No meshes given to export to HKX.")

        hkx_meshes = []  # type: list[HKX_MESH_TYPING]
        hkx_material_indices = []  # type: list[int]

        for bl_mesh in bl_meshes:

            material_index = self.props.get(bl_mesh, "HKX", "material_index")
            hkx_material_indices.append(material_index)

            hkx_verts = [BL_TO_GAME_VECTOR_LIST(vert.co) for vert in bl_mesh.data.vertices]
            hkx_faces = []
            for face in bl_mesh.data.polygons:
                if len(face.vertices) != 3:
                    raise ValueError(f"Found a non-triangular mesh face in HKX. It must be triangulated first.")
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
