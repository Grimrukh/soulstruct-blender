from __future__ import annotations

__all__ = [
    "BlenderMSBSpawnerEvent",
]

import typing as tp

import bpy
from io_soulstruct.msb.properties import MSBEventSubtype, MSBSpawnerEventProps
from io_soulstruct.utilities import LoggingOperator
from io_soulstruct.types import SoulstructType
from soulstruct.demonssouls.maps import MSB
from soulstruct.demonssouls.maps.msb import MSBSpawnerEvent
from .msb_event import BlenderMSBEvent


class BlenderMSBSpawnerEvent(BlenderMSBEvent[MSBSpawnerEvent, MSBSpawnerEventProps]):

    SOULSTRUCT_CLASS = MSBSpawnerEvent
    EVENT_SUBTYPE = MSBEventSubtype.Spawner
    PARENT_PROP_NAME = ""
    __slots__ = []

    AUTO_SUBTYPE_PROPS = [
        "max_count",
        "spawner_type",
        "limit_count",
        "min_spawner_count",
        "max_spawner_count",
        "min_interval",
        "max_interval",
        "initial_spawn_count",
    ]

    max_count: int
    spawner_type: int
    limit_count: int
    min_spawner_count: int
    max_spawner_count: int
    min_interval: float
    max_interval: float
    initial_spawn_count: int

    @property
    def spawn_parts(self) -> list[bpy.types.Object | None]:
        return self.subtype_properties.get_spawn_parts()

    @spawn_parts.setter
    def spawn_parts(self, value: list[bpy.types.Object | None]):
        if len(value) > 32:
            raise ValueError("Cannot have more than 32 spawn parts.")
        value = list(value)
        while len(value) < 32:
            value.append(None)
        for i, part in enumerate(value):
            setattr(self.subtype_properties, f"spawn_parts_{i}", part)

    @property
    def spawn_regions(self) -> list[bpy.types.Object | None]:
        return self.subtype_properties.get_spawn_regions()

    @spawn_regions.setter
    def spawn_regions(self, value: list[bpy.types.Object | None]):
        if len(value) > 4:
            raise ValueError("Cannot have more than 4 spawn regions.")
        value = list(value)
        while len(value) < 4:
            value.append(None)
        for i, region in enumerate(value):
            setattr(self.subtype_properties, f"spawn_regions_{i}", region)

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBSpawnerEvent,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
    ) -> tp.Self:
        bl_event = super().new_from_soulstruct_obj(
            operator, context, soulstruct_obj, name, collection, map_stem
        )  # type: BlenderMSBSpawnerEvent

        missing_collection_name = f"{map_stem} Missing MSB References".lstrip()

        bl_event.spawn_parts = [
            cls.entry_ref_to_bl_obj(
                operator,
                soulstruct_obj,
                f"spawn_parts[{i}]",
                soulstruct_obj.spawn_parts[i],
                SoulstructType.MSB_PART,
                missing_collection_name=missing_collection_name,
            )
            for i in range(32)
        ]
        bl_event.spawn_regions = [
            cls.entry_ref_to_bl_obj(
                operator,
                soulstruct_obj,
                f"spawn_regions[{i}]",
                soulstruct_obj.spawn_regions[i],
                SoulstructType.MSB_REGION,
                missing_collection_name=missing_collection_name,
            )
            for i in range(4)
        ]

        for prop_name in cls.AUTO_SUBTYPE_PROPS:
            setattr(bl_event, prop_name, getattr(soulstruct_obj, prop_name))

        return bl_event

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> MSBSpawnerEvent:
        spawner_event = super().to_soulstruct_obj(operator, context, map_stem, msb)  # type: MSBSpawnerEvent

        for i, part in enumerate(self.spawn_parts):
            spawner_event.spawn_parts[i] = self.bl_obj_to_entry_ref(msb, f"spawn_parts[{i}]", part, spawner_event)
        for i, region in enumerate(self.spawn_regions):
            spawner_event.spawn_regions[i] = self.bl_obj_to_entry_ref(msb, f"spawn_regions[{i}]", region, spawner_event)

        for prop_name in self.AUTO_SUBTYPE_PROPS:
            setattr(spawner_event, prop_name, getattr(self, prop_name))

        return spawner_event


BlenderMSBSpawnerEvent.add_auto_subtype_props(*BlenderMSBSpawnerEvent.AUTO_SUBTYPE_PROPS)
