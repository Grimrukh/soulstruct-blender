from __future__ import annotations

__all__ = [
    "ExportAnyMSB",
    "ExportMapMSB",
]

import traceback
import typing as tp
from pathlib import Path

import bpy

from soulstruct.darksouls1ptde.maps.msb import MSB as MSB_PTDE
from soulstruct.darksouls1ptde.maps.navmesh import NVMBND as NVMBND_PTDE
from soulstruct.darksouls1r.maps.msb import MSB as MSB_DSR
from soulstruct.darksouls1r.maps.navmesh import NVMBND as NVMBND_DSR
from soulstruct.demonssouls.maps.msb import MSB as MSB_PTDE
from soulstruct.demonssouls.maps.msb import MSB as MSB_DES
from soulstruct.demonssouls.maps.navmesh import NVMBND as NVMBND_DES
from soulstruct.dcx import DCXType
from soulstruct.games import *
from soulstruct.utilities.text import natural_keys
from soulstruct_havok.fromsoft.shared import HKXBHD, BothResHKXBHD

from io_soulstruct.general.game_config import BLENDER_GAME_CONFIG
from io_soulstruct.collision.types import BlenderMapCollision
from io_soulstruct.navmesh.nvm.types import BlenderNVM
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities.operators import LoggingOperator, LoggingExportOperator

from .operator_config import *
from .properties import BlenderMSBPartSubtype
from .utilities import MSB_COLLECTION_RE

if tp.TYPE_CHECKING:
    from io_soulstruct.msb.types.base import *
    MSB_TYPING = tp.Union[MSB_PTDE, MSB_DSR, MSB_DES]


