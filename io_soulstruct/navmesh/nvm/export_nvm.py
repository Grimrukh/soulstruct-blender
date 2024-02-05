from __future__ import annotations

__all__ = [
    "ExportLooseNVM",
    "ExportNVMIntoBinder",
    "ExportNVMIntoNVMBND",
    "ExportNVMMSBPart",
    "ExportAllNVMMSBParts",
]

import traceback
from pathlib import Path

import numpy as np
import typing as tp

import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper
import bmesh

from soulstruct.containers import Binder, BinderEntry
from soulstruct.dcx import DCXType
from soulstruct.base.maps.msb.utils import GroupBitSet128
from soulstruct.darksouls1r.maps.navmesh.nvm import NVM, NVMTriangle, NVMEventEntity
from soulstruct.darksouls1r.maps.navmesh.nvmbnd import NVMBND
from soulstruct.darksouls1r.maps.models import MSBNavmeshModel
from soulstruct.darksouls1r.maps.parts import MSBNavmesh

from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.utilities.operators import LoggingOperator, get_dcx_enum_property
from io_soulstruct.utilities.misc import MAP_STEM_RE, get_bl_obj_stem, natural_keys
from io_soulstruct.utilities.conversion import BlenderTransform

if tp.TYPE_CHECKING:
    from io_soulstruct.type_checking import MSB_TYPING


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
        if obj.get("Model File Stem", None) is not None:
            self.filepath = obj["Model File Stem"] + ".nvm"
        self.filepath = obj.name.split(" ")[0].split(".")[0] + ".nvm"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not self.poll(context):
            return self.error("No valid Mesh selected for NVM export.")

        # noinspection PyTypeChecker
        bl_mesh_obj = context.selected_objects[0]  # type: bpy.types.MeshObject

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

        exporter = NVMExporter(self, context)

        for bl_mesh_obj in selected_objs:
            model_file_stem = bl_mesh_obj.get("Model File Stem", bl_mesh_obj.name)

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

        if not settings.map_stem and not settings.detect_map_from_parent:
            return self.error(
                "No game map directory specified in Soulstruct settings and `Detect Map from Parent` is disabled."
            )
        default_map_path = Path(f"map/{settings.get_latest_map_stem_version()}") if settings.map_stem else None

        # TODO: Not needed for meshes only?
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        exporter = NVMExporter(self, context)

        opened_nvmbnds = {}  # type: dict[Path, Binder]
        for bl_mesh_obj in context.selected_objects:

            bl_mesh_obj: bpy.types.MeshObject

            if settings.detect_map_from_parent:
                if bl_mesh_obj.parent is None:
                    return self.error(
                        f"Object '{bl_mesh_obj.name}' has no parent. Deselect 'Detect Map from Parent' to use single "
                        f"game map specified in Soulstruct plugin settings."
                    )
                map_stem = bl_mesh_obj.parent.name.split(" ")[0]
                if not MAP_STEM_RE.match(map_stem):
                    return self.error(
                        f"Parent object '{bl_mesh_obj.parent.name}' does not start with a valid map stem."
                    )
                # NVMBND files come from latest 'map' version.
                map_stem = settings.get_latest_map_stem_version(map_stem)
                relative_nvmbnd_path = Path(f"map/{map_stem}/{map_stem}.nvmbnd")
            else:
                map_stem = settings.get_latest_map_stem_version()
                relative_nvmbnd_path = default_map_path / f"{map_stem}.nvmbnd"

            if relative_nvmbnd_path not in opened_nvmbnds:
                try:
                    nvmbnd_path = settings.prepare_project_file(relative_nvmbnd_path, False, must_exist=True)
                except FileNotFoundError as ex:
                    return self.error(f"Cannot find NVMBND: {relative_nvmbnd_path}. Error: {ex}")
                try:
                    nvmbnd = opened_nvmbnds[relative_nvmbnd_path] = Binder.from_path(nvmbnd_path)
                except Exception as ex:
                    self.error(f"Could not load NVMBND for map '{map_stem}'. Error: {ex}")
                    continue
            else:
                nvmbnd = opened_nvmbnds[relative_nvmbnd_path]

            model_file_stem = bl_mesh_obj.get("Model File Stem", get_bl_obj_stem(bl_mesh_obj))

            try:
                nvm = exporter.export_nvm(bl_mesh_obj)
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Cannot get exported NVM. Error: {ex}")
            else:
                nvm.dcx_type = DCXType.Null  # no DCX compression inside NVMBND

            nvm_entry_name = f"{model_file_stem}.nvm"
            nvmbnd.set_default_entry(
                nvm_entry_name,
                new_id=nvmbnd.highest_entry_id + 1,
                new_path=f"{map_stem}\\{nvm_entry_name}",
                new_flags=0x2,
            ).set_from_binary_file(nvm)

        for relative_nvmbnd_path, nvmbnd in opened_nvmbnds.items():
            nvmbnd.entries = list(sorted(nvmbnd.entries, key=lambda e: e.name))
            for i, entry in enumerate(nvmbnd.entries):
                entry.entry_id = i
            settings.export_file(self, nvmbnd, relative_nvmbnd_path)

        return {"FINISHED"}


