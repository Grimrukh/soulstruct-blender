from __future__ import annotations

__all__ = ["ExportNVM", "ExportNVMIntoBinder"]

import re
import traceback
import typing as tp
from pathlib import Path

import bpy
import bpy_types
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper
from soulstruct.containers.dcx import DCXType

from soulstruct.containers import Binder, BinderEntry
from soulstruct.darksouls1r.maps.nvm import NVM

from io_soulstruct.utilities import *
from .utilities import *


DEBUG_MESH_INDEX = None
DEBUG_VERTEX_INDICES = []
NVM_NAME_RE = re.compile(r"^([hl])(\d\d\d\d)B(\d)A(\d\d)$")  # no extensions


class ExportNVM(LoggingOperator, ExportHelper):
    """Export NVM from a selection of Blender meshes."""
    bl_idname = "export_scene.nvm"
    bl_label = "Export NVM"
    bl_description = "Export child meshes of selected Blender empty parent to a NVM collision file"

    # ExportHelper mixin class uses this
    filename_ext = ".nvm"

    filter_glob: StringProperty(
        default="*.nvm;*.nvm.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    dcx_type: EnumProperty(
        name="Compression",
        items=[
            ("Null", "None", "Export without any DCX compression"),
            ("DCX_EDGE", "DES", "Demon's Souls compression"),
            ("DCX_DFLT_10000_24_9", "DS1/DS2", "Dark Souls 1/2 compression"),
            ("DCX_DFLT_10000_44_9", "BB/DS3", "Bloodborne/Dark Souls 3 compression"),
            ("DCX_DFLT_11000_44_9", "Sekiro", "Sekiro compression (requires Oodle DLL)"),
            ("DCX_KRAK", "Elden Ring", "Elden Ring compression (requires Oodle DLL)"),
        ],
        description="Type of DCX compression to apply to exported file"
    )

    # TODO: Options to:
    #   - Detect appropriate MSB and update transform of this model instance (if unique) (low priority).

    @classmethod
    def poll(cls, context):
        """Requires selected of multiple meshes or a single empty (which should have child subpart meshes)."""
        return len(context.selected_objects) == 1 and context.selected_objects[0].type == "EMPTY"

    def execute(self, context):
        selected_objs = [obj for obj in context.selected_objects]
        if not selected_objs:
            return self.error("No Empty with child meshes selected for NVM export.")
        if len(selected_objs) > 1:
            return self.error("More than one object cannot be selected for NVM export.")

        bl_meshes = []
        nvm_name = selected_objs[0].name
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

        exporter = NVMExporter(self, context)

        try:
            nvm = exporter.export_nvm(bl_meshes, name=nvm_name)
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
    bl_description = "Export a NVM collision file into a FromSoftware Binder (BND/BHD)"

    # ImportHelper mixin class uses this
    filename_ext = ".nvmbhd"

    filter_glob: StringProperty(
        default="*.nvmbhd;*.nvmbhd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    dcx_type: EnumProperty(
        name="Compression",
        items=[
            ("Null", "None", "Export without any DCX compression"),
            ("DCX_EDGE", "DES", "Demon's Souls compression"),
            ("DCX_DFLT_10000_24_9", "DS1/DS2", "Dark Souls 1/2 compression"),
            ("DCX_DFLT_10000_44_9", "BB/DS3", "Bloodborne/Dark Souls 3 compression"),
            ("DCX_DFLT_11000_44_9", "Sekiro", "Sekiro compression (requires Oodle DLL)"),
            ("DCX_KRAK", "Elden Ring", "Elden Ring compression (requires Oodle DLL)"),
        ],
        default="DCX_DFLT_10000_24_9",
        description="Type of DCX compression to apply to exported file"
    )

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
                    "'mAA_BB_00_00', which will try to be detected from NVM name (eg 'h0500B1A12' -> 'm12_01_00_00')",
        default="{map}\\{name}.nvm.dcx",
    )

    @classmethod
    def poll(cls, context):
        """Requires selected of multiple meshes or a single empty (which should have child subpart meshes)."""
        return len(context.selected_objects) == 1 and context.selected_objects[0].type == "EMPTY"

    def execute(self, context):
        print("Executing NVM export to Binder...")

        selected_objs = [obj for obj in context.selected_objects]
        if not selected_objs:
            return self.error("No Empty with child meshes selected for NVM export.")
        if len(selected_objs) > 1:
            return self.error("More than one object cannot be selected for NVM export.")

        bl_meshes = []
        nvm_name = selected_objs[0].name
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

        exporter = NVMExporter(self, context)

        try:
            nvm = exporter.export_nvm(bl_meshes, name=nvm_name)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported NVM. Error: {ex}")
        else:
            nvm.dcx_type = DCXType[self.dcx_type]

        try:
            binder = Binder(self.filepath)
        except Exception as ex:
            return self.error(f"Could not load Binder file. Error: {ex}.")

        matching_entries = binder.find_entries_matching_name(rf"{nvm_name}\.nvm(\.dcx)?")
        if not matching_entries:
            # Create new entry.
            if "{map}" in self.default_entry_path:
                if match := NVM_NAME_RE.match(nvm_name):
                    block, area = int(match.group(3)), int(match.group(4))
                    map_str = f"m{area:02d}_{block:02d}_00_00"
                else:
                    return self.error(
                        f"Could not determine '{{map}}' for new Binder entry from NVM name: {nvm_name}. It must be in "
                        f"the format '[hl]####A#B##' for map name 'mAA_BB_00_00' to be detected."
                    )
                entry_path = self.default_entry_path.format(map=map_str, name=nvm_name)
            else:
                entry_path = self.default_entry_path.format(name=nvm_name)
            new_entry_id = binder.highest_entry_id + 1
            nvm_entry = BinderEntry(
                b"", entry_id=new_entry_id, path=entry_path, flags=self.default_entry_flags
            )
            binder.add_entry(nvm_entry)
            self.info(f"Creating new Binder entry: ID {new_entry_id}, path '{entry_path}'")
        else:
            if not self.overwrite_existing:
                return self.error(f"NVM named '{nvm_name}' already exists in Binder and overwrite is disabled.")

            if len(matching_entries) > 1:
                self.warning(
                    f"Multiple NVMs named '{nvm_name}' found in Binder. Replacing first: {matching_entries[0].name}"
                )
            else:
                self.info(f"Replacing existing Binder entry: ID {matching_entries[0]}, path '{matching_entries[0]}'")
            nvm_entry = matching_entries[0]

        nvm.dcx_type = DCXType[self.dcx_type]

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

    PROPERTIES = {
        "NVM": {
            "material_index": BlenderProp(int, 0),
        },
    }  # type: dict[str, dict[str, BlenderProp]]

    operator: bpy_types.Operator

    def __init__(self, operator: ExportNVM, context):
        self.operator = operator
        self.context = context

    def warning(self, msg: str):
        self.operator.report({"WARNING"}, msg)
        print(f"# WARNING: {msg}")

    @classmethod
    def get(cls, bl_obj, prop_class: str, bl_prop_name: str, py_prop_name: str = None):
        if py_prop_name is None:
            py_prop_name = bl_prop_name
        try:
            prop = cls.PROPERTIES[prop_class][py_prop_name]
        except KeyError:
            raise KeyError(f"Invalid Blender NVM property class/name: {prop_class}, {bl_prop_name}")

        prop_value = bl_obj.get(bl_prop_name, prop.default)

        if prop_value is None:
            raise KeyError(f"Object '{bl_obj.name}' does not have required `{prop_class}` property '{bl_prop_name}'.")
        if prop.bl_type is tuple:
            # Blender type is an `IDPropertyArray` with `typecode = 'i'` or `'d'`.
            if type(prop_value).__name__ != "IDPropertyArray":
                raise KeyError(
                    f"Object '{bl_obj.name}' property '{bl_prop_name}' does not have type `IDPropertyArray`."
                )
            if not prop.callback:
                prop_value = tuple(prop_value)  # convert `IDPropertyArray` to `tuple` by default
        elif not isinstance(prop_value, prop.bl_type):
            raise KeyError(f"Object '{bl_obj.name}' property '{bl_prop_name}' does not have type `{prop.bl_type}`.")

        if prop.callback:
            prop_value = prop.callback(prop_value)

        return prop_value

    @classmethod
    def get_all_props(cls, bl_obj, py_obj, prop_class: str, bl_prop_prefix: str = "") -> dict[str, tp.Any]:
        """Assign all class properties from Blender object `bl_obj` as attributes of Soulstruct object `py_obj`."""
        unassigned = {}
        for prop_name, prop in cls.PROPERTIES[prop_class].items():
            prop_value = cls.get(bl_obj, prop_class, bl_prop_prefix + prop_name, py_prop_name=prop_name)
            if prop.do_not_assign:
                unassigned[prop_name] = prop_value
            else:
                setattr(py_obj, prop_name, prop_value)
        return unassigned

    def export_nvm(self, bl_meshes, name: str) -> NVM:
        """Create NVM from Blender meshes (subparts)."""
        if not bl_meshes:
            raise ValueError("No meshes given to export to NVM.")

        nvm_meshes = []  # type: list[NVM_MESH_TYPING]
        nvm_material_indices = []  # type: list[int]

        for bl_mesh in bl_meshes:

            material_index = self.get(bl_mesh, "NVM", "material_index")
            nvm_material_indices.append(material_index)

            nvm_verts = [BL_TO_GAME_VECTOR_LIST(vert.co) for vert in bl_mesh.data.vertices]
            nvm_faces = []
            for face in bl_mesh.data.polygons:
                if len(face.vertices) != 3:
                    raise ValueError(f"Found a non-triangular mesh face in NVM. It must be triangulated first.")
                nvm_faces.append(tuple(face.vertices))

            nvm_meshes.append((nvm_verts, nvm_faces))

        # TODO
        nvm = NVM()

        return nvm
