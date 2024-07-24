"""Operators for importing `MSBNavmesh` entries, and their NVM models, from MSB files."""
from __future__ import annotations

__all__ = [
    "ImportMSBNavmesh",
    "ImportAllMSBNavmeshes",
    "ExportMSBNavmeshes",
    "ExportMSBNavmeshCollection",
]

import traceback
import typing as tp
from pathlib import Path

import bpy
from io_soulstruct import SoulstructSettings
from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.msb.operator_config import MSBPartOperatorConfig
from io_soulstruct.msb.properties import MSBPartSubtype
from io_soulstruct.navmesh.nvm import export_nvm_model
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import LoggingOperator, get_bl_obj_tight_name, MAP_STEM_RE
from soulstruct.dcx import DCXType
from soulstruct.darksouls1r.maps.navmesh import NVMBND
from soulstruct.utilities.text import natural_keys
from .base import *

if tp.TYPE_CHECKING:
    from io_soulstruct.type_checking import MSB_TYPING


msb_navmesh_operator_config = MSBPartOperatorConfig(
    PART_SUBTYPE=MSBPartSubtype.NAVMESH,
    MSB_LIST_NAME="navmeshes",
    MSB_MODEL_LIST_NAMES=["navmesh_models"],
    GAME_ENUM_NAME="navmesh_part",
    USE_LATEST_MAP_FOLDER=True,
)


class ImportMSBNavmesh(BaseImportSingleMSBPart):
    """Import a NVM from the current selected value of listed game MSB navmesh entries."""
    bl_idname = "import_scene.msb_navmesh_part"
    bl_label = "Import Navmesh Part"
    bl_description = "Import selected MSB Navmesh part, and NVM model if needed, from selected game map"

    config = msb_navmesh_operator_config


class ImportAllMSBNavmeshes(BaseImportAllMSBParts):
    """Import a NVM from the current selected value of listed game MSB navmesh entries."""
    bl_idname = "import_scene.all_msb_navmesh_parts"
    bl_label = "Import All Navmesh Parts"
    bl_description = (
        "Import all MSB Navmesh parts, and any NVM models if needed, from selected game map. Much faster than FLVER "
        "importing"
    )

    config = msb_navmesh_operator_config


class ExportMSBNavmeshes(BaseExportMSBParts):

    bl_idname = "export_scene.msb_navmesh_parts"
    bl_label = "Export Navmesh Parts"
    bl_description = "Export selected MSB Navmesh parts to MSB and optionally export their NVM models"

    config = msb_navmesh_operator_config

    opened_nvmbnds: dict[str, NVMBND]

    @classmethod
    def poll(cls, context):
        return cls.settings(context).is_game("DARK_SOULS_DSR") and super().poll(context)

    def init(self, context, settings):
        self.opened_nvmbnds = {}

    def finish_model_export(self, context: bpy.types.Context, settings: SoulstructSettings):
        for nvmbnd in self.opened_nvmbnds.values():
            nvmbnd.entries = list(sorted(nvmbnd.entries, key=lambda e: e.name))
            for i, entry in enumerate(nvmbnd.entries):
                entry.entry_id = i
            settings.export_file(self, nvmbnd, nvmbnd.path.relative_to(settings.game_directory))
        self.info(f"Exported NVMBNDs with new NVM models for {len(self.opened_nvmbnds)} maps.")

    def export_model(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_mesh: bpy.types.MeshObject,
        map_stem: str,
    ):
        """Finds NVMBND Binders and exports NVM files into them."""
        settings = operator.settings(context)
        relative_nvmbnd_path = Path(f"map/{map_stem}/{map_stem}.nvmbnd")
        if map_stem not in self.opened_nvmbnds:
            try:
                nvmbnd_path = settings.prepare_project_file(relative_nvmbnd_path, must_exist=True)
            except FileNotFoundError as ex:
                self.error(f"Cannot find NVMBND: {relative_nvmbnd_path}. Error: {ex}")
                raise
            try:
                nvmbnd = self.opened_nvmbnds[map_stem] = NVMBND.from_path(nvmbnd_path)
            except Exception as ex:
                self.error(f"Could not load NVMBND for map '{map_stem}'. Error: {ex}")
                raise
        else:
            nvmbnd = self.opened_nvmbnds[map_stem]

        try:
            nvm = export_nvm_model(self, model_mesh)
        except Exception as ex:
            traceback.print_exc()
            self.error(f"Cannot get exported NVM. Error: {ex}")
            raise
        else:
            nvm.dcx_type = DCXType.Null  # no DCX compression inside DS1 NVMBND

        model_stem = get_bl_obj_tight_name(model_mesh)
        nvmbnd.nvms[model_stem] = nvm  # no file suffix needed in `NVMBND` keys



