from __future__ import annotations

__all__ = [
    "BaseBlenderMSBEntry",
    "ENTRY_T",
    "TYPE_PROPS_T",
    "SUBTYPE_PROPS_T",
    "MSB_T",
]

import abc
import typing as tp
from enum import StrEnum

import bpy

from soulstruct.base.maps.msb import MSB as BaseMSB
from soulstruct.base.maps.msb.msb_entry import MSBEntry

from soulstruct.blender.msb.types.adapters import MSBReferenceFieldAdapter
from soulstruct.blender.types import BaseBlenderSoulstructObject
from soulstruct.blender.utilities.operators import LoggingOperator


class BlenderMSBEntryProps(tp.Protocol):
    entry_subtype: bpy.props.EnumProperty() | str


ENTRY_T = tp.TypeVar("ENTRY_T", bound=MSBEntry)
TYPE_PROPS_T = tp.TypeVar("TYPE_PROPS_T", bound=BlenderMSBEntryProps)  # narrowed
SUBTYPE_PROPS_T = tp.TypeVar("SUBTYPE_PROPS_T", bound=tp.Union[bpy.types.PropertyGroup, None])
MSB_T = tp.TypeVar("MSB_T", bound=BaseMSB)
SELF_T = tp.TypeVar("SELF_T", bound="BaseBlenderMSBEntry")


class BaseBlenderMSBEntry(
    BaseBlenderSoulstructObject[ENTRY_T, TYPE_PROPS_T],
    abc.ABC,
    tp.Generic[ENTRY_T, TYPE_PROPS_T, SUBTYPE_PROPS_T, MSB_T],
):
    """Base class for all `MSBEntry` Blender wrapper types.

    Extends generic types with Blender subtype property group and game-specific `MSB` class (required to resolve
    inter-entry references upon object export).
    """

    SOULSTRUCT_CLASS: tp.ClassVar[type[MSBEntry]]
    # Defined by subclass and used to find `subtype_properties`.
    MSB_ENTRY_SUBTYPE: tp.ClassVar[StrEnum]

    @property
    def subtype_properties(self) -> SUBTYPE_PROPS_T:
        """Retrieved based on MSB Entry subtype enum (type narrowed by supertype base class and set by final class)."""
        return getattr(self.obj, self.MSB_ENTRY_SUBTYPE)

    @property
    def transform_obj(self) -> bpy.types.Object:
        """Returns wrapped Blender object that MSB transform is stored on (e.g. Part's Armature)."""
        return self.obj

    @classmethod
    def new(
        cls: type[SELF_T],
        name: str,
        data: bpy.types.Mesh | None,
        collection: bpy.types.Collection = None,
    ) -> SELF_T:
        """Sets entry subtype appropriately under supertype properties (e.g. `obj.MSB_PART.entry_subtype`)."""
        bl_entry = super().new(name, data, collection)  # type: SELF_T
        bl_entry.type_properties.entry_subtype = cls.MSB_ENTRY_SUBTYPE
        return bl_entry

    def _create_soulstruct_obj(self) -> ENTRY_T:
        """Create a new MSB Entry instance of the appropriate subtype. Args are supplied automatically."""
        # noinspection PyArgumentList
        return self.SOULSTRUCT_CLASS(name=self.game_name)

    @classmethod
    def get_msb_subcollection(cls, msb_collection: bpy.types.Collection, msb_stem: str) -> bpy.types.Collection:
        """Get or create the subcollection for this MSB Entry type in the given MSB collection."""
        raise NotImplementedError(f"{cls.__name__} must implement `get_msb_subcollection()`.")

    def _read_props_from_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        msb_entry: ENTRY_T,
    ):
        """Read subtype fields as well as type fields.

        Skips MSB reference fields, which are read after all Blender entries are created.
        """
        for field in self.TYPE_FIELDS + self.SUBTYPE_FIELDS:
            if not isinstance(field, MSBReferenceFieldAdapter):
                field.soulstruct_to_blender(operator, context, msb_entry, self)

    def resolve_bl_entry_refs(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        msb_entry: ENTRY_T,
        missing_reference_callback: tp.Callable[[bpy.types.Object], None],
        msb_objects: tp.Iterable[bpy.types.Object],
    ):
        """Read all MSB Entry reference properties from the given MSB Entry into the Blender object.

        Called AFTER all MSB entry objects have been created in Blender, so that references can be resolved. MSB
        collection must be given to avoid referencing same-named objects in other loaded MSBs.
        """
        for field in self.TYPE_FIELDS + self.SUBTYPE_FIELDS:
            if isinstance(field, MSBReferenceFieldAdapter):
                field.soulstruct_to_blender(
                    operator,
                    context,
                    msb_entry,
                    self,
                    missing_reference_callback=missing_reference_callback,
                    msb_objects=msb_objects,
                )

    def _write_props_to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        msb_entry: ENTRY_T,
    ):
        """Write subtype fields as well as type fields.

        Skips MSB reference fields, which are read after all MSB entries are created.
        """
        for field in self.TYPE_FIELDS + self.SUBTYPE_FIELDS:
            if not isinstance(field, MSBReferenceFieldAdapter):
                field.blender_to_soulstruct(operator, context, self, msb_entry)

    def resolve_msb_entry_refs_and_map_stem(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        msb_entry: ENTRY_T,
        msb: MSB_T,
        map_stem: str,
    ):
        """Write all reference properties from the Blender object to the given MSB Entry. Also writes any
        miscellaneous fields that require `map_stem` (e.g. automatic SIB paths) in subclasses.

        `map_stem` is required for MSB Model automatic generation for MSB Parts (in override).

        Written AFTER all MSB entries have been created in the MSB, so that references can be resolved.
        """
        for field in self.TYPE_FIELDS + self.SUBTYPE_FIELDS:
            if isinstance(field, MSBReferenceFieldAdapter):
                field.blender_to_soulstruct(operator, context, self, msb_entry, msb=msb)
