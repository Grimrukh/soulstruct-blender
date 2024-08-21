from __future__ import annotations

__all__ = [
    "IBlenderMSBPart",
    "IBlenderMSBRegion",
    "IBlenderMSBEvent",
]

import typing as tp

import abc
import bpy
from io_soulstruct.types import *
from io_soulstruct.type_checking import *
from io_soulstruct.utilities import *
from soulstruct.base.maps.msb import MSB as BaseMSB, MSBEntry
from soulstruct.base.maps.msb.events import BaseMSBEvent
from soulstruct.base.maps.msb.parts import BaseMSBPart
from soulstruct.base.maps.msb.regions import BaseMSBRegion
from .properties import MSBPartSubtype, MSBRegionSubtype, MSBEventSubtype, RegionShapeType


class IBlenderMSBPart(SoulstructObject, abc.ABC):
    TYPE = SoulstructType.MSB_PART
    # OBJ_DATA_TYPE is subtype-dependent.
    SOULSTRUCT_CLASS: tp.ClassVar[type[MSB_PART_TYPING]]
    EXPORT_TIGHT_NAME: tp.ClassVar[bool]
    PART_SUBTYPE: tp.ClassVar[MSBPartSubtype]
    MODEL_SUBTYPES: tp.ClassVar[list[str]]  # for `MSB` model search on export
    MODEL_USES_LATEST_MAP: tp.ClassVar[bool] = False  # which map version folder to look for model in

    obj: bpy.types.MeshObject
    data: bpy.types.Mesh

    model: bpy.types.MeshObject | None
    entity_id: int

    @classmethod
    def find_model_mesh(cls, model_name: str, map_stem: str) -> bpy.types.MeshObject:
        """Find the given model in Blender data."""
        ...

    @classmethod
    def batch_import_models(
        cls, operator: LoggingOperator, context: bpy.types.Context, parts: list[BaseMSBPart], map_stem: str
    ):
        """Import all models for this part type in the current scene."""
        ...

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: BaseMSBPart,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
        try_import_model=True,
        model_collection: bpy.types.Collection = None,
    ) -> tp.Self:
        ...

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: BaseMSB = None,
    ) -> BaseMSBPart:
        ...


class IBlenderMSBRegion(SoulstructObject, abc.ABC):
    TYPE = SoulstructType.MSB_REGION
    OBJ_DATA_TYPE = SoulstructDataType.MESH
    SOULSTRUCT_CLASS: tp.ClassVar[type[MSB_REGION_TYPING]]
    EXPORT_TIGHT_NAME = False
    REGION_SUBTYPE: tp.ClassVar[MSBRegionSubtype]

    obj: bpy.types.MeshObject
    data: bpy.types.Mesh

    entity_id: int
    shape_type: RegionShapeType

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: BaseMSBRegion,
        name: str,
        collection: bpy.types.Collection = None,
        # No `map_stem` required to handle missing MSB references.
    ) -> tp.Self:
        ...


class IBlenderMSBEvent(SoulstructObject, abc.ABC):
    """Mesh-only MSB Part instance of a FLVER model of the corresponding Part subtype (Map Piece, Character, etc.).

    FLVER model Armatures and Dummies are NOT instantiated for FLVER parts -- strictly Meshes (or Empties for Player
    Starts).
    """

    TYPE: tp.ClassVar[SoulstructType] = SoulstructType.MSB_EVENT
    OBJ_DATA_TYPE: tp.ClassVar[SoulstructDataType] = SoulstructDataType.EMPTY
    SOULSTRUCT_CLASS: tp.ClassVar[type[MSB_EVENT_TYPING]]
    EXPORT_TIGHT_NAME: tp.ClassVar[bool] = False  # for MSB events, we never use tight names
    EVENT_SUBTYPE: tp.ClassVar[MSBEventSubtype]
    PARENT_PROP_NAME: tp.ClassVar[str] = ""  # name of property to use as Blender parent, if any ('attached_part', etc.)

    obj: bpy.types.EmptyObject
    data: None

    entity_id: int
    attached_part: bpy.types.MeshObject | None
    attached_region: bpy.types.Object | None

    @staticmethod
    def entry_ref_to_bl_obj(
        operator: LoggingOperator,
        event: BaseMSBEvent,
        prop_name: str,
        ref_entry: MSBEntry | None,
        ref_soulstruct_type: SoulstructType,
        missing_collection_name="Missing MSB References",
    ) -> bpy.types.Object | None:
        ...

    @staticmethod
    def bl_obj_to_entry_ref(
        msb: BaseMSB,
        prop_name: str,
        bl_obj: bpy.types.Object | None,
        event: BaseMSBEvent,
        entry_subtype: str = None
    ) -> MSBEntry | None:
        ...

    @classmethod
    def new(
        cls,
        name: str,
        data: None,
        collection: bpy.types.Collection = None,
    ) -> tp.Self:
        ...

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: BaseMSBEvent,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
    ) -> tp.Self:
        ...

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: BaseMSB = None,
    ) -> BaseMSBEvent:
        ...