def _export_msb(
    operator: LoggingOperator,
    context: bpy.types.Context,
    map_stem: str,
) -> tuple[MSB_TYPING | None, list[bpy.types.Object]]:
    """Export `MSB` from Blender.

    Given `map_stem` will be the map stem that is baked into MSB entries, e.g. for SIB paths. It should match the
    MSB's written file stem, obviously (up to caller).
    """
    settings = operator.settings(context)
    export_settings = context.scene.msb_export_settings

    msb_class = settings.game_config.msb_class
    if not msb_class:
        operator.error(f"MSB class not found for game '{settings.game}'.")
        return None, []

    # First, collect all Parts, Regions, and Events in this collection, recursively.
    # We don't care about where they appear, or how they are parented. (All Parts/Regions will have their WORLD
    # transforms used, so users can parent these purely as a matter of their own convenience, even though the MSB
    # supports no such parenting. Events have no transform.)
    bl_part_objs = []
    bl_region_objs = []
    bl_event_objs = []
    checked_names = set()

    if export_settings.skip_connect_collisions:
        operator.warning("Skipping MSB Connect Collision parts as requested. Other maps will not load.")

    # TODO: Don't blindly check all collections/objects. Look for expected subcollection names.
    #  (At the supertype level, at least.)

    collections = [context.collection] + list(context.collection.children_recursive)
    render_hidden_count = 0
    for col in collections:
        for obj in col.objects:
            if obj.name in checked_names:
                continue
            checked_names.add(obj.name)

            if export_settings.skip_render_hidden and obj.hide_render:
                render_hidden_count += 1
                continue

            if obj.soulstruct_type == SoulstructType.MSB_PART:
                if (
                    export_settings.skip_connect_collisions
                    and obj.MSB_PART.entry_subtype_enum == BlenderMSBPartSubtype.ConnectCollision
                ):
                    # Ignore Connect Collisions.
                    continue
                bl_part_objs.append(obj)
            elif obj.soulstruct_type == SoulstructType.MSB_REGION:
                bl_region_objs.append(obj)
            elif obj.soulstruct_type == SoulstructType.MSB_EVENT:
                bl_event_objs.append(obj)
            # Otherwise, ignore. We allow the user to include non-Soulstruct objects in the MSB collection.

    if render_hidden_count > 0:
        operator.warning(f"Skipped {render_hidden_count} hidden objects from MSB export.")

    # Sort by natural order to match Blender hierarchy.
    bl_part_objs.sort(key=lambda x: natural_keys(x.name))
    bl_region_objs.sort(key=lambda x: natural_keys(x.name))
    bl_event_objs.sort(key=lambda x: natural_keys(x.name))

    operator.to_object_mode(context)

    # Create new MSB.
    msb = msb_class()  # type: MSB_PTDE | MSB_DSR | MSB_DES
    # We set `msb.path` for internal map stem detection in some MSB classes. Obviously not written path (relative).
    msb.path = Path(f"map/{map_stem}/{map_stem}.msb")

    all_bl_and_msb_entries = {  # only really sorted to count them by supertype
        SoulstructType.MSB_REGION: [],
        SoulstructType.MSB_PART: [],
        SoulstructType.MSB_EVENT: [],
    }
    for bl_entry_classes, bl_entry_objs, soulstruct_type in (
        (BLENDER_MSB_REGION_CLASSES[settings.game], bl_region_objs, SoulstructType.MSB_REGION),
        (BLENDER_MSB_PART_CLASSES[settings.game], bl_part_objs, SoulstructType.MSB_PART),
        (BLENDER_MSB_EVENT_CLASSES[settings.game], bl_event_objs, SoulstructType.MSB_EVENT),
    ):
        bl_and_msb_entries = all_bl_and_msb_entries[soulstruct_type]
        for bl_entry_obj in bl_entry_objs:
            subtype_enum = getattr(bl_entry_obj, soulstruct_type.name).entry_subtype_enum
            bl_entry_class = bl_entry_classes[subtype_enum]
            bl_entry = bl_entry_class(bl_entry_obj)
            msb_entry = bl_entry.to_soulstruct_obj(operator, context)
            msb.add_entry(msb_entry)
            bl_and_msb_entries.append((bl_entry, msb_entry))
            # self.info(f"Added MSB {subtype_enum.name}: {msb_entry.name}")

    # Set all MSB Entry references and Part models/SIB paths.
    for bl_and_msb_entries in all_bl_and_msb_entries.values():
        for bl_entry, msb_entry in bl_and_msb_entries:
            bl_entry.resolve_msb_entry_refs_and_map_stem(operator, context, msb_entry, msb, map_stem)

    # Sort all MSB Models by name.
    for _, model_list in msb.get_models_dict().items():
        model_list.sort_by_name()  # in-place

    model_count = len(msb.get_models())
    part_count = len(all_bl_and_msb_entries[SoulstructType.MSB_PART])
    region_count = len(all_bl_and_msb_entries[SoulstructType.MSB_REGION])
    event_count = len(all_bl_and_msb_entries[SoulstructType.MSB_EVENT])

    operator.info(
        f"Created MSB {map_stem} successfully with {region_count} Regions, {event_count} Events, "
        f"{part_count} Parts, and {model_count} Models."
    )

    return msb, bl_part_objs


