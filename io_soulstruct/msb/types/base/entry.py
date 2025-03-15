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

from io_soulstruct.msb.types.adapters import SoulstructFieldAdapter, MSBReferenceFieldAdapter
from io_soulstruct.types import BaseBlenderSoulstructObject, TYPE_PROPS_T
from io_soulstruct.utilities.operators import LoggingOperator

from .msb_protocols import MSBEntryProtocol

ENTRY_T = tp.TypeVar("ENTRY_T", bound=MSBEntryProtocol)
SUBTYPE_PROPS_T = tp.TypeVar("SUBTYPE_PROPS_T", bound=tp.Union[bpy.types.PropertyGroup, None])
MSB_T = tp.TypeVar("MSB_T", bound=BaseMSB)


class BaseBlenderMSBEntry(
    BaseBlenderSoulstructObject[ENTRY_T, TYPE_PROPS_T],
    abc.ABC,
    tp.Generic[ENTRY_T, TYPE_PROPS_T, SUBTYPE_PROPS_T, MSB_T],
):
    """Base class for all `MSBEntry` Blender wrapper types.

    Extends generic types with Blender subtype property group and game-specific `MSB` class (required to resolve
    inter-entry references upon object export).
    """

    SOULSTRUCT_CLASS: tp.ClassVar[type[MSBEntryProtocol]]
    # Defined by subclass and used to find `subtype_properties`.
    MSB_ENTRY_SUBTYPE: tp.ClassVar[StrEnum]
    # Additional MSB subtype fields that are stored in `subtype_properties` in Blender rather than `type_properties`.
    SUBTYPE_FIELDS: tp.ClassVar[tuple[SoulstructFieldAdapter, ...]]

    @property
    def subtype_properties(self) -> SUBTYPE_PROPS_T:
        """Retrieved based on MSB Entry subtype enum (type narrowed by supertype base class and set by final class)."""
        return getattr(self.obj, self.MSB_ENTRY_SUBTYPE)

    def _create_soulstruct_obj(self) -> ENTRY_T:
        """Create a new MSB Entry instance of the appropriate subtype. Args are supplied automatically."""
        # noinspection PyArgumentList
        return self.SOULSTRUCT_CLASS(name=self.game_name)

    def _read_props_from_soulstruct_obj(self, operator: LoggingOperator, msb_entry: ENTRY_T):
        """Read subtype fields as well as type fields.

        Skips MSB reference fields, which are read after all Blender entries are created.
        """
        for field in (f for f in self.TYPE_FIELDS + self.SUBTYPE_FIELDS if not isinstance(f, MSBReferenceFieldAdapter)):
            field.read_prop_from_soulstruct_obj(operator, msb_entry, self)

    def resolve_bl_entry_refs(self, operator: LoggingOperator, msb_entry: ENTRY_T):
        """Read all MSB Entry reference properties from the given MSB Entry into the Blender object.

        Called AFTER all MSB entry objects have been created in Blender, so that references can be resolved.
        """
        for field in (f for f in self.TYPE_FIELDS + self.SUBTYPE_FIELDS if isinstance(f, MSBReferenceFieldAdapter)):
            field.read_prop_from_soulstruct_obj(operator, msb_entry, self)

    def _write_props_to_soulstruct_obj(self, operator: LoggingOperator, msb_entry: ENTRY_T):
        """Write subtype fields as well as type fields.

        Skips MSB reference fields, which are read after all MSB entries are created.
        """
        for field in (f for f in self.TYPE_FIELDS + self.SUBTYPE_FIELDS if not isinstance(f, MSBReferenceFieldAdapter)):
            field.write_prop_to_soulstruct_obj(operator, self, msb_entry)

    def resolve_msb_entry_refs_and_map_stem(
        self, operator: LoggingOperator, msb_entry: ENTRY_T, msb: MSB_T, map_stem: str
    ):
        """Write all reference properties from the Blender object to the given MSB Entry. Also writes any
        miscellaneous fields that require `map_stem` (e.g. automatic SIB paths) in subclasses.

        `map_stem` is required for MSB Model automatic generation for MSB Parts (in override).

        Written AFTER all MSB entries have been created in the MSB, so that references can be resolved.
        """
        for field in (f for f in self.TYPE_FIELDS + self.SUBTYPE_FIELDS if isinstance(f, MSBReferenceFieldAdapter)):
            field.write_prop_to_soulstruct_obj(operator, self, msb_entry)
