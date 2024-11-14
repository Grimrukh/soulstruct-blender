import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .id_override_library_property import IDOverrideLibraryProperty
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class IDOverrideLibraryProperties(
    bpy_prop_collection[IDOverrideLibraryProperty], bpy_struct
):
    """Collection of override properties"""

    def add(self, rna_path: str | typing.Any) -> IDOverrideLibraryProperty:
        """Add a property to the override library when it doesn't exist yet

        :param rna_path: RNA Path, RNA-Path of the property to add
        :type rna_path: str | typing.Any
        :return: New Property, Newly created override property or existing one
        :rtype: IDOverrideLibraryProperty
        """
        ...

    def remove(self, property: IDOverrideLibraryProperty | None):
        """Remove and delete a property

        :param property: Property, Override property to be deleted
        :type property: IDOverrideLibraryProperty | None
        """
        ...

    @classmethod
    def bl_rna_get_subclass(cls, id: str | None, default=None) -> Struct:
        """

        :param id: The RNA type identifier.
        :type id: str | None
        :param default:
        :return: The RNA type or default when not found.
        :rtype: Struct
        """
        ...

    @classmethod
    def bl_rna_get_subclass_py(cls, id: str | None, default=None) -> typing.Any:
        """

        :param id: The RNA type identifier.
        :type id: str | None
        :param default:
        :return: The class or default when not found.
        :rtype: typing.Any
        """
        ...
