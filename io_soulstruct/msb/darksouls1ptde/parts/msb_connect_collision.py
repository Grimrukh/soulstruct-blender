from __future__ import annotations

__all__ = [
    "BlenderMSBConnectCollision",
]

import typing as tp

import bpy
from io_soulstruct.exceptions import MissingPartModelError
from io_soulstruct.msb.properties import MSBPartSubtype, MSBConnectCollisionProps
from io_soulstruct.types import *
from io_soulstruct.utilities import *
from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.parts import MSBConnectCollision
from .msb_collision import BlenderMSBCollision
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

        This just hijacks the model import class method of `BlenderMSBCollision`.
        """
        return BlenderMSBCollision.import_model_mesh(operator, context, model_name, map_stem)
