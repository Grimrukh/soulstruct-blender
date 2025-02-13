from __future__ import annotations

__all__ = [
    "ExportMapMSB",
]

import traceback
import typing as tp
from pathlib import Path

import bpy
from io_soulstruct.general.game_config import GAME_CONFIG
from io_soulstruct.collision.types import BlenderMapCollision
from io_soulstruct.navmesh.nvm.types import BlenderNVM
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities.operators import LoggingOperator
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
from .operator_config import *
from .properties import MSBPartSubtype
from .utilities import MSB_COLLECTION_RE

if tp.TYPE_CHECKING:
    from io_soulstruct.msb.types import *
    from soulstruct.base.maps.msb.regions import BaseMSBRegion
    from soulstruct.base.maps.msb.events import BaseMSBEvent


# TODO: `ExportAnyMSB` operator.


class ExportMapMSB(LoggingOperator):

    bl_idname = "export_scene.map_msb"
    bl_label = "Export MSB"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = ("Export all Parts, Regions, and Events in active collection to a new MSB for the appropriate "
                      "map. Can also export full navmesh model NVMBND and/or full collision model HKXBHDs (DS1 only)")

    PART_SUBTYPE_ORDER = (
        MSBPartSubtype.MapPiece,
        MSBPartSubtype.Collision,  # environment event references ignored
        MSBPartSubtype.Navmesh,
        MSBPartSubtype.ConnectCollision,  # references Collision

        # These may have Draw Parents from above.
        MSBPartSubtype.Object,  # includes DummyObject
        MSBPartSubtype.Asset,
        MSBPartSubtype.Character,  # includes DummyCharacter
        MSBPartSubtype.PlayerStart,
    )

    @classmethod
    def poll(cls, context) -> bool:
        settings = cls.settings(context)
        if not GAME_CONFIG[settings.game].msb_class:
            return False  # unsupported
        if not context.collection:
            return False
        # TODO: Hack for now. Probably use an extension property for Collection marking it as an MSB.
        if not MSB_COLLECTION_RE.match(context.collection.name):
            return False
        return True

    def execute(self, context):
        settings = self.settings(context)
        export_settings = context.scene.msb_export_settings

        msb_class = settings.game_config.msb_class
        if not msb_class:
            return self.error(f"MSB class not found for game '{settings.game}'.")

        if settings.detect_map_from_collection:
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

        # First, collect all Parts, Regions, and Events in this collection, recursively.
        # We don't care about where they appear, or how they are parented. (All Parts/Regions will have their WORLD
        # transforms used, so users can parent these purely as a matter of their own convenience, even though the MSB
        # supports no such parenting. Events have no transform.)
        bl_parts = []
        bl_regions = []
        bl_events = []
        checked_names = set()

        if export_settings.skip_connect_collisions:
            self.warning("Skipping MSB Connect Collision parts as requested. Other maps will not load.")

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
                        and obj.MSB_PART.part_subtype_enum == MSBPartSubtype.ConnectCollision
                    ):
                        # Ignore Connect Collisions.
                        continue
                    bl_parts.append(obj)
                elif obj.soulstruct_type == SoulstructType.MSB_REGION:
                    bl_regions.append(obj)
                elif obj.soulstruct_type == SoulstructType.MSB_EVENT:
                    bl_events.append(obj)
                # Otherwise, ignore. We allow the user to include non-Soulstruct objects in the MSB collection.

        if render_hidden_count > 0:
            self.warning(f"Skipped {render_hidden_count} hidden objects from MSB export.")

        # Sort by natural order to match Blender hierarchy.
        bl_parts.sort(key=lambda x: natural_keys(x.name))
        bl_regions.sort(key=lambda x: natural_keys(x.name))
        bl_events.sort(key=lambda x: natural_keys(x.name))

        self.to_object_mode()

        # Create new MSB. TODO: Type-hinting DS1 for now for my own convenience.
        msb = msb_class()  # type: MSB_PTDE | MSB_DSR | MSB_DES
        msb.path = Path(f"map/{map_stem}/{map_stem}.msb")  # for internal usage

        # We add Regions first, then Parts (in careful subtype order), then Events.
        region_classes = BLENDER_MSB_REGION_TYPES[settings.game]
        region_count = 0
        for bl_region_obj in bl_regions:
            bl_region_type = region_classes[bl_region_obj.MSB_REGION.region_subtype_enum]
            bl_region = bl_region_type(bl_region_obj)  # type: IBlenderMSBRegion
            msb_region = bl_region.to_soulstruct_obj(self, context)  # type: BaseMSBRegion
            msb.add_entry(msb_region)
            region_count += 1
            # self.info(f"Added MSB Region: {msb_region.name}")

        # We add Parts next, carefully by subtype.
        part_classes = BLENDER_MSB_PART_TYPES[settings.game]  # type: dict[str, type[IBlenderMSBPart]]
        bl_and_msb_parts = []
        for bl_part_subtype in self.PART_SUBTYPE_ORDER:
            try:
                bl_part_type = part_classes[bl_part_subtype]
            except KeyError:
                continue  # not supported by this game

            # Get subtype parts. They are already sorted from above.
            bl_subtype_parts = [obj for obj in bl_parts if obj.MSB_PART.part_subtype_enum == bl_part_subtype]
            self.info(f"Adding {len(bl_subtype_parts)} {bl_part_subtype} parts.")

            # The same Blender part subtype may be exported as multiple real subtypes (e.g. Object and DummyObject) so
            # we need to detect the correct MSB list on an individual basis.
            for bl_part_obj in bl_subtype_parts:
                bl_part = bl_part_type(bl_part_obj)  # type: IBlenderMSBPart
                msb_part = bl_part.to_soulstruct_obj(self, context, map_stem, msb)  # will create and add MSB model
                msb.add_entry(msb_part)
                bl_and_msb_parts.append((bl_part, msb_part))
                # self.info(f"Added {bl_part_subtype} MSB Part: {msb_part.name}")

        # Sort all Models by name.
        for list_name in msb.get_subtype_list_names():
            if list_name.endswith("_models"):
                getattr(msb, list_name).sort_by_name()

        # Finally, we add Events.
        event_classes = BLENDER_MSB_EVENT_TYPES[settings.game]
        event_count = 0
        for bl_event_obj in bl_events:
            bl_event_type = event_classes[bl_event_obj.MSB_EVENT.event_subtype_enum]
            bl_event = bl_event_type(bl_event_obj)  # type: IBlenderMSBEvent
            msb_event = bl_event.to_soulstruct_obj(self, context, map_stem, msb)  # type: BaseMSBEvent
            msb.add_entry(msb_event)
            event_count += 1
            # self.info(f"Added {bl_event_obj.MSB_EVENT.event_subtype_enum} MSB Event: {msb_event.name}")

        # Resolve any deferred properties for Parts (e.g. Collision environment events).
        for bl_part, msb_part in bl_and_msb_parts:
            bl_part.to_soulstruct_obj_deferred(self, context, map_stem, msb, msb_part)

        # MSB is ready to write.
        relative_msb_path = settings.get_relative_msb_path(map_stem)  # will use latest MSB version

        try:
            settings.export_file(self, msb, relative_msb_path, class_name="MSB")
        except Exception as ex:
            # Do not try to export NVMBND or NVMDUMP below.
            return self.error(f"Could not export MSB. Error: {ex}")

        part_count = len(bl_and_msb_parts)

        self.info(
            f"Exported MSB {map_stem} successfully with {region_count} Regions, {event_count} Events, "
            f"{part_count} Parts, and {len(msb.get_models())} Models."
        )

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

        if export_settings.export_nvmdump and isinstance(msb, MSB_DSR):
            # Export NVMDUMP text file (DSR only).
            relative_nvmdump_path = Path(f"map/{map_stem}/{map_stem}.nvmdump")
            nvmdump = msb.get_nvmdump(map_stem)
            settings.export_text_file(self, nvmdump, relative_nvmdump_path)
            self.info(f"Exported NVMDUMP file next to NVMBND: {relative_nvmdump_path.name}")

        if export_settings.export_navmesh_models:
            bl_navmesh_type = part_classes[MSBPartSubtype.Navmesh]
            bl_navmesh_parts = [
                bl_navmesh_type(obj) for obj in bl_parts if obj.MSB_PART.part_subtype == MSBPartSubtype.Navmesh
            ]
            # NOTE: All these games use NVMBNDs.
            if settings.is_game(DEMONS_SOULS, DARK_SOULS_PTDE, DARK_SOULS_DSR):
                self.export_nvmbnd(context, map_stem, bl_navmesh_parts)
            else:
                self.warning(f"Navmesh model export not supported for game '{settings.game}'.")

        if export_settings.export_collision_models:
            bl_collision_type = part_classes[MSBPartSubtype.Collision]
            bl_collision_parts = [
                bl_collision_type(obj) for obj in bl_parts if obj.MSB_PART.part_subtype == MSBPartSubtype.Collision
            ]
            self.info(f"Exporting {len(bl_collision_parts)} Collision models (might take a few seconds).")
            if settings.is_game(DEMONS_SOULS, DARK_SOULS_PTDE):
                self.export_loose_hkxs(context, map_stem, bl_collision_parts)
            elif settings.is_game(DARK_SOULS_DSR):
                self.export_hkxbhds(context, map_stem, bl_collision_parts)
            else:
                self.warning(f"Collision model export not supported for game '{settings.game}'.")

        # NOTE: There is no option to export FLVER models, as this is slow and better done individually by user.

        return {"FINISHED"}

    def export_loose_nvms(
        self, context: bpy.types.Context, map_stem: str, bl_navmeshes: list[IBlenderMSBPart]
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
            model_stem = bl_navmesh.export_name
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

    def export_nvmbnd(self, context: bpy.types.Context, map_stem: str, bl_navmeshes: list[IBlenderMSBPart]) -> set[str]:
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

            model_stem = bl_nvm.export_name
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
        self, context: bpy.types.Context, map_stem: str, bl_collisions: list[IBlenderMSBPart]
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
            model_stem = bl_collision.export_name
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
        self, context: bpy.types.Context, map_stem: str, bl_collisions: list[IBlenderMSBPart]
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
            model_stem = bl_collision.export_name
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
