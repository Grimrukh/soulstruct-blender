from __future__ import annotations

__all__ = ["ExportNVM", "ExportNVMIntoBinder"]

import traceback
from pathlib import Path

import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper
import bmesh

from soulstruct.containers import Binder, BinderEntry, DCXType
from soulstruct.darksouls1r.maps.navmesh.nvm import NVM, NVMTriangle, NVMEventEntity

from io_soulstruct.utilities import *


DEBUG_MESH_INDEX = None
DEBUG_VERTEX_INDICES = []


class ExportNVM(LoggingOperator, ExportHelper):
    """Export NVM from a Blender mesh.

    Mesh faces should be using materials named `Navmesh Flag {type}`
    """
    bl_idname = "export_scene.nvm"
    bl_label = "Export NVM"
    bl_description = "Export a Blender mesh to an NVM navmesh file"

    filename_ext = ".nvm"

    filter_glob: StringProperty(
        default="*.nvm;*.nvm.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    dcx_type: get_dcx_enum_property(DCXType.Null)  # no compression in DS1

    # TODO: Options to:
    #   - Detect appropriate MSB and update transform of this model instance (if unique) (low priority).

    @classmethod
    def poll(cls, context):
        """Requires a single selected Mesh object."""
        return len(context.selected_objects) == 1 and context.selected_objects[0].type == "MESH"

    def execute(self, context):
        selected_objs = [obj for obj in context.selected_objects]
        if not selected_objs:
            return self.error("No Empty with child meshes selected for NVM export.")
        if len(selected_objs) > 1:
            return self.error("More than one object cannot be selected for NVM export.")
        bl_mesh_obj = selected_objs[0]

        # TODO: Not needed for meshes only?
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        exporter = NVMExporter(self, context)

        try:
            nvm = exporter.export_nvm(bl_mesh_obj)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported NVM. Error: {ex}")
        else:
            nvm.dcx_type = DCXType[self.dcx_type]

        try:
            # Will create a `.bak` file automatically if absent.
            nvm.write(Path(self.filepath))
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write exported NVM. Error: {ex}")

        return {"FINISHED"}


class ExportNVMIntoBinder(LoggingOperator, ImportHelper):
    bl_idname = "export_scene.nvm_binder"
    bl_label = "Export NVM Into Binder"
    bl_description = "Export NVM navmesh files into a FromSoftware Binder (BND/BHD)"

    filename_ext = ".nvmbnd"

    filter_glob: StringProperty(
        default="*.nvmbnd;*.nvmbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    dcx_type: get_dcx_enum_property(DCXType.Null)  # no compression in DS1 binders

    overwrite_existing: BoolProperty(
        name="Overwrite Existing",
        description="Overwrite first existing '{name}.nvm{.dcx}' matching entry in Binder",
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
                    "placeholder for the name of this NVM object and {map} as a format placeholder for map string "
                    "'mAA_BB_00_00', which will try to be detected from NVM name (eg 'n0500B1A12' -> 'm12_01_00_00')",
        default="{map}\\{name}.nvm.dcx",
    )

    @classmethod
    def poll(cls, context):
        """Requires one or more selected Mesh objects."""
        return len(context.selected_objects) >= 1 and all(obj.type == "MESH" for obj in context.selected_objects)

    def execute(self, context):
        print("Executing NVM export to Binder...")

        selected_objs = [obj for obj in context.selected_objects]
        if not selected_objs:
            return self.error("No Meshes selected for NVM export.")

        try:
            binder = Binder.from_path(self.filepath)
        except Exception as ex:
            return self.error(f"Could not load Binder file. Error: {ex}.")
        binder_stem = binder.path.name.split(".")[0]

        # TODO: Not needed for meshes only?
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        exporter = NVMExporter(self, context)

        for bl_mesh_obj in selected_objs:
            model_file_stem = bl_mesh_obj.get("model_file_stem", bl_mesh_obj.name)

            try:
                nvm = exporter.export_nvm(bl_mesh_obj)
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Cannot get exported NVM. Error: {ex}")
            else:
                nvm.dcx_type = DCXType[self.dcx_type]  # most likely `Null` for file in `nvmbnd` Binder

            matching_entries = binder.find_entries_matching_name(rf"{model_file_stem}\.nvm(\.dcx)?")
            if not matching_entries:
                # Create new entry.
                if "{map}" in self.default_entry_path:
                    if MAP_STEM_RE.match(binder_stem):
                        map_str = binder_stem
                    else:
                        return self.error(
                            f"Could not determine '{{map}}' for new Binder entry from Binder stem: {binder_stem}. "
                            f"You must replace the '{{map}}' template in the Default Entry Path with a known map stem."
                        )
                    entry_path = self.default_entry_path.format(map=map_str, name=model_file_stem)
                else:
                    entry_path = self.default_entry_path.format(name=model_file_stem)
                new_entry_id = binder.highest_entry_id + 1
                nvm_entry = BinderEntry(
                    b"", entry_id=new_entry_id, path=entry_path, flags=self.default_entry_flags
                )
                binder.add_entry(nvm_entry)
                self.info(f"Creating new Binder entry: ID {new_entry_id}, path '{entry_path}'")
            else:
                if not self.overwrite_existing:
                    return self.error(f"NVM named '{model_file_stem}' already exists in Binder and overwrite = False.")

                nvm_entry = matching_entries[0]

                if len(matching_entries) > 1:
                    self.warning(
                        f"Multiple NVMs with stem '{model_file_stem}' found in Binder. "
                        f"Replacing first: {nvm_entry.name}"
                    )
                else:
                    self.info(
                        f"Replacing existing Binder entry: ID {nvm_entry.entry_id}, path '{nvm_entry.path}'"
                    )

            try:
                nvm_entry.set_from_binary_file(nvm)
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Cannot write exported NVM. Error: {ex}")

        try:
            # Will create a `.bak` file automatically if absent.
            binder.write()
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write Binder with new NVM. Error: {ex}")

        return {"FINISHED"}


class NVMExporter:

    operator: LoggingOperator

    def __init__(self, operator: LoggingOperator, context):
        self.operator = operator
        self.context = context

    def warning(self, msg: str):
        self.operator.report({"WARNING"}, msg)
        print(f"# WARNING: {msg}")

    def export_nvm(self, bl_mesh_obj) -> NVM:
        """Create NVM from Blender meshes (subparts).

        This is much simpler than FLVER or HKX map collision mesh export. Note that the navmesh name is not needed, as
        it appears nowhere in the NVM binary file.
        """
        nvm_verts = [BL_TO_GAME_VECTOR3_LIST(vert.co) for vert in bl_mesh_obj.data.vertices]  # type: list[list[float]]
        nvm_faces = []  # type: list[tuple[int, int, int]]
        for face in bl_mesh_obj.data.polygons:
            if len(face.vertices) != 3:
                raise ValueError(f"Found a non-triangular mesh face in NVM. It must be triangulated first.")
            nvm_faces.append(tuple(face.vertices))

        def find_connected_face_index(edge_v1: int, edge_v2: int, not_face) -> int:
            """Find face that shares an edge with the given edge.

            Returns -1 if no connected face is found (i.e. edge is on the edge of the mesh).
            """
            # TODO: Could surely iterate over faces just once for this?
            for i_, f_ in enumerate(nvm_faces):
                if f_ != not_face and edge_v1 in f_ and edge_v2 in f_:  # order doesn't matter
                    return i_
            return -1

        # Get connected faces along each edge of each face.
        nvm_connected_face_indices = []  # type: list[tuple[int, int, int]]
        for face in nvm_faces:
            connected_v1 = find_connected_face_index(face[0], face[1], face)
            connected_v2 = find_connected_face_index(face[1], face[2], face)
            connected_v3 = find_connected_face_index(face[2], face[0], face)
            nvm_connected_face_indices.append((connected_v1, connected_v2, connected_v3))
            if connected_v1 == -1 and connected_v2 == -1 and connected_v3 == -1:
                self.warning(f"NVM face {face} appears to have no connected faces, which is very suspicious!")

        # Create `BMesh` to access custom face layers for `flags` and `obstacle_count`.
        bm = bmesh.new()
        bm.from_mesh(bl_mesh_obj.data)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        flags_layer = bm.faces.layers.int.get("nvm_face_flags")
        if not flags_layer:
            raise ValueError("NVM mesh does not have 'nvm_face_flags' custom face layer.")
        obstacle_count_layer = bm.faces.layers.int.get("nvm_face_obstacle_count")
        if not obstacle_count_layer:
            raise ValueError("NVM mesh does not have 'nvm_face_obstacle_count' custom face layer.")

        nvm_flags = []
        nvm_obstacle_counts = []
        for bm_face in bm.faces:
            nvm_flags.append(bm_face[flags_layer])
            nvm_obstacle_counts.append(bm_face[obstacle_count_layer])
        if len(nvm_flags) != len(nvm_faces):
            raise ValueError("NVM mesh has different number of `Mesh` faces and `BMesh` face flags.")

        nvm_triangles = [
            NVMTriangle(
                vertex_indices=nvm_faces[i],
                connected_indices=nvm_connected_face_indices[i],
                obstacle_count=nvm_obstacle_counts[i],
                flags=nvm_flags[i],
            )
            for i in range(len(nvm_faces))
        ]

        event_entities = []
        event_prefix = f"{bl_mesh_obj.name} Event "
        for child in bl_mesh_obj.children:
            if child.name.startswith(event_prefix):
                try:
                    entity_id = child["entity_id"]
                except KeyError:
                    self.warning(f"Event entity '{child.name}' does not have 'entity_id' custom property. Ignoring.")
                    continue
                try:
                    triangle_indices = child["triangle_indices"]
                except KeyError:
                    self.warning(f"Event entity '{child.name}' does not have 'triangle_indices' custom property. "
                                 f"Ignoring.")
                    continue
                event_entities.append(NVMEventEntity(entity_id=entity_id, triangle_indices=list(triangle_indices)))

        nvm = NVM(
            big_endian=False,
            vertices=nvm_verts,
            triangles=nvm_triangles,
            event_entities=event_entities,
            # quadtree boxes generated automatically
        )

        return nvm