class ExportAnyMSB(LoggingExportOperator):

    bl_idname = "export_scene.any_msb"
    bl_label = "Export MSB to File"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Export all Parts, Regions, and Events in active collection to a new MSB file"

    filename_ext = ".msb"

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)
        if not BLENDER_GAME_CONFIG[settings.game].msb_class:
            return False  # unsupported
        if not context.collection:
            return False
        # TODO: Hack for now. Probably use an extension property for Collection marking it as an MSB.
        if not MSB_COLLECTION_RE.match(context.collection.name):
            return False
        return True

    def invoke(self, context, _event):
        settings = self.settings(context)
        map_stem = ""
        if settings.auto_detect_export_map:
            match = MSB_COLLECTION_RE.match(context.collection.name)
            if match:
                map_stem = settings.get_latest_map_stem_version(match.group(1))
        else:
            map_stem = settings.get_latest_map_stem_version()  # MSB always uses latest
        if map_stem:
            self.filepath = f"{map_stem}.msb"
        return super().invoke(context, _event)

    def draw(self, context):
        layout = self.layout

        msb_export_settings = context.scene.msb_export_settings
        for prop_name in msb_export_settings.get_game_prop_names(context):
            if prop_name.startswith("export_"):
                continue  # no bonus exports (Models/JSON) for this generic operator
            layout.prop(msb_export_settings, prop_name)

    def execute(self, context):

        settings = self.settings(context)

        if settings.auto_detect_export_map:
            match = MSB_COLLECTION_RE.match(context.collection.name)
            if not match:
                return self.error(
                    f"Collection name '{context.collection.name}' does not match expected MSB collection name format. "
                    f"(You can still export this collection if you disable the 'Detect Map from Collection' setting.)"
                )
            map_stem = settings.get_latest_map_stem_version(match.group(1))
        else:
            map_stem = settings.get_latest_map_stem_version()  # MSB always uses latest
            if not map_stem:
                return self.error(
                    "No map selected in Soulstruct settings and `Detect Map from Collection` is disabled."
                )

        written_stem = Path(self.filepath).name.split(".")[0]
        if map_stem != written_stem:
            self.warning(
                f"Stem of written MSB file '{written_stem}' does not match exported MSB ID: {map_stem}. Internal MSB "
                f"strings (e.g. model SIB paths) may not match the written file."
            )

        msb, _ = _export_msb(self, context, map_stem)
        if msb is None:
            return self.error("Could not export MSB.")

        msb.write(Path(self.filepath))

        return {"FINISHED"}


