from __future__ import annotations

__all__ = [
    "ExportAnyNVM",
    "ExportNVMIntoAnyBinder",
    "ExportMapNVM",
]

import traceback
from pathlib import Path

import bpy

from soulstruct.base.maps.navmesh import NVM, BaseNVMBND
from soulstruct.containers import Binder, BinderEntry
from soulstruct.dcx import DCXType
from soulstruct.darksouls1r.maps.navmesh import NVMBND as NVMBND_DSR
from soulstruct.darksouls1ptde.maps.navmesh import NVMBND as NVMBND_PTDE
from soulstruct.demonssouls.maps.navmesh import NVMBND as NVMBND_DES
from soulstruct.games import DARK_SOULS_PTDE, DARK_SOULS_DSR, DEMONS_SOULS

from io_soulstruct.exceptions import SoulstructTypeError
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities.operators import *
from io_soulstruct.utilities.misc import *
from .types import *


class ExportAnyNVM(LoggingExportOperator):
    """Export loose NVM file from a Blender mesh.

    Mesh faces should be using materials named `Navmesh Flag {type}`
    """
    bl_idname = "export_scene.nvm"
    bl_label = "Export Loose NVM"
    bl_description = "Export a Blender mesh to an NVM navmesh file"

    filename_ext = ".nvm"

    filter_glob: bpy.props.StringProperty(
        default="*.nvm;*.nvm.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    dcx_type: get_dcx_enum_property(DCXType.Null)  # no compression in DS1

    @classmethod
    def poll(cls, context) -> bool:
        return context.active_object and context.active_object.soulstruct_type == SoulstructType.NAVMESH

    def invoke(self, context, _event):
        """Set default export name to name of object (before first space and without Blender dupe suffix)."""
        if not context.active_object:
            return super().invoke(context, _event)

        obj = context.active_object
        model_stem = obj.name.split(".")[0].split(" ")[0]
        settings = self.settings(context)
        self.filepath = settings.game.process_dcx_path(f"{model_stem}.nvm")
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if not self.poll(context):
            return self.error("No valid Mesh selected for NVM export.")

        # noinspection PyTypeChecker
        nvm_model = context.selected_objects[0]  # type: bpy.types.MeshObject

        try:
            nvm = BlenderNVM(nvm_model).to_soulstruct_obj(self, context)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported NVM. Error: {ex}")
        else:
            nvm.dcx_type = DCXType.from_member_name(self.dcx_type)

        try:
            # Will create a `.bak` file automatically if absent.
            nvm.write(Path(self.filepath))
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write exported NVM. Error: {ex}")

        return {"FINISHED"}


class ExportNVMIntoAnyBinder(LoggingImportOperator):
    bl_idname = "export_scene.nvm_binder"
    bl_label = "Export NVM Into Binder"
    bl_description = "Export NVM navmesh files into a FromSoftware Binder (BND/BHD)"

    filter_glob: bpy.props.StringProperty(
        default="*.nvmbnd;*.nvmbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    dcx_type: get_dcx_enum_property(DCXType.Null)  # no compression in DS1 binders

    overwrite_existing: bpy.props.BoolProperty(
        name="Overwrite Existing",
        description="Overwrite first existing '{name}.nvm{.dcx}' matching entry in Binder",
        default=True,
    )

    default_entry_flags: bpy.props.IntProperty(
        name="Default Flags",
        description="Flags to set to Binder entry if it needs to be created",
        default=0x2,
    )

    default_entry_path: bpy.props.StringProperty(
        name="Default Path",
        description="Path prefix to use for Binder entry if it needs to be created. Use {name} as a format "
                    "placeholder for the name of this NVM object and {map} as a format placeholder for map string "
                    "'mAA_BB_00_00', which will try to be detected from NVM name (eg 'n0500B1A12' -> 'm12_01_00_00')",
        default="{map}\\{name}.nvm.dcx",
    )

    @classmethod
    def poll(cls, context) -> bool:
        """Requires one or more selected Mesh objects."""
        return (
            len(context.selected_objects) >= 1
            and all(obj.soulstruct_type == SoulstructType.NAVMESH for obj in context.selected_objects)
        )

    def execute(self, context):
        if not self.poll(context):
            return self.error("No valid Meshes selected for NVM export.")

        selected_bl_nvms = BlenderNVM.from_selected_objects(context, sort=True)  # type: list[BlenderNVM]

        try:
            binder = Binder.from_path(self.filepath)
        except Exception as ex:
            return self.error(f"Could not load Binder file. Error: {ex}.")
        binder_stem = binder.path.name.split(".")[0]

        for bl_nvm in selected_bl_nvms:
            model_stem = bl_nvm.game_name

            try:
                nvm = bl_nvm.to_soulstruct_obj(self, context)
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Cannot get exported NVM. Error: {ex}")
            else:
                nvm.dcx_type = DCXType.from_member_name(self.dcx_type)  # most likely `Null` for file in `nvmbnd` Binder

            matching_entries = binder.find_entries_matching_name(rf"{model_stem}\.nvm(\.dcx)?")
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
                    entry_path = self.default_entry_path.format(map=map_str, name=model_stem)
                else:
                    entry_path = self.default_entry_path.format(name=model_stem)
                new_entry_id = binder.highest_entry_id + 1
                nvm_entry = BinderEntry(
                    b"", entry_id=new_entry_id, path=entry_path, flags=self.default_entry_flags
                )
                binder.add_entry(nvm_entry)
                self.info(f"Creating new Binder entry: ID {new_entry_id}, path '{entry_path}'")
            else:
                if not self.overwrite_existing:
                    return self.error(f"NVM named '{model_stem}' already exists in Binder and overwrite = False.")

                nvm_entry = matching_entries[0]

                if len(matching_entries) > 1:
                    self.warning(
                        f"Multiple NVMs with stem '{model_stem}' found in Binder. "
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


class ExportMapNVM(LoggingOperator):

    bl_idname = "export_scene.nvm_selected_map"
    bl_label = "Export NVM"
    bl_description = "Export selected meshes as NVM navmeshes into selected map NVMBND"

    # Always overwrites existing NVM entries.

    @classmethod
    def poll(cls, context) -> bool:
        """One or more 'n*' Meshes selected."""
        settings = cls.settings(context)
        if not settings.game_config.supports_nvm:
            return False
        # Map stem may be unselected if detected from collision.
        try:
            BlenderNVM.from_selected_objects(context)
        except SoulstructTypeError:
            return False
        return True  # at least one valid NVM selected

    def execute(self, context):
        if not self.poll(context):
            return self.error("No valid 'n' meshes selected for NVM export (or game does not support NVM export).")

        settings = self.settings(context)

        if not settings.map_stem and not settings.auto_detect_export_map:
            return self.error(
                "No game map directory specified in Soulstruct settings and `Detect Map from Collection` is disabled."
            )

        if settings.is_game(DARK_SOULS_PTDE):
            nvmbnd_class = NVMBND_PTDE
        elif settings.is_game(DARK_SOULS_DSR):
            nvmbnd_class = NVMBND_DSR
        elif settings.is_game(DEMONS_SOULS):
            nvmbnd_class = NVMBND_DES
        else:
            return self.error(f"Unsupported game: {settings.game}")

        opened_nvmbnds = {}  # type: dict[Path, BaseNVMBND]
        bl_nvms = BlenderNVM.from_selected_objects(context, sort=True)  # type: list[BlenderNVM]

        export_loose_des_nvms = settings.is_game(DEMONS_SOULS) and settings.des_export_debug_files
        loose_nvms_to_export = []  # type: list[tuple[NVM, Path]]

        for bl_nvm in bl_nvms:
            # NVMBND files come from latest 'map' folder version.
            map_stem = settings.get_map_stem_for_export(bl_nvm.obj, latest=True)
            relative_nvmbnd_path = Path(f"map/{map_stem}/{map_stem}.nvmbnd")

            if relative_nvmbnd_path not in opened_nvmbnds:
                # Open new NVMBND. We start with the game NVMBND unless `Prefer Import from Project` is enabled.
                try:
                    # We never overwrite existing project NVMBNDs as they may contain other custom NVMs.
                    nvmbnd = settings.get_initial_binder(self, relative_nvmbnd_path, nvmbnd_class)
                except Exception as ex:
                    self.error(f"Cannot find/open NVMBND: {relative_nvmbnd_path}. Error: {ex}")
                    continue
                opened_nvmbnds[relative_nvmbnd_path] = nvmbnd
            else:
                nvmbnd = opened_nvmbnds[relative_nvmbnd_path]

            model_stem = bl_nvm.game_name

            try:
                nvm = bl_nvm.to_soulstruct_obj(self, context)
            except Exception as ex:
                traceback.print_exc()
                self.error(f"Cannot get exported NVM. Error: {ex}")
                continue
            else:
                nvm.dcx_type = DCXType.Null  # no DCX compression inside NVMBND

            nvmbnd.set_nvm(model_stem, nvm)  # no extension needed

            if export_loose_des_nvms:
                # Note that the loose debug NVMs always have lower-case model stems.
                loose_nvms_to_export.append((nvm, Path(f"map/{map_stem}/{model_stem.lower()}.nvm")))

        exported_paths = []
        for relative_nvmbnd_path, nvmbnd in opened_nvmbnds.items():
            nvmbnd.entries = list(sorted(nvmbnd.entries, key=lambda e: e.name))
            for i, entry in enumerate(nvmbnd.entries):
                entry.entry_id = i
            exported_paths += settings.export_file(self, nvmbnd, relative_nvmbnd_path)

        if settings.is_game(DEMONS_SOULS) and settings.des_export_debug_files and loose_nvms_to_export:
            # Export loose NVMs next to NVMBND.
            for nvm, relative_nvm_path in loose_nvms_to_export:
                exported_paths += settings.export_file(self, nvm, relative_nvm_path)

        return {"FINISHED" if exported_paths else "CANCELLED"}
