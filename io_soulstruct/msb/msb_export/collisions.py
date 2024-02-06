from __future__ import annotations

__all__ = [
    "ExportMSBCollisions",
]

import traceback
import typing as tp
from pathlib import Path

from soulstruct.containers import Binder
from soulstruct.dcx import DCXType
from soulstruct.games import DARK_SOULS_DSR

from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.utilities import *
from io_soulstruct.havok.hkx_map_collision.model_export import *
from .core import *
from .settings import *

if tp.TYPE_CHECKING:
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
            if obj.type != "EMPTY":
                return False
            if not obj.children:
                return False
            if not all(child.type == "MESH" for child in obj.children):
                return False
        return True

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select a parent of one or more collision submeshes.")

        settings = self.settings(context)
        settings.save_settings()
        msb_export_settings = context.scene.msb_export_settings  # type: MSBExportSettings

        export_kwargs = dict(
            operator=self,
            context=context,
            dcx_type=DCXType.DS1_DS2,  # DS1R (inside HKXBHD)
            default_entry_path="{map}\\{name}.hkx.dcx",  # DS1R
            default_entry_flags=0x2,
            overwrite_existing=True,
        )

        opened_msbs = {}  # type: dict[Path, MSB_TYPING]  # keys are relative MSB paths
        opened_hkxbhds = {"h": {}, "l": {}}  # type: dict[str, dict[Path, Binder]]  # keys are relative HKXBHD paths
        edited_part_names = {}  # type: dict[str, set[str]]  # keys are MSB stems (which may differ from 'map' stems)
        return_strings = set()

        for hkx_parent in context.selected_objects:

            res = hkx_parent.name[0]
            if res not in "hl":
                self.error(f"Selected object '{hkx_parent.name}' must start with 'h' or 'l' to export.")
                continue

            map_stem = settings.get_map_stem_for_export(hkx_parent, oldest=True)
            relative_msb_path = settings.get_relative_msb_path(map_stem)  # will use latest map version
            msb_stem = relative_msb_path.stem

            # Get model file stem from MSB (must contain matching part).
            collision_part_name = get_bl_obj_stem(hkx_parent)
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

            model_name = hkx_parent.get("Model Name", None) if msb_export_settings.prefer_new_model_name else None
            if not model_name:  # could be None or empty string
                # Use existing MSB model name.
                model_name = msb_part.model.get_model_file_stem(map_stem)
            else:
                # Update MSB model name.
                msb_part.model.set_name_from_model_file_stem(model_name)

            edited_msb_part_names = edited_part_names.setdefault(msb_stem, set())
            if collision_part_name in edited_msb_part_names:
                self.warning(
                    f"Navmesh part '{collision_part_name}' was exported more than once in selected meshes."
                )
            edited_msb_part_names.add(collision_part_name)

            # Warn if HKX stem in MSB is unexpected. (Only reachable if `prefer_new_model_name = False`.)
            if (model_file_stem := hkx_parent.get("Model Name", None)) is not None:
                if model_file_stem != model_name:
                    self.warning(
                        f"Collision part '{model_name}' in MSB {msb_stem} for map {map_stem} has model name "
                        f"'{msb_part.model.name}' but Blender mesh 'Model Name' is '{model_file_stem}'. "
                        f"Prioritizing HKX stem from MSB model name; you may want to update the Blender mesh."
                    )

            obj_to_msb_entry_transform(hkx_parent, msb_part)

            if not msb_export_settings.export_msb_data_only:
                try:
                    bl_meshes, other_res_bl_meshes, other_res = get_mesh_children(self, hkx_parent, True)
                except HKXMapCollisionExportError as ex:
                    self.error(f"Children of object '{hkx_parent}' cannot be exported. Error: {ex}")
                    continue

                if res == "h":
                    res_meshes = {
                        "h": bl_meshes,
                        "l": other_res_bl_meshes,
                    }
                else:
                    # Swap res and meshes.
                    res_meshes = {
                        "h": other_res_bl_meshes,
                        "l": bl_meshes,
                    }

                for r in "hl":
                    meshes = res_meshes[r]
                    res_entry_stem = f"{r}{model_name[1:]}"
                    if not meshes:
                        continue
                    opened_res_hkxbhds = opened_hkxbhds[r]
                    relative_hkxbhd_path = Path(f"map/{map_stem}/{r}{map_stem[1:]}.hkxbhd")  # no DCX
                    if relative_hkxbhd_path not in opened_res_hkxbhds:
                        try:
                            hkxbhd_path = settings.prepare_project_file(relative_hkxbhd_path, False, must_exist=True)
                        except FileNotFoundError as ex:
                            return self.error(
                                f"Could not find HKXBHD file '{relative_hkxbhd_path}' for map '{map_stem}'. Error: {ex}"
                            )

                        relative_hkxbdt_path = Path(f"map/{map_stem}/{r}{map_stem[1:]}.hkxbdt")  # no DCX
                        try:
                            # Returned path of BDT not needed.
                            settings.prepare_project_file(relative_hkxbdt_path, False, must_exist=True)
                        except FileNotFoundError as ex:
                            return self.error(
                                f"Could not find HKXBDT file '{relative_hkxbdt_path}' for map '{map_stem}'. "
                                f"Error: {ex}"
                            )

                        opened_res_hkxbhds[relative_hkxbhd_path] = Binder.from_path(hkxbhd_path)

                    hkxbhd = opened_res_hkxbhds[relative_hkxbhd_path]

                    try:
                        export_hkx_to_binder(
                            bl_meshes=meshes,
                            hkxbhd=hkxbhd,
                            hkx_entry_stem=res_entry_stem,
                            map_stem=map_stem,
                            **export_kwargs,
                        )
                        self.info(f"Exported HKX '{res_entry_stem}' to '{relative_hkxbhd_path}'")
                    except Exception as ex:
                        traceback.print_exc()
                        self.error(f"Could not execute HKX export to Binder. Error: {ex}")

        for opened_res_hkxbhds in opened_hkxbhds.values():
            for relative_hkxbhd_path, hkxbhd in opened_res_hkxbhds.items():
                # Sort entries by name.
                hkxbhd.entries.sort(key=lambda e: e.name)
                return_strings |= settings.export_file(self, hkxbhd, relative_hkxbhd_path)

        for relative_msb_path, msb in opened_msbs.items():
            settings.export_file(self, msb, relative_msb_path)

        return {"FINISHED"} if "FINISHED" in return_strings else {"CANCELLED"}  # at least one success
