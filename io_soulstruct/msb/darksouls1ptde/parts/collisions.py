from __future__ import annotations

__all__ = [
    "BlenderMSBCollision",
]

import traceback

import bpy
from io_soulstruct.exceptions import MissingPartModelError
from io_soulstruct.general.core import SoulstructSettings
from io_soulstruct.havok.hkx_map_collision.model_import import *
from io_soulstruct.utilities import LoggingOperator, get_collection
from soulstruct.darksouls1ptde.maps.enums import CollisionHitFilter
from soulstruct.darksouls1ptde.maps.parts import MSBCollision
from soulstruct_havok.wrappers.hkx2015.hkx_binder import BothResHKXBHD
from .base import BlenderMSBPart
from io_soulstruct.msb.properties import MSBPartSubtype, MSBCollisionProps


class BlenderMSBCollision(BlenderMSBPart):
    """Not FLVER-based."""

    PART_SUBTYPE = MSBPartSubtype.COLLISION

    @property
    def collision_props(self) -> MSBCollisionProps:
        return self.obj.msb_collision_props

    @classmethod
    def find_model(cls, model_name: str, map_stem: str) -> bpy.types.MeshObject:
        """Find the model of the given type in the 'Map Collision Models' collection in the current scene.

        Returns the Empty parent of all 'h' and 'l' submeshes of the collision (`children`).
        """
        collection_name = f"{map_stem} Collision Models"
        try:
            collection = bpy.data.collections[collection_name]
        except KeyError:
            raise MissingPartModelError(f"Collection '{collection_name}' not found in current scene.")
        for obj in collection.objects:
            if obj.name == model_name and obj.type == "MESH":
                return obj
        raise MissingPartModelError(f"Collision model mesh '{model_name}' not found in '{collection_name}' collection.")

    @classmethod
    def import_model(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        model_name: str,
        map_stem: str,
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
            hkx_model = import_hkx_model_merged(hi_hkx, model_name=model_name, lo_hkx=lo_hkx)
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            raise HKXMapCollisionImportError(
                f"Cannot import HKX '{model_name}' from HKXBHDs in map {map_stem}. Error: {ex}"
            )
        collection.objects.link(hkx_model)
        for child in hkx_model.children:
            collection.objects.link(child)

        # TODO: HKX import is so fast that this just slows the console down when importing all collisions.
        # operator.info(f"Imported HKX '{hkx_model.name}' from model '{model_name}' in map {map_stem}.")

        return hkx_model

    def set_properties(self, operator: LoggingOperator, part: MSBCollision):
        super().set_properties(operator, part)
        props = self.obj.msb_collision_props

        for i in part.navmesh_groups:
            if 0 <= i < 32:
                props.navmesh_groups_0[i] = True
            elif 32 <= i < 64:
                props.navmesh_groups_1[i - 32] = True
            elif 64 <= i < 96:
                props.navmesh_groups_2[i - 64] = True
            elif 96 <= i < 128:
                props.navmesh_groups_3[i - 96] = True

        props.vagrant_entity_id_0 = part.vagrant_entity_ids[0]
        props.vagrant_entity_id_1 = part.vagrant_entity_ids[1]
        props.vagrant_entity_id_2 = part.vagrant_entity_ids[2]

        for prop_name in props.__annotations__:
            if prop_name.startswith("navmesh_groups_") or prop_name.startswith("vagrant_entity_id_"):
                continue  # handled above

            if prop_name == "hit_filter":
                # Redirect int value to enum name.
                props.hit_filter = CollisionHitFilter(part.hit_filter_id).name
            elif prop_name == "environment_event_name":
                # Redirect environment event to name.
                # TODO: Could potentially automate, or store event position + unknown data on Collision object itself.
                props.environment_event_name = part.environment_event.name if part.environment_event else ""
            else:
                setattr(props, prop_name, getattr(part, prop_name))
