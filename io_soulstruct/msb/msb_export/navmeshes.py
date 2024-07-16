from __future__ import annotations

__all__ = [
    "ExportMSBNavmeshes",
    "ExportCompleteMapNavigation",
]

import traceback
import typing as tp
from pathlib import Path

import bpy

from soulstruct.base.maps.msb.utils import GroupBitSet128
from soulstruct.darksouls1r.maps.models import MSBNavmeshModel
from soulstruct.darksouls1r.maps.parts import MSBNavmesh
from soulstruct.darksouls1r.maps.navmesh import NVMBND
from soulstruct.dcx import DCXType
from soulstruct.games import DARK_SOULS_DSR
from soulstruct.utilities.text import natural_keys

from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.utilities import *
from io_soulstruct.navmesh.nvm.model_export import *
from .core import obj_to_msb_entry_transform
from .settings import MSBExportSettings

if tp.TYPE_CHECKING:
    from io_soulstruct.type_checking import MSB_TYPING


def get_navmesh_group(nvm_mesh: bpy.types.MeshObject) -> int:
    navmesh_group = nvm_mesh.get("Navmesh Group", None)  # type: int
    if navmesh_group is None:
        # Get single navmesh group by parsing model ID from part name.
        # TODO: Theoretically more reliable from model name (below).
        try:
            navmesh_group = int(nvm_mesh.name[1:5]) % 1000  # model ID (modulo 1000)
        except ValueError:
            raise NVMExportError(
                f"Could not parse model ID of Blender navmesh '{nvm_mesh.name}' to use as navmesh group."
            )
    return navmesh_group


class ExportMSBNavmeshes(LoggingOperator):

    bl_idname = "export_scene.msb_nvm"
    bl_label = "Export Navmesh Part"
    bl_description = "Export transform and mesh of selected NVM navmeshes into selected game map MSB/NVMBND"

    # Always overwrites existing NVM parts and NVMBND entries.

    @classmethod
    def poll(cls, context):
        """One or more 'n*' Meshes selected."""
        return (
            cls.settings(context).is_game(DARK_SOULS_DSR)
            and len(context.selected_objects) > 0
            and all(obj.type == "MESH" and obj.name[0] == "n" for obj in context.selected_objects)
        )

    def execute(self, context):
        settings = self.settings(context)
        if settings.game_variable_name != "DARK_SOULS_DSR":
            return self.error("Quick MSB Navmesh export is only supported for Dark Souls: Remastered.")
        msb_export_settings = context.scene.msb_export_settings  # type: MSBExportSettings

        if not self.poll(context):
            return self.error("No valid 'n' meshes selected for quick NVM export.")

        if not settings.map_stem and not settings.detect_map_from_collection:
            return self.error(
                "No game map directory specified in Soulstruct settings and `Detect Map from Collection` is disabled."
            )

        opened_msbs = {}  # type: dict[Path, MSB_TYPING]
        edited_part_names = {}  # type: dict[str, set[str]]
        opened_nvmbnds = {}  # type: dict[str, NVMBND]

        for nvm_instance in context.selected_objects:

            nvm_instance: bpy.types.MeshObject

            # NVMBND files come from latest 'map' folder version.
            map_stem = settings.get_map_stem_for_export(nvm_instance, latest=True)
            relative_nvmbnd_path = Path(f"map/{map_stem}/{map_stem}.nvmbnd")

            if msb_export_settings.export_model_files:
                if map_stem not in opened_nvmbnds:
                    try:
                        nvmbnd_path = settings.prepare_project_file(relative_nvmbnd_path, must_exist=True)
                    except FileNotFoundError as ex:
                        self.error(f"Cannot find NVMBND: {relative_nvmbnd_path}. Error: {ex}")
                        continue
                    try:
                        nvmbnd = opened_nvmbnds[map_stem] = NVMBND.from_path(nvmbnd_path)
                    except Exception as ex:
                        self.error(f"Could not load NVMBND for map '{map_stem}'. Error: {ex}")
                        continue
                else:
                    nvmbnd = opened_nvmbnds[map_stem]
            else:
                nvmbnd = None

            # Get model file stem from MSB (must contain matching part).
            navmesh_part_name = get_bl_obj_stem(nvm_instance)  # could be the same as the file stem
            relative_msb_path = settings.get_relative_msb_path(map_stem)  # will also use latest MSB version
            msb_stem = relative_msb_path.stem

            if relative_msb_path not in opened_msbs:
                # Open new MSB. We start with the game MSB unless `Prefer Import from Project` is enabled.
                try:
                    msb_path = settings.prepare_project_file(relative_msb_path, must_exist=True)
                except FileNotFoundError as ex:
                    self.error(
                        f"Could not find MSB file '{relative_msb_path}' for map '{map_stem}'. Error: {ex}"
                    )
                    continue
                opened_msbs[relative_msb_path] = get_cached_file(msb_path, settings.get_game_msb_class())

            msb = opened_msbs[relative_msb_path]  # type: MSB_TYPING

            edited_msb_part_names = edited_part_names.setdefault(msb_stem, set())
            if navmesh_part_name in edited_msb_part_names:
                self.warning(
                    f"Navmesh part '{navmesh_part_name}' was exported more than once in selected meshes."
                )
            edited_msb_part_names.add(navmesh_part_name)

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

            model_name = find_model_name(self, nvm_instance, process_model_name_map_area(map_stem))
            msb_model_name = msb_part.model.get_model_file_stem(map_stem)
            if model_name != msb_model_name:
                # We update the MSB model name even if exporting MSB data only.
                self.warning(
                    f"Updating Navmesh model name of MSB part '{navmesh_part_name}' to '{model_name}'."
                )
                msb_part.model.set_name_from_model_file_stem(model_name)

            obj_to_msb_entry_transform(nvm_instance, msb_part)

            if msb_export_settings.export_model_files:
                try:
                    nvm = export_nvm_model(self, nvm_instance)
                except Exception as ex:
                    traceback.print_exc()
                    return self.error(f"Cannot get exported NVM. Error: {ex}")
                else:
                    nvm.dcx_type = DCXType.Null  # no DCX compression inside NVMBND
                nvmbnd.nvms[model_name] = nvm  # no file suffix needed in `NVMBND` keys

        for relative_msb_path, msb in opened_msbs.items():
            # Write MSB.
            settings.export_file(self, msb, relative_msb_path)

        if msb_export_settings.export_model_files:
            for nvmbnd in opened_nvmbnds.values():
                nvmbnd.entries = list(sorted(nvmbnd.entries, key=lambda e: e.name))
                for i, entry in enumerate(nvmbnd.entries):
                    entry.entry_id = i
                settings.export_file(self, nvmbnd, nvmbnd.path.relative_to(settings.game_directory))
            self.info(f"Exported MSB navmesh data/models and NVM parts to NVMBNDs for {len(opened_msbs)} maps.")
        else:
            self.info(f"Exported MSB navmesh data/models for {len(opened_msbs)} maps. No NVM models exported.")

        return {"FINISHED"}


