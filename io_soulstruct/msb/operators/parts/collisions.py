"""Operators for importing `MSBCollision` entries, and their HKX models, from MSB files."""
from __future__ import annotations

__all__ = [
    "ImportMSBMapCollision",
    "ImportAllMSBMapCollisions",
    "ExportMSBCollisions",
]

from pathlib import Path
from soulstruct_havok.wrappers.hkx2015.hkx_binder import BothResHKXBHD

import bpy
from io_soulstruct import SoulstructSettings
from io_soulstruct.exceptions import MapCollisionExportError
from io_soulstruct.collision.types import BlenderMapCollision
from io_soulstruct.msb.operator_config import MSBPartOperatorConfig
from io_soulstruct.msb.properties import MSBPartSubtype
from io_soulstruct.utilities import LoggingOperator
from .base import *


msb_collision_operator_config = MSBPartOperatorConfig(
    PART_SUBTYPE=MSBPartSubtype.COLLISION,
    MSB_LIST_NAME="collisions",
    MSB_MODEL_LIST_NAMES=["collision_models"],
)


class ImportMSBMapCollision(BaseImportSingleMSBPart):
    bl_idname = "import_scene.msb_map_collision_part"
    bl_label = "Import MSB Collision Part"
    bl_description = "Import selected MSB Collision entry from selected game MSB"

    config = msb_collision_operator_config


class ImportAllMSBMapCollisions(BaseImportAllMSBParts):
    bl_idname = "import_scene.all_msb_map_collision_parts"
    bl_label = "Import All Collision Parts"
    bl_description = "Import HKX meshes and MSB transform of every MSB Collision part. Moderately slow"

    config = msb_collision_operator_config


class ExportMSBCollisions(BaseExportMSBParts):
    """Export one or more HKX collision files into a FromSoftware DSR map directory BHD."""

    bl_idname = "export_scene_map.msb_map_collision"
    bl_label = "Export Map Collision"
    bl_description = (
        "Export transform and model of HKX map collisions into MSB and HKXBHD binder in appropriate game map (DS1R)"
    )

    config = msb_collision_operator_config

    opened_both_res_hkxbhds: dict[str, BothResHKXBHD]  # keys are map stems

    @classmethod
    def poll(cls, context):
        return cls.settings(context).is_game("DARK_SOULS_DSR") and super().poll(context)

    def init(self, context, settings):
        self.opened_both_res_hkxbhds = {}

    def export_model(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_mesh: bpy.types.MeshObject,
        map_stem: str,
    ):
        """Export the given Blender model object to a game model file and return the path and binary data."""

        settings = operator.settings(context)
        dcx_type = settings.game.get_dcx_type("hkx")  # will have DCX inside HKXBHD

        bl_map_collision = BlenderMapCollision(model_mesh)

        try:
            hi_hkx, lo_hkx = bl_map_collision.to_hkx_pair(self, require_hi=True, use_hi_if_missing_lo=True)
        except Exception as ex:
            raise MapCollisionExportError(f"Cannot get exported hi/lo HKX for '{model_mesh.name}'. Error: {ex}")
        hi_hkx.dcx_type = dcx_type
        lo_hkx.dcx_type = dcx_type

        if map_stem not in self.opened_both_res_hkxbhds:
            # Open both-res HKXBHDs for this map.
            relative_map_path = Path(f"map/{map_stem}")
            for res in "hl":
                for suffix in ("hkxbhd", "hkxbdt"):
                    relative_path = relative_map_path / f"{res}{map_stem[1:]}.{suffix}"  # no DCX
                    try:
                        settings.prepare_project_file(relative_path, must_exist=True)
                    except FileNotFoundError as ex:
                        raise MapCollisionExportError(
                            f"Could not find file '{relative_path}' for map '{map_stem}'. Error: {ex}"
                        )
            # We start with import path Binders. If we are exporting to the project, the `prepare` calls above will have
            # created the initial Binders there already, replacing them with the current game ones if `Prefer Import
            # from Project` is disabled.
            try:
                import_map_dir = settings.get_import_map_dir_path(map_stem=map_stem)
            except FileNotFoundError as ex:
                raise MapCollisionExportError(
                    f"Could not find map directory with existing HKX binders for {map_stem}. Error: {ex}"
                )
            self.opened_both_res_hkxbhds[map_stem] = BothResHKXBHD.from_map_path(import_map_dir)

        # Stems set during creation.
        self.opened_both_res_hkxbhds[map_stem].hi_res.set_hkx(hi_hkx.path_stem, hi_hkx)
        self.opened_both_res_hkxbhds[map_stem].lo_res.set_hkx(lo_hkx.path_stem, lo_hkx)

    def finish_model_export(self, context: bpy.types.Context, settings: SoulstructSettings):
        # Export all opened HKXBHDs.
        for map_stem, both_res_hkxbhd in self.opened_both_res_hkxbhds.items():
            settings.export_file(self, both_res_hkxbhd.hi_res, Path(f"map/{map_stem}/h{map_stem[1:]}.hkxbhd"))
            settings.export_file(self, both_res_hkxbhd.lo_res, Path(f"map/{map_stem}/l{map_stem[1:]}.hkxbhd"))
        return {"FINISHED"}
