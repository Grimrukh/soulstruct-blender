from __future__ import annotations

__all__ = [
    "BlenderMSBEntry",
]

import abc
import typing as tp

import bpy

from io_soulstruct.utilities import get_bl_obj_tight_name

if tp.TYPE_CHECKING:
    from io_soulstruct.general import SoulstructSettings
    from io_soulstruct.type_checking import MSB_TYPING
    from io_soulstruct.types import SoulstructType
    from io_soulstruct.utilities import LoggingOperator
    from soulstruct.base.maps.msb.core import MSBEntry


ENTRY_TYPE = tp.TypeVar("ENTRY_TYPE", bound=MSBEntry)


class BlenderMSBEntry(abc.ABC, tp.Generic[ENTRY_TYPE]):
    """Base class for Blender objects that represent MSB entries of any supertype/subtype."""

    # For type checking and exporting.
    SOULSTRUCT_CLASS: tp.ClassVar[type[MSBEntry]]
    SOULSTRUCT_TYPE: tp.ClassVar[SoulstructType]

    # If `True`, `MSBEntry` objects created by `to_entry()` will use `tight_name` instead of `name`.
    EXPORT_TIGHT_NAME: tp.ClassVar[bool] = False

    obj: bpy.types.Object

    def __init__(self, obj: bpy.types.Object):
        """NOTE: We don't check the `soulstruct_type` of `obj`."""
        self.obj = obj

    @property
    def name(self) -> str:
        return self.obj.name

    @name.setter
    def name(self, new_name: str):
        self.obj.name = new_name
    
    @property
    def tight_name(self):
        return get_bl_obj_tight_name(self.obj)

    def set_obj_properties(self, operator: LoggingOperator, entry: ENTRY_TYPE):
        self.assert_msb_entry_type(entry)
        self.obj.soulstruct_type = self.SOULSTRUCT_TYPE

    def set_entry_properties(self, operator: LoggingOperator, entry: ENTRY_TYPE, msb: MSB_TYPING):
        """`msb` is required to resolve internal MSB entry references."""
        self.assert_msb_entry_type(entry)
        self.assert_obj_type()

    @classmethod
    def assert_msb_entry_type(cls, entry: ENTRY_TYPE):
        if not isinstance(entry, cls.SOULSTRUCT_CLASS):
            raise TypeError(f"MSB entry is not of type {cls.SOULSTRUCT_CLASS.__name__}: {entry}")

    def assert_obj_type(self):
        if self.obj.soulstruct_type != self.SOULSTRUCT_TYPE:
            raise TypeError(f"Blender object '{self.name}' does not have Soulstruct type `{self.SOULSTRUCT_TYPE}`.")

    @classmethod
    @abc.abstractmethod
    def new_from_entry(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        map_stem: str,
        entry: ENTRY_TYPE,
        collection: bpy.types.Collection = None,
    ):
        """Create a new Blender object from `MSBEntry` of appropriate type."""

    @abc.abstractmethod
    def to_entry(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        map_stem: str,
        msb: MSB_TYPING,
    ) -> ENTRY_TYPE:
        """Create a new MSB entry from this Blender object."""
        entry = self.SOULSTRUCT_CLASS()
        entry.name = self.tight_name if self.EXPORT_TIGHT_NAME else self.name
        self.set_entry_properties(operator, entry, msb)
        return entry

    @staticmethod
    def set_obj_generic_props(
        entry: ENTRY_TYPE,
        props: bpy.types.PropertyGroup,
        skip_prefixes: tuple[str, ...] = (),
        skip_names: tp.Collection[str] = (),
    ):
        for prop_name in props.__annotations__:
            if prop_name.startswith(skip_prefixes):
                continue
            if prop_name in skip_names:
                continue
            setattr(props, prop_name, getattr(entry, prop_name))

    @staticmethod
    def set_entry_generic_props(
        props: bpy.types.PropertyGroup,
        entry: ENTRY_TYPE,
        skip_prefixes: tuple[str, ...] = (),
        skip_names: tp.Collection[str] = (),
    ):
        for prop_name in props.__annotations__:
            if prop_name.startswith(skip_prefixes):
                continue
            if prop_name in skip_names:
                continue
            setattr(entry, prop_name, getattr(props, prop_name))