class ExportCompleteMapNavigation(LoggingOperator):

    bl_idname = "export_scene.complete_map_navigation"
    bl_label = "Export Complete Map Navigation"
    bl_description = ("Fully replace MSB navmesh parts, NVMBND models, and NVMDUMP in selected game map with parts "
                      "whose name starts with 'n' in selected Blender collection whose name ends with 'Navmeshes' (for "
                      "safety). Make sure you are exporting ALL of this map's navmeshes at once")

    # Always overwrites existing MSB Navmesh parts, NVMBND entries, and NVMDUMP text file.

    # TODO: Can't be changed currently.
    write_nvmdump: bpy.props.BoolProperty(
        name="Write NVM Dump",
        description="Write a NVMDUMP text file next to the NVMBND with the NVM data for each navmesh MSB part",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        """Collection of "Navmeshes" with one or more 'n*' Meshes is active."""
        return (
            cls.settings(context).is_game(DARK_SOULS_DSR)
            and context.collection and "Navmeshes" in context.collection.name
            and len(context.collection.objects) > 0
            and all(obj.type == "MESH" and obj.name[0] == "n" for obj in context.collection.objects)
        )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        settings = self.settings(context)
        if settings.game_variable_name != "DARK_SOULS_DSR":
            return self.error("Quick MSB Navmesh export is only supported for Dark Souls: Remastered.")
        msb_export_settings = context.scene.msb_export_settings  # type: MSBExportSettings

        if not self.poll(context):
            return self.error("Must select a collection with name ending in 'Navmeshes'.")

        if not settings.map_stem and not settings.detect_map_from_collection:
            return self.error(
                "No game map directory specified in Soulstruct settings and `Detect Map from Collection` is disabled."
            )

        # TODO: Not needed for meshes only?
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        navmesh_part_instances = [
            mesh for mesh in context.collection.objects if mesh.type == "MESH" and mesh.name[0] == "n"
        ]  # type: list[bpy.types.MeshObject]

        if not navmesh_part_instances:
            return self.error(f"No 'n*' meshes found in selected collection '{context.collection.name}'.")

        if settings.detect_map_from_collection:
            match = MAP_STEM_RE.match(context.collection.name.split(" ")[0])
            if not match:
                raise ValueError(
                    f"Collection '{context.collection.name}' does not match map stem pattern. (You can always disable "
                    f"'Detect Map from Collection' in Soulstruct settings and manually select the map.)"
                )
            map_stem = context.collection.name.split(" ")[0]
        else:
            map_stem = settings.get_latest_map_stem_version()

        # SIB path comes from oldest 'map' version.
        sib_map_stem = settings.get_oldest_map_stem_version(map_stem)
        part_sib_path = f"N:\\FRPG\\data\\Model\\map\\{sib_map_stem}\\sib\\n_layout.SIB"
        msb_new_models = {}  # avoid adding duplicate MSB models

        if msb_export_settings.export_model_files:
            relative_nvmbnd_path = Path(f"map/{map_stem}/{map_stem}.nvmbnd")
            nvmbnd = NVMBND(map_stem=map_stem)
        else:
            relative_nvmbnd_path = nvmbnd = None

        relative_msb_path = settings.get_relative_msb_path(map_stem)  # will also use latest MSB version
        try:
            # We start with the game MSB unless `Prefer Import from Project` is enabled.
            msb_path = settings.prepare_project_file(relative_msb_path, must_exist=True)
        except FileNotFoundError as ex:
            return self.error(
                f"Could not find MSB file '{relative_msb_path}' for map '{map_stem}'. Error: {ex}"
            )
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING

        # Erase all MSB Navmesh models and parts. (No other MSB entries should reference navmeshes.)
        msb.navmeshes.clear()
        msb.navmesh_models.clear()

        # Sort MSB navmesh parts so that they match Blender's hierarchy order. Remember that this is important, because
        # binary MCG and MCP files will index these MSB navmeshes directly!
        navmesh_part_instances.sort(key=lambda o: natural_keys(o.name))

        for navmesh_part_instance in navmesh_part_instances:

            navmesh_part_name = get_bl_obj_stem(navmesh_part_instance)  # could be the same as the file stem
            navmesh_group = get_navmesh_group(navmesh_part_instance)

            model_name = find_model_name(self, navmesh_part_instance, process_model_name_map_area(map_stem))
            msb_model_name = model_name[:7]  # no area suffix

            if msb_model_name in msb_new_models:
                # NVM and MSB model already created. Retrieve MSB model entry. (Note that this is the only operator
                # that does this check currently.)
                msb_navmesh_model = msb_new_models[msb_model_name]
                self.warning(
                    f"Multiple Navmesh parts use MSB model '{msb_model_name}' (NVM model {model_name}). "
                    f"This is highly unusual!"
                )
            else:
                # Create NVM model and MSB model entry.
                msb_navmesh_model = MSBNavmeshModel(
                    name=msb_model_name,
                    sib_path=f"N:\\FRPG\\data\\Model\\map\\{sib_map_stem}\\navimesh\\{msb_model_name}.SIB"
                )
                msb.navmesh_models.append(msb_navmesh_model)

                if nvmbnd:
                    try:
                        nvm = export_nvm_model(self, navmesh_part_instance)
                    except Exception as ex_:
                        traceback.print_exc()
                        # We return here; no files will have been written.
                        return self.error(f"Cannot get exported NVM. Error: {ex_}")
                    nvm.dcx_type = DCXType.Null  # no DCX compression inside NVMBND
                    nvmbnd.nvms[model_name] = nvm  # no file suffix needed in `NVMBND` keys

                msb_new_models[msb_model_name] = msb_navmesh_model

            # Create MSB part entry.
            msb_navmesh_part = MSBNavmesh(
                name=navmesh_part_name,
                model=msb_navmesh_model,
                sib_path=part_sib_path,
                navmesh_groups=GroupBitSet128({navmesh_group}),
                # Transform set below.
            )
            obj_to_msb_entry_transform(navmesh_part_instance, msb_navmesh_part)
            msb.navmeshes.append(msb_navmesh_part)

        # Sort models parts, just in case any weird custom names were used. We don't sort parts because their order
        # matters for MCG/MCP indexing, which should be checked by the user.
        msb.navmesh_models.sort_by_name()

        # Write MSB.
        settings.export_file(self, msb, relative_msb_path)

        if nvmbnd:
            # Write NVMBND.
            settings.export_file(self, nvmbnd, relative_nvmbnd_path)

        if self.write_nvmdump:
            # NOTE: We write NVMDUMP even if only MSB data is requested, as it is an output of the MSB.
            relative_nvmdump_path = relative_nvmbnd_path.with_name(f"{map_stem}.nvmdump")
            nvmdump = msb.get_nvmdump(map_stem)
            settings.export_text_file(self, nvmdump, relative_nvmdump_path)
            self.info(f"Exported NVMDUMP file next to NVMBND: {relative_nvmdump_path.name}")

        if msb_export_settings.export_model_files:
            self.info(
                f"Exported complete list of MSB navmeshes and NVM models to {map_stem}: "
                f"{len(msb.navmeshes)} parts using {len(msb.navmesh_models)} models."
            )
        else:
            self.info(f"Exported complete list of MSB navmeshes to {map_stem}. No NVM models exported.")

        return {"FINISHED"}
