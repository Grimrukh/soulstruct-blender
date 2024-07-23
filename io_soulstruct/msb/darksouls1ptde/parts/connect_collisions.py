from __future__ import annotations

__all__ = [
    "BlenderMSBConnectCollision",
]

import traceback

import bpy
from io_soulstruct.exceptions import MissingPartModelError, MSBPartExportError
from io_soulstruct.general.core import SoulstructSettings
from io_soulstruct.havok.hkx_map_collision.model_import import *
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import *
from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.parts import MSBConnectCollision
from soulstruct_havok.wrappers.hkx2015.hkx_binder import BothResHKXBHD
from .base import BlenderMSBPart
from io_soulstruct.msb.properties import MSBPartSubtype, MSBConnectCollisionProps


class BlenderMSBConnectCollision(BlenderMSBPart):
    """Not FLVER-based."""

    SOULSTRUCT_CLASS = MSBConnectCollision
    PART_SUBTYPE = MSBPartSubtype.CONNECT_COLLISION
    MODEL_SUBTYPES = ["collision_models"]

    @property
    def connect_collision_props(self) -> MSBConnectCollisionProps:
        return self.obj.msb_connect_collision_props

    def set_obj_properties(self, operator: LoggingOperator, entry: MSBConnectCollision):
        super().set_obj_properties(operator, entry)
        props = self.obj.msb_connect_collision_props

        if entry.collision:
            was_missing, collision_obj = find_obj_or_create_empty(entry.collision.name, SoulstructType.MSB_PART)
            # noinspection PyUnresolvedReferences
            collision_obj.msb_part_props.msb_part_subtype = MSBPartSubtype.COLLISION
            props.collision = collision_obj
            if was_missing:
                # TODO: In almost all cases, the referenced Collision will share this model. Could do better than Empty.
                operator.warning(
                    f"Collision '{entry.collision.name}' not found in scene. Creating empty object with that name "
                    f"in Scene Collection to use as collision for Connect Collision '{entry.name}'."
                )

        # Only other properties are connected map ID components.
        props.map_area = entry.connected_map_id[0]
        props.map_block = entry.connected_map_id[1]
        props.map_cc = entry.connected_map_id[2]
        props.map_dd = entry.connected_map_id[3]

    def set_entry_properties(self, operator: LoggingOperator, entry: MSBConnectCollision, msb: MSB):
        super().set_entry_properties(operator, entry, msb)
        props = self.connect_collision_props

        if not props.collision:
            # Required.
            raise MSBPartExportError(f"MSB Connect Collision '{entry.name}' does not reference an MSB Collision.")
        self.set_part_entry_reference(props.collision, entry, "collision", msb)

        # Blender component props are already restricted to [-1, 99] or [0, 99] for area.
        entry.connected_map_id = [props.map_area, props.map_block, props.map_cc, props.map_dd]

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