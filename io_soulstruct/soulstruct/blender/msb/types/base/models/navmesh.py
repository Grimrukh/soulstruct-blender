from __future__ import annotations

__all__ = [
    "BlenderMSBNavmeshModelImporter",
]

import re
import traceback

import bpy

from soulstruct.containers import Binder, EntryNotFoundError
from soulstruct.base.maps.navmesh.nvm import NVM

from soulstruct.blender.exceptions import NVMImportError
from soulstruct.blender.navmesh.nvm.types import BlenderNVM
from soulstruct.blender.utilities import LoggingOperator, find_or_create_collection

from .base import BaseBlenderMSBModelImporter, MODEL_T


class BlenderMSBNavmeshModelImporter(BaseBlenderMSBModelImporter):

    @classmethod
    def import_model_mesh(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_name: str,
        map_stem: str,
        model_collection: bpy.types.Collection = None,
    ) -> bpy.types.MeshObject:
        """Import the Navmesh NVM model of the given name into a collection in the current scene.

        NOTE: `map_stem` should already be set to latest version if option is enabled. This function is agnostic.
        """
        settings = operator.settings(context)

        try:
            nvmbnd_path = settings.get_import_map_file_path(f"{map_stem}.nvmbnd")
        except FileNotFoundError:
            raise NVMImportError(f"Could not find NVMBND file for map {map_stem}.")

        nvm_entry_name = model_name + ".nvm"  # no DCX in any games that use NVM
        nvmbnd = Binder.from_path(nvmbnd_path)
        try:
            nvm_entry = nvmbnd.find_entry_matching_name(nvm_entry_name, flags=re.IGNORECASE, escape=True)
        except EntryNotFoundError:
            raise NVMImportError(f"Could not find NVM entry '{nvm_entry_name}' in NVMBND file '{nvmbnd_path.name}'.")

        nvm = nvm_entry.to_binary_file(NVM)

        if not model_collection:
            model_collection = find_or_create_collection(
                context.scene.collection,
                "Models",
                f"{map_stem} Models",
                f"{map_stem} Navmesh Models",
            )

        try:
            bl_nvm = BlenderNVM.new_from_soulstruct_obj(
                operator,
                context,
                nvm,
                model_name,
                collection=model_collection,
            )
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            raise NVMImportError(f"Cannot import NVM: {model_name}. Error: {ex}")

        bl_nvm.set_face_materials(nvm)
        # Don't create quadtree boxes.
        bl_nvm.obj.show_wire = True

        # NVM import is so fast that this just slows the console down when importing all navmeshes.
        # operator.info(f"Imported NVM model {import_info.model_file_stem} as '{import_info.bl_name}'.")

        return bl_nvm.obj

    @classmethod
    def batch_import_model_meshes(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        models: list[MODEL_T],
        map_stem: str,
    ):
        """Import all models for a batch of MSB Navmeshes, as needed, in parallel as much as possible.

        Quite simple, but means we only need to read the NVMBND once.
        """
        settings = operator.settings(context)

        model_collection = find_or_create_collection(
            context.scene.collection,
            "Models",
            f"{map_stem} Models",
            f"{map_stem} Navmesh Models",
        )

        imported_model_names = set()

        try:
            nvmbnd_path = settings.get_import_map_file_path(f"{map_stem}.nvmbnd")
        except FileNotFoundError:
            raise FileNotFoundError(f"Cannot find NVMBND for map {map_stem}.")

        nvmbnd_class = settings.game_config.nvmbnd_class

        nvmbnd = nvmbnd_class.from_path(nvmbnd_path)

        for model in models:
            model_name = model.get_model_file_stem(map_stem)

            if model_name in imported_model_names:
                continue
            imported_model_names.add(model_name)

            nvm = nvmbnd.get_nvm(model_name)

            try:
                bl_nvm = BlenderNVM.new_from_soulstruct_obj(
                    operator,
                    context,
                    nvm,
                    model_name,
                    collection=model_collection,
                )
            except Exception as ex:
                traceback.print_exc()  # for inspection in Blender console
                raise NVMImportError(
                    f"Cannot import NVM '{model_name}' from NVMBND in map {map_stem}. Error: {ex}"
                )

            bl_nvm.set_face_materials(nvm)
            # Don't create quadtree boxes.
            bl_nvm.obj.show_wire = True
