"""Operators for importing `MSBCollision` entries, and their HKX models, from MSB files."""
from __future__ import annotations

__all__ = [
    "ImportMSBMapCollision",
    "ImportAllMSBMapCollisions",
]

import time
import traceback
import typing as tp

import bpy
import bpy.ops

from soulstruct_havok.wrappers.hkx2015.hkx_binder import BothResHKXBHD

from io_soulstruct.utilities import *
from io_soulstruct.havok.hkx_map_collision.model_import import *
from .core import *

if tp.TYPE_CHECKING:
    from soulstruct.darksouls1r.maps.parts import MSBCollision  # TODO: use multi-game typing
    from soulstruct.base.models.mtd import MTDBND
    from io_soulstruct.general import SoulstructSettings


def find_map_collision_model(map_stem: str, model_name: str) -> bpy.types.MeshObject:
    """Find the model of the given type in the 'Map Collision Models' collection in the current scene.

    Returns the Empty parent of all 'h' and 'l' submeshes of the collision (`children`).
    """
    collection_name = f"{map_stem} Collision Models"
    try:
        collection = bpy.data.collections[collection_name]
    except KeyError:
        raise MissingModelError(f"Collection '{collection_name}' not found in current scene.")
    for obj in collection.objects:
        if obj.name == model_name and obj.type == "MESH":
            return obj
    raise MissingModelError(f"Collision model mesh '{model_name}' not found in '{collection_name}' collection.")


def import_collision_model(
    operator: LoggingOperator, context, settings: SoulstructSettings, map_stem: str, model_name: str
) -> bpy.types.MeshObject:
    """Import the Map Collison HKX model of the given name into a collection in the current scene.

    NOTE: `map_stem` should already be set to oldest version if option is enabled. This function is agnostic.
    """

    # NOTE: Hi and lo-res binders could come from different import folders (project vs. game).
    hi_res_hkxbhd_path = settings.get_import_map_path(f"h{map_stem[1:]}.hkxbhd")
    lo_res_hkxbhd_path = settings.get_import_map_path(f"l{map_stem[1:]}.hkxbhd")
    both_res_hkxbhd = BothResHKXBHD.from_both_paths(hi_res_hkxbhd_path, lo_res_hkxbhd_path)
    hi_hkx, lo_hkx = both_res_hkxbhd.get_both_hkx(model_name)
    collection = get_collection(f"{map_stem} Collision Models", context.scene.collection)

    # Import single HKX.
    try:
        hkx_model = import_hkx_model(hi_hkx, model_name=model_name, lo_hkx=lo_hkx)
    except Exception as ex:
        traceback.print_exc()  # for inspection in Blender console
        raise HKXMapCollisionImportError(
            f"Cannot import HKX '{model_name}' from HKXBHDs in map {map_stem}. Error: {ex}"
        )
    collection.objects.link(hkx_model)

    # TODO: HKX import is so fast that this just slows the console down when importing all collisions.
    # operator.info(f"Imported HKX '{hkx_model.name}' from model '{model_name}' in map {map_stem}.")

    return hkx_model

def get_collision_model(
    operator: LoggingOperator, context, settings: SoulstructSettings, map_stem: str, model_name: str
) -> bpy.types.MeshObject:
    """Find or create actual Blender collision model mesh."""
    try:
        return find_map_collision_model(map_stem, model_name)
    except MissingModelError:
        hkx_model = import_collision_model(operator, context, settings, map_stem, model_name)
        return hkx_model


def create_collision_model_instance(
    hkx_model: bpy.types.MeshObject,
    linked_name: str,
    collection: bpy.types.Collection,
) -> bpy.types.MeshObject:
    """Create linked HKX model instance mesh."""
    # noinspection PyTypeChecker
    hkx_instance = bpy.data.objects.new(linked_name, hkx_model.data)  # type: bpy.types.MeshObject
    hkx_instance["Model Name"] = hkx_model.name
    collection.objects.link(hkx_instance)
    return hkx_instance


class BaseImportMSBCollision(BaseImportMSBPart):

    PART_TYPE_NAME = "Collision"
    PART_TYPE_NAME_PLURAL = "Collisions"
    MSB_LIST_NAME = "collisions"

    def _create_part_instance(
        self,
        context,
        settings: SoulstructSettings,
        map_stem: str,
        part: MSBCollision,
        collection: bpy.types.Collection,
        mtdbnd: MTDBND | None = None,
    ) -> bpy.types.Object:
        model_name = part.model.get_model_file_stem(map_stem)
        hkx_model = get_collision_model(self, context, settings, map_stem, model_name)
        hkx_instance = create_collision_model_instance(hkx_model, part.name, collection)
        msb_entry_to_obj_transform(part, hkx_instance)
        return hkx_instance


class ImportMSBMapCollision(BaseImportMSBCollision):
    bl_idname = "import_scene.msb_map_collision_part"
    bl_label = "Import MSB Collision Part"
    bl_description = "Import selected MSB Collision entry from selected game MSB"

    GAME_ENUM_NAME = "hkx_map_collision_part"

    def execute(self, context):
        return self.import_enum_part(context)


class ImportAllMSBMapCollisions(BaseImportMSBCollision):
    bl_idname = "import_scene.all_msb_map_collision_parts"
    bl_label = "Import All Collision Parts"
    bl_description = "Import HKX meshes and MSB transform of every MSB Collision part. Moderately slow"

    GAME_ENUM_NAME = None

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        return self.import_all_parts(context)
