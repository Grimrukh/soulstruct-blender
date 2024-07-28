from __future__ import annotations

__all__ = [
    "BlenderMSBConnectCollision",
]

import traceback
import typing as tp

import bpy
from io_soulstruct.exceptions import MissingPartModelError
from io_soulstruct.collision.model_import import *
from io_soulstruct.msb.properties import MSBPartSubtype, MSBConnectCollisionProps
from io_soulstruct.types import *
from io_soulstruct.utilities import *
from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.parts import MSBConnectCollision
from soulstruct_havok.wrappers.hkx2015.hkx_binder import BothResHKXBHD
from .msb_part import BlenderMSBPart


class BlenderMSBConnectCollision(BlenderMSBPart[MSBConnectCollision, MSBConnectCollisionProps]):
    """Not FLVER-based."""

    OBJ_DATA_TYPE = SoulstructDataType.MESH
    SOULSTRUCT_CLASS = MSBConnectCollision
    PART_SUBTYPE = MSBPartSubtype.CONNECT_COLLISION
    MODEL_SUBTYPES = ["collision_models"]

    __slots__ = []

    collision: bpy.types.Object | None

    @property
    def collision(self) -> bpy.types.MeshObject | None:
        return self.subtype_properties.collision

    @collision.setter
    def collision(self, value: bpy.types.MeshObject | None):
        self.subtype_properties.collision = value

    @property
    def connected_map_id(self) -> tuple[int, int, int, int]:
        return (
            self.subtype_properties.map_area,
            self.subtype_properties.map_block,
            self.subtype_properties.map_cc,
            self.subtype_properties.map_dd,
        )

    @connected_map_id.setter
    def connected_map_id(self, value: tuple[int, int, int, int]):
        self.subtype_properties.map_area = value[0]
        self.subtype_properties.map_block = value[1]
        self.subtype_properties.map_cc = value[2]
        self.subtype_properties.map_dd = value[3]

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBConnectCollision,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
    ) -> tp.Self:

        bl_connect_collision = super().new_from_soulstruct_obj(
            operator, context, soulstruct_obj, name, collection, map_stem
        )  # type: BlenderMSBConnectCollision

        bl_connect_collision.collision = cls.entry_ref_to_bl_obj(
            operator,
            soulstruct_obj,
            "collision",
            soulstruct_obj.collision,
            SoulstructType.MSB_PART,
            missing_collection_name=f"{map_stem} Missing MSB References".lstrip(),
        )
        bl_connect_collision.connected_map_id = soulstruct_obj.connected_map_id

        return bl_connect_collision

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> MSBConnectCollision:
        connect_collision = super().to_soulstruct_obj(operator, context, map_stem, msb)  # type: MSBConnectCollision

        connect_collision.collision = self.bl_obj_to_entry_ref(msb, "collision", self.collision, connect_collision)
        connect_collision.connected_map_id = self.connected_map_id

        return connect_collision

    @classmethod
    def find_model_mesh(cls, model_name: str, map_stem: str) -> bpy.types.MeshObject:
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
    def import_model_mesh(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_name: str,
        map_stem: str,
    ) -> bpy.types.MeshObject:
        """Import the Map Collison HKX model of the given name into a collection in the current scene.

        NOTE: `map_stem` should already be set to oldest version if option is enabled. This function is agnostic.
        """
        settings = operator.settings(context)

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