class ExportNVMMSBPart(LoggingOperator):

    bl_idname = "export_scene.msb_nvm"
    bl_label = "Export Navmesh Part"
    bl_description = "Export transform and mesh of selected NVM navmeshes into selected game map MSB/NVMBND"

    # Always overwrites existing NVM parts and NVMBND entries.

    # TODO: Can't disable, but leaving here for now.
    prefer_new_model_file_stem: BoolProperty(
        name="Prefer New Model File Stem",
        description="Use the 'Model File Stem' property on the Blender mesh parent to update the model file stem in "
                    "the MSB and determine the NVM entry stem to write. If disabled, the MSB model name will be used.",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        """One or more 'n*' Meshes selected."""
        return (
            cls.settings(context).game_variable_name == "DARK_SOULS_DSR"
            and len(context.selected_objects) > 0
            and all(obj.type == "MESH" and obj.name[0] == "n" for obj in context.selected_objects)
        )

    def execute(self, context):
        settings = self.settings(context)
        if settings.game_variable_name != "DARK_SOULS_DSR":
            return self.error("Quick MSB Navmesh export is only supported for Dark Souls: Remastered.")

        if not self.poll(context):
            return self.error("No valid 'n' meshes selected for quick NVM export.")

        if not settings.map_stem and not settings.detect_map_from_parent:
            return self.error(
                "No game map directory specified in Soulstruct settings and `Detect Map from Parent` is disabled."
            )
        default_map_path = Path(f"map/{settings.get_latest_map_stem_version()}") if settings.map_stem else None

        # TODO: Not needed for meshes only?
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        exporter = NVMExporter(self, context)

        opened_nvmbnds = {}  # type: dict[str, Binder]
        opened_msbs = {}  # type: dict[Path, MSB_TYPING]
        edited_part_names = {}  # type: dict[str, set[str]]

        for bl_mesh_obj in context.selected_objects:

            bl_mesh_obj: bpy.types.MeshObject

            if settings.detect_map_from_parent:
                if bl_mesh_obj.parent is None:
                    return self.error(
                        f"Object '{bl_mesh_obj.name}' has no parent. Deselect 'Detect Map from Parent' to use single "
                        f"game map specified in Soulstruct plugin settings."
                    )
                map_stem = bl_mesh_obj.parent.name.split(" ")[0]
                if not MAP_STEM_RE.match(map_stem):
                    return self.error(
                        f"Parent object '{bl_mesh_obj.parent.name}' does not start with a valid map stem."
                    )
                # NVMBND files come from latest 'map' version.
                map_stem = settings.get_latest_map_stem_version(map_stem)
                relative_nvmbnd_path = Path(f"map/{map_stem}/{map_stem}.nvmbnd")
            else:
                map_stem = settings.get_latest_map_stem_version()
                relative_nvmbnd_path = default_map_path / f"{map_stem}.nvmbnd"

            if map_stem not in opened_nvmbnds:
                try:
                    nvmbnd_path = settings.prepare_project_file(relative_nvmbnd_path, False, must_exist=True)
                except FileNotFoundError as ex:
                    return self.error(f"Cannot find NVMBND: {relative_nvmbnd_path}. Error: {ex}")
                try:
                    nvmbnd = opened_nvmbnds[map_stem] = Binder.from_path(nvmbnd_path)
                except Exception as ex:
                    self.error(f"Could not load NVMBND for map '{map_stem}'. Error: {ex}")
                    continue
            else:
                nvmbnd = opened_nvmbnds[map_stem]

            # Get model file stem from MSB (must contain matching part).
            navmesh_part_name = get_bl_obj_stem(bl_mesh_obj)  # could be the same as the file stem
            relative_msb_path = settings.get_relative_msb_path(map_stem)  # will also use latest MSB version
            msb_stem = relative_msb_path.stem

            if relative_msb_path not in opened_msbs:
                # Open new MSB.
                try:
                    msb_path = settings.prepare_project_file(relative_msb_path, False, must_exist=True)
                except FileNotFoundError as ex:
                    self.error(
                        f"Could not find MSB file '{relative_msb_path}' for map '{map_stem}'. Error: {ex}"
                    )
                    continue
                opened_msbs[relative_msb_path] = get_cached_file(msb_path, settings.get_game_msb_class())

            msb = opened_msbs[relative_msb_path]  # type: MSB_TYPING

            try:
                msb_part = msb.navmeshes.find_entry_name(navmesh_part_name)
            except KeyError:
                return self.error(
                    f"Navmesh part '{navmesh_part_name}' not found in MSB {msb_stem}."
                )
            if not msb_part.model.name:
                return self.error(
                    f"Navmesh part '{navmesh_part_name}' in MSB {msb_stem} has no model name."
                )

            edited_msb_part_names = edited_part_names.setdefault(msb_stem, set())
            if navmesh_part_name in edited_msb_part_names:
                self.warning(
                    f"Navmesh part '{navmesh_part_name}' was exported more than once in selected meshes."
                )
            edited_msb_part_names.add(navmesh_part_name)

            model_stem = bl_mesh_obj.get("Model File Stem", None) if self.prefer_new_model_file_stem else None
            if not model_stem:  # could be None or empty string
                # Use existing MSB model name.
                model_stem = msb_part.model.get_model_file_stem(map_stem)
                # Warn if MSB model stem does not match (non-preferred) Blender object property.
                if (model_file_stem := bl_mesh_obj.get("Model File Stem", None)) is not None:
                    if model_file_stem != model_stem:
                        self.warning(
                            f"Navmesh part '{navmesh_part_name}' in MSB {msb_stem} has model name "
                            f"'{msb_part.model.name}' but Blender mesh 'Model File Stem' is '{model_file_stem}'. "
                            f"Using NVM stem from MSB model name; you may want to update the Blender mesh."
                        )
            else:
                # Update MSB model name (game-dependent format).
                msb_part.model.set_name_from_model_file_stem(model_stem)

            # Update part transform in MSB.
            bl_transform = BlenderTransform.from_bl_obj(bl_mesh_obj)
            msb_part.translate = bl_transform.game_translate
            msb_part.rotate = bl_transform.game_rotate_deg
            msb_part.scale = bl_transform.game_scale

            try:
                nvm = exporter.export_nvm(bl_mesh_obj)
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Cannot get exported NVM. Error: {ex}")
            else:
                nvm.dcx_type = DCXType.Null  # no DCX compression inside NVMBND

            nvm_entry_name = f"{model_stem}.nvm"
            nvmbnd.set_default_entry(
                nvm_entry_name,
                new_id=nvmbnd.highest_entry_id + 1,
                new_path=f"{map_stem}\\{nvm_entry_name}",
                new_flags=0x2,
            ).set_from_binary_file(nvm)

        for relative_msb_path, msb in opened_msbs.items():
            # Write MSB.
            settings.export_file(self, msb, relative_msb_path)

        for nvmbnd in opened_nvmbnds.values():
            nvmbnd.entries = list(sorted(nvmbnd.entries, key=lambda e: e.name))
            for i, entry in enumerate(nvmbnd.entries):
                entry.entry_id = i
            settings.export_file(self, nvmbnd, nvmbnd.path.relative_to(settings.game_directory))

        return {"FINISHED"}


class ExportAllNVMMSBParts(LoggingOperator):

    bl_idname = "export_scene.all_msb_nvm"
    bl_label = "Export All Navmesh Parts"
    bl_description = ("Fully replace MSB navmesh models and parts in selected game map MSB/NVMBND with children of "
                      "selected Blender object. Make sure you are exporting ALL of this map's navmeshes at once")

    # Always overwrites existing NVM parts and NVMBND entries.

    # TODO: Can't disable, but leaving here for now.
    prefer_new_model_file_stem: BoolProperty(
        name="Prefer New Model File Stem",
        description="Use the 'Model File Stem' property on the Blender mesh parent to update the model file stem in "
                    "the MSB and determine the NVM entry stem to write. If disabled, the MSB model name will be used.",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        """Parent of one or more 'n*' Meshes selected."""
        return (
            cls.settings(context).game_variable_name == "DARK_SOULS_DSR"
            and len(context.selected_objects) == 1
            and len(context.selected_objects[0].children) >= 1
            and all(child.type == "MESH" and child.name[0] == "n" for child in context.selected_objects[0].children)
        )

    def execute(self, context):
        settings = self.settings(context)
        if settings.game_variable_name != "DARK_SOULS_DSR":
            return self.error("Quick MSB Navmesh export is only supported for Dark Souls: Remastered.")

        if not self.poll(context):
            return self.error("Children of object selected for MSB model/part export are not all valid 'n' meshes.")

        if not settings.map_stem and not settings.detect_map_from_parent:
            return self.error(
                "No game map directory specified in Soulstruct settings and `Detect Map from Parent` is disabled."
            )
        default_map_path = Path(f"map/{settings.get_latest_map_stem_version()}") if settings.map_stem else None

        # TODO: Not needed for meshes only?
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        bl_parent = context.selected_objects[0]

        if settings.detect_map_from_parent:
            map_stem = bl_parent.name.split(" ")[0]
            if not MAP_STEM_RE.match(map_stem):
                return self.error(
                    f"Selected parent object '{bl_parent.name}' does not start with a valid map stem."
                )
            # NVMBND files come from latest 'map' version.
            map_stem = settings.get_latest_map_stem_version(map_stem)
            # SIB path comes from oldest 'map' version.
            sib_map_stem = settings.get_oldest_map_stem_version(map_stem)
            relative_nvmbnd_path = Path(f"map/{map_stem}/{map_stem}.nvmbnd")
        else:
            # Use Soulstruct selected map.
            map_stem = settings.get_latest_map_stem_version()
            sib_map_stem = settings.get_oldest_map_stem_version(map_stem)
            relative_nvmbnd_path = default_map_path / f"{map_stem}.nvmbnd"

        exporter = NVMExporter(self, context)

        nvmbnd = NVMBND(map_stem=map_stem)
        msb_new_models = {}
        part_sib_path = f"N:\\FRPG\\data\\Model\\map\\{sib_map_stem}\\sib\\n_layout.SIB"

        relative_msb_path = settings.get_relative_msb_path(map_stem)  # will also use latest MSB version
        try:
            msb_path = settings.prepare_project_file(relative_msb_path, False, must_exist=True)
        except FileNotFoundError as ex:
            return self.error(
                f"Could not find MSB file '{relative_msb_path}' for map '{map_stem}'. Error: {ex}"
            )
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING

        # Erase all MSB Navmesh models and parts. (No other MSB entries should reference navmeshes.)
        msb.navmeshes.clear()
        msb.navmesh_models.clear()

        children = list(bl_parent.children)
        children.sort(key=lambda o: natural_keys(o.name))  # ensure child order matches Blender hierarchy order

        for bl_mesh_obj in children:

            bl_mesh_obj: bpy.types.MeshObject

            # Get model file stem from MSB (must contain matching part).
            navmesh_part_name = get_bl_obj_stem(bl_mesh_obj)  # could be the same as the file stem

            # Get navmesh groups by parsing part name.
            # TODO: Check 'Navmesh Group' property?
            navmesh_group = bl_mesh_obj.get("Navmesh Group", None)  # type: int
            if navmesh_group is None:
                try:
                    navmesh_group = int(navmesh_part_name[1:5])  # model ID
                except ValueError:
                    return self.error(
                        f"Could not parse model ID of Blender navmesh '{navmesh_part_name}' to use as navmesh group."
                    )

            nvm_entry_stem = bl_mesh_obj.get("Model File Stem", None) if self.prefer_new_model_file_stem else None
            if not nvm_entry_stem:  # could be None or empty string
                # Use first seven characters of part name (e.g. 'n1234B0') and map area suffix (e.g. 'A12').
                nvm_entry_stem = navmesh_part_name[:7] + f"A{map_stem[1:3]}"
            msb_model_name = nvm_entry_stem[:7]  # no area suffix

            bl_transform = BlenderTransform.from_bl_obj(bl_mesh_obj)

            if msb_model_name in msb_new_models:
                # NVM and MSB model already created. Retrieve MSB model entry.
                msb_navmesh_model = msb_new_models[msb_model_name]
                self.warning(f"Multiple Navmesh parts use NVM model '{nvm_entry_stem}'. This is highly unusual!")
            else:
                # Create NVM model and MSB model entry.
                msb_navmesh_model = MSBNavmeshModel(
                    name=msb_model_name,
                    sib_path=f"N:\\FRPG\\data\\Model\\map\\{sib_map_stem}\\navimesh\\{msb_model_name}.SIB"
                )
                msb.navmesh_models.append(msb_navmesh_model)
                try:
                    nvm = exporter.export_nvm(bl_mesh_obj)
                except Exception as ex:
                    traceback.print_exc()
                    return self.error(f"Cannot get exported NVM. Error: {ex}")
                else:
                    nvm.dcx_type = DCXType.Null  # no DCX compression inside NVMBND

                nvmbnd.nvms[nvm_entry_stem] = nvm
                msb_new_models[msb_model_name] = msb_navmesh_model

            # Create MSB part entry.
            msb_navmesh_part = MSBNavmesh(
                name=navmesh_part_name,
                model=msb_navmesh_model,
                sib_path=part_sib_path,
                navmesh_groups=GroupBitSet128({navmesh_group}),
                # Set transform (usually identity).
                translate=bl_transform.game_translate,
                rotate=bl_transform.game_rotate_deg,
                scale=bl_transform.game_scale,
            )
            msb.navmeshes.append(msb_navmesh_part)

        # Sort models, just in case any weird custom names were used.
        msb.navmeshes.sort_by_name()

        # Write MSB.
        settings.export_file(self, msb, relative_msb_path)
        # Write NVMBND.
        settings.export_file(self, nvmbnd, relative_nvmbnd_path)

        self.info(
            f"Exported complete list of MSB navmeshes and NVM models to {map_stem}: "
            f"{len(msb.navmeshes)} parts using {len(msb.navmesh_models)} models."
        )

        return {"FINISHED"}


class NVMExporter:

    operator: LoggingOperator

    def __init__(self, operator: LoggingOperator, context):
        self.operator = operator
        self.context = context

    def warning(self, msg: str):
        self.operator.report({"WARNING"}, msg)
        print(f"# WARNING: {msg}")

    def export_nvm(self, bl_mesh_obj: bpy.types.MeshObject) -> NVM:
        """Create `NVM` from a Blender mesh object.

        This is much simpler than FLVER or HKX map collision mesh export. Note that the navmesh name is not needed, as
        it appears nowhere in the NVM binary file.
        """
        nvm_verts = np.array([vert.co for vert in bl_mesh_obj.data.vertices], dtype=np.float32)
        # Swap Y and Z coordinates.
        nvm_verts[:, [1, 2]] = nvm_verts[:, [2, 1]]

        nvm_faces = []  # type: list[tuple[int, int, int]]
        for face in bl_mesh_obj.data.polygons:
            if len(face.vertices) != 3:
                raise ValueError(f"Found a non-triangular mesh face in NVM. It must be triangulated first.")
            # noinspection PyTypeChecker
            vertices = tuple(face.vertices)  # type: tuple[int, int, int]
            nvm_faces.append(vertices)

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
            else:
                self.warning(f"Child object '{child.name}' of NVM object '{bl_mesh_obj.name}' does not start with "
                             f"'{event_prefix}'. Ignoring it as a navmesh event entity.")

        nvm = NVM(
            big_endian=False,
            vertices=nvm_verts,
            triangles=nvm_triangles,
            event_entities=event_entities,
            # quadtree boxes generated automatically
        )

        return nvm
