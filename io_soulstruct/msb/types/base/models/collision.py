from __future__ import annotations

__all__ = [
    "BlenderMSBCollisionModelImporter",
]

import traceback
from dataclasses import dataclass

import bpy

from soulstruct.containers import EntryNotFoundError
from soulstruct_havok.fromsoft.shared import BothResHKXBHD, MapCollisionModel

from io_soulstruct import SoulstructSettings
from io_soulstruct.collision.types import BlenderMapCollision
from io_soulstruct.exceptions import MapCollisionImportError
from io_soulstruct.utilities import find_or_create_collection, LoggingOperator

from .base import BaseBlenderMSBModelImporter, MODEL_T


@dataclass(slots=True)
class BlenderMSBCollisionModelImporter(BaseBlenderMSBModelImporter):
    """This class is concrete, as it only needs to support games that use loose files vs. HKXBHD binders."""

    uses_loose: bool = False

    def import_model_mesh(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_name: str,
        map_stem: str,
        model_collection: bpy.types.Collection = None,
    ) -> bpy.types.MeshObject:
        """Import the Map Collison HKX model of the given name into a collection in the current scene.

        NOTE: `map_stem` should already be set to oldest version if option is enabled. This function is agnostic.
        """
        settings = operator.settings(context)

        if not model_collection:
            model_collection = self._get_collision_model_map_collection(context, map_stem)

        if self.uses_loose:
            hi_collision, lo_collision = self._get_hi_lo_collisions_loose(settings, model_name, map_stem)
        else:
            hi_collision, lo_collision = self._get_hi_lo_collisions_hkxbhd(operator, settings, model_name, map_stem)

        # Import single HKX.
        try:
            return BlenderMapCollision.new_from_soulstruct_obj(
                operator,
                context,
                hi_collision,
                model_name,
                collection=model_collection,
                lo_collision=lo_collision,
            ).obj
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            raise MapCollisionImportError(
                f"Cannot import Collision model '{model_name}' from {'loose HKXs' if self.uses_loose else 'HKXBHDs'} "
                f"in map {map_stem}. Error: {ex}"
            )

    def batch_import_model_meshes(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        models: list[MODEL_T],
        map_stem: str,
        model_collection: bpy.types.Collection = None,
    ) -> None:
        """Import all models for a batch of MSB Collisions, as needed, in parallel as much as possible.

        Quite simple, but (for DSR) means we only need to read the HKXBHD once.
        """
        if not model_collection:
            model_collection = self._get_collision_model_map_collection(context, map_stem)

        if self.uses_loose:
            self._batch_import_model_meshes_from_loose(operator, context, models, map_stem, model_collection)
        else:
            self._batch_import_model_meshes_from_hkxbhd(operator, context, models, map_stem, model_collection)

    def _handle_missing_hkx(self, operator, model_name: str, map_stem: str):
        """Can be overridden to handle specific missing models (e.g. known DSR vanilla mistakes)."""
        operator.error(
            f"(Batch) Cannot find Collision model '{model_name}' in {'loose HKXs' if self.uses_loose else 'HKXBHDs'} "
            f"in map {map_stem}."
        )

    @staticmethod
    def _get_collision_model_map_collection(context: bpy.types.Context, map_stem: str) -> bpy.types.Collection:
        return find_or_create_collection(
            context.scene.collection,
            "Models",
            f"{map_stem} Models",
            f"{map_stem} Collision Models",
        )

    @staticmethod
    def _get_hi_lo_collisions_loose(
        settings: SoulstructSettings, model_name: str, map_stem: str
    ) -> tuple[MapCollisionModel, MapCollisionModel]:
        hi_res_hkx_name = f"h{model_name[1:]}.hkx"
        try:
            hi_res_hkx_path = settings.get_import_map_file_path(hi_res_hkx_name)
        except FileNotFoundError:
            raise FileNotFoundError(f"Cannot find hi-res HKX '{hi_res_hkx_name}' for map {map_stem}.")
        lo_res_hkx_name = f"l{model_name[1:]}.hkx"
        try:
            lo_res_hkx_path = settings.get_import_map_file_path(lo_res_hkx_name)
        except FileNotFoundError:
            raise FileNotFoundError(f"Cannot find lo-res HKX '{lo_res_hkx_name}' for map {map_stem}.")

        try:
            hi_collision = MapCollisionModel.from_path(hi_res_hkx_path)
        except Exception as ex:
            raise MapCollisionImportError(
                f"Cannot load hi-res HKX '{hi_res_hkx_name}' from map {map_stem}. Error: {ex}"
            )
        try:
            lo_collision = MapCollisionModel.from_path(lo_res_hkx_path)
        except Exception as ex:
            raise MapCollisionImportError(
                f"Cannot load lo-res HKX '{lo_res_hkx_name}' from map {map_stem}. Error: {ex}"
            )

        return hi_collision, lo_collision

    def _get_hi_lo_collisions_hkxbhd(
        self, operator: LoggingOperator, settings: SoulstructSettings, model_name: str, map_stem: str
    ):
        """NOTE: This will decompress and read the full HKXBHDs every time it is called, so prefer batch if possible."""
        try:
            hi_res_hkxbhd_path = settings.get_import_map_file_path(f"h{map_stem[1:]}.hkxbhd")
        except FileNotFoundError:
            raise FileNotFoundError(f"Cannot find hi-res HKXBHD for map {map_stem}.")
        try:
            lo_res_hkxbhd_path = settings.get_import_map_file_path(f"l{map_stem[1:]}.hkxbhd")
        except FileNotFoundError:
            raise FileNotFoundError(f"Cannot find lo-res HKXBHD for map {map_stem}.")

        both_res_hkxbhd = BothResHKXBHD.from_both_paths(hi_res_hkxbhd_path, lo_res_hkxbhd_path)
        try:
            return both_res_hkxbhd.get_both_hkx(model_name)
        except FileNotFoundError:
            self._handle_missing_hkx(operator, model_name, map_stem)
            raise  # can't be handled

    def _batch_import_model_meshes_from_loose(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        models: list[MODEL_T],
        map_stem: str,
        model_collection: bpy.types.Collection = None,
    ):
        imported_model_names = set()

        for model in models:
            model_name = model.get_model_file_stem(map_stem)
            if model_name in imported_model_names:
                continue
            imported_model_names.add(model_name)
            try:
                self.import_model_mesh(operator, context, model_name, map_stem, model_collection)
            except Exception as ex:
                operator.error(
                    f"(Batch) Cannot import Collision model '{model_name}' from loose HKXs in map {map_stem}. "
                    f"Error: {ex}"
                )

    def _batch_import_model_meshes_from_hkxbhd(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        models: list[MODEL_T],
        map_stem: str,
        model_collection: bpy.types.Collection = None,
    ) -> None:
        """Import all models from the same `BothResHKXBHD`.

        Hi and lo-res binders could end up being found in different import folders (project vs. game).

        SPECIAL NOTE: In m12_00_00_00 (Darkroot Garden), in DSR only, there is a new Collision model h0125B0 with
        corresponding MSB entry h0125B0_0000. This is a new model that is not present in PTDE, and it is only present in
        the m12_00_00_01 (new) HKXBHD binders - and because of that, it DOES NOT LOAD in-game. In other words, this is a
        botch job by QLOC. The guilty model will be correctly reported as missing here too. (The model itself is just a
        copy of h0017B0, the DLC portal collision, with new groups.)
        """
        settings = operator.settings(context)

        imported_model_names = set()

        try:
            hi_res_hkxbhd_path = settings.get_import_map_file_path(f"h{map_stem[1:]}.hkxbhd")
        except FileNotFoundError:
            raise FileNotFoundError(f"Cannot find hi-res HKXBHD for map {map_stem}.")
        try:
            lo_res_hkxbhd_path = settings.get_import_map_file_path(f"l{map_stem[1:]}.hkxbhd")
        except FileNotFoundError:
            raise FileNotFoundError(f"Cannot find lo-res HKXBHD for map {map_stem}.")

        both_res_hkxbhd = BothResHKXBHD.from_both_paths(hi_res_hkxbhd_path, lo_res_hkxbhd_path)

        for model in models:
            model_name = model.get_model_file_stem(map_stem)

            if model_name in imported_model_names:
                continue
            imported_model_names.add(model_name)

            try:
                hi_collision, lo_collision = both_res_hkxbhd.get_both_hkx(model_name)
            except EntryNotFoundError:
                self._handle_missing_hkx(operator, model_name, map_stem)
                continue
            except Exception as ex:
                operator.error(
                    f"(Batch) Cannot load Collision model '{model_name}' from HKXBHDs in map {map_stem}. Error: {ex}"
                )
                continue

            try:
                BlenderMapCollision.new_from_soulstruct_obj(
                    operator,
                    context,
                    hi_collision,
                    model_name,
                    collection=model_collection,
                    lo_collision=lo_collision,
                )
            except Exception as ex:
                traceback.print_exc()  # for inspection in Blender console
                operator.error(
                    f"(Batch) Cannot import Collision model '{model_name}' from HKXBHDs in map {map_stem}. Error: {ex}"
                )
                # We continue with other models.
