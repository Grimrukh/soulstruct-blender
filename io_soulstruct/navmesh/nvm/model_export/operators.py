from __future__ import annotations

__all__ = [
    "ExportLooseNVM",
    "ExportNVMIntoBinder",
    "ExportNVMIntoNVMBND",
]

import traceback
from pathlib import Path

import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper

from soulstruct.containers import Binder, BinderEntry
from soulstruct.dcx import DCXType
from soulstruct.darksouls1r.maps.navmesh import NVMBND

from io_soulstruct.utilities.operators import LoggingOperator, get_dcx_enum_property
from io_soulstruct.utilities.misc import *
from .core import *


class ExportLooseNVM(LoggingOperator, ExportHelper):
    """Export loose NVM file from a Blender mesh.

    Mesh faces should be using materials named `Navmesh Flag {type}`
    """
    bl_idname = "export_scene.nvm"
    bl_label = "Export Loose NVM"
    bl_description = "Export a Blender mesh to an NVM navmesh file"

    filename_ext = ".nvm"

    filter_glob: StringProperty(
        default="*.nvm;*.nvm.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    dcx_type: get_dcx_enum_property(DCXType.Null)  # no compression in DS1

    @classmethod
    def poll(cls, context):
        """Requires a single selected Mesh object."""
        return len(context.selected_objects) == 1 and context.selected_objects[0].type == "MESH"

    def invoke(self, context, _event):
        """Set default export name to name of object (before first space and without Blender dupe suffix)."""
        if not context.selected_objects:
            return super().invoke(context, _event)

        obj = context.selected_objects[0]
        model_name = find_model_name(self, obj, warn_property_mismatch=False)
        settings = self.settings(context)
        self.filepath = settings.game.process_dcx_path(f"{model_name}.nvm")
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not self.poll(context):
            return self.error("No valid Mesh selected for NVM export.")

        # noinspection PyTypeChecker
        nvm_model = context.selected_objects[0]  # type: bpy.types.MeshObject

        try:
            nvm = export_nvm_model(self, nvm_model)
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
        if not self.poll(context):
            return self.error("No valid Meshes selected for NVM export.")

        # noinspection PyTypeChecker
        selected_objs = [obj for obj in context.selected_objects]  # type: list[bpy.types.MeshObject]

        try:
            binder = Binder.from_path(self.filepath)
        except Exception as ex:
            return self.error(f"Could not load Binder file. Error: {ex}.")
        binder_stem = binder.path.name.split(".")[0]

        # TODO: Not needed for meshes only?
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        for nvm_model in selected_objs:
            model_name = find_model_name(self, nvm_model, warn_property_mismatch=False)  # can't auto-detect map

            try:
                nvm = export_nvm_model(self, nvm_model)
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Cannot get exported NVM. Error: {ex}")
            else:
                nvm.dcx_type = DCXType[self.dcx_type]  # most likely `Null` for file in `nvmbnd` Binder

            matching_entries = binder.find_entries_matching_name(rf"{model_name}\.nvm(\.dcx)?")
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
                    entry_path = self.default_entry_path.format(map=map_str, name=model_name)
                else:
                    entry_path = self.default_entry_path.format(name=model_name)
                new_entry_id = binder.highest_entry_id + 1
                nvm_entry = BinderEntry(
                    b"", entry_id=new_entry_id, path=entry_path, flags=self.default_entry_flags
                )
                binder.add_entry(nvm_entry)
                self.info(f"Creating new Binder entry: ID {new_entry_id}, path '{entry_path}'")
            else:
                if not self.overwrite_existing:
                    return self.error(f"NVM named '{model_name}' already exists in Binder and overwrite = False.")

                nvm_entry = matching_entries[0]

                if len(matching_entries) > 1:
                    self.warning(
                        f"Multiple NVMs with stem '{model_name}' found in Binder. "
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


class ExportNVMIntoNVMBND(LoggingOperator):

    bl_idname = "export_scene.nvm_entry"
    bl_label = "Export NVM"
    bl_description = "Export selected meshes as NVM navmeshes into selected game map NVMBND"

    # Always overwrites existing NVM entries.

    @classmethod
    def poll(cls, context):
        """One or more 'n*' Meshes selected."""
        return (
            cls.settings(context).game_variable_name == "DARK_SOULS_DSR"
            and len(context.selected_objects) > 0
            and all(obj.type == "MESH" and obj.name[0] == "n" for obj in context.selected_objects)
        )

    def execute(self, context):
        if not self.poll(context):
            return self.error("No valid 'n' meshes selected for quick NVM export.")

        settings = self.settings(context)
        settings.save_settings()
        if settings.game_variable_name != "DARK_SOULS_DSR":
            return self.error("Quick NVM export is only supported for Dark Souls: Remastered.")

        if not settings.map_stem and not settings.detect_map_from_collection:
            return self.error(
                "No game map directory specified in Soulstruct settings and `Detect Map from Collection` is disabled."
            )

        # TODO: Not needed for meshes only?
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        opened_nvmbnds = {}  # type: dict[Path, NVMBND]
        for nvm_model in context.selected_objects:
            nvm_model: bpy.types.MeshObject

            # NVMBND files come from latest 'map' folder version.
            map_stem = settings.get_map_stem_for_export(nvm_model, latest=True)
            relative_nvmbnd_path = Path(f"map/{map_stem}/{map_stem}.nvmbnd")

            if relative_nvmbnd_path not in opened_nvmbnds:
                try:
                    nvmbnd_path = settings.prepare_project_file(relative_nvmbnd_path, False, must_exist=True)
                except FileNotFoundError as ex:
                    self.error(f"Cannot find NVMBND: {relative_nvmbnd_path}. Error: {ex}")
                    continue
                try:
                    nvmbnd = opened_nvmbnds[relative_nvmbnd_path] = NVMBND.from_path(nvmbnd_path)
                except Exception as ex:
                    self.error(f"Could not load NVMBND for map '{map_stem}'. Error: {ex}")
                    continue
            else:
                nvmbnd = opened_nvmbnds[relative_nvmbnd_path]

            model_name = find_model_name(self, nvm_model, process_model_name_map_area(map_stem))

            try:
                nvm = export_nvm_model(self, nvm_model)
            except Exception as ex:
                traceback.print_exc()
                self.error(f"Cannot get exported NVM. Error: {ex}")
                continue
            else:
                nvm.dcx_type = DCXType.Null  # no DCX compression inside NVMBND

            nvmbnd.nvms[model_name] = nvm  # no extension needed

        for relative_nvmbnd_path, nvmbnd in opened_nvmbnds.items():
            nvmbnd.entries = list(sorted(nvmbnd.entries, key=lambda e: e.name))
            for i, entry in enumerate(nvmbnd.entries):
                entry.entry_id = i
            settings.export_file(self, nvmbnd, relative_nvmbnd_path)

        return {"FINISHED"}
