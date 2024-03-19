"""Operators for importing `MSBNavmesh` entries, and their NVM models, from MSB files."""
from __future__ import annotations

__all__ = [
    "ImportMSBNavmesh",
    "ImportAllMSBNavmeshes",
]

import traceback
import typing as tp

import bpy
import bpy.ops

from soulstruct.containers import Binder, EntryNotFoundError
from soulstruct.darksouls1r.maps.navmesh import NVM

from io_soulstruct.utilities import *
from io_soulstruct.navmesh.nvm.model_import import *
from .core import *

if tp.TYPE_CHECKING:
    from soulstruct.darksouls1r.maps.parts import MSBNavmesh  # TODO: use multi-game typing
    from soulstruct.base.models.mtd import MTDBND
    from io_soulstruct.general import SoulstructSettings


def find_navmesh_model(map_stem: str, model_name: str) -> bpy.types.MeshObject:
    """Find the given navmesh model in the '{map_stem} Navmesh Models' collection in the current scene."""
    collection_name = f"{map_stem} Navmesh Models"
    try:
        collection = bpy.data.collections[collection_name]
    except KeyError:
        raise MissingModelError(f"Collection '{collection_name}' not found in current scene.")
    for obj in collection.objects:
        if obj.name == model_name and obj.type == "MESH":
            return obj
    raise MissingModelError(f"Model '{model_name}' not found in '{collection_name}' collection.")


def import_navmesh_model(
    operator: LoggingOperator, context, settings: SoulstructSettings, map_stem: str, model_name: str
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

    collection = get_collection(f"{map_stem} Navmesh Models", context.scene.collection, hide_viewport=True)
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


def get_navmesh_model(
    operator: LoggingOperator, context, settings: SoulstructSettings, map_stem: str, model_name: str
) -> bpy.types.MeshObject:
    """Find or create actual Blender navmesh."""
    try:
        return find_navmesh_model(map_stem, model_name)
    except MissingModelError:
        nvm_model = import_navmesh_model(operator, context, settings, map_stem, model_name)
        return nvm_model


def create_navmesh_model_instance(
    nvm_model: bpy.types.MeshObject,
    linked_name: str,
    collection: bpy.types.Collection,
) -> bpy.types.MeshObject:
    """Create new Mesh linked to model mesh."""
    nvm_instance = bpy.data.objects.new(linked_name, nvm_model.data)
    nvm_instance["Model Name"] = nvm_model.name
    collection.objects.link(nvm_instance)
    # noinspection PyTypeChecker
    return nvm_instance


class BaseImportMSBNavmesh(BaseImportMSBPart):

    PART_TYPE_NAME = "Navmesh"
    PART_TYPE_NAME_PLURAL = "Navmeshes"
    MSB_LIST_NAME = "navmeshes"
    USE_LATEST_MAP_FOLDER = True

    def _create_part_instance(
        self,
        context,
        settings: SoulstructSettings,
        map_stem: str,
        part: MSBNavmesh,
        collection: bpy.types.Collection,
        mtdbnd: MTDBND | None = None,
    ) -> bpy.types.Object:
        model_name = part.model.get_model_file_stem(map_stem)
        nvm_model = get_navmesh_model(self, context, settings, map_stem, model_name)
        nvm_instance = create_navmesh_model_instance(nvm_model, part.name, collection)
        msb_entry_to_obj_transform(part, nvm_instance)
        return nvm_instance  # only return root object


class ImportMSBNavmesh(BaseImportMSBNavmesh):
    """Import a NVM from the current selected value of listed game MSB navmesh entries."""
    bl_idname = "import_scene.msb_navmesh_part"
    bl_label = "Import Navmesh Part"
    bl_description = "Import transform and model of selected Navmesh MSB part from selected game map"

    GAME_ENUM_NAME = "navmesh_part"

    def execute(self, context):
        return self.import_enum_part(context)


class ImportAllMSBNavmeshes(BaseImportMSBNavmesh):
    """Import a NVM from the current selected value of listed game MSB navmesh entries."""
    bl_idname = "import_scene.all_msb_navmesh_parts"
    bl_label = "Import All Navmesh Parts"
    bl_description = "Import NVM mesh and MSB transform of every MSB Navmesh part. Still quite fast"

    GAME_ENUM_NAME = None

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    # TODO: used to warn when the same navmesh model was used by multiple MSB parts:
    # if navmesh_part.model.name in used_model_names:
    #     first_part = used_model_names[navmesh_part.model.name]
    #     self.warning(
    #         f"MSB navmesh part '{navmesh_part.name}' uses model '{navmesh_part.model.name}', which has "
    #         f"already been loaded from MSB part '{first_part}'. No two MSB Navmesh parts should use the same "
    #         f"NVM asset; try duplicating the NVM and and change the MSB model name first."
    #     )
    #     continue
    # else:
    #     used_model_names[navmesh_part.model.name] = part_name

    def execute(self, context):
        return self.import_all_parts(context)
