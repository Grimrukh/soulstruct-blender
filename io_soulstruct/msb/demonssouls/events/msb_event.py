from __future__ import annotations

__all__ = [
    "BlenderMSBEvent",
]

import typing as tp

import bpy
from io_soulstruct.exceptions import *
from io_soulstruct.msb.properties import MSBEventSubtype, MSBEventProps
from io_soulstruct.types import *
from io_soulstruct.utilities import *
from soulstruct.demonssouls.maps.msb import MSBEvent

if tp.TYPE_CHECKING:
    from soulstruct.base.maps.msb import MSBEntry
    from soulstruct.demonssouls.maps.msb import MSB


EVENT_T = tp.TypeVar("EVENT_T", bound=MSBEvent)
SUBTYPE_PROPS_T = tp.TypeVar("SUBTYPE_PROPS_T", bound=bpy.types.PropertyGroup)


class BlenderMSBEvent(SoulstructObject[MSBEvent, MSBEventProps], tp.Generic[EVENT_T, SUBTYPE_PROPS_T]):
    """MSB Event instance. Always Empty object."""

    TYPE: tp.ClassVar[SoulstructType] = SoulstructType.MSB_EVENT
    OBJ_DATA_TYPE: tp.ClassVar[SoulstructDataType] = SoulstructDataType.EMPTY
    SOULSTRUCT_CLASS: tp.ClassVar[type[MSBEvent]]
    EXPORT_TIGHT_NAME: tp.ClassVar[bool] = True  # tight name strips away '<EventSubtype>' suffix
    EVENT_SUBTYPE: tp.ClassVar[MSBEventSubtype]
    PARENT_PROP_NAME: tp.ClassVar[str] = ""  # name of property to use as Blender parent, if any ('attached_part', etc.)

    __slots__ = []
    obj: bpy.types.EmptyObject
    data: None

    @property
    def tight_name(self):
        """Any name is permitted for events, including Unicode (Japanese) characters, and they do not have to be
        unique in the MSB (though this makes Soulstruct EMEVD event scripting harder). We just remove any Blender
        duplicate suffixes and the convenient '<SUBTYPE>' suffix added on import."""
        name = match.group(1) if (match := BLENDER_DUPE_RE.match(self.obj.name)) else self.obj.name
        return name.removesuffix(f"<{self.EVENT_SUBTYPE.name}>").strip()

    @property
    def subtype_properties(self) -> SUBTYPE_PROPS_T:
        return getattr(self.obj, self.EVENT_SUBTYPE)

    @property
    def entity_id(self) -> int:
        return self.type_properties.entity_id

    @entity_id.setter
    def entity_id(self, value: int):
        self.type_properties.entity_id = value

    @property
    def attached_part(self) -> bpy.types.MeshObject | None:
        return self.type_properties.attached_part

    @attached_part.setter
    def attached_part(self, value: bpy.types.MeshObject | None):
        self.type_properties.attached_part = value

    @property
    def attached_region(self) -> bpy.types.Object | None:
        return self.type_properties.attached_region

    @attached_region.setter
    def attached_region(self, value: bpy.types.Object | None):
        self.type_properties.attached_region = value

    @staticmethod
    def entry_ref_to_bl_obj(
        operator: LoggingOperator,
        event: MSBEvent,
        prop_name: str,
        ref_entry: MSBEntry | None,
        ref_soulstruct_type: SoulstructType,
        missing_collection_name="Missing MSB References",
    ) -> bpy.types.Object | None:
        if not ref_entry:
            return None

        was_missing, pointer_obj = find_obj_or_create_empty(
            ref_entry.name,
            find_stem=True,
            soulstruct_type=ref_soulstruct_type,
            missing_collection_name=missing_collection_name,
        )
        if was_missing:
            operator.warning(
                f"Referenced MSB entry '{ref_entry.name}' in field '{prop_name}' of MSB event '{event.name}' not "
                f"found in Blender data. Creating empty reference."
            )
        return pointer_obj

    @staticmethod
    def bl_obj_to_entry_ref(
        msb: MSB,
        prop_name: str,
        bl_obj: bpy.types.Object | None,
        event: MSBEvent,
        entry_subtype: str = None
    ) -> MSBEntry | None:

        if not bl_obj:
            return None  # leave event field as `None`
        if entry_subtype:
            subtypes = (entry_subtype,)
        else:
            subtypes = ()

        try:
            if bl_obj.soulstruct_type == SoulstructType.MSB_PART:
                msb_entry = msb.find_part_name(get_bl_obj_tight_name(bl_obj), subtypes=subtypes)
            elif bl_obj.soulstruct_type == SoulstructType.MSB_REGION:
                msb_entry = msb.find_region_name(bl_obj.name, subtypes=subtypes)  # full name
            elif bl_obj.soulstruct_type == SoulstructType.MSB_EVENT:
                msb_entry = msb.find_event_name(bl_obj.name, subtypes=subtypes)  # full name
            else:
                raise SoulstructTypeError(f"Blender object '{bl_obj.name}' is not an MSB Part, Region, or Event.")
            return msb_entry
        except KeyError:
            raise MissingMSBEntryError(
                f"MSB entry '{bl_obj.name}' referenced in field '{prop_name}' of event '{event.name}' "
                f"not found in MSB."
            )

    @classmethod
    def new(
        cls,
        name: str,
        data: None,
        collection: bpy.types.Collection = None,
    ) -> tp.Self:
        """Name has '<EventSubtype>' suffix for visibility, as Events aren't grouped like Parts."""
        name = f"{name} <{cls.EVENT_SUBTYPE.name}>"
        bl_event = super().new(name, data, collection)  # type: tp.Self
        bl_event.obj.MSB_EVENT.event_subtype = cls.EVENT_SUBTYPE.value  # NOT name
        bl_event.obj.empty_display_type = "SINGLE_ARROW"  # TODO: seems least annoying
        return bl_event

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: EVENT_T,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
    ) -> tp.Self:
        """Create a fully-represented MSB Event linked to a source model in Blender.

        Subclasses will override this to set additional Event-specific properties.
        """
        bl_event = cls.new(name, None, collection)  # type: tp.Self
        bl_event.entity_id = soulstruct_obj.entity_id
        bl_event.attached_part = cls.entry_ref_to_bl_obj(
            operator, soulstruct_obj, "attached_part", soulstruct_obj.attached_part, SoulstructType.MSB_PART
        )
        bl_event.attached_region = cls.entry_ref_to_bl_obj(
            operator, soulstruct_obj, "attached_region", soulstruct_obj.attached_region, SoulstructType.MSB_REGION
        )
        return bl_event

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> EVENT_T:
        if msb is None:
            raise ValueError("MSB must be provided to resolve Blender MSB references into real MSB entries.")

        event = self._create_soulstruct_obj(self.export_name)  # type: EVENT_T

        event.entity_id = self.entity_id
        event.attached_part = self.bl_obj_to_entry_ref(msb, "attached_part", self.attached_part, event)
        event.attached_region = self.bl_obj_to_entry_ref(msb, "attached_region", self.attached_region, event)

        return event

    @classmethod
    def add_auto_subtype_props(cls, *names):
        for prop_name in names:
            # `prop_name` must be baked in to each closure!
            setattr(
                cls, prop_name, property(
                    lambda self, pn=prop_name: getattr(self.subtype_properties, pn),
                    lambda self, value, pn=prop_name: setattr(self.subtype_properties, pn, value),
                )
            )
