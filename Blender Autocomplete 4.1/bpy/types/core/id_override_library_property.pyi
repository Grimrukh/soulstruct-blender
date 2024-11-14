import typing
import collections.abc
import mathutils
from .struct import Struct
from .id_override_library_property_operations import IDOverrideLibraryPropertyOperations
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class IDOverrideLibraryProperty(bpy_struct):
    """Description of an overridden property"""

    operations: IDOverrideLibraryPropertyOperations
    """ List of overriding operations for a property

    :type: IDOverrideLibraryPropertyOperations
    """

    rna_path: str
    """ RNA path leading to that property, from owning ID

    :type: str
    """

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