class ExportMapMSB(LoggingOperator):

    bl_idname = "export_scene.map_msb"
    bl_label = "Export MSB to Map"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = ("Export all Parts, Regions, and Events in active collection to a new MSB for the appropriate "
                      "map. Can also export NVMDUMP, full navmesh model NVMBND, full collision model HKXBHDs, and/or "
                      "Soulstruct Project JSONs (all DS1 only)")

    @classmethod
    def poll(cls, context) -> bool:
        settings = cls.settings(context)
        if not BLENDER_GAME_CONFIG[settings.game].msb_class:
            return False  # unsupported
        if not context.collection:
            return False
        # TODO: Hack for now. Probably use an extension property for Collection marking it as an MSB.
        if not MSB_COLLECTION_RE.match(context.collection.name):
            return False
        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):

        settings = self.settings(context)
        export_settings = context.scene.msb_export_settings

        if settings.auto_detect_export_map:
            match = MSB_COLLECTION_RE.match(context.collection.name)
            if not match:
                return self.error(
                    f"Collection name '{context.collection.name}' does not match expected MSB collection name format. "
                    f"(You can still export this collection if you disable the 'Detect Map from Collection' setting.)"
                )
            map_stem = settings.get_latest_map_stem_version(match.group(1))
        else:
            map_stem = settings.get_latest_map_stem_version()  # MSB always uses latest
            if not map_stem:
                return self.error(
                    "No map selected in Soulstruct settings and `Detect Map from Collection` is disabled."
                )

        msb, bl_part_objs = _export_msb(self, context, map_stem)
        if msb is None:
            return self.error("Could not export MSB.")

        # MSB is ready to write.
        relative_msb_path = settings.get_relative_msb_path(map_stem)  # will use latest MSB version

        try:
            settings.export_file(self, msb, relative_msb_path, class_name="MSB")
        except Exception as ex:
            # Do not try to export NVMBND or NVMDUMP below.
            self.error(f"Could not export MSB. Error: {ex}")
            return None

        # NOTE: MSB export is now irreversible. We handle any errors that occur below while doing optional extra exports
        # of NVMBND, HKXBHD, NVMDUMP, and Soulstruct project JSON files.

        soulstruct_project_root_path = settings.soulstruct_project_root_path
        if soulstruct_project_root_path is not None and export_settings.export_soulstruct_jsons:
            # Write MSB JSON to project 'maps' subfolder.
            msb_json_path = soulstruct_project_root_path / "maps" / f"{map_stem}.json"
            try:
                msb.write_json(msb_json_path)
                self.info(f"Exported MSB JSON to Soulstruct Project folder: {msb_json_path}")
            except Exception as ex:
                self.error(f"Could not write MSB JSON to Soulstruct Project folder (MSBs still written). Error: {ex}")

        if export_settings.is_bool_prop_active_and_true(context, "export_nvmdump") and isinstance(msb, MSB_DSR):
            # Export NVMDUMP text file (DSR only).
            relative_nvmdump_path = Path(f"map/{map_stem}/{map_stem}.nvmdump")
            nvmdump = msb.get_nvmdump(map_stem)
            settings.export_text_file(self, nvmdump, relative_nvmdump_path)
            self.info(f"Exported NVMDUMP file next to NVMBND: {relative_nvmdump_path.name}")

        if export_settings.is_bool_prop_active_and_true(context, "export_navmesh_models"):
            bl_navmesh_class = BLENDER_MSB_PART_CLASSES[settings.game][BlenderMSBPartSubtype.Navmesh]
            bl_navmesh_parts = [
                bl_navmesh_class(obj) for obj in bl_part_objs
                if obj.MSB_PART.entry_subtype == BlenderMSBPartSubtype.Navmesh
            ]
            self.info(f"Exporting models for {len(bl_navmesh_parts)} MSB Navmesh Parts (should be fast).")
            self.export_nvmbnd(context, map_stem, bl_navmesh_parts)

        if export_settings.is_bool_prop_active_and_true(context, "export_collision_models"):
            if not settings.game_config.supports_collision_model:
                self.warning(f"Collision model export not supported for game '{settings.game}'.")
            else:
                bl_collision_class = BLENDER_MSB_PART_CLASSES[settings.game][BlenderMSBPartSubtype.Collision]
                bl_collision_parts = [
                    bl_collision_class(obj) for obj in bl_part_objs
                    if obj.MSB_PART.entry_subtype == BlenderMSBPartSubtype.Collision
                ]
                self.info(
                    f"Exporting models for {len(bl_collision_parts)} MSB Collision Parts (might take a few seconds)."
                )

                if settings.game_config.uses_loose_collision_files:
                    self.export_loose_hkxs(context, map_stem, bl_collision_parts)
                else:
                    self.export_hkxbhds(context, map_stem, bl_collision_parts)

        # NOTE: There is no option to export FLVER models, as this is slow and better done individually by user.

        return {"FINISHED"}

    # TODO: A lot of redundancy below, with the existing Model export operators.

    def export_loose_nvms(
        self, context: bpy.types.Context, map_stem: str, bl_navmeshes: list[BaseBlenderMSBPart]
    ) -> set[str]:
        """Collect and export all NVMs for all MSB Navmesh models."""
        settings = context.scene.soulstruct_settings

        relative_map_dir = Path(f"map/{map_stem}")
        added_models = set()
        for bl_navmesh in bl_navmeshes:
            if not bl_navmesh.model:
                # Log error (should never happen in any valid MSB), but continue.
                self.error(f"Blender MSB Navmesh '{bl_navmesh.name}' has no model assigned to export.")
                continue
            model_stem = bl_navmesh.game_name
            if model_stem in added_models:
                self.warning(
                    f"MSB {map_stem} has duplicate MSB Navmesh models ('{model_stem}'), which is extremely unusual."
                )
                continue
            added_models.add(model_stem)
            try:
                nvm = BlenderNVM(bl_navmesh.model).to_soulstruct_obj(self, context)
            except Exception as ex:
                traceback.print_exc()
                self.error(f"Could not export NVM navmesh model. Error: {ex}")
                continue
            else:
                nvm.dcx_type = DCXType.Null  # no DCX compression inside DS1 NVMBND

            settings.export_file(self, nvm, relative_map_dir / f"{model_stem}.nvm")

        if not added_models:
            self.warning(f"No Navmesh models found to export in MSB {map_stem}. No NVMs written.")
            return {"CANCELLED"}

        return {"FINISHED"}

    def export_nvmbnd(
        self, context: bpy.types.Context, map_stem: str, bl_navmeshes: list[BaseBlenderMSBPart]
    ) -> set[str]:
        """Collect and export brand new NVMBND containing all MSB Navmesh models."""
        settings = context.scene.soulstruct_settings

        relative_nvmbnd_path = Path(f"map/{map_stem}/{map_stem}.nvmbnd")
        if settings.is_game(DEMONS_SOULS):
            nvmbnd = NVMBND_DES(map_stem=map_stem)
        elif settings.is_game(DARK_SOULS_PTDE):
            nvmbnd = NVMBND_PTDE(map_stem=map_stem)
        elif settings.is_game(DARK_SOULS_DSR):
            nvmbnd = NVMBND_DSR(map_stem=map_stem)
        else:
            return self.error(f"NVMBND export not supported for game '{settings.game}'.")

        added_models = set()
        for bl_navmesh in bl_navmeshes:
            if not bl_navmesh.model:
                # Log error (should never happen in any valid MSB), but continue.
                self.error(f"Blender MSB Navmesh '{bl_navmesh.name}' has no model assigned to export.")
                continue
            try:
                bl_nvm = BlenderNVM(bl_navmesh.model)
            except Exception as ex:
                self.error(f"MSB Navmesh Part '{bl_navmesh.name}' does not have a valid NVM model. Error: {ex}")
                continue

            model_stem = bl_nvm.game_name
            if model_stem in added_models:
                self.warning(
                    f"MSB {map_stem} has duplicate MSB Navmesh models ('{model_stem}'), which is extremely unusual."
                )
                continue
            added_models.add(model_stem)
            try:
                nvm = bl_nvm.to_soulstruct_obj(self, context)
            except Exception as ex:
                traceback.print_exc()
                self.error(f"Could not export NVM navmesh model. Error: {ex}")
                continue
            else:
                nvm.dcx_type = DCXType.Null  # no DCX compression inside DS1 NVMBND

            nvmbnd.set_nvm(model_stem, nvm)

        if not added_models:
            self.warning(f"No Navmesh models found to export in MSB {map_stem}. NVMBND not written.")
            return {"CANCELLED"}

        try:
            settings.export_file(self, nvmbnd, relative_nvmbnd_path)
        except Exception as ex:
            return self.error(f"MSB {map_stem} was exported, but could not export new NVMBND. Error: {ex}")

        return {"FINISHED"}

    def export_loose_hkxs(
        self, context: bpy.types.Context, map_stem: str, bl_collisions: list[BaseBlenderMSBPart]
    ) -> set[str]:
        """Collect and export all both-res loose HKXs for all MSB Collision models."""
        settings = context.scene.soulstruct_settings
        dcx_type = settings.game.get_dcx_type("hkx")  # probably no DCX
        havok_module = settings.game_config.havok_module
        if not havok_module:
            return self.error(f"Cannot export Collision models for game '{settings.game}' without PyHavok module.")

        relative_map_dir = Path(f"map/{map_stem}")
        added_models = set()
        exported_paths = []

        for bl_collision in bl_collisions:
            if not bl_collision.model:
                # Log error (should never happen in any valid MSB), but continue.
                self.error(f"Blender MSB Collision '{bl_collision.name}' has no model assigned to export.")
                continue
            model_stem = bl_collision.game_name
            if model_stem in added_models:
                # Acceptable, unlike navmeshes (e.g. kill planes or shifted dupes of some other kind).
                continue
            added_models.add(model_stem)

            bl_collision_model = BlenderMapCollision(bl_collision.model)
            try:
                hi_hkx, lo_hkx = bl_collision_model.to_hkx_pair(
                    self, havok_module, require_hi=True, use_hi_if_missing_lo=True
                )
            except Exception as ex:
                self.error(f"Cannot get exported hi/lo HKX for '{bl_collision.model.name}'. Error: {ex}")
                continue
            hi_hkx.dcx_type = dcx_type
            lo_hkx.dcx_type = dcx_type

            try:
                exported_paths += settings.export_file(self, hi_hkx, relative_map_dir / f"{hi_hkx.path_stem}.hkx")
            except Exception as ex:
                self.error(f"Could not export hi HKX for '{bl_collision.model.name}'. Error: {ex}")
                continue
            try:
                exported_paths += settings.export_file(self, lo_hkx, relative_map_dir / f"{lo_hkx.path_stem}.hkx")
            except Exception as ex:
                # TODO: Delete hi HKX...
                self.error(f"Hi HKX exported, but could not export lo HKX for '{bl_collision.model.name}'. Error: {ex}")
                continue

        if not added_models:
            self.warning(f"No Collision models found to export in MSB {map_stem}. No HKX files written.")
            return {"CANCELLED"}
        if not exported_paths:
            return self.error(f"Collision models were found in MSB {map_stem}, but no HKX files could be written.")

        return {"FINISHED"}

    def export_hkxbhds(
        self, context: bpy.types.Context, map_stem: str, bl_collisions: list[BaseBlenderMSBPart]
    ) -> set[str]:
        """Collect and export brand new both-res HKXBHDs containing all MSB Collision models."""
        settings = context.scene.soulstruct_settings
        dcx_type = settings.game.get_dcx_type("hkx")  # will have DCX inside HKXBHD
        havok_module = settings.game_config.havok_module
        if not havok_module:
            return self.error(f"Cannot export Collision models for game '{settings.game}' without PyHavok module.")

        # The `BothResHKXBHD` class is already DSR-specific.
        both_res_hkxbhd = BothResHKXBHD(
            hi_res=HKXBHD(map_stem=map_stem, path=Path(f"map/{map_stem}/h{map_stem[1:]}.hkxbhd")),
            lo_res=HKXBHD(map_stem=map_stem, path=Path(f"map/{map_stem}/l{map_stem[1:]}.hkxbhd")),
            path=Path(f"map/{map_stem}"),
        )  # brand new empty HKXBHDs
        added_models = set()

        for bl_collision in bl_collisions:
            if not bl_collision.model:
                # Log error (should never happen in any valid MSB), but continue.
                self.error(f"Blender MSB Collision '{bl_collision.name}' has no model assigned to export.")
                continue
            model_stem = bl_collision.game_name
            if model_stem in added_models:
                # Acceptable, unlike navmeshes (e.g. kill planes or shifted dupes of some other kind).
                continue
            added_models.add(model_stem)

            bl_collision_model = BlenderMapCollision(bl_collision.model)
            try:
                hi_hkx, lo_hkx = bl_collision_model.to_hkx_pair(
                    self, havok_module, require_hi=True, use_hi_if_missing_lo=True
                )
            except Exception as ex:
                self.error(f"Cannot get exported hi/lo HKX for '{bl_collision.model.name}'. Error: {ex}")
                continue
            hi_hkx.dcx_type = dcx_type
            lo_hkx.dcx_type = dcx_type

            both_res_hkxbhd.hi_res.set_hkx(hi_hkx.path_stem, hi_hkx)
            both_res_hkxbhd.lo_res.set_hkx(lo_hkx.path_stem, lo_hkx)

        if not added_models:
            self.warning(f"No Collision models found to export in MSB {map_stem}. HKXBHDs not written.")
            return {"CANCELLED"}

        try:
            # HKX paths are already set to correct relative path.
            settings.export_file(self, both_res_hkxbhd.hi_res, both_res_hkxbhd.hi_res.path)
            settings.export_file(self, both_res_hkxbhd.lo_res, both_res_hkxbhd.lo_res.path)
        except Exception as ex:
            return self.error(f"MSB {map_stem} was exported, but could not export new Collision HKXBHDs. Error: {ex}")

        return {"FINISHED"}