class ExportMSBNavmeshCollection(LoggingOperator):
    """Additional operator that makes it easier to export ALL MSB Navmesh parts at once from selected Collection.

    This is useful because the ordered list of MSB Navmesh parts is synchronized with MCG, MCP, and NVMDUMP files (the
    last of which is easily auto-generated here). NVM model writing is also fast enough that it's not a big deal to
    blindly export them all.
    """

    bl_idname = "export_scene.complete_map_navigation"
    bl_label = "Export Complete Map Navigation"
    bl_description = (
        "Fully replace MSB navmesh parts, NVMBND models, and NVMDUMP in selected game map with MSB Navmesh parts "
        "in selected Blender collection whose name ends with 'Navmeshes' (for misclick safety). Make sure the selected "
        "collection contains ALL of this map's navmesh parts. Always exports NVM models, regardless of current settings"
    )

    config = msb_navmesh_operator_config

    write_nvmdump: bpy.props.BoolProperty(
        name="Write NVM Dump",
        description="Write a NVMDUMP text file next to the NVMBND with the NVM data for each navmesh MSB part",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        """Collection of "Navmeshes" with one or more 'n*' Meshes is active."""
        return (
            cls.settings(context).is_game("DARK_SOULS_DSR")
            and context.collection and "Navmeshes" in context.collection.name
            and len(context.collection.objects) > 0
            and all(
                obj.soulstruct_type == SoulstructType.MSB_PART
                and obj.msb_part_props.part_subtype == MSBPartSubtype.NAVMESH
                for obj in context.collection.objects
            )
        )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):

        settings = self.settings(context)
        bl_navmesh_type = self.config.get_bl_part_type(settings.game)

        if not settings.map_stem and not settings.detect_map_from_collection:
            return self.error(
                "No game map directory specified in Soulstruct settings and `Detect Map from Collection` is disabled."
            )        
        
        # Important that we match Blender hierarchy sorting, as this will be used to index MCG and MCP files.
        bl_navmeshes = sorted(
            [bl_navmesh_type(obj) for obj in context.collection.objects],
            key=lambda o: natural_keys(o.name)
        )

        for bl_navmesh in bl_navmeshes:
            if not bl_navmesh.model:
                return self.error(f"Navmesh part '{bl_navmesh.name}' has no model assigned.")

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

        msb_new_models = {}  # avoid adding duplicate MSB models        
        relative_nvmbnd_path = Path(f"map/{map_stem}/{map_stem}.nvmbnd")
        nvmbnd = NVMBND(map_stem=map_stem)  # brand new empty NVMBND

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

        for bl_navmesh in bl_navmeshes:

            # We need to add model to MSB before creating Part that references it.
            model_stem = get_bl_obj_tight_name(bl_navmesh.model)  # already confirmed to be set

            if model_stem in msb_new_models:
                # NVM and MSB model already created.
                self.warning(
                    f"Multiple Navmesh parts use MSB model '{model_stem}'. This is highly unusual!"
                )
            else:
                # Create NVM model and MSB model entry.
                navmesh_model = msb.navmesh_models.new()
                navmesh_model.set_name_from_model_file_stem(model_stem)
                navmesh_model.set_auto_sib_path(map_stem)
                msb.navmesh_models.append(navmesh_model)

                try:
                    nvm = export_nvm_model(self, bl_navmesh.model)
                except Exception as ex:
                    traceback.print_exc()
                    self.error(f"Cannot get exported NVM. Error: {ex}")
                    raise
                else:
                    nvm.dcx_type = DCXType.Null  # no DCX compression inside DS1 NVMBND

                nvmbnd.nvms[model_stem] = nvm  # no file suffix needed in `NVMBND` keys

            # Create MSB Navmesh part. It will find the above model automatically.
            navmesh_part = bl_navmesh.to_entry(self, context, settings, map_stem, msb)
            msb.navmeshes.append(navmesh_part)

        # Sort models parts, just in case any weird custom names were used. We don't sort parts because their order
        # matters for MCG/MCP indexing, which should be checked by the user. Model order doesn't matter though.
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

        self.info(
            f"Exported complete list of MSB navmeshes and NVM models to {map_stem}: "
            f"{len(msb.navmeshes)} parts using {len(msb.navmesh_models)} models."
        )

        return {"FINISHED"}
