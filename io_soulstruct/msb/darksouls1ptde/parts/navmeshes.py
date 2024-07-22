from __future__ import annotations

__all__ = [
    "BlenderMSBNavmesh",
]

import traceback

import bpy
from io_soulstruct.exceptions import NVMImportError, MissingPartModelError
from io_soulstruct.general.core import SoulstructSettings
from io_soulstruct.navmesh.nvm.model_import import NVMImportInfo, NVMImporter
from io_soulstruct.utilities import LoggingOperator, get_collection
from soulstruct.containers import Binder, EntryNotFoundError
from soulstruct.darksouls1r.maps.navmesh.nvm import NVM
from soulstruct.darksouls1r.maps.parts import MSBNavmesh
from .base import BlenderMSBPart
from io_soulstruct.msb.properties import MSBPartSubtype, MSBNavmeshProps


class BlenderMSBNavmesh(BlenderMSBPart):
    """Not FLVER-based."""

    PART_SUBTYPE = MSBPartSubtype.NAVMESH

    @property
    def navmesh_props(self) -> MSBNavmeshProps:
        return self.obj.msb_navmesh_props

    @classmethod
    def find_model(cls, model_name: str, map_stem: str) -> bpy.types.MeshObject:
        """Find the given navmesh model in the '{map_stem} Navmesh Models' collection in the current scene."""
        collection_name = f"{map_stem} Navmesh Models"
        try:
            collection = bpy.data.collections[collection_name]
        except KeyError:
            raise MissingPartModelError(f"Collection '{collection_name}' not found in current scene.")
        for obj in collection.objects:
            if obj.name == model_name and obj.soulstruct_type == "NAVMESH":
                return obj
        raise MissingPartModelError(f"Navmesh model '{model_name}' not found in '{collection_name}' collection.")

    @classmethod
    def import_model(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        model_name: str,
        map_stem: str,
    ) -> bpy.types.MeshObject:
        """Import the Navmesh NVM model of the given name into a collection in the current scene.

        NOTE: `map_stem` should already be set to latest version if option is enabled. This function is agnostic.
        """
        if not settings.get_import_map_path():  # validation
            raise NVMImportError(
                "Game directory and map stem must be set in Blender's Soulstruct global settings."
            )

        nvmbnd_path = settings.get_import_map_path(f"{map_stem}.nvmbnd")
        if not nvmbnd_path or not nvmbnd_path.is_file():
            raise NVMImportError(f"Could not find NVMBND file for map '{map_stem}': {nvmbnd_path}")

        nvm_entry_name = model_name + ".nvm"  # no DCX in DSR
        nvmbnd = Binder.from_path(nvmbnd_path)
        try:
            nvm_entry = nvmbnd.find_entry_name(nvm_entry_name)
        except EntryNotFoundError:
            raise NVMImportError(f"Could not find NVM entry '{nvm_entry_name}' in NVMBND file '{nvmbnd_path.name}'.")

        import_info = NVMImportInfo(
            nvmbnd_path, nvm_entry.minimal_stem, model_name, nvm_entry.to_binary_file(NVM)
        )

        collection = get_collection(f"{map_stem} Navmesh Models", context.scene.collection)
        importer = NVMImporter(operator, context, collection=collection)

        try:
            nvm_model = importer.import_nvm(
                import_info,
                use_material=True,
                create_quadtree_boxes=False,
            )
        except Exception as ex:
            # Delete any objects created prior to exception.
            for obj in importer.all_bl_objs:
                bpy.data.objects.remove(obj)
            traceback.print_exc()  # for inspection in Blender console
            raise NVMImportError(f"Cannot import NVM: {import_info.path}. Error: {ex}")

        # TODO: NVM import is so fast that this just slows the console down when importing all navmeshes.
        # operator.info(f"Imported NVM model {import_info.model_file_stem} as '{import_info.bl_name}'.")

        return nvm_model

    def set_properties(self, operator: LoggingOperator, part: MSBNavmesh):
        super().set_properties(operator, part)
        props = self.obj.msb_navmesh_props

        for i in part.navmesh_groups:
            if 0 <= i < 32:
                props.navmesh_groups_0[i] = True
            elif 32 <= i < 64:
                props.navmesh_groups_1[i - 32] = True
            elif 64 <= i < 96:
                props.navmesh_groups_2[i - 64] = True
            elif 96 <= i < 128:
                props.navmesh_groups_3[i - 96] = True
