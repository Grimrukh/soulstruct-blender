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
from io_soulstruct.flver import FLVERExporter
from io_soulstruct.havok.hkx_map_collision.model_export import export_hkx_map_collision, HKXMapCollisionExportError
from io_soulstruct.msb.core import MSBPartOperatorConfig
from io_soulstruct.msb.properties import MSBPartSubtype
from io_soulstruct.utilities import get_bl_obj_tight_name
from .base import *


msb_collision_operator_config = MSBPartOperatorConfig(
    PART_SUBTYPE=MSBPartSubtype.COLLISION,
    MSB_LIST_NAME="collisions",
    MSB_MODEL_LIST_NAME="collision_models",
    GAME_ENUM_NAME="collision_part",
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

    bl_idname = "export_scene_map.msb_hkx_map_collision"
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
        bl_model_obj: bpy.types.MeshObject,
        settings: SoulstructSettings,
        map_stem: str,
        flver_exporter: FLVERExporter | None = None,
        export_textures=False,
    ):
        """Export the given Blender model object to a game model file and return the path and binary data."""

        model_stem = get_bl_obj_tight_name(bl_model_obj)
        dcx_type = settings.game.get_dcx_type("hkx")  # will have DCX inside HKXBHD

        if model_stem.startswith("h"):
            hi_name = model_stem
            lo_name = f"l{model_stem[1:]}"
        elif model_stem.startswith("l"):
            hi_name = f"h{model_stem[1:]}"
            lo_name = model_stem
        else:
            raise HKXMapCollisionExportError(f"Collision model name '{model_stem}' does not start with 'h' or 'l'.")

        try:
            hi_hkx, lo_hkx = export_hkx_map_collision(
                self, bl_model_obj, hi_name=hi_name, lo_name=lo_name, require_hi=True, use_hi_if_missing_lo=True
            )
        except Exception as ex:
            raise HKXMapCollisionExportError(f"Cannot get exported hi/lo HKX for '{bl_model_obj.name}'. Error: {ex}")
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
                        raise HKXMapCollisionExportError(
                            f"Could not find file '{relative_path}' for map '{map_stem}'. Error: {ex}"
                        )
            # We start with import path Binders. If we are exporting to the project, the `prepare` calls above will have
            # created the initial Binders there already, replacing them with the current game ones if `Prefer Import
            # from Project` is disabled.
            import_map_path = settings.get_import_map_path(map_stem)
            self.opened_both_res_hkxbhds[map_stem] = BothResHKXBHD.from_map_path(import_map_path)

        self.opened_both_res_hkxbhds[map_stem].hi_res.set_hkx(hi_name, hi_hkx)
        self.opened_both_res_hkxbhds[map_stem].lo_res.set_hkx(lo_name, lo_hkx)

    def finish_model_export(self, context: bpy.types.Context, settings: SoulstructSettings):
        # Export all opened HKXBHDs.
        for map_stem, both_res_hkxbhd in self.opened_both_res_hkxbhds.items():
            settings.export_file(self, both_res_hkxbhd.hi_res, Path(f"map/{map_stem}/h{map_stem[1:]}.hkxbhd"))
            settings.export_file(self, both_res_hkxbhd.lo_res, Path(f"map/{map_stem}/l{map_stem[1:]}.hkxbhd"))
