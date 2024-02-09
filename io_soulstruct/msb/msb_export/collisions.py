from __future__ import annotations

__all__ = [
    "ExportMSBCollisions",
]

import traceback
import typing as tp
from pathlib import Path

import bpy.types
from soulstruct.dcx import DCXType
from soulstruct.games import DARK_SOULS_DSR

from soulstruct_havok.wrappers.hkx2015.hkx_binder import BothResHKXBHD

from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.utilities import *
from io_soulstruct.havok.hkx_map_collision.model_export import *
from .core import *
from .settings import *

if tp.TYPE_CHECKING:
    from io_soulstruct.general.core import SoulstructSettings
    from io_soulstruct.type_checking import MSB_TYPING


class ExportMSBCollisions(LoggingOperator):
    """Export a HKX collision file into a FromSoftware DSR map directory BHD."""
    bl_idname = "export_scene_map.msb_hkx_map_collision"
    bl_label = "Export Map Collision"
    bl_description = (
        "Export transform and model of HKX map collisions into MSB and HKXBHD binder in appropriate game map (DS1R)"
    )

    @classmethod
    def poll(cls, context):
        """Must select empty parents of only (and at least one) child meshes.

        TODO: Also currently for DS1R only.
        """
        settings = cls.settings(context)
        if not settings.can_auto_export:
            return False
        if not settings.is_game(DARK_SOULS_DSR):
            return False
        if not context.selected_objects:
            return False
        for obj in context.selected_objects:
            if obj.type != "MESH":
                return False
        return True

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select a parent of one or more collision submeshes.")

        settings = self.settings(context)  # type: SoulstructSettings
        settings.save_settings()
        msb_export_settings = context.scene.msb_export_settings  # type: MSBExportSettings
        dcx_type = DCXType.DS1_DS2  # DS1R (inside HKXBHD)

        opened_msbs = {}  # type: dict[Path, MSB_TYPING]  # keys are relative MSB paths
        opened_both_res_hkxbhds = {}  # type: dict[str, BothResHKXBHD]  # keys are map stems
        edited_part_names = {}  # type: dict[str, set[str]]  # keys are MSB stems (which may differ from 'map' stems)
        return_strings = set()

        # TODO: Not a fan of how much of the code below is duplicated from the non-MSB game file exporter. Should
        #  probably use a shared operator base class that has methods for HKX model and HKXBHD handling.

        for hkx_model in context.selected_objects:
            hkx_model: bpy.types.MeshObject

            if hkx_model.name[0] not in "hl":
                self.error(f"Map collision mesh '{hkx_model.name}' must start with 'h' or 'l' to export.")
                continue

            map_stem = settings.get_map_stem_for_export(hkx_model, oldest=True)
            relative_msb_path = settings.get_relative_msb_path(map_stem)  # will use latest map version
            msb_stem = relative_msb_path.stem

            # Get model file stem from MSB (must contain matching part).
            collision_part_name = get_bl_obj_stem(hkx_model)
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

            edited_msb_part_names = edited_part_names.setdefault(msb_stem, set())
            if collision_part_name in edited_msb_part_names:
                self.warning(
                    f"Collision part '{collision_part_name}' was exported more than once among selected meshes."
                )
            edited_msb_part_names.add(collision_part_name)

            try:
                msb_part = msb.collisions.find_entry_name(collision_part_name)
            except KeyError:
                self.error(
                    f"Collision part '{collision_part_name}' not found in MSB {msb_stem} for map {map_stem}."
                )
                continue
            if not msb_part.model.name:
                self.error(
                    f"Collision part '{collision_part_name}' in MSB {msb_stem} for map {map_stem} has no model name."
                )
                continue

            model_name = find_model_name(self, hkx_model, process_model_name_map_area(map_stem))
            msb_model_name = msb_part.model.get_model_file_stem(map_stem)
            if model_name != msb_model_name:
                # We update the MSB model name even if exporting MSB data only.
                self.warning(
                    f"Updating collision model name of MSB part '{collision_part_name}' to '{model_name}'."
                )
                msb_part.model.set_name_from_model_file_stem(model_name)

            obj_to_msb_entry_transform(hkx_model, msb_part)

            if msb_export_settings.export_model_files:
                try:
                    self.export_hkx_model(hkx_model, model_name, opened_both_res_hkxbhds, settings, map_stem, dcx_type)
                except Exception as ex:
                    traceback.print_exc()
                    self.error(f"Error exporting HKX model '{model_name}' for map '{map_stem}': {ex}")

        if msb_export_settings.export_model_files:
            for map_stem, both_res_hkxbhd in opened_both_res_hkxbhds.items():
                return_strings |= settings.export_file(
                    self, both_res_hkxbhd.hi_res, Path(f"map/{map_stem}/h{map_stem}.hkxbhd")
                )
                return_strings |= settings.export_file(
                    self, both_res_hkxbhd.lo_res, Path(f"map/{map_stem}/l{map_stem}.hkxbhd")
                )

        for relative_msb_path, msb in opened_msbs.items():
            settings.export_file(self, msb, relative_msb_path)

        return {"FINISHED"} if "FINISHED" in return_strings else {"CANCELLED"}  # at least one success

    def export_hkx_model(
        self,
        hkx_model: bpy.types.MeshObject,
        model_name: str,
        opened_both_res_hkxbhds: dict[str, BothResHKXBHD],
        settings: SoulstructSettings,
        map_stem: str,
        dcx_type: DCXType,
    ):
        if model_name.startswith("h"):
            hi_name = model_name
            lo_name = f"l{model_name[1:]}"
        else:  # must start with 'l'
            hi_name = f"h{model_name[1:]}"
            lo_name = model_name

        try:
            hi_hkx, lo_hkx = export_hkx_map_collision(
                self, hkx_model, hi_name=hi_name, lo_name=lo_name, require_hi=True, use_hi_if_missing_lo=True
            )
        except Exception as ex:
            raise HKXMapCollisionExportError(f"Cannot get exported hi/lo HKX for '{hkx_model.name}'. Error: {ex}")
        hi_hkx.dcx_type = dcx_type
        lo_hkx.dcx_type = dcx_type

        if map_stem not in opened_both_res_hkxbhds:
            for res in "hl":
                for suffix in ("hkxbhd", "hkxbdt"):
                    relative_path = Path(f"map/{map_stem}/{res}{map_stem}.{suffix}")  # no DCX
                    try:
                        settings.prepare_project_file(relative_path, False, must_exist=True)
                    except FileNotFoundError as ex:
                        raise HKXMapCollisionExportError(
                            f"Could not find file '{relative_path}' for map '{map_stem}'. Error: {ex}"
                        )
            opened_both_res_hkxbhds[map_stem] = BothResHKXBHD.from_map_path(map_stem)

        opened_both_res_hkxbhds[map_stem].hi_res.set_hkx(hi_name, hi_hkx)
        opened_both_res_hkxbhds[map_stem].lo_res.set_hkx(lo_name, lo_hkx)
